from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np

from .semantic_anchor_corpus import semantic_anchor_texts_by_category


WHOLE_CODE_CONTEXT_TYPE = "__WHOLE_CODE_CONTEXT__"
ANCHOR_DATASET = "__cognascore_anchor__"
MATH_ANCHOR_TASK = "math_context"
APPLICATION_ANCHOR_TASK = "application_context"
SHORT_IDENTIFIER_GATE_THRESHOLD = 0.03
SHORT_IDENTIFIER_CANDIDATES = frozenset(("a", "b", "c", "d", "e", "i", "j", "k", "m", "n", "x", "y", "z"))
DEFAULT_WHOLE_CODE_CONTEXT_MAX_CHARS = 6000
DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_CHARS = 3000
DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_OVERLAP = 300


@dataclass(frozen=True)
class CodeAnchor:
    name: str
    code: str


def all_context_anchor_texts() -> list[str]:
    return [anchor.code for anchors in context_anchor_groups().values() for anchor in anchors]


def whole_code_context_segments(
    code: str,
    *,
    segment_chars: int = DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_CHARS,
    overlap_chars: int = DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_OVERLAP,
    max_total_chars: int | None = DEFAULT_WHOLE_CODE_CONTEXT_MAX_CHARS,
) -> list[str]:
    text = code if max_total_chars is None or max_total_chars <= 0 else whole_code_context_text(code, max_chars=max_total_chars)
    if segment_chars <= 0 or len(text) <= segment_chars:
        return [text]
    step = max(segment_chars - max(overlap_chars, 0), 1)
    segments = []
    start = 0
    while start < len(text):
        segment = text[start:start + segment_chars]
        if segment:
            segments.append(segment)
        if start + segment_chars >= len(text):
            break
        start += step
    return segments


def whole_code_context_text(code: str, *, max_chars: int | None = DEFAULT_WHOLE_CODE_CONTEXT_MAX_CHARS) -> str:
    if max_chars is None or max_chars <= 0 or len(code) <= max_chars:
        return code
    if max_chars < 32:
        return code[:max_chars]
    marker = "\n\n# ... CognaScore semantic-context middle truncation ...\n\n"
    budget = max_chars - len(marker)
    if budget <= 0:
        return code[:max_chars]
    head_chars = budget // 2
    tail_chars = budget - head_chars
    return code[:head_chars] + marker + code[-tail_chars:]


def context_anchor_groups() -> dict[str, tuple[CodeAnchor, ...]]:
    grouped = semantic_anchor_texts_by_category()
    return {
        MATH_ANCHOR_TASK: tuple(CodeAnchor(name, code) for name, code in grouped["mathematical"]),
        APPLICATION_ANCHOR_TASK: tuple(CodeAnchor(name, code) for name, code in grouped["application"]),
    }


def semantic_context_feature_names() -> list[str]:
    return [
        "short_identifier_prevalence",
        "short_identifier_mathematical_context",
    ]


def semantic_context_features(
    *,
    code_vector: np.ndarray | None,
    code_segment_vectors: list[tuple[str, np.ndarray]] | None = None,
    identifier_lexemes: list[str],
    math_centroid: np.ndarray | None,
    application_centroid: np.ndarray | None,
) -> dict[str, float]:
    ratio = short_identifier_prevalence(identifier_lexemes)
    margin_mean = 0.0
    if ratio > 0.0 and math_centroid is not None and application_centroid is not None:
        segment_vectors = code_segment_vectors or []
        candidate_segment_vectors = [
            vector for text, vector in segment_vectors
            if contains_short_identifier_candidate(text)
        ]
        if candidate_segment_vectors:
            margins = [
                math_application_margin(vector, math_centroid, application_centroid)
                for vector in candidate_segment_vectors
            ]
            margin_mean = float(np.mean(margins))
        elif code_vector is not None:
            margin_mean = math_application_margin(code_vector, math_centroid, application_centroid)
    return {
        "short_identifier_prevalence": ratio,
        "short_identifier_mathematical_context": margin_mean,
    }


def short_identifier_prevalence(identifier_lexemes: list[str]) -> float:
    if not identifier_lexemes:
        return 0.0
    candidate_count = sum(1 for lexeme in identifier_lexemes if lexeme in SHORT_IDENTIFIER_CANDIDATES)
    return candidate_count / len(identifier_lexemes)


def contains_short_identifier_candidate(text: str) -> bool:
    for candidate in SHORT_IDENTIFIER_CANDIDATES:
        if re.search(rf"(?<![A-Za-z0-9_$]){re.escape(candidate)}(?![A-Za-z0-9_$])", text):
            return True
    return False


def math_application_margin(
    vector: np.ndarray,
    math_centroid: np.ndarray,
    application_centroid: np.ndarray,
) -> float:
    x = normalize_vector(vector)
    s_math = float(x @ math_centroid)
    s_application = float(x @ application_centroid)
    return s_math - s_application


def centroid(vectors: list[np.ndarray]) -> np.ndarray | None:
    if not vectors:
        return None
    normalized = np.stack([normalize_vector(vector) for vector in vectors]).astype(np.float64)
    return normalize_vector(np.mean(normalized, axis=0))


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    x = np.asarray(vector, dtype=np.float64)
    norm = float(math.sqrt(float(x @ x)))
    if norm <= 0.0:
        return np.zeros_like(x, dtype=np.float64)
    return x / norm
