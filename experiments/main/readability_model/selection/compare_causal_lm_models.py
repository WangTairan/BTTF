"""Compare separate and consensus screens for two or three causal LMs.

This is a post-screen diagnostic. It never concatenates causal-LM
representations or changes the frozen model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

from experiments.main.readability_model.selection.screen_llm_features import (
    consensus_ranking,
    correlation_selection,
    evaluate_features,
    load_matrices,
)
from src.experiments.registry import READABILITY_MODEL_EMBEDDINGS
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.results import model_slug
from src.methods.readability_model.runners.supervised_ridge import (
    fit_ridge,
    ridge_coefficients,
)


def checked_screen(path: Path, model: str, checksums: dict[str, str]):
    payload = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    if payload["llm_model"] != model or payload["parameters"]["stability_rounds"] != 200:
        raise ValueError(f"Incompatible screening configuration: {path}")
    if payload["embedding_models"] != list(READABILITY_MODEL_EMBEDDINGS):
        raise ValueError(f"Incompatible embedding model order: {path}")
    for filename, expected in payload["input_csv_sha256"].items():
        if checksums.get(filename) != expected:
            raise ValueError(f"Screening input changed: {filename}")
    rankings = {}
    for embedding_model in READABILITY_MODEL_EMBEDDINGS:
        table = path / "per_model" / model_slug(embedding_model) / "ranking.csv"
        rankings[embedding_model] = pd.read_csv(table).to_dict("records")
    return payload, rankings


def joint_nonredundant(ranking, frames, top: int, threshold: float):
    """Reject a pair if redundant under any causal-LM instantiation."""
    features = [row["feature"] for row in ranking]
    correlations = []
    for frame in frames:
        x = SimpleImputer(strategy="median", keep_empty_features=True).fit_transform(
            frame[features]
        )
        data = pd.DataFrame(x, columns=features)
        correlations.append((data.corr(), data.corr(method="spearman")))
    selected, rejected = [], []
    for row in ranking:
        name = row["feature"]
        conflicts = []
        for prior in selected:
            for model_index, (pearson, spearman) in enumerate(correlations):
                p, s = pearson.loc[name, prior], spearman.loc[name, prior]
                if max(abs(p) if np.isfinite(p) else 0, abs(s) if np.isfinite(s) else 0) > threshold:
                    conflicts.append({"prior": prior, "model_index": model_index, "pearson": float(p), "spearman": float(s)})
        if conflicts:
            rejected.append({"feature": name, "rank": row["rank"], "conflicts": conflicts})
        else:
            selected.append(name)
            if len(selected) == top:
                break
    if len(selected) != top:
        raise ValueError(f"Only {len(selected)} nonredundant candidates")
    return selected, rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qwen-screen", type=Path, required=True)
    parser.add_argument("--deepseek-screen", type=Path, required=True)
    parser.add_argument("--opencoder-screen", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top", type=int, default=23)
    args = parser.parse_args()
    models = {
        "qwen": "Qwen/Qwen2.5-Coder-0.5B",
        "deepseek": "deepseek-ai/deepseek-coder-1.3b-base",
    }
    screen_paths = {"qwen": args.qwen_screen, "deepseek": args.deepseek_screen}
    if args.opencoder_screen is not None:
        models["opencoder"] = "infly/OpenCoder-1.5B-Base"
        screen_paths["opencoder"] = args.opencoder_screen
    matrices, rankings = {}, {}
    for name, model in models.items():
        loader_args = argparse.Namespace(
            embedding_models=tuple(READABILITY_MODEL_EMBEDDINGS),
            llm_model=model,
            base_root=BASE_FEATURE_ROOT,
            embedding_root=EMBEDDING_FEATURE_ROOT,
            llm_root=LLM_FEATURE_ROOT,
        )
        matrices[name], features, _, checksums = load_matrices(loader_args)
        _, rankings[name] = checked_screen(screen_paths[name], model, checksums)
        if set(features) != {row["feature"] for row in next(iter(rankings[name].values()))}:
            raise ValueError(f"Candidate inventory changed for {model}")
    reference_model = READABILITY_MODEL_EMBEDDINGS[0]
    references = {name: values[reference_model] for name, values in matrices.items()}
    single_rankings = {name: consensus_ranking(values) for name, values in rankings.items()}
    def rank_across(names):
        # Each LLM contributes five independent embedding-model screens.
        return consensus_ranking({
            f"{llm}/{embedding}": ranking
            for llm in names
            for embedding, ranking in rankings[llm].items()
        })

    joint_rankings = {"joint": rank_across(tuple(models))}
    if args.opencoder_screen is not None:
        joint_rankings["qwen_deepseek"] = rank_across(("qwen", "deepseek"))
    selected = {}
    for name, ranking in single_rankings.items():
        selected[name], _ = correlation_selection(
            ranking, references[name], [row["feature"] for row in ranking],
            top=args.top, threshold=0.9,
        )
    rejected = {}
    for name, ranking in joint_rankings.items():
        participating = ("qwen", "deepseek") if name == "qwen_deepseek" else tuple(models)
        selected[name], rejected[name] = joint_nonredundant(
            ranking, [references[llm] for llm in participating], args.top, 0.9
        )
    args.output.mkdir(parents=True, exist_ok=True)
    for name, ranking in {**single_rankings, **joint_rankings}.items():
        pd.DataFrame(ranking).to_csv(args.output / f"{name}_ranking.csv", index=False)
    rows, signs = [], []
    for selection_name, features in selected.items():
        for llm_name, frame in references.items():
            metrics, _ = evaluate_features(frame, features, folds=10, seed=42, alpha=200)
            model = fit_ridge(frame, np.ones(len(frame), dtype=bool), 200, features)
            coefficients = ridge_coefficients(model, features)
            rows.append({
                "selection": selection_name,
                "predictor_llm": llm_name,
                "pooled_mean": metrics["pooled_cv"]["unweighted_mean"],
                "lodo_mean": metrics["lodo"]["unweighted_mean"],
                **{f"pooled_{name}": data["value"] for name, data in metrics["pooled_cv"]["datasets"].items()},
            })
            signs.extend({"selection": selection_name, "predictor_llm": llm_name, "feature": feature, "coefficient": coefficient} for feature, coefficient in coefficients.items())
    pd.DataFrame(rows).to_csv(args.output / "evaluation.csv", index=False)
    pd.DataFrame(signs).to_csv(args.output / "ridge_coefficients.csv", index=False)
    (args.output / "selected.json").write_text(json.dumps({
        "selected": selected,
        "joint_correlation_rejected": rejected,
        "screen_sha256": {name: hashlib.sha256((screen_paths[name] / "summary.json").read_bytes()).hexdigest() for name in models},
        "note": "Consensus ranks causal-LM feature definitions across five embedding instantiations per LLM; no feature matrices are concatenated. CV/LODO refit Ridge only after full-pool feature ranking.",
    }, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
