"""Cross-validate the frozen CognaScore feature set without reselection."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)
from src.methods.cognascore.runners.supervised_ridge import (
    SELECTED_FEATURES,
    dataset_balanced_sample_weight,
    load_combined_features,
    load_selected_features,
    regression_target,
)


DEFAULT_DATASETS = (
    "mbjp",
    "buse",
    "dorn",
    "scalabrino",
    "schnappinger",
    "jetbrains",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate out-of-fold predictions for the frozen CognaScore feature set "
            "Ridge model. Features are never reselected inside or outside a fold."
        )
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DEFAULT_DATASETS,
        help="Dataset included in pooled fitting. Repeatable; defaults to all six.",
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument(
        "--selected-features-metadata",
        type=Path,
        help="JSON metadata containing selected_features; defaults to the frozen list.",
    )
    parser.add_argument(
        "--remove-feature",
        action="append",
        default=[],
        help="Remove a feature from the selected list before CV. Repeatable.",
    )
    parser.add_argument(
        "--add-feature",
        action="append",
        default=[],
        help="Append a feature to the selected list before CV. Repeatable.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Exact result directory. Defaults to "
            "results/experiments/cognascore/selected_<folds>fold_cv/."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = tuple(args.dataset or DEFAULT_DATASETS)
    selected_features = (
        load_selected_features(args.selected_features_metadata)
        if args.selected_features_metadata
        else list(SELECTED_FEATURES)
    )
    missing_removals = sorted(set(args.remove_feature) - set(selected_features))
    if missing_removals:
        raise SystemExit(f"Cannot remove unselected features: {missing_removals}")
    selected_features = [
        feature for feature in selected_features if feature not in set(args.remove_feature)
    ]
    selected_features.extend(
        feature for feature in args.add_feature if feature not in selected_features
    )
    if args.folds < 2:
        raise SystemExit("--folds must be at least 2.")

    frames = []
    for dataset_index, dataset in enumerate(datasets):
        frame = load_combined_features(
            dataset,
            args.base_root,
            args.embedding_root,
            selected_features,
        ).copy()
        frame["_task_occurrence"] = frame.groupby(["dataset", "task_id"]).cumcount()
        frame["_cv_fold"] = fold_assignments(
            frame,
            args.folds,
            args.seed + dataset_index,
        )
        frames.append(frame)
    pooled = pd.concat(frames, ignore_index=True)
    predictions = np.full(len(pooled), np.nan, dtype=float)
    binary_predictions = np.full(len(pooled), np.nan, dtype=float)

    fold_sizes = []
    for fold in range(args.folds):
        test_mask = pooled["_cv_fold"].to_numpy(dtype=int) == fold
        train_mask = ~test_mask
        train = pooled.loc[train_mask].reset_index(drop=True)
        test = pooled.loc[test_mask]
        model = fit_model(train, args.ridge_alpha, selected_features=selected_features)
        test_predictions = model.predict(
            test.loc[:, selected_features].to_numpy(dtype=float)
        )
        predictions[test.index.to_numpy(dtype=int)] = test_predictions
        fold_record = {
            "fold": fold,
            "train_count": int(train_mask.sum()),
            "test_count": int(test_mask.sum()),
            "test_count_by_dataset": {
                str(key): int(value)
                for key, value in test.groupby("dataset").size().items()
            },
        }
        jetbrains_train = train[train["dataset"] == "jetbrains"]
        jetbrains_test_mask = test["dataset"].to_numpy() == "jetbrains"
        jetbrains_labels = set(
            jetbrains_train["readability_score"].astype(float).tolist()
        )
        if (
            len(jetbrains_train)
            and jetbrains_test_mask.any()
            and jetbrains_labels.issubset({0.0, 1.0})
        ):
            train_predictions = model.predict(
                jetbrains_train.loc[:, selected_features].to_numpy(dtype=float)
            )
            threshold, _ = best_mcc_threshold(
                jetbrains_train["readability_score"].to_numpy(dtype=int),
                train_predictions,
            )
            test_indices = test.index.to_numpy(dtype=int)[jetbrains_test_mask]
            binary_predictions[test_indices] = (
                test_predictions[jetbrains_test_mask] >= threshold
            ).astype(int)
            fold_record["jetbrains_training_threshold"] = threshold
        fold_sizes.append(fold_record)

    if not np.isfinite(predictions).all():
        missing = int((~np.isfinite(predictions)).sum())
        raise SystemExit(f"Cross-validation left {missing} rows without predictions.")

    pooled["oof_prediction"] = predictions
    pooled["oof_binary_prediction"] = binary_predictions
    metrics = report_metrics(pooled)
    output = args.output or (
        EXPERIMENT_RESULTS_ROOT / f"selected_{args.folds}fold_cv"
    )
    output.mkdir(parents=True, exist_ok=True)
    write_predictions(output / "oof_predictions.csv", pooled)
    payload = {
        "method": f"CognaScore ML fixed-{len(selected_features)} cross-validation",
        "folds": args.folds,
        "seed": args.seed,
        "ridge_alpha": args.ridge_alpha,
        "datasets": list(datasets),
        "sample_count": len(pooled),
        "selected_feature_count": len(selected_features),
        "selected_features": selected_features,
        "feature_selection_inside_cv": False,
        "fold_construction": (
            "independent shuffled task-group folds within each dataset; repeated "
            "rows with the same task ID remain in one fold; StratifiedKFold for "
            "binary labels and KFold for continuous labels; matching fold indices "
            "are pooled across datasets"
        ),
        "training": (
            "one pooled Ridge per fold with median imputation, standardization, "
            "and inverse-dataset-size sample weighting"
        ),
        "metrics": metrics,
        "fold_sizes": fold_sizes,
        "limitation": (
            "These are out-of-fold model-fit estimates for an already frozen feature "
            f"set. Because the {len(selected_features)} features were previously selected using the six "
            "development datasets, this is not nested feature-selection CV and does "
            "not remove feature-selection bias."
        ),
    }
    summary_path = output / "summary.json"
    summary_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"wrote: {summary_path}")


def fold_assignments(frame: pd.DataFrame, folds: int, seed: int) -> np.ndarray:
    task_groups = (
        frame.groupby("task_id", sort=False)["readability_score"]
        .mean()
        .reset_index()
    )
    if len(task_groups) < folds:
        raise SystemExit(
            f"Dataset {frame['dataset'].iloc[0]} has {len(task_groups)} unique tasks, "
            f"fewer than the requested {folds} folds."
        )
    labels = task_groups["readability_score"].to_numpy(dtype=float)
    unique = set(labels.tolist())
    group_assignments = np.full(len(task_groups), -1, dtype=int)
    indices = np.arange(len(task_groups))
    if unique.issubset({0.0, 1.0}):
        counts = np.bincount(labels.astype(int), minlength=2)
        if int(counts.min()) < folds:
            raise SystemExit(
                f"Binary dataset {frame['dataset'].iloc[0]} has fewer than {folds} "
                "samples in one class."
            )
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
        splits = splitter.split(indices, labels)
    else:
        splitter = KFold(n_splits=folds, shuffle=True, random_state=seed)
        splits = splitter.split(indices)
    for fold, (_, test_indices) in enumerate(splits):
        group_assignments[test_indices] = fold
    fold_by_task = dict(zip(task_groups["task_id"], group_assignments))
    return frame["task_id"].map(fold_by_task).to_numpy(dtype=int)


def fit_model(
    train: pd.DataFrame,
    ridge_alpha: float,
    *,
    selected_features: list[str] | tuple[str, ...] = tuple(SELECTED_FEATURES),
):
    target = regression_target(train)
    eligible = np.ones(len(train), dtype=bool)
    sample_weight = dataset_balanced_sample_weight(train, eligible)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=ridge_alpha),
    )
    model.fit(
        train.loc[:, selected_features].to_numpy(dtype=float),
        target,
        ridge__sample_weight=sample_weight,
    )
    return model


def report_metrics(frame: pd.DataFrame) -> dict[str, dict[str, float | int | str]]:
    metrics: dict[str, dict[str, float | int | str]] = {}
    continuous_values = []
    for dataset, group in frame.groupby("dataset", sort=False):
        actual = group["readability_score"].to_numpy(dtype=float)
        predicted = group["oof_prediction"].to_numpy(dtype=float)
        if set(actual.tolist()).issubset({0.0, 1.0}):
            fixed_prediction = (predicted >= 0.5).astype(int)
            trained_threshold_prediction = group[
                "oof_binary_prediction"
            ].to_numpy(dtype=int)
            threshold, best_mcc = best_mcc_threshold(actual.astype(int), predicted)
            metrics[str(dataset)] = {
                "n": len(group),
                "metric": "mcc",
                "mcc_training_fold_threshold": matthews_correlation_coefficient(
                    trained_threshold_prediction.tolist(),
                    actual.astype(int).tolist(),
                ),
                "mcc_fixed_0_5": matthews_correlation_coefficient(
                    fixed_prediction.tolist(),
                    actual.astype(int).tolist(),
                ),
                "mcc_best_oof_threshold": best_mcc,
                "best_oof_threshold": threshold,
            }
        else:
            value = spearman(predicted.tolist(), actual.tolist())
            metrics[str(dataset)] = {
                "n": len(group),
                "metric": "spearman",
                "value": value,
            }
            if math.isfinite(value):
                continuous_values.append(value)
    if continuous_values:
        metrics["macro_continuous"] = {
            "n_datasets": len(continuous_values),
            "metric": "mean_spearman",
            "value": mean(continuous_values),
        }
    return metrics


def best_mcc_threshold(actual: np.ndarray, predicted: np.ndarray) -> tuple[float, float]:
    unique = np.unique(predicted)
    thresholds = [float(unique[0] - 1e-12), float(unique[-1] + 1e-12)]
    thresholds.extend(float((left + right) / 2.0) for left, right in zip(unique, unique[1:]))
    best_threshold = 0.5
    best_value = -1.0
    for threshold in thresholds:
        labels = (predicted >= threshold).astype(int)
        value = matthews_correlation_coefficient(labels.tolist(), actual.tolist())
        if value > best_value:
            best_value = value
            best_threshold = threshold
    return best_threshold, best_value


def write_predictions(path: Path, frame: pd.DataFrame) -> None:
    columns = [
        "dataset",
        "task_id",
        "readability_score",
        "_task_occurrence",
        "_cv_fold",
        "oof_prediction",
        "oof_binary_prediction",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in frame.loc[:, columns].to_dict("records"):
            writer.writerow(row)


if __name__ == "__main__":
    main()
