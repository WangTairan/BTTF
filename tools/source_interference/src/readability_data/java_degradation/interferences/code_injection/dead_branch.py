from __future__ import annotations

from readability_data.java_degradation.interferences.code_injection.common import (
    callable_insertion_points,
)
from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    apply_edits,
    seeded_mask,
)


class InsertDeadBranches(Interference):
    category = "code-injection"
    slug = "insert-dead-branches"
    description = "Insert deterministic runtime-dead branches into callable bodies"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        edits = []
        inserted = 0
        for node, offset in callable_insertion_points(source):
            mask = seeded_mask(
                context.seed + 1, context.identity, node.start_byte, "literal"
            )
            noise = (
                f"\nif (((0x{mask:X} ^ 0x{mask:X}) != 0)) "
                "{ throw new AssertionError(); }\n"
            ).encode()
            edits.append((offset, offset, noise))
            inserted += 1
        return TransformResult(
            apply_edits(source, edits), {"dead_branches_inserted": inserted}
        )
