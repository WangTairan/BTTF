"""Ablate feature families from the final representation.

The selected 11-feature schema is fixed before this experiment.  The ablated
configurations remove the traditional, embedding-derived, or causal-LM family
without reselection and refit the same Ridge pipeline on the remaining
features.  Every configuration is evaluated on the six human-rated datasets
and the two controlled-interference datasets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from experiments.main.readability_model.evaluation.compare_embedding_model_refits import (
    CONSTRUCTED_DATASETS,
    CORE_DATASETS,
    evaluate_constructed,
    leave_one_dataset_out,
    load_model_frame,
    pooled_cross_validation,
)
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.runners.supervised_ridge import (
    fit_ridge,
    load_selected_features,
)


DEFAULT_OUTPUT = Path(
    "results/experiments/readability_model/consensus11_family_ablation"
)

FEATURE_FAMILIES = {
    "traditional": "base__",
    "embedding": "embedding__",
    "causal_lm": "llm__",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-features-metadata", type=Path, required=True)
    parser.add_argument(
        "--embedding-model",
        default="jinaai/jina-embeddings-v2-base-code",
    )
    parser.add_argument(
        "--llm-model",
        default="infly/OpenCoder-1.5B-Base",
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def evaluate_configuration(
    args: argparse.Namespace,
    selected_features: list[str],
) -> dict[str, Any]:
    frames = {
        dataset: load_model_frame(
            dataset,
            args.embedding_model,
            args.base_root,
            args.embedding_root,
            args.llm_root,
            args.llm_model,
            selected_features,
        )
        for dataset in CORE_DATASETS
    }
    complete = pd.concat(frames.values(), ignore_index=True)
    model = fit_ridge(
        complete,
        np.ones(len(complete), dtype=bool),
        args.ridge_alpha,
        selected_features,
    )
    return {
        "features": selected_features,
        "feature_count": len(selected_features),
        "pooled_cross_validation": pooled_cross_validation(
            frames,
            folds=args.folds,
            seed=args.seed,
            ridge_alpha=args.ridge_alpha,
            selected_features=selected_features,
        ),
        "leave_one_dataset_out": leave_one_dataset_out(
            frames,
            ridge_alpha=args.ridge_alpha,
            selected_features=selected_features,
        ),
        "constructed": evaluate_constructed(
            model,
            args.embedding_model,
            args.base_root,
            args.embedding_root,
            args.llm_root,
            args.llm_model,
            selected_features,
        ),
    }


def main() -> None:
    args = parse_args()
    full_features = load_selected_features(args.selected_features_metadata)
    family_features = {
        family: [
            feature for feature in full_features if feature.startswith(prefix)
        ]
        for family, prefix in FEATURE_FAMILIES.items()
    }
    assigned = {
        feature for features in family_features.values() for feature in features
    }
    if assigned != set(full_features):
        raise SystemExit(
            "Feature families do not partition the selected schema: "
            f"unassigned={sorted(set(full_features) - assigned)}"
        )
    if any(not features for features in family_features.values()):
        raise SystemExit(f"Empty feature family: {family_features}")

    configurations = {"complete": full_features}
    for family, removed in family_features.items():
        configurations[f"without_{family}"] = [
            feature for feature in full_features if feature not in set(removed)
        ]
    results = {
        name: evaluate_configuration(args, features)
        for name, features in configurations.items()
    }
    payload = {
        "experiment": "Final-model feature-family ablation",
        "protocol": (
            "Remove one feature family from the fixed final schema without "
            "reselection, then refit the same dataset-balanced bounded Ridge."
        ),
        "selected_features_metadata": str(args.selected_features_metadata),
        "embedding_model": args.embedding_model,
        "llm_model": args.llm_model,
        "folds": args.folds,
        "seed": args.seed,
        "ridge_alpha": args.ridge_alpha,
        "core_datasets": list(CORE_DATASETS),
        "constructed_datasets": list(CONSTRUCTED_DATASETS),
        "feature_families": family_features,
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / "summary.json"
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print("configuration\tfeatures\tpooled\tlodo\tjava\tpython")
    for name, result in results.items():
        java = result["constructed"]["java_comparative_obfuscation"]["overall"]
        python = result["constructed"]["python_comparative_degradation"]["overall"]
        print(
            f"{name}\t{result['feature_count']}\t"
            f"{result['pooled_cross_validation']['unweighted_average']:.6f}\t"
            f"{result['leave_one_dataset_out']['unweighted_average']:.6f}\t"
            f"{java['changed_only_score_decrease_rate']:.6f}\t"
            f"{python['changed_only_score_decrease_rate']:.6f}"
        )
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
