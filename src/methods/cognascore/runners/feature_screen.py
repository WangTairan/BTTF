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
from sklearn.preprocessing import StandardScaler

from src.experiments.paths import output_dir
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS

from ..results import model_slug
from .common import dataset_output_name


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")
IDENTITY_COLUMNS = {"dataset", "task_id", "readability_score"}
CORE_SOTA_THRESHOLDS = {
    "scalabrino": 0.5919,
    "jetbrains": 0.3594,
    "dorn": 0.5857,
    "schnappinger": 0.6057,
}


@dataclass(frozen=True)
class FeatureTable:
    rows: dict[tuple[str, str], dict[str, float]]
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
    parser.add_argument("--base-root", type=Path, default=Path("output/cognascore_features"))
    parser.add_argument("--embedding-root", type=Path, default=Path("output/cognascore_embedding_features"))
    parser.add_argument(
        "--feature-source",
        choices=("base", "embedding", "combined"),
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
    parser.add_argument("--c", type=float, default=0.05, help="Inverse L1 regularization strength.")
    parser.add_argument("--cv", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability-rounds", type=int, default=200)
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
        default=["base__generalized_score"],
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
        help="Output root. Defaults to output/cognascore_feature_screen/logistic_l1/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    dataset_names = [dataset_output_name(path) for path in dataset_paths]
    slug = model_slug(args.embedding_model)

    base_table = (
        _load_feature_family(args.base_root, dataset_names, slug, prefix="base")
        if args.feature_source in {"base", "combined"}
        else None
    )
    embedding_table = (
        _load_feature_family(args.embedding_root, dataset_names, slug, prefix="embedding")
        if args.feature_source in {"embedding", "combined"}
        else None
    )
    merged_rows, groups = _merge_tables(base_table, embedding_table)
    prepared = _prepare_matrix(
        merged_rows,
        groups,
        continuous_threshold=args.continuous_threshold,
        drop_middle=args.drop_middle,
    )
    x, y, sample_weight, feature_names, row_metadata = prepared
    excluded_features = list(args.exclude_feature or [])
    excluded_prefixes = list(args.exclude_feature_prefix or [])
    if excluded_features or excluded_prefixes:
        x, feature_names = _drop_features(x, feature_names, excluded_features, excluded_prefixes)
    regression_target = _regression_target(row_metadata)
    model = _build_model(args.c, args.seed)
    cv_payload = _cross_validate(model, x, y, sample_weight, args.cv)
    model.fit(x, y, logisticregression__sample_weight=sample_weight)
    coefficients = _extract_coefficients(model, feature_names)
    stability = _stability_selection(
        x,
        y,
        sample_weight,
        feature_names,
        c=args.c,
        rounds=args.stability_rounds,
        seed=args.seed,
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
    _fit_final_model(final_model, x[:, selected_indices], final_target, sample_weight, args.final_model)
    final_prediction = _predict_final_model(final_model, x[:, selected_indices], args.final_model)
    final_metrics = _report_metrics_by_dataset(row_metadata, final_prediction)
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
    final_lodo_sota_objective = _core_sota_objective(final_lodo_metrics)

    prediction = model.predict(x)
    probability = model.predict_proba(x)[:, 1]
    train_payload = {
        "accuracy": float(accuracy_score(y, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "roc_auc": _safe_auc(y, probability),
    }
    out_dir = output_dir(args.output, "cognascore_feature_screen", "logistic_l1")
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
        "c": args.c,
        "cv": args.cv,
        "seed": args.seed,
        "stability_rounds": args.stability_rounds,
        "row_count": int(x.shape[0]),
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
        "final_train_report_metrics": final_metrics,
        "final_leave_one_dataset_out_report_metrics": final_lodo_metrics,
        "core_sota_objective": {
            "definition": (
                "Schnappinger must reach SOTA, and at least one of Scalabrino, "
                "JetBrains, or Dorn must also reach SOTA. MBJP is ignored."
            ),
            "thresholds": CORE_SOTA_THRESHOLDS,
            "train_all": final_sota_objective,
            "leave_one_dataset_out": final_lodo_sota_objective,
        },
        "top_features": ranking[: args.top],
    }
    _write_final_metrics(metrics_path, final_metrics, final_lodo_metrics)
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
        SimpleImputer(strategy="median"),
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
            SimpleImputer(strategy="median"),
            StandardScaler(),
            ElasticNet(
                alpha=elasticnet_alpha,
                l1_ratio=elasticnet_l1_ratio,
                max_iter=10000,
                random_state=seed,
            ),
        )
    return make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=ridge_alpha),
    )


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
    rows: dict[tuple[str, str], dict[str, float]] = {}
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
                    feature_name = _prefixed_name(prefix, column)
                    columns.append(feature_name)
                    groups.setdefault(feature_name, _infer_feature_group(feature_name))
            for row in reader:
                key = (row["dataset"], row["task_id"])
                rows.setdefault(key, {})
                rows[key]["readability_score"] = _to_float(row.get("readability_score"))
                for column, value in row.items():
                    if column in IDENTITY_COLUMNS:
                        continue
                    rows[key][_prefixed_name(prefix, column)] = _to_float(value)
    return FeatureTable(rows=rows, groups=groups, columns=list(dict.fromkeys(columns)))


def _feature_groups_from_metadata(metadata: Mapping[str, Any], *, prefix: str) -> dict[str, str]:
    groups = {}
    for definition in metadata.get("feature_definitions", []):
        name = definition.get("name")
        group = definition.get("group")
        if name and group and name not in IDENTITY_COLUMNS:
            groups[_prefixed_name(prefix, name)] = str(group)
    return groups


def _infer_feature_group(feature_name: str) -> str:
    if "__" not in feature_name:
        return "unknown"
    family, raw_name = feature_name.split("__", 1)
    if "__" in raw_name:
        view, rest = raw_name.split("__", 1)
        algorithm = rest.split("_", 1)[0] if "_" in rest else rest
        return f"{family}_view_{view}_{algorithm}"
    if raw_name.startswith("kmeans_k_"):
        return f"{family}_fixed_kmeans"
    if raw_name.startswith("auto_dbscan_"):
        return f"{family}_auto_dbscan"
    if raw_name.startswith("embedding_"):
        return f"{family}_geometry"
    return f"{family}_other"


def _merge_tables(
    base_table: FeatureTable | None,
    embedding_table: FeatureTable | None,
) -> tuple[dict[tuple[str, str], dict[str, float]], dict[str, str]]:
    if base_table is None and embedding_table is None:
        raise SystemExit("No feature tables selected.")
    keys = None
    for table in (base_table, embedding_table):
        if table is None:
            continue
        table_keys = set(table.rows)
        keys = table_keys if keys is None else keys & table_keys
    assert keys is not None
    rows: dict[tuple[str, str], dict[str, float]] = {}
    groups: dict[str, str] = {}
    for table in (base_table, embedding_table):
        if table is None:
            continue
        groups.update(table.groups)
    for key in sorted(keys):
        merged: dict[str, float] = {}
        for table in (base_table, embedding_table):
            if table is None:
                continue
            merged.update(table.rows[key])
        rows[key] = merged
    return rows, groups


def _prepare_matrix(
    merged_rows: Mapping[tuple[str, str], Mapping[str, float]],
    groups: Mapping[str, str],
    *,
    continuous_threshold: str,
    drop_middle: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[dict[str, Any]]]:
    if not 0.0 <= drop_middle < 1.0:
        raise SystemExit("--drop-middle must be in [0, 1).")
    feature_names = sorted(groups)
    by_dataset: dict[str, list[tuple[str, Mapping[str, float]]]] = {}
    for (dataset, task_id), row in merged_rows.items():
        if row.get("readability_score") is None or not math.isfinite(float(row["readability_score"])):
            continue
        by_dataset.setdefault(dataset, []).append((task_id, row))

    x_rows: list[list[float]] = []
    y_rows: list[int] = []
    metadata_rows: list[dict[str, Any]] = []
    dataset_counts: dict[str, int] = {}
    for dataset, rows in sorted(by_dataset.items()):
        labels = np.asarray([float(row["readability_score"]) for _, row in rows], dtype=float)
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
        for keep_row, target, label, (task_id, row) in zip(keep, targets, labels, rows):
            if not keep_row:
                continue
            x_rows.append([float(row.get(name, 0.0)) for name in feature_names])
            y_rows.append(int(target))
            metadata_rows.append(
                {
                    "dataset": dataset,
                    "task_id": task_id,
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
    feature_names: Sequence[str],
    *,
    c: float,
    rounds: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    nonzero_count = np.zeros(len(feature_names), dtype=int)
    abs_coef_sum = np.zeros(len(feature_names), dtype=float)
    signed_coef_sum = np.zeros(len(feature_names), dtype=float)
    for _ in range(rounds):
        indices = rng.choice(np.arange(len(y)), size=len(y), replace=True)
        if len(set(y[indices].tolist())) < 2:
            continue
        model = _build_model(c, int(rng.integers(0, 2**31 - 1)))
        model.fit(x[indices], y[indices], logisticregression__sample_weight=sample_weight[indices])
        coef = model.named_steps["logisticregression"].coef_[0]
        nonzero = np.abs(coef) > 1e-12
        nonzero_count += nonzero.astype(int)
        abs_coef_sum += np.abs(coef)
        signed_coef_sum += coef
    denominator = max(rounds, 1)
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
    columns = ("dataset", "task_id", "readability_score", "binary_target", "dataset_threshold")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_final_metrics(
    path: Path,
    train_metrics: Mapping[str, Mapping[str, Any]],
    lodo_metrics: Mapping[str, Mapping[str, Any]],
) -> None:
    columns = ("evaluation", "dataset", "n", "metric", "value", "threshold")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for evaluation, metrics in (("train_all", train_metrics), ("leave_one_dataset_out", lodo_metrics)):
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


def _prefixed_name(prefix: str, column: str) -> str:
    return f"{prefix}__{column}"


def _to_float(value: Any) -> float:
    if value is None or value == "":
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


if __name__ == "__main__":
    main()
