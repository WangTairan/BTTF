from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from src.experiments.paths import result_dir
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL, DATASETS

from src.methods.cognascore.results import model_slug
from src.methods.cognascore.dataset_io import dataset_output_name
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)

from . import feature_selection as fs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sweep top-K selected CognaScore features. The expensive L1/stability ranking "
            "is computed once; Ridge is refit for each K."
        )
    )
    parser.add_argument("datasets", nargs="*", type=Path)
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument(
        "--extra-embedding-model",
        action="append",
        default=[],
        help="Additional embedding feature table to merge. Can be repeated.",
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument(
        "--feature-source",
        choices=(
            "base",
            "embedding",
            "combined",
        ),
        default="combined",
    )
    parser.add_argument("--continuous-threshold", choices=("median", "mean"), default="median")
    parser.add_argument("--drop-middle", type=float, default=0.0)
    parser.add_argument("--drop-middle-scope", choices=("all", "training"), default="all")
    parser.add_argument("--c", type=float, default=0.08)
    parser.add_argument("--cv", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability-rounds", type=int, default=200)
    parser.add_argument("--stability-sample-fraction", type=float, default=0.7)
    parser.add_argument("--selection-dataset", action="append", default=[])
    parser.add_argument("--external-dataset", action="append", default=[])
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--k-min", type=int, default=1)
    parser.add_argument("--k-max", type=int)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT,
        help="Experiment-results root. Defaults to results/experiments/cognascore/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in fs.DEFAULT_DATASET_KEYS]
    dataset_names = [dataset_output_name(path) for path in dataset_paths]
    slug = model_slug(args.embedding_model)

    base_table = (
        _load_base_table(args.base_root, dataset_names, slug)
        if args.feature_source in {"base", "combined"}
        else None
    )
    embedding_tables = []
    if args.feature_source in {"embedding", "combined"}:
        embedding_models = [args.embedding_model, *args.extra_embedding_model]
        multi_embedding = len(embedding_models) > 1
        for model_name in embedding_models:
            model_prefix = "embedding" if not multi_embedding else f"embedding_{_short_model_slug(model_name)}"
            embedding_tables.append(
                fs._load_feature_family(
                    args.embedding_root,
                    dataset_names,
                    model_slug(model_name),
                    prefix=model_prefix,
                )
            )
    merged_rows, groups = fs._merge_tables(base_table, *embedding_tables)
    x, y, sample_weight, feature_names, row_metadata = fs._prepare_matrix(
        merged_rows,
        groups,
        continuous_threshold=args.continuous_threshold,
        drop_middle=args.drop_middle if args.drop_middle_scope == "all" else 0.0,
    )
    selection_datasets = tuple(args.selection_dataset or fs.DEFAULT_SELECTION_DATASETS)
    external_datasets = tuple(args.external_dataset or fs.DEFAULT_EXTERNAL_DATASETS)
    selection_mask = fs._dataset_mask(row_metadata, selection_datasets)
    external_mask = fs._dataset_mask(row_metadata, external_datasets)
    training_middle_keep_mask = (
        fs._middle_keep_mask(row_metadata, args.drop_middle)
        if args.drop_middle_scope == "training"
        else np.ones(len(row_metadata), dtype=bool)
    )
    fit_selection_mask = selection_mask & training_middle_keep_mask
    if int(np.sum(fit_selection_mask)) == 0:
        raise SystemExit("No fitting rows selected.")
    fit_sample_weight = fs._sample_weight_for_rows(row_metadata, fit_selection_mask)

    screening_model = fs._build_model(args.c, args.seed)
    screening_model.fit(
        x[fit_selection_mask],
        y[fit_selection_mask],
        logisticregression__sample_weight=fit_sample_weight[fit_selection_mask],
    )
    coefficients = fs._extract_coefficients(screening_model, feature_names)
    stability = fs._stability_selection(
        x,
        y,
        sample_weight,
        row_metadata,
        feature_names,
        c=args.c,
        rounds=args.stability_rounds,
        seed=args.seed,
        selection_datasets=selection_datasets,
        eligible_mask=training_middle_keep_mask,
        sample_fraction=args.stability_sample_fraction,
    )
    ranking = fs._rank_features(coefficients, stability, groups)

    regression_target = fs._regression_target(row_metadata)
    k_min = max(1, args.k_min)
    k_max = min(args.k_max or len(ranking), len(ranking))
    if k_min > k_max:
        raise SystemExit(f"Invalid K range: {k_min}..{k_max}")

    out_dir = result_dir(args.output, "cognascore_feature_screen_sweep", "logistic_l1_ridge")
    out_dir.mkdir(parents=True, exist_ok=True)
    ranking_path = out_dir / "feature_ranking.csv"
    curve_path = out_dir / "topk_curve.csv"
    metadata_path = out_dir / "metadata.json"
    fs._write_ranking(ranking_path, ranking)

    curve_rows: list[dict[str, Any]] = []
    for k in range(k_min, k_max + 1):
        selected_features = [row["feature"] for row in ranking[:k]]
        selected_indices = np.asarray([feature_names.index(name) for name in selected_features], dtype=int)
        model = fs._build_final_model(
            "ridge",
            c=args.c,
            ridge_alpha=args.ridge_alpha,
            elasticnet_alpha=0.02,
            elasticnet_l1_ratio=0.2,
            seed=args.seed,
        )
        fs._fit_final_model(
            model,
            x[fit_selection_mask][:, selected_indices],
            regression_target[fit_selection_mask],
            fit_sample_weight[fit_selection_mask],
            "ridge",
        )
        prediction = fs._predict_final_model(model, x[:, selected_indices], "ridge")
        all_metrics = fs._report_metrics_by_dataset(row_metadata, prediction)
        selection_metrics = fs._report_metrics_by_dataset(
            fs._subset_rows(row_metadata, selection_mask),
            prediction[selection_mask],
        )
        external_metrics = fs._report_metrics_by_dataset(
            fs._subset_rows(row_metadata, external_mask),
            prediction[external_mask],
        )
        curve_rows.append(
            {
                "k": k,
                "feature_count": len(feature_names),
                "selected_features": selected_features,
                "all_metrics": all_metrics,
                "selection_metrics": selection_metrics,
                "external_metrics": external_metrics,
            "core_sota_objective": fs._core_sota_objective(all_metrics),
            }
        )
        if k == 1 or k == k_max or k % 10 == 0:
            print(f"swept K={k}/{k_max}", flush=True)

    write_curve_csv(curve_path, curve_rows)
    metadata = {
        "feature_source": args.feature_source,
        "embedding_model": args.embedding_model,
        "extra_embedding_models": args.extra_embedding_model,
        "datasets": dataset_names,
        "selection_datasets": selection_datasets,
        "external_datasets": external_datasets,
        "row_count": len(row_metadata),
        "fit_selection_row_count": int(np.sum(fit_selection_mask)),
        "feature_count": len(feature_names),
        "k_min": k_min,
        "k_max": k_max,
        "c": args.c,
        "ridge_alpha": args.ridge_alpha,
        "stability_rounds": args.stability_rounds,
        "stability_sample_fraction": args.stability_sample_fraction,
        "ranking_csv": str(ranking_path),
        "curve_csv": str(curve_path),
        "best_by_dataset": best_by_dataset(curve_rows),
        "best_core_objective": best_core_objective(curve_rows),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


def _short_model_slug(model_name: str) -> str:
    slug = model_slug(model_name)
    replacements = {
        "nomic-ai-nomic-embed-text-v1.5": "nomic",
        "jinaai-jina-embeddings-v2-base-code": "jina",
        "Qwen-Qwen3-Embedding-0.6B": "qwen",
        "Snowflake-snowflake-arctic-embed-m-v2.0": "snowflake",
        "voyageai-voyage-4-nano": "voyage",
    }
    return replacements.get(slug, slug)


def _load_base_table(base_root: Path, dataset_names: Sequence[str], slug: str) -> fs.FeatureTable:
    try:
        return fs._load_feature_family(base_root, dataset_names, slug, prefix="base")
    except SystemExit:
        default_slug = model_slug(COGNASCORE_DEFAULT_MODEL)
        if slug == default_slug:
            raise
        return fs._load_feature_family(base_root, dataset_names, default_slug, prefix="base")


def write_curve_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    datasets = sorted({dataset for row in rows for dataset in row["all_metrics"]})
    columns = ["k"]
    for dataset in datasets:
        columns.extend([f"{dataset}_metric", f"{dataset}_value", f"{dataset}_threshold"])
    columns.extend(["core_objective_met", "core_hit_count", "selected_features"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            flat: dict[str, Any] = {"k": row["k"], "selected_features": ";".join(row["selected_features"])}
            for dataset in datasets:
                metric = row["all_metrics"].get(dataset, {})
                flat[f"{dataset}_metric"] = metric.get("metric")
                flat[f"{dataset}_value"] = metric.get("value")
                flat[f"{dataset}_threshold"] = metric.get("threshold")
            objective = row["core_sota_objective"]
            flat["core_objective_met"] = objective["objective_met"]
            flat["core_hit_count"] = sum(bool(value) for value in objective["hits"].values())
            writer.writerow(flat)


def best_by_dataset(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        for dataset, metric in row["all_metrics"].items():
            value = metric.get("value")
            if value is None or not math.isfinite(float(value)):
                continue
            current = best.get(dataset)
            if current is None or float(value) > float(current["value"]):
                best[dataset] = {"k": row["k"], "value": float(value), "metric": metric.get("metric")}
    return best


def best_core_objective(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for row in rows:
        objective = row["core_sota_objective"]
        values = objective["values"]
        finite_values = [float(value) for value in values.values() if value is not None and math.isfinite(float(value))]
        score = (
            int(objective["objective_met"]),
            sum(bool(value) for value in objective["hits"].values()),
            float(np.mean(finite_values)) if finite_values else float("-inf"),
        )
        if best is None or score > best["score"]:
            best = {"k": row["k"], "score": score, "objective": objective}
    assert best is not None
    return best


if __name__ == "__main__":
    main()
