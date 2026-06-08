from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import hashlib
import random
import re
from typing import Sequence

from .config import (
    DEFAULT_AST_MAX_COMBINATION_SIZE,
    DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
    DEFAULT_AST_MIN_TOKENS,
    DEFAULT_AST_SAMPLING_SEED,
)
from .masking import MASK_TOKEN, apply_masks, merge_adjacent_spans
from .types import MaskConstraints, MaskSpan, MaskedSequence


NATURAL_LANGUAGE_STRATEGY = "natural_language_stratified_v1"
NATURAL_GRANULARITIES = ("paragraph", "sentence")


@dataclass(frozen=True)
class NaturalCandidate:
    start: int
    end: int
    word_count: int


def natural_language_masks(
    units: Sequence[str],
    constraints: MaskConstraints,
    granularity: str,
    min_words: int = DEFAULT_AST_MIN_TOKENS,
    max_combination_size: int = DEFAULT_AST_MAX_COMBINATION_SIZE,
    max_samples_per_stratum: int | None = DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
    sampling_seed: int = DEFAULT_AST_SAMPLING_SEED,
) -> tuple[MaskedSequence, ...]:
    constraints.validate()
    if granularity not in NATURAL_GRANULARITIES:
        raise ValueError(f"granularity must be one of {NATURAL_GRANULARITIES}")
    if min_words < 1:
        raise ValueError("min_words must be >= 1")
    if max_combination_size < 1:
        raise ValueError("max_combination_size must be >= 1")
    if max_samples_per_stratum is not None and max_samples_per_stratum < 1:
        raise ValueError("max_samples_per_stratum must be >= 1")

    cleaned = tuple(unit for unit in units if unit.strip())
    candidates = tuple(
        NaturalCandidate(index, index + 1, count)
        for index, unit in enumerate(cleaned)
        if (count := _word_count(unit)) >= min_words
    )
    masks = [
        _build_mask(cleaned, (candidate,), granularity)
        for candidate in candidates
    ]
    for count in range(2, min(max_combination_size, len(candidates)) + 1):
        sampled, total = _sample_combinations(
            candidates,
            count,
            max_samples_per_stratum,
            cleaned,
            granularity,
            sampling_seed,
        )
        for selected in sampled:
            masks.append(
                _build_mask(
                    cleaned,
                    selected,
                    granularity,
                    stratum_total=total,
                    stratum_sampled=len(sampled),
                    sampling_seed=sampling_seed,
                )
            )
    return tuple(masks)


def _build_mask(
    units: Sequence[str],
    candidates: tuple[NaturalCandidate, ...],
    granularity: str,
    stratum_total: int | None = None,
    stratum_sampled: int | None = None,
    sampling_seed: int | None = None,
) -> MaskedSequence:
    ordered = tuple(sorted(candidates, key=lambda item: item.start))
    spans = merge_adjacent_spans(MaskSpan(candidate.start, candidate.end) for candidate in ordered)
    return MaskedSequence(
        lines=apply_masks(units, spans),
        spans=spans,
        granularity=len(ordered),
        masked_segments=len(spans),
        selected_segments=len(ordered),
        strategy=NATURAL_LANGUAGE_STRATEGY,
        token_count=sum(candidate.word_count for candidate in ordered),
        ast_role="unit" if len(ordered) == 1 else None,
        ast_granularity=granularity,
        ast_roles=tuple("unit" for _ in ordered),
        stratum_total=stratum_total,
        stratum_sampled=stratum_sampled,
        sampling_seed=sampling_seed,
    )


def _sample_combinations(
    candidates: tuple[NaturalCandidate, ...],
    count: int,
    limit: int | None,
    units: Sequence[str],
    granularity: str,
    sampling_seed: int,
) -> tuple[tuple[tuple[NaturalCandidate, ...], ...], int]:
    all_combinations = tuple(combinations(candidates, count))
    total = len(all_combinations)
    if limit is None or total <= limit:
        return all_combinations, total
    digest = hashlib.sha256("\n".join(units).encode("utf-8")).hexdigest()
    rng = random.Random(f"{sampling_seed}:{digest}:{granularity}:{count}")
    indexes = sorted(rng.sample(range(total), limit))
    return tuple(all_combinations[index] for index in indexes), total


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))
