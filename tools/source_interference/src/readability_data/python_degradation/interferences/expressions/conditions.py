from __future__ import annotations

import ast
import re

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
    offsets,
    span,
)


class InvertConditions(Interference):
    category = "expressions"
    slug = "invert-conditions"
    description = "Invert eligible conditions and exchange their branches"

    def apply(self, source: str, context: Context) -> Result:
        tree = ast.parse(source)
        starts = offsets(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        lines = source.splitlines(keepends=True)
        edits = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.If) or _has_if_ancestor(node, parents):
                continue
            if node.orelse and isinstance(node.orelse[0], ast.If):
                continue
            if (
                node.test.end_lineno != node.lineno
                or node.body[0].lineno <= node.lineno
            ):
                continue
            rendered = _render_inversion(node, source, lines, starts)
            if rendered is not None:
                edits.append((*span(node, starts), rendered))
        return Result(apply_edits(source, edits), {"conditions_inverted": len(edits)})


def _has_if_ancestor(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.If):
            return True
    return False


def _render_inversion(
    node: ast.If, source: str, lines: list[str], starts: list[int]
) -> str | None:
    test_start, test_end = span(node.test, starts)
    test_text = source.encode()[test_start:test_end].decode("utf-8")
    indent = lines[node.lineno - 1][: node.col_offset]
    true_start = node.test.end_lineno
    if not node.orelse:
        true_suite = "".join(lines[true_start : node.end_lineno])
        return (
            f"if not ({test_text}):\n{indent}    pass\n{indent}else:\n{true_suite}"
        ).rstrip("\n")

    else_line = next(
        (
            number
            for number in range(node.body[-1].end_lineno + 1, node.orelse[0].lineno + 1)
            if re.match(rf"^\s{{{node.col_offset}}}else\s*:", lines[number - 1])
        ),
        None,
    )
    if else_line is None:
        return None
    true_suite = "".join(lines[true_start : else_line - 1])
    false_suite = "".join(lines[else_line : node.end_lineno])
    return (f"if not ({test_text}):\n{false_suite}{indent}else:\n{true_suite}").rstrip(
        "\n"
    )
