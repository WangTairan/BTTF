"""Measure paired candidate-feature responses to one constructed interference."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.runners.supervised_ridge import load_combined_features


DEFAULT_DATASET = "java_comparative_obfuscation"
DEFAULT_DATASET_PATH = Path(
    "datasets/constructed/java-comparative-obfuscation-class-100"
)
REFERENCE_DATASETS = (
    "mbjp",
    "buse",
    "dorn",
    "scalabrino",
    "schnappinger",
    "jetbrains",
)
DEFAULT_MODEL_MANIFEST = Path(
    "frozen_models/cognascore/consensus18_6dataset_sampled_margin_nomic/"
    "nomic-ai-nomic-embed-text-v1.5/model.json"
)
DEFAULT_RANKING = Path(
    "results/experiments/cognascore/current_6dataset_l1_ranking/"
    "cognascore_feature_screen_consensus/five_model/consensus_ranking.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare every candidate feature between original classes and one "
            "independently transformed variant."
        )
    )
    parser.add_argument("--interference", required=True)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument(
        "--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT
    )
    parser.add_argument("--model-manifest", type=Path, default=DEFAULT_MODEL_MANIFEST)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(
            "results/experiments/cognascore/constructed_candidate_feature_impacts"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_rows = [
        json.loads(line)
        for line in (args.dataset_path / "manifest.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    originals = {
        str(row["group_id"]): row
        for row in manifest_rows
        if row.get("interference") is None
    }
    variants = [
        row
        for row in manifest_rows
        if str(row.get("interference") or "") == args.interference
    ]
    if not variants:
        raise ValueError(f"No manifest variants for interference {args.interference!r}")
    if len(variants) != len(originals):
        raise ValueError(
            f"Expected one {args.interference!r} variant per original: "
            f"originals={len(originals)}, variants={len(variants)}"
        )

    target = load_combined_features(
        args.dataset,
        args.feature_root,
        args.embedding_feature_root,
        [],
    ).set_index("task_id")
    if not target.index.is_unique:
        raise ValueError(f"Duplicate task_id values in feature table for {args.dataset}")
    feature_names = sorted(
        column
        for column in target.columns
        if column not in {"dataset", "readability_score"}
        and pd.api.types.is_numeric_dtype(target[column])
    )
    reference = pd.concat(
        [
            load_combined_features(
                dataset,
                args.feature_root,
                args.embedding_feature_root,
                [],
            )
            for dataset in REFERENCE_DATASETS
        ],
        ignore_index=True,
    )
    reference_std = reference[feature_names].std(axis=0, ddof=0)

    selected = set(
        json.loads(args.model_manifest.read_text(encoding="utf-8"))["features"][
            "ordered_names"
        ]
    )
    ranks: dict[str, int] = {}
    if args.ranking.is_file():
        ranking = pd.read_csv(args.ranking)
        ranks = {
            str(row.feature): int(row.rank)
            for row in ranking.itertuples(index=False)
        }

    rows: list[dict[str, object]] = []
    for feature in feature_names:
        deltas = []
        for variant in variants:
            original = originals[str(variant["group_id"])]
            original_value = float(target.at[str(original["variant_id"]), feature])
            variant_value = float(target.at[str(variant["variant_id"]), feature])
            if not np.isfinite(original_value) or not np.isfinite(variant_value):
                raise ValueError(
                    f"Non-finite paired value for {feature}: "
                    f"{original['variant_id']} -> {variant['variant_id']}"
                )
            deltas.append(variant_value - original_value)

        values = np.asarray(deltas, dtype=float)
        tolerance = 1e-12
        increase_rate = float(np.mean(values > tolerance))
        decrease_rate = float(np.mean(values < -tolerance))
        tie_rate = float(np.mean(np.abs(values) <= tolerance))
        dominant_rate = max(increase_rate, decrease_rate)
        direction = (
            "increase"
            if increase_rate > decrease_rate
            else "decrease"
            if decrease_rate > increase_rate
            else "mixed_or_tied"
        )
        scale = float(reference_std[feature])
        standardized_shift = (
            float(np.mean(values) / scale) if scale > tolerance else 0.0
        )
        impact_score = abs(standardized_shift) * dominant_rate
        rows.append(
            {
                "feature": feature,
                "family": feature.split("__", 1)[0],
                "pair_count": len(values),
                "nonzero_rate": 1.0 - tie_rate,
                "increase_rate": increase_rate,
                "decrease_rate": decrease_rate,
                "tie_rate": tie_rate,
                "dominant_direction": direction,
                "direction_consistency": dominant_rate,
                "mean_variant_minus_original": float(np.mean(values)),
                "median_variant_minus_original": float(np.median(values)),
                "reference_std_six_datasets": scale,
                "standardized_mean_shift": standardized_shift,
                "impact_score": impact_score,
                "readability_coefficient_direction": (
                    "negative"
                    if direction == "increase"
                    else "positive"
                    if direction == "decrease"
                    else "undetermined"
                ),
                "selected_in_frozen18": feature in selected,
                "consensus_rank": ranks.get(feature),
            }
        )

    result = pd.DataFrame(rows).sort_values(
        by=["impact_score", "direction_consistency", "feature"],
        ascending=[False, False, True],
    )
    result.insert(0, "impact_rank", np.arange(1, len(result) + 1))
    output_dir = args.output / args.interference
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "feature_impacts.csv"
    result.to_csv(table_path, index=False)

    summary = {
        "dataset": args.dataset,
        "dataset_path": str(args.dataset_path),
        "interference": args.interference,
        "pair_count": len(variants),
        "candidate_feature_count": len(result),
        "reference_datasets_for_standardization": list(REFERENCE_DATASETS),
        "impact_score": (
            "abs(mean(variant-original) / pooled six-dataset feature std) * "
            "max(increase_rate, decrease_rate)"
        ),
        "table": str(table_path),
        "top_features": [
            {
                key: (
                    None
                    if isinstance(value, float) and not math.isfinite(value)
                    else value
                )
                for key, value in row.items()
            }
            for row in result.head(20).to_dict(orient="records")
        ],
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(result.head(30).to_string(index=False), flush=True)
    print(f"Wrote {table_path}", flush=True)
    print(f"Wrote {summary_path}", flush=True)


if __name__ == "__main__":
    main()
