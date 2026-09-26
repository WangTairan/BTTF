"""Compare embedding-only and causal-LM-extended ranked feature prefixes.

This is a development diagnostic, not a nested feature-selection estimate.  The
two consensus rankings were constructed from the complete six-dataset
development pool.  For every prefix length, only the Ridge predictor and its
preprocessing are refitted within the pooled-CV and LODO training partitions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiments.main.readability_model.figures.plot_feature_count_sensitivity import (
    plot_pdf as plot_single_route_pdf,
    write_curve as write_single_route_curve,
)
from experiments.main.readability_model.selection.screen_llm_features import evaluate_features
from src.experiments.registry import COGNASCORE_EMBEDDING_MODELS
from src.methods.readability_model.llm_features.types import DEFAULT_CAUSAL_LM
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.runners.supervised_ridge import load_combined_features


DATASETS = ("mbjp", "buse", "scalabrino", "dorn", "schnappinger", "jetbrains")
DATASET_LABELS = {
    "mbjp": "MBJP",
    "buse": "Buse",
    "scalabrino": "Scalabrino",
    "dorn": "Dorn",
    "schnappinger": "Schnappinger",
    "jetbrains": "JetBrains",
}
ROUTES = {
    "embedding_only": "Embedding-only ranking",
    "llm_extended": "LLM-extended ranking",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--embedding-only-ranking",
        type=Path,
        default=Path(
            "results/experiments/cognascore/llm47_top30_screen/"
            "without_llm_consensus_ranking.csv"
        ),
    )
    parser.add_argument(
        "--llm-extended-ranking",
        type=Path,
        default=Path(
            "results/experiments/cognascore/llm47_top30_screen/"
            "consensus_ranking.csv"
        ),
    )
    parser.add_argument(
        "--embedding-model",
        default=COGNASCORE_EMBEDDING_MODELS[0],
        choices=COGNASCORE_EMBEDDING_MODELS,
    )
    parser.add_argument("--llm-model", default=DEFAULT_CAUSAL_LM)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument(
        "--embedding-root",
        type=Path,
        default=EMBEDDING_FEATURE_ROOT,
    )
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--max-k", type=int, default=30)
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures/diagnostics/ranked_prefix_comparison"),
    )
    return parser.parse_args()


def read_ranking(path: Path, max_k: int) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if "feature" not in (rows[0] if rows else {}):
        raise ValueError(f"Ranking has no feature column: {path}")
    features = [row["feature"] for row in rows]
    if len(features) != len(set(features)):
        raise ValueError(f"Ranking contains duplicate features: {path}")
    if len(features) < max_k:
        raise ValueError(f"Ranking contains only {len(features)} features: {path}")
    return features[:max_k]


def load_frame(args: argparse.Namespace, required_features: list[str]) -> pd.DataFrame:
    frames = [
        load_combined_features(
            dataset,
            args.base_root,
            args.embedding_root,
            required_features,
            llm_feature_root=args.llm_root,
            embedding_model=args.embedding_model,
            llm_model=args.llm_model,
        )
        for dataset in DATASETS
    ]
    return pd.concat(frames, ignore_index=True)


def evaluate_prefixes(
    frame: pd.DataFrame,
    rankings: dict[str, list[str]],
    args: argparse.Namespace,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route, ranking in rankings.items():
        for k in range(1, args.max_k + 1):
            print(f"{ROUTES[route]}: K={k}/{args.max_k}", flush=True)
            result, _ = evaluate_features(
                frame,
                ranking[:k],
                folds=args.folds,
                seed=args.seed,
                alpha=args.ridge_alpha,
            )
            row: dict[str, object] = {
                "route": route,
                "k": k,
                "pooled_average": result["pooled_cv"]["unweighted_mean"],
                "lodo_average": result["lodo"]["unweighted_mean"],
            }
            for dataset in DATASETS:
                row[f"pooled_{dataset}"] = result["pooled_cv"]["datasets"][dataset][
                    "value"
                ]
                row[f"lodo_{dataset}"] = result["lodo"]["datasets"][dataset]["value"]
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def plot_dataset_curves(path: Path, rows: list[dict[str, object]], max_k: int) -> None:
    configure_plotting()
    frame = pd.DataFrame(rows)
    colors = {"embedding_only": "#64748b", "llm_extended": "#0f766e"}
    fig, axes = plt.subplots(2, 3, figsize=(10.8, 6.25), sharex=True)
    for axis, dataset in zip(axes.ravel(), DATASETS, strict=True):
        for route in ROUTES:
            current = frame.loc[frame["route"] == route].sort_values("k")
            axis.plot(
                current["k"],
                current[f"pooled_{dataset}"],
                color=colors[route],
                linewidth=1.6,
                label=ROUTES[route],
            )
        axis.set_title(DATASET_LABELS[dataset], loc="left", fontweight="bold")
        axis.set_xlim(1, max_k)
        axis.set_xticks([1, 5, 10, 15, 20, 25, 30])
        axis.grid(axis="y", color="#e2e8f0", linewidth=0.65)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#94a3b8")
    axes[0, 0].legend(frameon=False, loc="lower right")
    for axis in axes[:, 0]:
        axis.set_ylabel("Pooled 10-fold Spearman")
    fig.supxlabel("Number of consensus-ranked features (K)", y=0.015)
    fig.tight_layout(rect=(0.02, 0.05, 0.995, 0.995), h_pad=1.2, w_pad=1.0)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_average_curves(path: Path, rows: list[dict[str, object]], max_k: int) -> None:
    configure_plotting()
    frame = pd.DataFrame(rows)
    colors = {"embedding_only": "#64748b", "llm_extended": "#0f766e"}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharex=True, sharey=True)
    for axis, metric, title in zip(
        axes,
        ("pooled_average", "lodo_average"),
        ("Pooled 10-fold CV", "Leave-one-dataset-out"),
        strict=True,
    ):
        for route in ROUTES:
            current = frame.loc[frame["route"] == route].sort_values("k")
            axis.plot(
                current["k"],
                current[metric],
                color=colors[route],
                linewidth=1.8,
                label=ROUTES[route],
            )
            best = current.loc[current[metric].idxmax()]
            axis.scatter(best["k"], best[metric], color=colors[route], s=18, zorder=3)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_xlim(1, max_k)
        axis.set_xticks([1, 5, 10, 15, 20, 25, 30])
        axis.grid(axis="y", color="#e2e8f0", linewidth=0.65)
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_color("#94a3b8")
    axes[0].set_ylabel("Unweighted mean Spearman")
    axes[0].legend(frameon=False, loc="lower right")
    fig.supxlabel("Number of consensus-ranked features (K)", y=0.01)
    fig.tight_layout(rect=(0.02, 0.08, 0.995, 0.995), w_pad=1.2)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def write_extended_sensitivity_figure(
    csv_path: Path,
    pdf_path: Path,
    rows: list[dict[str, object]],
    max_k: int,
) -> None:
    """Render the extended route in the established six-panel paper style."""
    extended = [row for row in rows if row["route"] == "llm_extended"]
    curve: list[dict[str, object]] = [
        {
            "k": 0,
            **{dataset: {"value": 0.0} for dataset in DATASETS},
        }
    ]
    for row in extended:
        curve.append(
            {
                "k": int(row["k"]),
                **{
                    dataset: {"value": float(row[f"pooled_{dataset}"])}
                    for dataset in DATASETS
                },
            }
        )
    write_single_route_curve(csv_path, curve)
    plot_single_route_pdf(pdf_path, curve, top_k=23, max_k=max_k)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    if args.max_k < 1:
        raise SystemExit("--max-k must be positive")
    rankings = {
        "embedding_only": read_ranking(args.embedding_only_ranking, args.max_k),
        "llm_extended": read_ranking(args.llm_extended_ranking, args.max_k),
    }
    required = list(dict.fromkeys(rankings["embedding_only"] + rankings["llm_extended"]))
    frame = load_frame(args, required)
    rows = evaluate_prefixes(frame, rankings, args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "ranked_prefix_performance.csv"
    dataset_pdf = args.output_dir / "ranked_prefix_six_datasets.pdf"
    average_pdf = args.output_dir / "ranked_prefix_averages.pdf"
    extended_csv = (
        args.output_dir / "cognascore_llm_feature_count_sensitivity_data.csv"
    )
    extended_pdf = (
        args.output_dir
        / "cognascore_llm_feature_count_sensitivity_six_datasets.pdf"
    )
    metadata_path = args.output_dir / "metadata.json"
    write_csv(csv_path, rows)
    plot_dataset_curves(dataset_pdf, rows, args.max_k)
    plot_average_curves(average_pdf, rows, args.max_k)
    write_extended_sensitivity_figure(
        extended_csv,
        extended_pdf,
        rows,
        args.max_k,
    )
    metadata_path.write_text(
        json.dumps(
            {
                "diagnostic_only": True,
                "note": (
                    "The rankings were estimated on the complete six-dataset "
                    "development pool; the curves refit only the Ridge predictor."
                ),
                "embedding_model": args.embedding_model,
                "llm_model": args.llm_model,
                "datasets": list(DATASETS),
                "folds": args.folds,
                "seed": args.seed,
                "ridge_alpha": args.ridge_alpha,
                "max_k": args.max_k,
                "ranking_files": {
                    "embedding_only": {
                        "path": str(args.embedding_only_ranking),
                        "sha256": sha256(args.embedding_only_ranking),
                    },
                    "llm_extended": {
                        "path": str(args.llm_extended_ranking),
                        "sha256": sha256(args.llm_extended_ranking),
                    },
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {csv_path}")
    print(f"Wrote {dataset_pdf}")
    print(f"Wrote {average_pdf}")
    print(f"Wrote {extended_csv}")
    print(f"Wrote {extended_pdf}")
    print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
