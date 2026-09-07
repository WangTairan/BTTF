import math

import pytest

from src.methods.cognascore.llm_surprisal import (
    TokenLoss,
    aggregate_surprisal_features,
    identifier_spans,
)


def test_aggregate_surprisal_uses_one_loss_trace_for_all_features():
    source = "int value = x + 1;"
    losses = [
        TokenLoss(1, 4, 9, math.log(2.0)),
        TokenLoss(2, 10, 11, math.log(4.0)),
        TokenLoss(3, 12, 13, math.log(2.0)),
        TokenLoss(4, 14, 15, math.log(8.0)),
        TokenLoss(5, 16, 17, math.log(2.0)),
    ]
    features = aggregate_surprisal_features(
        source,
        losses,
        identifier_spans=[(4, 9), (12, 13)],
        local_block_tokens=2,
        tail_fraction=0.5,
    )

    assert set(features) == {
        "llm__code_perplexity",
        "llm__code_bits_per_byte",
        "llm__local_surprisal_concentration",
        "llm__identifier_excess_surprisal",
    }
    assert features["llm__code_perplexity"] == pytest.approx(3.031433133)
    assert features["llm__local_surprisal_concentration"] >= features["llm__code_bits_per_byte"]


def test_identifier_spans_exclude_keywords_strings_and_comments():
    java = 'int useful = call("ignoredName"); // commentName\n'
    java_values = [java[left:right] for left, right in identifier_spans(java, language="java")]
    assert java_values == ["useful", "call"]

    python = 'value = call("ignored_name")  # comment_name\n'
    python_values = [
        python[left:right] for left, right in identifier_spans(python, language="python")
    ]
    assert python_values == ["value", "call"]


def test_invalid_tail_fraction_fails_loudly():
    with pytest.raises(ValueError, match="tail_fraction"):
        aggregate_surprisal_features(
            "ab",
            [TokenLoss(1, 1, 2, 1.0)],
            identifier_spans=[],
            local_block_tokens=1,
            tail_fraction=0.0,
        )
