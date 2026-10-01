"""Screen base, embedding and causal-LM candidates without changing frozen models.

Five embedding matrices are ranked independently; they are never concatenated.
The shared causal-LM columns participate in each fit. Candidate names, not
embedding vectors, are aggregated into a consensus ranking. Predictor-only
CV/LODO diagnostics use this fixed ranking and do not drive its construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from packaging.version import Version
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from experiments.main.readability_model.evaluation.cross_validate_fixed import (
    DEFAULT_DATASETS,
    fold_assignments,
)
from experiments.main.readability_model.evaluation.metrics import unweighted_spearman_average
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS, READABILITY_MODEL_EMBEDDINGS
from src.experiments.statistics import spearman
from src.methods.readability_model.dataset_io import item_source_sha256
from src.methods.readability_model.feature_schema import feature_family, namespaced_feature
from src.methods.readability_model.llm_features.inventory import (
    LLM_FEATURE_BUILD_VERSION,
    LLM_FEATURE_NAMES,
)
from src.methods.readability_model.llm_features.types import DEFAULT_CAUSAL_LM
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
    LLM_FEATURE_ROOT,
)
from src.methods.readability_model.results import model_slug
from src.methods.readability_model.runners.supervised_ridge import (
    SELECTED_FEATURES,
    dataset_balanced_sample_weight,
    fit_ridge,
)

FROZEN_CONFIG = Path(
    "experiments/main/readability_model/configs/consensus18_6dataset_sampled_margin.json"
)
CORE_DATASETS = tuple(DEFAULT_DATASETS)
NONZERO_EPSILON = 1e-12


def load_table(path, prefix, expected, *, dataset, llm=False):
    """Require a current source hash and an exact identity/label match."""
    metadata = json.loads(path.with_name("metadata.json").read_text(encoding="utf-8"))
    frame = pd.read_csv(path)
    identity = {"dataset", "task_id", "readability_score"}
    if (
        not identity.issubset(frame.columns)
        or frame.duplicated(["dataset", "task_id"]).any()
    ):
        raise ValueError(f"Invalid/duplicate feature identities: {path}")
    frame = frame.set_index("task_id")
    if set(frame.index) != set(expected):
        raise ValueError(f"Feature identities differ from the current dataset: {path}")
    frame = frame.loc[list(expected)].copy().reset_index()
    if llm:
        if not metadata.get("complete") or metadata.get("feature_count") != len(
            LLM_FEATURE_NAMES
        ):
            raise ValueError(
                f"The {len(LLM_FEATURE_NAMES)}-feature LLM table is incomplete: {path}"
            )
        if (
            metadata["configuration"]["feature_build_version"]
            != LLM_FEATURE_BUILD_VERSION
        ):
            raise ValueError(f"Outdated LLM feature build: {path}")
        if set(frame.columns) - identity != set(LLM_FEATURE_NAMES):
            raise ValueError(f"Unexpected LLM feature inventory: {path}")
        hashes = {row["task_id"]: row["source_sha256"] for row in metadata["rows"]}
    else:
        hashes = metadata["source_sha256_by_task"]
    for row in frame.itertuples(index=False):
        item = expected[row.task_id]
        if row.dataset != dataset:
            raise ValueError(f"Wrong dataset namespace for {row.task_id}: {path}")
        if hashes.get(row.task_id) != item_source_sha256(item):
            raise ValueError(f"Outdated source content for {row.task_id}: {path}")
        if item.readability_score is None:
            if not pd.isna(row.readability_score):
                raise ValueError(f"Invented readability label for {row.task_id}: {path}")
        elif not np.isclose(
            float(row.readability_score),
            float(item.readability_score),
            rtol=0,
            atol=1e-12,
        ):
            raise ValueError(f"Outdated readability label for {row.task_id}: {path}")
    frame = frame.rename(
        columns={
            name: namespaced_feature(prefix, name)
            for name in frame
            if name not in identity
        }
    )
    values = frame.drop(columns=list(identity)).to_numpy(float)
    if np.isinf(values).any():
        raise ValueError(f"Infinite candidate feature value: {path}")
    return frame


def load_matrices(args):
    matrices = {model: [] for model in args.embedding_models}
    checksums = {}
    base_slug, llm_slug = (
        model_slug(READABILITY_MODEL_EMBEDDINGS[0]),
        model_slug(args.llm_model),
    )
    for dataset in CORE_DATASETS:
        items = load_code_dataset(DATASETS[dataset].path)
        expected = {item.task_id: item for item in items}
        if len(expected) != len(items):
            raise ValueError(f"Duplicate source tasks in {dataset}")
        paths = {
            "base": args.base_root / dataset / base_slug / "features.csv",
            "llm": args.llm_root / dataset / llm_slug / "features.csv",
        }
        base = load_table(paths["base"], "base", expected, dataset=dataset)
        llm = load_table(paths["llm"], "llm", expected, dataset=dataset, llm=True)
        shared = base.merge(
            llm.drop(columns="readability_score"),
            on=["dataset", "task_id"],
            validate="one_to_one",
        )
        for model in args.embedding_models:
            path = args.embedding_root / dataset / model_slug(model) / "features.csv"
            embedding = load_table(path, "embedding", expected, dataset=dataset)
            merged = shared.merge(
                embedding.drop(columns="readability_score"),
                on=["dataset", "task_id"],
                validate="one_to_one",
            )
            matrices[model].append(merged)
            paths[model] = path
        for path in paths.values():
            checksums[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"Validated {dataset}: {len(items)} rows", flush=True)
    matrices = {
        model: pd.concat(frames, ignore_index=True)
        for model, frames in matrices.items()
    }
    inventory = None
    for frame in matrices.values():
        current = set(frame) - {"dataset", "task_id", "readability_score"}
        if inventory is not None and current != inventory:
            raise ValueError("Embedding-model candidate schemas differ")
        inventory = current
    config = json.loads(FROZEN_CONFIG.read_text(encoding="utf-8"))
    exclusions = {
        name
        for group in config["selection_evidence"]["theory_driven_exclusions"].values()
        for name in group["features"]
    }
    features = sorted(inventory - exclusions)
    for name in features:
        feature_family(name)
        if any(
            term in name.lower()
            for term in ("__dbscan", "graph__", "generalized_score", "supervised_score")
        ):
            raise ValueError(f"Unexpected legacy/model-output candidate: {name}")
    return matrices, features, sorted(exclusions), checksums


def logistic_model(c, seed):
    # Explicit API adaptation: both branches request L1, never a default L2 fit.
    penalty = (
        {"l1_ratio": 1.0}
        if Version(sklearn.__version__) >= Version("1.8")
        else {"penalty": "l1"}
    )
    return make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(
            C=c,
            solver="liblinear",
            class_weight="balanced",
            max_iter=5000,
            random_state=seed,
            **penalty,
        ),
    )


def binary_targets(frame):
    labels = frame["readability_score"].to_numpy(float)
    if not np.isfinite(labels).all():
        raise ValueError("Screening requires finite readability labels")
    result = np.empty(len(frame), dtype=int)
    for indices in frame.groupby("dataset", sort=False).indices.values():
        values = labels[indices]
        result[indices] = (values >= np.median(values)).astype(int)
        if len(np.unique(result[indices])) != 2:
            raise ValueError("Median binarization produced a single-class dataset")
    return result


def stability_ranking(frame, features, *, c, rounds, fraction, seed,
                      feature_transform=None):
    """Rank features; optional measurement calibration sees only fit rows.

    feature_transform returns a frame with the requested columns. It is called
    separately for the complete fit and each subsample, before the usual
    training-only imputer/scaler. Readability targets and sampling are unchanged.
    """
    x, y = frame[features].to_numpy(float), binary_targets(frame)
    weights = dataset_balanced_sample_weight(frame, np.ones(len(frame), dtype=bool))
    groups = list(frame.groupby("dataset", sort=False).indices.values())
    rng = np.random.default_rng(seed)
    counts, magnitudes = np.zeros(len(features)), np.zeros(len(features))

    def coefficients(indices, model_seed):
        if len(np.unique(y[indices])) != 2:
            raise ValueError("Stability subsample has only one class")
        model = logistic_model(c, model_seed)
        fit_x = x[indices]
        if feature_transform is not None:
            fit_frame = frame.iloc[indices].reset_index(drop=True)
            transformed = feature_transform(fit_frame)
            identity = ["dataset", "task_id"]
            if len(transformed) != len(indices) or not transformed[identity].equals(fit_frame[identity]):
                raise ValueError("Measurement transform changed fit-row identity/order")
            fit_x = transformed[features].to_numpy(float)
            if np.isinf(fit_x).any():
                raise ValueError("Infinite transformed screening feature")
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(
                fit_x,
                y[indices],
                logisticregression__sample_weight=weights[indices],
            )
        return model.named_steps["logisticregression"].coef_[0]

    full = coefficients(np.arange(len(frame)), seed)
    for round_index in range(rounds):
        indices = np.concatenate(
            [
                rng.choice(group, max(1, round(len(group) * fraction)), replace=False)
                for group in groups
            ]
        )
        coef = coefficients(indices, int(rng.integers(0, 2**31 - 1)))
        counts += np.abs(coef) > NONZERO_EPSILON
        magnitudes += np.abs(coef)
        if (round_index + 1) % 50 == 0:
            print(f"  stability {round_index + 1}/{rounds}", flush=True)
    rows = [
        {
            "feature": name,
            "family": feature_family(name),
            "selection_frequency": float(counts[index] / rounds),
            "coefficient": float(full[index]),
            "abs_coefficient": float(abs(full[index])),
            "mean_stability_abs_coefficient": float(magnitudes[index] / rounds),
            "active": bool(counts[index] > 0 or abs(full[index]) > NONZERO_EPSILON),
        }
        for index, name in enumerate(features)
    ]
    rows.sort(
        key=lambda row: (
            -row["selection_frequency"],
            -row["abs_coefficient"],
            -row["mean_stability_abs_coefficient"],
            row["feature"],
        )
    )
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows


def consensus_ranking(rankings):
    names = {row["feature"] for ranking in rankings.values() for row in ranking}
    if any(
        {row["feature"] for row in ranking} != names for ranking in rankings.values()
    ):
        raise ValueError("Cannot aggregate rankings with different inventories")
    lookup = [{row["feature"]: row for row in ranking} for ranking in rankings.values()]
    rows = []
    for name in sorted(names):
        supported = [ranking[name] for ranking in lookup]
        rows.append(
            {
                "feature": name,
                "family": feature_family(name),
                "active_model_count": sum(row["active"] for row in supported),
                "mean_selection_frequency": float(
                    np.mean([row["selection_frequency"] for row in supported])
                ),
                "mean_abs_coefficient": float(
                    np.mean([row["abs_coefficient"] for row in supported])
                ),
                "mean_stability_abs_coefficient": float(
                    np.mean(
                        [row["mean_stability_abs_coefficient"] for row in supported]
                    )
                ),
                "mean_reciprocal_rank": float(
                    np.mean([1 / row["rank"] for row in supported])
                ),
                "best_rank": min(row["rank"] for row in supported),
            }
        )
    rows.sort(
        key=lambda row: (
            -row["active_model_count"],
            -row["mean_selection_frequency"],
            -row["mean_abs_coefficient"],
            -row["mean_reciprocal_rank"],
            row["best_rank"],
            row["feature"],
        )
    )
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows


def correlation_selection(ranking, frame, features, *, top, threshold):
    values = SimpleImputer(strategy="median", keep_empty_features=True).fit_transform(
        frame[features]
    )
    data = pd.DataFrame(values, columns=features)
    pearson, rank_correlation = data.corr(), data.corr(method="spearman")
    selected, rejected = [], []
    for row in ranking:
        name = row["feature"]
        conflicts = []
        for retained in selected:
            p, s = (
                float(pearson.loc[name, retained]),
                float(rank_correlation.loc[name, retained]),
            )
            # Correlation is undefined for constants; an inactive constant is
            # not evidence of redundancy with a variable candidate.
            if (
                max(
                    abs(p) if np.isfinite(p) else 0.0, abs(s) if np.isfinite(s) else 0.0
                )
                > threshold
            ):
                conflicts.append(
                    {"retained_feature": retained, "pearson": p, "spearman": s}
                )
        if conflicts:
            rejected.append(
                {"feature": name, "rank": row["rank"], "conflicts": conflicts}
            )
        else:
            selected.append(name)
        if len(selected) == top:
            break
    if len(selected) != top:
        raise ValueError(f"Only {len(selected)} nonredundant candidates for top{top}")
    return selected, rejected


def metric_summary(frame, predictions):
    if not np.isfinite(predictions).all():
        raise ValueError("Non-finite predictor output")
    metrics = {}
    for dataset, indices in frame.groupby("dataset", sort=False).indices.items():
        metrics[dataset] = {
            "n": len(indices),
            "value": float(
                spearman(
                    predictions[indices].tolist(),
                    frame.iloc[indices]["readability_score"].to_numpy(float).tolist(),
                )
            ),
        }
    return {
        "datasets": metrics,
        "unweighted_mean": unweighted_spearman_average(metrics, CORE_DATASETS),
    }


def evaluate_features(frame, features, *, folds, seed, alpha):
    fold_ids = np.full(len(frame), -1, dtype=int)
    for dataset_index, dataset in enumerate(CORE_DATASETS):
        indices = np.flatnonzero(frame["dataset"].to_numpy() == dataset)
        fold_ids[indices] = fold_assignments(
            frame.iloc[indices], folds, seed + dataset_index
        )
    if (fold_ids < 0).any():
        raise ValueError("Missing pooled fold assignment")
    pooled, lodo = np.full(len(frame), np.nan), np.full(len(frame), np.nan)
    for fold in range(folds):
        test = fold_ids == fold
        train = frame.loc[~test].reset_index(drop=True)
        model = fit_ridge(train, np.ones(len(train), dtype=bool), alpha, features)
        pooled[test] = model.predict(frame.loc[test, features].to_numpy(float))
    for held_out in CORE_DATASETS:
        test = frame["dataset"].to_numpy() == held_out
        train = frame.loc[~test].reset_index(drop=True)
        model = fit_ridge(train, np.ones(len(train), dtype=bool), alpha, features)
        lodo[test] = model.predict(frame.loc[test, features].to_numpy(float))
    model = fit_ridge(frame, np.ones(len(frame), dtype=bool), alpha, features)
    fit = model.predict(frame[features].to_numpy(float))
    prediction_rows = frame[["dataset", "task_id", "readability_score"]].copy()
    prediction_rows["cv_fold"] = fold_ids
    prediction_rows["pooled_oof_prediction"] = pooled
    prediction_rows["lodo_prediction"] = lodo
    prediction_rows["full_fit_prediction"] = fit
    result = {
        "selected_features": features,
        "feature_count": len(features),
        "family_counts": dict(Counter(feature_family(name) for name in features)),
        "pooled_cv": metric_summary(frame, pooled),
        "lodo": metric_summary(frame, lodo),
        "full_fit": metric_summary(frame, fit),
    }
    return result, prediction_rows


def main():
    parser = argparse.ArgumentParser(
        description="Six-dataset L1 stability screen of all 47 causal-LM candidates."
    )
    parser.add_argument(
        "--embedding-model",
        dest="embedding_models",
        action="append",
        default=None,
        choices=READABILITY_MODEL_EMBEDDINGS,
    )
    parser.add_argument("--llm-model", default=DEFAULT_CAUSAL_LM)
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--c", type=float, default=0.08)
    parser.add_argument("--stability-rounds", type=int, default=200)
    parser.add_argument("--sample-fraction", type=float, default=0.7)
    parser.add_argument("--ridge-alpha", type=float, default=200.0)
    parser.add_argument("--folds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--correlation-threshold", type=float, default=0.9)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=EXPERIMENT_RESULTS_ROOT / "llm47_top30_screen",
    )
    args = parser.parse_args()
    args.embedding_models = tuple(args.embedding_models or READABILITY_MODEL_EMBEDDINGS)
    if (
        args.stability_rounds < 1
        or not 0 < args.sample_fraction <= 1
        or args.c <= 0
        or args.top < 1
        or args.folds < 2
        or args.ridge_alpha <= 0
        or not 0 < args.correlation_threshold <= 1
    ):
        raise ValueError("Invalid screening/evaluation parameters")
    if len(set(args.embedding_models)) != len(args.embedding_models):
        raise ValueError("Embedding models must be unique")
    matrices, features, exclusions, checksums = load_matrices(args)
    reference_model = args.embedding_models[0]
    reference = matrices[reference_model]
    rankings, controls = {}, {}
    args.output.mkdir(parents=True, exist_ok=True)
    without_llm = [name for name in features if feature_family(name) != "llm"]
    for embedding_model, frame in matrices.items():
        print(
            f"Screening {embedding_model}: {len(features)} candidates, including {len(LLM_FEATURE_NAMES)} LLM features",
            flush=True,
        )
        rankings[embedding_model] = stability_ranking(
            frame,
            features,
            c=args.c,
            rounds=args.stability_rounds,
            fraction=args.sample_fraction,
            seed=args.seed,
        )
        controls[embedding_model] = stability_ranking(
            frame,
            without_llm,
            c=args.c,
            rounds=args.stability_rounds,
            fraction=args.sample_fraction,
            seed=args.seed,
        )
        directory = args.output / "per_model" / model_slug(embedding_model)
        directory.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rankings[embedding_model]).to_csv(
            directory / "ranking.csv", index=False
        )
        pd.DataFrame(controls[embedding_model]).to_csv(
            directory / "without_llm_ranking.csv", index=False
        )
    ranking, control_ranking = consensus_ranking(rankings), consensus_ranking(controls)
    selected, rejected = correlation_selection(
        ranking, reference, features, top=args.top, threshold=args.correlation_threshold
    )
    control, control_rejected = correlation_selection(
        control_ranking,
        reference,
        without_llm,
        top=args.top,
        threshold=args.correlation_threshold,
    )
    pd.DataFrame(ranking).to_csv(args.output / "consensus_ranking.csv", index=False)
    pd.DataFrame(control_ranking).to_csv(
        args.output / "without_llm_consensus_ranking.csv", index=False
    )
    pd.DataFrame(ranking[: args.top]).to_csv(
        args.output / f"raw_top{args.top}.csv", index=False
    )
    pd.DataFrame(
        [
            {**row, "selected_position": index + 1}
            for index, name in enumerate(selected)
            for row in ranking
            if row["feature"] == name
        ]
    ).to_csv(args.output / f"selected_top{args.top}.csv", index=False)
    pd.DataFrame(
        [
            {
                "feature": name,
                "family": feature_family(name),
                "missing_ratio": float(reference[name].isna().mean()),
                "zero_ratio_observed": float(reference[name].dropna().eq(0).mean())
                if reference[name].notna().any()
                else None,
            }
            for name in features
        ]
    ).to_csv(args.output / "coverage.csv", index=False)
    configurations = {
        "frozen18": list(SELECTED_FEATURES),
        f"without_llm_top{args.top}": control,
        f"with_llm_raw_top{args.top}": [row["feature"] for row in ranking[: args.top]],
        f"with_llm_nonredundant_top{args.top}": selected,
    }
    results = {}
    for name, chosen in configurations.items():
        print(f"Evaluating {name}: {len(chosen)} features", flush=True)
        results[name], predictions = evaluate_features(
            reference, chosen, folds=args.folds, seed=args.seed, alpha=args.ridge_alpha
        )
        predictions.to_csv(args.output / f"{name}_predictions.csv", index=False)
    payload = {
        "datasets": list(CORE_DATASETS),
        "sample_count": len(reference),
        "embedding_models": list(args.embedding_models),
        "llm_model": args.llm_model,
        "predictor_embedding_model": reference_model,
        "constructed_datasets_used": False,
        "candidate_count": len(features),
        "candidate_family_counts": dict(
            Counter(feature_family(name) for name in features)
        ),
        "excluded_features": exclusions,
        "parameters": {
            "c": args.c,
            "stability_rounds": args.stability_rounds,
            "sample_fraction": args.sample_fraction,
            "ridge_alpha": args.ridge_alpha,
            "folds": args.folds,
            "seed": args.seed,
            "top": args.top,
            "correlation_threshold": args.correlation_threshold,
        },
        "ranking_rules": {
            "per_model": [
                "selection_frequency DESC",
                "full_fit_abs_coefficient DESC",
                "mean_stability_abs_coefficient DESC",
                "feature_name ASC",
            ],
            "consensus": [
                "active_model_count DESC",
                "mean_selection_frequency DESC",
                "mean_full_fit_abs_coefficient DESC",
                "mean_reciprocal_rank DESC",
                "best_rank ASC",
                "feature_name ASC",
            ],
            "active": "selected in at least one stability round or nonzero in full fit; abs(coef)>1e-12",
            "sampling": "70% within each dataset without replacement; inverse-dataset-size sample weights and balanced class weights",
            "binarization": "within each dataset: score >= median(score); ties belong to higher-readability class; no drop_middle",
            "correlation_replacement": "median-imputed predictor matrix; skip a lower-ranked candidate when absolute Pearson or Spearman exceeds threshold and take the next candidate",
        },
        "feature_selection_inside_cv": False,
        "evaluation_note": "Fixed full-development-pool selection; CV and LODO refit only the Ridge predictor. Predictor diagnostics are not inputs to the ranking and do not constitute nested selection evaluation.",
        "input_csv_sha256": checksums,
        "sklearn_version": sklearn.__version__,
        "top_candidates": ranking[: args.top],
        "correlation_rejected": rejected,
        "without_llm_correlation_rejected": control_rejected,
        "results": results,
    }
    (args.output / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                name: {
                    "pooled_mean": result["pooled_cv"]["unweighted_mean"],
                    "lodo_mean": result["lodo"]["unweighted_mean"],
                    "families": result["family_counts"],
                }
                for name, result in results.items()
            },
            indent=2,
        ),
        flush=True,
    )
    print(f"Wrote {args.output / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()
