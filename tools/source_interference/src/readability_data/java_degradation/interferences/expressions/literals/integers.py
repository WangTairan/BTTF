from __future__ import annotations

import re

from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    apply_edits,
    tree,
    walk,
)


class EncodeIntegerLiterals(Interference):
    category = "expressions"
    slug = "encode-integer-literals"
    description = "Rewrite eligible decimal integer literals in hexadecimal notation"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        edits: list[tuple[int, int, bytes]] = []
        for node in walk(tree(source).root_node):
            if node.type != "decimal_integer_literal":
                continue
            raw = source[node.start_byte : node.end_byte].decode("utf-8")
            match = re.fullmatch(r"([0-9][0-9_]*)([lL]?)", raw)
            if not match:
                continue
            value = int(match.group(1).replace("_", ""))
            suffix = "L" if match.group(2) else ""
            replacement = f"0x{value:x}{suffix}".encode()
            edits.append((node.start_byte, node.end_byte, replacement))
        return TransformResult(
            apply_edits(source, edits),
            {"decimal_integer_literals_rewritten_as_hexadecimal": len(edits)},
        )
