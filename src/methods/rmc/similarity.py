from difflib import SequenceMatcher
from math import sqrt
import re
from collections import Counter
from typing import Sequence

from .embeddings import embedding_cosine_similarity


def sequence_similarity(original: str, recovered: str) -> float:
    return SequenceMatcher(a=original, b=recovered).ratio()


def cosine_similarity(original: str, recovered: str) -> float:
    return embedding_cosine_similarity(original, recovered)


def exact_match_similarity(original: str, recovered: str) -> float:
    return 1.0 if normalize_for_match(original) == normalize_for_match(recovered) else 0.0


def edit_similarity(original: str, recovered: str) -> float:
    left = tokenize(original)
    right = tokenize(recovered)
    if not left and not right:
        return 1.0
    return 1.0 - levenshtein_distance(left, right) / max(len(left), len(right), 1)


def token_jaccard_similarity(original: str, recovered: str) -> float:
    left = set(tokenize(original))
    right = set(tokenize(recovered))
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def token_cosine_similarity(original: str, recovered: str) -> float:
    left = Counter(tokenize(original))
    right = Counter(tokenize(recovered))

    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0

    common = left.keys() & right.keys()
    dot = sum(left[token] * right[token] for token in common)
    left_norm = sqrt(sum(count * count for count in left.values()))
    right_norm = sqrt(sum(count * count for count in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def bleu_similarity(original: str, recovered: str, max_order: int = 4) -> float:
    reference = tokenize(original)
    candidate = tokenize(recovered)
    if not reference and not candidate:
        return 1.0
    if not reference or not candidate:
        return 0.0

    precisions = []
    for order in range(1, max_order + 1):
        ref_counts = ngram_counts(reference, order)
        cand_counts = ngram_counts(candidate, order)
        overlap = sum(min(count, ref_counts.get(ngram, 0)) for ngram, count in cand_counts.items())
        total = sum(cand_counts.values())
        precisions.append((overlap + 1.0) / (total + 1.0) if total else 1.0)

    log_precision = sum(__import__("math").log(value) for value in precisions) / max_order
    brevity_penalty = 1.0
    if len(candidate) < len(reference):
        brevity_penalty = __import__("math").exp(1.0 - len(reference) / max(len(candidate), 1))
    return brevity_penalty * __import__("math").exp(log_precision)


def rouge_l_similarity(original: str, recovered: str) -> float:
    reference = tokenize(original)
    candidate = tokenize(recovered)
    if not reference and not candidate:
        return 1.0
    if not reference or not candidate:
        return 0.0
    lcs = lcs_length(reference, candidate)
    precision = lcs / len(candidate)
    recall = lcs / len(reference)
    if precision == 0.0 or recall == 0.0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", text)


def normalize_for_match(text: str) -> str:
    return " ".join(tokenize(text))


def levenshtein_distance(left: Sequence[str], right: Sequence[str]) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def ngram_counts(tokens: Sequence[str], order: int) -> Counter[tuple[str, ...]]:
    return Counter(tuple(tokens[index : index + order]) for index in range(len(tokens) - order + 1))


def lcs_length(left: Sequence[str], right: Sequence[str]) -> int:
    previous = [0] * (len(right) + 1)
    for left_token in left:
        current = [0]
        for index, right_token in enumerate(right, start=1):
            current.append(
                previous[index - 1] + 1
                if left_token == right_token
                else max(previous[index], current[index - 1])
            )
        previous = current
    return previous[-1]


def mean(scores: Sequence[float]) -> float:
    if not scores:
        raise ValueError("Cannot compute the mean of an empty score sequence")
    return sum(scores) / len(scores)
