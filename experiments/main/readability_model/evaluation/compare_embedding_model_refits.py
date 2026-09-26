"""Compare the fixed readability representation across embedding models.

The feature names, Ridge pipeline, training datasets, folds, and evaluation
protocols are held fixed.  Only the embedding-model instantiation changes.
This is a diagnostic refit experiment and never overwrites the frozen model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from experiments.main.readability_model.evaluation.cross_validate_fixed import fold_assignments
from experiments.main.readability_model.evaluation.metrics import unweighted_spearman_average
from experiments.main.readability_model.evaluation.evaluate_constructed_variants import (
    prediction_rows,
    summarize_paired_variants,
)
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.experiments.statistics import spearman
from src.methods.readability_model.llm_features.types import DEFAULT_CAUSAL_LM
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.runners.supervised_ridge import (
    SELECTED_FEATURES,
    fit_ridge,
    load_combined_features,
    load_selected_features,
)


CORE_DATASETS = (
    "mbjp",
    "buse",
    "dorn",
    "scalabrino",
    "schnappinger",
    "jetbrains",
)
CONSTRUCTED_DATASETS = (
    "java_comparative_obfuscation",
    "python_comparative_degradation",
)
EMBEDDING_MODELS = (
    "nomic-ai/nomic-embed-text-v1.5",
    "Qwen/Qwen3-Embedding-0.6B",
    "jinaai/jina-embeddings-v2-base-code",
    "Snowflake/snowflake-arctic-embed-m-v2.0",
    "voyageai/voyage-4-nano",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refit a fixed readability feature schema separately for each embedding "
            "model and compare pooled CV, LODO, and constructed-set responses."
        )
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument(
        "--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT
    )
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--llm-model", default=DEFAULT_CAUSAL_LM)
    parser.add_argument(
        "--selected-features-metadata",
        type=Path,
        help=(
            "JSON file containing selected_features. When omitted, evaluate "
            "the frozen embedding-only 18-feature schema."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(
            "results/experiments/cognascore/embedding_model_refit_comparison"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.folds < 2:
        raise SystemExit("--folds must be at least 2")
    selected_features = (
        load_selected_features(args.selected_features_metadata)
        if args.selected_features_metadata
        else list(SELECTED_FEATURES)
    )

    results: dict[str, Any] = {}
    for embedding_model in EMBEDDING_MODELS:
        print(f"Evaluating {embedding_model}", flush=True)
        core_frames = {
            dataset: load_model_frame(
                dataset,
                embedding_model,
                args.base_root,
                args.embedding_root,
                args.llm_root,
                args.llm_model,
                selected_features,
            )
            for dataset in CORE_DATASETS
        }
        pooled = pd.concat(core_frames.values(), ignore_index=True)
        fit_mask = np.ones(len(pooled), dtype=bool)
        final_model = fit_ridge(
            pooled,
            fit_mask,
            args.ridge_alpha,
            selected_features,
        )
        results[embedding_model] = {
            "standardized_coefficients": {
                feature: float(coefficient)
                for feature, coefficient in zip(
                    selected_features,
                    final_model.named_steps["ridge"].coef_,
                    strict=True,
                )
            },
            "full_fit": evaluate_model(
                final_model,
                core_frames,
                selected_features,
            ),
            "pooled_cross_validation": pooled_cross_validation(
                core_frames,
                folds=args.folds,
                seed=args.seed,
                ridge_alpha=args.ridge_alpha,
                selected_features=selected_features,
            ),
            "leave_one_dataset_out": leave_one_dataset_out(
                core_frames,
                ridge_alpha=args.ridge_alpha,
                selected_features=selected_features,
            ),
            "constructed": evaluate_constructed(
                final_model,
                embedding_model,
                args.base_root,
                args.embedding_root,
                args.llm_root,
                args.llm_model,
                selected_features,
            ),
        }

    payload = {
        "protocol": (
            f"Fixed {len(selected_features)}-feature readability representation; "
            "each embedding model "
            "is refitted independently with the same dataset-balanced bounded "
            "Ridge(alpha=200), target transformation, folds, and datasets."
        ),
        "embedding_models": list(EMBEDDING_MODELS),
        "core_datasets": list(CORE_DATASETS),
        "constructed_datasets": list(CONSTRUCTED_DATASETS),
        "selected_features": selected_features,
        "selected_features_metadata": (
            str(args.selected_features_metadata)
            if args.selected_features_metadata
            else None
        ),
        "llm_model": (
            args.llm_model
            if any(feature.startswith("llm__") for feature in selected_features)
            else None
        ),
        "folds": args.folds,
        "seed": args.seed,
        "ridge_alpha": args.ridge_alpha,
        "dataset_average": (
            "Unweighted arithmetic mean of the six dataset-specific Spearman "
            "correlations; each dataset contributes equally."
        ),
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / "summary.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print_summary(results)
    print(f"Wrote {path}", flush=True)


def load_model_frame(
    dataset: str,
    embedding_model: str,
    base_root: Path,
    embedding_root: Path,
    llm_root: Path,
    llm_model: str,
    selected_features: list[str],
) -> pd.DataFrame:
    return load_combined_features(
        dataset,
        base_root,
        embedding_root,
        selected_features,
        llm_feature_root=llm_root,
        embedding_model=embedding_model,
        llm_model=llm_model,
    )


def evaluate_model(
    model: Any,
    frames: dict[str, pd.DataFrame],
    selected_features: list[str],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for dataset, frame in frames.items():
        prediction = model.predict(frame[selected_features].to_numpy(float))
        value = spearman(
            prediction.tolist(), frame["readability_score"].astype(float).tolist()
        )
        metrics[dataset] = {"n": len(frame), "spearman": value}
    metrics["unweighted_average"] = unweighted_spearman_average(
        metrics, CORE_DATASETS, value_key="spearman"
    )
    return metrics


def pooled_cross_validation(
    frames: dict[str, pd.DataFrame],
    *,
    folds: int,
    seed: int,
    ridge_alpha: float,
    selected_features: list[str],
) -> dict[str, Any]:
    prepared = []
    for dataset_index, (dataset, frame) in enumerate(frames.items()):
        current = frame.copy()
        current["_cv_fold"] = fold_assignments(
            current,
            folds,
            seed + dataset_index,
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
            selected_features,
        )
        predictions[test_mask] = model.predict(
            pooled.loc[test_mask, selected_features].to_numpy(float)
        )
    if not np.isfinite(predictions).all():
        raise ValueError("Pooled cross-validation produced missing predictions")
    pooled["prediction"] = predictions
    return correlation_metrics(pooled)


def leave_one_dataset_out(
    frames: dict[str, pd.DataFrame],
    *,
    ridge_alpha: float,
    selected_features: list[str],
) -> dict[str, Any]:
    predictions = []
    for held_out, test in frames.items():
        train = pd.concat(
            [frame for dataset, frame in frames.items() if dataset != held_out],
            ignore_index=True,
        )
        model = fit_ridge(
            train,
            np.ones(len(train), dtype=bool),
            ridge_alpha,
            selected_features,
        )
        current = test[["dataset", "task_id", "readability_score"]].copy()
        current["prediction"] = model.predict(
            test[selected_features].to_numpy(float)
        )
        predictions.append(current)
    return correlation_metrics(pd.concat(predictions, ignore_index=True))


def correlation_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for dataset, group in frame.groupby("dataset", sort=False):
        value = spearman(
            group["prediction"].astype(float).tolist(),
            group["readability_score"].astype(float).tolist(),
        )
        metrics[str(dataset)] = {"n": len(group), "spearman": value}
    metrics["unweighted_average"] = unweighted_spearman_average(
        metrics, CORE_DATASETS, value_key="spearman"
    )
    return metrics


def evaluate_constructed(
    model: Any,
    embedding_model: str,
    base_root: Path,
    embedding_root: Path,
    llm_root: Path,
    llm_model: str,
    selected_features: list[str],
) -> dict[str, Any]:
    results = {}
    for dataset in CONSTRUCTED_DATASETS:
        frame = load_model_frame(
            dataset,
            embedding_model,
            base_root,
            embedding_root,
            llm_root,
            llm_model,
            selected_features,
        )
        items = load_code_dataset(DATASETS[dataset].path)
        item_by_id = {item.task_id: item for item in items}
        prediction = model.predict(frame[selected_features].to_numpy(float))
        rows = prediction_rows(frame, prediction, item_by_id)
        results[dataset] = summarize_paired_variants(rows)
    return results


def print_summary(results: dict[str, Any]) -> None:
    print("\nmodel\tpooled_cv\tlodo\tjava_changed\tpython_changed")
    for model, result in results.items():
        java = result["constructed"]["java_comparative_obfuscation"]["overall"]
        python = result["constructed"]["python_comparative_degradation"]["overall"]
        print(
            f"{model}\t"
            f"{result['pooled_cross_validation']['unweighted_average']:.6f}\t"
            f"{result['leave_one_dataset_out']['unweighted_average']:.6f}\t"
            f"{java['changed_only_score_decrease_rate']:.6f}\t"
            f"{python['changed_only_score_decrease_rate']:.6f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
