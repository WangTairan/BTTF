"""Evaluate frozen readability features by leaving out one dataset at a time."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

from experiments.main.readability_model.evaluation.cross_validate_fixed import (
    DEFAULT_DATASETS,
    best_mcc_threshold,
    fit_model,
)
from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.llm_features.types import DEFAULT_CAUSAL_LM
from src.methods.readability_model.runners.supervised_ridge import (
    EMBEDDING_MODEL,
    SELECTED_FEATURES,
    load_combined_features,
    load_selected_features,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train on all selected datasets except one, then evaluate on the "
            "entire unseen dataset using the frozen feature list."
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
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--embedding-model")
    parser.add_argument("--llm-model")
    parser.add_argument(
        "--selected-features-metadata",
        type=Path,
        help="JSON metadata containing selected_features; defaults to the frozen list.",
    )
    parser.add_argument("--remove-feature", action="append", default=[])
    parser.add_argument("--add-feature", action="append", default=[])
    parser.add_argument("-o", "--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = tuple(args.dataset or DEFAULT_DATASETS)
    metadata = (
        json.loads(args.selected_features_metadata.read_text(encoding="utf-8"))
        if args.selected_features_metadata
        else {}
    )
    selected_features = (
        load_selected_features(args.selected_features_metadata)
        if args.selected_features_metadata
        else list(SELECTED_FEATURES)
    )
    embedding_model = args.embedding_model or metadata.get("embedding_model") or EMBEDDING_MODEL
    llm_model = args.llm_model or metadata.get("llm_feature_model") or DEFAULT_CAUSAL_LM
    missing_removals = sorted(set(args.remove_feature) - set(selected_features))
    if missing_removals:
        raise SystemExit(f"Cannot remove unselected features: {missing_removals}")
    selected_features = [
        feature for feature in selected_features if feature not in set(args.remove_feature)
    ]
    selected_features.extend(
        feature for feature in args.add_feature if feature not in selected_features
    )
    if len(datasets) < 2:
        raise SystemExit("Leave-one-dataset-out requires at least two datasets.")
    frames = {
        dataset: load_combined_features(
            dataset,
            args.base_root,
            args.embedding_root,
            selected_features,
            llm_feature_root=args.llm_root,
            embedding_model=str(embedding_model),
            llm_model=str(llm_model),
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
        model = fit_model(train, args.ridge_alpha, selected_features=selected_features)
        prediction = model.predict(
            test.loc[:, selected_features].to_numpy(dtype=float)
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
        EXPERIMENT_RESULTS_ROOT / "selected_leave_one_dataset_out"
    )
    output.mkdir(parents=True, exist_ok=True)
    write_prediction_rows(output / "predictions.csv", rows)
    payload = {
        "method": f"Readability model fixed-{len(selected_features)} leave-one-dataset-out evaluation",
        "protocol": (
            "one bounded Ridge fit on N-1 datasets for each held-out dataset, "
            "using the frozen model's median-imputation, training-range-clipping, "
            "standardization, and inverse-dataset-size weighting pipeline"
        ),
        "ridge_alpha": args.ridge_alpha,
        "datasets": list(datasets),
        "selected_feature_count": len(selected_features),
        "embedding_model": embedding_model,
        "llm_feature_model": (
            llm_model if any(name.startswith("llm__") for name in selected_features) else None
        ),
        "selected_features": selected_features,
        "feature_selection_inside_cv": False,
        "metrics": metrics,
        "fit_sizes": fit_sizes,
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
