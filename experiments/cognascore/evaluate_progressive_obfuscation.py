"""Evaluate frozen CognaScore on grouped progressive obfuscations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Callable

import joblib
import numpy as np
import pandas as pd

from src.datasets import load_code_dataset
from src.experiments.statistics import spearman
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
    TRAINED_MODEL_ROOT,
)
from src.methods.cognascore.results import model_slug
from src.methods.cognascore.runners.supervised_ridge import load_combined_features


DATASET_KEY = "java_progressive_obfuscation"
DATASET_PATH = Path("datasets/constructed/java-progressive-obfuscation-class-100")
MODEL_NAME = "consensus26_progressive_optics_identifier_cv_development_nomic"
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EXPECTED_LEVELS = tuple(range(7))
TOLERANCE = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the frozen CognaScore model on complete L0--L6 chains."
    )
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument(
        "--model-artifact",
        type=Path,
        default=TRAINED_MODEL_ROOT / MODEL_NAME / model_slug(EMBEDDING_MODEL),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT / MODEL_NAME / "progressive_obfuscation_nomic",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest, model = load_frozen_model(args.model_artifact)
    embedding_model = str(manifest["embedding_model"])
    if embedding_model != EMBEDDING_MODEL:
        raise ValueError(f"This experiment is Nomic-only; artifact uses {embedding_model!r}")
    selected_features = [str(value) for value in manifest["features"]["ordered_names"]]

    items = load_code_dataset(args.dataset)
    item_by_id = {item.task_id: item for item in items}
    frame = load_combined_features(
        DATASET_KEY,
        args.feature_root,
        args.embedding_feature_root,
        selected_features,
    )
    feature_ids = set(str(value) for value in frame["task_id"])
    item_ids = set(item_by_id)
    if feature_ids != item_ids:
        raise ValueError(
            "Dataset/feature identity mismatch: "
            f"missing_features={len(item_ids - feature_ids)}, "
            f"unknown_feature_rows={len(feature_ids - item_ids)}"
        )

    scores = model.predict(frame[selected_features].to_numpy(dtype=float))
    predictions = build_predictions(frame, scores, item_by_id)
    summary = {
        **summarize(predictions),
        "dataset": DATASET_KEY,
        "dataset_path": str(args.dataset),
        "label_policy": "readability_target = 1 - progressive_obfuscation_level / 6",
        "label_scope": (
            "construction-order target; cumulative transformations are not "
            "independent human readability judgments"
        ),
        "model_artifact": str(args.model_artifact),
        "model_artifact_sha256": sha256_file(args.model_artifact / "model.joblib"),
        "embedding_model": embedding_model,
        "selected_feature_count": len(selected_features),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    predictions_path = args.output / "predictions.csv"
    summary_path = args.output / "summary.json"
    pd.DataFrame(predictions).to_csv(predictions_path, index=False)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print_report(summary)
    print(f"Wrote {predictions_path}", flush=True)
    print(f"Wrote {summary_path}", flush=True)


def load_frozen_model(artifact_dir: Path) -> tuple[dict[str, Any], Any]:
    manifest_path = artifact_dir / "model.json"
    if not manifest_path.is_file():
        manifest_path = artifact_dir / "metadata.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing model manifest under: {artifact_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_path = artifact_dir / str(manifest["serialized_model"])
    if not model_path.is_file():
        raise FileNotFoundError(f"Missing frozen model: {model_path}")
    actual_hash = sha256_file(model_path)
    expected_hash = str(manifest["serialized_model_sha256"])
    if actual_hash != expected_hash:
        raise ValueError(
            f"Frozen-model hash mismatch: expected {expected_hash}, got {actual_hash}"
        )
    return manifest, joblib.load(model_path)


def build_predictions(
    frame: pd.DataFrame,
    scores: np.ndarray,
    item_by_id: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record, score in zip(frame.to_dict("records"), scores):
        task_id = str(record["task_id"])
        item = item_by_id[task_id]
        metadata = item.metadata
        rows.append(
            {
                "task_id": task_id,
                "group_id": str(metadata["group_id"]),
                "source": str(metadata["source"]),
                "unit_name": str(metadata.get("unit_name", "")),
                "level": int(metadata["level"]),
                "stage": str(metadata["stage"]),
                "readability_target": float(item.readability_score),
                "score": float(score),
                "content_sha256": str(metadata["content_sha256"]),
                "parent_variant_id": metadata.get("parent_variant_id"),
            }
        )
    rows.sort(key=lambda row: (row["group_id"], row["level"]))
    return rows


def summarize(
    rows: list[dict[str, Any]],
    *,
    expected_levels: tuple[int, ...] = EXPECTED_LEVELS,
) -> dict[str, Any]:
    groups = grouped_rows(rows, expected_levels=expected_levels)
    group_correlations: list[float] = []
    non_increasing = 0
    strictly_decreasing = 0
    changed_only_decreasing = 0
    endpoints_correct = 0
    endpoint_drops: list[float] = []
    transition_rows: list[dict[str, Any]] = []

    for group in groups.values():
        scores = [float(row["score"]) for row in group]
        targets = [float(row["readability_target"]) for row in group]
        group_correlations.append(spearman(scores, targets))
        deltas = [left - right for left, right in zip(scores, scores[1:])]
        changed = [
            left["content_sha256"] != right["content_sha256"]
            for left, right in zip(group, group[1:])
        ]
        non_increasing += int(all(delta >= -TOLERANCE for delta in deltas))
        strictly_decreasing += int(all(delta > TOLERANCE for delta in deltas))
        changed_only_decreasing += int(
            all(delta > TOLERANCE for delta, did_change in zip(deltas, changed) if did_change)
        )
        endpoints_correct += int(scores[0] > scores[-1] + TOLERANCE)
        endpoint_drops.append(scores[0] - scores[-1])
        for left, right, score_drop, did_change in zip(group, group[1:], deltas, changed):
            transition_rows.append(
                {
                    "from_level": int(left["level"]),
                    "to_level": int(right["level"]),
                    "content_changed": did_change,
                    "score_drop": score_drop,
                }
            )

    finite_group_rhos = [value for value in group_correlations if math.isfinite(value)]
    return {
        "variant_count": len(rows),
        "group_count": len(groups),
        "pooled_spearman": finite_or_none(
            spearman(
                [float(row["score"]) for row in rows],
                [float(row["readability_target"]) for row in rows],
            )
        ),
        "within_group_spearman": {
            "mean": finite_or_none(mean(finite_group_rhos)) if finite_group_rhos else None,
            "median": finite_or_none(median(finite_group_rhos)) if finite_group_rhos else None,
            "valid_group_count": len(finite_group_rhos),
        },
        "chain_direction": {
            "non_increasing_group_rate": non_increasing / len(groups),
            "strictly_decreasing_group_rate": strictly_decreasing / len(groups),
            "changed_transitions_all_decrease_group_rate": changed_only_decreasing / len(groups),
            "endpoint_first_above_last_rate": endpoints_correct / len(groups),
            "mean_first_minus_last_score": mean(endpoint_drops),
        },
        "levels": level_summaries(rows, expected_levels=expected_levels),
        "adjacent_transitions": transition_summaries(
            transition_rows,
            expected_levels=expected_levels,
        ),
        "sources": source_summaries(rows, expected_levels=expected_levels),
    }


def grouped_rows(
    rows: list[dict[str, Any]],
    *,
    expected_levels: tuple[int, ...] = EXPECTED_LEVELS,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["group_id"]), []).append(row)
    for group_id, group in groups.items():
        group.sort(key=lambda row: int(row["level"]))
        levels = [int(row["level"]) for row in group]
        if levels != list(expected_levels):
            raise ValueError(f"Incomplete prediction chain for {group_id!r}: {levels}")
    return groups


def level_summaries(
    rows: list[dict[str, Any]],
    *,
    expected_levels: tuple[int, ...] = EXPECTED_LEVELS,
) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for level in expected_levels:
        values = [float(row["score"]) for row in rows if int(row["level"]) == level]
        summaries[str(level)] = {
            "count": len(values),
            "mean_score": mean(values),
            "median_score": median(values),
            "score_std": pstdev(values),
        }
    return summaries


def transition_summaries(
    rows: list[dict[str, Any]],
    *,
    expected_levels: tuple[int, ...] = EXPECTED_LEVELS,
) -> dict[str, Any]:
    def one_summary(selected: list[dict[str, Any]]) -> dict[str, Any]:
        changed = [row for row in selected if bool(row["content_changed"])]
        return {
            "count": len(selected),
            "changed_count": len(changed),
            "unchanged_count": len(selected) - len(changed),
            "decrease_rate": proportion(selected, lambda row: float(row["score_drop"]) > TOLERANCE),
            "tie_rate": proportion(selected, lambda row: abs(float(row["score_drop"])) <= TOLERANCE),
            "changed_only_decrease_rate": proportion(
                changed, lambda row: float(row["score_drop"]) > TOLERANCE
            ),
            "mean_score_drop": mean(float(row["score_drop"]) for row in selected),
            "changed_only_mean_score_drop": (
                mean(float(row["score_drop"]) for row in changed) if changed else None
            ),
        }

    by_stage = {}
    for from_level, to_level in zip(expected_levels, expected_levels[1:]):
        selected = [
            row
            for row in rows
            if int(row["from_level"]) == from_level
            and int(row["to_level"]) == to_level
        ]
        by_stage[f"L{from_level}->L{to_level}"] = one_summary(selected)
    return {"overall": one_summary(rows), "by_stage": by_stage}


def source_summaries(
    rows: list[dict[str, Any]],
    *,
    expected_levels: tuple[int, ...] = EXPECTED_LEVELS,
) -> dict[str, dict[str, Any]]:
    result = {}
    for source in sorted({str(row["source"]) for row in rows}):
        selected = [row for row in rows if str(row["source"]) == source]
        groups = grouped_rows(selected, expected_levels=expected_levels)
        group_rhos = [
            spearman(
                [float(row["score"]) for row in group],
                [float(row["readability_target"]) for row in group],
            )
            for group in groups.values()
        ]
        endpoint_correct = sum(
            float(group[0]["score"]) > float(group[-1]["score"]) + TOLERANCE
            for group in groups.values()
        )
        finite_group_rhos = [value for value in group_rhos if math.isfinite(value)]
        result[source] = {
            "variant_count": len(selected),
            "group_count": len(groups),
            "pooled_spearman": finite_or_none(
                spearman(
                    [float(row["score"]) for row in selected],
                    [float(row["readability_target"]) for row in selected],
                )
            ),
            "mean_within_group_spearman": (
                finite_or_none(mean(finite_group_rhos)) if finite_group_rhos else None
            ),
            "endpoint_first_above_last_rate": endpoint_correct / len(groups),
        }
    return result


def proportion(
    rows: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> float | None:
    if not rows:
        return None
    return sum(bool(predicate(row)) for row in rows) / len(rows)


def finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def print_report(summary: dict[str, Any]) -> None:
    chain = summary["chain_direction"]
    adjacent = summary["adjacent_transitions"]["overall"]
    print(f"Pooled Spearman: {summary['pooled_spearman']:.4f}")
    print(f"Mean within-group Spearman: {summary['within_group_spearman']['mean']:.4f}")
    print(
        f"L{EXPECTED_LEVELS[0]} > L{EXPECTED_LEVELS[-1]} groups: "
        f"{chain['endpoint_first_above_last_rate']:.1%}"
    )
    print(f"Non-increasing complete chains: {chain['non_increasing_group_rate']:.1%}")
    print(f"Adjacent decrease rate: {adjacent['decrease_rate']:.1%}")
    print(f"Changed-only adjacent decrease rate: {adjacent['changed_only_decrease_rate']:.1%}")


if __name__ == "__main__":
    main()
