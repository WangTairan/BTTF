"""One six-dataset curve for a fixed three-causal-LM consensus ranking.

At each feature count, each causal LM supplies its own feature values and
Ridge fit. The plotted dataset value is the mean of the three Spearman
correlations, not a prediction ensemble. Ranking is never recomputed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.main.readability_model.figures.plot_feature_count_sensitivity import (
    DATASET_ORDER,
    ensure_origin,
    plot_pdf,
    write_curve,
)
from experiments.main.readability_model.selection.screen_llm_features import (
    evaluate_features,
    load_matrices,
)
from src.experiments.registry import COGNASCORE_EMBEDDING_MODELS
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
)


CAUSAL_LMS = (
    "Qwen/Qwen2.5-Coder-0.5B",
    "deepseek-ai/deepseek-coder-1.3b-base",
    "infly/OpenCoder-1.5B-Base",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranking", type=Path, required=True)
    parser.add_argument(
        "--figure-output-dir", type=Path, default=Path("figures/publication")
    )
    parser.add_argument(
        "--data-output-dir", type=Path, default=Path("figures/data")
    )
    parser.add_argument("--max-k", type=int, default=150)
    parser.add_argument("--marker", type=int, default=11)
    args = parser.parse_args()

    ranking = pd.read_csv(args.ranking).sort_values("rank")
    features = ranking["feature"].tolist()
    if len(features) != len(set(features)) or not 1 <= args.max_k <= len(features):
        raise ValueError("Invalid fixed consensus ranking or feature-count limit")

    frames = []
    for causal_lm in CAUSAL_LMS:
        loader_args = argparse.Namespace(
            embedding_models=(COGNASCORE_EMBEDDING_MODELS[0],),
            llm_model=causal_lm,
            base_root=BASE_FEATURE_ROOT,
            embedding_root=EMBEDDING_FEATURE_ROOT,
            llm_root=LLM_FEATURE_ROOT,
        )
        matrices, eligible, _, _ = load_matrices(loader_args)
        if not set(features).issubset(eligible):
            raise ValueError(f"Ranking includes ineligible features for {causal_lm}")
        frames.append(matrices[COGNASCORE_EMBEDDING_MODELS[0]])

    rows: list[dict[str, object]] = []
    for k in range(1, args.max_k + 1):
        metrics = [
            evaluate_features(frame, features[:k], folds=10, seed=42, alpha=200)[0]
            for frame in frames
        ]
        row: dict[str, object] = {"k": k}
        for dataset in DATASET_ORDER:
            row[dataset] = {
                "value": float(np.mean([
                    metric["pooled_cv"]["datasets"][dataset]["value"]
                    for metric in metrics
                ]))
            }
        rows.append(row)
        if k % 10 == 0 or k == args.max_k:
            print(f"Evaluated K={k}/{args.max_k}", flush=True)

    args.figure_output_dir.mkdir(parents=True, exist_ok=True)
    args.data_output_dir.mkdir(parents=True, exist_ok=True)
    stem = "three_llm_consensus_feature_count_sensitivity_six_datasets"
    csv_path = args.data_output_dir / f"{stem}.csv"
    pdf_path = args.figure_output_dir / f"{stem}.pdf"
    rows = ensure_origin(rows)
    write_curve(csv_path, rows)
    plot_pdf(pdf_path, rows, args.marker, args.max_k, marker_label="K", show_best=False)
    print(f"Wrote {csv_path} and {pdf_path}", flush=True)


if __name__ == "__main__":
    main()
