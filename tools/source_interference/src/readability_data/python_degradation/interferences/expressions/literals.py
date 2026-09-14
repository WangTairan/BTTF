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


class EncodeIntegerLiterals(Interference):
    category = "expressions"
    slug = "encode-integer-literals"
    description = "Rewrite eligible decimal integer literals in hexadecimal notation"

    def apply(self, source: str, context: Context) -> Result:
        tree = ast.parse(source)
        starts = offsets(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        edits: list[tuple[int, int, str]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or _in_pattern(node, parents):
                continue
            start, end = span(node, starts)
            if not _eligible_integer(node, source, start, end):
                continue
            edits.append((start, end, hex(int(node.value))))
        return Result(
            apply_edits(source, edits),
            {"decimal_integer_literals_rewritten_as_hexadecimal": len(edits)},
        )


def _eligible_integer(node: ast.Constant, source: str, start: int, end: int) -> bool:
    if not isinstance(node.value, int) or isinstance(node.value, bool):
        return False
    raw = source.encode()[start:end].decode("utf-8")
    return re.fullmatch(r"[0-9][0-9_]*", raw) is not None


def _in_pattern(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.MatchValue, ast.MatchSingleton, ast.JoinedStr)):
            return True
    return False


# Compatibility alias for callers that used the former generic name.
EncodeLiterals = EncodeIntegerLiterals
