"""Original-source aggregation of causal token losses into 47 measurements.

A token's loss is distributed uniformly over its original UTF-8 source bytes.
Overlapping tokenizer offsets (e.g. Unicode byte pieces) accumulate loss, but
covered source bytes are counted only once. For block and subtoken statistics,
each byte is shared equally among tokens covering it. This preserves all
token loss without duplicating the byte denominator. Source roles may overlap
one another; their summaries are therefore not additive contributions.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from src.methods.readability_model.semantic_context import SHORT_IDENTIFIER_CANDIDATES

from .inventory import LLM_FEATURE_NAMES, ROLE_DIFFICULTY_NAMES, ROLE_NAMES
from .types import TokenLoss

if TYPE_CHECKING:
    from .source_spans import SourceAnalysis, SourceSpan


class _SourceLoss:
    def __init__(self, source: str, losses: Sequence[TokenLoss]) -> None:
        if not losses:
            raise ValueError("At least one scored token is required.")
        self.losses = list(losses)
        indices = [row.token_index for row in self.losses]
        if len(set(indices)) != len(indices) or indices != sorted(indices):
            raise ValueError("Token losses must have unique, increasing token indices.")
        starts = [row.start for row in self.losses]
        ends = [row.end for row in self.losses]
        if starts != sorted(starts) or ends != sorted(ends):
            raise ValueError("Tokenizer offsets must preserve source order.")
        self.character_bytes = np.asarray(
            [len(char.encode("utf-8")) for char in source], dtype=float
        )
        self.byte_prefix = np.concatenate(([0.0], np.cumsum(self.character_bytes)))
        counts_delta = np.zeros(len(source) + 1, dtype=np.int64)
        density_delta = np.zeros(len(source) + 1, dtype=float)
        for row in self.losses:
            if not 0 <= row.start < row.end <= len(source):
                raise ValueError(f"Token has invalid original-source offsets: {row}")
            if not math.isfinite(row.nll) or row.nll < 0:
                raise ValueError("Token NLL must be finite and nonnegative.")
            counts_delta[row.start] += 1
            counts_delta[row.end] -= 1
            bits_per_byte = (
                row.nll / math.log(2.0) / self.span_bytes(row.start, row.end)
            )
            density_delta[row.start] += bits_per_byte
            density_delta[row.end] -= bits_per_byte
        self.coverage_count = np.cumsum(counts_delta[:-1])
        covered = self.coverage_count > 0
        self.covered_byte_prefix = np.concatenate(
            ([0.0], np.cumsum(self.character_bytes * covered))
        )
        self.bits_prefix = np.concatenate(
            ([0.0], np.cumsum(np.cumsum(density_delta[:-1]) * self.character_bytes))
        )
        allocated = np.divide(
            self.character_bytes,
            self.coverage_count,
            out=np.zeros_like(self.character_bytes),
            where=covered,
        )
        self.allocated_byte_prefix = np.concatenate(([0.0], np.cumsum(allocated)))
        self.token_bytes = np.asarray(
            [self.allocated_bytes(row.start, row.end) for row in self.losses]
        )
        self.token_bits = np.asarray([row.nll / math.log(2.0) for row in self.losses])

    def span_bytes(self, start: int, end: int) -> float:
        return float(self.byte_prefix[end] - self.byte_prefix[start])

    def allocated_bytes(self, start: int, end: int) -> float:
        return float(
            self.allocated_byte_prefix[end] - self.allocated_byte_prefix[start]
        )

    def totals(self, intervals: Sequence[tuple[int, int]]) -> tuple[float, float]:
        bits = bytes_ = 0.0
        for start, end in _union(intervals):
            bits += float(self.bits_prefix[end] - self.bits_prefix[start])
            bytes_ += float(
                self.covered_byte_prefix[end] - self.covered_byte_prefix[start]
            )
        return bits, bytes_

    def q(self, intervals: Sequence[tuple[int, int]]) -> float | None:
        bits, bytes_ = self.totals(intervals)
        return bits / bytes_ if bytes_ > 0 else None

    def piece_totals(self, row: TokenLoss, start: int, end: int) -> tuple[float, float]:
        left, right = max(start, row.start), min(end, row.end)
        if left >= right:
            return 0.0, 0.0
        bits = (
            row.nll
            / math.log(2.0)
            * self.span_bytes(left, right)
            / self.span_bytes(row.start, row.end)
        )
        return bits, self.allocated_bytes(left, right)


def _union(intervals: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for start, end in sorted(set(intervals)):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def _tail(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    return float(
        np.mean(
            sorted(values, reverse=True)[: max(1, math.ceil(len(values) * fraction))]
        )
    )


def _mean(values: Sequence[float]) -> float | None:
    return float(np.mean(values)) if values else None


def _occurrence_values(loss: _SourceLoss, spans: Sequence[SourceSpan]) -> list[float]:
    return [
        value
        for span in spans
        if (value := loss.q([(span.start, span.end)])) is not None
    ]


def _gini(values: np.ndarray) -> float:
    total = float(np.sum(values))
    if total == 0:
        return 0.0
    ordered = np.sort(values)
    n = len(ordered)
    return float(np.dot(2 * np.arange(1, n + 1) - n - 1, ordered) / (n * total))


def aggregate_features(
    source: str,
    token_losses: Sequence[TokenLoss],
    analysis: SourceAnalysis,
    *,
    local_block_tokens: int = 32,
    tail_fraction: float = 0.2,
    short_context_losses: Sequence[TokenLoss] | None = None,
    long_context_losses: Sequence[TokenLoss] | None = None,
    context_target_tokens: int = 32,
    short_context_tokens: int = 32,
    comment_gain: float | None = None,
    comment_gain_source_density: float = 0.0,
) -> tuple[dict[str, float | None], dict]:
    """Return schema-stable scalars and coverage metadata, without model fitting.

    Missing/structurally unavailable categories are ``None``, not artificial
    zero difficulty. A single occurrence has a mathematically defined zero
    population standard deviation. Context traces must score identical tokens.
    Context gain describes prefixes preceding matched target blocks, with the
    preceding tokens within each target block shared by both predictions. An
    occurrence is eligible only when every intersecting target token belongs
    to a block with more preceding source tokens than the short-prefix budget.
    Early targets without extra measurable context are missing, not zero gain.
    """
    if local_block_tokens < 1:
        raise ValueError("local_block_tokens must be positive.")
    if not 0 < tail_fraction <= 1:
        raise ValueError("tail_fraction must be in (0, 1].")
    if context_target_tokens < 1:
        raise ValueError("context_target_tokens must be positive.")
    if short_context_tokens < 0:
        raise ValueError("short_context_tokens must be nonnegative.")
    loss = _SourceLoss(source, token_losses)
    features: dict[str, float | None] = dict.fromkeys(LLM_FEATURE_NAMES)
    roles = {role: [] for role in ROLE_NAMES}
    seen = set()
    identifier_bindings = {}
    for span in analysis.spans:
        if span.role not in roles:
            raise ValueError(f"Unknown source role: {span.role}")
        if not 0 <= span.start < span.end <= len(source):
            raise ValueError(f"Invalid original-source role span: {span}")
        if span.role not in analysis.roles_available:
            raise ValueError(f"Source spans contradict unavailable role: {span.role}")
        if span.role == "identifier":
            coordinate = (span.start, span.end)
            if (
                coordinate in identifier_bindings
                and identifier_bindings[coordinate] != span.binding
            ):
                raise ValueError(
                    "One identifier occurrence has contradictory bindings."
                )
            identifier_bindings[coordinate] = span.binding
        key = (span.role, span.start, span.end, span.binding)
        if key not in seen:
            roles[span.role].append(span)
            seen.add(key)
    for spans in roles.values():
        spans.sort(key=lambda span: (span.start, span.end))
    metadata = {
        "token_count": len(token_losses),
        "covered_utf8_bytes": int(loss.covered_byte_prefix[-1]),
        "roles": {},
        "source_analysis": analysis.metadata,
    }
    metadata["byte_attribution"] = {
        "role_denominator": "union of covered original UTF-8 source bytes",
        "token_bits": "uniform per-byte allocation within each original token span",
        "overlapping_offset_bytes": "shared equally among covering tokens for block and subtoken denominators",
    }
    mean_nll = float(np.mean([row.nll for row in token_losses]))
    if mean_nll >= math.log(np.finfo(float).max):
        raise OverflowError("Mean token loss is too large to represent perplexity.")
    features["llm__code_perplexity"] = math.exp(mean_nll)
    global_q = float(np.sum(loss.token_bits) / np.sum(loss.token_bytes))
    features["llm__code_bits_per_byte"] = global_q
    blocks = np.asarray(
        [
            float(
                np.sum(loss.token_bits[start : start + local_block_tokens])
                / np.sum(loss.token_bytes[start : start + local_block_tokens])
            )
            for start in range(0, len(token_losses), local_block_tokens)
        ]
    )
    block_tail = _tail(blocks.tolist(), tail_fraction)
    features["llm__local_surprisal_concentration"] = block_tail
    for role, spans in roles.items():
        intervals = [(span.start, span.end) for span in spans]
        values = _occurrence_values(loss, spans)
        _, byte_count = loss.totals(intervals)
        metadata["roles"][role] = {
            "available": role in analysis.roles_available,
            "occurrence_count": len(spans),
            "scored_occurrence_count": len(values),
            "covered_utf8_bytes": byte_count,
        }
        if values and role in ROLE_DIFFICULTY_NAMES:
            mean_name = (
                "llm__assignment_value_surprisal"
                if role == "assignment_rhs"
                else f"llm__{role}__bpb_mean"
            )
            tail_name = (
                "llm__literal_tail_surprisal"
                if role == "literal"
                else f"llm__{role}__bpb_tail_mean"
            )
            variation_name = (
                "llm__declaration_surprisal_variation"
                if role == "declaration_header"
                else f"llm__{role}__bpb_std"
            )
            features[mean_name] = loss.q(intervals)
            features[tail_name] = _tail(values, tail_fraction)
            features[variation_name] = float(np.std(values))
    features["llm__block_bpb_std"] = float(np.std(blocks))
    features["llm__block_tail_to_global_ratio"] = (
        block_tail / global_q if global_q > 0 else None
    )
    jumps = np.abs(np.diff(blocks))
    if len(jumps):
        features["llm__block_surprisal_jump_mean"] = float(np.mean(jumps))
        features["llm__block_surprisal_jump_q90"] = float(np.quantile(jumps, 0.9))
    longest = current = 0
    for hot in blocks > np.quantile(blocks, 0.8):
        current = current + 1 if hot else 0
        longest = max(longest, current)
    features["llm__hard_block_run_ratio"] = longest / len(blocks)
    features["llm__block_bpb_gini"] = _gini(blocks)
    metadata["blocks"] = {
        "count": len(blocks),
        "tokens_per_block": local_block_tokens,
        "tail_fraction": tail_fraction,
    }

    identifiers = roles["identifier"]
    short = [
        span
        for span in identifiers
        if source[span.start : span.end] in SHORT_IDENTIFIER_CANDIDATES
    ]
    features["llm__short_identifier_bpb"] = loss.q(
        [(span.start, span.end) for span in short]
    )
    bindings: dict[str, list[SourceSpan]] = {}
    for span in identifiers:
        if span.binding is not None:
            bindings.setdefault(span.binding, []).append(span)
    first = [spans[0] for spans in bindings.values()]
    reused_bindings = [spans for spans in bindings.values() if len(spans) > 1]
    later = [span for spans in reused_bindings for span in spans[1:]]
    features["llm__identifier_first_occurrence_bpb"] = loss.q(
        [(span.start, span.end) for span in first]
    )
    features["llm__identifier_reuse_bpb"] = loss.q(
        [(span.start, span.end) for span in later]
    )
    features["llm__identifier_reuse_tail_bpb"] = _tail(
        _occurrence_values(loss, later), tail_fraction
    )
    increases, within_stds = [], []
    for spans in reused_bindings:
        values = [loss.q([(span.start, span.end)]) for span in spans]
        if all(value is not None for value in values):
            increases.append(
                float(np.mean([max(value - values[0], 0.0) for value in values[1:]]))
            )
            within_stds.append(float(np.std(values)))
    features["llm__identifier_reuse_difficulty_increase"] = _mean(increases)
    features["llm__identifier_within_binding_bpb_std"] = _mean(within_stds)
    first_piece_bits = first_piece_bytes = continuation_bits = continuation_bytes = 0.0
    first_piece_count = continuation_count = token_cursor = 0
    for span in identifiers:
        while (
            token_cursor < len(loss.losses)
            and loss.losses[token_cursor].end <= span.start
        ):
            token_cursor += 1
        token_stop = token_cursor
        while (
            token_stop < len(loss.losses) and loss.losses[token_stop].start < span.end
        ):
            token_stop += 1
        pieces = [
            row for row in loss.losses[token_cursor:token_stop] if row.end > span.start
        ]
        for position, row in enumerate(pieces):
            bits, bytes_ = loss.piece_totals(row, span.start, span.end)
            if position == 0:
                first_piece_bits += bits
                first_piece_bytes += bytes_
                first_piece_count += 1
            else:
                continuation_bits += bits
                continuation_bytes += bytes_
                continuation_count += 1
    features["llm__identifier_onset_surprisal"] = (
        first_piece_bits / first_piece_bytes if first_piece_bytes > 0 else None
    )
    features["llm__identifier_continuation_bpb"] = (
        continuation_bits / continuation_bytes if continuation_bytes > 0 else None
    )
    metadata["identifiers"] = {
        "occurrence_count": len(identifiers),
        "short_candidate_count": len(short),
        "confirmed_binding_count": len(bindings),
        "reused_binding_count": len(reused_bindings),
        "first_confirmed_occurrence_count": len(first),
        "later_confirmed_occurrence_count": len(later),
        "first_subtoken_count": first_piece_count,
        "continuation_subtoken_count": continuation_count,
    }

    if (short_context_losses is None) != (long_context_losses is None):
        raise ValueError("Short and long context losses must be supplied together.")
    metadata["context"] = {
        "available": short_context_losses is not None,
        "target_block_tokens": context_target_tokens,
        "short_prefix_tokens": short_context_tokens,
        "prefix_policy": "matched source target blocks; only the prefix preceding each block differs; within-block teacher-forced tokens are shared",
        "eligibility_policy": "all tokens intersecting an occurrence must satisfy floor(token_index/target_block_tokens)*target_block_tokens > short_prefix_tokens",
    }
    if short_context_losses is not None:
        short_loss, long_loss = (
            _SourceLoss(source, short_context_losses),
            _SourceLoss(source, long_context_losses),
        )
        short_coordinates = [
            (row.token_index, row.start, row.end) for row in short_loss.losses
        ]
        long_coordinates = [
            (row.token_index, row.start, row.end) for row in long_loss.losses
        ]
        global_coordinates = [
            (row.token_index, row.start, row.end) for row in loss.losses
        ]
        if (
            short_coordinates != long_coordinates
            or short_coordinates != global_coordinates
        ):
            raise ValueError(
                "Context gain requires identical original target tokens and offsets "
                "in global, short and long traces."
            )
        eligible_tokens = [
            (row.token_index // context_target_tokens) * context_target_tokens
            > short_context_tokens
            for row in loss.losses
        ]
        ineligible_delta = np.zeros(len(source) + 1, dtype=np.int64)
        for row, eligible in zip(loss.losses, eligible_tokens):
            if not eligible:
                ineligible_delta[row.start] += 1
                ineligible_delta[row.end] -= 1
        ineligible_character_prefix = np.concatenate(
            ([0], np.cumsum(np.cumsum(ineligible_delta[:-1]) > 0))
        )
        metadata["context"]["eligible_token_count"] = sum(eligible_tokens)
        metadata["context"]["ineligible_token_count"] = len(loss.losses) - sum(
            eligible_tokens
        )
        context_roles = [("identifier", identifiers), ("short_identifier", short)]
        context_roles.extend(
            (role, roles[role])
            for role in (
                "call_target",
                "expression",
                "assignment_rhs",
                "control_header",
            )
        )
        for name, spans in context_roles:
            gains = []
            eligible_occurrences = skipped_no_extra_prefix = 0
            for span in spans:
                if (
                    ineligible_character_prefix[span.end]
                    > ineligible_character_prefix[span.start]
                ):
                    skipped_no_extra_prefix += 1
                    continue
                eligible_occurrences += 1
                short_q = short_loss.q([(span.start, span.end)])
                long_q = long_loss.q([(span.start, span.end)])
                if short_q is not None and long_q is not None:
                    gains.append(short_q - long_q)
            feature_name = (
                "llm__short_identifier_context_dependence"
                if name == "short_identifier"
                else f"llm__{name}_context_gain_mean"
            )
            features[feature_name] = _mean(gains)
            metadata["context"][f"{name}_scored_occurrences"] = len(gains)
            metadata["context"][f"{name}_eligible_occurrences"] = eligible_occurrences
            metadata["context"][f"{name}_skipped_no_extra_prefix"] = (
                skipped_no_extra_prefix
            )
            metadata["context"][f"{name}_skipped_no_scored_bytes"] = (
                eligible_occurrences - len(gains)
            )
            if name == "identifier" and gains:
                features["llm__identifier_context_gain_q10"] = float(
                    np.quantile(gains, 0.1)
                )
    if comment_gain is not None:
        if not math.isfinite(comment_gain):
            raise ValueError("Comment prediction gain must be finite when supplied.")
        if not roles["comment"]:
            raise ValueError(
                "Comment prediction gain cannot be supplied without a source comment."
            )
    if not math.isfinite(comment_gain_source_density):
        raise ValueError("Comment prediction-gain source density must be finite.")
    if comment_gain_source_density != 0.0 and not roles["comment"]:
        raise ValueError(
            "Nonzero global comment prediction gain requires a source comment."
        )
    features["llm__comment_code_prediction_gain"] = comment_gain
    features["llm__comment_code_prediction_gain_source_density"] = (
        comment_gain_source_density
    )
    metadata["context"]["comment_gain_available"] = comment_gain is not None
    metadata["context"]["comment_gain_source_density_is_structural_zero"] = (
        comment_gain is None
    )
    if set(features) != set(LLM_FEATURE_NAMES):
        raise AssertionError("LLM feature aggregation does not match its inventory.")
    return features, metadata
