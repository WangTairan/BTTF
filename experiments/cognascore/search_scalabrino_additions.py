"""Search existing Scalabrino-inspired features to add to a frozen candidate list.

This is explicitly a development-set search: both the Scalabrino correlation and
the progressive-obfuscation pooled correlation participate in choosing the
three-feature addition.  It must not be reported as external validation.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.experiments.statistics import spearman
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from src.methods.cognascore.runners.supervised_ridge import (
    TRAIN_DATASETS,
    fit_ridge,
    load_combined_features,
    training_middle_keep_mask,
)


DEFAULT_BASE = Path(
    "experiments/cognascore/configs/consensus28_progressive_protected_development.json"
)
DEFAULT_OUTPUT = Path(
    "results/experiments/cognascore/scalabrino_existing_feature_additions"
)
PROGRESSIVE_DATASET = "java_progressive_obfuscation"
PREFIX = "base__scalabrino_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--add-count", type=int, default=3)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--feature-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-feature-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.base_config.read_text(encoding="utf-8"))
    base_features = [str(value) for value in config["selected_features"]]

    schema = pd.read_csv(
        args.feature_root
        / "scalabrino"
        / "nomic-ai-nomic-embed-text-v1.5"
        / "features.csv",
        nrows=1,
    )
    candidates = sorted(
        f"base__{column}"
        for column in schema.columns
        if column.startswith("scalabrino_") and f"base__{column}" not in base_features
    )
    all_features = base_features + candidates
    frames = {
        dataset: load_combined_features(
            dataset, args.feature_root, args.embedding_feature_root, all_features
        )
        for dataset in (*TRAIN_DATASETS, PROGRESSIVE_DATASET)
    }
    train = pd.concat([frames[name] for name in TRAIN_DATASETS], ignore_index=True)
    fit_mask = training_middle_keep_mask(train, 0.0)

    def evaluate(additions: tuple[str, ...]) -> dict[str, object]:
        selected = base_features + list(additions)
        model = fit_ridge(train, fit_mask, args.ridge_alpha, selected)
        scalabrino_frame = frames["scalabrino"]
        progressive_frame = frames[PROGRESSIVE_DATASET]
        scalabrino_prediction = model.predict(
            scalabrino_frame[selected].to_numpy(dtype=float)
        )
        progressive_prediction = model.predict(
            progressive_frame[selected].to_numpy(dtype=float)
        )
        return {
            "added_features": ";".join(additions),
            "scalabrino_spearman": spearman(
                scalabrino_prediction.tolist(),
                scalabrino_frame["readability_score"].astype(float).tolist(),
            ),
            "progressive_pooled_spearman": spearman(
                progressive_prediction.tolist(),
                progressive_frame["readability_score"].astype(float).tolist(),
            ),
        }

    baseline = evaluate(())
    rows = [evaluate(combo) for combo in itertools.combinations(candidates, args.add_count)]
    for row in rows:
        row["delta_scalabrino"] = float(row["scalabrino_spearman"]) - float(
            baseline["scalabrino_spearman"]
        )
        row["delta_progressive"] = float(row["progressive_pooled_spearman"]) - float(
            baseline["progressive_pooled_spearman"]
        )
        row["balanced_gain"] = min(
            float(row["delta_scalabrino"]), float(row["delta_progressive"])
        )
        row["sum_gain"] = float(row["delta_scalabrino"]) + float(row["delta_progressive"])
    rows.sort(
        key=lambda row: (
            float(row["balanced_gain"]),
            float(row["sum_gain"]),
            str(row["added_features"]),
        ),
        reverse=True,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "three_feature_combinations.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "status": "development_search_not_external_validation",
        "base_config": str(args.base_config),
        "base_feature_count": len(base_features),
        "candidate_features": candidates,
        "combination_count": len(rows),
        "selection_rule": (
            "maximize the smaller of the absolute Scalabrino and progressive pooled "
            "Spearman improvements; break ties by their summed improvement"
        ),
        "baseline": baseline,
        "best": rows[0],
        "top_10": rows[:10],
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
