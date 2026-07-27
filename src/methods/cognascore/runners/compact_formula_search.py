from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS
from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.cognascore.results import model_slug
from src.methods.cognascore.runners.common import dataset_output_name
from src.methods.cognascore.runners.feature_screen import _load_feature_family, _merge_tables


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")
TRAIN_DATASETS = ("scalabrino", "schnappinger", "dorn", "buse")
IDENTITY_COLUMNS = {"dataset", "task_id", "readability_score"}
EXCLUDED_FEATURES = {
    "base__generalized_score",
    "base__score",
    "base__supervised_score",
}
EXCLUDED_PREFIXES = (
    "embedding__kmeans_k_",
)
CORE_COGNASCORE_MARKERS = (
    "base__noise",
    "base__semantic_",
    "base__junk_",
    "base__cluster",
    "base__avg_cluster_diameter",
    "base__type_",
    "base__chunk_",
    "embedding__embedding_",
    "embedding__auto_dbscan_",
    "embedding__hdbscan_",
    "embedding__optics_",
    "embedding__auto_kmeans_",
    "embedding__auto_agglo_",
    "embedding__graph_",
)
NON_CORE_MARKERS = (
    "source_count",
    "available_source_count",
    "coverage_ratio",
    "unique_text_count",
    "algorithm_unique_text_count",
)
PRIOR_FEATURES = {
    "base__log_vocabulary_size",
    "base__vocabulary_size",
    "base__noise_ratio",
    "base__semantic_noise_ratio",
    "base__avg_cluster_diameter",
    "base__chunk_chars_mean",
    "base__chunk_chars_cv",
    "base__cluster_count",
    "base__type_logical_cluster_count",
    "base__type_control_flow_cluster_count",
    "base__type_control_flow_cluster_diameter_mean",
}


@dataclass(frozen=True)
class FeatureVariant:
    name: str
    source: str
    transform: str
    values: np.ndarray
    core: bool
    train_score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search compact interpretable CognaScore formulas with 2-3 transformed features."
    )
    parser.add_argument("datasets", nargs="*", type=Path, help="Dataset paths. Defaults to all code datasets.")
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--base-root", type=Path, default=Path("output/cognascore_features"))
    parser.add_argument("--embedding-root", type=Path, default=Path("output/cognascore_embedding_features"))
    parser.add_argument("--ridge-alpha", type=float, default=30.0)
    parser.add_argument("--top-candidates", type=int, default=100)
    parser.add_argument("--top-core-candidates", type=int, default=50)
    parser.add_argument("--max-combination-size", type=int, default=3, choices=(2, 3))
    parser.add_argument("--keep", type=int, default=80)
    parser.add_argument("-o", "--output", type=Path, default=Path("output/cognascore_compact_formula_search"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    dataset_names = [dataset_output_name(path) for path in dataset_paths]
    slug = model_slug(args.embedding_model)
    base_table = _load_feature_family(args.base_root, dataset_names, slug, prefix="base")
    embedding_table = _load_feature_family(args.embedding_root, dataset_names, slug, prefix="embedding")
    merged_rows, groups = _merge_tables(base_table, embedding_table)
    frame = _rows_to_frame(merged_rows)
    feature_names = [
        name
        for name in sorted(groups)
        if name not in EXCLUDED_FEATURES and not name.startswith(EXCLUDED_PREFIXES)
    ]
    variants = _candidate_variants(frame, feature_names, args)
    results = _search_combinations(frame, variants, args)
    output_dir = args.output / "cognascore_compact_formula_search" / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_results(output_dir / "results.csv", results)
    metadata = {
        "embedding_model": args.embedding_model,
        "datasets": dataset_names,
        "training_datasets": list(TRAIN_DATASETS),
        "ridge_alpha": args.ridge_alpha,
        "top_candidates": args.top_candidates,
        "top_core_candidates": args.top_core_candidates,
        "max_combination_size": args.max_combination_size,
        "candidate_variant_count": len(variants),
        "searched_combination_count": len(results),
        "core_constraint": "At least one selected feature variant must be a CognaScore chunk/cluster/embedding feature.",
        "excluded_features": sorted(EXCLUDED_FEATURES),
        "excluded_prefixes": list(EXCLUDED_PREFIXES),
        "best": results[: min(args.keep, len(results))],
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(output_dir / "results.csv")
    print(output_dir / "metadata.json")
    if results:
        print(json.dumps(results[0], indent=2, ensure_ascii=False))


def _rows_to_frame(merged_rows: Mapping[tuple[str, str], Mapping[str, float]]) -> pd.DataFrame:
    rows = []
    for (dataset, task_id), values in sorted(merged_rows.items()):
        row = {"dataset": dataset, "task_id": task_id}
        row.update(values)
        rows.append(row)
    return pd.DataFrame(rows)


def _candidate_variants(frame: pd.DataFrame, feature_names: Sequence[str], args: argparse.Namespace) -> list[FeatureVariant]:
    train_mask = frame["dataset"].isin(TRAIN_DATASETS).to_numpy()
    y = _rank_percentile_target(frame.loc[train_mask])
    variants: list[FeatureVariant] = []
    for feature in feature_names:
        raw = pd.to_numeric(frame[feature], errors="coerce").to_numpy(dtype=float)
        if not np.any(np.isfinite(raw)):
            continue
        fill = np.nanmedian(raw[np.isfinite(raw)])
        raw = np.where(np.isfinite(raw), raw, fill)
        for transform_name, transform in _transforms(raw):
            values = transform(raw)
            if not np.all(np.isfinite(values)) or float(np.nanstd(values[train_mask])) <= 1e-12:
                continue
            score = abs(_safe_spearman(y, values[train_mask]))
            variants.append(
                FeatureVariant(
                    name=f"{transform_name}({feature})" if transform_name != "identity" else feature,
                    source=feature,
                    transform=transform_name,
                    values=values,
                    core=_is_core_feature(feature),
                    train_score=score,
                )
            )
    variants.sort(key=lambda item: (item.train_score, item.core), reverse=True)
    selected = list(variants[: args.top_candidates])
    core_selected = [variant for variant in variants if variant.core][: args.top_core_candidates]
    prior_selected = [variant for variant in variants if variant.source in PRIOR_FEATURES]
    by_name = {variant.name: variant for variant in selected}
    by_name.update({variant.name: variant for variant in core_selected})
    by_name.update({variant.name: variant for variant in prior_selected})
    return list(by_name.values())


def _transforms(raw: np.ndarray) -> list[tuple[str, Callable[[np.ndarray], np.ndarray]]]:
    transforms: list[tuple[str, Callable[[np.ndarray], np.ndarray]]] = [
        ("identity", lambda x: x.astype(float)),
        ("rank", lambda x: _rank01(x)),
    ]
    finite = raw[np.isfinite(raw)]
    if len(finite) and np.min(finite) >= 0.0:
        transforms.extend(
            [
                ("log1p", lambda x: np.log1p(np.maximum(x, 0.0))),
                ("sqrt", lambda x: np.sqrt(np.maximum(x, 0.0))),
            ]
        )
    return transforms


def _search_combinations(
    frame: pd.DataFrame,
    variants: Sequence[FeatureVariant],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    train_mask = frame["dataset"].isin(TRAIN_DATASETS).to_numpy()
    y_train = _rank_percentile_target(frame.loc[train_mask])
    y_all = {
        dataset: group["readability_score"].astype(float).to_numpy()
        for dataset, group in frame.groupby("dataset")
    }
    indices_by_dataset = {
        dataset: group.index.to_numpy()
        for dataset, group in frame.groupby("dataset")
    }
    rows: list[dict[str, Any]] = []
    for size in range(2, args.max_combination_size + 1):
        for combo in itertools.combinations(variants, size):
            if not any(variant.core for variant in combo):
                continue
            if len({variant.source for variant in combo}) != len(combo):
                continue
            x = np.column_stack([variant.values for variant in combo])
            prediction, intercept, coefficients = _ridge_fit_predict(x[train_mask], y_train, x, args.ridge_alpha)
            metrics = _metrics_by_dataset(frame, prediction, y_all, indices_by_dataset)
            objective = _objective(metrics)
            rows.append(
                {
                    "feature_count": size,
                    "features": [variant.name for variant in combo],
                    "source_features": [variant.source for variant in combo],
                    "transforms": [variant.transform for variant in combo],
                    "core_features": [variant.name for variant in combo if variant.core],
                    "formula": _formula_text(intercept, coefficients, combo),
                    "train_all_metrics": metrics,
                    "leave_one_dataset_out_metrics": {},
                    "objective": objective,
                    "lodo_objective": {},
                    "scalabrino": _metric_value(metrics, "scalabrino"),
                    "schnappinger": _metric_value(metrics, "schnappinger"),
                    "dorn": _metric_value(metrics, "dorn"),
                    "buse": _metric_value(metrics, "buse"),
                    "mbjp": _metric_value(metrics, "mbjp"),
                    "jetbrains": _metric_value(metrics, "jetbrains"),
                    "lodo_scalabrino": None,
                    "lodo_schnappinger": None,
                    "lodo_dorn": None,
                    "lodo_buse": None,
                    "lodo_jetbrains": None,
                    "_x": x,
                }
            )
    rows.sort(
        key=lambda row: (
            row["objective"]["sota_hits"],
            row["objective"]["core_mean"],
            row["feature_count"] == 2,
        ),
        reverse=True,
    )
    for row in rows[: args.keep]:
        lodo = _lodo_metrics(frame, row.pop("_x"), args.ridge_alpha)
        row["leave_one_dataset_out_metrics"] = lodo
        row["lodo_objective"] = _objective(lodo)
        row["lodo_scalabrino"] = _metric_value(lodo, "scalabrino")
        row["lodo_schnappinger"] = _metric_value(lodo, "schnappinger")
        row["lodo_dorn"] = _metric_value(lodo, "dorn")
        row["lodo_buse"] = _metric_value(lodo, "buse")
        row["lodo_jetbrains"] = _metric_value(lodo, "jetbrains")
    for row in rows[args.keep :]:
        row.pop("_x", None)
    return rows


def _metrics_by_dataset(
    frame: pd.DataFrame,
    prediction: np.ndarray,
    y_by_dataset: Mapping[str, np.ndarray],
    indices_by_dataset: Mapping[str, np.ndarray],
) -> dict[str, dict[str, float | int | str | None]]:
    metrics = {}
    for dataset, indices in indices_by_dataset.items():
        labels = y_by_dataset[dataset]
        scores = prediction[indices]
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            value, threshold = _best_mcc(scores, labels.astype(int))
            metric = "mcc_best_threshold"
        else:
            value = _safe_spearman(labels, scores)
            threshold = None
            metric = "spearman"
        metrics[dataset] = {"n": len(indices), "metric": metric, "value": value, "threshold": threshold}
    return metrics


def _lodo_metrics(frame: pd.DataFrame, x: np.ndarray, ridge_alpha: float) -> dict[str, dict[str, float | int | str | None]]:
    metrics = {}
    for dataset in sorted(frame["dataset"].unique()):
        train_mask = frame["dataset"].isin([name for name in TRAIN_DATASETS if name != dataset]).to_numpy()
        test_mask = (frame["dataset"] == dataset).to_numpy()
        if not np.any(test_mask) or not np.any(train_mask):
            continue
        y_train = _rank_percentile_target(frame.loc[train_mask])
        prediction, _, _ = _ridge_fit_predict(x[train_mask], y_train, x[test_mask], ridge_alpha)
        labels = frame.loc[test_mask, "readability_score"].astype(float).to_numpy()
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            value, threshold = _best_mcc(prediction, labels.astype(int))
            metric = "mcc_best_threshold"
        else:
            value = _safe_spearman(labels, prediction)
            threshold = None
            metric = "spearman"
        metrics[dataset] = {"n": int(np.sum(test_mask)), "metric": metric, "value": value, "threshold": threshold}
    return metrics


def _ridge_fit_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_predict: np.ndarray,
    alpha: float,
) -> tuple[np.ndarray, float, np.ndarray]:
    mean = np.mean(x_train, axis=0)
    std = np.std(x_train, axis=0)
    std = np.where(std <= 1e-12, 1.0, std)
    y_mean = float(np.mean(y_train))
    x_train_scaled = (x_train - mean) / std
    centered_y = y_train - y_mean
    gram = x_train_scaled.T @ x_train_scaled
    rhs = x_train_scaled.T @ centered_y
    coef_scaled = np.linalg.solve(gram + alpha * np.eye(gram.shape[0]), rhs)
    coef_original = coef_scaled / std
    intercept = y_mean - float(mean @ coef_original)
    prediction = x_predict @ coef_original + intercept
    return prediction, intercept, coef_original


def _rank_percentile_target(frame: pd.DataFrame) -> np.ndarray:
    frame = frame.reset_index(drop=True)
    target = np.zeros(len(frame), dtype=float)
    for _, indices in frame.groupby("dataset").groups.items():
        labels = frame.loc[indices, "readability_score"].astype(float)
        if set(labels.unique()).issubset({0.0, 1.0}):
            values = labels.to_numpy(dtype=float)
        else:
            ranks = labels.rank(method="average").to_numpy(dtype=float)
            values = (ranks - 1.0) / max(len(labels) - 1.0, 1.0)
        target[list(indices)] = values
    return target


def _objective(metrics: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    core = ["scalabrino", "schnappinger", "dorn", "buse"]
    thresholds = {"scalabrino": 0.5919, "schnappinger": 0.6057, "dorn": 0.5857, "jetbrains": 0.3594}
    values = {dataset: _metric_value(metrics, dataset) for dataset in core}
    finite_values = [value for value in values.values() if value is not None and math.isfinite(value)]
    hits = {
        dataset: (value := _metric_value(metrics, dataset)) is not None and math.isfinite(value) and value >= threshold
        for dataset, threshold in thresholds.items()
    }
    return {
        "core_mean": float(np.mean(finite_values)) if finite_values else None,
        "sota_hits": int(sum(hits.values())),
        "sota_hits_by_dataset": hits,
    }


def _metric_value(metrics: Mapping[str, Mapping[str, Any]], dataset: str) -> float | None:
    value = metrics.get(dataset, {}).get("value")
    return None if value is None else float(value)


def _best_mcc(scores: np.ndarray, labels: np.ndarray) -> tuple[float, float | None]:
    if len(scores) == 0:
        return math.nan, None
    order = np.argsort(scores)
    sorted_scores = scores[order]
    sorted_labels = labels.astype(int)[order]
    total_pos = int(np.sum(sorted_labels == 1))
    total_neg = int(np.sum(sorted_labels == 0))
    # Threshold below the minimum predicts every row positive.
    tp = total_pos
    fp = total_neg
    tn = 0
    fn = 0
    best_value = _mcc_counts(tp, tn, fp, fn)
    best_threshold = float(sorted_scores[0] - 1e-12)
    for index, label in enumerate(sorted_labels):
        if label == 1:
            tp -= 1
            fn += 1
        else:
            fp -= 1
            tn += 1
        if index + 1 < len(sorted_scores) and sorted_scores[index + 1] == sorted_scores[index]:
            continue
        threshold = (
            float((sorted_scores[index] + sorted_scores[index + 1]) / 2.0)
            if index + 1 < len(sorted_scores)
            else float(sorted_scores[index] + 1e-12)
        )
        value = _mcc_counts(tp, tn, fp, fn)
        if value > best_value:
            best_value = value
            best_threshold = threshold
    return float(best_value), best_threshold


def _mcc_counts(tp: int, tn: int, fp: int, fn: int) -> float:
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denominator == 0:
        return 0.0
    return float((tp * tn - fp * fn) / denominator)


def _safe_spearman(left: Sequence[float], right: Sequence[float]) -> float:
    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    if len(left_array) < 2 or np.std(left_array) <= 1e-12 or np.std(right_array) <= 1e-12:
        return 0.0
    left_rank = rankdata(left_array, method="average")
    right_rank = rankdata(right_array, method="average")
    value = float(np.corrcoef(left_rank, right_rank)[0, 1])
    return 0.0 if not math.isfinite(value) else float(value)


def _rank01(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    return ranks / max(len(values) - 1.0, 1.0)


def _is_core_feature(feature: str) -> bool:
    return feature.startswith(CORE_COGNASCORE_MARKERS) and not any(marker in feature for marker in NON_CORE_MARKERS)


def _formula_text(intercept: float, coefficients: Sequence[float], variants: Sequence[FeatureVariant]) -> str:
    parts = [f"{intercept:.9g}"]
    for coefficient, variant in zip(coefficients, variants):
        sign = "+" if coefficient >= 0 else "-"
        parts.append(f" {sign} {abs(float(coefficient)):.9g} * {variant.name}")
    return "score = " + "".join(parts)


def _write_results(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "feature_count",
        "scalabrino",
        "schnappinger",
        "dorn",
        "buse",
        "jetbrains",
        "mbjp",
        "lodo_scalabrino",
        "lodo_schnappinger",
        "lodo_dorn",
        "lodo_buse",
        "lodo_jetbrains",
        "features",
        "core_features",
        "formula",
        "objective",
        "lodo_objective",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    **{
                        key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                        for key, value in row.items()
                        if key in fieldnames
                    },
                }
            )


if __name__ == "__main__":
    main()
