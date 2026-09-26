"""Evaluate the frozen final model on paired transformed variants."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

import pandas as pd
import joblib

from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
    LLM_FEATURE_ROOT,
    TRAINED_MODEL_ROOT,
)
from src.methods.readability_model.results import model_slug
from src.methods.readability_model.runners.supervised_ridge import load_combined_features

DATASET_KEYS = (
    "java_comparative_obfuscation",
    "python_comparative_degradation",
)
MODEL_NAME = "consensus11_6dataset_three_llm_opencoder_jina"
DEFAULT_EMBEDDING_MODEL = "jinaai/jina-embeddings-v2-base-code"
TOLERANCE = 1e-12


def load_frozen_model(artifact_dir: Path) -> tuple[dict[str, Any], Any]:
    """Load a frozen pipeline only after verifying its recorded SHA-256."""
    manifest_path = artifact_dir / "model.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing frozen-model manifest: {manifest_path}")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare each independently transformed class with its matched original."
    )
    parser.add_argument("--dataset", choices=DATASET_KEYS, action="append")
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--llm-feature-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument(
        "--model-artifact",
        type=Path,
        default=(
            TRAINED_MODEL_ROOT / MODEL_NAME / model_slug(DEFAULT_EMBEDDING_MODEL)
        ),
    )
    parser.add_argument(
        "-o",
        "--output-root",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT / MODEL_NAME / "constructed_variants",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest, model = load_frozen_model(args.model_artifact)
    selected_features = [str(value) for value in manifest["features"]["ordered_names"]]
    selected_datasets = args.dataset or list(DATASET_KEYS)

    for dataset_key in selected_datasets:
        dataset_path = DATASETS[dataset_key].path
        items = load_code_dataset(dataset_path)
        item_by_id = {item.task_id: item for item in items}
        frame = load_combined_features(
            dataset_key,
            args.feature_root,
            args.embedding_feature_root,
            selected_features,
            llm_feature_root=args.llm_feature_root,
            embedding_model=str(manifest["embedding_model"]),
            llm_model=str(manifest.get("llm_feature_model") or ""),
        )
        validate_identities(frame, item_by_id)
        scores = model.predict(frame[selected_features].to_numpy(dtype=float))
        rows = prediction_rows(frame, scores, item_by_id)
        summary = {
            **summarize_paired_variants(rows),
            "dataset": dataset_key,
            "dataset_path": str(dataset_path),
            "evaluation_protocol": (
                "Each independent transformation is paired with its original class; "
                "a response is correct when the frozen readability score decreases."
            ),
            "model_artifact": str(args.model_artifact),
            "embedding_model": str(manifest["embedding_model"]),
            "llm_feature_model": manifest.get("llm_feature_model"),
            "selected_feature_count": len(selected_features),
        }
        output = args.output_root / dataset_key
        output.mkdir(parents=True, exist_ok=True)
        predictions_path = output / "predictions.csv"
        summary_path = output / "summary.json"
        pd.DataFrame(rows).to_csv(predictions_path, index=False)
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print_report(summary)
        print(f"Wrote {predictions_path}", flush=True)
        print(f"Wrote {summary_path}", flush=True)


def validate_identities(frame: pd.DataFrame, item_by_id: dict[str, Any]) -> None:
    feature_ids = set(str(value) for value in frame["task_id"])
    item_ids = set(item_by_id)
    if feature_ids != item_ids:
        raise ValueError(
            "Dataset/feature identity mismatch: "
            f"missing_features={len(item_ids - feature_ids)}, "
            f"unknown_feature_rows={len(feature_ids - item_ids)}"
        )


def prediction_rows(
    frame: pd.DataFrame,
    scores: Any,
    item_by_id: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record, score in zip(frame.to_dict("records"), scores):
        task_id = str(record["task_id"])
        metadata = item_by_id[task_id].metadata
        rows.append(
            {
                "task_id": task_id,
                "group_id": str(metadata["group_id"]),
                "source": str(metadata["source"]),
                "unit_name": str(metadata.get("unit_name", "")),
                "position": int(metadata.get("order", metadata["level"])),
                "stage": str(metadata["stage"]),
                "interference": metadata.get("interference"),
                "category": metadata.get("category"),
                "is_baseline": bool(metadata["is_baseline_variant"]),
                "score": float(score),
                "content_sha256": str(metadata["content_sha256"]),
            }
        )
    rows.sort(key=lambda row: (row["group_id"], row["position"]))
    return rows


def summarize_paired_variants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row["group_id"]), []).append(row)

    paired: list[dict[str, Any]] = []
    for group_id, group in groups.items():
        baselines = [row for row in group if row["is_baseline"]]
        if len(baselines) != 1:
            raise ValueError(f"Expected one original for {group_id!r}, got {len(baselines)}")
        baseline = baselines[0]
        for variant in group:
            if variant["is_baseline"]:
                continue
            score_drop = float(baseline["score"]) - float(variant["score"])
            paired.append(
                {
                    **variant,
                    "original_task_id": baseline["task_id"],
                    "original_score": float(baseline["score"]),
                    "content_changed": (
                        baseline["content_sha256"] != variant["content_sha256"]
                    ),
                    "score_drop": score_drop,
                }
            )

    by_interference: dict[str, dict[str, Any]] = {}
    for label in sorted({pair_label(row) for row in paired}):
        by_interference[label] = summarize_pairs(
            [row for row in paired if pair_label(row) == label]
        )

    by_category: dict[str, dict[str, Any]] = {}
    categories = sorted({str(row["category"]) for row in paired if row.get("category")})
    for category in categories:
        by_category[category] = summarize_pairs(
            [row for row in paired if str(row.get("category")) == category]
        )

    return {
        "variant_count": len(rows),
        "group_count": len(groups),
        "transformed_pair_count": len(paired),
        "overall": summarize_pairs(paired),
        "by_interference": by_interference,
        "by_category": by_category,
    }


def pair_label(row: dict[str, Any]) -> str:
    return str(row.get("interference") or row["stage"])


def summarize_pairs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    drops = [float(row["score_drop"]) for row in rows]
    changed = [row for row in rows if bool(row["content_changed"])]
    changed_drops = [float(row["score_drop"]) for row in changed]
    return {
        "pair_count": len(rows),
        "changed_pair_count": len(changed),
        "score_decrease_rate": ratio_above_zero(drops),
        "score_tie_rate": sum(abs(value) <= TOLERANCE for value in drops) / len(drops),
        "mean_original_minus_variant": mean(drops),
        "median_original_minus_variant": median(drops),
        "changed_only_score_decrease_rate": ratio_above_zero(changed_drops),
        "changed_only_mean_original_minus_variant": (
            mean(changed_drops) if changed_drops else None
        ),
    }


def ratio_above_zero(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(value > TOLERANCE for value in values) / len(values)


def print_report(summary: dict[str, Any]) -> None:
    overall = summary["overall"]
    print(
        f"{summary['dataset']}: {summary['group_count']} groups, "
        f"{overall['changed_pair_count']} changed pairs, "
        f"decrease={overall['changed_only_score_decrease_rate']:.4f}, "
        f"mean_drop={overall['changed_only_mean_original_minus_variant']:.6f}",
        flush=True,
    )
    for label, metrics in summary["by_interference"].items():
        if not metrics["changed_pair_count"]:
            continue
        print(
            f"  {label}: n={metrics['changed_pair_count']}, "
            f"decrease={metrics['changed_only_score_decrease_rate']:.4f}, "
            f"mean_drop={metrics['changed_only_mean_original_minus_variant']:.6f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
