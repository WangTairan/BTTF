"""Exhaustively search fixed-size one-for-one feature swaps for Progressive."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

from src.experiments.statistics import spearman
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.runners.supervised_ridge import (
    TRAIN_DATASETS,
    fit_ridge,
    load_combined_features,
    training_middle_keep_mask,
)

from .search_progressive_single_additions import (
    DEFAULT_CONFIG,
    DEFAULT_RANKING,
    PROGRESSIVE_DATASET,
    is_cognascore_group,
)


DEFAULT_OUTPUT = Path("results/experiments/cognascore/progressive_feature_swaps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--candidate-rank-max", type=int, default=40)
    parser.add_argument("--minimum-gain", type=float, default=0.01)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = [
        str(value)
        for value in json.loads(args.config.read_text(encoding="utf-8"))["selected_features"]
    ]
    with args.ranking.open(newline="", encoding="utf-8") as handle:
        ranking = list(csv.DictReader(handle))
    candidates = [
        row
        for row in ranking
        if int(row["rank"]) <= args.candidate_rank_max
        and row["feature"] not in selected
        and is_cognascore_group(row["group"])
    ]
    candidate_names = [row["feature"] for row in candidates]
    all_features = selected + candidate_names
    frames = {
        dataset: load_combined_features(
            dataset, args.feature_root, args.embedding_feature_root, all_features
        )
        for dataset in (*TRAIN_DATASETS, PROGRESSIVE_DATASET)
    }
    train = pd.concat([frames[name] for name in TRAIN_DATASETS], ignore_index=True)
    fit_mask = training_middle_keep_mask(train, 0.0)

    def evaluate(features: list[str]) -> tuple[float, float]:
        model = fit_ridge(train, fit_mask, args.ridge_alpha, features)
        values = []
        for dataset in (PROGRESSIVE_DATASET, "scalabrino"):
            frame = frames[dataset]
            scores = model.predict(frame[features].to_numpy(dtype=float))
            values.append(
                spearman(
                    scores.tolist(), frame["readability_score"].astype(float).tolist()
                )
            )
        return float(values[0]), float(values[1])

    baseline_progressive, baseline_scalabrino = evaluate(selected)
    rows = []
    total = len(selected) * len(candidates)
    completed = 0
    for removed in selected:
        for candidate in candidates:
            added = candidate["feature"]
            features = [feature for feature in selected if feature != removed] + [added]
            progressive, scalabrino = evaluate(features)
            rows.append(
                {
                    "removed_feature": removed,
                    "added_feature": added,
                    "added_consensus_rank": int(candidate["rank"]),
                    "added_group": candidate["group"],
                    "progressive_pooled_spearman": progressive,
                    "progressive_gain": progressive - baseline_progressive,
                    "scalabrino_spearman": scalabrino,
                    "scalabrino_gain": scalabrino - baseline_scalabrino,
                }
            )
            completed += 1
            if completed % 25 == 0 or completed == total:
                print(f"swap {completed}/{total}", flush=True)
    rows.sort(
        key=lambda row: (
            float(row["progressive_gain"]),
            float(row["scalabrino_gain"]),
        ),
        reverse=True,
    )
    passing = [row for row in rows if float(row["progressive_gain"]) >= args.minimum_gain]

    args.output.mkdir(parents=True, exist_ok=True)
    for name, values in (("all_swaps.csv", rows), ("passing_swaps.csv", passing)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(values)
    summary = {
        "status": "progressive-supervised development search; not external validation",
        "base_config": str(args.config),
        "candidate_rank_max": args.candidate_rank_max,
        "candidate_features": candidate_names,
        "swap_count": len(rows),
        "baseline_progressive_pooled_spearman": baseline_progressive,
        "baseline_scalabrino_spearman": baseline_scalabrino,
        "minimum_gain": args.minimum_gain,
        "passing_count": len(passing),
        "best": rows[0],
        "passing_swaps": passing,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
