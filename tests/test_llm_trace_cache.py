import math

import pytest

from src.methods.readability_model.llm_features.cache import LLMTraceCache, fingerprint
from src.methods.readability_model.llm_features.types import TokenLoss


def test_trace_checkpoints_survive_interruption_and_statistics_changes(tmp_path):
    path = tmp_path / "traces.sqlite"
    rows = [TokenLoss(0, 0, 1, math.log(2)), TokenLoss(1, 1, 2, math.log(4))]
    with LLMTraceCache(path) as cache:
        cache.put_tokenization(
            "s",
            "t",
            {
                "input_ids": [10, 11],
                "offsets": [[0, 1], [1, 2]],
                "boundary_token_id": 0,
            },
        )
        cache.append_window("s", "t", "global", 1, rows[:1])
    with LLMTraceCache(path) as cache:
        assert cache.get_trace("s", "t", "global") == rows[:1]
        cache.append_window("s", "t", "global", 2, rows[1:])
        cache.put_features("s", "old-stats", {"llm__x": 1.0}, {"n": 2})
        assert cache.get_features("s", "new-stats") is None
        assert cache.get_trace("s", "t", "global") == rows
        assert cache.get_features("s", "old-stats")["features"] == {"llm__x": 1.0}
        cache.put_comment_effect("s", "t", "c", {"gain": None})
        assert cache.get_comment_effects("s", "t") == {"c": {"gain": None}}


def test_invalid_checkpoint_and_changed_tokenization_fail(tmp_path):
    with LLMTraceCache(tmp_path / "traces.sqlite") as cache:
        with pytest.raises(ValueError, match="continue"):
            cache.append_window("s", "t", "global", 2, [TokenLoss(1, 1, 2, 1.0)])
        with pytest.raises(ValueError, match="invalid"):
            cache.append_window(
                "s", "t", "global", 1, [TokenLoss(0, 0, 1, float("nan"))]
            )
        payload = {"input_ids": [1], "offsets": [[0, 1]], "boundary_token_id": 0}
        cache.put_tokenization("s", "t", payload)
        with pytest.raises(ValueError, match="changed"):
            cache.put_tokenization("s", "t", {**payload, "input_ids": [2]})


def test_fingerprint_is_deterministic():
    assert fingerprint({"a": 1, "b": 2}) == fingerprint({"b": 2, "a": 1})
    assert fingerprint({"a": 1}) != fingerprint({"a": 2})
