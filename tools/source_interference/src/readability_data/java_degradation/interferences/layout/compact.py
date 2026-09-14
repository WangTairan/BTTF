from __future__ import annotations

from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    literal_end,
    seeded_mask,
)


class PartiallyCompactLayout(Interference):
    category = "layout"
    slug = "partially-compact-layout"
    description = "Remove about 40% of line-break groups while retaining structure"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        text = source.decode("utf-8")
        candidates: list[tuple[int, int]] = []
        index = 0
        while index < len(text):
            if text.startswith("//", index):
                newline = text.find("\n", index + 2)
                index = len(text) if newline < 0 else newline + 1
                continue
            if text.startswith("/*", index):
                closing = text.find("*/", index + 2)
                index = len(text) if closing < 0 else closing + 2
                continue
            if text.startswith('"""', index):
                index = literal_end(text, index, '"""')
                continue
            if text[index] in {'"', "'"}:
                index = literal_end(text, index, text[index])
                continue
            if not text[index].isspace():
                index += 1
                continue
            end = index + 1
            while end < len(text) and text[end].isspace():
                end += 1
            if "\n" in text[index:end] and index > 0 and end < len(text):
                candidates.append((index, end))
            index = end

        removable = max(0, len(candidates) - 2)
        selected_count = min(removable, max(1, (len(candidates) * 2) // 5))
        selected = set(
            sorted(
                candidates,
                key=lambda span: (
                    seeded_mask(
                        context.seed + 2,
                        context.identity,
                        span[0],
                        "literal",
                    ),
                    span[0],
                ),
            )[:selected_count]
        )
        output: list[str] = []
        cursor = 0
        line_breaks_removed = 0
        whitespace_removed = 0
        for start, end in candidates:
            if (start, end) not in selected:
                continue
            output.append(text[cursor:start])
            output.append(" ")
            line_breaks_removed += text[start:end].count("\n")
            whitespace_removed += end - start - 1
            cursor = end
        output.append(text[cursor:])
        return TransformResult(
            "".join(output).encode(),
            {
                "line_break_groups_available": len(candidates),
                "line_break_groups_removed": len(selected),
                "line_breaks_removed": line_breaks_removed,
                "whitespace_characters_removed": whitespace_removed,
            },
        )
