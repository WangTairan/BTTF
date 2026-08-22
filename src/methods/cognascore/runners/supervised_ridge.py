from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.methods.cognascore.feature_schema import namespaced_feature
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.results import model_slug


EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_SLUG = model_slug(EMBEDDING_MODEL)
ALL_DATASETS = (
    "scalabrino",
    "schnappinger",
    "dorn",
    "buse",
    "mbjp",
    "jetbrains",
    "generated_readability_90",
    "generated_binary_readability",
)
TRAIN_DATASETS = ("buse", "dorn", "scalabrino")
EXTERNAL_DATASETS = ("schnappinger", "jetbrains", "mbjp")
SCORE_MODEL_NAME = "consensus24_6dataset_nomic"
TRAINING_DROP_MIDDLE = 0.0

SELECTED_FEATURES = [
    "base__visual_operator_density",
    "base__byte_entropy",
    "base__blank_line_ratio",
    "base__chunk_y_std",
    "base__visual_identifier_area_ratio",
    "base__type_literal_ratio",
    "base__visual_period_y_mean",
    "embedding__structural_core__auto_kmeans_selected_k",
    "base__max_line_length",
    "embedding__only_identifier__embedding_first_pc_explained_variance",
    "base__chunk_chars_cv",
    "base__type_unused_import_count",
    "base__type_regex_ratio",
    "base__visual_keyword_area_ratio",
    "base__std_indent",
    "base__type_bitwise_ratio",
    "embedding__structural_core__optics_cluster_type_entropy_mean",
    "base__indent_transition_mean",
    "base__identifier_single_letter_ratio",
    "base__log_max_chunk_chars",
    "embedding__structural_core__optics_noise_ratio",
    "base__identifier_length_cv",
    "compression__zlib_line_ratio_std",
    "base__long_line_ratio_100",
]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize the frozen CognaScore ML Consensus-24 Ridge model."
    )
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument(
        "--embedding-feature-root",
        type=Path,
        default=EMBEDDING_FEATURE_ROOT,
    )
    parser.add_argument("--output-root", type=Path, default=Path("results/methods"))
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--method", default="cognascore_ml_consensus24")
    parser.add_argument("--score-model-name", default=SCORE_MODEL_NAME)
    parser.add_argument(
        "--selected-features-metadata",
        type=Path,
        help="Experiment metadata containing selected_features. Defaults to the frozen Consensus-24 list.",
    )
    parser.add_argument(
        "--train-dataset",
        action="append",
        default=[],
        help="Dataset used to fit the final ML Ridge model. Can be repeated. Defaults to buse, dorn, scalabrino.",
    )
    parser.add_argument(
        "--report-dataset",
        action="append",
        default=[],
        help="Dataset to materialize predictions for. Can be repeated. Defaults to the six standard datasets.",
    )
    args = parser.parse_args()
    selected_features = (
        load_selected_features(args.selected_features_metadata)
        if args.selected_features_metadata
        else list(SELECTED_FEATURES)
    )
    feature_category_counts = feature_category_counts_for(selected_features)

    report_datasets = tuple(args.report_dataset or ALL_DATASETS)
    train_datasets = tuple(args.train_dataset or TRAIN_DATASETS)
    frames = {
        dataset: load_combined_features(dataset, args.feature_root, args.embedding_feature_root, selected_features)
        for dataset in sorted(set((*train_datasets, *report_datasets)))
    }
    missing_train = [dataset for dataset in train_datasets if dataset not in frames]
    if missing_train:
        raise SystemExit(f"Unknown training datasets: {missing_train}")
    train = pd.concat([frames[name] for name in train_datasets], ignore_index=True)
    fit_mask = training_middle_keep_mask(train, TRAINING_DROP_MIDDLE)
    ridge = fit_ridge(train, fit_mask, args.ridge_alpha, selected_features)
    coefficients = ridge_coefficients(ridge, selected_features)
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
    }


def fit_ridge(frame: pd.DataFrame, fit_mask: np.ndarray, ridge_alpha: float, selected_features: list[str]):
    target = regression_target(frame)
    sample_weight = dataset_balanced_sample_weight(frame, fit_mask)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=ridge_alpha),
    )
    x_train = frame.loc[fit_mask, selected_features].to_numpy(dtype=float)
    model.fit(x_train, target[fit_mask], ridge__sample_weight=sample_weight[fit_mask])
    return model


def load_combined_features(
    dataset: str,
    feature_root: Path,
    embedding_feature_root: Path,
    selected_features: list[str],
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


def training_middle_keep_mask(frame: pd.DataFrame, drop_middle: float) -> np.ndarray:
    if not 0.0 <= drop_middle < 1.0:
        raise ValueError("drop_middle must be in [0, 1).")
    keep = np.ones(len(frame), dtype=bool)
    if drop_middle <= 0.0:
        return keep
    for _, indices in frame.groupby("dataset").groups.items():
        labels = frame.loc[indices, "readability_score"].astype(float).to_numpy(dtype=float)
        unique = set(labels.tolist())
        if unique.issubset({0.0, 1.0}):
            continue
        threshold = float(np.median(labels))
        distances = np.abs(labels - threshold)
        cutoff = float(np.quantile(distances, drop_middle))
        keep[np.asarray(list(indices), dtype=int)] = distances > cutoff
    return keep


def dataset_balanced_sample_weight(frame: pd.DataFrame, eligible_mask: np.ndarray) -> np.ndarray:
    eligible = pd.Series(eligible_mask, index=frame.index)
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
    binary = dataset == "jetbrains" or (
        bool(valid)
        and all(row.get("metadata", {}).get("evaluation_metric") == "mcc" for row in valid)
    )

    threshold = None
    rho = None
    mcc = None
    confusion_matrix = None
    predicted_positive_count = None
    if binary:
        threshold, mcc, confusion_matrix, predicted_positive_count = best_binary_threshold(valid)
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
        "classification_threshold_policy": "best_on_dataset" if binary else None,
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
                "Frozen 24-feature list produced by five-embedding-model consensus "
                "stability screening across the six development datasets, followed "
                "by correlation filtering"
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
            "training_drop_middle": TRAINING_DROP_MIDDLE,
            "training_drop_middle_scope": "none",
            "target": (
                "per-dataset rank-percentile readability for continuous datasets; "
                "original binary labels for binary datasets"
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
            "limitations": (
                "The final Ridge fit uses three datasets, but the frozen feature list "
                "was selected using all six development datasets. Results on those six "
                "datasets are development-benchmark results, not untouched external tests."
            ),
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
    return {
        "scalabrino": "datasets/scalabrino/dataset",
        "schnappinger": "datasets/schnappinger",
        "dorn": "datasets/dorn/dataset",
        "buse": "datasets/buse",
        "mbjp": "datasets/mbjp_dev_dataset/readability_dataset.json",
        "jetbrains": "datasets/jetbrains",
        "generated_readability_90": "datasets/readability_dataset_90.jsonl",
        "generated_binary_readability": "datasets/readability_binary.jsonl",
    }.get(dataset, dataset)


if __name__ == "__main__":
    main()
