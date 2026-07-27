from __future__ import annotations

import math
from typing import Mapping

from .extractors.python import LexemeExtractor
from .ml_features import extract_features, feature_names


# Frozen from Ridge(alpha=30) on 30 Scalabrino samples selected with seed 8734.
INTERCEPT = 1.178590141
LOG_VOCABULARY_WEIGHT = -0.187275298
NOISE_RATIO_WEIGHT = 0.200950211
FORMULA = (
    "1.178590141 - 0.187275298 * log(1 + vocabulary_size) "
    "+ 0.200950211 * noise_ratio"
)


def score_from_values(vocabulary_size: int, noise_ratio: float) -> float:
    return float(
        INTERCEPT
        + LOG_VOCABULARY_WEIGHT * math.log1p(vocabulary_size)
        + NOISE_RATIO_WEIGHT * noise_ratio
    )


def generalized_readability_score(code: str, cognascore_result: Mapping[str, object]) -> float:
    """Return the frozen two-feature cross-dataset readability prediction."""
    values = extract_features(code, cognascore_result, extractor=LexemeExtractor())
    names = feature_names()
    log_vocabulary = values[names.index("log_vocabulary_size")]
    noise_ratio = values[names.index("noise_ratio")]
    return score_from_log_values(float(log_vocabulary), float(noise_ratio))


def score_from_log_values(log_vocabulary_size: float, noise_ratio: float) -> float:
    return float(
        INTERCEPT
        + LOG_VOCABULARY_WEIGHT * log_vocabulary_size
        + NOISE_RATIO_WEIGHT * noise_ratio
    )
