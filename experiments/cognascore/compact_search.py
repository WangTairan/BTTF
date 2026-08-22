from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.methods.cognascore.results import model_slug
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)

from .feature_selection import (
    CORE_SOTA_THRESHOLDS,
    DEFAULT_DATASET_KEYS,
    _core_sota_objective,
    _report_metrics_by_dataset,
    _sample_weight_for_rows,
)


EMBEDDING_MODELS = {
    "nomic": "nomic-ai/nomic-embed-text-v1.5",
    "qwen": "Qwen/Qwen3-Embedding-0.6B",
    "jina": "jinaai/jina-embeddings-v2-base-code",
}
IDENTITY_COLUMNS = {"dataset", "task_id", "readability_score"}
DEFAULT_TRAIN_DATASETS = ("scalabrino", "schnappinger", "dorn", "buse")
DEFAULT_REPORT_DATASETS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")


@dataclass(frozen=True)
class Candidate:
    name: str
    raw_name: str
    transform: str
    values: np.ndarray
    univariate_score: float


@dataclass(frozen=True)
class BeamItem:
    features: tuple[int, ...]
    score: float
    train_metrics: dict[str, dict[str, Any]]


def main() -> None:
    args = parse_args()
    train_datasets = tuple(args.train_dataset or DEFAULT_TRAIN_DATASETS)
    report_datasets = tuple(args.report_dataset or DEFAULT_REPORT_DATASETS)
    embedding_models = [EMBEDDING_MODELS.get(name, name) for name in args.embedding_model]
    frame = load_feature_frame(
        report_datasets,
        base_root=args.base_root,
        embedding_root=args.embedding_root,
        base_model=args.base_model,
        embedding_models=embedding_models,
    )
    row_metadata = row_metadata_from_frame(frame)
    target = rank_percentile_target(row_metadata)
    sample_weight = _sample_weight_for_rows(row_metadata)
    train_mask = np.asarray([row["dataset"] in train_datasets for row in row_metadata], dtype=bool)
    if int(np.sum(train_mask)) == 0:
        raise SystemExit(f"No training rows for datasets: {train_datasets}")

    candidates = build_candidates(
        frame,
        target,
        train_mask,
        min_nonzero_fraction=args.min_nonzero_fraction,
        min_unique=args.min_unique,
        max_missing_fraction=args.max_missing_fraction,
        exclude_substrings=args.exclude_substring,
    )
    if args.candidate_limit and len(candidates) > args.candidate_limit:
        candidates = candidates[: args.candidate_limit]
    if not candidates:
        raise SystemExit("No usable compact-search candidates after filtering.")

    x_all = np.column_stack([candidate.values for candidate in candidates])
    beam_history, best = beam_search(
        x_all,
        candidates,
        target,
        sample_weight,
        row_metadata,
        train_mask,
        max_features=args.max_features,
        beam_size=args.beam_size,
        ridge_alpha=args.ridge_alpha,
        feature_count_penalty=args.feature_count_penalty,
        require_new_feature=args.require_new_feature,
        require_embedding_feature=args.require_embedding_feature,
    )
    final_payload = fit_and_report(
        best,
        x_all,
        candidates,
        target,
        sample_weight,
        row_metadata,
        train_mask,
        ridge_alpha=args.ridge_alpha,
    )
    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)
    write_candidates(out_dir / "candidate_ranking.csv", candidates)
    write_beam(out_dir / "beam_history.csv", beam_history, candidates)
    (out_dir / "metadata.json").write_text(
        json.dumps(
            {
                "script": "experiments.cognascore.compact_search",
                "training_datasets": list(train_datasets),
                "report_datasets": list(report_datasets),
                "base_model": args.base_model,
                "embedding_models": embedding_models,
                "ridge_alpha": args.ridge_alpha,
                "max_features": args.max_features,
                "beam_size": args.beam_size,
                "feature_count_penalty": args.feature_count_penalty,
                "candidate_limit": args.candidate_limit,
                "candidate_count_after_filter": len(candidates),
                "filters": {
                    "min_nonzero_fraction": args.min_nonzero_fraction,
                    "min_unique": args.min_unique,
                    "max_missing_fraction": args.max_missing_fraction,
                    "exclude_substring": args.exclude_substring,
                    "require_new_feature": args.require_new_feature,
                    "require_embedding_feature": args.require_embedding_feature,
                },
                **final_payload,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(final_payload, indent=2, ensure_ascii=False))
    print(f"wrote: {out_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search compact CognaScore formulas from existing feature tables. "
            "This script only reads feature CSVs; it does not run extraction or embeddings."
        )
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--base-model", default=EMBEDDING_MODELS["nomic"])
    parser.add_argument(
        "--embedding-model",
        action="append",
        default=[],
        help="Embedding model or short alias. Repeatable. Defaults to nomic, qwen, and jina.",
    )
    parser.add_argument(
        "--train-dataset",
        action="append",
        default=[],
        choices=DEFAULT_DATASET_KEYS,
        help="Dataset used to fit and score formulas during search. Repeatable.",
    )
    parser.add_argument(
        "--report-dataset",
        action="append",
        default=[],
        choices=DEFAULT_DATASET_KEYS,
        help="Dataset loaded and reported. Repeatable. Defaults to all current datasets.",
    )
    parser.add_argument("--max-features", type=int, default=4)
    parser.add_argument("--beam-size", type=int, default=40)
    parser.add_argument("--candidate-limit", type=int, default=360)
    parser.add_argument("--ridge-alpha", type=float, default=30.0)
    parser.add_argument(
        "--feature-count-penalty",
        type=float,
        default=0.01,
        help=(
            "Penalty subtracted from the search objective per selected feature. "
            "Compact formulas should only add a feature when it clearly helps."
        ),
    )
    parser.add_argument("--min-nonzero-fraction", type=float, default=0.05)
    parser.add_argument("--min-unique", type=int, default=8)
    parser.add_argument("--max-missing-fraction", type=float, default=0.20)
    parser.add_argument(
        "--exclude-substring",
        action="append",
        default=[],
        help="Drop features containing this substring before transforms are generated. Repeatable.",
    )
    parser.add_argument(
        "--require-new-feature",
        action="store_true",
        help="Keep only final formulas containing at least one non-size/non-lexical CognaScore feature.",
    )
    parser.add_argument(
        "--require-embedding-feature",
        action="store_true",
        help="Keep only final formulas containing at least one embedding-derived feature.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT / "compact_search" / "latest",
    )
    args = parser.parse_args()
    if not args.embedding_model:
        args.embedding_model = ["nomic", "qwen", "jina"]
    if args.max_features < 1:
        raise SystemExit("--max-features must be >= 1")
    if args.max_features > 4:
        raise SystemExit("Compact CognaScore is capped at 4 features. Use the ML route for larger models.")
    return args


def load_feature_frame(
    datasets: Sequence[str],
    *,
    base_root: Path,
    embedding_root: Path,
    base_model: str,
    embedding_models: Sequence[str],
) -> pd.DataFrame:
    frames = []
    base_slug = model_slug(base_model)
    for dataset in datasets:
        base_path = base_root / dataset / base_slug / "features.csv"
        if not base_path.exists():
            raise SystemExit(f"Missing base feature table: {base_path}")
        base = pd.read_csv(base_path)
        merged = prefix_features(base, "base")
        merged["_row_occurrence"] = merged.groupby(["dataset", "task_id"]).cumcount()
        for model in embedding_models:
            prefix = short_model_prefix(model)
            path = embedding_root / dataset / model_slug(model) / "features.csv"
            if not path.exists():
                raise SystemExit(f"Missing embedding feature table: {path}")
            embedding = pd.read_csv(path)
            embedding = prefix_features(embedding, prefix).drop(columns=["readability_score"])
            embedding["_row_occurrence"] = embedding.groupby(["dataset", "task_id"]).cumcount()
            before = len(merged)
            merged = merged.merge(
                embedding,
                on=["dataset", "task_id", "_row_occurrence"],
                how="inner",
                validate="one_to_one",
            )
            if len(merged) != before:
                raise SystemExit(
                    f"Feature identity mismatch while merging {dataset}/{prefix}: "
                    f"before={before}, after={len(merged)}"
                )
        frames.append(merged.drop(columns=["_row_occurrence"]))
    return pd.concat(frames, ignore_index=True)


def prefix_features(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    return frame.rename(
        columns={column: f"{prefix}__{column}" for column in frame.columns if column not in IDENTITY_COLUMNS}
    ).copy()


def short_model_prefix(model: str) -> str:
    for prefix, full_name in EMBEDDING_MODELS.items():
        if model == prefix or model == full_name:
            return prefix
    return model_slug(model).replace("-", "_")


def row_metadata_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for record in frame.to_dict("records"):
        label = float(record["readability_score"])
        if not math.isfinite(label):
            continue
        rows.append(
            {
                "dataset": str(record["dataset"]),
                "task_id": str(record["task_id"]),
                "readability_score": label,
            }
        )
    return rows


def rank_percentile_target(row_metadata: Sequence[Mapping[str, Any]]) -> np.ndarray:
    target = np.zeros(len(row_metadata), dtype=float)
    by_dataset: dict[str, list[int]] = {}
    for index, row in enumerate(row_metadata):
        by_dataset.setdefault(str(row["dataset"]), []).append(index)
    for indices in by_dataset.values():
        labels = np.asarray([float(row_metadata[index]["readability_score"]) for index in indices], dtype=float)
        if set(np.unique(labels)).issubset({0.0, 1.0}):
            values = labels
        elif len(labels) == 1:
            values = np.asarray([0.5], dtype=float)
        else:
            values = (rankdata(labels, method="average") - 1.0) / max(len(labels) - 1.0, 1.0)
        target[indices] = values
    return target


def build_candidates(
    frame: pd.DataFrame,
    target: np.ndarray,
    train_mask: np.ndarray,
    *,
    min_nonzero_fraction: float,
    min_unique: int,
    max_missing_fraction: float,
    exclude_substrings: Sequence[str],
) -> list[Candidate]:
    feature_columns = [
        column
        for column in frame.columns
        if column not in IDENTITY_COLUMNS and not excluded(column, exclude_substrings)
    ]
    candidates: list[Candidate] = []
    for column in feature_columns:
        raw = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        finite_train = raw[train_mask & np.isfinite(raw)]
        if len(finite_train) == 0:
            continue
        missing_fraction = 1.0 - len(finite_train) / max(int(np.sum(train_mask)), 1)
        if missing_fraction > max_missing_fraction:
            continue
        fill = float(np.median(finite_train))
        raw = np.where(np.isfinite(raw), raw, fill)
        if len(np.unique(raw[train_mask])) < min_unique:
            continue
        nonzero_fraction = float(np.mean(np.abs(raw[train_mask]) > 1e-12))
        if nonzero_fraction < min_nonzero_fraction:
            continue
        for transform_name, values in transformed_variants(raw):
            if len(np.unique(values[train_mask])) < min_unique:
                continue
            score = abs_spearman(values[train_mask], target[train_mask])
            if score is None:
                continue
            candidates.append(
                Candidate(
                    name=format_candidate_name(transform_name, column),
                    raw_name=column,
                    transform=transform_name,
                    values=values,
                    univariate_score=score,
                )
            )
    candidates.sort(key=lambda candidate: candidate.univariate_score, reverse=True)
    return candidates


def excluded(column: str, substrings: Sequence[str]) -> bool:
    lower = column.lower()
    return any(substring.lower() in lower for substring in substrings)


def transformed_variants(raw: np.ndarray) -> Iterable[tuple[str, np.ndarray]]:
    yield "identity", raw.astype(float)
    finite = raw[np.isfinite(raw)]
    if len(finite) and float(np.min(finite)) >= 0.0:
        yield "log1p", np.log1p(np.maximum(raw, 0.0))
        yield "sqrt", np.sqrt(np.maximum(raw, 0.0))


def format_candidate_name(transform: str, raw_name: str) -> str:
    return raw_name if transform == "identity" else f"{transform}({raw_name})"


def abs_spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 3 or len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return None
    value = spearmanr(x, y).correlation
    if value is None or not math.isfinite(float(value)):
        return None
    return abs(float(value))


def beam_search(
    x_all: np.ndarray,
    candidates: Sequence[Candidate],
    target: np.ndarray,
    sample_weight: np.ndarray,
    row_metadata: Sequence[Mapping[str, Any]],
    train_mask: np.ndarray,
    *,
    max_features: int,
    beam_size: int,
    ridge_alpha: float,
    feature_count_penalty: float,
    require_new_feature: bool,
    require_embedding_feature: bool,
) -> tuple[list[dict[str, Any]], BeamItem]:
    beam: list[BeamItem] = [BeamItem(features=(), score=-math.inf, train_metrics={})]
    history: list[dict[str, Any]] = []
    best: BeamItem | None = None
    for depth in range(1, max_features + 1):
        expanded: dict[tuple[int, ...], BeamItem] = {}
        for item in beam:
            used = set(item.features)
            start = item.features[-1] + 1 if item.features else 0
            for index in range(start, len(candidates)):
                if index in used:
                    continue
                features = tuple(sorted((*item.features, index)))
                if features in expanded:
                    continue
                if not formula_allowed(features, candidates, require_new_feature, require_embedding_feature, final=False):
                    continue
                score, metrics = score_subset(
                    x_all[:, features],
                    target,
                    sample_weight,
                    row_metadata,
                    train_mask,
                    ridge_alpha=ridge_alpha,
                    feature_count_penalty=feature_count_penalty,
                )
                expanded[features] = BeamItem(features=features, score=score, train_metrics=metrics)
        if not expanded:
            break
        ranked = sorted(expanded.values(), key=lambda item: item.score, reverse=True)
        beam = ranked[:beam_size]
        for rank, item in enumerate(beam, start=1):
            history.append(
                {
                    "depth": depth,
                    "rank": rank,
                    "score": item.score,
                    "features": [candidates[index].name for index in item.features],
                    "train_metrics": item.train_metrics,
                }
            )
        for item in ranked:
            if not formula_allowed(item.features, candidates, require_new_feature, require_embedding_feature, final=True):
                continue
            if best is None or item.score > best.score:
                best = item
            break
    if best is None:
        raise SystemExit("No formula satisfied the final constraints.")
    return history, best


def formula_allowed(
    features: Sequence[int],
    candidates: Sequence[Candidate],
    require_new_feature: bool,
    require_embedding_feature: bool,
    *,
    final: bool,
) -> bool:
    if not final:
        return True
    names = [candidates[index].raw_name for index in features]
    if require_embedding_feature and not any(name.startswith(("nomic__", "qwen__", "jina__")) for name in names):
        return False
    if require_new_feature and not any(is_new_cognascore_feature(name) for name in names):
        return False
    return True


def is_new_cognascore_feature(name: str) -> bool:
    traditional_markers = (
        "base__loc",
        "base__log_loc",
        "base__vocabulary_size",
        "base__token_count",
        "base__halstead_",
        "base__mean_line_length",
        "base__max_line_length",
        "base__blank_line_ratio",
    )
    return not name.startswith(traditional_markers)


def score_subset(
    x_subset: np.ndarray,
    target: np.ndarray,
    sample_weight: np.ndarray,
    row_metadata: Sequence[Mapping[str, Any]],
    train_mask: np.ndarray,
    *,
    ridge_alpha: float,
    feature_count_penalty: float,
) -> tuple[float, dict[str, dict[str, Any]]]:
    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=ridge_alpha))
    model.fit(x_subset[train_mask], target[train_mask], ridge__sample_weight=sample_weight[train_mask])
    prediction = np.asarray(model.predict(x_subset), dtype=float)
    train_rows = [row for row, keep in zip(row_metadata, train_mask) if bool(keep)]
    train_metrics = _report_metrics_by_dataset(train_rows, prediction[train_mask])
    score = objective_score(train_metrics) - feature_count_penalty * x_subset.shape[1]
    return score, train_metrics


def objective_score(metrics: Mapping[str, Mapping[str, Any]]) -> float:
    values = {
        dataset: float(row["value"])
        for dataset, row in metrics.items()
        if row.get("value") is not None and math.isfinite(float(row["value"]))
    }
    if not values:
        return -math.inf
    mean_value = float(np.mean(list(values.values())))
    minimum = float(np.min(list(values.values())))
    sota_bonus = 0.04 * len(_core_sota_objective(metrics)["secondary_hits"])
    schnappinger_bonus = 0.06 if values.get("schnappinger", -math.inf) >= CORE_SOTA_THRESHOLDS["schnappinger"] else 0.0
    return mean_value + 0.35 * minimum + sota_bonus + schnappinger_bonus


def fit_and_report(
    item: BeamItem,
    x_all: np.ndarray,
    candidates: Sequence[Candidate],
    target: np.ndarray,
    sample_weight: np.ndarray,
    row_metadata: Sequence[Mapping[str, Any]],
    train_mask: np.ndarray,
    *,
    ridge_alpha: float,
) -> dict[str, Any]:
    selected = [candidates[index] for index in item.features]
    x_selected = x_all[:, item.features]
    pipeline = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=ridge_alpha))
    pipeline.fit(x_selected[train_mask], target[train_mask], ridge__sample_weight=sample_weight[train_mask])
    prediction = np.asarray(pipeline.predict(x_selected), dtype=float)
    all_metrics = _report_metrics_by_dataset(row_metadata, prediction)
    train_rows = [row for row, keep in zip(row_metadata, train_mask) if bool(keep)]
    train_metrics = _report_metrics_by_dataset(train_rows, prediction[train_mask])
    raw_formula = raw_scale_formula(pipeline, selected)
    return {
        "selected_feature_count": len(selected),
        "selected_features": [candidate.name for candidate in selected],
        "selected_raw_features": [candidate.raw_name for candidate in selected],
        "search_objective_score": item.score,
        "formula": raw_formula["text"],
        "intercept": raw_formula["intercept"],
        "coefficients": raw_formula["coefficients"],
        "train_metrics": train_metrics,
        "all_report_metrics": all_metrics,
        "core_sota_objective_all_report": _core_sota_objective(all_metrics),
        "core_sota_objective_train_report": _core_sota_objective(train_metrics),
    }


def raw_scale_formula(pipeline: Any, selected: Sequence[Candidate]) -> dict[str, Any]:
    imputer = pipeline.named_steps["simpleimputer"]
    scaler = pipeline.named_steps["standardscaler"]
    ridge = pipeline.named_steps["ridge"]
    fills = np.asarray(imputer.statistics_, dtype=float)
    scales = np.asarray(scaler.scale_, dtype=float)
    means = np.asarray(scaler.mean_, dtype=float)
    model_coefs = np.asarray(ridge.coef_, dtype=float)
    coefficients = model_coefs / np.where(scales == 0.0, 1.0, scales)
    intercept = float(ridge.intercept_ - np.sum(coefficients * means))
    # SimpleImputer fill values affect prediction only where values are missing; feature tables should not need
    # missing-value terms in the displayed formula, but keep fills in metadata for reproducibility.
    terms = [f"{intercept:.9g}"]
    coef_payload = {}
    for coefficient, candidate, fill in zip(coefficients, selected, fills):
        coef_payload[candidate.name] = {"coefficient": float(coefficient), "missing_fill": float(fill)}
        sign = "+" if coefficient >= 0.0 else "-"
        terms.append(f" {sign} {abs(float(coefficient)):.9g} * {candidate.name}")
    return {
        "text": "score = " + "".join(terms),
        "intercept": intercept,
        "coefficients": coef_payload,
    }


def write_candidates(path: Path, candidates: Sequence[Candidate]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("rank", "feature", "raw_feature", "transform", "univariate_abs_spearman"))
        writer.writeheader()
        for rank, candidate in enumerate(candidates, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "feature": candidate.name,
                    "raw_feature": candidate.raw_name,
                    "transform": candidate.transform,
                    "univariate_abs_spearman": candidate.univariate_score,
                }
            )


def write_beam(path: Path, history: Sequence[Mapping[str, Any]], candidates: Sequence[Candidate]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("depth", "rank", "score", "features", "train_metrics"))
        writer.writeheader()
        for row in history:
            writer.writerow(
                {
                    "depth": row["depth"],
                    "rank": row["rank"],
                    "score": row["score"],
                    "features": json.dumps(row["features"], ensure_ascii=False),
                    "train_metrics": json.dumps(row["train_metrics"], ensure_ascii=False),
                }
            )


if __name__ == "__main__":
    main()
