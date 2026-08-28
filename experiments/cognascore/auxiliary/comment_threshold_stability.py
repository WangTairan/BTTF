"""Test comment-to-code threshold stability on the six readability datasets.

Comments paired with their source program are weak positives. Weak negatives
are comments borrowed from a different program in the same dataset. Sampling
is stratified, deterministic from the recorded seed, and fully exported.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev

import numpy as np

from src.experiments.registry import COGNASCORE_DEFAULT_MODEL
from src.experiments.registry import DATASETS
from src.datasets import load_code_dataset
from src.methods.cognascore.comment_relevance import (
    calibrate_comment_relevance,
    maximum_cosine_to_code,
    normalized_code_matrix,
    select_balanced_threshold,
)
from src.methods.cognascore.embedding_cache import EmbeddingCache, embedding_cache_path
from src.methods.cognascore.paths import EMBEDDING_CACHE_ROOT
from src.methods.cognascore.semantic_context import WHOLE_CODE_CONTEXT_TYPE


DEFAULT_DATASETS = ("mbjp", "buse", "dorn", "scalabrino", "schnappinger", "jetbrains")


@dataclass(frozen=True)
class CommentTask:
    dataset: str
    task_id: str
    code_matrix: np.ndarray
    comments: tuple[tuple[str, np.ndarray], ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--embedding-cache-root", type=Path, default=EMBEDDING_CACHE_ROOT)
    parser.add_argument("--dataset", action="append", dest="datasets")
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument(
        "--min-readability-percentile",
        type=float,
        default=0.5,
        help=(
            "Within-dataset human-readability percentile required for sampled "
            "programs; 0 disables the filter (default: 0.5, the upper half)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/experiments/cognascore/auxiliary/comment_threshold_stability"),
    )
    return parser.parse_args()


def load_comment_tasks(
    cache: EmbeddingCache,
    datasets: tuple[str, ...],
    minimum_scores: dict[str, float],
    readability_scores: dict[str, dict[str, float]],
) -> dict[str, list[CommentTask]]:
    placeholders = ",".join("?" for _ in datasets)
    identities = cache.connection.execute(
        f"""
        SELECT DISTINCT dataset, task_id
        FROM sources
        WHERE dataset IN ({placeholders}) AND UPPER(chunk_type) = 'COMMENT'
        ORDER BY dataset, task_id
        """,
        list(datasets),
    ).fetchall()
    grouped = {dataset: [] for dataset in datasets}
    for dataset, task_id in identities:
        dataset = str(dataset)
        task_id = str(task_id)
        score = readability_scores.get(dataset, {}).get(task_id)
        if score is None or score < minimum_scores[dataset]:
            continue
        rows = cache.task_vectors(dataset, task_id)
        comments = tuple(
            (text, vector)
            for chunk_type, text, _, vector in rows
            if chunk_type.upper() == "COMMENT"
        )
        code_rows = [
            row
            for row in rows
            if row[0].upper() != "COMMENT" and row[0] != WHOLE_CODE_CONTEXT_TYPE
        ]
        if comments and code_rows:
            grouped[dataset].append(
                CommentTask(
                    dataset=dataset,
                    task_id=task_id,
                    code_matrix=normalized_code_matrix(code_rows),
                    comments=comments,
                )
            )
    missing = [dataset for dataset, tasks in grouped.items() if len(tasks) < 2]
    if missing:
        raise ValueError(f"Need at least two comment-bearing programs per dataset: {missing}")
    return grouped


def stratified_quotas(
    sample_size: int,
    datasets: tuple[str, ...],
    rng: random.Random,
    capacities: dict[str, int] | None = None,
) -> dict[str, int]:
    if sample_size < len(datasets):
        raise ValueError("sample-size must be at least the number of datasets")
    base, remainder = divmod(sample_size, len(datasets))
    extra = set(rng.sample(list(datasets), remainder))
    quotas = {dataset: base + int(dataset in extra) for dataset in datasets}
    if capacities is None:
        return quotas
    quotas = {dataset: min(quota, capacities[dataset]) for dataset, quota in quotas.items()}
    remaining = sample_size - sum(quotas.values())
    while remaining:
        available = [dataset for dataset in datasets if quotas[dataset] < capacities[dataset]]
        if not available:
            raise ValueError(
                f"Only {sum(capacities.values())} eligible programs are available "
                f"for requested sample size {sample_size}"
            )
        rng.shuffle(available)
        for dataset in available:
            quotas[dataset] += 1
            remaining -= 1
            if remaining == 0:
                break
    return quotas


def readability_filter(
    datasets: tuple[str, ...],
    percentile: float,
) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    if not 0.0 <= percentile < 1.0:
        raise ValueError("min-readability-percentile must satisfy 0 <= value < 1")
    scores: dict[str, dict[str, float]] = {}
    cutoffs: dict[str, float] = {}
    for dataset in datasets:
        if dataset not in DATASETS:
            raise ValueError(f"Unknown registered readability dataset: {dataset!r}")
        rows = load_code_dataset(DATASETS[dataset].path)
        dataset_scores = {
            item.task_id: float(item.readability_score)
            for item in rows
            if item.readability_score is not None
        }
        if not dataset_scores:
            raise ValueError(f"Dataset {dataset!r} has no continuous readability scores")
        scores[dataset] = dataset_scores
        cutoffs[dataset] = float(np.quantile(list(dataset_scores.values()), percentile))
    return scores, cutoffs


def evaluate_repeat(
    grouped: dict[str, list[CommentTask]],
    datasets: tuple[str, ...],
    sample_size: int,
    repeat_seed: int,
    reference_threshold: float,
) -> tuple[dict[str, float | int], list[dict[str, object]]]:
    rng = random.Random(repeat_seed)
    capacities = {dataset: len(grouped[dataset]) for dataset in datasets}
    quotas = stratified_quotas(sample_size, datasets, rng, capacities)
    labels: list[int] = []
    scores: list[float] = []
    pair_rows: list[dict[str, object]] = []
    for dataset in datasets:
        quota = quotas[dataset]
        if quota > len(grouped[dataset]):
            raise ValueError(
                f"Dataset {dataset!r} has {len(grouped[dataset])} eligible programs, "
                f"fewer than quota {quota}"
            )
        selected = rng.sample(grouped[dataset], quota)
        donor_order = selected.copy()
        rng.shuffle(donor_order)
        shift = rng.randrange(1, len(donor_order))
        negative_donor = {
            donor_order[index].task_id: donor_order[(index + shift) % len(donor_order)]
            for index in range(len(donor_order))
        }
        for task in selected:
            positive_text, positive_vector = rng.choice(task.comments)
            donor = negative_donor[task.task_id]
            negative_text, negative_vector = rng.choice(donor.comments)
            for label, role, comment_task_id, text, vector in (
                (1, "paired", task.task_id, positive_text, positive_vector),
                (0, "mismatched", donor.task_id, negative_text, negative_vector),
            ):
                score = maximum_cosine_to_code(vector, task.code_matrix)
                labels.append(label)
                scores.append(score)
                pair_rows.append(
                    {
                        "repeat_seed": repeat_seed,
                        "dataset": dataset,
                        "role": role,
                        "code_task_id": task.task_id,
                        "comment_task_id": comment_task_id,
                        "comment_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "similarity": score,
                    }
                )
    label_array = np.asarray(labels, dtype=int)
    score_array = np.asarray(scores, dtype=float)
    threshold, accuracy = select_balanced_threshold(label_array, score_array)
    reference_accuracy = float(
        np.mean(score_array[label_array == 1] >= reference_threshold) / 2.0
        + np.mean(score_array[label_array == 0] < reference_threshold) / 2.0
    )
    return (
        {
            "repeat_seed": repeat_seed,
            "threshold": threshold,
            "balanced_accuracy": accuracy,
            "reference_threshold_balanced_accuracy": reference_accuracy,
            "paired_mean": float(np.mean(score_array[label_array == 1])),
            "mismatched_mean": float(np.mean(score_array[label_array == 0])),
        },
        pair_rows,
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if args.sample_size <= 0 or args.repeats <= 0:
        raise SystemExit("--sample-size and --repeats must be positive")
    datasets = tuple(args.datasets or DEFAULT_DATASETS)
    if len(set(datasets)) != len(datasets):
        raise SystemExit("Each --dataset may be specified only once")
    cache_path = embedding_cache_path(args.embedding_cache_root, args.embedding_model)
    if not cache_path.exists():
        raise SystemExit(f"Missing embedding cache: {cache_path}")
    try:
        readability_scores, minimum_scores = readability_filter(
            datasets, args.min_readability_percentile
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        grouped = load_comment_tasks(
            cache,
            datasets,
            minimum_scores,
            readability_scores,
        )
        anchor_calibration = calibrate_comment_relevance(cache)
        repeat_rows: list[dict[str, object]] = []
        pair_rows: list[dict[str, object]] = []
        for repeat in range(args.repeats):
            row, pairs = evaluate_repeat(
                grouped,
                datasets,
                args.sample_size,
                args.seed + repeat,
                anchor_calibration.threshold,
            )
            row["repeat"] = repeat
            repeat_rows.append(row)
            pair_rows.extend({"repeat": repeat, **pair} for pair in pairs)

    thresholds = np.asarray([float(row["threshold"]) for row in repeat_rows])
    accuracies = np.asarray([float(row["balanced_accuracy"]) for row in repeat_rows])
    reference_accuracies = np.asarray(
        [float(row["reference_threshold_balanced_accuracy"]) for row in repeat_rows]
    )
    paired_means = np.asarray([float(row["paired_mean"]) for row in repeat_rows])
    mismatched_means = np.asarray([float(row["mismatched_mean"]) for row in repeat_rows])
    anchor_threshold = anchor_calibration.threshold
    summary = {
        "experiment": "comment_threshold_stability",
        "weak_label_definition": {
            "positive": "comment and code originate from the same program",
            "negative": "comment originates from a different program in the same dataset",
            "caveat": "same-program pairing is a reproducible proxy, not human relevance annotation",
        },
        "embedding_model": args.embedding_model,
        "embedding_cache": str(cache_path),
        "datasets": list(datasets),
        "readability_filter": {
            "within_dataset_minimum_percentile": args.min_readability_percentile,
            "minimum_scores": minimum_scores,
        },
        "eligible_programs": {key: len(value) for key, value in grouped.items()},
        "sample_size_per_repeat": args.sample_size,
        "repeats": args.repeats,
        "base_seed": args.seed,
        "anchor_threshold": anchor_threshold,
        "resampled_threshold": {
            "mean": float(mean(thresholds)),
            "std": float(pstdev(thresholds)),
            "median": float(np.median(thresholds)),
            "p05": float(np.quantile(thresholds, 0.05)),
            "p95": float(np.quantile(thresholds, 0.95)),
            "mean_absolute_difference_from_anchor": float(
                np.mean(np.abs(thresholds - anchor_threshold))
            ),
            "fraction_within_0_01_of_anchor": float(
                np.mean(np.abs(thresholds - anchor_threshold) <= 0.01)
            ),
            "fraction_within_0_02_of_anchor": float(
                np.mean(np.abs(thresholds - anchor_threshold) <= 0.02)
            ),
        },
        "balanced_accuracy": {
            "per_repeat_optimal_threshold_mean": float(mean(accuracies)),
            "per_repeat_optimal_threshold_std": float(pstdev(accuracies)),
            "fixed_anchor_threshold_mean": float(mean(reference_accuracies)),
            "fixed_anchor_threshold_std": float(pstdev(reference_accuracies)),
            "mean_difference": float(mean(accuracies - reference_accuracies)),
        },
        "similarity": {
            "paired_mean": float(mean(paired_means)),
            "mismatched_mean": float(mean(mismatched_means)),
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "repeats.csv", repeat_rows)
    write_csv(args.output / "pairs.csv", pair_rows)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
