"""Compare readability methods on the progressive-obfuscation chains."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.statistics import spearman
from src.methods.cognascore.paths import EXPERIMENT_RESULTS_ROOT

from .evaluate_progressive_obfuscation import EXPECTED_LEVELS, summarize


EXPECTED_VARIANT_COUNT = 700
PRE_LAYOUT_MAX_LEVEL = 4


DEFAULT_INPUTS = {
    "CognaScore ML": Path(
        "results/experiments/cognascore/consensus18_6dataset_sampled_margin_nomic/"
        "progressive_obfuscation_nomic/predictions.csv"
    ),
    "Posnett": Path(
        "results/methods/posnett/java_progressive_obfuscation/summary.json"
    ),
    "Scalabrino": Path(
        "results/methods/scalabrino/java_progressive_obfuscation/summary.json"
    ),
    "LOC": Path(
        "results/methods/loc_baseline/java_progressive_obfuscation/summary.json"
    ),
}

# All comparison scores must use the same higher-is-more-readable direction.
SCORE_MULTIPLIER = {
    "CognaScore ML": 1.0,
    "Posnett": 1.0,
    "Scalabrino": 1.0,
    "LOC": -1.0,
}

SCORE_REPRESENTATION = {
    "CognaScore ML": "frozen_ridge_score",
    "Posnett": "pre_sigmoid_z_value",
    "Scalabrino": "released_tool_score",
    "LOC": "negative_nonempty_loc",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a direction-aligned comparison on progressive obfuscation."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT / "progressive_obfuscation_comparison",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    loaded: dict[str, tuple[list[dict[str, Any]], list[float]]] = {}
    complete_groups_by_method: dict[str, set[str]] = {}
    missing: dict[str, str] = {}
    for method, path in DEFAULT_INPUTS.items():
        if not path.is_file():
            missing[method] = str(path)
            continue
        loaded[method] = load_rows(
            path,
            method=method,
            multiplier=SCORE_MULTIPLIER[method],
        )
        complete_groups_by_method[method] = complete_group_ids(loaded[method][0])

    shared_groups = (
        set.intersection(*complete_groups_by_method.values())
        if complete_groups_by_method
        else set()
    )
    detailed: dict[str, dict[str, Any]] = {}
    table_rows: list[dict[str, Any]] = []
    for method, (rows, raw_scores) in loaded.items():
        complete_groups = complete_groups_by_method[method]
        complete_rows = [row for row in rows if str(row["group_id"]) in complete_groups]
        shared_rows = [row for row in rows if str(row["group_id"]) in shared_groups]
        available_metrics = summarize(complete_rows)
        shared_metrics = summarize(shared_rows)
        available_without_l1 = [
            row for row in complete_rows if int(row["level"]) != 1
        ]
        omit_l1_metrics = summarize(
            available_without_l1,
            expected_levels=tuple(level for level in EXPECTED_LEVELS if level != 1),
        )
        available_before_layout = [
            row for row in complete_rows if int(row["level"]) <= PRE_LAYOUT_MAX_LEVEL
        ]
        available_metrics["pooled_spearman_pre_layout"] = finite_or_none(
            spearman(
                [float(row["score"]) for row in available_before_layout],
                [float(row["readability_target"]) for row in available_before_layout],
            )
        )
        before_layout = [
            row for row in shared_rows if int(row["level"]) <= PRE_LAYOUT_MAX_LEVEL
        ]
        shared_metrics["pooled_spearman_pre_layout"] = finite_or_none(
            spearman(
                [float(row["score"]) for row in before_layout],
                [float(row["readability_target"]) for row in before_layout],
            )
        )
        all_valid_pooled = finite_or_none(
            spearman(
                [float(row["score"]) for row in rows],
                [float(row["readability_target"]) for row in rows],
            )
        )
        raw_rho = spearman(
            raw_scores,
            [float(row["readability_target"]) for row in rows],
        )
        metrics = {
            "availability": {
                "valid_variant_count": len(rows),
                "missing_variant_count": EXPECTED_VARIANT_COUNT - len(rows),
                "complete_group_count": len(complete_groups),
            },
            "all_valid_pooled_spearman": all_valid_pooled,
            "raw_all_valid_pooled_spearman": finite_or_none(raw_rho),
            "available_complete_groups": available_metrics,
            "sensitivity_omit_l1": omit_l1_metrics,
            "shared_complete_groups": shared_metrics,
            "score_multiplier_for_readability_direction": SCORE_MULTIPLIER[method],
            "score_representation": SCORE_REPRESENTATION[method],
        }
        detailed[method] = metrics
        table_rows.append(flatten_metrics(method, metrics))

    args.output.mkdir(parents=True, exist_ok=True)
    csv_path = args.output / "comparison.csv"
    omit_l1_csv_path = args.output / "comparison_omit_l1.csv"
    json_path = args.output / "summary.json"
    pd.DataFrame(table_rows).to_csv(csv_path, index=False)
    pd.DataFrame(
        flatten_omit_l1_metrics(method, metrics)
        for method, metrics in detailed.items()
    ).to_csv(omit_l1_csv_path, index=False)
    json_path.write_text(
        json.dumps(
            {
                "score_direction": "higher transformed score means more readable",
                "loc_transform": (
                    "LOC is multiplied by -1 because the registered baseline defines "
                    "fewer non-empty lines as more readable"
                ),
                "comparison_scope": (
                    "primary metrics use every complete L0--L6 group available to each "
                    "method; shared-group metrics are retained as a sensitivity analysis"
                ),
                "shared_complete_group_count": len(shared_groups),
                "methods": detailed,
                "missing_methods": missing,
            },
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print_table(table_rows)
    print("\nSensitivity analysis: L1 omitted", flush=True)
    print_table(
        [flatten_omit_l1_metrics(method, metrics) for method, metrics in detailed.items()]
    )
    if missing:
        print("Pending: " + ", ".join(sorted(missing)), flush=True)
    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {omit_l1_csv_path}", flush=True)
    print(f"Wrote {json_path}", flush=True)


def load_rows(
    path: Path,
    *,
    method: str,
    multiplier: float,
) -> tuple[list[dict[str, Any]], list[float]]:
    if path.suffix == ".csv":
        records = pd.read_csv(path).to_dict("records")
        result_rows = []
        raw_scores = []
        for record in records:
            raw_score = float(record["score"])
            raw_scores.append(raw_score)
            result_rows.append(
                {
                    **record,
                    "score": multiplier * raw_score,
                    "raw_score": raw_score,
                    "readability_target": float(record["readability_target"]),
                }
            )
        return result_rows, raw_scores

    payload = json.loads(path.read_text(encoding="utf-8"))
    result_rows = []
    for record in payload["results"]:
        if record.get("score") is None:
            continue
        metadata = record["metadata"]
        raw_score = method_score(record, method=method)
        result_rows.append(
            {
                "task_id": str(record["task_id"]),
                "group_id": str(metadata["group_id"]),
                "source": str(metadata["source"]),
                "level": int(metadata["level"]),
                "readability_target": float(record["readability_score"]),
                "score": multiplier * raw_score,
                "raw_score": raw_score,
                "content_sha256": str(metadata["content_sha256"]),
            }
        )
    result_rows.sort(key=lambda row: (row["group_id"], row["level"]))
    return result_rows, [float(row["raw_score"]) for row in result_rows]


def method_score(record: dict[str, Any], *, method: str) -> float:
    if method == "Posnett":
        # The released formula applies sigmoid(z). Large complete classes can
        # underflow to an exact probability of zero and introduce artificial
        # rank ties. z is the mathematically equivalent monotonic score.
        return float(record["result"]["z_value"])
    return float(record["score"])


def complete_group_ids(rows: list[dict[str, Any]]) -> set[str]:
    levels_by_group: dict[str, set[int]] = {}
    for row in rows:
        levels_by_group.setdefault(str(row["group_id"]), set()).add(int(row["level"]))
    return {
        group_id
        for group_id, levels in levels_by_group.items()
        if levels == set(EXPECTED_LEVELS)
    }


def flatten_metrics(method: str, metrics: dict[str, Any]) -> dict[str, Any]:
    available = metrics["available_complete_groups"]
    chain = available["chain_direction"]
    adjacent = available["adjacent_transitions"]["overall"]
    return {
        "method": method,
        "valid_variant_count": metrics["availability"]["valid_variant_count"],
        "complete_group_count": available["group_count"],
        "pooled_spearman": available["pooled_spearman"],
        "pooled_spearman_pre_layout": available["pooled_spearman_pre_layout"],
        "all_valid_pooled_spearman": metrics["all_valid_pooled_spearman"],
        "mean_within_group_spearman": available["within_group_spearman"]["mean"],
        "first_above_last_rate": chain["endpoint_first_above_last_rate"],
        "non_increasing_chain_rate": chain["non_increasing_group_rate"],
        "adjacent_decrease_rate": adjacent["decrease_rate"],
        "changed_only_adjacent_decrease_rate": adjacent["changed_only_decrease_rate"],
    }


def flatten_omit_l1_metrics(method: str, metrics: dict[str, Any]) -> dict[str, Any]:
    omit_l1 = metrics["sensitivity_omit_l1"]
    chain = omit_l1["chain_direction"]
    adjacent = omit_l1["adjacent_transitions"]["overall"]
    return {
        "method": method,
        "valid_variant_count": omit_l1["variant_count"],
        "complete_group_count": omit_l1["group_count"],
        "pooled_spearman": omit_l1["pooled_spearman"],
        "mean_within_group_spearman": omit_l1["within_group_spearman"]["mean"],
        "first_above_last_rate": chain["endpoint_first_above_last_rate"],
        "non_increasing_chain_rate": chain["non_increasing_group_rate"],
        "adjacent_decrease_rate": adjacent["decrease_rate"],
        "changed_only_adjacent_decrease_rate": adjacent["changed_only_decrease_rate"],
    }


def finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def print_table(rows: list[dict[str, Any]]) -> None:
    print(
        "Method                 Valid/groups  Pooled rho  Within-group rho  L0>L6  Changed adjacent",
        flush=True,
    )
    for row in rows:
        print(
            f"{row['method']:<22} "
            f"{row['valid_variant_count']:>4}/{row['complete_group_count']:<6}  "
            f"{row['pooled_spearman']:>10.4f}  "
            f"{row['mean_within_group_spearman']:>16.4f}  "
            f"{row['first_above_last_rate']:>6.1%}  "
            f"{row['changed_only_adjacent_decrease_rate']:>16.1%}",
            flush=True,
        )


if __name__ == "__main__":
    main()
