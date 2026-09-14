from __future__ import annotations

import io
import tokenize

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
)
from readability_data.shared.determinism import stable_mask


class PartiallyCompactLayout(Interference):
    category = "layout"
    slug = "partially-compact-layout"
    description = (
        "Deterministically remove some optional blank lines and bracketed line breaks"
    )

    def apply(self, source: str, context: Context) -> Result:
        char_starts = [0]
        for line in source.splitlines(keepends=True):
            char_starts.append(char_starts[-1] + len(line))
        candidates: list[tuple[int, int, str]] = []
        token_stream = list(tokenize.generate_tokens(io.StringIO(source).readline))
        comment_lines = {
            token.start[0] for token in token_stream if token.type == tokenize.COMMENT
        }
        depth = 0
        for token in token_stream:
            if token.type == tokenize.OP and token.string in "([{":
                depth += 1
            elif token.type == tokenize.OP and token.string in ")]}":
                depth = max(0, depth - 1)
            elif (
                token.type == tokenize.NL
                and depth > 0
                and token.start[0] not in comment_lines
                and token.string
            ):
                a = char_starts[token.start[0] - 1] + token.start[1]
                b = char_starts[token.end[0] - 1] + token.end[1]
                candidates.append(
                    (len(source[:a].encode()), len(source[:b].encode()), " ")
                )
        lines = source.splitlines(keepends=True)
        byte_cursor = 0
        for line in lines:
            size = len(line.encode())
            if not line.strip():
                candidates.append((byte_cursor, byte_cursor + size, ""))
            byte_cursor += size
        candidates = _nonoverlapping(candidates)
        removable = max(0, len(candidates) - 2)
        selected_count = min(removable, max(1, (len(candidates) * 2) // 5))
        selected = sorted(
            candidates,
            key=lambda edit: (
                stable_mask(
                    context.seed + 2,
                    context.identity,
                    edit[0],
                    "literal",
                ),
                edit[0],
            ),
        )[:selected_count]
        line_breaks_removed = sum(
            source.encode()[start:end].count(b"\n") for start, end, _ in selected
        )
        whitespace_removed = sum(
            len(source.encode()[start:end]) - len(replacement.encode())
            for start, end, replacement in selected
        )
        result = apply_edits(source, selected)
        return Result(
            result,
            {
                "line_break_groups_available": len(candidates),
                "line_break_groups_removed": len(selected),
                "line_breaks_removed": line_breaks_removed,
                "whitespace_characters_removed": whitespace_removed,
            },
        )


def _nonoverlapping(edits):
    result = []
    for edit in sorted(edits):
        if result and edit[0] < result[-1][1]:
            continue
        result.append(edit)
    return result


PLUGINS = (PartiallyCompactLayout(),)
