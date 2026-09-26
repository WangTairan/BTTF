"""Render the retained six-dataset feature-count curve from its CSV data."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


DATASET_ORDER = ("buse", "dorn", "jetbrains", "mbjp", "scalabrino", "schnappinger")
DATASET_LABELS = {
    "buse": "Buse",
    "dorn": "Dorn",
    "jetbrains": "JetBrains",
    "mbjp": "MBJP",
    "scalabrino": "Scalabrino",
    "schnappinger": "Schnappinger",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures/publication"),
    )
    parser.add_argument(
        "--curve-csv",
        type=Path,
        default=Path("figures/data/cognascore_feature_count_sensitivity_data.csv"),
        help="Retained curve CSV to render.",
    )
    parser.add_argument("--top-k-marker", type=int, default=18)
    parser.add_argument("--max-k", type=int, default=150)
    return parser.parse_args()


def write_curve(path: Path, rows: list[dict[str, object]]) -> None:
    columns = ["k"] + [f"{dataset}_value" for dataset in DATASET_ORDER]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "k": row["k"],
                    **{
                        f"{dataset}_value": row.get(dataset, {}).get("value")
                        for dataset in DATASET_ORDER
                    },
                }
            )


def read_curve(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row: dict[str, object] = {"k": int(raw["k"])}
            for dataset in DATASET_ORDER:
                value = raw.get(f"{dataset}_value", "")
                row[dataset] = {"value": float(value) if value else None}
            rows.append(row)
    return rows


def ensure_origin(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Add the defined no-feature reference point (K=0, score=0)."""
    if rows and int(rows[0]["k"]) == 0:
        return rows
    origin: dict[str, object] = {"k": 0}
    for dataset in DATASET_ORDER:
        origin[dataset] = {"value": 0.0}
    return [origin, *rows]


def plot_pdf(
    path: Path,
    rows: list[dict[str, object]],
    top_k: int,
    max_k: int,
    marker_label: str = "Final K",
    show_best: bool = True,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    rows = [row for row in rows if int(row["k"]) <= max_k]
    x = np.asarray([int(row["k"]) for row in rows])
    fig, axes = plt.subplots(2, 3, figsize=(11.2, 6.7), sharex=True, sharey=True)
    axes = axes.ravel()
    line_color = "#155e75"
    marker_color = "#0f766e"
    for axis, dataset in zip(axes, DATASET_ORDER):
        y = np.asarray(
            [
                float(row[dataset]["value"])
                if row.get(dataset, {}).get("value") is not None
                else np.nan
                for row in rows
            ]
        )
        axis.plot(x, y, color=line_color, linewidth=1.35, solid_capstyle="round")
        if top_k <= x[-1]:
            axis.axvline(top_k, color="#b91c1c", linewidth=1.0, linestyle=(0, (4, 3)), zorder=0)
            label_x = top_k - 0.6 if max_k <= 30 else top_k + 2
            axis.text(
                label_x,
                0.975,
                f"{marker_label}={top_k}",
                color="#991b1b",
                fontsize=7.5,
                ha="right" if max_k <= 30 else "left",
                va="top",
            )
        finite = np.isfinite(y)
        if show_best and np.any(finite):
            best_index = int(np.nanargmax(y))
            axis.scatter([x[best_index]], [y[best_index]], color=marker_color, s=12, zorder=3)
        axis.set_title(
            DATASET_LABELS[dataset],
            loc="left",
            fontweight="bold",
            pad=7,
        )
        if max_k > 30:
            axis.text(
                0.98,
                0.96,
                "Spearman",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontsize=8,
                color="#4b5563",
            )
        axis.set_xlim(0, max_k)
        # A gentle power scale expands the first features only slightly,
        # avoiding the excessive distortion of log and square-root axes.
        axis.set_xscale(
            "function",
            functions=(
                lambda value: np.sign(value) * np.abs(value) ** 0.8,
                lambda value: np.sign(value) * np.abs(value) ** 1.25,
            ),
        )
        axis.set_ylim(0.0, 1.0)
        if max_k <= 30:
            ticks = [tick for tick in (0, 5, 10, 15, 20, 25, 30) if tick <= max_k]
        elif max_k <= 50:
            ticks = [tick for tick in (0, 5, 10, 20, 30, 40, 50) if tick <= max_k]
        else:
            ticks = [tick for tick in (0, 5, 10, 20, 50, 100, 150) if tick <= max_k]
        axis.set_xticks(ticks)
        axis.tick_params(axis="x", labelrotation=25, labelsize=7)
        axis.grid(axis="y", color="#e5e7eb", linewidth=0.65)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color("#9ca3af")
        axis.spines["bottom"].set_color("#9ca3af")
    for axis in (axes[0], axes[3]):
        axis.set_ylabel("Spearman")
    fig.supxlabel("Number of consensus-ranked features (K, power scale)", y=0.015)
    fig.tight_layout(rect=(0.02, 0.05, 0.99, 0.93), h_pad=1.35, w_pad=1.0)
    fig.subplots_adjust(top=0.88)
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "cognascore_feature_count_sensitivity_data.csv"
    pdf_path = args.output_dir / "cognascore_feature_count_sensitivity_six_datasets.pdf"
    rows = read_curve(args.curve_csv)
    rows = ensure_origin(rows)
    write_curve(csv_path, rows)
    plot_pdf(pdf_path, rows, args.top_k_marker, args.max_k)
    print(f"Wrote {len(rows)} K values to {csv_path}")
    print(f"Wrote figure to {pdf_path}")


if __name__ == "__main__":
    main()
