"""Small paired probe on the constructed non-informative-comment interference."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.datasets import load_code_dataset
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS
from src.methods.cognascore.comment_relevance import (
    calibrate_comment_relevance,
    maximum_cosine_to_code,
    normalized_code_matrix,
)
from src.methods.cognascore.embedding_cache import EmbeddingCache, embedding_cache_path
from src.methods.cognascore.paths import EMBEDDING_CACHE_ROOT
from src.methods.cognascore.semantic_context import WHOLE_CODE_CONTEXT_TYPE


INTERFERENCE = "inject-natural-language-comment"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--embedding-cache-root", type=Path, default=EMBEDDING_CACHE_ROOT)
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument(
        "--stability-summary",
        type=Path,
        default=Path(
            "results/experiments/cognascore/auxiliary/"
            "comment_threshold_stability/summary.json"
        ),
    )
    parser.add_argument(
        "--threshold-config",
        type=Path,
        default=Path("experiments/cognascore/auxiliary/comment_threshold.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/experiments/cognascore/auxiliary/comment_constructed_probe"),
    )
    return parser.parse_args()


def comment_scores(
    cache: EmbeddingCache,
    task_id: str,
) -> dict[str, float]:
    rows = cache.task_vectors("java_comparative_obfuscation", task_id)
    comment_rows = [row for row in rows if row[0].upper() == "COMMENT"]
    code_rows = [
        row
        for row in rows
        if row[0].upper() != "COMMENT" and row[0] != WHOLE_CODE_CONTEXT_TYPE
    ]
    if not comment_rows or not code_rows:
        return {}
    code_matrix = normalized_code_matrix(code_rows)
    return {
        text: maximum_cosine_to_code(vector, code_matrix)
        for _, text, _, vector in comment_rows
    }


def threshold_metrics(
    pairs: list[dict[str, object]],
    threshold: float,
) -> dict[str, float | int]:
    direction_hits = 0
    nondirection_hits = 0
    original_labels: list[bool] = []
    injected_labels: list[bool] = []
    for pair in pairs:
        original = np.asarray(pair["original_scores"], dtype=float)
        injected = np.asarray(pair["injected_scores"], dtype=float)
        new = np.asarray(pair["new_comment_scores"], dtype=float)
        original_ratio = float(np.mean(original < threshold)) if original.size else 0.0
        injected_ratio = float(np.mean(injected < threshold)) if injected.size else 0.0
        pair[f"original_irrelevant_ratio@{threshold:.6f}"] = original_ratio
        pair[f"injected_irrelevant_ratio@{threshold:.6f}"] = injected_ratio
        direction_hits += int(injected_ratio > original_ratio)
        nondirection_hits += int(injected_ratio >= original_ratio)
        original_labels.extend((original >= threshold).tolist())
        injected_labels.extend((new < threshold).tolist())
    original_tpr = float(np.mean(original_labels)) if original_labels else float("nan")
    injected_tnr = float(np.mean(injected_labels)) if injected_labels else float("nan")
    return {
        "threshold": threshold,
        "sampled_groups": len(pairs),
        "strict_pairwise_direction_accuracy": direction_hits / len(pairs),
        "nondecreasing_pairwise_direction_accuracy": nondirection_hits / len(pairs),
        "new_injected_comment_detection_rate": injected_tnr,
        "original_comment_retention_rate": original_tpr,
        "proxy_balanced_accuracy": (original_tpr + injected_tnr) / 2.0,
    }


def main() -> None:
    args = parse_args()
    if args.sample_size <= 0:
        raise SystemExit("--sample-size must be positive")
    if not args.stability_summary.exists():
        raise SystemExit(
            f"Missing stability result: {args.stability_summary}. "
            "Run comment_threshold_stability first."
        )
    stability = json.loads(args.stability_summary.read_text(encoding="utf-8"))
    resampled_threshold = float(stability["resampled_threshold"]["median"])
    threshold_config = json.loads(args.threshold_config.read_text(encoding="utf-8"))
    configured_threshold = float(threshold_config["threshold"])
    if threshold_config["embedding_model"] != args.embedding_model:
        raise SystemExit(
            "Threshold configuration embedding model does not match --embedding-model"
        )
    if not math.isclose(configured_threshold, resampled_threshold, abs_tol=1e-12):
        raise SystemExit(
            "Configured comment threshold does not match the reproduced stability median: "
            f"{configured_threshold} != {resampled_threshold}"
        )
    items = load_code_dataset(DATASETS["java_comparative_obfuscation"].path)
    by_group: dict[str, dict[str, str]] = defaultdict(dict)
    for item in items:
        group_id = str(item.metadata["group_id"])
        interference = item.metadata.get("interference")
        if interference is None:
            by_group[group_id]["original"] = item.task_id
        elif interference == INTERFERENCE:
            by_group[group_id]["injected"] = item.task_id
    complete = sorted(
        group_id
        for group_id, identities in by_group.items()
        if {"original", "injected"}.issubset(identities)
    )
    if args.sample_size > len(complete):
        raise SystemExit(f"Requested {args.sample_size} groups but only {len(complete)} are complete")
    selected = random.Random(args.seed).sample(complete, args.sample_size)
    cache_path = embedding_cache_path(args.embedding_cache_root, args.embedding_model)
    if not cache_path.exists():
        raise SystemExit(f"Missing embedding cache: {cache_path}")
    pairs: list[dict[str, object]] = []
    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        anchor_threshold = calibrate_comment_relevance(cache).threshold
        for group_id in selected:
            identities = by_group[group_id]
            original_scores = comment_scores(cache, identities["original"])
            injected_scores = comment_scores(cache, identities["injected"])
            new_comments = sorted(set(injected_scores) - set(original_scores))
            if not new_comments:
                raise ValueError(f"No newly injected comment embeddings for group {group_id}")
            pairs.append(
                {
                    "group_id": group_id,
                    "original_task_id": identities["original"],
                    "injected_task_id": identities["injected"],
                    "original_scores": list(original_scores.values()),
                    "injected_scores": list(injected_scores.values()),
                    "new_comment_scores": [injected_scores[text] for text in new_comments],
                    "new_comment_count": len(new_comments),
                }
            )

    thresholds = {
        "handcrafted_anchor": anchor_threshold,
        "selected_high_readability_resampled_median": configured_threshold,
    }
    metrics = {
        name: threshold_metrics(pairs, threshold)
        for name, threshold in thresholds.items()
    }
    summary = {
        "experiment": "comment_constructed_probe",
        "interference": INTERFERENCE,
        "embedding_model": args.embedding_model,
        "embedding_cache": str(cache_path),
        "sample_size": args.sample_size,
        "seed": args.seed,
        "available_complete_groups": len(complete),
        "thresholds": thresholds,
        "selected_threshold_config": str(args.threshold_config),
        "metrics": metrics,
        "interpretation_caveat": (
            "Injected comments are known non-informative negatives. Original comments are "
            "treated only as weak positives and may include licenses or unrelated prose."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "pairs.csv").open("w", newline="", encoding="utf-8") as handle:
        scalar_rows = [
            {key: value for key, value in pair.items() if not isinstance(value, list)}
            for pair in pairs
        ]
        writer = csv.DictWriter(handle, fieldnames=list(scalar_rows[0]))
        writer.writeheader()
        writer.writerows(scalar_rows)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
