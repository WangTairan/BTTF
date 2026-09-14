from __future__ import annotations

from readability_data.java_degradation.interferences.code_injection.common import (
    existing_identifiers,
    select_callable_insertion_points,
    unique_identifier,
)
from readability_data.java_degradation.interferences.code_injection.low_readability_templates import (
    LOW_READABILITY_TEMPLATES,
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
from readability_data.shared.determinism import stable_index


class InjectLowReadabilityCode(Interference):
    """Inject opaque, self-contained arithmetic whose state cannot escape its block."""

    category = "code-injection"
    slug = "inject-low-readability-unrelated-code"
    description = "Select one of ten low-readability unrelated code templates per class"

    def __init__(self, template_index: int | None = None) -> None:
        if template_index is not None and not 0 <= template_index < len(
            LOW_READABILITY_TEMPLATES
        ):
            raise ValueError(
                f"template_index must be between 0 and "
                f"{len(LOW_READABILITY_TEMPLATES) - 1}"
            )
        self.template_index = template_index

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        used = existing_identifiers(source)
        edits: list[tuple[int, int, bytes]] = []
        points = select_callable_insertion_points(
            source, context.seed, context.identity, self.slug
        )
        for node, offset in points:
            names: dict[str, str] = {}

            def name(role: str) -> str:
                if role not in names:
                    names[role] = unique_identifier(
                        "lI0O",
                        used,
                        context.seed,
                        context.identity,
                        node.start_byte,
                        role,
                    )
                return names[role]

            mask = seeded_mask(
                context.seed, context.identity, node.start_byte, "opaque-injection"
            )
            template_index = self._select_template(context, node.start_byte)
            snippet = LOW_READABILITY_TEMPLATES[template_index](name, mask).encode()
            edits.append((offset, offset, snippet))
        return TransformResult(
            apply_edits(source, edits),
            {
                "low_readability_blocks_injected": len(edits),
                "low_readability_template_index": (
                    self._select_template(context, points[0][0].start_byte)
                    if points
                    else -1
                ),
            },
        )

    def _select_template(
        self, context: InterferenceContext, callable_offset: int
    ) -> int:
        if self.template_index is not None:
            return self.template_index
        return stable_index(
            context.seed,
            context.identity,
            len(LOW_READABILITY_TEMPLATES),
            self.slug,
            callable_offset,
            "template",
        )
