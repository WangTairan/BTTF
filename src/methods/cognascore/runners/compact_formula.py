from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
import pandas as pd

from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.cognascore.results import model_slug
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT


EMBEDDING_MODELS = {
    "nomic": "nomic-ai/nomic-embed-text-v1.5",
    "qwen": "Qwen/Qwen3-Embedding-0.6B",
    "jina": "jinaai/jina-embeddings-v2-base-code",
}
EMBEDDING_MODEL = EMBEDDING_MODELS["qwen"]
EMBEDDING_SLUG = model_slug(EMBEDDING_MODEL)
METHOD = "cognascore_compact"
DATASETS = (
    "scalabrino",
    "schnappinger",
    "dorn",
    "buse",
    "mbjp",
    "jetbrains",
)
DEFAULT_DATASETS = DATASETS[:6]

# Fitted on Scalabrino + Schnappinger + Dorn + Buse rank-percentile labels.
# Constraint: compact interpretable formula using layout, chunk geometry, and embedding-clustering signals.
FEATURES = (
    "log1p(base__operator_density)",
    "sqrt(base__log_loc)",
    "log1p(base__std_chunks_per_source_line)",
    "log1p(qwen__only_identifier__auto_kmeans_cluster_diameter_max)",
)
INTERCEPT = 1.43341466
COEFFICIENTS = {
    "log1p(base__operator_density)": -0.30461071,
    "sqrt(base__log_loc)": -0.227365225,
    "log1p(base__std_chunks_per_source_line)": -0.0463927146,
    "log1p(qwen__only_identifier__auto_kmeans_cluster_diameter_max)": -0.196472171,
}
SEARCH_RESULT = {
    "scalabrino": 0.4915,
    "schnappinger": 0.6063,
    "dorn": 0.5982,
    "buse": 0.6809,
    "jetbrains": 0.4121,
    "mbjp": 0.5833,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize the compact CognaScore formula.")
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--output-root", type=Path, default=Path("results/methods"))
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DATASETS,
        help="Dataset to materialize. Can be repeated. Defaults to all compact datasets.",
    )
    args = parser.parse_args()
    for dataset in args.dataset or DEFAULT_DATASETS:
        frame = load_combined_features(dataset, args.feature_root, args.embedding_feature_root)
        predictions = predict(frame)
        write_summary(dataset=dataset, frame=frame, predictions=predictions, output_root=args.output_root)


def load_combined_features(dataset: str, feature_root: Path, embedding_feature_root: Path) -> pd.DataFrame:
    default_slug = model_slug(EMBEDDING_MODELS["nomic"])
    base_path = feature_root / dataset / default_slug / "features.csv"
    base = pd.read_csv(base_path)
    id_columns = ["dataset", "task_id", "readability_score"]
    base_features = base.rename(
        columns={column: f"base__{column}" for column in base.columns if column not in id_columns}
    ).copy()
    merge_columns = ["dataset", "task_id", "_feature_row_occurrence"]
    base_features["_feature_row_occurrence"] = base_features.groupby(["dataset", "task_id"]).cumcount()
    merged = base_features
    required_embedding_prefixes = {
        feature.split("__", 1)[0]
        for feature in (raw_feature_name(feature) for feature in FEATURES)
        if "__" in feature and feature.split("__", 1)[0] in EMBEDDING_MODELS
    }
    for prefix, model in EMBEDDING_MODELS.items():
        if prefix not in required_embedding_prefixes:
            continue
        slug = model_slug(model)
        embedding_path = embedding_feature_root / dataset / slug / "features.csv"
        embedding = pd.read_csv(embedding_path)
        embedding_features = embedding.rename(
            columns={column: f"{prefix}__{column}" for column in embedding.columns if column not in id_columns}
        ).copy()
        embedding_features["_feature_row_occurrence"] = embedding_features.groupby(["dataset", "task_id"]).cumcount()
        embedding_features = embedding_features.drop(columns=["readability_score"])
        previous_len = len(merged)
        merged = merged.merge(
            embedding_features,
            on=merge_columns,
            how="inner",
            validate="one_to_one",
        )
        if len(merged) != previous_len or len(merged) != len(embedding_features):
            raise ValueError(
                f"Feature identity mismatch for {dataset}/{prefix}: "
                f"base={previous_len}, embedding={len(embedding_features)}, merged={len(merged)}"
            )
    return merged.drop(columns=["_feature_row_occurrence"])


def predict(frame: pd.DataFrame) -> np.ndarray:
    score = np.full(len(frame), INTERCEPT, dtype=float)
    for feature, coefficient in COEFFICIENTS.items():
        values = transform_feature(frame, feature)
        score += coefficient * values
    return score


def raw_feature_name(feature: str) -> str:
    if feature.startswith("log1p(") and feature.endswith(")"):
        return feature[6:-1]
    if feature.startswith("sqrt(") and feature.endswith(")"):
        return feature[5:-1]
    return feature


def transform_feature(frame: pd.DataFrame, feature: str) -> np.ndarray:
    if feature.startswith("log1p(") and feature.endswith(")"):
        raw_name = feature[6:-1]
        values = raw_feature(frame, raw_name)
        return np.log1p(np.maximum(values, 0.0))
    if feature.startswith("sqrt(") and feature.endswith(")"):
        raw_name = feature[5:-1]
        values = raw_feature(frame, raw_name)
        return np.sqrt(np.maximum(values, 0.0))
    return raw_feature(frame, feature)


def raw_feature(frame: pd.DataFrame, raw_name: str) -> np.ndarray:
    values = pd.to_numeric(frame[raw_name], errors="coerce").to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    fill = float(np.median(finite)) if len(finite) else 0.0
    return np.where(np.isfinite(values), values, fill)


def write_summary(*, dataset: str, frame: pd.DataFrame, predictions: np.ndarray, output_root: Path) -> None:
    rows = []
    for record, score in zip(frame.to_dict("records"), predictions):
        rows.append(
            {
                "task_id": str(record["task_id"]),
                "readability_score": none_if_nan(record.get("readability_score")),
                "method": METHOD,
                "score": float(score),
                "result": {
                    "score": float(score),
                    "formula": formula_text(),
                    "score_model": "compact_4_feature_formula",
                    "operator_density": none_if_nan(record.get("base__operator_density")),
                    "log_loc": none_if_nan(record.get("base__log_loc")),
                    "std_chunks_per_source_line": none_if_nan(record.get("base__std_chunks_per_source_line")),
                    "qwen_only_identifier_auto_kmeans_cluster_diameter_max": none_if_nan(
                        record.get("qwen__only_identifier__auto_kmeans_cluster_diameter_max")
                    ),
                },
                "metadata": {},
            }
        )
    valid = [
        row
        for row in rows
        if row["readability_score"] is not None
        and row["score"] is not None
        and math.isfinite(float(row["score"]))
    ]
    binary = dataset == "jetbrains"
    rho = None
    mcc = None
    threshold = None
    confusion_matrix = None
    predicted_positive_count = None
    if binary:
        threshold, mcc, confusion_matrix, predicted_positive_count = best_binary_threshold(valid)
    elif len(valid) >= 2:
        rho = spearman([float(row["score"]) for row in valid], [float(row["readability_score"]) for row in valid])
    payload = {
        "dataset": dataset_path(dataset),
        "method": METHOD,
        "model": EMBEDDING_MODEL,
        "configuration": "compact-4-feature-qwen-formula",
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
            "name": "compact_4_feature_qwen_formula",
            "training_policy": (
                "Ridge formula fit on Scalabrino + Schnappinger + Dorn + Buse "
                "rank-percentile labels."
            ),
            "feature_selection": (
                "Multi-start compact search over interpretable features. Layout, chunk "
                "geometry, embedding geometry, and adaptive clustering features are allowed."
            ),
            "training_datasets": ["scalabrino", "schnappinger", "dorn", "buse"],
            "target": "per-dataset rank percentile readability",
            "selected_feature_count": len(FEATURES),
            "selected_features": list(FEATURES),
            "formula": formula_text(),
            "coefficients": COEFFICIENTS,
            "intercept": INTERCEPT,
            "search_result": SEARCH_RESULT,
            "limitations": (
                "This compact formula prioritizes interpretability; its Scalabrino "
                "score is lower than the high-feature CognaScore route."
            ),
        },
    }
    output_dir = output_root / METHOD / dataset / EMBEDDING_SLUG
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "summary.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def formula_text() -> str:
    return (
        "score = 1.43341466"
        " - 0.30461071 * log1p(operator_density)"
        " - 0.227365225 * sqrt(log_LOC)"
        " - 0.0463927146 * log1p(std_chunks_per_source_line)"
        " - 0.196472171 * log1p(qwen_only_identifier_auto_kmeans_cluster_diameter_max)"
    )


def none_if_nan(value: Any) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    return None if math.isnan(numeric) else numeric


def best_binary_threshold(rows: list[dict]) -> tuple[float | None, float | None, dict[str, int] | None, int | None]:
    scores = sorted({float(row["score"]) for row in rows})
    if not scores:
        return None, None, None, None
    candidates = [scores[0] - 1e-12]
    candidates.extend((left + right) / 2 for left, right in zip(scores, scores[1:]))
    candidates.append(scores[-1] + 1e-12)
    actual = [int(float(row["readability_score"])) for row in rows]
    best = None
    for threshold in candidates:
        predicted = [int(float(row["score"]) >= threshold) for row in rows]
        value = matthews_correlation_coefficient(predicted, actual)
        confusion_matrix = {
            "true_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 1),
            "true_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 0),
            "false_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 0),
            "false_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 1),
        }
        candidate = (threshold, value, confusion_matrix, sum(predicted))
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
    }[dataset]


if __name__ == "__main__":
    main()
