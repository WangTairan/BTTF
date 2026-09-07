"""Run reproducible group ablations for the frozen 18-feature CognaScore model.

The feature list is never reselected.  Each ablation removes a conceptually
defined feature family or embedding subfamily and delegates evaluation to the
canonical pooled-CV and LODO runners.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from experiments.cognascore.evaluation.cross_validate_fixed import fit_model
from experiments.cognascore.evaluation.evaluate_constructed_variants import (
    prediction_rows,
    summarize_paired_variants,
    validate_identities,
)
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS as DATASET_REGISTRY
from src.methods.cognascore.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
)
from src.methods.cognascore.runners.supervised_ridge import (
    SELECTED_FEATURES,
    load_combined_features,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = EXPERIMENT_RESULTS_ROOT / "final18_group_ablation"
DATASETS = ("mbjp", "buse", "scalabrino", "dorn", "schnappinger", "jetbrains")
CONSTRUCTED_DATASETS = (
    "java_comparative_obfuscation",
    "python_comparative_degradation",
)

FEATURE_COMPONENTS: dict[str, tuple[str, ...]] = {
    "code_level": (
        "base__operator_density",
        "base__byte_entropy",
        "base__literal_expression_log_balance",
        "base__max_line_length",
        "base__indent_transition_mean",
        "base__type_regex_ratio",
        "base__type_bitwise_ratio",
        "base__identifier_length_cv",
        "base__comparison_operator_density",
        "base__operator_character_density",
    ),
    "embedding_geometry": (
        "embedding__only_identifier__embedding_first_pc_explained_variance",
        "embedding__structural_core__embedding_first_pc_explained_variance",
    ),
    "embedding_clustering": (
        "embedding__structural_core__auto_kmeans_selected_k",
        "embedding__structural_core__optics_cluster_type_entropy_mean",
        "embedding__structural_core__auto_agglo_cluster_type_entropy_mean",
        "embedding__structural_core__optics_noise_ratio",
    ),
    "short_identifier_semantics": (
        "semantic__short_identifier_candidate_ratio",
        "semantic__short_identifier_math_application_margin_mean",
    ),
}

ABLATION_GROUPS: dict[str, tuple[str, ...]] = {
    "code_level": FEATURE_COMPONENTS["code_level"],
    "embedding_derived": (
        *FEATURE_COMPONENTS["embedding_geometry"],
        *FEATURE_COMPONENTS["embedding_clustering"],
        *FEATURE_COMPONENTS["short_identifier_semantics"],
    ),
    "embedding_geometry": FEATURE_COMPONENTS["embedding_geometry"],
    "embedding_clustering": FEATURE_COMPONENTS["embedding_clustering"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse a protocol result only when its summary.json already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_partition()
    configurations = [("full", None, ())] + [
        (f"without_{group}", group, features)
        for group, features in ABLATION_GROUPS.items()
    ]

    summaries: dict[str, dict[str, Any]] = {}
    for name, removed_group, removed_features in configurations:
        configuration_root = args.output / name
        pooled = run_protocol(
            module="experiments.cognascore.evaluation.cross_validate_fixed",
            output=configuration_root / "pooled_10fold",
            removed_features=removed_features,
            shared_args=(
                "--folds",
                str(args.folds),
                "--seed",
                str(args.seed),
                "--ridge-alpha",
                str(args.ridge_alpha),
            ),
            reuse_existing=args.reuse_existing,
        )
        lodo = run_protocol(
            module="experiments.cognascore.evaluation.leave_one_dataset_out",
            output=configuration_root / "lodo",
            removed_features=removed_features,
            shared_args=("--ridge-alpha", str(args.ridge_alpha)),
            reuse_existing=args.reuse_existing,
        )
        remaining_features = [
            feature for feature in SELECTED_FEATURES if feature not in set(removed_features)
        ]
        constructed = evaluate_constructed(
            selected_features=remaining_features,
            ridge_alpha=args.ridge_alpha,
            output=configuration_root / "constructed",
            reuse_existing=args.reuse_existing,
        )
        summaries[name] = {
            "removed_group": removed_group,
            "removed_features": list(removed_features),
            "remaining_feature_count": len(SELECTED_FEATURES) - len(removed_features),
            "pooled_metrics": pooled["metrics"],
            "lodo_metrics": lodo["metrics"],
            "constructed": constructed,
        }

    full_pooled = unweighted_dataset_average(summaries["full"]["pooled_metrics"])
    full_lodo = unweighted_dataset_average(summaries["full"]["lodo_metrics"])
    rows = []
    for name, _, _ in configurations:
        record = summaries[name]
        pooled_average = unweighted_dataset_average(record["pooled_metrics"])
        lodo_average = unweighted_dataset_average(record["lodo_metrics"])
        rows.append(
            {
                "configuration": name,
                "removed_group": record["removed_group"] or "none",
                "remaining_feature_count": record["remaining_feature_count"],
                **dataset_values("pooled", record["pooled_metrics"]),
                "pooled_unweighted_average": pooled_average,
                "pooled_unweighted_average_change": pooled_average - full_pooled,
                **dataset_values("lodo", record["lodo_metrics"]),
                "lodo_unweighted_average": lodo_average,
                "lodo_unweighted_average_change": lodo_average - full_lodo,
            }
        )

    args.output.mkdir(parents=True, exist_ok=True)
    write_rows(args.output / "ablation_results.csv", rows)
    constructed_rows = [
        constructed_overview_row(name, summaries[name])
        for name, _, _ in configurations
    ]
    write_rows(args.output / "constructed_ablation_results.csv", constructed_rows)
    detail_rows = [
        row
        for name, _, _ in configurations
        for row in constructed_detail_rows(name, summaries[name])
    ]
    write_rows(args.output / "constructed_ablation_details.csv", detail_rows)
    payload = {
        "experiment": "Frozen CognaScore 18-feature group ablation",
        "protocol": (
            "Remove one disjoint feature group without feature reselection; refit "
            "the canonical bounded Ridge under pooled grouped 10-fold CV and LODO."
        ),
        "folds": args.folds,
        "seed": args.seed,
        "ridge_alpha": args.ridge_alpha,
        "datasets": list(DATASETS),
        "dataset_average": (
            "Unweighted arithmetic mean of the six dataset-specific Spearman "
            "correlations; each dataset contributes equally."
        ),
        "full_features": list(SELECTED_FEATURES),
        "feature_components": {
            name: list(features) for name, features in FEATURE_COMPONENTS.items()
        },
        "ablation_groups": {
            name: list(features) for name, features in ABLATION_GROUPS.items()
        },
        "results": rows,
        "constructed_results": constructed_rows,
    }
    summary_path = args.output / "summary.json"
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))
    print(f"wrote: {summary_path}")


def validate_partition() -> None:
    flattened = [feature for features in FEATURE_COMPONENTS.values() for feature in features]
    duplicate_features = sorted({feature for feature in flattened if flattened.count(feature) > 1})
    if duplicate_features:
        raise RuntimeError(f"Overlapping ablation groups: {duplicate_features}")
    selected = set(SELECTED_FEATURES)
    grouped = set(flattened)
    if selected != grouped:
        raise RuntimeError(
            "Ablation groups do not partition the frozen features: "
            f"missing={sorted(selected - grouped)}, extra={sorted(grouped - selected)}"
        )
    for name, features in ABLATION_GROUPS.items():
        unknown = sorted(set(features) - selected)
        if unknown:
            raise RuntimeError(f"Ablation group {name!r} contains unknown features: {unknown}")


def run_protocol(
    *,
    module: str,
    output: Path,
    removed_features: Sequence[str],
    shared_args: Sequence[str],
    reuse_existing: bool,
) -> Mapping[str, Any]:
    summary_path = output / "summary.json"
    if not (reuse_existing and summary_path.is_file()):
        command = [
            sys.executable,
            "-m",
            module,
            *shared_args,
            "--output",
            str(output),
        ]
        for feature in removed_features:
            command.extend(("--remove-feature", feature))
        print(f"running: {' '.join(command)}", flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    return json.loads(summary_path.read_text(encoding="utf-8"))


def evaluate_constructed(
    *,
    selected_features: Sequence[str],
    ridge_alpha: float,
    output: Path,
    reuse_existing: bool,
) -> dict[str, dict[str, Any]]:
    reusable: dict[str, dict[str, Any]] = {}
    if reuse_existing:
        for dataset in CONSTRUCTED_DATASETS:
            summary_path = output / dataset / "summary.json"
            if not summary_path.is_file():
                break
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if summary.get("selected_features") != list(selected_features):
                break
            reusable[dataset] = summary
    if len(reusable) == len(CONSTRUCTED_DATASETS):
        return reusable

    training_frames = [
        load_combined_features(
            dataset,
            BASE_FEATURE_ROOT,
            EMBEDDING_FEATURE_ROOT,
            list(selected_features),
        )
        for dataset in DATASETS
    ]
    train = pd.concat(training_frames, ignore_index=True)
    model = fit_model(train, ridge_alpha, selected_features=selected_features)

    summaries: dict[str, dict[str, Any]] = {}
    for dataset_key in CONSTRUCTED_DATASETS:
        dataset_path = DATASET_REGISTRY[dataset_key].path
        items = load_code_dataset(dataset_path)
        item_by_id = {item.task_id: item for item in items}
        frame = load_combined_features(
            dataset_key,
            BASE_FEATURE_ROOT,
            EMBEDDING_FEATURE_ROOT,
            list(selected_features),
        )
        validate_identities(frame, item_by_id)
        scores = model.predict(frame.loc[:, selected_features].to_numpy(dtype=float))
        rows = prediction_rows(frame, scores, item_by_id)
        summary = {
            **summarize_paired_variants(rows),
            "dataset": dataset_key,
            "dataset_path": str(dataset_path),
            "evaluation_protocol": (
                "Fit the ablated bounded Ridge on the six human-rated development "
                "datasets, then compare every independently transformed variant "
                "with its matched original without further fitting or selection."
            ),
            "training_datasets": list(DATASETS),
            "ridge_alpha": ridge_alpha,
            "selected_feature_count": len(selected_features),
            "selected_features": list(selected_features),
        }
        dataset_output = output / dataset_key
        dataset_output.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(dataset_output / "predictions.csv", index=False)
        (dataset_output / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        summaries[dataset_key] = summary
    return summaries


def constructed_overview_row(
    configuration: str,
    record: Mapping[str, Any],
) -> dict[str, Any]:
    summaries = record["constructed"]
    row: dict[str, Any] = {
        "configuration": configuration,
        "removed_group": record["removed_group"] or "none",
        "remaining_feature_count": record["remaining_feature_count"],
    }
    for dataset in CONSTRUCTED_DATASETS:
        prefix = "java" if dataset.startswith("java_") else "python"
        summary = summaries[dataset]
        overall = summary["overall"]
        row.update(
            {
                f"{prefix}_changed_pair_count": int(overall["changed_pair_count"]),
                f"{prefix}_changed_micro": float(overall["changed_only_score_decrease_rate"]),
                f"{prefix}_changed_mean_drop": float(
                    overall["changed_only_mean_original_minus_variant"]
                ),
            }
        )
    return row


def constructed_detail_rows(
    configuration: str,
    record: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset in CONSTRUCTED_DATASETS:
        summary = record["constructed"][dataset]
        sections = (
            ("overall", {"overall": summary["overall"]}),
            ("category", summary["by_category"]),
            ("interference", summary["by_interference"]),
        )
        for level, values in sections:
            for label, metrics in values.items():
                rows.append(
                    {
                        "configuration": configuration,
                        "removed_group": record["removed_group"] or "none",
                        "remaining_feature_count": record["remaining_feature_count"],
                        "dataset": dataset,
                        "level": level,
                        "label": label,
                        "pair_count": int(metrics["pair_count"]),
                        "changed_pair_count": int(metrics["changed_pair_count"]),
                        "changed_score_decrease_rate": metrics[
                            "changed_only_score_decrease_rate"
                        ],
                        "changed_mean_original_minus_variant": metrics[
                            "changed_only_mean_original_minus_variant"
                        ],
                    }
                )
    return rows


def dataset_values(prefix: str, metrics: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    return {
        f"{prefix}_{dataset}": metric_value(metrics[dataset])
        for dataset in DATASETS
    }


def unweighted_dataset_average(metrics: Mapping[str, Mapping[str, Any]]) -> float:
    values: list[float] = []
    for dataset in DATASETS:
        value = metric_value(metrics[dataset])
        if math.isfinite(value):
            values.append(value)
    return sum(values) / len(values) if values else float("nan")


def metric_value(record: Mapping[str, Any]) -> float:
    if "value" in record:
        return float(record["value"])
    if "mcc_training_fold_threshold" in record:
        return float(record["mcc_training_fold_threshold"])
    if "mcc_fixed_target_midpoint_0_5" in record:
        return float(record["mcc_fixed_target_midpoint_0_5"])
    raise KeyError(f"No primary metric in record: {record}")


def write_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
