"""Numerical/source-alignment tests without downloading a language model."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from src.methods.readability_model.llm_features.scoring import (
    CommentTarget,
    LazyCausalScorer,
    TokenizedSource,
    TraceConfiguration,
)
from src.methods.readability_model.llm_features.types import TokenLoss


class CharacterTokenizer:
    is_fast = True
    bos_token_id = None
    eos_token_id = 0

    def __call__(self, text, *, add_special_tokens, return_offsets_mapping=False):
        assert add_special_tokens is False
        encoded = {"input_ids": [ord(character) % 15 + 1 for character in text]}
        if return_offsets_mapping:
            encoded["offset_mapping"] = [
                (index, index + 1) for index in range(len(text))
            ]
        return encoded


class SlowSentencePieceTokenizer:
    is_fast = False
    bos_token_id = 1
    eos_token_id = 2

    class PreTokenizer:
        @staticmethod
        def pre_tokenize_str(text):
            return [(text, (0, len(text)))]

    class SentencePiece:
        @staticmethod
        def encode(text, *, return_type):
            assert return_type == "proto"
            pieces = []
            byte_position = 0
            for character in text:
                right = byte_position + len(character.encode("utf-8"))
                pieces.append(
                    SimpleNamespace(
                        id=ord(character) % 31 + 3,
                        begin=byte_position,
                        end=right,
                    )
                )
                byte_position = right
            return SimpleNamespace(pieces=pieces)

    pre_tokenizer = PreTokenizer()
    sp_model = SentencePiece()

    def __call__(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return {"input_ids": [ord(character) % 31 + 3 for character in text]}


class ContextSensitiveModel:
    config = SimpleNamespace(max_position_embeddings=128)

    def __init__(self):
        self.calls = []

    def __call__(self, *, input_ids, use_cache):
        assert use_cache is False
        self.calls.append(input_ids[0].tolist())
        # Every prediction uses only its causal prefix, never a future token.
        favored = input_ids.cumsum(dim=1) % 16
        logits = torch.zeros((*input_ids.shape, 16), dtype=torch.float32)
        logits.scatter_(2, favored.unsqueeze(-1), 2.0)
        return SimpleNamespace(logits=logits)


def scorer_for_test():
    model = ContextSensitiveModel()
    configuration = TraceConfiguration(
        window_tokens=32,
        stride_tokens=24,
        context_target_tokens=8,
        comment_target_tokens=8,
        short_context_tokens=2,
        long_context_tokens=16,
    )
    scorer = LazyCausalScorer(
        configuration, device="cpu", tokenizer=CharacterTokenizer(), model=model
    )
    return scorer, model


def test_whole_source_is_scored_once_with_bounded_windows():
    scorer, model = scorer_for_test()
    source = "int count = 3;\n" * 15
    tokenized = scorer.tokenize(source)
    checkpoints = []
    rows = scorer.score_trace(
        tokenized,
        kind="global",
        checkpoint=lambda kind, progress, new: checkpoints.append(
            (kind, progress, new)
        ),
    )
    assert [row.token_index for row in rows] == list(range(len(source)))
    assert [(row.start, row.end) for row in rows] == tokenized.offsets
    assert np.isfinite([row.nll for row in rows]).all()
    assert all(len(inputs) <= 32 for inputs in model.calls)
    assert model.calls[0][0] == tokenized.boundary_token_id
    assert sum(len(new) for _, _, new in checkpoints) == len(source)
    assert checkpoints[-1][1] == len(source)


def test_paired_context_sweeps_hold_all_target_ids_and_blocks_fixed():
    scorer, model = scorer_for_test()
    tokenized = scorer.tokenize("0123456789abcdef" * 3)
    short = scorer.score_trace(tokenized, kind="short")
    short_calls = list(model.calls)
    model.calls.clear()
    long = scorer.score_trace(tokenized, kind="long")
    assert len(short_calls) == len(model.calls) == 6
    for block, (short_inputs, long_inputs) in enumerate(zip(short_calls, model.calls)):
        targets = tokenized.input_ids[block * 8 : (block + 1) * 8]
        assert short_inputs[-len(targets) :] == long_inputs[-len(targets) :] == targets
    assert short_calls[0] == model.calls[0]
    assert len(short_calls[2]) == 10
    assert len(model.calls[2]) == 24
    assert [row.token_index for row in short] == [row.token_index for row in long]
    assert any(left.nll != right.nll for left, right in zip(short, long))


def test_resume_uses_a_valid_contiguous_prefix_and_checkpoints_each_window():
    scorer, model = scorer_for_test()
    tokenized = scorer.tokenize("f(a, b): return a + b\n" * 5)
    saved = []

    def interrupt_after_first(kind, progress, new):
        assert kind == "global" and progress == 24
        saved.extend(new)
        raise InterruptedError(
            "Simulated process interruption after an atomic checkpoint."
        )

    with pytest.raises(InterruptedError):
        scorer.score_trace(tokenized, kind="global", checkpoint=interrupt_after_first)
    model.calls.clear()
    resumed = scorer.score_trace(tokenized, kind="global", existing_losses=saved)
    assert resumed[:24] == saved
    assert len(resumed) == len(tokenized.input_ids)
    assert model.calls[0][:8] == tokenized.input_ids[16:24]
    completed_only_cache = LazyCausalScorer(scorer.configuration, device="cpu")
    assert (
        completed_only_cache.score_trace(
            tokenized, kind="global", existing_losses=resumed
        )
        == resumed
    )
    assert completed_only_cache.model_loaded is False
    with pytest.raises(ValueError, match="contiguous"):
        scorer.score_trace(
            tokenized, kind="global", existing_losses=[TokenLoss(1, 1, 2, 0.5)]
        )
    with pytest.raises(ValueError, match="block boundary"):
        scorer.score_trace(tokenized, kind="global", existing_losses=saved[:1])


def test_comment_contrast_changes_only_the_fixed_original_prefix():
    scorer, model = scorer_for_test()
    source = "// hi\nx = 1"
    tokenized = scorer.tokenize(source)
    target = CommentTarget(0, 5, 6, len(source))
    checkpoints = []
    effects = scorer.score_comment_effects(
        source,
        tokenized,
        [target],
        checkpoint=lambda progress, effect: checkpoints.append((progress, effect)),
    )
    assert len(effects) == 1
    effect = effects[0]
    targets = tokenized.input_ids[6:]
    present, removed = model.calls
    assert present[-len(targets) :] == removed[-len(targets) :] == targets
    assert present[: -len(targets)] == [0, *tokenized.input_ids[:6]]
    assert removed[: -len(targets)] == [
        0,
        *CharacterTokenizer()("\n", add_special_tokens=False)["input_ids"],
    ]
    assert [row.token_index for row in effect.present_losses] == list(
        range(6, len(source))
    )
    assert [row.token_index for row in effect.removed_losses] == list(
        range(6, len(source))
    )
    assert effect.visible_comment_bytes == 5
    assert checkpoints == [(1, effect)]
    model.calls.clear()
    assert (
        scorer.score_comment_effects(
            source, tokenized, [target], existing_effects=effects
        )
        == effects
    )
    assert not model.calls


def test_unicode_offsets_and_duplicate_bpe_offsets_are_not_reconstructed():
    scorer, _ = scorer_for_test()
    source = "α = β"
    tokenized = scorer.tokenize(source)
    assert tokenized.offsets[0] == (0, 1)
    repeated_bpe = TokenizedSource([1, 2, 3, 4], [(0, 1), (0, 1), (1, 2), (2, 3)], 0)
    rows = scorer.score_trace(repeated_bpe, kind="global")
    assert [(row.start, row.end) for row in rows] == repeated_bpe.offsets
    assert [row.token_index for row in rows] == [0, 1, 2, 3]


def test_slow_sentencepiece_offsets_are_exactly_reconstructed_from_utf8_bytes():
    scorer = LazyCausalScorer(
        TraceConfiguration(),
        device="cpu",
        tokenizer=SlowSentencePieceTokenizer(),
        model=ContextSensitiveModel(),
    )
    source = "aα🙂"
    tokenized = scorer.tokenize(source)
    assert tokenized.offsets == [(0, 1), (1, 2), (2, 3)]
    assert tokenized.input_ids == [ord(character) % 31 + 3 for character in source]


def test_configuration_and_source_failures_are_explicit():
    scorer, model = scorer_for_test()
    with pytest.raises(ValueError, match="pinned"):
        TraceConfiguration(revision="main")
    with pytest.raises(ValueError, match="window"):
        TraceConfiguration(window_tokens=100, stride_tokens=99)
    with pytest.raises(ValueError, match="zero tokens"):
        scorer.tokenize("")
    source = "x = 1\n// later"
    tokenized = scorer.tokenize(source)
    with pytest.raises(ValueError, match="preceding"):
        scorer.score_comment_effects(source, tokenized, [CommentTarget(6, 14, 0, 5)])
    model.config = SimpleNamespace(max_position_embeddings=8)
    with pytest.raises(ValueError, match="model context limit"):
        scorer.score_trace(tokenized, kind="global")


def test_scoring_protocols_have_independent_cache_fingerprints():
    original = TraceConfiguration()
    paired_changed = replace(
        original, context_target_tokens=16, short_context_tokens=16
    )
    assert paired_changed.fingerprint != original.fingerprint
    assert paired_changed.tokenization_fingerprint == original.tokenization_fingerprint
    assert paired_changed.fingerprint_for("global") == original.fingerprint_for(
        "global"
    )
    assert paired_changed.fingerprint_for("short") != original.fingerprint_for("short")
    assert paired_changed.fingerprint_for("long") != original.fingerprint_for("long")
    assert paired_changed.fingerprint_for("comment") == original.fingerprint_for(
        "comment"
    )
    global_changed = replace(original, window_tokens=600, stride_tokens=400)
    assert global_changed.fingerprint_for("global") != original.fingerprint_for(
        "global"
    )
    assert global_changed.tokenization_fingerprint == original.tokenization_fingerprint
    for kind in ("short", "long", "comment"):
        assert global_changed.fingerprint_for(kind) == original.fingerprint_for(kind)
    comment_changed = replace(original, comment_target_tokens=64)
    assert comment_changed.fingerprint_for("comment") != original.fingerprint_for(
        "comment"
    )
    for kind in ("global", "short", "long"):
        assert comment_changed.fingerprint_for(kind) == original.fingerprint_for(kind)
    dtype_changed = replace(original, compute_dtype="float16")
    assert dtype_changed.tokenization_fingerprint == original.tokenization_fingerprint
    assert dtype_changed.fingerprint_for("global") != original.fingerprint_for("global")
    assert original.context_target_tokens == 32
    assert original.comment_target_tokens == 128
    with pytest.raises(ValueError, match="protocol"):
        original.fingerprint_for("other")


def test_comment_target_coverage_is_independent_of_paired_block_size():
    scorer, model = scorer_for_test()
    scorer.configuration = replace(scorer.configuration, context_target_tokens=2)
    source = "// hi\nx = 12345678"
    tokenized = scorer.tokenize(source)
    effects = scorer.score_comment_effects(
        source, tokenized, [CommentTarget(0, 5, 6, len(source))]
    )
    assert len(effects[0].present_losses) == len(effects[0].removed_losses) == 8
    assert len(model.calls) == 2
