"""Diagnose and optimize Progressive within-group Spearman with one-for-one swaps.

This experiment directly uses the Progressive dataset as a development objective.
Its results are diagnostics, not external-validation evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.cognascore.evaluate_progressive_obfuscation import (
    build_predictions,
    summarize,
)
from experiments.cognascore.search_progressive_single_additions import DEFAULT_RANKING
from experiments.cognascore.search_scalabrino_remove2_add1 import jetbrains_metric
from src.datasets import load_code_dataset
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


DEFAULT_CONFIG = Path(
    "experiments/cognascore/configs/consensus28_progressive_protected_development.json"
)
DEFAULT_OUTPUT = Path(
    "results/experiments/cognascore/progressive_within_group_swap_top50"
)
PROGRESSIVE_DATASET = "java_progressive_obfuscation"
PROGRESSIVE_PATH = Path(
    "datasets/constructed/java-progressive-obfuscation-class-100"
)
REPORT_DATASETS = (*TRAIN_DATASETS, "jetbrains", PROGRESSIVE_DATASET)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--candidate-rank-max", type=int, default=50)
    parser.add_argument(
        "--candidate-feature",
        action="append",
        default=[],
        help=(
            "Restrict additions to an explicit feature. Repeat for several features. "
            "When omitted, use every available candidate up to --candidate-rank-max."
        ),
    )
    parser.add_argument(
        "--removed-feature",
        action="append",
        default=[],
        help=(
            "Restrict removals to an explicit selected feature. Repeat for several "
            "features. When omitted, test removing every selected feature."
        ),
    )
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument(
        "--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT
    )
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = [
        str(value)
        for value in json.loads(args.config.read_text(encoding="utf-8"))[
            "selected_features"
        ]
    ]
    removal_features = list(args.removed_feature) or list(selected)
    missing_removals = sorted(set(removal_features) - set(selected))
    if missing_removals:
        raise SystemExit(f"Requested removal features are not selected: {missing_removals}")
    with args.ranking.open(newline="", encoding="utf-8") as handle:
        ranking = list(csv.DictReader(handle))

    available = available_features(args.feature_root, args.embedding_feature_root)
    candidates = [
        row
        for row in ranking
        if int(row["rank"]) <= args.candidate_rank_max
        and row["feature"] not in selected
        and row["feature"] in available
    ]
    if args.candidate_feature:
        requested = list(dict.fromkeys(args.candidate_feature))
        missing = sorted(set(requested) - available)
        if missing:
            raise SystemExit(f"Requested candidate features unavailable: {missing}")
        ranking_by_feature = {str(row["feature"]): row for row in ranking}
        candidates = [
            ranking_by_feature.get(
                feature,
                {
                    "feature": feature,
                    "rank": "",
                    "group": "unranked_new_feature",
                },
            )
            for feature in requested
        ]
    candidate_names = [str(row["feature"]) for row in candidates]
    all_features = list(dict.fromkeys([*selected, *candidate_names]))
    frames = {
        dataset: load_combined_features(
            dataset,
            args.feature_root,
            args.embedding_feature_root,
            all_features,
        )
        for dataset in REPORT_DATASETS
    }
    train = pd.concat([frames[name] for name in TRAIN_DATASETS], ignore_index=True)
    fit_mask = training_middle_keep_mask(train, 0.0)
    progressive_items = {
        item.task_id: item for item in load_code_dataset(PROGRESSIVE_PATH)
    }

    def evaluate(features: list[str]) -> tuple[Any, dict[str, float]]:
        model = fit_ridge(train, fit_mask, args.ridge_alpha, features)
        metrics: dict[str, float] = {}
        for dataset in TRAIN_DATASETS:
            frame = frames[dataset]
            prediction = model.predict(frame[features].to_numpy(dtype=float))
            metrics[dataset] = float(
                spearman(
                    prediction.tolist(),
                    frame["readability_score"].astype(float).tolist(),
                )
            )
        progressive = frames[PROGRESSIVE_DATASET]
        prediction = model.predict(progressive[features].to_numpy(dtype=float))
        rows = build_predictions(progressive, prediction, progressive_items)
        grouped = summarize(rows)
        metrics["progressive_pooled"] = float(grouped["pooled_spearman"])
        metrics["progressive_within_group"] = float(
            grouped["within_group_spearman"]["mean"]
        )
        metrics["progressive_endpoint_rate"] = float(
            grouped["chain_direction"]["endpoint_first_above_last_rate"]
        )
        metrics["progressive_changed_decrease_rate"] = float(
            grouped["adjacent_transitions"]["overall"][
                "changed_only_decrease_rate"
            ]
        )
        threshold, _ = calibrate_classification_threshold(
            model, train, fit_mask, features
        )
        metrics["jetbrains"] = jetbrains_metric(
            model, features, frames["jetbrains"], threshold
        )
        metrics["threshold"] = float(threshold)
        return model, metrics

    _, baseline = evaluate(selected)
    leave_one_rows: list[dict[str, Any]] = []
    for removed in removal_features:
        position = selected.index(removed) + 1
        features = [feature for feature in selected if feature != removed]
        _, metrics = evaluate(features)
        row: dict[str, Any] = {
            "removed_feature": removed,
            "model_position": position,
        }
        add_metrics(row, metrics, baseline)
        row["within_group_contribution"] = (
            baseline["progressive_within_group"]
            - metrics["progressive_within_group"]
        )
        leave_one_rows.append(row)
    leave_one_rows.sort(key=lambda row: row["within_group_contribution"])

    swap_rows: list[dict[str, Any]] = []
    total = len(removal_features) * len(candidates)
    completed = 0
    for removed in removal_features:
        retained = [feature for feature in selected if feature != removed]
        for candidate in candidates:
            added = str(candidate["feature"])
            _, metrics = evaluate([*retained, added])
            row = {
                "removed_feature": removed,
                "added_feature": added,
                "added_consensus_rank": (
                    int(candidate["rank"]) if str(candidate["rank"]).strip() else None
                ),
                "added_group": str(candidate["group"]),
            }
            add_metrics(row, metrics, baseline)
            swap_rows.append(row)
            completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"swap {completed}/{total}", flush=True)
    swap_rows.sort(
        key=lambda row: (
            row["progressive_within_group"],
            row["progressive_pooled"],
            row["scalabrino"],
            row["jetbrains"],
        ),
        reverse=True,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(leave_one_rows).to_csv(
        args.output / "leave_one_contributions.csv", index=False
    )
    pd.DataFrame(swap_rows).to_csv(args.output / "swap_candidates.csv", index=False)
    summary = {
        "status": "Progressive-supervised development search; not validation",
        "config": str(args.config),
        "ranking": str(args.ranking),
        "candidate_rank_max": args.candidate_rank_max,
        "selected_feature_count": len(selected),
        "candidate_count": len(candidates),
        "swap_count": len(swap_rows),
        "baseline": baseline,
        "negative_contribution_features": [
            row
            for row in leave_one_rows
            if float(row["within_group_contribution"]) < 0.0
        ],
        "leave_one": leave_one_rows,
        "top_swaps": swap_rows[:50],
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({**summary, "leave_one": leave_one_rows[:10], "top_swaps": swap_rows[:10]}, indent=2))


def available_features(base_root: Path, embedding_root: Path) -> set[str]:
    identity = {"dataset", "task_id", "readability_score"}
    base_columns = pd.read_csv(
        base_root / "scalabrino" / EMBEDDING_SLUG / "features.csv", nrows=1
    ).columns
    embedding_columns = pd.read_csv(
        embedding_root / "scalabrino" / EMBEDDING_SLUG / "features.csv", nrows=1
    ).columns
    return {
        namespaced_feature("base", column)
        for column in base_columns
        if column not in identity
    } | {
        namespaced_feature("embedding", column)
        for column in embedding_columns
        if column not in identity
    }


def add_metrics(
    row: dict[str, Any], metrics: dict[str, float], baseline: dict[str, float]
) -> None:
    for name, value in metrics.items():
        row[name] = value
        row[f"delta_{name}"] = value - baseline[name]


if __name__ == "__main__":
    main()
