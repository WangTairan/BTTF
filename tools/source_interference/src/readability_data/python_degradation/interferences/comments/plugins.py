from __future__ import annotations

import ast
import io
import tokenize

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
    offsets,
    span,
)


class RemoveComments(Interference):
    category = "comments"
    slug = "remove-comments"
    description = "Remove comments and docstrings"

    def apply(self, source: str, context: Context) -> Result:
        starts = offsets(source)
        edits: list[tuple[int, int, str]] = []
        docstrings = 0
        removed_bytes = 0
        tree = ast.parse(source)
        for owner in ast.walk(tree):
            body = getattr(owner, "body", None)
            if (
                isinstance(body, list)
                and body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node = body[0]
                start, end = span(node, starts)
                replacement = "pass" if len(body) == 1 else ""
                edits.append((start, end, replacement))
                removed_bytes += end - start - len(replacement.encode("utf-8"))
                docstrings += 1
        comment_count = 0
        line_starts = [0]
        for line in source.splitlines(keepends=True):
            line_starts.append(line_starts[-1] + len(line))
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            start = line_starts[token.start[0] - 1] + token.start[1]
            end = line_starts[token.end[0] - 1] + token.end[1]
            prefix = source[:start].encode("utf-8")
            bstart = len(prefix)
            bend = bstart + len(source[start:end].encode("utf-8"))
            edits.append((bstart, bend, " "))
            removed_bytes += bend - bstart - 1
            comment_count += 1
        return Result(
            apply_edits(source, _nonoverlapping(edits)),
            {
                "comments_removed": comment_count + docstrings,
                "line_comments_removed": comment_count,
                "docstrings_removed": docstrings,
                "comment_bytes_removed": removed_bytes,
            },
        )


def _nonoverlapping(edits: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    result = []
    for edit in sorted(edits):
        if result and edit[0] < result[-1][1]:
            continue
        result.append(edit)
    return result


PLUGINS = (RemoveComments(),)
