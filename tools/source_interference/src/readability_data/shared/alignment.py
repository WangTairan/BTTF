"""Cross-language experimental contract for aligned Java and Python plugins."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterferenceSpec:
    category: str
    slug: str
    target_policy: str
    template_count: int = 0


INTERFERENCE_SPECS = (
    InterferenceSpec("comments", "remove-comments", "all-comments-and-documentation"),
    InterferenceSpec("identifiers", "shorten-identifiers", "all-eligible-bindings"),
    InterferenceSpec("identifiers", "mislead-identifiers", "all-eligible-bindings"),
    InterferenceSpec("identifiers", "garble-identifiers", "all-eligible-bindings"),
    InterferenceSpec(
        "expressions",
        "encode-integer-literals",
        "all-safely-rewritable-decimal-integers-as-hexadecimal",
    ),
    InterferenceSpec("expressions", "invert-conditions", "all-safe-outer-conditions"),
    InterferenceSpec("code-injection", "insert-dead-branches", "every-callable"),
    InterferenceSpec(
        "code-injection", "inject-readable-unrelated-code", "one-callable-per-class", 10
    ),
    InterferenceSpec(
        "code-injection",
        "inject-low-readability-unrelated-code",
        "one-callable-per-class",
        10,
    ),
    InterferenceSpec(
        "layout", "partially-compact-layout", "fixed-40-percent-retain-two"
    ),
    InterferenceSpec(
        "data-flow", "introduce-numeric-intermediates", "all-safe-in-function-integers"
    ),
    InterferenceSpec(
        "data-flow", "inline-intermediate-variables", "all-eligible-single-use"
    ),
    InterferenceSpec("control-flow", "lower-for-to-while", "all-eligible-for-loops"),
)

INTERFERENCE_SPEC_BY_SLUG = {spec.slug: spec for spec in INTERFERENCE_SPECS}

READABLE_CODE_TEMPLATE_FAMILIES = (
    "sum-small-sequence",
    "count-down",
    "count-even-numbers",
    "choose-higher-score",
    "choose-lower-temperature",
    "calculate-average-score",
    "calculate-small-factorial",
    "toggle-feature-state",
    "advance-fibonacci-sequence",
    "measure-travel-distance",
)

LOW_READABILITY_CODE_TEMPLATE_FAMILIES = (
    "xor-cancellation",
    "subtraction-cancellation",
    "bounded-opaque-loop",
    "shift-and-clear",
    "opaque-boolean",
    "nested-false-branch",
    "opaque-multiway-branch",
    "single-cycle-loop",
    "opaque-ternary-chain",
    "redundant-bit-mix",
)
