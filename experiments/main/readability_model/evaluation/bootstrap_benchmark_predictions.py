"""Bootstrap uncertainty for fixed benchmark predictions.

Rows are resampled independently within each readability dataset.  Each
replicate recomputes the six dataset-specific Spearman correlations and their
unweighted mean, matching the benchmark table's aggregation rule.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


DATASET_ORDER = (
    "mbjp",
    "buse",
    "scalabrino",
    "dorn",
    "schnappinger",
    "jetbrains",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pooled-predictions", type=Path, required=True)
    parser.add_argument("--lodo-predictions", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260923)
    parser.add_argument("-o", "--output", type=Path, required=True)
    return parser.parse_args()


def normalize(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    prediction = "prediction" if "prediction" in frame else "oof_prediction"
    dataset = "dataset" if "dataset" in frame else "held_out_dataset"
    required = {dataset, "readability_score", prediction}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    output = frame[[dataset, "readability_score", prediction]].rename(
        columns={dataset: "dataset", prediction: "prediction"}
    )
    if set(output["dataset"]) != set(DATASET_ORDER):
        raise ValueError(f"Unexpected dataset inventory in {path}")
    return output


def correlation(group: pd.DataFrame, indices: np.ndarray | None = None) -> float:
    if indices is not None:
        group = group.iloc[indices]
    value = spearmanr(
        group["readability_score"].to_numpy(float),
        group["prediction"].to_numpy(float),
    ).statistic
    return float(value)


def bootstrap(frame: pd.DataFrame, rounds: int, seed: int) -> dict:
    groups = {dataset: frame[frame["dataset"] == dataset] for dataset in DATASET_ORDER}
    point = {dataset: correlation(group) for dataset, group in groups.items()}
    point["average"] = float(np.mean(list(point.values())))
    rng = np.random.default_rng(seed)
    replicates = {key: [] for key in (*DATASET_ORDER, "average")}
    valid_rounds = 0
    for _ in range(rounds):
        values = {}
        for dataset, group in groups.items():
            indices = rng.integers(0, len(group), size=len(group))
            value = correlation(group, indices)
            if not np.isfinite(value):
                break
            values[dataset] = value
        else:
            valid_rounds += 1
            for dataset, value in values.items():
                replicates[dataset].append(value)
            replicates["average"].append(float(np.mean(list(values.values()))))
    if valid_rounds < rounds * 0.95:
        raise ValueError(
            f"Only {valid_rounds}/{rounds} bootstrap replicates were defined"
        )
    estimates = {}
    for key in (*DATASET_ORDER, "average"):
        low, high = np.quantile(replicates[key], [0.025, 0.975])
        estimates[key] = {
            "estimate": point[key],
            "ci_95_low": float(low),
            "ci_95_high": float(high),
        }
    return {"valid_rounds": valid_rounds, "estimates": estimates}


def main() -> None:
    args = parse_args()
    if args.rounds < 100:
        raise ValueError("Use at least 100 bootstrap rounds")
    protocols = {
        "pooled_cv": bootstrap(
            normalize(args.pooled_predictions), args.rounds, args.seed
        ),
        "lodo": bootstrap(
            normalize(args.lodo_predictions), args.rounds, args.seed + 1
        ),
    }
    payload = {
        "method": (
            "Dataset-stratified nonparametric bootstrap of fixed predictions; "
            "rows are resampled within each dataset and the six correlations "
            "are averaged with equal dataset weight."
        ),
        "rounds_requested": args.rounds,
        "seed": args.seed,
        "pooled_predictions": str(args.pooled_predictions),
        "lodo_predictions": str(args.lodo_predictions),
        "protocols": protocols,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rows = []
    for protocol, result in protocols.items():
        for dataset, estimate in result["estimates"].items():
            rows.append({"protocol": protocol, "dataset": dataset, **estimate})
    table = pd.DataFrame(rows)
    table.to_csv(args.output / "intervals.csv", index=False)
    print(table.to_string(index=False, float_format=lambda value: f"{value:.6f}"))


if __name__ == "__main__":
    main()
