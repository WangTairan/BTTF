"""Exhaustive top-ranked remove-two/add-one development search."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import matthews_corrcoef

from src.experiments.statistics import spearman
from src.methods.cognascore.feature_schema import namespaced_feature
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.runners.supervised_ridge import (
    EMBEDDING_SLUG,
    TRAIN_DATASETS,
    calibrate_classification_threshold,
    fit_ridge,
    load_combined_features,
    training_middle_keep_mask,
)

from .search_progressive_single_additions import DEFAULT_CONFIG, DEFAULT_RANKING


PROGRESSIVE_DATASET = "java_progressive_obfuscation"
REPORT_DATASETS = (*TRAIN_DATASETS, "jetbrains", PROGRESSIVE_DATASET)
DEFAULT_OUTPUT = Path(
    "results/experiments/cognascore/scalabrino_remove2_add1_top50"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--candidate-rank-max", type=int, default=50)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--jetbrains-top", type=int, default=100)
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

    base_columns = pd.read_csv(
        args.feature_root / "scalabrino" / EMBEDDING_SLUG / "features.csv", nrows=1
    ).columns
    embedding_columns = pd.read_csv(
        args.embedding_feature_root / "scalabrino" / EMBEDDING_SLUG / "features.csv",
        nrows=1,
    ).columns
    identity = {"dataset", "task_id", "readability_score"}
    available = {
        namespaced_feature("base", name) for name in base_columns if name not in identity
    } | {
        namespaced_feature("embedding", name)
        for name in embedding_columns
        if name not in identity
    }
    candidates = [
        row
        for row in ranking
        if int(row["rank"]) <= args.candidate_rank_max
        and row["feature"] not in selected
        and row["feature"] in available
    ]
    candidate_names = [row["feature"] for row in candidates]
    all_features = selected + candidate_names
    frames = {
        dataset: load_combined_features(
            dataset, args.feature_root, args.embedding_feature_root, all_features
        )
        for dataset in REPORT_DATASETS
    }
    train = pd.concat([frames[name] for name in TRAIN_DATASETS], ignore_index=True)
    fit_mask = training_middle_keep_mask(train, 0.0)

    def continuous_metrics(model, features: list[str]) -> dict[str, float]:
        metrics = {}
        for dataset in (*TRAIN_DATASETS, PROGRESSIVE_DATASET):
            frame = frames[dataset]
            prediction = model.predict(frame[features].to_numpy(dtype=float))
            metrics[dataset] = float(
                spearman(
                    prediction.tolist(),
                    frame["readability_score"].astype(float).tolist(),
                )
            )
        return metrics

    baseline_model = fit_ridge(train, fit_mask, args.ridge_alpha, selected)
    baseline = continuous_metrics(baseline_model, selected)
    baseline_threshold, _ = calibrate_classification_threshold(
        baseline_model, train, fit_mask, selected
    )
    baseline["jetbrains"] = jetbrains_metric(
        baseline_model, selected, frames["jetbrains"], baseline_threshold
    )

    rows = []
    combinations = list(itertools.combinations(selected, 2))
    total = len(combinations) * len(candidates)
    completed = 0
    for removed in combinations:
        retained = [feature for feature in selected if feature not in removed]
        for candidate in candidates:
            added = candidate["feature"]
            features = [*retained, added]
            model = fit_ridge(train, fit_mask, args.ridge_alpha, features)
            metrics = continuous_metrics(model, features)
            row = {
                "removed_feature_1": removed[0],
                "removed_feature_2": removed[1],
                "added_feature": added,
                "added_consensus_rank": int(candidate["rank"]),
                "added_group": candidate["group"],
            }
            for dataset, value in metrics.items():
                row[dataset] = value
                row[f"delta_{dataset}"] = value - baseline[dataset]
            continuous_costs = {
                dataset: row[f"delta_{dataset}"]
                for dataset in (*TRAIN_DATASETS, PROGRESSIVE_DATASET)
                if dataset != "scalabrino"
            }
            cost_dataset = min(continuous_costs, key=continuous_costs.get)
            row["largest_continuous_cost_dataset"] = cost_dataset
            row["largest_continuous_cost"] = continuous_costs[cost_dataset]
            rows.append(row)
            completed += 1
            if completed % 250 == 0 or completed == total:
                print(f"search {completed}/{total}", flush=True)

    rows.sort(
        key=lambda row: (
            float(row["scalabrino"]),
            float(row[PROGRESSIVE_DATASET]),
            float(row["largest_continuous_cost"]),
        ),
        reverse=True,
    )
    for row in rows[: args.jetbrains_top]:
        removed = {row["removed_feature_1"], row["removed_feature_2"]}
        features = [feature for feature in selected if feature not in removed]
        features.append(row["added_feature"])
        model = fit_ridge(train, fit_mask, args.ridge_alpha, features)
        threshold, _ = calibrate_classification_threshold(
            model, train, fit_mask, features
        )
        value = jetbrains_metric(
            model, features, frames["jetbrains"], threshold
        )
        row["jetbrains"] = value
        row["delta_jetbrains"] = value - baseline["jetbrains"]

    serializable_rows = rows
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "all_combinations.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fields = list(serializable_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(serializable_rows)

    improved = [
        row for row in serializable_rows if float(row["delta_scalabrino"]) > 0.0
    ]
    summary = {
        "status": "Scalabrino-supervised development search; not validation",
        "base_config": str(args.config),
        "base_feature_count": len(selected),
        "result_feature_count": len(selected) - 1,
        "candidate_rank_max": args.candidate_rank_max,
        "candidate_features": candidate_names,
        "combination_count": len(rows),
        "baseline_metrics": baseline,
        "scalabrino_improving_count": len(improved),
        "top_25": serializable_rows[:25],
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def jetbrains_metric(model, features: list[str], frame: pd.DataFrame, threshold: float) -> float:
    prediction = model.predict(frame[features].to_numpy(dtype=float))
    labels = frame["readability_score"].astype(int).to_numpy()
    return float(matthews_corrcoef(labels, (prediction >= threshold).astype(int)))


if __name__ == "__main__":
    main()
