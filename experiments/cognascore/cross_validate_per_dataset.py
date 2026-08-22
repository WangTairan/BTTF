"""Run independent within-dataset CV for the frozen CognaScore features."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.cognascore.cross_validate_fixed import (
    DEFAULT_DATASETS,
    best_mcc_threshold,
    fit_model,
    fold_assignments,
    report_metrics,
    write_predictions,
)
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
            "Train and evaluate a separate frozen-24 Ridge model for every "
            "dataset using out-of-fold predictions."
        )
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DEFAULT_DATASETS,
        help="Dataset to evaluate. Repeatable; defaults to all six.",
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = tuple(args.dataset or DEFAULT_DATASETS)
    if args.folds < 2:
        raise SystemExit("--folds must be at least 2.")

    all_predictions: list[pd.DataFrame] = []
    metrics: dict[str, dict] = {}
    fold_sizes: dict[str, list[dict]] = {}
    for dataset_index, dataset in enumerate(datasets):
        frame = load_combined_features(
            dataset,
            args.base_root,
            args.embedding_root,
            list(SELECTED_FEATURES),
        ).copy()
        frame["_task_occurrence"] = frame.groupby(["dataset", "task_id"]).cumcount()
        frame["_cv_fold"] = fold_assignments(
            frame,
            args.folds,
            args.seed + dataset_index,
        )
        predictions = np.full(len(frame), np.nan, dtype=float)
        binary_predictions = np.full(len(frame), np.nan, dtype=float)
        dataset_fold_sizes = []

        for fold in range(args.folds):
            test_mask = frame["_cv_fold"].to_numpy(dtype=int) == fold
            train_mask = ~test_mask
            train = frame.loc[train_mask].reset_index(drop=True)
            test = frame.loc[test_mask]
            model = fit_model(train, args.ridge_alpha)
            test_prediction = model.predict(
                test.loc[:, SELECTED_FEATURES].to_numpy(dtype=float)
            )
            test_indices = test.index.to_numpy(dtype=int)
            predictions[test_indices] = test_prediction

            fold_record = {
                "fold": fold,
                "train_count": int(train_mask.sum()),
                "test_count": int(test_mask.sum()),
            }
            labels = train["readability_score"].to_numpy(dtype=float)
            if set(labels.tolist()).issubset({0.0, 1.0}):
                train_prediction = model.predict(
                    train.loc[:, SELECTED_FEATURES].to_numpy(dtype=float)
                )
                threshold, _ = best_mcc_threshold(labels.astype(int), train_prediction)
                binary_predictions[test_indices] = (
                    test_prediction >= threshold
                ).astype(int)
                fold_record["training_fold_threshold"] = threshold
            dataset_fold_sizes.append(fold_record)

        if not np.isfinite(predictions).all():
            missing = int((~np.isfinite(predictions)).sum())
            raise SystemExit(f"{dataset}: {missing} rows have no OOF prediction.")
        frame["oof_prediction"] = predictions
        frame["oof_binary_prediction"] = binary_predictions
        metrics[dataset] = report_metrics(frame)[dataset]
        fold_sizes[dataset] = dataset_fold_sizes
        all_predictions.append(frame)

    combined = pd.concat(all_predictions, ignore_index=True)
    output = args.output or (
        EXPERIMENT_RESULTS_ROOT / f"fixed24_per_dataset_{args.folds}fold_cv"
    )
    output.mkdir(parents=True, exist_ok=True)
    write_predictions(output / "oof_predictions.csv", combined)
    payload = {
        "method": "CognaScore ML fixed-24 independent per-dataset cross-validation",
        "protocol": "one separate Ridge model per dataset and fold",
        "folds": args.folds,
        "seed": args.seed,
        "ridge_alpha": args.ridge_alpha,
        "datasets": list(datasets),
        "sample_count": len(combined),
        "selected_feature_count": len(SELECTED_FEATURES),
        "selected_features": list(SELECTED_FEATURES),
        "feature_selection_inside_cv": False,
        "metrics": metrics,
        "fold_sizes": fold_sizes,
        "binary_threshold_policy": (
            "chosen using only the corresponding outer-fold training rows"
        ),
        "limitation": (
            "The frozen features were selected previously using all six development "
            "datasets; this estimates model-fit variance but does not remove feature-"
            "selection bias."
        ),
    }
    summary = output / "summary.json"
    summary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"wrote: {summary}")


if __name__ == "__main__":
    main()
