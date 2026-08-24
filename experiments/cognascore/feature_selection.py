from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.impute import SimpleImputer
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, balanced_accuracy_score, matthews_corrcoef, roc_auc_score
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.experiments.paths import result_dir
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS

from src.methods.cognascore.feature_schema import namespaced_feature
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)
from src.methods.cognascore.results import model_slug
from src.methods.cognascore.modeling import BoundedRidge, TrainingRangeClipper
from src.methods.cognascore.dataset_io import dataset_output_name


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")
DEFAULT_SELECTION_DATASETS = ("buse", "dorn", "scalabrino")
DEFAULT_EXTERNAL_DATASETS = ("schnappinger", "jetbrains", "mbjp")
IDENTITY_COLUMNS = {"dataset", "task_id", "readability_score"}
CORE_SOTA_THRESHOLDS = {
    "scalabrino": 0.5919,
    "jetbrains": 0.3594,
    "dorn": 0.5857,
    "schnappinger": 0.6057,
}


@dataclass(frozen=True)
class FeatureTable:
    rows: dict[tuple[str, str, int], dict[str, float]]
    groups: dict[str, str]
    columns: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Screen CognaScore feature tables with sparse logistic regression. "
            "Continuous datasets are binarized within dataset by label median by default."
        )
    )
    parser.add_argument(
        "datasets",
        nargs="*",
        type=Path,
        help="Dataset paths. Defaults to all current code datasets.",
    )
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument(
        "--feature-source",
        choices=(
            "base",
            "embedding",
            "combined",
        ),
        default="combined",
        help="Which feature table family to screen.",
    )
    parser.add_argument(
        "--continuous-threshold",
        choices=("median", "mean"),
        default="median",
        help="How to binarize continuous labels inside each dataset.",
    )
    parser.add_argument(
        "--drop-middle",
        type=float,
        default=0.0,
        help="Drop this central fraction of continuous labels per dataset before binarization.",
    )
    parser.add_argument(
        "--drop-middle-scope",
        choices=("all", "training"),
        default="all",
        help=(
            "Where --drop-middle applies. 'all' preserves the historical behavior and removes rows "
            "before both training and evaluation. 'training' removes middle rows only from feature "
            "screening/final fitting, then evaluates on the complete datasets."
        ),
    )
    parser.add_argument("--c", type=float, default=0.05, help="Inverse L1 regularization strength.")
    parser.add_argument("--cv", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability-rounds", type=int, default=200)
    parser.add_argument(
        "--stability-sample-fraction",
        type=float,
        default=0.7,
        help="Fraction sampled independently from each selection dataset in every stability round.",
    )
    parser.add_argument(
        "--selection-dataset",
        action="append",
        default=[],
        help=(
            "Dataset used for feature selection and final Ridge fitting. Can be repeated. "
            "Defaults to buse, dorn, scalabrino."
        ),
    )
    parser.add_argument(
        "--external-dataset",
        action="append",
        default=[],
        help=(
            "Dataset kept out of feature selection and fitting, then reported as external validation. "
            "Can be repeated. Defaults to schnappinger, jetbrains, mbjp."
        ),
    )
    parser.add_argument("--top", type=int, default=80)
    parser.add_argument(
        "--select-top",
        type=int,
        default=40,
        help="Use this many screened features in the final model.",
    )
    parser.add_argument(
        "--final-model",
        choices=("ridge", "elasticnet", "logistic_l1"),
        default="ridge",
        help="Model fitted after L1 feature screening for report-metric evaluation.",
    )
    parser.add_argument(
        "--exclude-feature",
        action="append",
        default=[],
        help="Feature to remove before screening/final fitting. Can be repeated.",
    )
    parser.add_argument(
        "--exclude-feature-prefix",
        action="append",
        default=[],
        help="Remove every feature whose name starts with this prefix. Can be repeated.",
    )
    parser.add_argument("--ridge-alpha", type=float, default=30.0)
    parser.add_argument("--elasticnet-alpha", type=float, default=0.02)
    parser.add_argument("--elasticnet-l1-ratio", type=float, default=0.2)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT,
        help="Experiment-results root. Defaults to results/experiments/cognascore/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    dataset_names = [dataset_output_name(path) for path in dataset_paths]
    slug = model_slug(args.embedding_model)

    use_base = args.feature_source in {"base", "combined"}
    use_embedding = args.feature_source in {"embedding", "combined"}
    base_table = (
        _load_feature_family(args.base_root, dataset_names, slug, prefix="base")
        if use_base
        else None
    )
    embedding_table = (
        _load_feature_family(args.embedding_root, dataset_names, slug, prefix="embedding")
        if use_embedding
        else None
    )
    merged_rows, groups = _merge_tables(base_table, embedding_table)
    prepared = _prepare_matrix(
        merged_rows,
        groups,
        continuous_threshold=args.continuous_threshold,
        drop_middle=args.drop_middle if args.drop_middle_scope == "all" else 0.0,
    )
    x, y, sample_weight, feature_names, row_metadata = prepared
    selection_datasets = tuple(args.selection_dataset or DEFAULT_SELECTION_DATASETS)
    external_datasets = tuple(args.external_dataset or DEFAULT_EXTERNAL_DATASETS)
    selection_mask = _dataset_mask(row_metadata, selection_datasets)
    external_mask = _dataset_mask(row_metadata, external_datasets)
    training_middle_keep_mask = (
        _middle_keep_mask(row_metadata, args.drop_middle)
        if args.drop_middle_scope == "training"
        else np.ones(len(row_metadata), dtype=bool)
    )
    fit_selection_mask = selection_mask & training_middle_keep_mask
    fit_sample_weight = _sample_weight_for_rows(row_metadata, fit_selection_mask)
    if int(np.sum(selection_mask)) == 0:
        raise SystemExit(f"No rows found for selection datasets: {selection_datasets}")
    if int(np.sum(fit_selection_mask)) == 0:
        raise SystemExit(
            f"No rows left for fitting after --drop-middle={args.drop_middle} "
            f"with scope={args.drop_middle_scope}."
        )
    excluded_features = list(args.exclude_feature or [])
    excluded_prefixes = list(args.exclude_feature_prefix or [])
    if excluded_features or excluded_prefixes:
        x, feature_names = _drop_features(x, feature_names, excluded_features, excluded_prefixes)
    regression_target = _regression_target(row_metadata)
    model = _build_model(args.c, args.seed)
    cv_payload = _cross_validate(
        model,
        x[fit_selection_mask],
        y[fit_selection_mask],
        fit_sample_weight[fit_selection_mask],
        args.cv,
    )
    model.fit(
        x[fit_selection_mask],
        y[fit_selection_mask],
        logisticregression__sample_weight=fit_sample_weight[fit_selection_mask],
    )
    coefficients = _extract_coefficients(model, feature_names)
    stability = _stability_selection(
        x,
        y,
        sample_weight,
        row_metadata,
        feature_names,
        c=args.c,
        rounds=args.stability_rounds,
        seed=args.seed,
        selection_datasets=selection_datasets,
        eligible_mask=training_middle_keep_mask,
        sample_fraction=args.stability_sample_fraction,
    )
    ranking = _rank_features(coefficients, stability, groups)
    selected_features = [row["feature"] for row in ranking[: args.select_top]]
    selected_indices = np.asarray([feature_names.index(name) for name in selected_features], dtype=int)
    final_model = _build_final_model(
        args.final_model,
        c=args.c,
        ridge_alpha=args.ridge_alpha,
        elasticnet_alpha=args.elasticnet_alpha,
        elasticnet_l1_ratio=args.elasticnet_l1_ratio,
        seed=args.seed,
    )
    final_target = y if args.final_model == "logistic_l1" else regression_target
    _fit_final_model(
        final_model,
        x[fit_selection_mask][:, selected_indices],
        final_target[fit_selection_mask],
        fit_sample_weight[fit_selection_mask],
        args.final_model,
    )
    final_prediction = _predict_final_model(final_model, x[:, selected_indices], args.final_model)
    final_metrics = _report_metrics_by_dataset(row_metadata, final_prediction)
    final_selection_metrics = _report_metrics_by_dataset(
        _subset_rows(row_metadata, selection_mask),
        final_prediction[selection_mask],
    )
    final_external_metrics = _report_metrics_by_dataset(
        _subset_rows(row_metadata, external_mask),
        final_prediction[external_mask],
    )
    final_lodo_metrics = _leave_one_dataset_out_metrics(
        x[:, selected_indices],
        final_target,
        sample_weight,
        row_metadata,
        final_model_name=args.final_model,
        c=args.c,
        ridge_alpha=args.ridge_alpha,
        elasticnet_alpha=args.elasticnet_alpha,
        elasticnet_l1_ratio=args.elasticnet_l1_ratio,
        seed=args.seed,
    )
    final_sota_objective = _core_sota_objective(final_metrics)
    final_external_sota_objective = _core_sota_objective(final_external_metrics)

    prediction = model.predict(x)
    probability = model.predict_proba(x)[:, 1]
    train_payload = {
        "accuracy": float(accuracy_score(y, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "roc_auc": _safe_auc(y, probability),
    }
    out_dir = result_dir(args.output, "cognascore_feature_screen", "logistic_l1")
    out_dir.mkdir(parents=True, exist_ok=True)
    ranking_path = out_dir / "feature_ranking.csv"
    metadata_path = out_dir / "metadata.json"
    rows_path = out_dir / "training_rows.csv"
    metrics_path = out_dir / "final_metrics.csv"
    _write_ranking(ranking_path, ranking)
    _write_training_rows(rows_path, row_metadata)
    metadata = {
        "feature_source": args.feature_source,
        "embedding_model": args.embedding_model,
        "datasets": dataset_names,
        "continuous_threshold": args.continuous_threshold,
        "drop_middle": args.drop_middle,
        "drop_middle_scope": args.drop_middle_scope,
        "c": args.c,
        "cv": args.cv,
        "seed": args.seed,
        "stability_rounds": args.stability_rounds,
        "stability_sample_fraction": args.stability_sample_fraction,
        "selection_datasets": list(selection_datasets),
        "external_datasets": list(external_datasets),
        "row_count": int(x.shape[0]),
        "selection_row_count": int(np.sum(selection_mask)),
        "fit_selection_row_count": int(np.sum(fit_selection_mask)),
        "external_row_count": int(np.sum(external_mask)),
        "feature_count": int(x.shape[1]),
        "excluded_features": excluded_features,
        "excluded_feature_prefixes": excluded_prefixes,
        "positive_count": int(np.sum(y)),
        "negative_count": int(len(y) - np.sum(y)),
        "train_metrics": train_payload,
        "cv_metrics": cv_payload,
        "nonzero_feature_count": int(sum(1 for row in ranking if row["nonzero"])),
        "selected_feature_count": len(selected_features),
        "selected_features": selected_features,
        "final_model": args.final_model,
        "final_model_parameters": {
            "ridge_alpha": args.ridge_alpha,
            "elasticnet_alpha": args.elasticnet_alpha,
            "elasticnet_l1_ratio": args.elasticnet_l1_ratio,
            "c": args.c,
        },
        "final_all_report_metrics": final_metrics,
        "final_selection_train_report_metrics": final_selection_metrics,
        "final_external_report_metrics": final_external_metrics,
        "final_leave_one_dataset_out_report_metrics": final_lodo_metrics,
        "core_sota_objective": {
            "definition": (
                "Schnappinger must reach SOTA, and at least one of Scalabrino, "
                "JetBrains, or Dorn must also reach SOTA. MBJP is ignored."
            ),
            "thresholds": CORE_SOTA_THRESHOLDS,
            "all_rows_after_training_on_selection_datasets": final_sota_objective,
            "external_only_after_training_on_selection_datasets": final_external_sota_objective,
        },
        "top_features": ranking[: args.top],
    }
    _write_final_metrics(
        metrics_path,
        final_metrics,
        final_selection_metrics,
        final_external_metrics,
        final_lodo_metrics,
    )
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                **metadata,
                "ranking_csv": str(ranking_path),
                "rows_csv": str(rows_path),
                "metrics_csv": str(metrics_path),
            },
            indent=2,
        )
    )


def _build_model(c: float, seed: int):
    return make_pipeline(
        _median_imputer(),
        StandardScaler(),
        LogisticRegression(
            C=c,
            l1_ratio=1.0,
            solver="liblinear",
            class_weight="balanced",
            max_iter=5000,
            random_state=seed,
        ),
    )


def _build_final_model(
    name: str,
    *,
    c: float,
    ridge_alpha: float,
    elasticnet_alpha: float,
    elasticnet_l1_ratio: float,
    seed: int,
):
    if name == "logistic_l1":
        return _build_model(c, seed)
    if name == "elasticnet":
        return make_pipeline(
            _median_imputer(),
            StandardScaler(),
            ElasticNet(
                alpha=elasticnet_alpha,
                l1_ratio=elasticnet_l1_ratio,
                max_iter=10000,
                random_state=seed,
            ),
        )
    return Pipeline(
        [
            ("simpleimputer", _median_imputer()),
            ("trainingrangeclipper", TrainingRangeClipper()),
            ("standardscaler", StandardScaler()),
            ("ridge", BoundedRidge(alpha=ridge_alpha)),
        ]
    )


def _median_imputer() -> SimpleImputer:
    try:
        return SimpleImputer(strategy="median", keep_empty_features=True)
    except TypeError:
        return SimpleImputer(strategy="constant", fill_value=0.0)


def _fit_final_model(model, x: np.ndarray, y: np.ndarray, sample_weight: np.ndarray, name: str) -> None:
    if name == "logistic_l1":
        model.fit(x, y.astype(int), logisticregression__sample_weight=sample_weight)
    elif name == "elasticnet":
        model.fit(x, y, elasticnet__sample_weight=sample_weight)
    else:
        model.fit(x, y, ridge__sample_weight=sample_weight)


def _predict_final_model(model, x: np.ndarray, name: str) -> np.ndarray:
    if name == "logistic_l1":
        return model.predict_proba(x)[:, 1]
    return np.asarray(model.predict(x), dtype=float)


def _load_feature_family(root: Path, dataset_names: Sequence[str], slug: str, *, prefix: str) -> FeatureTable:
    rows: dict[tuple[str, str, int], dict[str, float]] = {}
    groups: dict[str, str] = {}
    columns: list[str] = []
    for dataset_name in dataset_names:
        table_dir = root / dataset_name / slug
        csv_path = table_dir / "features.csv"
        metadata_path = table_dir / "metadata.json"
        if not csv_path.exists():
            raise SystemExit(f"Missing feature table: {csv_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
        groups.update(_feature_groups_from_metadata(metadata, prefix=prefix))
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for column in reader.fieldnames or []:
                if column not in IDENTITY_COLUMNS:
                    feature_name = namespaced_feature(prefix, column)
                    columns.append(feature_name)
                    groups.setdefault(feature_name, _infer_feature_group(feature_name))
            occurrences: dict[tuple[str, str], int] = {}
            for row in reader:
                identity = (row["dataset"], row["task_id"])
                occurrence = occurrences.get(identity, 0)
                occurrences[identity] = occurrence + 1
                key = (row["dataset"], row["task_id"], occurrence)
                rows.setdefault(key, {})
                rows[key]["readability_score"] = _to_float(row.get("readability_score"))
                for column, value in row.items():
                    if column in IDENTITY_COLUMNS:
                        continue
                    rows[key][namespaced_feature(prefix, column)] = _to_float(value)
    return FeatureTable(rows=rows, groups=groups, columns=list(dict.fromkeys(columns)))


def _feature_groups_from_metadata(metadata: Mapping[str, Any], *, prefix: str) -> dict[str, str]:
    groups = {}
    for definition in metadata.get("feature_definitions", []):
        name = definition.get("name")
        group = definition.get("group")
        if name and group and name not in IDENTITY_COLUMNS:
            groups[namespaced_feature(prefix, name)] = str(group)
    return groups


def _infer_feature_group(feature_name: str) -> str:
    if "__" not in feature_name:
        return "unknown"
    family, raw_name = feature_name.split("__", 1)
    if "__" in raw_name:
        view, rest = raw_name.split("__", 1)
        algorithm = rest.split("_", 1)[0] if "_" in rest else rest
        return f"{family}_view_{view}_{algorithm}"
    if raw_name.startswith("embedding_"):
        return f"{family}_geometry"
    return f"{family}_other"


def _merge_tables(
    *tables: FeatureTable | None,
) -> tuple[dict[tuple[str, str, int], dict[str, float]], dict[str, str]]:
    active_tables = [table for table in tables if table is not None]
    if not active_tables:
        raise SystemExit("No feature tables selected.")
    keys = None
    for table in active_tables:
        table_keys = set(table.rows)
        keys = table_keys if keys is None else keys & table_keys
    assert keys is not None
    rows: dict[tuple[str, str, int], dict[str, float]] = {}
    groups: dict[str, str] = {}
    for table in active_tables:
        groups.update(table.groups)
    for key in sorted(keys):
        merged: dict[str, float] = {}
        for table in active_tables:
            merged.update(table.rows[key])
        rows[key] = merged
    return rows, groups


def _prepare_matrix(
    merged_rows: Mapping[tuple[str, str, int], Mapping[str, float]],
    groups: Mapping[str, str],
    *,
    continuous_threshold: str,
    drop_middle: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[dict[str, Any]]]:
    if not 0.0 <= drop_middle < 1.0:
        raise SystemExit("--drop-middle must be in [0, 1).")
    feature_names = sorted(groups)
    by_dataset: dict[str, list[tuple[str, int, Mapping[str, float]]]] = {}
    for (dataset, task_id, occurrence), row in merged_rows.items():
        if row.get("readability_score") is None or not math.isfinite(float(row["readability_score"])):
            continue
        by_dataset.setdefault(dataset, []).append((task_id, occurrence, row))

    x_rows: list[list[float]] = []
    y_rows: list[int] = []
    metadata_rows: list[dict[str, Any]] = []
    dataset_counts: dict[str, int] = {}
    for dataset, rows in sorted(by_dataset.items()):
        labels = np.asarray([float(row["readability_score"]) for _, _, row in rows], dtype=float)
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            targets = labels.astype(int)
            keep = np.ones(len(rows), dtype=bool)
            threshold_value = 0.5
        else:
            threshold_value = float(np.median(labels) if continuous_threshold == "median" else np.mean(labels))
            distances = np.abs(labels - threshold_value)
            keep = np.ones(len(rows), dtype=bool)
            if drop_middle > 0.0:
                cutoff = np.quantile(distances, drop_middle)
                keep = distances > cutoff
            targets = (labels >= threshold_value).astype(int)
        if len(set(targets[keep].tolist())) < 2:
            continue
        dataset_counts[dataset] = int(np.sum(keep))
        for keep_row, target, label, (task_id, occurrence, row) in zip(keep, targets, labels, rows):
            if not keep_row:
                continue
            x_rows.append([float(row.get(name, 0.0)) for name in feature_names])
            y_rows.append(int(target))
            metadata_rows.append(
                {
                    "dataset": dataset,
                    "task_id": task_id,
                    "feature_row_occurrence": occurrence,
                    "readability_score": float(label),
                    "binary_target": int(target),
                    "dataset_threshold": threshold_value,
                }
            )
    if not x_rows:
        raise SystemExit("No usable rows after label preparation.")
    sample_weight = np.asarray(
        [1.0 / max(dataset_counts[row["dataset"]], 1) for row in metadata_rows],
        dtype=float,
    )
    sample_weight *= len(sample_weight) / float(np.sum(sample_weight))
    return (
        np.asarray(x_rows, dtype=float),
        np.asarray(y_rows, dtype=int),
        sample_weight,
        feature_names,
        metadata_rows,
    )


def _drop_features(
    x: np.ndarray,
    feature_names: Sequence[str],
    excluded_features: Sequence[str],
    excluded_prefixes: Sequence[str],
) -> tuple[np.ndarray, list[str]]:
    excluded = set(excluded_features)
    prefixes = tuple(excluded_prefixes)
    keep = [
        index
        for index, name in enumerate(feature_names)
        if name not in excluded and not name.startswith(prefixes)
    ]
    return x[:, keep], [feature_names[index] for index in keep]


def _dataset_mask(
    row_metadata: Sequence[Mapping[str, Any]],
    datasets: Sequence[str],
) -> np.ndarray:
    dataset_set = set(datasets)
    return np.asarray([str(row["dataset"]) in dataset_set for row in row_metadata], dtype=bool)


def _middle_keep_mask(
    row_metadata: Sequence[Mapping[str, Any]],
    drop_middle: float,
) -> np.ndarray:
    if not 0.0 <= drop_middle < 1.0:
        raise SystemExit("--drop-middle must be in [0, 1).")
    keep = np.ones(len(row_metadata), dtype=bool)
    if drop_middle <= 0.0:
        return keep
    by_dataset: dict[str, list[int]] = {}
    for index, row in enumerate(row_metadata):
        by_dataset.setdefault(str(row["dataset"]), []).append(index)
    for indices in by_dataset.values():
        labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in indices], dtype=float)
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            continue
        thresholds = np.asarray([float(row_metadata[index]["dataset_threshold"]) for index in indices], dtype=float)
        distances = np.abs(labels - thresholds)
        cutoff = float(np.quantile(distances, drop_middle))
        for index, distance in zip(indices, distances):
            keep[index] = bool(distance > cutoff)
    return keep


def _sample_weight_for_rows(
    row_metadata: Sequence[Mapping[str, Any]],
    eligible_mask: np.ndarray | None = None,
) -> np.ndarray:
    if eligible_mask is None:
        eligible_mask = np.ones(len(row_metadata), dtype=bool)
    dataset_counts: dict[str, int] = {}
    for row, eligible in zip(row_metadata, eligible_mask):
        if bool(eligible):
            dataset = str(row["dataset"])
            dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
    weights = np.asarray(
        [
            (1.0 / dataset_counts[str(row["dataset"])]) if bool(eligible) and dataset_counts.get(str(row["dataset"]), 0) else 0.0
            for row, eligible in zip(row_metadata, eligible_mask)
        ],
        dtype=float,
    )
    total = float(np.sum(weights))
    if total > 0.0:
        weights *= int(np.sum(eligible_mask)) / total
    return weights


def _subset_rows(
    row_metadata: Sequence[Mapping[str, Any]],
    mask: np.ndarray,
) -> list[Mapping[str, Any]]:
    return [row for row, keep in zip(row_metadata, mask) if bool(keep)]


def _regression_target(row_metadata: Sequence[Mapping[str, Any]]) -> np.ndarray:
    target = np.zeros(len(row_metadata), dtype=float)
    by_dataset: dict[str, list[int]] = {}
    for index, row in enumerate(row_metadata):
        by_dataset.setdefault(str(row["dataset"]), []).append(index)
    for dataset, indices in by_dataset.items():
        labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in indices], dtype=float)
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            values = labels
        elif len(labels) == 1:
            values = np.asarray([0.5], dtype=float)
        else:
            values = (rankdata(labels, method="average") - 1.0) / max(len(labels) - 1.0, 1.0)
        target[indices] = values
    return target


def _report_metrics_by_dataset(
    row_metadata: Sequence[Mapping[str, Any]],
    prediction: np.ndarray,
) -> dict[str, dict[str, float | int | str | None]]:
    metrics: dict[str, dict[str, float | int | str | None]] = {}
    datasets = sorted({str(row["dataset"]) for row in row_metadata})
    for dataset in datasets:
        indices = [index for index, row in enumerate(row_metadata) if row["dataset"] == dataset]
        labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in indices], dtype=float)
        scores = prediction[indices]
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            metric_name = "mcc_best_threshold"
            metric_value, threshold = _best_mcc(scores, labels.astype(int))
        else:
            metric_name = "spearman"
            threshold = None
            metric_value = _safe_spearman(labels, scores)
        metrics[dataset] = {
            "n": len(indices),
            "metric": metric_name,
            "value": metric_value,
            "threshold": threshold,
        }
    return metrics


def _leave_one_dataset_out_metrics(
    x: np.ndarray,
    y: np.ndarray,
    sample_weight: np.ndarray,
    row_metadata: Sequence[Mapping[str, Any]],
    *,
    final_model_name: str,
    c: float,
    ridge_alpha: float,
    elasticnet_alpha: float,
    elasticnet_l1_ratio: float,
    seed: int,
) -> dict[str, dict[str, float | int | str | None]]:
    metrics: dict[str, dict[str, float | int | str | None]] = {}
    datasets = sorted({str(row["dataset"]) for row in row_metadata})
    for dataset in datasets:
        test = np.asarray([row["dataset"] == dataset for row in row_metadata], dtype=bool)
        train = ~test
        if np.sum(train) == 0 or np.sum(test) == 0:
            continue
        model = _build_final_model(
            final_model_name,
            c=c,
            ridge_alpha=ridge_alpha,
            elasticnet_alpha=elasticnet_alpha,
            elasticnet_l1_ratio=elasticnet_l1_ratio,
            seed=seed,
        )
        _fit_final_model(model, x[train], y[train], sample_weight[train], final_model_name)
        prediction = _predict_final_model(model, x[test], final_model_name)
        labels = np.asarray(
            [float(row["readability_score"]) for row, is_test in zip(row_metadata, test) if is_test],
            dtype=float,
        )
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            metric_name = "mcc_best_threshold"
            metric_value, threshold = _best_mcc(prediction, labels.astype(int))
        else:
            metric_name = "spearman"
            threshold = None
            metric_value = _safe_spearman(labels, prediction)
        metrics[dataset] = {
            "n": int(np.sum(test)),
            "metric": metric_name,
            "value": metric_value,
            "threshold": threshold,
        }
    return metrics


def _cross_validate(model, x: np.ndarray, y: np.ndarray, sample_weight: np.ndarray, cv: int) -> dict[str, float | None]:
    splits = min(cv, int(np.sum(y == 0)), int(np.sum(y == 1)))
    if splits < 2:
        return {"roc_auc": None, "balanced_accuracy": None}
    splitter = StratifiedKFold(n_splits=splits, shuffle=True, random_state=42)
    auc_scores = []
    balanced_accuracy_scores = []
    for train_index, test_index in splitter.split(x, y):
        fold_model = clone(model)
        fold_model.fit(
            x[train_index],
            y[train_index],
            logisticregression__sample_weight=sample_weight[train_index],
        )
        prediction = fold_model.predict(x[test_index])
        probability = fold_model.predict_proba(x[test_index])[:, 1]
        auc = _safe_auc(y[test_index], probability)
        if auc is not None:
            auc_scores.append(auc)
        balanced_accuracy_scores.append(float(balanced_accuracy_score(y[test_index], prediction)))
    return {
        "roc_auc": float(np.mean(auc_scores)) if auc_scores else None,
        "balanced_accuracy": float(np.mean(balanced_accuracy_scores)) if balanced_accuracy_scores else None,
    }


def _extract_coefficients(model, feature_names: Sequence[str]) -> dict[str, float]:
    logistic = model.named_steps["logisticregression"]
    coefficients = logistic.coef_[0]
    return {name: float(value) for name, value in zip(feature_names, coefficients)}


def _stability_selection(
    x: np.ndarray,
    y: np.ndarray,
    sample_weight: np.ndarray,
    row_metadata: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    *,
    c: float,
    rounds: int,
    seed: int,
    selection_datasets: Sequence[str],
    eligible_mask: np.ndarray | None,
    sample_fraction: float,
) -> dict[str, dict[str, float]]:
    if not 0.0 < sample_fraction <= 1.0:
        raise SystemExit("--stability-sample-fraction must be in (0, 1].")
    rng = np.random.default_rng(seed)
    nonzero_count = np.zeros(len(feature_names), dtype=int)
    abs_coef_sum = np.zeros(len(feature_names), dtype=float)
    signed_coef_sum = np.zeros(len(feature_names), dtype=float)
    by_dataset: dict[str, np.ndarray] = {}
    selection_set = set(selection_datasets)
    if eligible_mask is None:
        eligible_mask = np.ones(len(row_metadata), dtype=bool)
    for dataset in selection_datasets:
        indices = np.asarray(
            [
                index
                for index, row in enumerate(row_metadata)
                if str(row["dataset"]) == dataset and bool(eligible_mask[index])
            ],
            dtype=int,
        )
        if len(indices) > 0:
            by_dataset[dataset] = indices
    if not by_dataset:
        raise SystemExit(f"No rows found for selection datasets: {sorted(selection_set)}")
    completed_rounds = 0
    for _ in range(rounds):
        sampled: list[np.ndarray] = []
        for indices in by_dataset.values():
            sample_size = max(1, int(round(len(indices) * sample_fraction)))
            sampled.append(rng.choice(indices, size=sample_size, replace=False))
        indices = np.concatenate(sampled)
        if len(set(y[indices].tolist())) < 2:
            continue
        model = _build_model(c, int(rng.integers(0, 2**31 - 1)))
        model.fit(x[indices], y[indices], logisticregression__sample_weight=sample_weight[indices])
        coef = model.named_steps["logisticregression"].coef_[0]
        nonzero = np.abs(coef) > 1e-12
        nonzero_count += nonzero.astype(int)
        abs_coef_sum += np.abs(coef)
        signed_coef_sum += coef
        completed_rounds += 1
    denominator = max(completed_rounds, 1)
    return {
        name: {
            "selection_frequency": float(nonzero_count[index] / denominator),
            "mean_abs_coefficient": float(abs_coef_sum[index] / denominator),
            "mean_signed_coefficient": float(signed_coef_sum[index] / denominator),
        }
        for index, name in enumerate(feature_names)
    }


def _rank_features(
    coefficients: Mapping[str, float],
    stability: Mapping[str, Mapping[str, float]],
    groups: Mapping[str, str],
) -> list[dict[str, Any]]:
    rows = []
    for name, coefficient in coefficients.items():
        stable = stability.get(name, {})
        rows.append(
            {
                "feature": name,
                "group": groups.get(name, "unknown"),
                "coefficient": float(coefficient),
                "abs_coefficient": abs(float(coefficient)),
                "nonzero": abs(float(coefficient)) > 1e-12,
                "selection_frequency": float(stable.get("selection_frequency", 0.0)),
                "mean_abs_coefficient": float(stable.get("mean_abs_coefficient", 0.0)),
                "mean_signed_coefficient": float(stable.get("mean_signed_coefficient", 0.0)),
            }
        )
    rows.sort(
        key=lambda row: (
            row["selection_frequency"],
            row["abs_coefficient"],
            row["mean_abs_coefficient"],
        ),
        reverse=True,
    )
    return rows


def _write_ranking(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    columns = (
        "rank",
        "feature",
        "group",
        "coefficient",
        "abs_coefficient",
        "nonzero",
        "selection_frequency",
        "mean_abs_coefficient",
        "mean_signed_coefficient",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({"rank": rank, **row})


def _write_training_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    columns = ("dataset", "task_id", "feature_row_occurrence", "readability_score", "binary_target", "dataset_threshold")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_final_metrics(
    path: Path,
    all_metrics: Mapping[str, Mapping[str, Any]],
    selection_metrics: Mapping[str, Mapping[str, Any]],
    external_metrics: Mapping[str, Mapping[str, Any]],
    lodo_metrics: Mapping[str, Mapping[str, Any]],
) -> None:
    columns = ("evaluation", "dataset", "n", "metric", "value", "threshold")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for evaluation, metrics in (
            ("all_rows_after_selection_train_fit", all_metrics),
            ("selection_train_fit", selection_metrics),
            ("external_after_selection_train_fit", external_metrics),
            ("leave_one_dataset_out_diagnostic", lodo_metrics),
        ):
            for dataset, row in sorted(metrics.items()):
                writer.writerow({"evaluation": evaluation, "dataset": dataset, **row})


def _core_sota_objective(
    metrics: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    values = {
        dataset: metrics.get(dataset, {}).get("value")
        for dataset in CORE_SOTA_THRESHOLDS
        if dataset in metrics
    }
    hits = {
        dataset: (
            value is not None
            and math.isfinite(float(value))
            and float(value) >= CORE_SOTA_THRESHOLDS[dataset]
        )
        for dataset, value in values.items()
    }
    secondary = ("scalabrino", "jetbrains", "dorn")
    return {
        "values": values,
        "hits": hits,
        "schnappinger_hit": bool(hits.get("schnappinger", False)),
        "secondary_hits": [dataset for dataset in secondary if hits.get(dataset, False)],
        "objective_met": bool(hits.get("schnappinger", False))
        and any(hits.get(dataset, False) for dataset in secondary),
    }


def _safe_auc(y: np.ndarray, probability: np.ndarray) -> float | None:
    if len(set(y.tolist())) < 2:
        return None
    return float(roc_auc_score(y, probability))


def _safe_spearman(labels: np.ndarray, scores: np.ndarray) -> float | None:
    if len(labels) < 2 or len(set(labels.tolist())) < 2 or len(set(scores.tolist())) < 2:
        return None
    value = float(spearmanr(labels, scores).statistic)
    return value if math.isfinite(value) else None


def _best_mcc(scores: np.ndarray, labels: np.ndarray) -> tuple[float | None, float | None]:
    if len(labels) == 0 or len(set(labels.tolist())) < 2:
        return None, None
    candidates = sorted(set(float(score) for score in scores))
    if not candidates:
        return None, None
    thresholds = [candidates[0] - 1e-12]
    thresholds.extend((left + right) / 2.0 for left, right in zip(candidates, candidates[1:]))
    thresholds.append(candidates[-1] + 1e-12)
    best_value: float | None = None
    best_threshold: float | None = None
    for threshold in thresholds:
        predicted = (scores >= threshold).astype(int)
        value = float(matthews_corrcoef(labels, predicted))
        if best_value is None or value > best_value:
            best_value = value
            best_threshold = float(threshold)
    return best_value, best_threshold


def _to_float(value: Any) -> float:
    if value is None or value == "":
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    main()
