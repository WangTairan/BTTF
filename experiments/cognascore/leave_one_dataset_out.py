"""Evaluate the frozen CognaScore features by leaving out one dataset at a time."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.cognascore.cross_validate_fixed import (
    DEFAULT_DATASETS,
    best_mcc_threshold,
    fit_model,
)
from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)
from src.methods.cognascore.runners.supervised_ridge import (
    SELECTED_FEATURES,
    load_combined_features,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train on all selected datasets except one, then evaluate on the "
            "entire unseen dataset using the frozen 24-feature list."
        )
    )
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DEFAULT_DATASETS,
        help="Dataset in the leave-one-out pool. Repeatable; defaults to all six.",
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = tuple(args.dataset or DEFAULT_DATASETS)
    if len(datasets) < 2:
        raise SystemExit("Leave-one-dataset-out requires at least two datasets.")
    frames = {
        dataset: load_combined_features(
            dataset,
            args.base_root,
            args.embedding_root,
            list(SELECTED_FEATURES),
        ).copy()
        for dataset in datasets
    }

    metrics: dict[str, dict] = {}
    rows: list[dict] = []
    fit_sizes: dict[str, dict] = {}
    for held_out in datasets:
        training_datasets = tuple(dataset for dataset in datasets if dataset != held_out)
        train = pd.concat(
            [frames[dataset] for dataset in training_datasets],
            ignore_index=True,
        )
        test = frames[held_out]
        model = fit_model(train, args.ridge_alpha)
        prediction = model.predict(
            test.loc[:, SELECTED_FEATURES].to_numpy(dtype=float)
        )
        actual = test["readability_score"].to_numpy(dtype=float)
        is_binary = set(actual.tolist()).issubset({0.0, 1.0})
        if is_binary:
            fixed_labels = (prediction >= 0.5).astype(int)
            posthoc_threshold, posthoc_mcc = best_mcc_threshold(
                actual.astype(int), prediction
            )
            metrics[held_out] = {
                "n": len(test),
                "metric": "mcc",
                "mcc_fixed_target_midpoint_0_5": matthews_correlation_coefficient(
                    fixed_labels.tolist(), actual.astype(int).tolist()
                ),
                "mcc_best_held_out_threshold_reference_only": posthoc_mcc,
                "best_held_out_threshold_reference_only": posthoc_threshold,
            }
        else:
            metrics[held_out] = {
                "n": len(test),
                "metric": "spearman",
                "value": spearman(prediction.tolist(), actual.tolist()),
            }

        fit_sizes[held_out] = {
            "training_datasets": list(training_datasets),
            "train_count": len(train),
            "test_count": len(test),
        }
        for record, score in zip(test.to_dict("records"), prediction):
            rows.append(
                {
                    "held_out_dataset": held_out,
                    "task_id": record["task_id"],
                    "readability_score": record["readability_score"],
                    "prediction": float(score),
                }
            )

    output = args.output or (
        EXPERIMENT_RESULTS_ROOT / "fixed24_leave_one_dataset_out"
    )
    output.mkdir(parents=True, exist_ok=True)
    write_prediction_rows(output / "predictions.csv", rows)
    payload = {
        "method": "CognaScore ML fixed-24 leave-one-dataset-out evaluation",
        "protocol": "one Ridge fit on N-1 datasets for each completely held-out dataset",
        "ridge_alpha": args.ridge_alpha,
        "datasets": list(datasets),
        "selected_feature_count": len(SELECTED_FEATURES),
        "selected_features": list(SELECTED_FEATURES),
        "feature_selection_inside_cv": False,
        "metrics": metrics,
        "fit_sizes": fit_sizes,
        "jetbrains_threshold_policy": (
            "fixed score midpoint 0.5; the Ridge output is not interpreted as a "
            "probability; best held-out threshold is reference-only"
        ),
        "limitation": (
            "The held-out labels are excluded from model fitting, but the frozen "
            "feature list was selected previously using all six development datasets. "
            "This is therefore not a fully untouched external-validation estimate."
        ),
    }
    summary = output / "summary.json"
    summary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"wrote: {summary}")


def write_prediction_rows(path: Path, rows: list[dict]) -> None:
    columns = [
        "held_out_dataset",
        "task_id",
        "readability_score",
        "prediction",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
