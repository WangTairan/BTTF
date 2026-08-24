"""Screen existing CognaScore features for progressive pooled-Spearman gain.

The progressive dataset directly controls this development search, so its output
is an optimization diagnostic rather than external validation evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pandas as pd

from src.experiments.statistics import spearman
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.runners.supervised_ridge import (
    TRAIN_DATASETS,
    fit_ridge,
    load_combined_features,
    training_middle_keep_mask,
)


DEFAULT_CONFIG = Path(
    "experiments/cognascore/configs/consensus28_progressive_protected_development.json"
)
DEFAULT_RANKING = Path(
    "results/experiments/cognascore/consensus_k30_fit_5continuous/"
    "cognascore_feature_screen_consensus/five_model/consensus_ranking_current_schema.csv"
)
DEFAULT_OUTPUT = Path(
    "results/experiments/cognascore/progressive_existing_feature_additions"
)
PROGRESSIVE_DATASET = "java_progressive_obfuscation"


def is_cognascore_group(group: str) -> bool:
    return (
        group.startswith("cognascore_")
        or group.startswith("chunk_view_")
        or group in {
            "embedding_geometry",
            "embedding_coverage",
            "semantic_context_gate",
            "code_compression",
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    parser.add_argument("--minimum-gain", type=float, default=0.01)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = [
        str(value)
        for value in json.loads(args.config.read_text(encoding="utf-8"))["selected_features"]
    ]
    with args.ranking.open(newline="", encoding="utf-8") as handle:
        ranking = list(csv.DictReader(handle))
    candidates = [
        row
        for row in ranking
        if row["feature"] not in selected and is_cognascore_group(row["group"])
    ]
    all_features = selected + [row["feature"] for row in candidates]
    frames = {
        dataset: load_combined_features(
            dataset, args.feature_root, args.embedding_feature_root, all_features
        )
        for dataset in (*TRAIN_DATASETS, PROGRESSIVE_DATASET)
    }
    train = pd.concat([frames[name] for name in TRAIN_DATASETS], ignore_index=True)
    fit_mask = training_middle_keep_mask(train, 0.0)

    def evaluate(model, features: list[str], dataset: str) -> float:
        frame = frames[dataset]
        scores = model.predict(frame[features].to_numpy(dtype=float))
        return spearman(scores.tolist(), frame["readability_score"].astype(float).tolist())

    baseline_model = fit_ridge(train, fit_mask, args.ridge_alpha, selected)
    baseline_progressive = evaluate(baseline_model, selected, PROGRESSIVE_DATASET)
    rows = []
    for index, candidate in enumerate(candidates, start=1):
        feature = candidate["feature"]
        features = [*selected, feature]
        model = fit_ridge(train, fit_mask, args.ridge_alpha, features)
        progressive = evaluate(model, features, PROGRESSIVE_DATASET)
        scalabrino = evaluate(model, features, "scalabrino")
        rows.append(
            {
                "consensus_rank": int(candidate["rank"]),
                "feature": feature,
                "group": candidate["group"],
                "active_model_count": int(candidate["active_model_count"]),
                "mean_selection_frequency": float(candidate["mean_selection_frequency"]),
                "progressive_pooled_spearman": progressive,
                "progressive_gain": progressive - baseline_progressive,
                "scalabrino_spearman": scalabrino,
            }
        )
        print(f"screen {index}/{len(candidates)}: rank {candidate['rank']}", flush=True)
    rows.sort(key=lambda row: int(row["consensus_rank"]))
    passing = [row for row in rows if float(row["progressive_gain"]) >= args.minimum_gain]

    args.output.mkdir(parents=True, exist_ok=True)
    for name, values in (("all_candidates.csv", rows), ("passing_candidates.csv", passing)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(values)
    summary = {
        "status": "progressive-supervised development search; not external validation",
        "base_config": str(args.config),
        "base_feature_count": len(selected),
        "baseline_progressive_pooled_spearman": baseline_progressive,
        "candidate_count": len(candidates),
        "minimum_gain": args.minimum_gain,
        "passing_count": len(passing),
        "passing_in_consensus_order": passing,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
