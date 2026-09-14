from __future__ import annotations

from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    ancestor,
    apply_edits,
    tree,
    walk,
)


class InvertConditions(Interference):
    category = "expressions"
    slug = "invert-conditions"
    description = "Invert eligible conditions and exchange their branches"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        edits = []
        inverted = 0
        for node in walk(tree(source).root_node):
            if (
                node.type != "if_statement"
                or ancestor(node, {"if_statement"}) is not None
            ):
                continue
            condition = node.child_by_field_name("condition")
            consequence = node.child_by_field_name("consequence")
            alternative = node.child_by_field_name("alternative")
            if condition is None or consequence is None:
                continue
            condition_text = source[condition.start_byte : condition.end_byte]
            consequence_text = _as_block(
                source[consequence.start_byte : consequence.end_byte]
            )
            alternative_text = (
                _as_block(source[alternative.start_byte : alternative.end_byte])
                if alternative is not None
                else b"{}"
            )
            replacement = (
                b"if (!("
                + condition_text
                + b")) "
                + alternative_text
                + b" else "
                + consequence_text
            )
            edits.append((node.start_byte, node.end_byte, replacement))
            inverted += 1
        return TransformResult(
            apply_edits(source, edits), {"conditions_inverted": inverted}
        )


def _as_block(statement: bytes) -> bytes:
    stripped = statement.strip()
    return stripped if stripped.startswith(b"{") else b"{ " + stripped + b" }"
