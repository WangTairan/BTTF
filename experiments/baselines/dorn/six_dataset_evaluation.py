"""Evaluate fixed Dorn features with pooled CV, LODO, and a full six-set fit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from experiments.main.readability_model.evaluation.cross_validate_fixed import fold_assignments
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.experiments.statistics import spearman
from src.methods.readability_model.runners.supervised_ridge import (
    dataset_balanced_sample_weight,
    regression_target,
)
from src.methods.dorn.extractor import extract_dorn_features
from src.methods.dorn.method import DEFAULT_MODEL_PATH, load_model, metric_value


DATASET_KEYS = ("mbjp", "buse", "dorn", "scalabrino", "schnappinger", "jetbrains")
DEFAULT_CACHE = Path("artifacts/baselines/dorn/six_dataset_features")
DEFAULT_OUTPUT = Path("results/experiments/dorn_retrained/six_dataset")
DORN_EXTRACTOR_VERSION = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize the frozen seven Dorn features, then report pooled "
            "10-fold, leave-one-dataset-out, and full-fit results."
        )
    )
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--refresh-features",
        action="store_true",
        help="Recompute cached Dorn features even when code hashes match.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.folds < 2:
        raise SystemExit("--folds must be at least 2")
    model_metadata = load_model(args.model)
    features = list(model_metadata["selected_features"])
    frames = {
        key: materialize_dataset(
            key,
            features,
            args.cache,
            refresh=args.refresh_features,
        )
        for key in DATASET_KEYS
    }
    pooled = pd.concat(frames.values(), ignore_index=True)
    args.output.mkdir(parents=True, exist_ok=True)

    pooled_payload, pooled_rows = pooled_cross_validation(
        frames,
        features,
        folds=args.folds,
        seed=args.seed,
        ridge_alpha=args.ridge_alpha,
    )
    lodo_payload, lodo_rows = leave_one_dataset_out(
        frames,
        features,
        ridge_alpha=args.ridge_alpha,
    )
    full_payload, full_rows = full_fit(
        pooled,
        features,
        ridge_alpha=args.ridge_alpha,
    )

    common = {
        "feature_model": "Dorn (retrained) fixed seven-feature representation",
        "selected_features": features,
        "feature_selection_inside_evaluation": False,
        "target": "within-dataset rank percentile of the continuous human score",
        "training_weighting": "inverse dataset size",
        "ridge_alpha": args.ridge_alpha,
        "datasets": list(DATASET_KEYS),
    }
    write_protocol(args.output, "pooled_10fold", common | pooled_payload, pooled_rows)
    write_protocol(args.output, "lodo", common | lodo_payload, lodo_rows)
    write_protocol(args.output, "full_fit", common | full_payload, full_rows)

    combined = {
        "pooled_10fold": pooled_payload["metrics"],
        "lodo": lodo_payload["metrics"],
        "full_fit_training_pool": full_payload["metrics"],
        "warning": (
            "full_fit_training_pool is descriptive in-sample performance and is not "
            "a validation estimate"
        ),
    }
    combined_path = args.output / "summary.json"
    combined_path.write_text(
        json.dumps(combined, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(combined, indent=2, ensure_ascii=False), flush=True)
    print(f"wrote: {combined_path}", flush=True)


def materialize_dataset(
    dataset: str,
    features: list[str],
    cache_root: Path,
    *,
    refresh: bool,
) -> pd.DataFrame:
    items = load_code_dataset(DATASETS[dataset].path)
    dataset_cache = cache_root / dataset
    dataset_cache.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for index, item in enumerate(items, start=1):
        digest = hashlib.sha256(item.content.encode("utf-8")).hexdigest()
        cache_path = dataset_cache / f"{safe_name(item.task_id)}.json"
        row = None
        if not refresh and cache_path.is_file():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                cached.get("content_sha256") == digest
                and cached.get("dorn_extractor_version") == DORN_EXTRACTOR_VERSION
            ):
                row = cached
        if row is None:
            print(
                f"[{dataset} {index}/{len(items)}] Extracting Dorn features for {item.task_id}",
                flush=True,
            )
            language = str(item.metadata.get("language", "java"))
            metrics = extract_dorn_features(item.content, language)
            row = {
                "dataset": dataset,
                "task_id": item.task_id,
                "readability_score": float(item.readability_score),
                "content_sha256": digest,
                "dorn_extractor_version": DORN_EXTRACTOR_VERSION,
                **{
                    feature: finite_or_none(metric_value(metrics, feature))
                    for feature in features
                },
            }
            cache_path.write_text(
                json.dumps(row, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        rows.append(row)
    frame = pd.DataFrame(rows)
    missing = [feature for feature in features if feature not in frame]
    if missing:
        raise ValueError(f"Missing Dorn features for {dataset}: {missing}")
    return frame


def pooled_cross_validation(
    frames: dict[str, pd.DataFrame],
    features: list[str],
    *,
    folds: int,
    seed: int,
    ridge_alpha: float,
) -> tuple[dict, pd.DataFrame]:
    assigned = []
    for dataset_index, (dataset, source) in enumerate(frames.items()):
        frame = source.copy()
        frame["fold"] = fold_assignments(frame, folds, seed + dataset_index)
        assigned.append(frame)
    pooled = pd.concat(assigned, ignore_index=True)
    prediction = np.full(len(pooled), np.nan, dtype=float)
    for fold in range(folds):
        test_mask = pooled["fold"].to_numpy(dtype=int) == fold
        train = pooled.loc[~test_mask].reset_index(drop=True)
        test = pooled.loc[test_mask]
        fitted = fit_ridge(train, features, ridge_alpha)
        prediction[test.index] = fitted.predict(test[features].to_numpy(dtype=float))
    if not np.isfinite(prediction).all():
        raise RuntimeError("Pooled cross-validation left non-finite predictions")
    pooled["prediction"] = prediction
    return {
        "protocol": f"pooled {folds}-fold out-of-fold evaluation",
        "folds": folds,
        "seed": seed,
        "metrics": metrics_by_dataset(pooled),
    }, pooled


def leave_one_dataset_out(
    frames: dict[str, pd.DataFrame],
    features: list[str],
    *,
    ridge_alpha: float,
) -> tuple[dict, pd.DataFrame]:
    rows = []
    for held_out, test in frames.items():
        train = pd.concat(
            [frame for key, frame in frames.items() if key != held_out],
            ignore_index=True,
        )
        fitted = fit_ridge(train, features, ridge_alpha)
        scored = test.copy()
        scored["prediction"] = fitted.predict(test[features].to_numpy(dtype=float))
        rows.append(scored)
    combined = pd.concat(rows, ignore_index=True)
    return {
        "protocol": "leave one entire readability dataset out",
        "metrics": metrics_by_dataset(combined),
    }, combined


def full_fit(
    pooled: pd.DataFrame,
    features: list[str],
    *,
    ridge_alpha: float,
) -> tuple[dict, pd.DataFrame]:
    fitted = fit_ridge(pooled, features, ridge_alpha)
    scored = pooled.copy()
    scored["prediction"] = fitted.predict(pooled[features].to_numpy(dtype=float))
    return {
        "protocol": "one Ridge fit and evaluated on the complete six-dataset training pool",
        "metrics": metrics_by_dataset(scored),
        "interpretation": "descriptive training-pool fit; not validation",
    }, scored


def fit_ridge(frame: pd.DataFrame, features: list[str], ridge_alpha: float):
    target = regression_target(frame)
    eligible = np.ones(len(frame), dtype=bool)
    weights = dataset_balanced_sample_weight(frame, eligible)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=ridge_alpha),
    )
    model.fit(
        frame[features].to_numpy(dtype=float),
        target,
        ridge__sample_weight=weights,
    )
    return model


def metrics_by_dataset(frame: pd.DataFrame) -> dict[str, dict]:
    metrics: dict[str, dict] = {}
    values = []
    for dataset, group in frame.groupby("dataset", sort=False):
        value = spearman(
            group["prediction"].astype(float).tolist(),
            group["readability_score"].astype(float).tolist(),
        )
        metrics[str(dataset)] = {
            "n": len(group),
            "metric": "spearman",
            "value": value,
        }
        if math.isfinite(value):
            values.append(value)
    metrics["macro"] = {
        "n_datasets": len(values),
        "metric": "mean_spearman",
        "value": mean(values),
    }
    return metrics


def write_protocol(
    output: Path,
    name: str,
    payload: dict,
    rows: pd.DataFrame,
) -> None:
    protocol_dir = output / name
    protocol_dir.mkdir(parents=True, exist_ok=True)
    (protocol_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    columns = ["dataset", "task_id", "readability_score", "prediction"]
    with (protocol_dir / "predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows[columns].to_dict("records"))


def safe_name(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None


if __name__ == "__main__":
    main()
