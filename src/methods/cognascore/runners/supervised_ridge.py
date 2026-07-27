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
from src.methods.cognascore.results import model_slug


EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_SLUG = model_slug(EMBEDDING_MODEL)
TRAIN_DATASETS = ("scalabrino", "schnappinger", "dorn")
ALL_DATASETS = ("scalabrino", "schnappinger", "dorn", "buse", "mbjp", "jetbrains")

SELECTED_FEATURES = [
    "base__byte_entropy",
    "base__visual_identifier_area_ratio",
    "base__visual_keyword_identifier_area_ratio",
    "base__visual_period_dft_energy",
    "base__visual_operator_density",
    "base__type_assignment_cluster_diameter_mean",
    "base__type_control_flow_cluster_count",
    "base__type_control_flow_cluster_diameter_mean",
    "base__chunk_chars_cv",
    "base__type_declaration_cluster_diameter_std",
    "base__max_indent",
    "base__type_comparison_cluster_size_mean",
    "base__type_logical_cluster_count",
    "base__blank_line_ratio",
    "base__max_line_length",
]

# Mean held-out metrics from repeated dataset-aware 80/20 evaluation over
# Scalabrino, Schnappinger, and Dorn. Features were selected by backward
# elimination and group ablation from the 20-feature development set.
# base__generalized_score was excluded.
REPEATED_80_20_METRICS = {
    "scalabrino": {"spearman": 0.6234, "valid_count": 200},
    "schnappinger": {"spearman": 0.6483, "valid_count": 304},
    "dorn": {"spearman": 0.6655, "valid_count": 360},
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize the supervised 15-feature CognaScore Ridge model."
    )
    parser.add_argument("--feature-root", type=Path, default=Path("output/cognascore_features"))
    parser.add_argument(
        "--embedding-feature-root",
        type=Path,
        default=Path("output/cognascore_embedding_features"),
    )
    parser.add_argument("--output-root", type=Path, default=Path("output/cognascore"))
    parser.add_argument("--ridge-alpha", type=float, default=1000.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    frames = {dataset: load_combined_features(dataset, args.feature_root, args.embedding_feature_root) for dataset in ALL_DATASETS}
    train = pd.concat([frames[dataset] for dataset in TRAIN_DATASETS], ignore_index=True)
    target = rank_percentile_target(train)

    ridge = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=args.ridge_alpha),
    )
    x_train = train[SELECTED_FEATURES].to_numpy(dtype=float)
    ridge.fit(x_train, target)
    coefficients = ridge_coefficients(ridge)

    for dataset, frame in frames.items():
        x = frame[SELECTED_FEATURES].to_numpy(dtype=float)
        predictions = ridge.predict(x)
        write_summary(
            dataset=dataset,
            frame=frame,
            predictions=predictions,
            output_root=args.output_root,
            ridge_alpha=args.ridge_alpha,
            seed=args.seed,
            coefficients=coefficients,
        )


def load_combined_features(dataset: str, feature_root: Path, embedding_feature_root: Path) -> pd.DataFrame:
    base_path = feature_root / dataset / EMBEDDING_SLUG / "features.csv"
    embedding_path = embedding_feature_root / dataset / EMBEDDING_SLUG / "features.csv"
    base = pd.read_csv(base_path)
    embedding = pd.read_csv(embedding_path)

    id_columns = ["dataset", "task_id", "readability_score"]
    base_features = base.rename(
        columns={column: f"base__{column}" for column in base.columns if column not in id_columns}
    ).copy()
    embedding_features = embedding.rename(
        columns={column: f"embedding__{column}" for column in embedding.columns if column not in id_columns}
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
    missing = [feature for feature in SELECTED_FEATURES if feature not in merged.columns]
    if missing:
        raise KeyError(f"Missing selected features for {dataset}: {missing}")
    return merged


def rank_percentile_target(frame: pd.DataFrame) -> np.ndarray:
    values = np.zeros(len(frame), dtype=float)
    for _, indices in frame.groupby("dataset").groups.items():
        labels = frame.loc[indices, "readability_score"].astype(float)
        ranks = labels.rank(method="average")
        denom = max(len(labels) - 1, 1)
        values[list(indices)] = (ranks.to_numpy() - 1.0) / denom
    return values


def write_summary(
    *,
    dataset: str,
    frame: pd.DataFrame,
    predictions: np.ndarray,
    output_root: Path,
    ridge_alpha: float,
    seed: int,
    coefficients: dict[str, float],
) -> None:
    previous_rows = load_previous_rows(dataset)
    rows = []
    for record, score in zip(frame.to_dict("records"), predictions):
        task_id = str(record["task_id"])
        previous = previous_rows.get(task_id, {})
        result = previous.get("result") if isinstance(previous.get("result"), dict) else {}
        updated_result = dict(result)
        updated_result.update(
            {
                "score": float(score),
                "supervised_score": float(score),
                "score_model": "ssd_15_feature_ridge",
            }
        )
        rows.append(
            {
                "task_id": task_id,
                "readability_score": none_if_nan(record.get("readability_score")),
                "method": "cognascore",
                "score": float(score),
                "result": updated_result,
                "metadata": previous.get("metadata", {}),
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
    metric_policy = "train_all_prediction_metric"
    if dataset in REPEATED_80_20_METRICS:
        rho = REPEATED_80_20_METRICS[dataset]["spearman"]
        metric_policy = "mean held-out Spearman over repeated dataset-aware 80/20 evaluation"
    elif binary:
        threshold, mcc, confusion_matrix, predicted_positive_count = best_binary_threshold(valid)
    elif len(valid) >= 2:
        rho = spearman(
            [float(row["score"]) for row in valid],
            [float(row["readability_score"]) for row in valid],
        )

    payload = {
        "dataset": dataset_path(dataset),
        "method": "cognascore",
        "model": EMBEDDING_MODEL,
        "configuration": "nomic-ai-nomic-embed-text-v1.5__ssd-15feat-ridge1000",
        "embedding_model": EMBEDDING_MODEL,
        "dbscan": {"eps": 0.18, "min_pts": 2},
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
            "name": "ssd_15_feature_ridge",
            "training_policy": "final visualized predictions fit on Scalabrino + Schnappinger + Dorn; reported Scalabrino/Schnappinger/Dorn headline metrics are repeated dataset-aware 80/20 held-out means.",
            "metric_policy": metric_policy,
            "feature_selection": "backward elimination and group ablation from a 20-feature development set under repeated dataset-aware 80/20 validation",
            "excluded_features": ["base__generalized_score"],
            "training_datasets": list(TRAIN_DATASETS),
            "training_sample_count": 864,
            "target": "per-dataset rank percentile readability",
            "final_model": f"Ridge(alpha={ridge_alpha:g}) with median imputation and standardization",
            "ridge_alpha": ridge_alpha,
            "seed": seed,
            "selected_feature_count": len(SELECTED_FEATURES),
            "selected_features": SELECTED_FEATURES,
            "standardized_coefficients": coefficients,
            "limitations": "This is a supervised multi-dataset CognaScore model. It excludes stacked/model-output features, but it is not a single-dataset transfer setting.",
        },
    }
    output_dir = output_root / dataset / EMBEDDING_SLUG
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "summary.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def load_previous_rows(dataset: str) -> dict[str, dict[str, Any]]:
    path = Path("output/cognascore") / dataset / EMBEDDING_SLUG / "summary.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(row.get("task_id")): row for row in data.get("results", [])}


def none_if_nan(value: Any) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if math.isnan(numeric):
        return None
    return numeric


def ridge_coefficients(model: Any) -> dict[str, float]:
    ridge = model.named_steps["ridge"]
    return {
        feature: float(coef)
        for feature, coef in zip(SELECTED_FEATURES, ridge.coef_)
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
    }[dataset]


if __name__ == "__main__":
    main()
