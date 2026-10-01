"""Screen content-aware comment candidates in the complete 15-model grid.

This supplementary experiment changes exactly one element of the frozen
selection procedure: six content-conditioned comment-BPB means are appended
to the 228 eligible candidates.  The six human-rated datasets, three causal
code LMs, five embedding models, stability-selection parameters, and consensus
ordering are otherwise unchanged.  Constructed interference data are never
loaded.  Existing token-loss traces are reaggregated; no LM inference occurs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd

from experiments.main.readability_model.selection.screen_llm_features import (
    consensus_ranking,
    load_matrices,
    stability_ranking,
)
from experiments.supplementary.comment_validity.comment_content_groups import (
    CLASSIFIER_VERSION,
    GROUPS,
    PREFIX,
    attach,
    derive_statistics,
)
from src.experiments.registry import READABILITY_MODEL_EMBEDDINGS
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
    LLM_SURPRISAL_CACHE_ROOT,
)
from src.methods.readability_model.results import model_slug


CAUSAL_LMS = (
    "Qwen/Qwen2.5-Coder-0.5B",
    "deepseek-ai/deepseek-coder-1.3b-base",
    "infly/OpenCoder-1.5B-Base",
)
CONTENT_FEATURES = tuple(PREFIX + group + "__bpb_mean" for group in GROUPS)
FROZEN_RANKING = Path(
    "experiments/main/readability_model/configs/evidence/"
    "consensus11_three_llm_full_ranking.csv"
)

# The complete frozen ranking predates the paper-facing terminology cleanup.
# These are definition-preserving aliases, not candidate substitutions.
FROZEN_NAME_ALIASES = {
    "embedding__all__hdbscan_cluster_type_entropy_mean": "embedding__all__hdbscan_pattern_mixing",
    "embedding__all__hdbscan_noise_ratio": "embedding__all__hdbscan_unclustered_ratio",
    "embedding__only_identifier__hdbscan_noise_ratio": "embedding__only_identifier__hdbscan_unclustered_ratio",
    "embedding__semantic_core__hdbscan_cluster_type_entropy_mean": "embedding__semantic_core__hdbscan_pattern_mixing",
    "embedding__semantic_core__hdbscan_noise_ratio": "embedding__semantic_core__hdbscan_unclustered_ratio",
    "embedding__structural_core__hdbscan_cluster_type_entropy_mean": "embedding__structural_core__hdbscan_pattern_mixing",
    "embedding__structural_core__hdbscan_noise_ratio": "embedding__structural_core__hdbscan_unclustered_ratio",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete_global_trace(path: Path, required_sources: int) -> tuple[str, int]:
    """Choose the unique cached global trace covering the complete corpus."""
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT trace_sha256, COUNT(DISTINCT source_sha256) "
            "FROM trace_windows WHERE kind='global' GROUP BY trace_sha256"
        ).fetchall()
    finally:
        connection.close()
    complete = [(fingerprint, count) for fingerprint, count in rows if count >= required_sources]
    if len(complete) != 1:
        raise ValueError(f"Expected one complete global trace in {path}, found {complete}")
    return complete[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/experiments/readability_model/comment_content_candidate_screen"
        ),
    )
    parser.add_argument("--stability-rounds", type=int, default=200)
    parser.add_argument("--sample-fraction", type=float, default=0.7)
    parser.add_argument("--c", type=float, default=0.08)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reuse-statistics", action="store_true")
    args = parser.parse_args()
    if args.stability_rounds < 1 or not 0 < args.sample_fraction <= 1 or args.c <= 0:
        raise ValueError("Invalid stability-selection parameters")

    frozen = pd.read_csv(FROZEN_RANKING)
    frozen_features = [
        FROZEN_NAME_ALIASES.get(name, name) for name in frozen["feature"].tolist()
    ]
    if len(frozen_features) != 228 or frozen["rank"].tolist() != list(range(1, 229)):
        raise ValueError("Frozen 228-candidate ranking is not the expected artifact")

    args.output.mkdir(parents=True, exist_ok=True)
    all_rankings: dict[str, list[dict]] = {}
    input_hashes: dict[str, str] = {str(FROZEN_RANKING): file_sha256(FROZEN_RANKING)}
    coverage: dict[str, dict] = {}

    for causal_lm in CAUSAL_LMS:
        loader = argparse.Namespace(
            embedding_models=tuple(READABILITY_MODEL_EMBEDDINGS),
            llm_model=causal_lm,
            base_root=BASE_FEATURE_ROOT,
            embedding_root=EMBEDDING_FEATURE_ROOT,
            llm_root=LLM_FEATURE_ROOT,
        )
        matrices, eligible, exclusions, checksums = load_matrices(loader)
        if set(eligible) != set(frozen_features):
            missing = sorted(set(frozen_features) - set(eligible))
            added = sorted(set(eligible) - set(frozen_features))
            raise ValueError(
                f"Candidate inventory changed for {causal_lm}: missing={missing}, added={added}"
            )
        input_hashes.update(checksums)

        model_dir = args.output / model_slug(causal_lm)
        model_dir.mkdir(parents=True, exist_ok=True)
        statistics_path = model_dir / "comment_content_statistics.csv"
        occurrences_path = model_dir / "comment_occurrences.csv"
        trace_path = LLM_SURPRISAL_CACHE_ROOT / model_slug(causal_lm) / "traces.sqlite"
        if not trace_path.exists():
            raise FileNotFoundError(trace_path)
        input_hashes[str(trace_path)] = file_sha256(trace_path)
        reference = matrices[READABILITY_MODEL_EMBEDDINGS[0]]

        trace_fingerprint, trace_source_count = complete_global_trace(
            trace_path, len(reference)
        )

        args.llm_model = causal_lm
        args.llm_root = LLM_FEATURE_ROOT
        args.cache_root = LLM_SURPRISAL_CACHE_ROOT
        args.trace_sha256_override = trace_fingerprint
        if args.reuse_statistics:
            statistics = pd.read_csv(statistics_path)
            if set(CONTENT_FEATURES) - set(statistics):
                raise ValueError(f"Incomplete reused statistics: {statistics_path}")
        else:
            statistics, occurrences = derive_statistics(reference, args)
            statistics.to_csv(statistics_path, index=False)
            occurrences.to_csv(occurrences_path, index=False)

        observed = {
            name: int(statistics[name].notna().sum()) for name in CONTENT_FEATURES
        }
        coverage[causal_lm] = {
            "observed_samples": observed,
            "sample_count": len(statistics),
            "trace_sha256": trace_fingerprint,
            "trace_source_count": trace_source_count,
        }
        candidates = eligible + list(CONTENT_FEATURES)
        if len(candidates) != 234 or len(set(candidates)) != 234:
            raise ValueError("Expected 228 original plus six new candidates")

        for embedding_model, matrix in matrices.items():
            frame = attach(matrix, statistics)
            pair = f"{causal_lm}::{embedding_model}"
            print(f"Screening {pair}: {len(candidates)} candidates", flush=True)
            ranking = stability_ranking(
                frame,
                candidates,
                c=args.c,
                rounds=args.stability_rounds,
                fraction=args.sample_fraction,
                seed=args.seed,
            )
            all_rankings[pair] = ranking
            pair_dir = model_dir / "per_embedding" / model_slug(embedding_model)
            pair_dir.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(ranking).to_csv(pair_dir / "ranking.csv", index=False)

    consensus = consensus_ranking(all_rankings)
    consensus_frame = pd.DataFrame(consensus)
    consensus_frame.to_csv(args.output / "consensus_ranking.csv", index=False)
    new_top11 = consensus_frame.head(11)["feature"].tolist()
    old_top11 = [
        FROZEN_NAME_ALIASES.get(name, name)
        for name in frozen.head(11)["feature"].tolist()
    ]
    comment_rows = consensus_frame[
        consensus_frame["feature"].isin(CONTENT_FEATURES)
    ].sort_values("rank")
    comment_rows.to_csv(args.output / "comment_candidate_ranks.csv", index=False)

    summary = {
        "experiment": "content-aware comment candidate extension",
        "question": "Do content-conditioned comment predictability features enter the fixed Top-11 budget under the original 15-model consensus screen?",
        "datasets": ["mbjp", "buse", "scalabrino", "dorn", "schnappinger", "jetbrains"],
        "causal_language_models": list(CAUSAL_LMS),
        "embedding_models": list(READABILITY_MODEL_EMBEDDINGS),
        "pairing_count": len(all_rankings),
        "original_candidate_count": 228,
        "added_candidate_count": 6,
        "candidate_count": 234,
        "added_features": list(CONTENT_FEATURES),
        "classifier_version": CLASSIFIER_VERSION,
        "parameters": {
            "c": args.c,
            "stability_rounds": args.stability_rounds,
            "sample_fraction": args.sample_fraction,
            "seed": args.seed,
        },
        "selection_rule": "first 11 positions of the 15-pair canonical-feature consensus ranking",
        "constructed_datasets_used": False,
        "language_model_inference_performed": False,
        "old_top11": old_top11,
        "new_top11": new_top11,
        "top11_members_unchanged": set(new_top11) == set(old_top11),
        "top11_order_unchanged": new_top11 == old_top11,
        "added_feature_in_top11": bool(set(new_top11) & set(CONTENT_FEATURES)),
        "comment_candidate_results": comment_rows.to_dict("records"),
        "coverage": coverage,
        "family_counts": dict(Counter(row["family"] for row in consensus)),
        "input_sha256": input_hashes,
        "definition_preserving_frozen_name_aliases": FROZEN_NAME_ALIASES,
        "interpretation_guardrail": "The experiment tests selection support for six content-conditioned comment-BPB candidates. It does not establish that comments are unimportant or measure causal comment quality.",
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(comment_rows[["rank", "feature", "active_model_count", "mean_selection_frequency"]].to_string(index=False), flush=True)
    print(
        json.dumps(
            {
                "top11_members_unchanged": summary["top11_members_unchanged"],
                "top11_order_unchanged": summary["top11_order_unchanged"],
                "added_feature_in_top11": summary["added_feature_in_top11"],
                "new_top11": new_top11,
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
