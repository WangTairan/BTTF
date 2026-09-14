from __future__ import annotations

from readability_data.java_degradation.interferences.code_injection.common import (
    existing_identifiers,
    select_callable_insertion_points,
    unique_readable_identifier,
)
from readability_data.java_degradation.interferences.code_injection.readable_templates import (
    READABLE_TEMPLATES,
)
from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import apply_edits
from readability_data.shared.determinism import stable_index


class InjectReadableCode(Interference):
    """Inject clear, self-contained arithmetic whose state cannot escape its block."""

    category = "code-injection"
    slug = "inject-readable-unrelated-code"
    description = (
        "Select one of ten high-readability unrelated code templates per class"
    )

    def __init__(self, template_index: int | None = None) -> None:
        if template_index is not None and not 0 <= template_index < len(
            READABLE_TEMPLATES
        ):
            raise ValueError(
                f"template_index must be between 0 and {len(READABLE_TEMPLATES) - 1}"
            )
        self.template_index = template_index

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        used = existing_identifiers(source)
        edits: list[tuple[int, int, bytes]] = []
        points = select_callable_insertion_points(
            source, context.seed, context.identity, self.slug
        )
        for node, offset in points:
            template_index = self._select_template(context, node.start_byte)
            names: dict[str, str] = {}

            def name(base: str) -> str:
                if base not in names:
                    names[base] = unique_readable_identifier(base, used)
                return names[base]

            snippet = READABLE_TEMPLATES[template_index](name).encode()
            edits.append((offset, offset, snippet))
        return TransformResult(
            apply_edits(source, edits),
            {
                "readable_blocks_injected": len(edits),
                "readable_lines_injected": sum(
                    replacement.count(b"\n") - 1 for _, _, replacement in edits
                ),
                "readable_template_index": (
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
            len(READABLE_TEMPLATES),
            self.slug,
            callable_offset,
            "template",
        )
