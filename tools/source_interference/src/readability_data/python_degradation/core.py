from __future__ import annotations

import ast
import io
import tokenize

from readability_data.shared.contracts import (
    Interference as Interference,
)
from readability_data.shared.contracts import (
    InterferenceContext,
    TransformResult,
)

Context = InterferenceContext
Result = TransformResult


def validate(source: str) -> None:
    source.encode("utf-8")
    ast.parse(source)


def offsets(source: str) -> list[int]:
    starts = [0]
    for line in source.splitlines(keepends=True):
        starts.append(starts[-1] + len(line.encode("utf-8")))
    return starts


def span(node: ast.AST, starts: list[int]) -> tuple[int, int]:
    return (
        starts[node.lineno - 1] + node.col_offset,
        starts[node.end_lineno - 1] + node.end_col_offset,
    )


def apply_edits(source: str, edits: list[tuple[int, int, str]]) -> str:
    data = source.encode("utf-8")
    last = len(data) + 1
    for start, end, replacement in sorted(edits, reverse=True):
        if end > last or start > end:
            raise ValueError("overlapping source edits")
        data = data[:start] + replacement.encode("utf-8") + data[end:]
        last = start
    result = data.decode("utf-8")
    validate(result)
    return result


def tokens(source: str) -> list[tokenize.TokenInfo]:
    return list(tokenize.generate_tokens(io.StringIO(source).readline))
