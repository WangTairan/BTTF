import math
from dataclasses import dataclass, field

import pytest

from src.methods.readability_model.llm_features.aggregate import aggregate_features
from src.methods.readability_model.llm_features.inventory import (
    LLM_FEATURE_INVENTORY,
    LLM_FEATURE_NAMES,
    ROLE_NAMES,
)
from src.methods.readability_model.llm_features.types import TokenLoss


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    role: str
    binding: str | None = None


@dataclass
class Analysis:
    spans: list[Span]
    roles_available: set[str] = field(default_factory=lambda: set(ROLE_NAMES))
    metadata: dict = field(default_factory=dict)


def losses_for_characters(source, bits):
    return [
        TokenLoss(index, index, index + 1, value * math.log(2))
        for index, value in enumerate(bits)
    ]


def test_inventory_has_47_unique_interpretable_definitions():
    assert len(LLM_FEATURE_NAMES) == len(set(LLM_FEATURE_NAMES)) == 47
    assert all(
        item.name.startswith("llm__") and item.formula and item.description
        for item in LLM_FEATURE_INVENTORY
    )
    assert not any("excess" in name for name in LLM_FEATURE_NAMES)
    assert not any(name.startswith("llm__comment__bpb_") for name in LLM_FEATURE_NAMES)


def test_binding_role_blocks_and_context_gain_numerically():
    source = "a+a"
    losses = losses_for_characters(source, [1, 2, 3])
    analysis = Analysis(
        [
            Span(0, 1, "identifier", "local-a"),
            Span(2, 3, "identifier", "local-a"),
            Span(0, 3, "expression"),
        ]
    )
    short = losses_for_characters(source, [2, 3, 4])
    features, metadata = aggregate_features(
        source,
        losses,
        analysis,
        local_block_tokens=1,
        short_context_losses=short,
        long_context_losses=losses,
        context_target_tokens=2,
        short_context_tokens=0,
    )
    expected = {
        "code_perplexity": 4,
        "code_bits_per_byte": 2,
        "local_surprisal_concentration": 3,
        "identifier__bpb_mean": 2,
        "identifier__bpb_tail_mean": 3,
        "identifier__bpb_std": 1,
        "block_tail_to_global_ratio": 1.5,
        "block_surprisal_jump_mean": 1,
        "block_surprisal_jump_q90": 1,
        "hard_block_run_ratio": 1 / 3,
        "block_bpb_gini": 2 / 9,
        "identifier_first_occurrence_bpb": 1,
        "identifier_reuse_bpb": 3,
        "identifier_reuse_tail_bpb": 3,
        "identifier_reuse_difficulty_increase": 2,
        "identifier_within_binding_bpb_std": 1,
        "identifier_onset_difficulty": 2,
        "identifier_context_gain_mean": 1,
        "identifier_context_gain_q10": 1,
        "short_identifier_context_dependence": 1,
    }
    for name, value in expected.items():
        assert features[f"llm__{name}"] == pytest.approx(value)
    assert features["llm__identifier_continuation_bpb"] is None
    assert features["llm__comment_code_prediction_gain"] is None
    assert features["llm__comment_code_prediction_gain_source_density"] == 0.0
    assert features["llm__expression_context_gain_mean"] is None
    assert metadata["identifiers"]["confirmed_binding_count"] == 1
    assert metadata["roles"]["identifier"]["covered_utf8_bytes"] == 2
    assert metadata["context"]["identifier_eligible_occurrences"] == 1
    assert metadata["context"]["identifier_skipped_no_extra_prefix"] == 1


def test_role_union_does_not_double_count_overlapping_source():
    source = "abcd"
    features, metadata = aggregate_features(
        source,
        losses_for_characters(source, [1, 2, 3, 4]),
        Analysis([Span(0, 3, "expression"), Span(1, 4, "expression")]),
    )
    assert features["llm__expression__bpb_mean"] == pytest.approx(2.5)
    assert features["llm__expression__bpb_tail_mean"] == pytest.approx(3)
    assert features["llm__expression__bpb_std"] == pytest.approx(0.5)
    assert metadata["roles"]["expression"]["covered_utf8_bytes"] == 4


def test_duplicate_unicode_offsets_accumulate_bits_but_not_bytes():
    source = "aéz"
    rows = [
        TokenLoss(0, 0, 1, math.log(2)),
        TokenLoss(1, 1, 2, 2 * math.log(2)),
        TokenLoss(2, 1, 2, math.log(2)),
        TokenLoss(3, 2, 3, math.log(2)),
    ]
    features, metadata = aggregate_features(
        source,
        rows,
        Analysis([Span(1, 2, "identifier", "unicode")]),
        local_block_tokens=1,
    )
    assert features["llm__code_bits_per_byte"] == pytest.approx(5 / 4)
    assert features["llm__identifier__bpb_mean"] == pytest.approx(3 / 2)
    assert features["llm__identifier_onset_difficulty"] == pytest.approx(2)
    assert features["llm__identifier_continuation_bpb"] == pytest.approx(1)
    assert metadata["covered_utf8_bytes"] == 4


def test_straddling_token_loss_is_fractionally_allocated_to_identifier():
    features, _ = aggregate_features(
        " a ",
        [TokenLoss(0, 0, 3, 3 * math.log(2))],
        Analysis([Span(1, 2, "identifier")]),
    )
    assert features["llm__identifier__bpb_mean"] == pytest.approx(1)
    assert features["llm__identifier_onset_difficulty"] == pytest.approx(1)
    assert features["llm__identifier_first_occurrence_bpb"] is None


def test_equal_names_in_separate_scopes_do_not_create_a_shared_binding():
    source = "a a a a"
    rows = [
        TokenLoss(i, start, start + 1, bits * math.log(2))
        for i, (start, bits) in enumerate(zip((0, 2, 4, 6), (1, 2, 10, 9)))
    ]
    analysis = Analysis(
        [
            Span(0, 1, "identifier", "scope1:a"),
            Span(2, 3, "identifier", "scope1:a"),
            Span(4, 5, "identifier", "scope2:a"),
            Span(6, 7, "identifier", "scope2:a"),
        ]
    )
    features, metadata = aggregate_features(source, rows, analysis)
    assert features["llm__identifier_first_occurrence_bpb"] == pytest.approx(5.5)
    assert features["llm__identifier_reuse_bpb"] == pytest.approx(5.5)
    assert features["llm__identifier_reuse_difficulty_increase"] == pytest.approx(0.5)
    assert features["llm__identifier_within_binding_bpb_std"] == pytest.approx(0.5)
    assert metadata["identifiers"]["confirmed_binding_count"] == 2


def test_absence_and_structural_unavailability_remain_distinct_in_metadata():
    features, metadata = aggregate_features(
        "+", losses_for_characters("+", [0]), Analysis([], {"comment"})
    )
    assert "llm__comment__bpb_std" not in features
    assert features["llm__identifier__bpb_std"] is None
    assert metadata["roles"]["comment"]["available"] is True
    assert metadata["roles"]["identifier"]["available"] is False
    assert features["llm__block_bpb_std"] == 0
    assert features["llm__block_surprisal_jump_mean"] is None
    assert features["llm__block_tail_to_global_ratio"] is None
    assert features["llm__block_bpb_gini"] == 0


def test_same_role_duplicate_span_is_counted_once():
    features, metadata = aggregate_features(
        "x",
        losses_for_characters("x", [1]),
        Analysis([Span(0, 1, "identifier", "x"), Span(0, 1, "identifier", "x")]),
    )
    assert features["llm__identifier__bpb_std"] == 0
    assert features["llm__identifier_reuse_bpb"] is None
    assert metadata["roles"]["identifier"]["occurrence_count"] == 1


def test_context_targets_must_match_exactly_and_missing_gains_are_not_zero():
    source = "ab"
    rows = losses_for_characters(source, [1, 1])
    analysis = Analysis([Span(0, 2, "identifier")])
    with pytest.raises(ValueError, match="supplied together"):
        aggregate_features(source, rows, analysis, short_context_losses=rows)
    with pytest.raises(ValueError, match="identical original target"):
        aggregate_features(
            source,
            rows,
            analysis,
            short_context_losses=rows[:1],
            long_context_losses=rows,
        )
    with pytest.raises(ValueError, match="in global, short and long traces"):
        aggregate_features(
            source,
            rows,
            analysis,
            short_context_losses=rows[:1],
            long_context_losses=rows[:1],
        )
    features, _ = aggregate_features(source, rows, analysis)
    assert features["llm__identifier_context_gain_mean"] is None


def test_context_gain_uses_only_complete_occurrences_with_extra_source_prefix():
    source = "a" * 68
    global_rows = losses_for_characters(source, [1] * len(source))
    short_bits = [51] * 64 + [0.5, 1, 3, 3]
    short_rows = losses_for_characters(source, short_bits)
    analysis = Analysis(
        [
            Span(0, 1, "identifier"),
            Span(32, 33, "identifier"),
            Span(63, 65, "identifier"),
            Span(64, 65, "identifier"),
            Span(66, 68, "identifier"),
            Span(63, 65, "expression"),
            Span(64, 65, "assignment_rhs"),
            Span(64, 65, "call_target"),
            Span(66, 68, "control_header"),
        ]
    )
    features, metadata = aggregate_features(
        source,
        global_rows,
        analysis,
        short_context_losses=short_rows,
        long_context_losses=global_rows,
    )
    assert features["llm__identifier_context_gain_mean"] == pytest.approx(0.75)
    assert features["llm__identifier_context_gain_q10"] == pytest.approx(-0.25)
    assert features["llm__short_identifier_context_dependence"] == pytest.approx(-0.5)
    assert features["llm__expression_context_gain_mean"] is None
    assert features["llm__assignment_rhs_context_gain_mean"] == pytest.approx(-0.5)
    assert features["llm__call_target_context_gain_mean"] == pytest.approx(-0.5)
    assert features["llm__control_header_context_gain_mean"] == pytest.approx(2)
    assert metadata["context"]["eligible_token_count"] == 4
    assert metadata["context"]["identifier_eligible_occurrences"] == 2
    assert metadata["context"]["identifier_skipped_no_extra_prefix"] == 3
    assert metadata["context"]["expression_skipped_no_extra_prefix"] == 1


def test_early_occurrences_are_unmeasurable_not_zero_context_gain():
    rows = losses_for_characters("x", [1])
    features, metadata = aggregate_features(
        "x",
        rows,
        Analysis([Span(0, 1, "identifier")]),
        short_context_losses=rows,
        long_context_losses=rows,
    )
    assert features["llm__identifier_context_gain_mean"] is None
    assert features["llm__identifier_context_gain_q10"] is None
    assert features["llm__short_identifier_context_dependence"] is None
    assert metadata["context"]["identifier_eligible_occurrences"] == 0
    assert metadata["context"]["identifier_skipped_no_extra_prefix"] == 1


@pytest.mark.parametrize(
    "parameters", [{"context_target_tokens": 0}, {"short_context_tokens": -1}]
)
def test_invalid_context_aggregation_parameters_fail(parameters):
    with pytest.raises(ValueError):
        aggregate_features(
            "a", losses_for_characters("a", [1]), Analysis([]), **parameters
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1])
def test_nonfinite_or_negative_loss_fails_loudly(bad):
    with pytest.raises(ValueError, match="finite and nonnegative"):
        aggregate_features("a", [TokenLoss(0, 0, 1, bad)], Analysis([]))


def test_invalid_source_offsets_and_unknown_roles_fail_loudly():
    with pytest.raises(ValueError, match="invalid original-source offsets"):
        aggregate_features("a", [TokenLoss(0, 0, 2, 1)], Analysis([]))
    with pytest.raises(ValueError, match="Unknown source role"):
        aggregate_features(
            "a", [TokenLoss(0, 0, 1, 1)], Analysis([Span(0, 1, "normalized_chunk")])
        )


def test_unordered_token_offsets_and_contradictory_bindings_fail_loudly():
    with pytest.raises(ValueError, match="preserve source order"):
        aggregate_features(
            "ab", [TokenLoss(0, 1, 2, 1), TokenLoss(1, 0, 1, 1)], Analysis([])
        )
    with pytest.raises(ValueError, match="contradictory bindings"):
        aggregate_features(
            "a",
            [TokenLoss(0, 0, 1, 1)],
            Analysis(
                [Span(0, 1, "identifier", "first"), Span(0, 1, "identifier", "second")]
            ),
        )


def test_comment_gain_requires_a_comment_and_preserves_negative_values():
    rows = losses_for_characters("#hi", [1, 1, 1])
    with pytest.raises(ValueError, match="without a source comment"):
        aggregate_features("#hi", rows, Analysis([]), comment_gain=0.1)
    features, _ = aggregate_features(
        "#hi",
        rows,
        Analysis([Span(0, 3, "comment")]),
        comment_gain=-0.2,
        comment_gain_source_density=-0.1,
    )
    assert features["llm__comment_code_prediction_gain"] == -0.2
    assert features["llm__comment_code_prediction_gain_source_density"] == -0.1


def test_global_comment_gain_is_defined_without_comments_and_rejects_false_effect():
    rows = losses_for_characters("abc", [1, 1, 1])
    features, metadata = aggregate_features("abc", rows, Analysis([]))
    assert features["llm__comment_code_prediction_gain_source_density"] == 0.0
    assert (
        metadata["context"]["comment_gain_source_density_is_structural_zero"]
        is True
    )
    with pytest.raises(ValueError, match="requires a source comment"):
        aggregate_features(
            "abc", rows, Analysis([]), comment_gain_source_density=0.1
        )
