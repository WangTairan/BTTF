"""Plot normalized human-label distributions for the six core datasets.

Run from the repository root:

    python figures/plot_readability_label_distributions.py

The five rating datasets are normalized with their documented rating scales,
not their observed minima and maxima. JetBrains uses its retained fraction of
readable votes rather than the majority-vote binary label. Higher values always
mean more readable code.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS


@dataclass(frozen=True)
class DatasetDisplay:
    key: str
    label: str
    color: str
    scale_min: float
    scale_max: float
    score_source: str = "readability_score"


DATASET_DISPLAYS = (
    DatasetDisplay("mbjp", "MBJP", "#4477AA", 1.0, 5.0),
    DatasetDisplay("buse", "Buse", "#EE6677", 1.0, 5.0),
    DatasetDisplay("scalabrino", "Scalabrino", "#228833", 1.0, 5.0),
    DatasetDisplay("dorn", "Dorn", "#CCBB44", 1.0, 5.0),
    DatasetDisplay("schnappinger", "Schnappinger", "#66CCEE", 1.0, 4.0),
    DatasetDisplay(
        "jetbrains",
        "JetBrains",
        "#AA3377",
        0.0,
        1.0,
        score_source="human_readable_vote_fraction",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("figures/readability_label_distributions.pdf"),
    )
    parser.add_argument(
        "--data-output",
        type=Path,
        default=Path("figures/readability_label_distributions_data.csv"),
    )
    parser.add_argument("--bins", type=int, default=20)
    return parser.parse_args()


def normalized_scores(display: DatasetDisplay) -> list[tuple[str, float, float]]:
    items = load_code_dataset(DATASETS[display.key].path)
    denominator = display.scale_max - display.scale_min
    if denominator <= 0:
        raise ValueError(f"Invalid label scale for {display.key}")

    rows: list[tuple[str, float, float]] = []
    for item in items:
        if display.score_source == "human_readable_vote_fraction":
            raw_score = item.metadata.get("human_readable_vote_fraction")
        else:
            raw_score = item.readability_score
        if raw_score is None or not math.isfinite(float(raw_score)):
            continue
        raw = float(raw_score)
        normalized = (raw - display.scale_min) / denominator
        # Probability-derived expected ratings may exceed an endpoint by a few
        # parts per million because the published class probabilities are
        # rounded independently.
        if normalized < -1e-5 or normalized > 1.0 + 1e-5:
            raise ValueError(
                f"{display.key} score {raw} falls outside documented scale "
                f"[{display.scale_min}, {display.scale_max}]"
            )
        rows.append((item.task_id, raw, min(1.0, max(0.0, normalized))))
    if not rows:
        raise ValueError(f"No finite readability labels for {display.key}")
    return rows


def load_all_scores() -> dict[str, list[tuple[str, float, float]]]:
    return {display.key: normalized_scores(display) for display in DATASET_DISPLAYS}


def write_data(
    path: Path,
    score_rows: dict[str, list[tuple[str, float, float]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    displays = {display.key: display for display in DATASET_DISPLAYS}
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "dataset",
                "task_id",
                "raw_score",
                "normalized_score",
                "scale_min",
                "scale_max",
                "score_source",
            ),
        )
        writer.writeheader()
        for dataset, rows in score_rows.items():
            display = displays[dataset]
            for task_id, raw, normalized in rows:
                writer.writerow(
                    {
                        "dataset": dataset,
                        "task_id": task_id,
                        "raw_score": raw,
                        "normalized_score": normalized,
                        "scale_min": display.scale_min,
                        "scale_max": display.scale_max,
                        "score_source": display.score_source,
                    }
                )


def plot_distributions(
    path: Path,
    score_rows: dict[str, list[tuple[str, float, float]]],
    bins: int,
) -> None:
    if bins < 5:
        raise ValueError("--bins must be at least 5")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    edges = np.linspace(0.0, 1.0, bins + 1)
    fig, axes = plt.subplots(2, 3, figsize=(10.6, 5.8), sharex=True, sharey=True)
    axes = axes.ravel()
    for axis, display in zip(axes, DATASET_DISPLAYS):
        values = np.asarray([row[2] for row in score_rows[display.key]], dtype=float)
        weights = np.full(values.shape, 1.0 / len(values), dtype=float)
        axis.hist(
            values,
            bins=edges,
            weights=weights,
            color=display.color,
            alpha=0.76,
            edgecolor="white",
            linewidth=0.45,
        )
        median = float(np.median(values))
        axis.axvline(median, color=display.color, linewidth=1.5, linestyle=(0, (4, 2)))
        axis.set_title(display.label, loc="left", fontweight="bold", color=display.color)
        axis.text(
            0.98,
            0.94,
            f"n={len(values)}   median={median:.2f}",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=8,
            color="#4b5563",
        )
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(bottom=0.0)
        axis.set_xticks(np.linspace(0.0, 1.0, 6))
        axis.grid(axis="y", color="#e5e7eb", linewidth=0.6)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color("#9ca3af")
        axis.spines["bottom"].set_color("#9ca3af")

    for axis in axes[3:]:
        axis.set_xlabel("Normalized human readability label")
    for axis in (axes[0], axes[3]):
        axis.set_ylabel("Fraction of samples per bin")
    fig.tight_layout(h_pad=1.25, w_pad=1.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    score_rows = load_all_scores()
    write_data(args.data_output, score_rows)
    plot_distributions(args.output, score_rows, args.bins)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.data_output}")


if __name__ == "__main__":
    main()
