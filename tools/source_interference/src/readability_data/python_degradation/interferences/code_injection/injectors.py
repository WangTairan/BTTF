from __future__ import annotations

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
)
from readability_data.shared.determinism import stable_index, stable_mask

from .common import (
    callable_insertion_points,
    existing_identifiers,
    indent_snippet,
    select_callable_insertion_points,
    unique_opaque_identifier,
    unique_readable_identifier,
)
from .low_readability_templates import LOW_READABILITY_TEMPLATES
from .readable_templates import READABLE_TEMPLATES


class InsertDeadBranches(Interference):
    category, slug = "code-injection", "insert-dead-branches"
    description = "Insert deterministic runtime-dead branches into callable bodies"

    def apply(self, source: str, context: Context) -> Result:
        edits = []
        for point in callable_insertion_points(source):
            mask = stable_mask(
                context.seed + 1, context.identity, point.callable_offset, "literal"
            )
            lines = (
                f"if (({hex(mask)} ^ {hex(mask)}) != 0):",
                "    raise AssertionError()",
            )
            edits.append(
                (
                    point.insertion_offset,
                    point.insertion_offset,
                    indent_snippet(lines, point.indent),
                )
            )
        return Result(
            apply_edits(source, edits), {"dead_branches_inserted": len(edits)}
        )


class InjectReadableCode(Interference):
    category, slug = "code-injection", "inject-readable-unrelated-code"
    description = (
        "Select one of ten high-readability unrelated code templates per class"
    )

    def apply(self, source: str, context: Context) -> Result:
        used = existing_identifiers(source)
        points = select_callable_insertion_points(
            source, context.seed, context.identity, self.slug
        )
        edits, template_index = [], -1
        for point in points:
            template_index = stable_index(
                context.seed,
                context.identity,
                len(READABLE_TEMPLATES),
                self.slug,
                point.callable_offset,
                "template",
            )
            names: dict[str, str] = {}

            def name(base: str) -> str:
                if base not in names:
                    names[base] = unique_readable_identifier(base, used)
                return names[base]

            lines = READABLE_TEMPLATES[template_index](name)
            edits.append(
                (
                    point.insertion_offset,
                    point.insertion_offset,
                    indent_snippet(lines, point.indent),
                )
            )
        return Result(
            apply_edits(source, edits),
            {
                "readable_blocks_injected": len(edits),
                "readable_lines_injected": sum(r.count("\n") for _, _, r in edits),
                "readable_template_index": template_index,
            },
        )


class InjectLowReadabilityCode(Interference):
    category, slug = "code-injection", "inject-low-readability-unrelated-code"
    description = "Select one of ten low-readability unrelated code templates per class"

    def apply(self, source: str, context: Context) -> Result:
        used = existing_identifiers(source)
        points = select_callable_insertion_points(
            source, context.seed, context.identity, self.slug
        )
        edits, template_index = [], -1
        for point in points:
            template_index = stable_index(
                context.seed,
                context.identity,
                len(LOW_READABILITY_TEMPLATES),
                self.slug,
                point.callable_offset,
                "template",
            )
            names: dict[str, str] = {}

            def name(role: str) -> str:
                if role not in names:
                    names[role] = unique_opaque_identifier(
                        used,
                        context.seed,
                        context.identity,
                        point.callable_offset,
                        role,
                    )
                return names[role]

            mask = stable_mask(
                context.seed,
                context.identity,
                point.callable_offset,
                "opaque-injection",
            )
            lines = LOW_READABILITY_TEMPLATES[template_index](name, mask)
            edits.append(
                (
                    point.insertion_offset,
                    point.insertion_offset,
                    indent_snippet(lines, point.indent),
                )
            )
        return Result(
            apply_edits(source, edits),
            {
                "low_readability_blocks_injected": len(edits),
                "low_readability_template_index": template_index,
            },
        )
