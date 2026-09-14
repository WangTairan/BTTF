from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.methods.cognascore.feature_schema import namespaced_feature
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
    TRAINED_MODEL_ROOT,
)
from src.methods.cognascore.llm_surprisal import DEFAULT_CAUSAL_LM
from src.methods.cognascore.results import model_slug
from src.methods.cognascore.modeling import BoundedRidge, TrainingRangeClipper


EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_SLUG = model_slug(EMBEDDING_MODEL)
LLM_FEATURE_SLUG = model_slug(DEFAULT_CAUSAL_LM)
ALL_DATASETS = (
    "scalabrino",
    "schnappinger",
    "dorn",
    "buse",
    "mbjp",
    "jetbrains",
)
TRAIN_DATASETS = ("mbjp", "buse", "dorn", "scalabrino", "schnappinger", "jetbrains")
SCORE_MODEL_NAME = "consensus18_6dataset_sampled_margin_nomic"
METHOD_KEY = "cognascore_ml_consensus18_6dataset_sampled_margin"

SELECTED_FEATURES = [
    "base__operator_density",
    "base__byte_entropy",
    "base__literal_expression_log_balance",
    "base__max_line_length",
    "embedding__structural_core__auto_kmeans_selected_k",
    "embedding__only_identifier__embedding_first_pc_explained_variance",
    "base__indent_transition_mean",
    "embedding__structural_core__optics_cluster_type_entropy_mean",
    "embedding__structural_core__embedding_first_pc_explained_variance",
    "base__type_regex_ratio",
    "embedding__structural_core__auto_agglo_cluster_type_entropy_mean",
    "semantic__short_identifier_candidate_ratio",
    "semantic__short_identifier_math_application_margin_mean",
    "base__type_bitwise_ratio",
    "embedding__structural_core__optics_noise_ratio",
    "base__identifier_length_cv",
    "base__comparison_operator_density",
    "base__operator_character_density",
]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize the current 18-feature CognaScore ML Ridge model."
    )
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument(
        "--embedding-feature-root",
        type=Path,
        default=EMBEDDING_FEATURE_ROOT,
    )
    parser.add_argument("--output-root", type=Path, default=Path("results/methods"))
    parser.add_argument("--artifact-root", type=Path, default=TRAINED_MODEL_ROOT)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--method", default=METHOD_KEY)
    parser.add_argument("--score-model-name", default=SCORE_MODEL_NAME)
    parser.add_argument(
        "--overwrite-artifact",
        action="store_true",
        help=(
            "Explicitly allow replacement of an existing frozen model artifact. "
            "Without this flag, an existing model directory is protected."
        ),
    )
    parser.add_argument(
        "--selected-features-metadata",
        type=Path,
        help="Experiment metadata containing selected_features. Defaults to the current 18-feature list.",
    )
    parser.add_argument(
        "--remove-feature",
        action="append",
        default=[],
        help="Remove a feature from the selected list before fitting. Repeatable.",
    )
    parser.add_argument(
        "--add-feature",
        action="append",
        default=[],
        help="Append a feature to the selected list before fitting. Repeatable.",
    )
    parser.add_argument(
        "--train-dataset",
        action="append",
        default=[],
        help="Dataset used to fit the final ML Ridge model. Can be repeated. Defaults to the six continuous-score datasets.",
    )
    parser.add_argument(
        "--report-dataset",
        action="append",
        default=[],
        help="Dataset to materialize predictions for. Can be repeated. Defaults to the six development datasets.",
    )
    args = parser.parse_args()
    requested_artifact_dir = (
        args.artifact_root / args.score_model_name / EMBEDDING_SLUG
    )
    if requested_artifact_dir.exists() and not args.overwrite_artifact:
        raise SystemExit(
            f"Refusing to overwrite frozen model artifact: {requested_artifact_dir}. "
            "Use a new --score-model-name for experiments, or pass "
            "--overwrite-artifact explicitly."
        )
    selected_features = (
        load_selected_features(args.selected_features_metadata)
        if args.selected_features_metadata
        else list(SELECTED_FEATURES)
    )
    unknown_removals = sorted(set(args.remove_feature) - set(selected_features))
    if unknown_removals:
        raise SystemExit(f"Cannot remove unselected features: {unknown_removals}")
    selected_features = [
        feature for feature in selected_features if feature not in args.remove_feature
    ]
    for feature in args.add_feature:
        if feature not in selected_features:
            selected_features.append(feature)
    feature_category_counts = feature_category_counts_for(selected_features)

    report_datasets = tuple(args.report_dataset or ALL_DATASETS)
    train_datasets = tuple(args.train_dataset or TRAIN_DATASETS)
    frames = {
        dataset: load_combined_features(dataset, args.feature_root, args.embedding_feature_root, selected_features)
        for dataset in sorted(set((*train_datasets, *report_datasets)))
    }
    train = pd.concat([frames[name] for name in train_datasets], ignore_index=True)
    fit_mask = np.ones(len(train), dtype=bool)
    ridge = fit_ridge(train, fit_mask, args.ridge_alpha, selected_features)
    coefficients = ridge_coefficients(ridge, selected_features)
    binary_training_dataset = any(
        DATASETS[name].label_type == "binary"
        for name in train_datasets
        if name in DATASETS
    )
    if binary_training_dataset:
        fixed_threshold, threshold_metrics = calibrate_classification_threshold(
            ridge,
            train,
            fit_mask,
            selected_features,
        )
    else:
        fixed_threshold, threshold_metrics = None, None
    artifact_dir = write_model_artifact(
        model=ridge,
        artifact_root=args.artifact_root,
        score_model_name=args.score_model_name,
        selected_features=selected_features,
        feature_category_counts=feature_category_counts,
        ridge_alpha=args.ridge_alpha,
        seed=args.seed,
        train=train,
        fit_mask=fit_mask,
        training_datasets=train_datasets,
        classification_threshold=fixed_threshold,
        threshold_metrics=threshold_metrics,
        feature_root=args.feature_root,
        embedding_feature_root=args.embedding_feature_root,
    )
    print(f"Wrote frozen model artifact: {artifact_dir}", flush=True)
    for dataset in report_datasets:
        frame = frames[dataset]
        x = frame[selected_features].to_numpy(dtype=float)
        predictions = ridge.predict(x)
        item_metadata = load_item_metadata(dataset)
        write_summary(
            dataset=dataset,
            frame=frame,
            predictions=predictions,
            item_metadata=item_metadata,
            output_root=args.output_root,
            method=args.method,
            score_model_name=args.score_model_name,
            ridge_alpha=args.ridge_alpha,
            seed=args.seed,
            coefficients=coefficients,
            selected_features=selected_features,
            feature_category_counts=feature_category_counts,
            training_sample_count=int(fit_mask.sum()),
            training_pool_sample_count=len(train),
            training_datasets=train_datasets,
            classification_threshold=fixed_threshold,
            classification_threshold_source=(
                "dataset_balanced_continuous_training_pool"
                if fixed_threshold is not None
                else None
            ),
            model_artifact=artifact_dir,
        )


def load_selected_features(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    features = data.get("selected_features")
    if not isinstance(features, list) or not features:
        raise SystemExit(f"No selected_features list in {path}")
    return [str(feature) for feature in features]


def feature_category_counts_for(selected_features: list[str]) -> dict[str, int]:
    return {
        "base": sum(1 for feature in selected_features if feature.startswith("base__")),
        "compression": sum(1 for feature in selected_features if feature.startswith("compression__")),
        "embedding_derived": sum(1 for feature in selected_features if feature.startswith("embedding__")),
        "semantic_context": sum(1 for feature in selected_features if feature.startswith("semantic__")),
        "causal_lm": sum(1 for feature in selected_features if feature.startswith("llm__")),
    }


def fit_ridge(frame: pd.DataFrame, fit_mask: np.ndarray, ridge_alpha: float, selected_features: list[str]):
    target = regression_target(frame)
    sample_weight = dataset_balanced_sample_weight(frame, fit_mask)
    model = Pipeline(
        [
            ("simpleimputer", SimpleImputer(strategy="median")),
            ("trainingrangeclipper", TrainingRangeClipper()),
            ("standardscaler", StandardScaler()),
            ("ridge", BoundedRidge(alpha=ridge_alpha)),
        ]
    )
    x_train = frame.loc[fit_mask, selected_features].to_numpy(dtype=float)
    model.fit(x_train, target[fit_mask], ridge__sample_weight=sample_weight[fit_mask])
    return model


def load_combined_features(
    dataset: str,
    feature_root: Path,
    embedding_feature_root: Path,
    selected_features: list[str],
    llm_feature_root: Path = LLM_FEATURE_ROOT,
) -> pd.DataFrame:
    base_path = feature_root / dataset / EMBEDDING_SLUG / "features.csv"
    embedding_path = embedding_feature_root / dataset / EMBEDDING_SLUG / "features.csv"
    base = pd.read_csv(base_path)
    embedding = pd.read_csv(embedding_path)

    id_columns = ["dataset", "task_id", "readability_score"]
    base_features = base.rename(
        columns={
            column: namespaced_feature("base", column)
            for column in base.columns
            if column not in id_columns
        }
    ).copy()
    embedding_features = embedding.rename(
        columns={
            column: namespaced_feature("embedding", column)
            for column in embedding.columns
            if column not in id_columns
        }
    ).copy()
    merge_columns = ["dataset", "task_id", "_feature_row_occurrence"]
    base_features["_feature_row_occurrence"] = base_features.groupby(["dataset", "task_id"]).cumcount()
    embedding_features["_feature_row_occurrence"] = embedding_features.groupby(["dataset", "task_id"]).cumcount()
    embedding_features = embedding_features.drop(columns=["readability_score"])
    merged = base_features.merge(
        embedding_features,
        on=merge_columns,
        how="inner",
        validate="one_to_one",
    ).drop(columns=["_feature_row_occurrence"])
    if len(merged) != len(base_features) or len(merged) != len(embedding_features):
        raise ValueError(
            f"Feature identity mismatch for {dataset}: "
            f"base={len(base_features)}, embedding={len(embedding_features)}, merged={len(merged)}"
        )
    if any(feature.startswith("llm__") for feature in selected_features):
        llm_path = llm_feature_root / dataset / LLM_FEATURE_SLUG / "features.csv"
        llm = pd.read_csv(llm_path)
        llm_features = llm.rename(
            columns={
                column: namespaced_feature("llm", column)
                for column in llm.columns
                if column not in id_columns
            }
        ).copy()
        llm_features["_feature_row_occurrence"] = llm_features.groupby(
            ["dataset", "task_id"]
        ).cumcount()
        llm_features = llm_features.drop(columns=["readability_score"])
        merged["_feature_row_occurrence"] = merged.groupby(
            ["dataset", "task_id"]
        ).cumcount()
        before = len(merged)
        merged = merged.merge(
            llm_features,
            on=merge_columns,
            how="inner",
            validate="one_to_one",
        ).drop(columns=["_feature_row_occurrence"])
        if len(merged) != before or len(merged) != len(llm_features):
            raise ValueError(
                f"LLM feature identity mismatch for {dataset}: "
                f"combined={before}, llm={len(llm_features)}, merged={len(merged)}"
            )
    missing = [feature for feature in selected_features if feature not in merged.columns]
    if missing:
        raise KeyError(f"Missing selected features for {dataset}: {missing}")
    return merged


def regression_target(frame: pd.DataFrame) -> np.ndarray:
    values = np.zeros(len(frame), dtype=float)
    for _, indices in frame.groupby("dataset").groups.items():
        labels = frame.loc[indices, "readability_score"].astype(float)
        unique = set(labels.dropna().unique().tolist())
        if unique.issubset({0.0, 1.0}):
            values[list(indices)] = labels.to_numpy(dtype=float)
        else:
            ranks = labels.rank(method="average")
            denom = max(len(labels) - 1, 1)
            values[list(indices)] = (ranks.to_numpy() - 1.0) / denom
    return values


def dataset_balanced_sample_weight(frame: pd.DataFrame, eligible_mask: np.ndarray) -> np.ndarray:
    counts = frame.loc[eligible_mask].groupby("dataset")["task_id"].transform("count").astype(float)
    count_by_index = pd.Series(0.0, index=frame.index)
    count_by_index.loc[eligible_mask] = counts
    weights = np.zeros(len(frame), dtype=float)
    eligible_counts = count_by_index.to_numpy(dtype=float)
    nonzero = eligible_mask & (eligible_counts > 0.0)
    weights[nonzero] = 1.0 / eligible_counts[nonzero]
    total = float(np.sum(weights))
    if total > 0.0:
        weights *= len(weights) / total
    return weights


def write_summary(
    *,
    dataset: str,
    frame: pd.DataFrame,
    predictions: np.ndarray,
    item_metadata: dict[str, dict[str, Any]],
    output_root: Path,
    method: str,
    score_model_name: str,
    ridge_alpha: float,
    seed: int,
    coefficients: dict[str, float],
    selected_features: list[str],
    feature_category_counts: dict[str, int],
    training_sample_count: int,
    training_pool_sample_count: int,
    training_datasets: tuple[str, ...],
    classification_threshold: float | None,
    classification_threshold_source: str | None,
    model_artifact: Path,
) -> None:
    rows = []
    for record, score in zip(frame.to_dict("records"), predictions):
        task_id = str(record["task_id"])
        rows.append(
            {
                "task_id": task_id,
                "readability_score": none_if_nan(record.get("readability_score")),
                "method": method,
                "score": float(score),
                "result": {
                    "score": float(score),
                    "supervised_score": float(score),
                    "score_model": score_model_name,
                },
                "metadata": item_metadata.get(task_id, {}),
            }
        )

    valid = [
        row
        for row in rows
        if row.get("readability_score") is not None
        and row.get("score") is not None
        and math.isfinite(float(row["score"]))
    ]
    dataset_spec = DATASETS.get(dataset)
    binary = (
        dataset_spec is not None and dataset_spec.label_type == "binary"
    ) or (
        dataset_spec is None
        and bool(valid)
        and all(row.get("metadata", {}).get("evaluation_metric") == "mcc" for row in valid)
    )

    threshold = None
    rho = None
    mcc = None
    confusion_matrix = None
    predicted_positive_count = None
    if binary:
        if classification_threshold is None:
            threshold, mcc, confusion_matrix, predicted_positive_count = best_binary_threshold(valid)
            threshold_policy = "best_on_dataset"
        else:
            threshold = classification_threshold
            mcc, confusion_matrix, predicted_positive_count = binary_metrics_at_threshold(valid, threshold)
            threshold_policy = "fixed_from_continuous_training_pool"
    elif len(valid) >= 2:
        rho = spearman(
            [float(row["score"]) for row in valid],
            [float(row["readability_score"]) for row in valid],
        )

    payload = {
        "dataset": dataset_path(dataset),
        "method": method,
        "model": EMBEDDING_MODEL,
        "configuration": f"nomic-ai-nomic-embed-text-v1.5__{score_model_name}",
        "embedding_model": EMBEDDING_MODEL,
        "output_policy": "overwrite",
        "count": len(rows),
        "valid_count": len(valid),
        "error_count": len(rows) - len(valid),
        "evaluation_metric": "mcc" if binary else "spearman",
        "classification_threshold": threshold,
        "classification_threshold_policy": threshold_policy if binary else None,
        "classification_threshold_source": classification_threshold_source if binary else None,
        "classification_direction": "higher_score_more_readable",
        "predicted_positive_count": predicted_positive_count,
        "spearman": rho,
        "mcc": mcc,
        "confusion_matrix": confusion_matrix,
        "mean_score": mean(float(row["score"]) for row in valid) if valid else None,
        "results": rows,
        "score_model": {
            "name": score_model_name,
            "training_policy": (
                "single fixed ML model trained on "
                f"{', '.join(training_datasets)}; datasets outside this fit pool are "
                "predicted only after fitting"
            ),
            "metric_policy": (
                "training-pool predictions for fitted datasets; transfer predictions "
                "for datasets outside the final fit pool"
            ),
            "feature_selection": (
                f"Current {len(selected_features)}-feature development list derived from five-embedding-model "
                "consensus stability screening across the six development datasets, "
                "followed by correlation filtering and feature removal"
            ),
            "feature_selection_datasets": [
                "mbjp",
                "buse",
                "dorn",
                "scalabrino",
                "schnappinger",
                "jetbrains",
            ],
            "excluded_feature_families": [
                "fixed-parameter DBSCAN",
                "graph-derived features",
                "legacy model scores",
            ],
            "validation_dataset": dataset,
            "training_datasets": list(training_datasets),
            "training_sample_count": int(training_sample_count),
            "training_pool_sample_count": int(training_pool_sample_count),
            "target": (
                "per-dataset rank-percentile readability for the six continuous datasets"
            ),
            "final_model": (
                f"Ridge(alpha={ridge_alpha:g}) with median imputation and standardization"
            ),
            "ridge_alpha": ridge_alpha,
            "seed": seed,
            "selected_feature_count": len(selected_features),
            "selected_feature_category_counts": feature_category_counts,
            "selected_features": selected_features,
            "standardized_coefficients": coefficients,
            "frozen_model_artifact": str(model_artifact),
        },
    }
    output_dir = output_root / method / dataset / EMBEDDING_SLUG
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "summary.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def load_item_metadata(dataset: str) -> dict[str, dict[str, Any]]:
    spec = DATASETS.get(dataset)
    if spec is None:
        return {}
    items = load_code_dataset(spec.path)
    return {
        item.task_id: {
            **item.metadata,
            "readability_prompt": item.readability_prompt,
        }
        for item in items
    }


def none_if_nan(value: Any) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if math.isnan(numeric):
        return None
    return numeric


def ridge_coefficients(model: Any, selected_features: list[str]) -> dict[str, float]:
    ridge = model.named_steps["ridge"]
    return {
        feature: float(coef)
        for feature, coef in zip(selected_features, ridge.coef_)
    }


def calibrate_classification_threshold(
    model: Any,
    train: pd.DataFrame,
    fit_mask: np.ndarray,
    selected_features: list[str],
) -> tuple[float | None, dict[str, Any] | None]:
    calibration = train.loc[fit_mask].reset_index(drop=True)
    if calibration.empty:
        return None, None
    predictions = model.predict(calibration[selected_features].to_numpy(dtype=float))
    binary_labels = (regression_target(calibration) >= 0.5).astype(int)
    eligible = np.ones(len(calibration), dtype=bool)
    weights = dataset_balanced_sample_weight(calibration, eligible)
    threshold, weighted_mcc, weighted_confusion = best_dataset_balanced_threshold(
        predictions,
        binary_labels,
        weights,
    )
    predicted = (predictions >= threshold).astype(int)
    per_dataset = {}
    for dataset, indices in calibration.groupby("dataset").groups.items():
        positions = np.asarray(list(indices), dtype=int)
        rows = [
            {
                "score": float(predictions[position]),
                "readability_score": int(binary_labels[position]),
            }
            for position in positions
        ]
        dataset_mcc, confusion_matrix, predicted_positive_count = binary_metrics_at_threshold(
            rows,
            threshold,
        )
        per_dataset[str(dataset)] = {
            "sample_count": len(rows),
            "mcc": dataset_mcc,
            "confusion_matrix": confusion_matrix,
            "predicted_positive_count": predicted_positive_count,
        }
    return threshold, {
        "datasets": sorted(str(value) for value in calibration["dataset"].unique()),
        "sample_count": len(calibration),
        "label_policy": (
            "rank-percentile >= 0.5 for continuous datasets; original 0/1 label "
            "for binary datasets"
        ),
        "weight_policy": "each dataset has equal total weight",
        "objective": "maximize dataset-balanced pooled MCC",
        "tie_breaker": "threshold closest to 0.5, then lower threshold",
        "weighted_mcc": weighted_mcc,
        "weighted_confusion_matrix": weighted_confusion,
        "unweighted_mcc": matthews_correlation_coefficient(
            predicted.astype(int).tolist(),
            binary_labels.astype(int).tolist(),
        ),
        "predicted_positive_count": int(predicted.sum()),
        "per_dataset": per_dataset,
    }


def best_dataset_balanced_threshold(
    scores: np.ndarray,
    actual: np.ndarray,
    weights: np.ndarray,
) -> tuple[float, float, dict[str, float]]:
    unique_scores = sorted(set(float(score) for score in scores))
    if not unique_scores:
        raise ValueError("Cannot calibrate a threshold without scores.")
    candidates = [unique_scores[0] - 1e-12]
    candidates.extend(
        (left + right) / 2.0
        for left, right in zip(unique_scores, unique_scores[1:])
    )
    candidates.append(unique_scores[-1] + 1e-12)
    best: tuple[tuple[float, float, float], float, dict[str, float]] | None = None
    for threshold in candidates:
        predicted = scores >= threshold
        confusion = weighted_confusion_matrix(predicted, actual, weights)
        mcc = mcc_from_confusion(confusion)
        key = (mcc, -abs(threshold - 0.5), -threshold)
        if best is None or key > best[0]:
            best = (key, threshold, confusion)
    assert best is not None
    return float(best[1]), float(best[0][0]), best[2]


def weighted_confusion_matrix(
    predicted: np.ndarray,
    actual: np.ndarray,
    weights: np.ndarray,
) -> dict[str, float]:
    return {
        "true_positive": float(weights[(predicted == 1) & (actual == 1)].sum()),
        "true_negative": float(weights[(predicted == 0) & (actual == 0)].sum()),
        "false_positive": float(weights[(predicted == 1) & (actual == 0)].sum()),
        "false_negative": float(weights[(predicted == 0) & (actual == 1)].sum()),
    }


def mcc_from_confusion(confusion: dict[str, float]) -> float:
    tp = confusion["true_positive"]
    tn = confusion["true_negative"]
    fp = confusion["false_positive"]
    fn = confusion["false_negative"]
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denominator == 0.0:
        return 0.0
    return (tp * tn - fp * fn) / denominator


def binary_metrics_at_threshold(
    rows: list[dict],
    threshold: float,
) -> tuple[float, dict[str, int], int]:
    actual = [int(float(row["readability_score"])) for row in rows]
    predicted = [int(float(row["score"]) >= threshold) for row in rows]
    confusion_matrix = {
        "true_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 1),
        "true_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 0),
        "false_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 0),
        "false_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 1),
    }
    return (
        matthews_correlation_coefficient(predicted, actual),
        confusion_matrix,
        sum(predicted),
    )


def write_model_artifact(
    *,
    model: Any,
    artifact_root: Path,
    score_model_name: str,
    selected_features: list[str],
    feature_category_counts: dict[str, int],
    ridge_alpha: float,
    seed: int,
    train: pd.DataFrame,
    fit_mask: np.ndarray,
    training_datasets: tuple[str, ...],
    classification_threshold: float | None,
    threshold_metrics: dict[str, Any] | None,
    feature_root: Path,
    embedding_feature_root: Path,
) -> Path:
    artifact_dir = artifact_root / score_model_name / EMBEDDING_SLUG
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "model.joblib"
    joblib.dump(model, model_path)

    imputer = model.named_steps["simpleimputer"]
    range_clipper = model.named_steps["trainingrangeclipper"]
    scaler = model.named_steps["standardscaler"]
    ridge = model.named_steps["ridge"]
    training_rows = train.loc[fit_mask, ["dataset", "task_id", "readability_score"]]
    feature_sources = []
    for dataset in training_datasets:
        for family, root in (
            ("base", feature_root),
            ("embedding", embedding_feature_root),
        ):
            path = root / dataset / EMBEDDING_SLUG / "features.csv"
            feature_sources.append(
                {
                    "dataset": dataset,
                    "family": family,
                    "path": str(path),
                    "sha256": sha256_file(path),
                }
            )
    manifest = {
        "artifact_format_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "name": score_model_name,
        "embedding_model": EMBEDDING_MODEL,
        "serialized_model": "model.joblib",
        "serialized_model_sha256": sha256_file(model_path),
        "libraries": {
            "python_model_format": "joblib",
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "training": {
            "datasets": list(training_datasets),
            "sample_count": int(fit_mask.sum()),
            "sample_count_by_dataset": {
                str(dataset): int(count)
                for dataset, count in training_rows.groupby("dataset").size().items()
            },
            "row_identity_sha256": sha256_records(training_rows),
            "target": (
                "per-dataset rank-percentile readability for continuous datasets; "
                "original 0/1 labels for binary datasets"
            ),
            "sample_weight": "inverse dataset size, normalized over the pooled training set",
            "feature_sources": feature_sources,
        },
        "features": {
            "count": len(selected_features),
            "ordered_names": selected_features,
            "category_counts": feature_category_counts,
        },
        "pipeline": {
            "steps": ["median_imputation", "training_range_clipping", "standardization", "bounded_ridge"],
            "ridge_alpha": ridge_alpha,
            "seed": seed,
            "imputer_statistics": imputer.statistics_.astype(float).tolist(),
            "training_feature_min": range_clipper.feature_min_.astype(float).tolist(),
            "training_feature_max": range_clipper.feature_max_.astype(float).tolist(),
            "scaler_mean": scaler.mean_.astype(float).tolist(),
            "scaler_scale": scaler.scale_.astype(float).tolist(),
            "ridge_coefficients": ridge.coef_.astype(float).tolist(),
            "ridge_intercept": float(ridge.intercept_),
            "prediction_bounds": [0.0, 1.0],
        },
        "classification": {
            "direction": "score >= threshold means readable/high",
            "threshold": classification_threshold,
            "calibration": threshold_metrics,
        },
    }
    manifest_path = artifact_dir / "model.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return artifact_dir


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_records(frame: pd.DataFrame) -> str:
    payload = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def best_binary_threshold(
    rows: list[dict],
) -> tuple[float | None, float | None, dict[str, int] | None, int | None]:
    scores = sorted({float(row["score"]) for row in rows})
    if not scores:
        return None, None, None, None
    candidates = [scores[0] - 1e-12]
    candidates.extend((left + right) / 2 for left, right in zip(scores, scores[1:]))
    candidates.append(scores[-1] + 1e-12)
    actual = [int(float(row["readability_score"])) for row in rows]
    best: tuple[float, float, dict[str, int], int] | None = None
    for threshold in candidates:
        predicted = [int(float(row["score"]) >= threshold) for row in rows]
        mcc = matthews_correlation_coefficient(predicted, actual)
        confusion_matrix = {
            "true_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 1),
            "true_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 0),
            "false_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 0),
            "false_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 1),
        }
        candidate = (threshold, mcc, confusion_matrix, sum(predicted))
        if best is None or candidate[1] > best[1]:
            best = candidate
    assert best is not None
    return best


def dataset_path(dataset: str) -> str:
    return str(DATASETS[dataset].path)


if __name__ == "__main__":
    main()
