"""Shared reporting contract for the frozen-model benchmark experiments."""

import math
from typing import Any, Mapping, Sequence


def unweighted_spearman_average(
    metrics: Mapping[str, Mapping[str, Any]],
    datasets: Sequence[str],
    *,
    value_key: str = "value",
) -> float:
    """Give every requested dataset equal weight; never omit failed metrics."""
    if not datasets or len(set(datasets)) != len(datasets):
        raise ValueError("Benchmark datasets must be nonempty and unique")
    values = []
    for dataset in datasets:
        record = metrics[dataset]
        value = float(record[value_key])
        if int(record["n"]) <= 0 or not math.isfinite(value):
            raise ValueError(f"Invalid benchmark metric for {dataset}: {record}")
        values.append(value)
    return sum(values) / len(values)
