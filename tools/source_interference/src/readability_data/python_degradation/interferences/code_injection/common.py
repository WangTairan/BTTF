from __future__ import annotations

import ast
from dataclasses import dataclass

from readability_data.python_degradation.core import offsets, span
from readability_data.shared.determinism import stable_digest


@dataclass(frozen=True)
class CallablePoint:
    node: ast.FunctionDef | ast.AsyncFunctionDef
    callable_offset: int
    insertion_offset: int
    indent: str


def callable_insertion_points(source: str) -> list[CallablePoint]:
    tree = ast.parse(source)
    starts = offsets(source)
    lines = source.splitlines(keepends=True)
    points = []
    for node in ast.walk(tree):
        if (
            not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            or not node.body
        ):
            continue
        first = node.body[0]
        if first.lineno <= node.lineno:
            continue
        if lines[first.lineno - 1][: first.col_offset].strip():
            # The suite begins after a multi-line signature on the same line.
            continue
        insertion_line = first.end_lineno + 1 if _is_docstring(first) else first.lineno
        points.append(
            CallablePoint(
                node=node,
                callable_offset=span(node, starts)[0],
                insertion_offset=starts[insertion_line - 1],
                indent=" " * first.col_offset,
            )
        )
    return sorted(points, key=lambda point: point.callable_offset)


def select_callable_insertion_points(
    source: str, seed: int, identity: str, namespace: str, count: int = 1
) -> list[CallablePoint]:
    return sorted(
        callable_insertion_points(source),
        key=lambda point: stable_digest(
            seed, identity, namespace, point.callable_offset
        ),
    )[:count]


def existing_identifiers(source: str) -> set[str]:
    tree = ast.parse(source)
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }


def unique_readable_identifier(base: str, used: set[str]) -> str:
    candidate = base
    suffix = 1
    while candidate in used:
        suffix += 1
        candidate = f"{base}{suffix}"
    used.add(candidate)
    return candidate


def unique_opaque_identifier(
    used: set[str], seed: int, identity: str, offset: int, role: str
) -> str:
    nonce = 0
    while True:
        digest = stable_digest(seed, identity, offset, role, nonce).hex()[:8]
        candidate = f"lI0O_{digest}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        nonce += 1


def indent_snippet(lines: tuple[str, ...], indent: str) -> str:
    return "".join(f"{indent}{line}\n" for line in lines)


def _is_docstring(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )
