"""Evaluate the fixed final feature schema across causal language models.

The embedding representation, selected feature definitions, Ridge pipeline,
datasets, and fold assignments are fixed.  Only the causal-LM feature table is
changed.  Predictions are retained so that uncertainty analyses can reuse the
exact evaluated outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from experiments.main.readability_model.evaluation.compare_embedding_model_refits import (
    CORE_DATASETS,
    correlation_metrics,
)
from experiments.main.readability_model.evaluation.cross_validate_fixed import (
    fold_assignments,
)
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.results import model_slug
from src.methods.readability_model.runners.supervised_ridge import (
    fit_ridge,
    load_combined_features,
    load_selected_features,
)


CAUSAL_LMS = (
    "Qwen/Qwen2.5-Coder-0.5B",
    "deepseek-ai/deepseek-coder-1.3b-base",
    "infly/OpenCoder-1.5B-Base",
)

EXPECTED_SIGNS = {
    "base__operator_density": -1,
    "llm__literal_tail_surprisal": -1,
    "embedding__computation_control_pattern_count": -1,
    "llm__identifier_onset_surprisal": -1,
    "base__decision_density": -1,
    "base__expression_literal_density": -1,
    "llm__assignment_value_surprisal": -1,
    "base__longest_line_length": -1,
    "llm__declaration_surprisal_variation": -1,
    "llm__short_identifier_context_dependence": -1,
    "embedding__only_identifier__embedding_dispersion": -1,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--selected-features-metadata",
        type=Path,
        required=True,
        help="Frozen configuration containing selected_features.",
    )
    parser.add_argument(
        "--embedding-model",
        default="jinaai/jina-embeddings-v2-base-code",
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(
            "results/experiments/readability_model/consensus11_model_grid/"
            "jina_causal_refits"
        ),
    )
    return parser.parse_args()


def load_frames(args: argparse.Namespace, causal_lm: str, features: list[str]):
    return {
        dataset: load_combined_features(
            dataset,
            args.base_root,
            args.embedding_root,
            features,
            llm_feature_root=args.llm_root,
            embedding_model=args.embedding_model,
            llm_model=causal_lm,
        )
        for dataset in CORE_DATASETS
    }


def pooled_predictions(
    frames: dict[str, pd.DataFrame],
    *,
    folds: int,
    seed: int,
    ridge_alpha: float,
    features: list[str],
) -> pd.DataFrame:
    prepared = []
    for dataset_index, (dataset, frame) in enumerate(frames.items()):
        current = frame.copy()
        current["_cv_fold"] = fold_assignments(
            current, folds, seed + dataset_index
        )
        prepared.append(current)
    pooled = pd.concat(prepared, ignore_index=True)
    predictions = np.full(len(pooled), np.nan)
    for fold in range(folds):
        test_mask = pooled["_cv_fold"].to_numpy(int) == fold
        train = pooled.loc[~test_mask].reset_index(drop=True)
        model = fit_ridge(
            train,
            np.ones(len(train), dtype=bool),
            ridge_alpha,
            features,
        )
        predictions[test_mask] = model.predict(
            pooled.loc[test_mask, features].to_numpy(float)
        )
    if not np.isfinite(predictions).all():
        raise ValueError("Pooled cross-validation produced missing predictions")
    output = pooled[["dataset", "task_id", "readability_score", "_cv_fold"]].copy()
    output["prediction"] = predictions
    return output


def lodo_predictions(
    frames: dict[str, pd.DataFrame],
    *,
    ridge_alpha: float,
    features: list[str],
) -> pd.DataFrame:
    rows = []
    for held_out, test in frames.items():
        train = pd.concat(
            [frame for dataset, frame in frames.items() if dataset != held_out],
            ignore_index=True,
        )
        model = fit_ridge(
            train,
            np.ones(len(train), dtype=bool),
            ridge_alpha,
            features,
        )
        current = test[["dataset", "task_id", "readability_score"]].copy()
        current["prediction"] = model.predict(test[features].to_numpy(float))
        rows.append(current)
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    args = parse_args()
    features = load_selected_features(args.selected_features_metadata)
    if set(features) != set(EXPECTED_SIGNS):
        raise ValueError(
            "The selected feature schema does not match the prespecified "
            "11-feature sign audit."
        )
    results: dict[str, Any] = {}
    args.output.mkdir(parents=True, exist_ok=True)
    for causal_lm in CAUSAL_LMS:
        print(f"Evaluating {causal_lm}", flush=True)
        frames = load_frames(args, causal_lm, features)
        complete = pd.concat(frames.values(), ignore_index=True)
        model = fit_ridge(
            complete,
            np.ones(len(complete), dtype=bool),
            args.ridge_alpha,
            features,
        )
        coefficients = {
            feature: float(value)
            for feature, value in zip(
                features, model.named_steps["ridge"].coef_, strict=True
            )
        }
        sign_agreement = sum(
            int(np.sign(coefficients[feature]) == expected)
            for feature, expected in EXPECTED_SIGNS.items()
        )
        pooled = pooled_predictions(
            frames,
            folds=args.folds,
            seed=args.seed,
            ridge_alpha=args.ridge_alpha,
            features=features,
        )
        lodo = lodo_predictions(
            frames,
            ridge_alpha=args.ridge_alpha,
            features=features,
        )
        destination = args.output / model_slug(causal_lm)
        destination.mkdir(parents=True, exist_ok=True)
        pooled.to_csv(destination / "pooled_predictions.csv", index=False)
        lodo.to_csv(destination / "lodo_predictions.csv", index=False)
        results[causal_lm] = {
            "pooled_cross_validation": correlation_metrics(pooled),
            "leave_one_dataset_out": correlation_metrics(lodo),
            "standardized_coefficients": coefficients,
            "expected_sign_agreement": sign_agreement,
            "expected_sign_total": len(EXPECTED_SIGNS),
        }

    payload = {
        "protocol": (
            "Fixed Qwen3 embedding instantiation and fixed 11-feature schema; "
            "only the causal-LM feature table changes. Each model is refitted "
            "with the same dataset-balanced bounded Ridge, folds, and datasets."
        ),
        "causal_lms": list(CAUSAL_LMS),
        "embedding_model": args.embedding_model,
        "selected_features": features,
        "selected_features_metadata": str(args.selected_features_metadata),
        "folds": args.folds,
        "seed": args.seed,
        "ridge_alpha": args.ridge_alpha,
        "dataset_average": (
            "Unweighted arithmetic mean of the six dataset-specific Spearman "
            "correlations."
        ),
        "results": results,
    }
    (args.output / "summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("\ncausal_lm\tpooled\tlodo\tsign_agreement")
    for causal_lm, result in results.items():
        print(
            f"{causal_lm}\t"
            f"{result['pooled_cross_validation']['unweighted_average']:.6f}\t"
            f"{result['leave_one_dataset_out']['unweighted_average']:.6f}\t"
            f"{result['expected_sign_agreement']}/{result['expected_sign_total']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
