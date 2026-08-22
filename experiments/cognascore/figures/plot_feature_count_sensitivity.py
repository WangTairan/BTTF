"""Plot the complete six-dataset consensus Top-K sensitivity curve.

The script reuses the feature-screening implementation and the already
generated consensus ranking.  It refits the final Ridge model for every
K=1..N, then writes a publication-sized 2x3 vector PDF.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from experiments.cognascore import consensus_selection as consensus
from experiments.cognascore import feature_selection as fs
from src.experiments.registry import DATASETS
from src.methods.cognascore.dataset_io import dataset_output_name
from src.methods.cognascore.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT


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
        "--ranking",
        type=Path,
        default=Path(
            "results/experiments/cognascore/ml_6dataset_5model_consensus24/"
            "cognascore_feature_screen_consensus/five_model/consensus_ranking.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("figures"),
    )
    parser.add_argument(
        "--curve-csv",
        type=Path,
        help="Reuse a previously computed curve CSV instead of refitting all K values.",
    )
    parser.add_argument("--top-k-marker", type=int, default=25)
    parser.add_argument("--max-k", type=int, default=150)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--c", type=float, default=0.08)
    return parser.parse_args()


def make_args(ridge_alpha: float, c: float) -> argparse.Namespace:
    dataset_names = [dataset_output_name(DATASETS[key].path) for key in fs.DEFAULT_DATASET_KEYS]
    return argparse.Namespace(
        base_root=BASE_FEATURE_ROOT,
        embedding_root=EMBEDDING_FEATURE_ROOT,
        continuous_threshold="median",
        drop_middle=0.0,
        drop_middle_scope="all",
        final_embedding_model="nomic-ai/nomic-embed-text-v1.5",
        c=c,
        seed=42,
        ridge_alpha=ridge_alpha,
        select_top=24,
        correlation_threshold=0.9,
        dataset_names=dataset_names,
    )


def load_ranking(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def calculate_curve(
    args: argparse.Namespace,
    ranking: list[dict[str, str]],
) -> list[dict[str, object]]:
    runtime_args = make_args(args.ridge_alpha, args.c)
    dataset_names = runtime_args.dataset_names
    bundle = consensus.load_model_bundle(
        runtime_args,
        dataset_names,
        runtime_args.final_embedding_model,
        selection_datasets=fs.DEFAULT_DATASET_KEYS,
        external_datasets=fs.DEFAULT_DATASET_KEYS,
    )
    max_k = min(len(ranking), len(bundle["feature_names"]))
    rows: list[dict[str, object]] = []
    for k in range(1, max_k + 1):
        try:
            selected, _ = consensus.select_with_correlation_replacement(
                ranking,
                bundle["x"],
                bundle["feature_names"],
                bundle["row_metadata"],
                top_k=k,
                threshold=runtime_args.correlation_threshold,
            )
        except SystemExit:
            # The correlation filter can make the requested K infeasible.  The
            # last feasible K is the complete non-redundant curve.
            break
        indices = np.asarray(
            [bundle["feature_names"].index(name) for name in selected],
            dtype=int,
        )
        model = fs._build_final_model(
            "ridge",
            c=runtime_args.c,
            ridge_alpha=runtime_args.ridge_alpha,
            elasticnet_alpha=0.02,
            elasticnet_l1_ratio=0.2,
            seed=runtime_args.seed,
        )
        fit_mask = bundle["fit_selection_mask"]
        fs._fit_final_model(
            model,
            bundle["x"][fit_mask][:, indices],
            bundle["regression_target"][fit_mask],
            bundle["fit_sample_weight"][fit_mask],
            "ridge",
        )
        prediction = fs._predict_final_model(model, bundle["x"][:, indices], "ridge")
        metrics = fs._report_metrics_by_dataset(bundle["row_metadata"], prediction)
        rows.append({"k": k, **metrics})
    return rows


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


def plot_pdf(path: Path, rows: list[dict[str, object]], top_k: int, max_k: int) -> None:
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
            axis.text(top_k + 2, 0.975, f"K={top_k}", color="#991b1b", fontsize=7.5, va="top")
        finite = np.isfinite(y)
        if np.any(finite):
            best_index = int(np.nanargmax(y))
            axis.scatter([x[best_index]], [y[best_index]], color=marker_color, s=12, zorder=3)
        axis.set_title(DATASET_LABELS[dataset], loc="left", fontweight="bold")
        axis.text(
            0.98,
            0.96,
            "MCC" if dataset == "jetbrains" else "Spearman",
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
        ticks = [0, 1, 5, 10, 25, 50, 100, 150]
        if x[-1] not in ticks:
            ticks.append(int(x[-1]))
        axis.set_xticks(ticks)
        axis.tick_params(axis="x", labelrotation=25, labelsize=7)
        axis.grid(axis="y", color="#e5e7eb", linewidth=0.65)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color("#9ca3af")
        axis.spines["bottom"].set_color("#9ca3af")
    for axis in axes[3:]:
        axis.set_xlabel("Number of consensus-ranked features (K, power scale)")
    for axis in (axes[0], axes[3]):
        axis.set_ylabel("Spearman / MCC")
    fig.tight_layout(rect=(0.02, 0.03, 0.99, 0.98), h_pad=1.35, w_pad=1.0)
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ranking = load_ranking(args.ranking)
    csv_path = args.output_dir / "cognascore_feature_count_sensitivity_data.csv"
    pdf_path = args.output_dir / "cognascore_feature_count_sensitivity_six_datasets.pdf"
    if args.curve_csv:
        rows = read_curve(args.curve_csv)
    else:
        rows = calculate_curve(args, ranking)
    rows = ensure_origin(rows)
    write_curve(csv_path, rows)
    plot_pdf(pdf_path, rows, args.top_k_marker, args.max_k)
    print(f"Wrote {len(rows)} K values to {csv_path}")
    print(f"Wrote figure to {pdf_path}")


if __name__ == "__main__":
    main()
