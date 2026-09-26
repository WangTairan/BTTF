"""Compare comment forms and label-free normalizations using cached token loss.

This is a fixed-feature diagnostic, not a feature-selection or inference runner.
All other selected features, folds, targets and Ridge settings stay unchanged.
Calibration uses training rows only. No production table or model is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.main.readability_model.evaluation.cross_validate_fixed import fold_assignments
from experiments.main.readability_model.evaluation.evaluate_constructed_variants import (
    prediction_rows,
    summarize_paired_variants,
)
from experiments.main.readability_model.selection.screen_llm_features import (
    CORE_DATASETS,
    load_matrices,
    load_table,
    metric_summary,
)
from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.experiments.statistics import spearman
from src.methods.readability_model.dataset_io import item_source_sha256
from src.methods.readability_model.llm_features.aggregate import _SourceLoss, _union
from src.methods.readability_model.llm_features.cache import _unpack
from src.methods.readability_model.llm_features.scoring import TraceConfiguration
from src.methods.readability_model.llm_features.source_spans import analyze_source
from src.methods.readability_model.llm_features.types import TokenLoss
from src.methods.readability_model.paths import (
    BASE_FEATURE_ROOT,
    EMBEDDING_FEATURE_ROOT,
    EXPERIMENT_RESULTS_ROOT,
    LLM_FEATURE_ROOT,
    LLM_SURPRISAL_CACHE_ROOT,
)
from src.methods.readability_model.results import model_slug
from src.methods.readability_model.runners.llm_surprisal_features import _source_policy
from src.methods.readability_model.runners.supervised_ridge import fit_ridge

COMMENT = "llm__comment__bpb_mean"
DOCUMENTATION_COMMENT = "llm__documentation_comment__bpb_mean"
FORMS = ("line", "block", "documentation")
MODES = (
    "original",
    "without_comment",
    "documentation_only",
    "minus_code",
    "ratio_to_code",
    "log_ratio_to_code",
    "centered_gated",
    "form_centered_gated",
    "form_standardized_gated",
    "form_split_raw",
    "form_split_centered_gated",
    "form_minus_code_centered_gated",
    "form_minus_code_standardized_gated",
)


def comment_form(source: str, span, language: str) -> str:
    text = source[span.start : span.end]
    if language == "python":
        return "line" if text.startswith("#") else "documentation"
    if text.startswith("//"):
        return "line"
    if text.startswith("/**"):
        return "documentation"
    if text.startswith("/*"):
        return "block"
    raise ValueError(f"Unexpected comment representation: {text[:40]!r}")


def noncomment_intervals(length: int, comments) -> list[tuple[int, int]]:
    result, start = [], 0
    for left, right in _union(comments):
        if start < left:
            result.append((start, left))
        start = right
    if start < length:
        result.append((start, length))
    return result


def read_trace(
    connection, source_hash, configuration, expected_count, *, trace_sha256=None
):
    fingerprint = trace_sha256 or configuration.fingerprint_for("global")
    rows = connection.execute(
        "SELECT token_start, token_stop, payload FROM trace_windows "
        "WHERE source_sha256=? AND trace_sha256=? AND kind='global' "
        "ORDER BY token_start",
        (source_hash, fingerprint),
    )
    losses = []
    for start, stop, payload in rows:
        window = [TokenLoss(*values) for values in _unpack(payload)]
        if start != len(losses) or stop != start + len(window):
            raise ValueError("Cached global trace has a gap or overlap")
        if [value.token_index for value in window] != list(range(start, stop)):
            raise ValueError("Cached global trace has inconsistent token indices")
        losses.extend(window)
    if len(losses) != expected_count:
        raise ValueError(f"Incomplete cached trace: {len(losses)}/{expected_count}")
    return losses


def derive_statistics(frame, args):
    """Reaggregate exact original-source spans; SQLite is opened read-only."""
    path = args.cache_root / model_slug(args.llm_model) / "traces.sqlite"
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    rows = []
    try:
        for dataset, part in frame.groupby("dataset", sort=False):
            items = {
                item.task_id: item
                for item in load_code_dataset(DATASETS[dataset].path)
            }
            metadata_path = (
                args.llm_root / dataset / model_slug(args.llm_model) / "metadata.json"
            )
            metadata = json.loads(metadata_path.read_text())
            config = TraceConfiguration(**metadata["configuration"]["trace"])
            by_id = {row["task_id"]: row for row in metadata["rows"]}
            for index, row in enumerate(part.itertuples(index=False), 1):
                item = items[row.task_id]
                source_hash = item_source_sha256(item)
                stored = by_id[row.task_id]
                if source_hash != stored["source_sha256"]:
                    raise ValueError(f"Stale source for {dataset}/{row.task_id}")
                language, fragments, members = _source_policy(item, dataset)
                analysis = analyze_source(
                    item.content, language, allow_fragments=fragments,
                    allow_class_members=members,
                )
                spans = [span for span in analysis.spans if span.role == "comment"]
                values = {
                    "dataset": dataset,
                    "task_id": row.task_id,
                    "source_sha256": source_hash,
                    "language": language,
                    "noncomment_code_bpb": np.nan,
                }
                for form in FORMS:
                    values[f"{form}_bpb"] = np.nan
                    values[f"{form}_bytes"] = 0.0
                    values[f"{form}_count"] = 0
                if spans:
                    losses = read_trace(
                        connection, source_hash, config, stored["token_count"]
                    )
                    loss = _SourceLoss(item.content, losses)
                    intervals = [(span.start, span.end) for span in spans]
                    original = loss.q(intervals)
                    recorded = float(part.loc[part.task_id == row.task_id, COMMENT].iloc[0])
                    if original is None or not np.isclose(
                        original, recorded, rtol=1e-9, atol=1e-9
                    ):
                        raise ValueError(
                            f"Comment BPB disagrees with existing table: {row.task_id}"
                        )
                    code_bpb = loss.q(noncomment_intervals(len(item.content), intervals))
                    values["noncomment_code_bpb"] = code_bpb if code_bpb is not None else np.nan
                    for form in FORMS:
                        selected = [
                            span for span in spans
                            if comment_form(item.content, span, language) == form
                        ]
                        bits, bytes_ = loss.totals(
                            [(span.start, span.end) for span in selected]
                        )
                        values[f"{form}_bytes"] = bytes_
                        values[f"{form}_count"] = len(selected)
                        values[f"{form}_bpb"] = bits / bytes_ if bytes_ else np.nan
                elif pd.notna(part.loc[part.task_id == row.task_id, COMMENT].iloc[0]):
                    raise ValueError(f"Existing comment BPB has no source spans: {row.task_id}")
                rows.append(values)
                if index % 50 == 0 or index == len(part):
                    print(f"Cached comment aggregation: {dataset} {index}/{len(part)}", flush=True)
    finally:
        connection.close()
    return pd.DataFrame(rows)


class CommentTransform:
    """Fit comment-form reference means without readability labels."""

    def __init__(self, mode: str):
        if mode not in MODES:
            raise ValueError(f"Unknown probe: {mode}")
        self.mode = mode

    def fit(self, frame):
        self.means = {}
        self.scales = {}
        if self.mode == "centered_gated":
            self.means["all"] = float(frame[COMMENT].dropna().mean())
            if not np.isfinite(self.means["all"]):
                raise ValueError("No training observations for comment calibration")
        if "form" in self.mode and self.mode != "form_split_raw":
            for form in FORMS:
                values = frame[f"{form}_bpb"].to_numpy(float)
                if self.mode.startswith("form_minus_code_"):
                    values = values - frame["noncomment_code_bpb"].to_numpy(float)
                available = values[np.isfinite(values)]
                if not len(available):
                    raise ValueError(f"No training observations for {form} calibration")
                self.means[form] = float(np.mean(available))
                self.scales[form] = float(np.std(available))
                if "standardized" in self.mode and self.scales[form] == 0:
                    raise ValueError(f"Zero training variance for {form} calibration")
        return self

    def transform(self, frame, selected):
        output = frame.copy()
        if self.mode == "original":
            return output, list(selected), [COMMENT]
        retained = [name for name in selected if name != COMMENT]
        if self.mode == "without_comment":
            return output, retained, []
        if self.mode == "documentation_only":
            output[DOCUMENTATION_COMMENT] = frame["documentation_bpb"]
            return (
                output,
                retained + [DOCUMENTATION_COMMENT],
                [DOCUMENTATION_COMMENT],
            )
        c = frame[COMMENT].to_numpy(float)
        code = frame["noncomment_code_bpb"].to_numpy(float)
        if self.mode == "minus_code":
            values = c - code
        elif self.mode in {"ratio_to_code", "log_ratio_to_code"}:
            values = np.full(len(frame), np.nan)
            valid = np.isfinite(c) & np.isfinite(code) & (code > 0)
            if self.mode == "ratio_to_code":
                values[valid] = c[valid] / code[valid]
            else:
                valid &= c > 0
                values[valid] = np.log(c[valid]) - np.log(code[valid])
        elif self.mode == "centered_gated":
            values = np.where(np.isfinite(c), c - self.means["all"], 0.0)
        else:
            by_form, weights = [], []
            for form in FORMS:
                values = frame[f"{form}_bpb"].to_numpy(float)
                if self.mode.startswith("form_minus_code_"):
                    values = values - code
                valid = np.isfinite(values)
                weights.append(np.where(valid, frame[f"{form}_bytes"], 0.0))
                if self.mode != "form_split_raw":
                    values = np.where(valid, values - self.means[form], 0.0)
                    if "standardized" in self.mode:
                        values = values / self.scales[form]
                by_form.append(values)
            if self.mode in {"form_split_raw", "form_split_centered_gated"}:
                columns = [f"llm__comment_probe__{self.mode}__{form}" for form in FORMS]
                for column, values in zip(columns, by_form):
                    output[column] = values
                return output, retained + columns, columns
            weights = np.asarray(weights).T
            total = weights.sum(axis=1)
            values = np.divide(
                (np.asarray(by_form).T * weights).sum(axis=1), total,
                out=np.zeros(len(frame)), where=total > 0,
            )
        name = f"llm__comment_probe__{self.mode}"
        output[name] = values
        return output, retained + [name], [name]


def evaluate(frame, selected, mode, args):
    fold_ids = np.full(len(frame), -1, dtype=int)
    for index, dataset in enumerate(CORE_DATASETS):
        indices = np.flatnonzero(frame.dataset.to_numpy() == dataset)
        fold_ids[indices] = fold_assignments(frame.iloc[indices], args.folds, args.seed + index)
    if (fold_ids < 0).any():
        raise ValueError("Missing fold assignments")
    pooled, lodo = np.full(len(frame), np.nan), np.full(len(frame), np.nan)
    fold_coefficients = []
    for kind, target, tests in (
        ("pooled", pooled, [fold_ids == fold for fold in range(args.folds)]),
        ("lodo", lodo, [frame.dataset.to_numpy() == dataset for dataset in CORE_DATASETS]),
    ):
        for index, test in enumerate(tests):
            train, validation = frame.loc[~test].reset_index(drop=True), frame.loc[test].reset_index(drop=True)
            transform = CommentTransform(mode).fit(train)
            train, features, probes = transform.transform(train, selected)
            validation, _, _ = transform.transform(validation, selected)
            model = fit_ridge(train, np.ones(len(train), bool), args.alpha, features)
            target[test] = model.predict(validation[features].to_numpy(float))
            if kind == "pooled":
                fold_coefficients.append({
                    "fold": index,
                    "coefficients": {name: float(model.named_steps["ridge"].coef_[features.index(name)]) for name in probes},
                })
    transform = CommentTransform(mode).fit(frame)
    transformed, features, probes = transform.transform(frame, selected)
    model = fit_ridge(transformed, np.ones(len(frame), bool), args.alpha, features)
    diagnostics = {}
    for name in probes:
        single = fit_ridge(transformed, np.ones(len(frame), bool), args.alpha, [name])
        correlations = {}
        for dataset, part in transformed.groupby("dataset", sort=False):
            available = part.loc[part[name].notna()]
            correlations[dataset] = {
                "n": len(available),
                "rho": spearman(available[name].tolist(), available.readability_score.tolist())
                if len(available) > 1 and available[name].nunique() > 1 else None,
            }
        diagnostics[name] = {
            "coefficient": float(model.named_steps["ridge"].coef_[features.index(name)]),
            "single_feature_coefficient": float(single.named_steps["ridge"].coef_[0]),
            "missing_ratio": float(transformed[name].isna().mean()),
            "single_correlations": correlations,
        }
    return {
        "feature_count": len(features), "features": features,
        "pooled_cv": metric_summary(frame, pooled), "lodo": metric_summary(frame, lodo),
        "comment_features": diagnostics, "pooled_fold_coefficients": fold_coefficients,
    }, transform, model, features


def attach_statistics(frame, statistics):
    result = frame.merge(statistics.drop(columns="source_sha256"), on=["dataset", "task_id"], validate="one_to_one")
    if len(result) != len(frame):
        raise ValueError("Comment statistics lost feature rows")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-summary", type=Path, default=EXPERIMENT_RESULTS_ROOT / "llm49_top24_screen/summary.json")
    parser.add_argument("--output", type=Path, default=EXPERIMENT_RESULTS_ROOT / "comment_feature_probes")
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--cache-root", type=Path, default=LLM_SURPRISAL_CACHE_ROOT)
    parser.add_argument("--constructed-dataset", action="append", default=[], choices=("java_comparative_obfuscation", "python_comparative_degradation"))
    args = parser.parse_args()
    screen = json.loads(args.screen_summary.read_text())
    args.embedding_models = [screen["predictor_embedding_model"]]
    args.llm_model = screen["llm_model"]
    args.alpha, args.seed, args.folds = screen["parameters"]["ridge_alpha"], screen["parameters"]["seed"], screen["parameters"]["folds"]
    selected = screen["results"]["with_llm_nonredundant_top24"]["selected_features"]
    if selected.count(COMMENT) != 1:
        raise ValueError("Expected exactly one original comment BPB feature")
    matrices, _, _, checksums = load_matrices(args)
    if any(screen["input_csv_sha256"][path] != value for path, value in checksums.items()):
        raise ValueError("Input feature tables changed since screening")
    reference = matrices[args.embedding_models[0]]
    args.output.mkdir(parents=True, exist_ok=True)
    statistics = derive_statistics(reference, args)
    statistics.to_csv(args.output / "comment_statistics.csv", index=False)
    reference = attach_statistics(reference, statistics)
    constructed = {}
    for dataset in args.constructed_dataset:
        items = {item.task_id: item for item in load_code_dataset(DATASETS[dataset].path)}
        slugs = {"base": model_slug(args.embedding_models[0]), "embedding": model_slug(args.embedding_models[0]), "llm": model_slug(args.llm_model)}
        tables = []
        for family, root in (("base", args.base_root), ("embedding", args.embedding_root), ("llm", args.llm_root)):
            path = root / dataset / slugs[family] / "features.csv"
            tables.append(load_table(path, family, items, dataset=dataset, llm=family == "llm"))
            checksums[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        frame = tables[0]
        for table in tables[1:]:
            frame = frame.merge(table.drop(columns="readability_score"), on=["dataset", "task_id"], validate="one_to_one")
        stats = derive_statistics(frame, args)
        stats.to_csv(args.output / f"{dataset}_comment_statistics.csv", index=False)
        constructed[dataset] = (attach_statistics(frame, stats), items)
    results = {}
    for mode in MODES:
        result, transform, model, features = evaluate(reference, selected, mode, args)
        result["constructed"] = {}
        for dataset, (frame, items) in constructed.items():
            data, _, _ = transform.transform(frame, selected)
            scores = model.predict(data[features].to_numpy(float))
            result["constructed"][dataset] = summarize_paired_variants(prediction_rows(frame, scores, items))
        results[mode] = result
        payload = {
            "input_csv_sha256": checksums, "screen_summary": str(args.screen_summary),
            "parameters": {"alpha": args.alpha, "seed": args.seed, "folds": args.folds},
            "inference_performed": False, "calibration_uses_readability_labels": False,
            "reference_means_fitted_within_predictor_folds": True,
            "noncomment_bpb_definition": "Original trace loss over non-comment source bytes, including whitespace; not a comment-deletion contrast",
            "form_counts": {form: int((statistics[f"{form}_bytes"] > 0).sum()) for form in FORMS},
            "results": results,
        }
        (args.output / "summary.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
        print(f"{mode}: K={result['feature_count']}, pooled={result['pooled_cv']['unweighted_mean']:.6f}, LODO={result['lodo']['unweighted_mean']:.6f}", flush=True)


if __name__ == "__main__":
    main()
