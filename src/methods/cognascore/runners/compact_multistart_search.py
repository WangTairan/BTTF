from __future__ import annotations

import argparse
import csv
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from src.experiments.statistics import matthews_correlation_coefficient
from src.methods.cognascore.results import model_slug


DATASETS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")
TRAIN_DATASETS = ("scalabrino", "schnappinger", "dorn", "buse")
EMBEDDING_MODELS = {
    "nomic": "nomic-ai/nomic-embed-text-v1.5",
    "qwen": "Qwen/Qwen3-Embedding-0.6B",
    "jina": "jinaai/jina-embeddings-v2-base-code",
}
SOTA_THRESHOLDS = {
    "scalabrino": 0.5919,
    "schnappinger": 0.6057,
    "dorn": 0.5857,
    "jetbrains": 0.3594,
}


@dataclass(frozen=True)
class Variant:
    name: str
    values: np.ndarray
    source: str
    core: bool
    expected_sign: int
    score: float
    family: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Large multi-start compact CognaScore formula search over base + multi-embedding features."
    )
    parser.add_argument("--base-root", type=Path, default=Path("output/cognascore_features"))
    parser.add_argument("--embedding-root", type=Path, default=Path("output/cognascore_embedding_features"))
    parser.add_argument("--output", type=Path, default=Path("output/cognascore_compact_multistart_search"))
    parser.add_argument("--ridge-alpha", type=float, default=30.0)
    parser.add_argument("--max-size", type=int, default=4, choices=(2, 3, 4, 5))
    parser.add_argument("--base-top", type=int, default=60)
    parser.add_argument("--core-top", type=int, default=160)
    parser.add_argument("--core-pair-top", type=int, default=80)
    parser.add_argument("--base-pair-top", type=int, default=35)
    parser.add_argument("--keep", type=int, default=1000)
    parser.add_argument("--min-nonzero", type=float, default=0.75)
    parser.add_argument("--min-unique", type=int, default=12)
    parser.add_argument("--allow-halstead", action="store_true")
    parser.add_argument("--exclude-family", action="append", default=[])
    parser.add_argument("--include-fixed-kmeans", action="store_true", default=True)
    parser.add_argument("--include-control-flow", action="store_true")
    parser.add_argument("--allow-noise", action="store_true")
    parser.add_argument("--objective", choices=("balanced", "scalabrino", "sota"), default="balanced")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = load_frame(args)
    context = prepare_context(frame)
    variants = build_variants(frame, context, args)
    base = [variant for variant in variants if not variant.core][: args.base_top]
    core = [variant for variant in variants if variant.core][: args.core_top]
    print(f"base variants: {len(base)}")
    print([variant.name for variant in base[:20]])
    print(f"core variants: {len(core)}")
    print([variant.name for variant in core[:30]])

    results = search(base=base, core=core, context=context, args=args)
    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    write_results(output_dir / "top_results.csv", results[: args.keep])
    metadata = {
        "ridge_alpha": args.ridge_alpha,
        "max_size": args.max_size,
        "base_top": args.base_top,
        "core_top": args.core_top,
        "base_pair_top": args.base_pair_top,
        "core_pair_top": args.core_pair_top,
        "min_nonzero": args.min_nonzero,
        "min_unique": args.min_unique,
        "allow_halstead": args.allow_halstead,
        "exclude_family": args.exclude_family,
        "include_fixed_kmeans": args.include_fixed_kmeans,
        "include_control_flow": args.include_control_flow,
        "allow_noise": args.allow_noise,
        "objective": args.objective,
        "top_base": [variant.name for variant in base],
        "top_core": [variant.name for variant in core],
        "best": [result_summary(row) for row in results[:100]],
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(output_dir / "top_results.csv")
    for index, row in enumerate(results[:20], start=1):
        print()
        print(f"#{index} hits={row['hits']} coremean={row['coremean']:.4f}")
        print({dataset: round(row[dataset], 4) for dataset in DATASETS})
        print(row["features"])
        print("std_effects", [round(value, 4) for value in row["std_effects"]])
        print(row["formula"])


def load_frame(args: argparse.Namespace) -> pd.DataFrame:
    rows = []
    ids = ["dataset", "task_id", "readability_score"]
    default_slug = model_slug(EMBEDDING_MODELS["nomic"])
    for dataset in DATASETS:
        base = pd.read_csv(args.base_root / dataset / default_slug / "features.csv")
        frame = base.rename(columns={column: f"base__{column}" for column in base.columns if column not in ids}).copy()
        for prefix, model in EMBEDDING_MODELS.items():
            slug = model_slug(model)
            embedding = pd.read_csv(args.embedding_root / dataset / slug / "features.csv")
            embedding = embedding.rename(
                columns={column: f"{prefix}__{column}" for column in embedding.columns if column not in ids}
            ).copy()
            frame = pd.concat(
                [frame.reset_index(drop=True), embedding.drop(columns=ids).reset_index(drop=True)],
                axis=1,
            )
        frame["dataset_key"] = dataset
        rows.append(frame.copy())
    return pd.concat(rows, ignore_index=True)


def prepare_context(frame: pd.DataFrame) -> dict[str, Any]:
    train_mask = frame["dataset_key"].isin(TRAIN_DATASETS).to_numpy()
    train = frame.loc[train_mask].reset_index(drop=True)
    y = np.zeros(len(train), dtype=float)
    for _, indices in train.groupby("dataset_key").groups.items():
        labels = train.loc[indices, "readability_score"].astype(float).to_numpy()
        y[list(indices)] = (rankdata(labels, method="average") - 1.0) / max(len(labels) - 1.0, 1.0)
    indices_by_dataset = {}
    ranks_by_dataset = {}
    labels_by_dataset = {}
    binary_by_dataset = {}
    for dataset, group in frame.groupby("dataset_key"):
        indices = group.index.to_numpy()
        labels = group["readability_score"].astype(float).to_numpy()
        binary = set(np.unique(labels)).issubset({0.0, 1.0})
        indices_by_dataset[dataset] = indices
        labels_by_dataset[dataset] = labels.astype(int)
        binary_by_dataset[dataset] = binary
        ranks_by_dataset[dataset] = None if binary else rankdata(labels, method="average")
    return {
        "train_mask": train_mask,
        "target": y,
        "indices_by_dataset": indices_by_dataset,
        "ranks_by_dataset": ranks_by_dataset,
        "labels_by_dataset": labels_by_dataset,
        "binary_by_dataset": binary_by_dataset,
        "frame": frame,
    }


def build_variants(frame: pd.DataFrame, context: dict[str, Any], args: argparse.Namespace) -> list[Variant]:
    variants = []
    for source in frame.columns:
        if not is_allowed_source(source, args):
            continue
        raw = raw_values(frame, source)
        if not coverage_ok(raw, context["train_mask"], args):
            continue
        for name, values in transformed_values(source, raw):
            if values[context["train_mask"]].std() <= 1e-12:
                continue
            family = feature_family(source)
            score = variant_score(values, context, objective=args.objective)
            variants.append(
                Variant(
                    name=name,
                    values=values,
                    source=source,
                    core=is_core_source(source),
                    expected_sign=expected_sign(source),
                    score=score,
                    family=family,
                )
            )
    variants.sort(key=lambda item: (item.score, item.core), reverse=True)
    return variants


def is_allowed_source(source: str, args: argparse.Namespace) -> bool:
    if source in {"dataset", "task_id", "readability_score", "dataset_key"}:
        return False
    lower = source.lower()
    if not args.allow_halstead and "halstead" in lower:
        return False
    if not args.include_control_flow and "control_flow" in lower:
        return False
    if not args.allow_noise and "noise" in lower:
        return False
    if any(family and family in lower for family in args.exclude_family):
        return False
    blocked = [
        "generalized_score",
        "supervised_score",
        "source_count",
        "coverage_ratio",
        "unique_text_count",
        "algorithm_unique_text_count",
        "selected_k",
        "min_samples",
        "min_cluster_size",
        "eps",
        "xi",
        "similarity_threshold",
        "persistence",
        "membership_strength",
    ]
    if any(token in lower for token in blocked):
        return False
    if not args.include_fixed_kmeans and "__kmeans_k_" in source:
        return False
    if source.startswith("base__"):
        return any(
            token in lower
            for token in [
                "vocabulary",
                "loc",
                "line_length",
                "blank_line",
                "byte_entropy",
                "lexeme_entropy",
                "visual_operator_density",
                "visual_token_density",
                "visual_identifier_density",
                "visual_keyword_density",
                "semantic_chunk_count",
                "semantic_chunk_ratio",
                "chunk_chars_cv",
                "log_avg_chunk_chars",
                "chunks_per_loc",
                "chunks_per_source_line",
                "type_identifier_count",
                "type_logical_count",
                "type_call_count",
                "type_assignment_count",
                "type_comparison_count",
                "type_arithmetic_count",
                "cluster_count",
                "cluster_diameter",
                "avg_cluster_diameter",
            ]
        )
    return any(
        token in lower
        for token in [
            "embedding_centroid_norm",
            "embedding_mean_cosine_to_centroid",
            "embedding_std_cosine_to_centroid",
            "embedding_max_cosine_to_centroid",
            "embedding_pairwise_cosine_mean",
            "embedding_pairwise_cosine_std",
            "embedding_effective_rank",
            "kmeans_k_2",
            "kmeans_k_4",
            "kmeans_k_8",
            "kmeans_k_16",
            "auto_kmeans_cluster",
            "auto_kmeans_silhouette",
            "auto_kmeans_inertia_per_weight",
            "auto_dbscan_cluster_count",
            "auto_dbscan_cluster_diameter",
            "auto_dbscan_cluster_type_entropy",
            "auto_dbscan_cluster_type_purity",
            "auto_dbscan_mixed_cluster_ratio",
            "hdbscan_cluster_count",
            "hdbscan_cluster_diameter",
            "hdbscan_cluster_type_entropy",
            "hdbscan_cluster_type_purity",
            "hdbscan_mixed_cluster_ratio",
            "optics_cluster_count",
            "optics_cluster_diameter",
            "optics_cluster_type_entropy",
            "optics_cluster_type_purity",
            "optics_mixed_cluster_ratio",
            "graph_component_count",
            "graph_edge_density",
            "graph_component_diameter",
            "graph_component_type_entropy",
            "graph_component_type_purity",
            "graph_mixed_component_ratio",
        ]
    )


def raw_values(frame: pd.DataFrame, source: str) -> np.ndarray:
    values = pd.to_numeric(frame[source], errors="coerce").to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    fill = float(np.median(finite)) if len(finite) else 0.0
    return np.where(np.isfinite(values), values, fill)


def transformed_values(source: str, raw: np.ndarray) -> list[tuple[str, np.ndarray]]:
    values = [(source, raw)]
    if raw.min() >= 0:
        values.extend(
            [
                (f"log1p({source})", np.log1p(raw)),
                (f"sqrt({source})", np.sqrt(raw)),
            ]
        )
    return values


def coverage_ok(values: np.ndarray, train_mask: np.ndarray, args: argparse.Namespace) -> bool:
    train_values = values[train_mask]
    nonzero = float(np.mean(np.abs(train_values) > 1e-12))
    unique = len(np.unique(train_values))
    return nonzero >= args.min_nonzero and unique >= args.min_unique


def variant_score(values: np.ndarray, context: dict[str, Any], *, objective: str) -> float:
    train_mask = context["train_mask"]
    train_score = abs_rank_corr(values[train_mask], context["target"])
    scalabrino = dataset_variant_corr(values, context, "scalabrino")
    schnappinger = dataset_variant_corr(values, context, "schnappinger")
    dorn = dataset_variant_corr(values, context, "dorn")
    if objective == "scalabrino":
        return 0.60 * scalabrino + 0.25 * train_score + 0.15 * schnappinger
    if objective == "sota":
        return 0.30 * train_score + 0.25 * schnappinger + 0.25 * dorn + 0.20 * scalabrino
    return 0.35 * train_score + 0.30 * scalabrino + 0.20 * schnappinger + 0.15 * dorn


def dataset_variant_corr(values: np.ndarray, context: dict[str, Any], dataset: str) -> float:
    indices = context["indices_by_dataset"][dataset]
    labels = context["frame"].loc[indices, "readability_score"].astype(float).to_numpy()
    return abs_rank_corr(values[indices], labels)


def abs_rank_corr(left: np.ndarray, right: np.ndarray) -> float:
    left_rank = rankdata(left, method="average")
    right_rank = rankdata(right, method="average")
    if left_rank.std() <= 1e-12 or right_rank.std() <= 1e-12:
        return 0.0
    return abs(float(np.corrcoef(left_rank, right_rank)[0, 1]))


def is_core_source(source: str) -> bool:
    lower = source.lower()
    return not source.startswith("base__") or any(
        token in lower for token in ["chunk", "type_", "cluster", "embedding", "kmeans", "hdbscan", "optics", "graph"]
    )


def expected_sign(source: str) -> int:
    lower = source.lower()
    if any(token in lower for token in ["purity", "silhouette", "edge_density", "semantic_chunk_ratio"]):
        return 1
    return -1


def feature_family(source: str) -> str:
    if source.startswith("base__"):
        return source.split("__", 1)[1].split("_", 1)[0]
    prefix, rest = source.split("__", 1)
    if "__" in rest:
        view, feature = rest.split("__", 1)
        return f"{prefix}:{view}:{feature.split('_', 1)[0]}"
    return f"{prefix}:{rest.split('_', 1)[0]}"


def search(*, base: Sequence[Variant], core: Sequence[Variant], context: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    combos: list[tuple[Variant, ...]] = []
    combos.extend((b, c) for b in base for c in core)
    if args.max_size >= 3:
        combos.extend((b1, b2, c) for b1, b2 in itertools.combinations(base, 2) for c in core)
        combos.extend((b, c1, c2) for b in base for c1, c2 in itertools.combinations(core[: args.core_pair_top], 2))
    if args.max_size >= 4:
        combos.extend(
            (b1, b2, c1, c2)
            for b1, b2 in itertools.combinations(base[: args.base_pair_top], 2)
            for c1, c2 in itertools.combinations(core[: args.core_pair_top], 2)
        )
    if args.max_size >= 5:
        combos.extend(
            (b1, b2, c1, c2, c3)
            for b1, b2 in itertools.combinations(base[: max(args.base_pair_top // 2, 1)], 2)
            for c1, c2, c3 in itertools.combinations(core[: max(args.core_pair_top // 2, 1)], 3)
        )

    results = []
    for combo in combos:
        if len({variant.source for variant in combo}) != len(combo):
            continue
        prediction, intercept, coefficients, matrix = ridge_fit_predict(combo, context, args.ridge_alpha)
        if not sign_ok(combo, coefficients):
            continue
        metrics = metrics_by_dataset(prediction, context)
        hits = sum(metrics[dataset] >= threshold for dataset, threshold in SOTA_THRESHOLDS.items())
        coremean = float(np.mean([metrics[dataset] for dataset in ("scalabrino", "schnappinger", "dorn", "buse")]))
        std_effects = (coefficients * matrix[context["train_mask"]].std(axis=0)).tolist()
        results.append(
            {
                "hits": int(hits),
                "coremean": coremean,
                "features": [variant.name for variant in combo],
                "source_features": [variant.source for variant in combo],
                "families": [variant.family for variant in combo],
                "std_effects": [float(value) for value in std_effects],
                "formula": formula_text(intercept, coefficients, combo),
                **{dataset: float(metrics[dataset]) for dataset in DATASETS},
            }
        )
    results.sort(key=lambda row: sort_key(row, args.objective), reverse=True)
    return results


def ridge_fit_predict(
    combo: Sequence[Variant],
    context: dict[str, Any],
    alpha: float,
) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    matrix = np.column_stack([variant.values for variant in combo])
    train = matrix[context["train_mask"]]
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std = np.where(std <= 1e-12, 1.0, std)
    target = context["target"]
    target_mean = float(target.mean())
    scaled = (train - mean) / std
    coef_scaled = np.linalg.solve(scaled.T @ scaled + alpha * np.eye(len(combo)), scaled.T @ (target - target_mean))
    coefficients = coef_scaled / std
    intercept = target_mean - float(mean @ coefficients)
    prediction = matrix @ coefficients + intercept
    return prediction, intercept, coefficients, matrix


def sign_ok(combo: Sequence[Variant], coefficients: np.ndarray) -> bool:
    for variant, coefficient in zip(combo, coefficients):
        if variant.expected_sign < 0 and coefficient > 1e-10:
            return False
        if variant.expected_sign > 0 and coefficient < -1e-10:
            return False
    return True


def metrics_by_dataset(prediction: np.ndarray, context: dict[str, Any]) -> dict[str, float]:
    metrics = {}
    for dataset in DATASETS:
        indices = context["indices_by_dataset"][dataset]
        scores = prediction[indices]
        if context["binary_by_dataset"][dataset]:
            metrics[dataset] = best_mcc(scores, context["labels_by_dataset"][dataset])
        else:
            score_rank = rankdata(scores, method="average")
            label_rank = context["ranks_by_dataset"][dataset]
            metrics[dataset] = 0.0 if score_rank.std() <= 1e-12 else float(np.corrcoef(score_rank, label_rank)[0, 1])
    return metrics


def best_mcc(scores: np.ndarray, labels: np.ndarray) -> float:
    order = np.argsort(scores)
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    tp = int((sorted_labels == 1).sum())
    fp = int((sorted_labels == 0).sum())
    tn = 0
    fn = 0
    best = mcc_counts(tp, tn, fp, fn)
    for index, label in enumerate(sorted_labels):
        if label == 1:
            tp -= 1
            fn += 1
        else:
            fp -= 1
            tn += 1
        if index + 1 < len(sorted_scores) and sorted_scores[index + 1] == sorted_scores[index]:
            continue
        best = max(best, mcc_counts(tp, tn, fp, fn))
    return float(best)


def mcc_counts(tp: int, tn: int, fp: int, fn: int) -> float:
    denominator = ((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) ** 0.5
    if denominator == 0:
        return 0.0
    return float((tp * tn - fp * fn) / denominator)


def formula_text(intercept: float, coefficients: Sequence[float], combo: Sequence[Variant]) -> str:
    text = f"score = {intercept:.9g}"
    for coefficient, variant in zip(coefficients, combo):
        sign = "+" if coefficient >= 0 else "-"
        text += f" {sign} {abs(float(coefficient)):.9g} * {variant.name}"
    return text


def sort_key(row: dict[str, Any], objective: str) -> tuple[Any, ...]:
    if objective == "scalabrino":
        return (row["scalabrino"] >= 0.57, row["scalabrino"], row["hits"], row["coremean"], row["schnappinger"])
    if objective == "sota":
        return (row["hits"], row["coremean"], row["scalabrino"], row["jetbrains"])
    return (row["scalabrino"] >= 0.57, row["hits"], row["coremean"], row["scalabrino"], row["jetbrains"])


def write_results(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    columns = [
        "rank",
        "hits",
        "coremean",
        "scalabrino",
        "schnappinger",
        "dorn",
        "buse",
        "jetbrains",
        "mbjp",
        "features",
        "source_features",
        "families",
        "std_effects",
        "formula",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    **{
                        key: json.dumps(value) if isinstance(value, list) else value
                        for key, value in row.items()
                        if key in columns
                    },
                }
            )


def result_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in [
            "hits",
            "coremean",
            "scalabrino",
            "schnappinger",
            "dorn",
            "buse",
            "jetbrains",
            "mbjp",
            "features",
            "formula",
        ]
    }


if __name__ == "__main__":
    main()
