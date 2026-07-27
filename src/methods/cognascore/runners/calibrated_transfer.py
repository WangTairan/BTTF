from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import matthews_corrcoef
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.experiments.paths import output_dir
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS

from ..results import model_slug
from .common import dataset_output_name
from .feature_screen import _load_feature_family, _merge_tables


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")
DEFAULT_EXCLUDE_FEATURES = ("base__generalized_score",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train a small calibrated CognaScore transfer model from stable feature tables. "
            "Default mode uses only a stratified Scalabrino calibration subset for feature "
            "selection and fitting, then reports all datasets as transfer evaluations."
        )
    )
    parser.add_argument("datasets", nargs="*", type=Path, help="Dataset paths. Defaults to all code datasets.")
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--base-root", type=Path, default=Path("output/cognascore_features"))
    parser.add_argument("--embedding-root", type=Path, default=Path("output/cognascore_embedding_features"))
    parser.add_argument("--feature-source", choices=("base", "embedding", "combined"), default="combined")
    parser.add_argument("--train-dataset", default="scalabrino")
    parser.add_argument("--train-size", type=int, default=60)
    parser.add_argument("--seed", type=int, default=78)
    parser.add_argument("--alpha", type=float, default=100.0)
    parser.add_argument("--features", type=int, default=20)
    parser.add_argument("--cv", type=int, default=5)
    parser.add_argument("--label-bins", type=int, default=10)
    parser.add_argument("--length-bins", type=int, default=1)
    parser.add_argument(
        "--length-feature",
        default="base__loc",
        help="Feature used for optional length-stratified sampling, e.g. base__loc or base__token_count.",
    )
    parser.add_argument(
        "--selection",
        choices=("train_cv_greedy", "transfer_greedy", "provided"),
        default="train_cv_greedy",
        help=(
            "Feature selection policy. train_cv_greedy uses calibration data only; "
            "transfer_greedy optimizes named evaluation datasets and is an exploratory upper-bound mode."
        ),
    )
    parser.add_argument(
        "--selection-dataset",
        action="append",
        default=[],
        help="Dataset to optimize in --selection transfer_greedy. Can be repeated. Defaults to schnappinger.",
    )
    parser.add_argument("--selected-features", type=Path, help="JSON list of features for --selection provided.")
    parser.add_argument("--exclude-feature", action="append", default=list(DEFAULT_EXCLUDE_FEATURES))
    parser.add_argument("-o", "--output", type=Path, help="Output root. Defaults to output/cognascore_calibrated_transfer/.")
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
    row_metadata, matrix, feature_names = _matrix_from_rows(merged_rows, groups, args.exclude_feature)
    labels = np.asarray([row["readability_score"] for row in row_metadata], dtype=float)
    train_indices = _sample_training_indices(
        row_metadata,
        matrix,
        feature_names,
        train_dataset=args.train_dataset,
        train_size=args.train_size,
        seed=args.seed,
        label_bins=args.label_bins,
        length_bins=args.length_bins,
        length_feature=args.length_feature,
    )
    target = _rank_target(labels)

    if args.selection == "provided":
        if args.selected_features is None:
            raise SystemExit("--selected-features is required for --selection provided.")
        selected_features = json.loads(args.selected_features.read_text(encoding="utf-8"))
        if not isinstance(selected_features, list) or not all(isinstance(name, str) for name in selected_features):
            raise SystemExit("--selected-features must be a JSON list of feature names.")
        missing = [name for name in selected_features if name not in feature_names]
        if missing:
            raise SystemExit(f"Selected features missing from table: {missing[:10]}")
    else:
        if args.selection == "transfer_greedy":
            selected_features = _greedy_transfer_features(
                matrix,
                target,
                train_indices,
                row_metadata,
                feature_names,
                count=args.features,
                alpha=args.alpha,
                selection_datasets=args.selection_dataset or ["schnappinger"],
            )
        else:
            selected_features = _greedy_train_cv_features(
                matrix,
                target,
                train_indices,
                feature_names,
                count=args.features,
                alpha=args.alpha,
                cv=args.cv,
                seed=args.seed,
            )
    selected_indices = np.asarray([feature_names.index(name) for name in selected_features], dtype=int)

    model = _ridge(args.alpha)
    model.fit(matrix[train_indices][:, selected_indices], target[train_indices])
    predictions = model.predict(matrix[:, selected_indices])
    metrics = _metrics_by_dataset(row_metadata, predictions, train_indices)

    out_dir = output_dir(
        args.output,
        "cognascore_calibrated_transfer",
        f"{args.train_dataset}_{args.train_size}_seed_{args.seed}",
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "embedding_model": args.embedding_model,
        "feature_source": args.feature_source,
        "datasets": dataset_names,
        "train_dataset": args.train_dataset,
        "train_size": len(train_indices),
        "seed": args.seed,
        "alpha": args.alpha,
        "selection": args.selection,
        "selection_datasets": args.selection_dataset or (["schnappinger"] if args.selection == "transfer_greedy" else []),
        "requested_feature_count": args.features,
        "selected_feature_count": len(selected_features),
        "selected_features": selected_features,
        "label_bins": args.label_bins,
        "length_bins": args.length_bins,
        "length_feature": args.length_feature,
        "excluded_features": args.exclude_feature,
        "metrics": metrics,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_predictions(out_dir / "predictions.csv", row_metadata, predictions, train_indices)
    print(json.dumps({**metadata, "output_dir": str(out_dir)}, indent=2))


def _matrix_from_rows(
    merged_rows: Mapping[tuple[str, str], Mapping[str, float]],
    groups: Mapping[str, str],
    excluded_features: Sequence[str],
) -> tuple[list[dict[str, Any]], np.ndarray, list[str]]:
    excluded = set(excluded_features)
    feature_names = sorted(name for name in groups if name not in excluded)
    metadata: list[dict[str, Any]] = []
    rows: list[list[float]] = []
    for (dataset, task_id), row in sorted(merged_rows.items()):
        label = row.get("readability_score")
        if label is None or not math.isfinite(float(label)):
            continue
        metadata.append({"dataset": dataset, "task_id": task_id, "readability_score": float(label)})
        rows.append([float(row.get(name, float("nan"))) for name in feature_names])
    x = np.asarray(rows, dtype=float)
    x = SimpleImputer(strategy="median").fit_transform(x)
    return metadata, x, feature_names


def _sample_training_indices(
    row_metadata: Sequence[Mapping[str, Any]],
    x: np.ndarray,
    feature_names: Sequence[str],
    *,
    train_dataset: str,
    train_size: int,
    seed: int,
    label_bins: int,
    length_bins: int,
    length_feature: str,
) -> np.ndarray:
    candidates = np.asarray(
        [index for index, row in enumerate(row_metadata) if row["dataset"] == train_dataset],
        dtype=int,
    )
    if candidates.size == 0:
        raise SystemExit(f"No rows for train dataset: {train_dataset}")
    if train_size >= candidates.size:
        return candidates
    labels = np.asarray([row_metadata[index]["readability_score"] for index in candidates], dtype=float)
    length_values = (
        x[candidates, feature_names.index(length_feature)]
        if length_feature in feature_names
        else np.zeros(candidates.size, dtype=float)
    )
    strata = _strata(labels, length_values, label_bins=label_bins, length_bins=length_bins)
    rng = np.random.default_rng(seed)
    selected: list[int] = []
    unique_strata = sorted(set(strata.tolist()))
    base_quota = train_size // max(len(unique_strata), 1)
    remainder = train_size % max(len(unique_strata), 1)
    for offset, stratum in enumerate(unique_strata):
        members = candidates[strata == stratum]
        quota = base_quota + int(offset < remainder)
        if quota <= 0:
            continue
        take = min(quota, len(members))
        selected.extend(rng.choice(members, size=take, replace=False).tolist())
    if len(selected) < train_size:
        remaining = np.asarray([index for index in candidates if index not in set(selected)], dtype=int)
        extra = rng.choice(remaining, size=train_size - len(selected), replace=False)
        selected.extend(extra.tolist())
    return np.asarray(sorted(selected), dtype=int)


def _strata(labels: np.ndarray, lengths: np.ndarray, *, label_bins: int, length_bins: int) -> np.ndarray:
    label_ids = _quantile_bins(labels, label_bins)
    if length_bins <= 1:
        return label_ids
    length_ids = _quantile_bins(lengths, length_bins)
    return label_ids * length_bins + length_ids


def _quantile_bins(values: np.ndarray, bins: int) -> np.ndarray:
    if bins <= 1 or len(set(values.tolist())) <= 1:
        return np.zeros(values.size, dtype=int)
    ranks = rankdata(values, method="ordinal") - 1
    return np.minimum((ranks * bins // len(values)).astype(int), bins - 1)


def _rank_target(labels: np.ndarray) -> np.ndarray:
    if len(labels) <= 1:
        return np.zeros(labels.size, dtype=float)
    return (rankdata(labels, method="average") - 1.0) / max(len(labels) - 1.0, 1.0)


def _greedy_train_cv_features(
    x: np.ndarray,
    y: np.ndarray,
    train_indices: np.ndarray,
    feature_names: Sequence[str],
    *,
    count: int,
    alpha: float,
    cv: int,
    seed: int,
) -> list[str]:
    selected: list[int] = []
    remaining = set(range(len(feature_names)))
    for _ in range(min(count, len(feature_names))):
        best: tuple[float, int] | None = None
        for candidate in sorted(remaining):
            columns = selected + [candidate]
            score = _cv_spearman(x[train_indices][:, columns], y[train_indices], alpha=alpha, cv=cv, seed=seed)
            if best is None or score > best[0]:
                best = (score, candidate)
        if best is None:
            break
        selected.append(best[1])
        remaining.remove(best[1])
    return [feature_names[index] for index in selected]


def _greedy_transfer_features(
    x: np.ndarray,
    y: np.ndarray,
    train_indices: np.ndarray,
    row_metadata: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    *,
    count: int,
    alpha: float,
    selection_datasets: Sequence[str],
) -> list[str]:
    selected: list[int] = []
    remaining = set(range(len(feature_names)))
    selection_set = set(selection_datasets)
    for _ in range(min(count, len(feature_names))):
        best: tuple[float, int] | None = None
        for candidate in sorted(remaining):
            columns = selected + [candidate]
            model = _ridge(alpha)
            model.fit(x[train_indices][:, columns], y[train_indices])
            predictions = model.predict(x[:, columns])
            score = _transfer_objective(row_metadata, predictions, selection_set, train_indices)
            if best is None or score > best[0]:
                best = (score, candidate)
        if best is None:
            break
        selected.append(best[1])
        remaining.remove(best[1])
    return [feature_names[index] for index in selected]


def _transfer_objective(
    row_metadata: Sequence[Mapping[str, Any]],
    predictions: np.ndarray,
    selection_datasets: set[str],
    train_indices: np.ndarray,
) -> float:
    train_set = set(train_indices.tolist())
    values: list[float] = []
    for dataset in sorted(selection_datasets):
        indices = [
            index
            for index, row in enumerate(row_metadata)
            if row["dataset"] == dataset and index not in train_set
        ]
        if len(indices) < 2:
            continue
        labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in indices], dtype=float)
        scores = predictions[indices]
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            value, _ = _best_mcc(scores, labels.astype(int))
        else:
            value = _spearman(labels, scores)
        if value is not None and math.isfinite(float(value)):
            values.append(float(value))
    return float(np.mean(values)) if values else -1.0


def _cv_spearman(x: np.ndarray, y: np.ndarray, *, alpha: float, cv: int, seed: int) -> float:
    splits = min(cv, len(y))
    if splits < 2:
        return 0.0
    predictions = np.zeros(len(y), dtype=float)
    splitter = KFold(n_splits=splits, shuffle=True, random_state=seed)
    for train, test in splitter.split(x):
        model = _ridge(alpha)
        model.fit(x[train], y[train])
        predictions[test] = model.predict(x[test])
    value = spearmanr(y, predictions).statistic
    return float(value) if math.isfinite(float(value)) else 0.0


def _ridge(alpha: float):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def _metrics_by_dataset(
    row_metadata: Sequence[Mapping[str, Any]],
    predictions: np.ndarray,
    train_indices: np.ndarray,
) -> dict[str, dict[str, Any]]:
    train_set = set(train_indices.tolist())
    metrics: dict[str, dict[str, Any]] = {}
    for dataset in sorted({str(row["dataset"]) for row in row_metadata}):
        indices = np.asarray([i for i, row in enumerate(row_metadata) if row["dataset"] == dataset], dtype=int)
        labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in indices], dtype=float)
        scores = predictions[indices]
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            value, threshold = _best_mcc(scores, labels.astype(int))
            metric = "mcc_best_threshold"
        else:
            value = _spearman(labels, scores)
            threshold = None
            metric = "spearman"
        split = "train_dataset" if dataset == row_metadata[train_indices[0]]["dataset"] else "external_transfer"
        heldout_indices = [index for index in indices.tolist() if index not in train_set]
        heldout_value = None
        if heldout_indices and len(heldout_indices) != len(indices):
            held_labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in heldout_indices])
            held_scores = predictions[heldout_indices]
            heldout_value = _spearman(held_labels, held_scores)
        metrics[dataset] = {
            "n": int(len(indices)),
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "split": split,
            "train_count": int(sum(index in train_set for index in indices.tolist())),
            "heldout_value": heldout_value,
        }
    return metrics


def _spearman(labels: np.ndarray, scores: np.ndarray) -> float | None:
    if len(labels) < 2 or len(set(labels.tolist())) < 2 or len(set(scores.tolist())) < 2:
        return None
    value = float(spearmanr(labels, scores).statistic)
    return value if math.isfinite(value) else None


def _best_mcc(scores: np.ndarray, labels: np.ndarray) -> tuple[float | None, float | None]:
    if len(labels) == 0 or len(set(labels.tolist())) < 2:
        return None, None
    candidates = sorted(set(float(score) for score in scores))
    thresholds = [candidates[0] - 1e-12]
    thresholds.extend((left + right) / 2.0 for left, right in zip(candidates, candidates[1:]))
    thresholds.append(candidates[-1] + 1e-12)
    best_value: float | None = None
    best_threshold: float | None = None
    for threshold in thresholds:
        value = float(matthews_corrcoef(labels, (scores >= threshold).astype(int)))
        if best_value is None or value > best_value:
            best_value = value
            best_threshold = float(threshold)
    return best_value, best_threshold


def _write_predictions(path: Path, rows: Sequence[Mapping[str, Any]], predictions: np.ndarray, train_indices: np.ndarray) -> None:
    train_set = set(train_indices.tolist())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("dataset", "task_id", "readability_score", "prediction", "is_train"))
        writer.writeheader()
        for index, (row, prediction) in enumerate(zip(rows, predictions)):
            writer.writerow(
                {
                    "dataset": row["dataset"],
                    "task_id": row["task_id"],
                    "readability_score": row["readability_score"],
                    "prediction": float(prediction),
                    "is_train": int(index in train_set),
                }
            )


if __name__ == "__main__":
    main()
