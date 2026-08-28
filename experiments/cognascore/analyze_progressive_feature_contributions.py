"""Diagnose frozen Ridge feature contributions on progressive obfuscation.

This is a post-hoc external analysis.  It never refits the model and does not
use progressive-obfuscation labels for feature selection or calibration.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from src.datasets import load_code_dataset
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.runners.supervised_ridge import load_combined_features

from .evaluate_progressive_obfuscation import (
    DATASET_KEY,
    DATASET_PATH,
    EXPECTED_LEVELS,
    load_frozen_model,
)


DEFAULT_MODEL_ARTIFACT = Path(
    "frozen_models/cognascore/consensus18_6dataset_sampled_margin_nomic/"
    "nomic-ai-nomic-embed-text-v1.5"
)
DEFAULT_OUTPUT = Path(
    "results/experiments/cognascore/"
    "consensus18_6dataset_sampled_margin_nomic/progressive_feature_contributions"
)
TRANSITIONS = ((0, 1), (1, 2), (2, 3))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decompose a frozen CognaScore Ridge model on L0--L3 transitions."
    )
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--model-artifact", type=Path, default=DEFAULT_MODEL_ARTIFACT)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest, model = load_frozen_model(args.model_artifact)
    features = [str(value) for value in manifest["features"]["ordered_names"]]
    frame = load_combined_features(
        DATASET_KEY,
        args.feature_root,
        args.embedding_feature_root,
        features,
    )
    items = {item.task_id: item for item in load_code_dataset(args.dataset)}
    if set(str(value) for value in frame["task_id"]) != set(items):
        raise ValueError("Progressive dataset and feature-table task IDs do not match.")

    x = frame[features].to_numpy(dtype=float)
    transformed = x
    for step_name in ("simpleimputer", "trainingrangeclipper", "standardscaler"):
        transformed = model.named_steps[step_name].transform(transformed)
    ridge = model.named_steps["ridge"]
    coefficients = np.asarray(ridge.coef_, dtype=float).reshape(-1)
    contributions = transformed * coefficients
    raw_scores = float(ridge.intercept_) + np.sum(contributions, axis=1)
    bounded_scores = np.asarray(model.predict(x), dtype=float)
    if not np.allclose(np.clip(raw_scores, 0.0, 1.0), bounded_scores, atol=1e-10):
        raise ValueError("Linear contribution reconstruction does not match model predictions.")

    row_index = {str(task_id): index for index, task_id in enumerate(frame["task_id"])}
    groups: dict[str, dict[int, tuple[int, Any]]] = {}
    for task_id, item in items.items():
        group_id = str(item.metadata["group_id"])
        level = int(item.metadata["level"])
        groups.setdefault(group_id, {})[level] = (row_index[task_id], item)
    for group_id, levels in groups.items():
        if set(levels) != set(EXPECTED_LEVELS):
            raise ValueError(f"Incomplete chain for {group_id}: {sorted(levels)}")

    records: list[dict[str, Any]] = []
    evaluation_rows = [
        (levels[level][0], level, group_id)
        for group_id, levels in groups.items()
        for level in (1, 2, 3)
    ]
    evaluation_indices = np.asarray([row[0] for row in evaluation_rows], dtype=int)
    evaluation_levels = np.asarray([row[1] for row in evaluation_rows], dtype=float)
    baseline_l1_l3 = progressive_metrics(
        bounded_scores[evaluation_indices], evaluation_levels, evaluation_rows
    )
    for feature_index, feature in enumerate(features):
        record: dict[str, Any] = {
            "feature": feature,
            "category": feature.split("__", 1)[0],
            "standardized_coefficient": float(coefficients[feature_index]),
        }
        for left_level, right_level in TRANSITIONS:
            all_drops: list[float] = []
            changed_drops: list[float] = []
            for levels in groups.values():
                left_index, left_item = levels[left_level]
                right_index, right_item = levels[right_level]
                drop = float(
                    contributions[left_index, feature_index]
                    - contributions[right_index, feature_index]
                )
                all_drops.append(drop)
                if left_item.metadata["content_sha256"] != right_item.metadata["content_sha256"]:
                    changed_drops.append(drop)
            prefix = f"l{left_level}_l{right_level}"
            record[f"{prefix}_mean_drop_all"] = float(np.mean(all_drops))
            record[f"{prefix}_mean_drop_changed"] = (
                float(np.mean(changed_drops)) if changed_drops else 0.0
            )
            record[f"{prefix}_wrong_direction_rate_changed"] = (
                float(np.mean(np.asarray(changed_drops) < 0.0)) if changed_drops else 0.0
            )

        endpoint_drops = [
            float(contributions[levels[1][0], feature_index] - contributions[levels[3][0], feature_index])
            for levels in groups.values()
        ]
        record["l1_l3_mean_drop"] = float(np.mean(endpoint_drops))
        record["l1_l3_wrong_direction_rate"] = float(
            np.mean(np.asarray(endpoint_drops) < 0.0)
        )
        neutralized_scores = np.clip(
            raw_scores[evaluation_indices] - contributions[evaluation_indices, feature_index],
            0.0,
            1.0,
        )
        neutralized_metrics = progressive_metrics(
            neutralized_scores, evaluation_levels, evaluation_rows
        )
        for metric, value in neutralized_metrics.items():
            record[f"neutralized_{metric}"] = value
            record[f"neutralized_delta_{metric}"] = value - baseline_l1_l3[metric]
        records.append(record)

    records.sort(key=lambda row: (row["l1_l3_mean_drop"], row["feature"]))
    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "feature_contributions_l0_l3.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    summary = {
        "analysis_policy": (
            "post-hoc external diagnosis; frozen model is not refitted and progressive "
            "labels are not used"
        ),
        "model_artifact": str(args.model_artifact),
        "dataset": DATASET_KEY,
        "group_count": len(groups),
        "feature_count": len(features),
        "interpretation": (
            "positive mean_drop supports the expected readability decrease; negative "
            "mean_drop opposes it"
        ),
        "l1_l3_baseline_metrics": baseline_l1_l3,
        "neutralization_policy": (
            "set one standardized feature contribution to zero without refitting; positive "
            "metric delta means the frozen model improves under that counterfactual"
        ),
        "largest_l1_l3_drags": records[:10],
        "largest_l1_l3_supporters": list(reversed(records[-10:])),
    }
    summary_path = args.output / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print_report(records)
    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {summary_path}", flush=True)


def progressive_metrics(
    scores: np.ndarray,
    levels: np.ndarray,
    evaluation_rows: list[tuple[int, int, str]],
) -> dict[str, float]:
    pooled = float(spearmanr(-levels, scores).statistic)
    by_group: dict[str, list[tuple[int, float]]] = {}
    for (_, level, group_id), score in zip(evaluation_rows, scores, strict=True):
        by_group.setdefault(group_id, []).append((level, float(score)))
    within = [
        float(spearmanr([-level for level, _ in values], [score for _, score in values]).statistic)
        for values in by_group.values()
        if len({score for _, score in values}) > 1
    ]
    monotonic = [
        all(left >= right for left, right in zip(group_scores, group_scores[1:]))
        for values in by_group.values()
        for group_scores in [[score for _, score in sorted(values)]]
    ]
    return {
        "pooled_spearman": pooled,
        "mean_within_group_spearman": float(np.mean(within)),
        "non_increasing_chain_rate": float(np.mean(monotonic)),
    }


def print_report(records: list[dict[str, Any]]) -> None:
    print("Largest L1->L3 opposing contributions:")
    for row in records[:10]:
        print(
            f"  {row['feature']}: {row['l1_l3_mean_drop']:+.6f} "
            f"(wrong in {row['l1_l3_wrong_direction_rate']:.1%} of groups)"
        )
    print("Largest L1->L3 supporting contributions:")
    for row in reversed(records[-10:]):
        print(
            f"  {row['feature']}: {row['l1_l3_mean_drop']:+.6f} "
            f"(wrong in {row['l1_l3_wrong_direction_rate']:.1%} of groups)"
        )
    print("Largest improvements after neutralizing one feature (no refit):")
    by_neutralized_gain = sorted(
        records,
        key=lambda row: row["neutralized_delta_pooled_spearman"],
        reverse=True,
    )
    for row in by_neutralized_gain[:10]:
        print(
            f"  {row['feature']}: pooled Spearman "
            f"{row['neutralized_delta_pooled_spearman']:+.6f}, within-group "
            f"{row['neutralized_delta_mean_within_group_spearman']:+.6f}, monotonic "
            f"{row['neutralized_delta_non_increasing_chain_rate']:+.1%}"
        )


if __name__ == "__main__":
    main()
