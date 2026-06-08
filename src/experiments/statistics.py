import math
from statistics import mean
from typing import Sequence


def spearman(left: Sequence[float], right: Sequence[float]) -> float:
    return pearson(average_ranks(left), average_ranks(right))


def matthews_correlation_coefficient(
    predicted: Sequence[int],
    actual: Sequence[int],
) -> float:
    if len(predicted) != len(actual):
        raise ValueError("Classification inputs must have the same length")
    if not predicted:
        return math.nan

    true_positive = sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 1)
    true_negative = sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 0)
    false_positive = sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 0)
    false_negative = sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 1)
    denominator = math.sqrt(
        (true_positive + false_positive)
        * (true_positive + false_negative)
        * (true_negative + false_positive)
        * (true_negative + false_negative)
    )
    if denominator == 0:
        return 0.0
    return (
        true_positive * true_negative - false_positive * false_negative
    ) / denominator


def average_ranks(values: Sequence[float]) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(values):
        next_index = index + 1
        while (
            next_index < len(values)
            and values[ordered[next_index]] == values[ordered[index]]
        ):
            next_index += 1

        average_rank = (index + 1 + next_index) / 2.0
        for rank_index in range(index, next_index):
            ranks[ordered[rank_index]] = average_rank
        index = next_index
    return ranks


def pearson(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Correlation inputs must have the same length")
    if len(left) < 2:
        return math.nan

    left_mean = mean(left)
    right_mean = mean(right)
    left_delta = [value - left_mean for value in left]
    right_delta = [value - right_mean for value in right]
    left_norm = math.sqrt(sum(value * value for value in left_delta))
    right_norm = math.sqrt(sum(value * value for value in right_delta))
    if left_norm == 0 or right_norm == 0:
        return math.nan

    return sum(
        left_value * right_value
        for left_value, right_value in zip(left_delta, right_delta)
    ) / (left_norm * right_norm)
