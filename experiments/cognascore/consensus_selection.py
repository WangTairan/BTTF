from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import joblib
from scipy.stats import rankdata

from src.experiments.paths import result_dir
from src.experiments.registry import DATASETS

from src.methods.cognascore.results import model_slug
from src.methods.cognascore.dataset_io import dataset_output_name
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)

from . import feature_selection as fs


DEFAULT_EMBEDDING_MODELS = (
    "nomic-ai/nomic-embed-text-v1.5",
    "Qwen/Qwen3-Embedding-0.6B",
    "jinaai/jina-embeddings-v2-base-code",
    "Snowflake/snowflake-arctic-embed-m-v2.0",
    "voyageai/voyage-4-nano",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Consensus CognaScore ML feature screening. Each embedding model is screened "
            "independently; feature names are then aggregated across models. The final Ridge "
            "model is fitted on one chosen embedding model instantiation."
        )
    )
    parser.add_argument("datasets", nargs="*", type=Path)
    parser.add_argument(
        "--embedding-model",
        action="append",
        default=[],
        help="Embedding model included in consensus. Defaults to the current five-model set.",
    )
    parser.add_argument(
        "--final-embedding-model",
        default="nomic-ai/nomic-embed-text-v1.5",
        help="Embedding model instantiation used for final Ridge fitting/evaluation.",
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--continuous-threshold", choices=("median", "mean"), default="median")
    parser.add_argument("--drop-middle", type=float, default=0.0)
    parser.add_argument("--drop-middle-scope", choices=("all", "training"), default="all")
    parser.add_argument("--c", type=float, default=0.08)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability-rounds", type=int, default=200)
    parser.add_argument("--stability-sample-fraction", type=float, default=0.7)
    parser.add_argument("--selection-dataset", action="append", default=[])
    parser.add_argument(
        "--fit-dataset",
        action="append",
        default=[],
        help=(
            "Dataset used to fit the final continuous Ridge model. Repeat as needed. "
            "Defaults to the selection datasets."
        ),
    )
    parser.add_argument("--external-dataset", action="append", default=[])
    parser.add_argument("--select-top", type=int, default=30)
    parser.add_argument("--candidate-limit", type=int, default=220)
    parser.add_argument(
        "--curve-k-max",
        type=int,
        default=50,
        help="Also evaluate consensus-selected Ridge models for K=1..curve-k-max and plot every dataset metric.",
    )
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.9,
        help="Reject later-ranked candidates whose absolute Pearson or Spearman correlation with a selected feature exceeds this value.",
    )
    parser.add_argument(
        "--exclude-feature",
        action="append",
        default=[],
        help="Remove one exact namespaced feature before every model screen. Repeat as needed.",
    )
    parser.add_argument(
        "--exclude-feature-prefix",
        action="append",
        default=[],
        help="Remove features whose names start with this prefix. Repeat as needed.",
    )
    parser.add_argument(
        "--exclude-group",
        action="append",
        default=[],
        help="Remove an entire feature-schema group before screening. Repeat as needed.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Number of consensus-ranked rows to include in metadata preview.",
    )
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
    embedding_models = tuple(args.embedding_model or DEFAULT_EMBEDDING_MODELS)
    if args.final_embedding_model not in embedding_models:
        raise SystemExit("--final-embedding-model must be one of the consensus --embedding-model values.")

    selection_datasets = tuple(args.selection_dataset or fs.DEFAULT_DATASET_KEYS)
    fit_datasets = tuple(args.fit_dataset or selection_datasets)
    external_datasets = tuple(args.external_dataset or fs.DEFAULT_DATASET_KEYS)

    per_model_rankings: dict[str, list[dict[str, Any]]] = {}
    for model_name in embedding_models:
        print(f"screening {model_name}", flush=True)
        ranking, _ = screen_one_model(
            args,
            dataset_names,
            model_name,
            selection_datasets=selection_datasets,
        )
        per_model_rankings[model_name] = ranking

    consensus_ranking = consensus_rank(per_model_rankings, candidate_limit=args.candidate_limit)

    final_bundle = load_model_bundle(
        args,
        dataset_names,
        args.final_embedding_model,
        selection_datasets=selection_datasets,
        fit_datasets=fit_datasets,
        external_datasets=external_datasets,
    )
    selected_features, rejected_features = select_with_correlation_replacement(
        consensus_ranking,
        final_bundle["x"],
        final_bundle["feature_names"],
        final_bundle["row_metadata"],
        top_k=args.select_top,
        threshold=args.correlation_threshold,
    )
    selected_indices = np.asarray([final_bundle["feature_names"].index(name) for name in selected_features], dtype=int)

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
        final_bundle["x"][final_bundle["fit_selection_mask"]][:, selected_indices],
        final_bundle["regression_target"][final_bundle["fit_selection_mask"]],
        final_bundle["fit_sample_weight"][final_bundle["fit_selection_mask"]],
        "ridge",
    )
    prediction = fs._predict_final_model(model, final_bundle["x"][:, selected_indices], "ridge")
    all_metrics = fs._report_metrics_by_dataset(final_bundle["row_metadata"], prediction)
    selection_metrics = fs._report_metrics_by_dataset(
        fs._subset_rows(final_bundle["row_metadata"], final_bundle["selection_mask"]),
        prediction[final_bundle["selection_mask"]],
    )
    external_metrics = fs._report_metrics_by_dataset(
        fs._subset_rows(final_bundle["row_metadata"], final_bundle["external_mask"]),
        prediction[final_bundle["external_mask"]],
    )
    fit_scope = final_bundle["fit_dataset_mask"]
    lodo_metrics = fs._leave_one_dataset_out_metrics(
        final_bundle["x"][fit_scope][:, selected_indices],
        final_bundle["regression_target"][fit_scope],
        final_bundle["sample_weight"][fit_scope],
        fs._subset_rows(final_bundle["row_metadata"], fit_scope),
        final_model_name="ridge",
        c=args.c,
        ridge_alpha=args.ridge_alpha,
        elasticnet_alpha=0.02,
        elasticnet_l1_ratio=0.2,
        seed=args.seed,
    )
    curve_rows = compute_topk_curve(
        args,
        consensus_ranking,
        final_bundle,
        k_max=args.curve_k_max,
    )
    ablation_rows = compute_feature_ablation(
        args,
        selected_features,
        final_bundle,
        baseline_metrics=all_metrics,
    )

    out_dir = result_dir(args.output, "cognascore_feature_screen_consensus", "five_model")
    out_dir.mkdir(parents=True, exist_ok=True)
    consensus_path = out_dir / "consensus_ranking.csv"
    selected_path = out_dir / "selected_features.csv"
    metrics_path = out_dir / "final_metrics.csv"
    curve_path = out_dir / "topk_curve.csv"
    curve_svg_path = out_dir / "topk_curve.svg"
    ablation_path = out_dir / "feature_ablation.csv"
    ablation_svg_path = out_dir / "feature_ablation.svg"
    metadata_path = out_dir / "metadata.json"
    model_manifest_path = out_dir / "model.json"
    model_path = out_dir / "model.joblib"
    write_consensus_ranking(consensus_path, consensus_ranking)
    write_selected(selected_path, selected_features, consensus_ranking)
    fs._write_final_metrics(metrics_path, all_metrics, selection_metrics, external_metrics, lodo_metrics)
    write_topk_curve(curve_path, curve_rows)
    write_topk_curve_svg(curve_svg_path, curve_rows)
    write_feature_ablation(ablation_path, ablation_rows)
    write_feature_ablation_svg(ablation_svg_path, ablation_rows)
    joblib.dump(model, model_path)

    metadata = {
        "method": "five_model_consensus_l1_stability_ridge",
        "feature_selection_rule": (
            "Each embedding model is screened independently using the same L1 logistic stability procedure. "
            "Features are canonicalized by name, not concatenated across models. Consensus ranking sorts by "
            "active_model_count, mean_selection_frequency, mean_abs_coefficient, and mean_rank_score. "
            "A later-ranked feature is rejected if its absolute Pearson or Spearman correlation with any "
            "already selected feature in the final-model feature table exceeds the configured threshold; "
            "the next consensus candidate is used instead."
        ),
        "embedding_models": list(embedding_models),
        "final_embedding_model": args.final_embedding_model,
        "datasets": dataset_names,
        "selection_datasets": list(selection_datasets),
        "fit_datasets": list(fit_datasets),
        "external_datasets": list(external_datasets),
        "row_count": len(final_bundle["row_metadata"]),
        "feature_count_per_model": len(final_bundle["feature_names"]),
        "select_top": args.select_top,
        "candidate_limit": args.candidate_limit,
        "curve_k_max": args.curve_k_max,
        "correlation_threshold": args.correlation_threshold,
        "c": args.c,
        "ridge_alpha": args.ridge_alpha,
        "stability_rounds": args.stability_rounds,
        "stability_sample_fraction": args.stability_sample_fraction,
        "selected_feature_count": len(selected_features),
        "selected_features": selected_features,
        "features": {"ordered_names": selected_features},
        "embedding_model": args.final_embedding_model,
        "serialized_model": model_path.name,
        "serialized_model_sha256": _sha256_file(model_path),
        "selected_feature_category_counts": feature_category_counts(selected_features),
        "rejected_by_correlation": rejected_features,
        "final_all_report_metrics": all_metrics,
        "final_selection_train_report_metrics": selection_metrics,
        "final_external_report_metrics": external_metrics,
        "final_leave_one_dataset_out_report_metrics": lodo_metrics,
        "core_sota_objective": fs._core_sota_objective(all_metrics),
        "consensus_ranking_csv": str(consensus_path),
        "selected_features_csv": str(selected_path),
        "metrics_csv": str(metrics_path),
        "topk_curve_csv": str(curve_path),
        "topk_curve_svg": str(curve_svg_path),
        "topk_curve_best_by_dataset": best_by_dataset(curve_rows),
        "feature_ablation_csv": str(ablation_path),
        "feature_ablation_svg": str(ablation_svg_path),
        "feature_ablation_ordering": "descending mean metric drop across all datasets after removing one selected feature and refitting Ridge",
        "top_feature_ablation": ablation_rows[: args.top],
        "top_consensus_features": consensus_ranking[: args.top],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    model_manifest_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2), flush=True)


def screen_one_model(
    args: argparse.Namespace,
    dataset_names: Sequence[str],
    model_name: str,
    *,
    selection_datasets: Sequence[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bundle = load_model_bundle(
        args,
        dataset_names,
        model_name,
        selection_datasets=selection_datasets,
        external_datasets=(),
    )
    model = fs._build_model(args.c, args.seed)
    model.fit(
        bundle["x"][bundle["fit_selection_mask"]],
        bundle["y"][bundle["fit_selection_mask"]],
        logisticregression__sample_weight=bundle["fit_sample_weight"][bundle["fit_selection_mask"]],
    )
    coefficients = fs._extract_coefficients(model, bundle["feature_names"])
    stability = fs._stability_selection(
        bundle["x"],
        bundle["y"],
        bundle["sample_weight"],
        bundle["row_metadata"],
        bundle["feature_names"],
        c=args.c,
        rounds=args.stability_rounds,
        seed=args.seed,
        selection_datasets=selection_datasets,
        eligible_mask=bundle["training_middle_keep_mask"],
        sample_fraction=args.stability_sample_fraction,
    )
    ranking = fs._rank_features(coefficients, stability, bundle["groups"])
    return ranking, bundle


def load_model_bundle(
    args: argparse.Namespace,
    dataset_names: Sequence[str],
    model_name: str,
    *,
    selection_datasets: Sequence[str],
    fit_datasets: Sequence[str] | None = None,
    external_datasets: Sequence[str],
) -> dict[str, Any]:
    slug = model_slug(model_name)
    base_table = fs._load_feature_family(args.base_root, dataset_names, slug, prefix="base")
    embedding_table = fs._load_feature_family(args.embedding_root, dataset_names, slug, prefix="embedding")
    merged_rows, groups = fs._merge_tables(base_table, embedding_table)
    x, y, sample_weight, feature_names, row_metadata = fs._prepare_matrix(
        merged_rows,
        groups,
        continuous_threshold=args.continuous_threshold,
        drop_middle=args.drop_middle if args.drop_middle_scope == "all" else 0.0,
    )
    x, feature_names, groups, excluded_features = apply_feature_exclusions(
        x,
        feature_names,
        groups,
        exact=args.exclude_feature,
        prefixes=args.exclude_feature_prefix,
        excluded_groups=args.exclude_group,
    )
    selection_mask = fs._dataset_mask(row_metadata, selection_datasets)
    fit_dataset_mask = fs._dataset_mask(row_metadata, fit_datasets or selection_datasets)
    external_mask = (
        fs._dataset_mask(row_metadata, external_datasets)
        if external_datasets
        else np.zeros(len(row_metadata), dtype=bool)
    )
    training_middle_keep_mask = (
        fs._middle_keep_mask(row_metadata, args.drop_middle)
        if args.drop_middle_scope == "training"
        else np.ones(len(row_metadata), dtype=bool)
    )
    fit_selection_mask = fit_dataset_mask & training_middle_keep_mask
    if int(np.sum(fit_selection_mask)) == 0:
        raise SystemExit(f"No fitting rows selected for {model_name}.")
    return {
        "x": x,
        "y": y,
        "sample_weight": sample_weight,
        "feature_names": feature_names,
        "row_metadata": row_metadata,
        "groups": groups,
        "selection_mask": selection_mask,
        "fit_dataset_mask": fit_dataset_mask,
        "external_mask": external_mask,
        "training_middle_keep_mask": training_middle_keep_mask,
        "fit_selection_mask": fit_selection_mask,
        "fit_sample_weight": fs._sample_weight_for_rows(row_metadata, fit_selection_mask),
        "regression_target": fs._regression_target(row_metadata),
        "excluded_features": excluded_features,
    }


def apply_feature_exclusions(
    x: np.ndarray,
    feature_names: Sequence[str],
    groups: Mapping[str, str],
    *,
    exact: Sequence[str],
    prefixes: Sequence[str],
    excluded_groups: Sequence[str],
) -> tuple[np.ndarray, list[str], dict[str, str], list[str]]:
    """Apply the same theory-driven candidate exclusions to every model table."""
    exact_set = set(exact)
    group_set = set(excluded_groups)
    excluded = [
        feature
        for feature in feature_names
        if feature in exact_set
        or any(feature.startswith(prefix) for prefix in prefixes)
        or groups.get(feature) in group_set
    ]
    keep_indices = [
        index for index, feature in enumerate(feature_names) if feature not in set(excluded)
    ]
    if not keep_indices:
        raise SystemExit("Feature exclusions removed the complete candidate inventory.")
    kept_names = [feature_names[index] for index in keep_indices]
    kept_groups = {feature: groups[feature] for feature in kept_names}
    return x[:, np.asarray(keep_indices, dtype=int)], kept_names, kept_groups, excluded


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def consensus_rank(
    per_model_rankings: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    candidate_limit: int,
) -> list[dict[str, Any]]:
    aggregate: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "feature": "",
            "models": [],
            "active_model_count": 0,
            "selection_frequency_sum": 0.0,
            "abs_coefficient_sum": 0.0,
            "mean_abs_coefficient_sum": 0.0,
            "rank_score_sum": 0.0,
            "best_rank": None,
            "group_votes": defaultdict(int),
        }
    )
    total_models = len(per_model_rankings)
    for model_name, ranking in per_model_rankings.items():
        for rank, row in enumerate(ranking[:candidate_limit], start=1):
            feature = str(row["feature"])
            entry = aggregate[feature]
            entry["feature"] = feature
            entry["models"].append(model_name)
            frequency = float(row.get("selection_frequency", 0.0))
            if frequency > 0.0 or bool(row.get("nonzero", False)):
                entry["active_model_count"] += 1
            entry["selection_frequency_sum"] += frequency
            entry["abs_coefficient_sum"] += float(row.get("abs_coefficient", 0.0))
            entry["mean_abs_coefficient_sum"] += float(row.get("mean_abs_coefficient", 0.0))
            entry["rank_score_sum"] += 1.0 / rank
            entry["best_rank"] = rank if entry["best_rank"] is None else min(entry["best_rank"], rank)
            entry["group_votes"][str(row.get("group", "unknown"))] += 1

    rows: list[dict[str, Any]] = []
    for feature, entry in aggregate.items():
        model_count = len(entry["models"])
        group = max(entry["group_votes"].items(), key=lambda item: item[1])[0]
        rows.append(
            {
                "feature": feature,
                "group": group,
                "model_count": model_count,
                "active_model_count": int(entry["active_model_count"]),
                "mean_selection_frequency": float(entry["selection_frequency_sum"] / total_models),
                "mean_abs_coefficient": float(entry["abs_coefficient_sum"] / total_models),
                "mean_stability_abs_coefficient": float(entry["mean_abs_coefficient_sum"] / total_models),
                "mean_rank_score": float(entry["rank_score_sum"] / total_models),
                "best_rank": int(entry["best_rank"] or candidate_limit + 1),
                "models": ";".join(entry["models"]),
            }
        )
    rows.sort(
        key=lambda row: (
            row["active_model_count"],
            row["mean_selection_frequency"],
            row["mean_abs_coefficient"],
            row["mean_rank_score"],
            -row["best_rank"],
        ),
        reverse=True,
    )
    return rows


def select_with_correlation_replacement(
    ranking: Sequence[Mapping[str, Any]],
    x: np.ndarray,
    feature_names: Sequence[str],
    row_metadata: Sequence[Mapping[str, Any]],
    *,
    top_k: int,
    threshold: float,
) -> tuple[list[str], list[dict[str, Any]]]:
    del row_metadata
    name_to_index = {name: index for index, name in enumerate(feature_names)}
    imputer = fs._median_imputer()
    x_imputed = imputer.fit_transform(x)
    selected: list[str] = []
    rejected: list[dict[str, Any]] = []
    for row in ranking:
        feature = str(row["feature"])
        if feature not in name_to_index:
            continue
        conflicts = [
            conflict
            for selected_feature in selected
            if (
                conflict := correlation_conflict(
                    x_imputed[:, name_to_index[feature]],
                    x_imputed[:, name_to_index[selected_feature]],
                    selected_feature,
                    threshold,
                )
            )
        ]
        if conflicts:
            rejected.append({"feature": feature, "conflicts": conflicts, "replacement_policy": "skip_and_take_next_consensus_candidate"})
            continue
        selected.append(feature)
        if len(selected) >= top_k:
            break
    if len(selected) < top_k:
        raise SystemExit(f"Only selected {len(selected)} features after correlation filtering; requested {top_k}.")
    return selected, rejected


def correlation_conflict(
    candidate: np.ndarray,
    selected: np.ndarray,
    selected_name: str,
    threshold: float,
) -> dict[str, Any] | None:
    pearson = safe_corr(candidate, selected)
    spearman = safe_corr(rankdata(candidate, method="average"), rankdata(selected, method="average"))
    max_abs = max(abs(pearson), abs(spearman))
    if max_abs <= threshold:
        return None
    return {
        "selected_feature": selected_name,
        "pearson": pearson,
        "spearman": spearman,
        "max_abs_correlation": max_abs,
    }


def safe_corr(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 2 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def feature_category_counts(features: Sequence[str]) -> dict[str, int]:
    return {
        "base": sum(feature.startswith("base__") for feature in features),
        "compression": sum(feature.startswith("compression__") for feature in features),
        "embedding": sum(feature.startswith("embedding__") for feature in features),
        "semantic": sum(feature.startswith("semantic__") for feature in features),
    }


def compute_topk_curve(
    args: argparse.Namespace,
    ranking: Sequence[Mapping[str, Any]],
    bundle: Mapping[str, Any],
    *,
    k_max: int,
) -> list[dict[str, Any]]:
    if k_max <= 0:
        return []
    max_k = min(k_max, len(ranking), len(bundle["feature_names"]))
    rows: list[dict[str, Any]] = []
    for k in range(1, max_k + 1):
        selected_features, rejected_features = select_with_correlation_replacement(
            ranking,
            bundle["x"],
            bundle["feature_names"],
            bundle["row_metadata"],
            top_k=k,
            threshold=args.correlation_threshold,
        )
        selected_indices = np.asarray([bundle["feature_names"].index(name) for name in selected_features], dtype=int)
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
            bundle["x"][bundle["fit_selection_mask"]][:, selected_indices],
            bundle["regression_target"][bundle["fit_selection_mask"]],
            bundle["fit_sample_weight"][bundle["fit_selection_mask"]],
            "ridge",
        )
        prediction = fs._predict_final_model(model, bundle["x"][:, selected_indices], "ridge")
        all_metrics = fs._report_metrics_by_dataset(bundle["row_metadata"], prediction)
        rows.append(
            {
                "k": k,
                "selected_features": selected_features,
                "selected_feature_category_counts": feature_category_counts(selected_features),
                "rejected_by_correlation_count": len(rejected_features),
                "all_metrics": all_metrics,
                "core_sota_objective": fs._core_sota_objective(all_metrics),
            }
        )
        if k == 1 or k == max_k or k % 10 == 0:
            print(f"curve K={k}/{max_k}", flush=True)
    return rows


def write_topk_curve(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    datasets = sorted({dataset for row in rows for dataset in row["all_metrics"]})
    columns = ["k"]
    for dataset in datasets:
        columns.extend([f"{dataset}_metric", f"{dataset}_value", f"{dataset}_threshold"])
    columns.extend(
        [
            "core_objective_met",
            "core_hit_count",
            "base_count",
            "compression_count",
            "embedding_count",
            "semantic_count",
            "rejected_by_correlation_count",
            "selected_features",
        ]
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            flat: dict[str, Any] = {"k": row["k"]}
            for dataset in datasets:
                metric = row["all_metrics"].get(dataset, {})
                flat[f"{dataset}_metric"] = metric.get("metric")
                flat[f"{dataset}_value"] = metric.get("value")
                flat[f"{dataset}_threshold"] = metric.get("threshold")
            objective = row["core_sota_objective"]
            counts = row["selected_feature_category_counts"]
            flat["core_objective_met"] = objective["objective_met"]
            flat["core_hit_count"] = sum(bool(value) for value in objective["hits"].values())
            flat["base_count"] = counts["base"]
            flat["compression_count"] = counts["compression"]
            flat["embedding_count"] = counts["embedding"]
            flat["semantic_count"] = counts["semantic"]
            flat["rejected_by_correlation_count"] = row["rejected_by_correlation_count"]
            flat["selected_features"] = ";".join(row["selected_features"])
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
                best[dataset] = {
                    "k": row["k"],
                    "metric": metric.get("metric"),
                    "value": float(value),
                    "selected_feature_category_counts": row["selected_feature_category_counts"],
                }
    return best


def evaluate_feature_set(
    args: argparse.Namespace,
    selected_features: Sequence[str],
    bundle: Mapping[str, Any],
) -> dict[str, dict[str, float | int | str | None]]:
    selected_indices = np.asarray([bundle["feature_names"].index(name) for name in selected_features], dtype=int)
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
        bundle["x"][bundle["fit_selection_mask"]][:, selected_indices],
        bundle["regression_target"][bundle["fit_selection_mask"]],
        bundle["fit_sample_weight"][bundle["fit_selection_mask"]],
        "ridge",
    )
    prediction = fs._predict_final_model(model, bundle["x"][:, selected_indices], "ridge")
    return fs._report_metrics_by_dataset(bundle["row_metadata"], prediction)


def compute_feature_ablation(
    args: argparse.Namespace,
    selected_features: Sequence[str],
    bundle: Mapping[str, Any],
    *,
    baseline_metrics: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    datasets = sorted(baseline_metrics)
    for index, removed_feature in enumerate(selected_features, start=1):
        remaining = [feature for feature in selected_features if feature != removed_feature]
        ablated_metrics = evaluate_feature_set(args, remaining, bundle)
        deltas: dict[str, float | None] = {}
        finite_deltas: list[float] = []
        for dataset in datasets:
            baseline_value = baseline_metrics.get(dataset, {}).get("value")
            ablated_value = ablated_metrics.get(dataset, {}).get("value")
            if (
                baseline_value is None
                or ablated_value is None
                or not math.isfinite(float(baseline_value))
                or not math.isfinite(float(ablated_value))
            ):
                deltas[dataset] = None
                continue
            delta = float(baseline_value) - float(ablated_value)
            deltas[dataset] = delta
            finite_deltas.append(delta)
        core_datasets = [dataset for dataset in ("scalabrino", "jetbrains", "dorn", "schnappinger") if deltas.get(dataset) is not None]
        core_deltas = [float(deltas[dataset]) for dataset in core_datasets]
        rows.append(
            {
                "removed_feature": removed_feature,
                "original_rank": index,
                "category": removed_feature.split("__", 1)[0] if "__" in removed_feature else "unknown",
                "mean_delta_all": float(np.mean(finite_deltas)) if finite_deltas else 0.0,
                "mean_delta_core": float(np.mean(core_deltas)) if core_deltas else 0.0,
                "deltas": deltas,
                "ablated_metrics": ablated_metrics,
            }
        )
        print(f"ablation {index}/{len(selected_features)}", flush=True)
    rows.sort(key=lambda row: (row["mean_delta_all"], row["mean_delta_core"]), reverse=True)
    return rows


def write_feature_ablation(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    datasets = sorted({dataset for row in rows for dataset in row["deltas"]})
    columns = ["impact_rank", "original_rank", "removed_feature", "category", "mean_delta_all", "mean_delta_core"]
    for dataset in datasets:
        columns.extend([f"{dataset}_delta", f"{dataset}_ablated_value"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for impact_rank, row in enumerate(rows, start=1):
            flat: dict[str, Any] = {
                "impact_rank": impact_rank,
                "original_rank": row["original_rank"],
                "removed_feature": row["removed_feature"],
                "category": row["category"],
                "mean_delta_all": row["mean_delta_all"],
                "mean_delta_core": row["mean_delta_core"],
            }
            for dataset in datasets:
                flat[f"{dataset}_delta"] = row["deltas"].get(dataset)
                flat[f"{dataset}_ablated_value"] = row["ablated_metrics"].get(dataset, {}).get("value")
            writer.writerow(flat)


def write_feature_ablation_svg(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    datasets = ["buse", "dorn", "jetbrains", "mbjp", "scalabrino", "schnappinger"]
    row_h = 28
    top = 64
    left = 430
    bar_w = 220
    cell_w = 74
    right = 34
    height = top + row_h * len(rows) + 56
    width = left + bar_w + cell_w * len(datasets) + right
    max_abs_delta = max(
        [abs(float(row["mean_delta_all"])) for row in rows]
        + [
            abs(float(delta))
            for row in rows
            for delta in row["deltas"].values()
            if delta is not None and math.isfinite(float(delta))
        ]
        + [0.001]
    )

    def color_for(delta: float | None) -> str:
        if delta is None:
            return "#f3f4f6"
        value = max(-1.0, min(1.0, float(delta) / max_abs_delta))
        if value >= 0:
            intensity = int(255 - 105 * value)
            return f"rgb(255,{intensity},{intensity})"
        intensity = int(255 - 105 * abs(value))
        return f"rgb({intensity},{intensity},255)"

    def bar_len(delta: float) -> float:
        return min(abs(delta) / max_abs_delta, 1.0) * (bar_w / 2 - 8)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Feature ablation sensitivity">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#111827}.muted{fill:#6b7280;font-size:12px}.small{font-size:11px}.grid{stroke:#e5e7eb;stroke-width:1}.zero{stroke:#6b7280;stroke-width:1}</style>',
        '<text x="24" y="26" font-size="18" font-weight="700">Leave-one-feature-out sensitivity</text>',
        '<text x="24" y="46" class="muted">Rows are ordered by mean metric drop after removing one selected feature and refitting Ridge. Red means removal hurts; blue means removal helps.</text>',
        f'<text x="{left}" y="{top - 16}" class="muted">Mean Δ</text>',
    ]
    for index, dataset in enumerate(datasets):
        x = left + bar_w + index * cell_w
        parts.append(f'<text x="{x + cell_w / 2:.1f}" y="{top - 16}" class="muted" text-anchor="middle">{html.escape(dataset)}</text>')
    zero_x = left + bar_w / 2
    parts.append(f'<line class="zero" x1="{zero_x:.1f}" y1="{top - 8}" x2="{zero_x:.1f}" y2="{top + row_h * len(rows)}"/>')
    for row_index, row in enumerate(rows):
        y = top + row_index * row_h
        center_y = y + row_h / 2
        if row_index % 2 == 0:
            parts.append(f'<rect x="0" y="{y:.1f}" width="{width}" height="{row_h}" fill="#f9fafb"/>')
        label = str(row["removed_feature"])
        if len(label) > 58:
            label = "…" + label[-57:]
        parts.append(f'<text x="24" y="{center_y + 4:.1f}" class="small">{html.escape(label)}</text>')
        mean_delta = float(row["mean_delta_all"])
        length = bar_len(mean_delta)
        if mean_delta >= 0:
            x = zero_x
        else:
            x = zero_x - length
        parts.append(f'<rect x="{x:.1f}" y="{center_y - 6:.1f}" width="{length:.1f}" height="12" fill="{color_for(mean_delta)}" stroke="#d1d5db"/>')
        parts.append(f'<text x="{left + bar_w - 4}" y="{center_y + 4:.1f}" class="small" text-anchor="end">{mean_delta:+.3f}</text>')
        for index, dataset in enumerate(datasets):
            x = left + bar_w + index * cell_w
            delta = row["deltas"].get(dataset)
            parts.append(f'<rect x="{x:.1f}" y="{y + 3:.1f}" width="{cell_w - 4}" height="{row_h - 6}" fill="{color_for(delta)}" stroke="#ffffff"/>')
            text = "" if delta is None else f"{float(delta):+.3f}"
            parts.append(f'<text x="{x + cell_w / 2 - 2:.1f}" y="{center_y + 4:.1f}" class="small" text-anchor="middle">{text}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_topk_curve_svg(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    datasets = ["buse", "dorn", "jetbrains", "mbjp", "scalabrino", "schnappinger"]
    colors = {
        "buse": "#2563eb",
        "dorn": "#16a34a",
        "jetbrains": "#dc2626",
        "mbjp": "#9333ea",
        "scalabrino": "#ea580c",
        "schnappinger": "#0891b2",
    }
    values = [
        float(metric["value"])
        for row in rows
        for metric in row["all_metrics"].values()
        if metric.get("value") is not None and math.isfinite(float(metric["value"]))
    ]
    y_min = min(0.0, min(values, default=0.0))
    y_max = max(0.75, max(values, default=0.75))
    padding = 0.04 * max(y_max - y_min, 1e-6)
    y_min -= padding
    y_max += padding

    width, height = 1100, 620
    left, right, top, bottom = 74, 240, 42, 78
    plot_w = width - left - right
    plot_h = height - top - bottom
    k_values = [int(row["k"]) for row in rows]
    k_min, k_max = min(k_values), max(k_values)

    def x_for(k: int) -> float:
        if k_max == k_min:
            return left + plot_w / 2
        return left + ((k - k_min) / (k_max - k_min)) * plot_w

    def y_for(value: float) -> float:
        return top + (1.0 - ((value - y_min) / (y_max - y_min))) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Top-K feature curve">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#111827} .muted{fill:#6b7280;font-size:12px} .axis{stroke:#9ca3af;stroke-width:1} .grid{stroke:#e5e7eb;stroke-width:1} .line{fill:none;stroke-width:2.4} .sota{stroke:#9ca3af;stroke-dasharray:4 4;stroke-width:1.2}</style>',
        '<text x="74" y="24" font-size="18" font-weight="700">CognaScore consensus Top-K curve</text>',
        '<text x="74" y="44" class="muted">Final Ridge uses the selected final embedding model; JetBrains is MCC, others are Spearman.</text>',
    ]
    for tick in np.linspace(y_min, y_max, 6):
        y = y_for(float(tick))
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}"/>')
        parts.append(f'<text class="muted" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{tick:.2f}</text>')
    for k in range(k_min, k_max + 1, 5):
        x = x_for(k)
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}"/>')
        parts.append(f'<text class="muted" x="{x:.1f}" y="{height - 44}" text-anchor="middle">{k}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>')
    parts.append(f'<text class="muted" x="{left + plot_w / 2:.1f}" y="{height - 16}" text-anchor="middle">Number of selected consensus features (K)</text>')
    parts.append(f'<text class="muted" transform="translate(18 {top + plot_h / 2:.1f}) rotate(-90)" text-anchor="middle">Metric value</text>')

    for dataset in datasets:
        points = []
        for row in rows:
            metric = row["all_metrics"].get(dataset, {})
            value = metric.get("value")
            if value is not None and math.isfinite(float(value)):
                points.append((int(row["k"]), float(value)))
        if not points:
            continue
        path_data = " ".join(
            ("M" if index == 0 else "L") + f"{x_for(k):.1f},{y_for(value):.1f}"
            for index, (k, value) in enumerate(points)
        )
        color = colors[dataset]
        parts.append(f'<path class="line" d="{path_data}" stroke="{color}"/>')
        for k, value in points:
            if k == k_min or k == k_max or k % 10 == 0:
                parts.append(f'<circle cx="{x_for(k):.1f}" cy="{y_for(value):.1f}" r="3.2" fill="{color}"/>')
        last_k, last_value = points[-1]
        parts.append(
            f'<text x="{left + plot_w + 12}" y="{y_for(last_value) + 4:.1f}" font-size="12" fill="{color}">'
            f'{html.escape(dataset)} {last_value:.3f}</text>'
        )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_consensus_ranking(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    columns = (
        "rank",
        "feature",
        "group",
        "model_count",
        "active_model_count",
        "mean_selection_frequency",
        "mean_abs_coefficient",
        "mean_stability_abs_coefficient",
        "mean_rank_score",
        "best_rank",
        "models",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for rank, row in enumerate(rows, start=1):
            writer.writerow({"rank": rank, **{column: row.get(column) for column in columns if column != "rank"}})


def write_selected(
    path: Path,
    selected_features: Sequence[str],
    ranking: Sequence[Mapping[str, Any]],
) -> None:
    by_feature = {str(row["feature"]): row for row in ranking}
    columns = (
        "selected_rank",
        "consensus_rank",
        "feature",
        "group",
        "active_model_count",
        "mean_selection_frequency",
        "mean_abs_coefficient",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for selected_rank, feature in enumerate(selected_features, start=1):
            row = by_feature[feature]
            consensus_rank = ranking.index(row) + 1
            writer.writerow(
                {
                    "selected_rank": selected_rank,
                    "consensus_rank": consensus_rank,
                    "feature": feature,
                    "group": row["group"],
                    "active_model_count": row["active_model_count"],
                    "mean_selection_frequency": row["mean_selection_frequency"],
                    "mean_abs_coefficient": row["mean_abs_coefficient"],
                }
            )


if __name__ == "__main__":
    main()
