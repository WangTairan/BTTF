"""Conservative mechanism-based comment groups from existing global token loss.

Content grouping is deterministic and label-free, not only syntax-form splitting.
Source comment boundaries and existing parser uncertainty are preserved. BPB uses
the complete original comment interval, never classifier-normalized body text.
Code-like content confounds code and comment difficulty; separators/provenance
are nuisance content. Explanatory prose BPB retains the negative-difficulty
hypothesis before results, and is not relabeled after observing coefficients.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import sqlite3
import textwrap
import tokenize
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.main.readability_model.evaluation.cross_validate_fixed import fold_assignments
from experiments.main.readability_model.evaluation.evaluate_constructed_variants import prediction_rows, summarize_paired_variants
from experiments.supplementary.comment_validity.comment_span_features import (
    COMMENT,
    comment_form,
    noncomment_intervals,
    read_trace,
)
from experiments.main.readability_model.selection.screen_llm_features import CORE_DATASETS, load_matrices, load_table, metric_summary
from src.datasets import load_code_dataset
from src.experiments.registry import COGNASCORE_EMBEDDING_MODELS, DATASETS
from src.experiments.statistics import spearman
from src.methods.readability_model.dataset_io import item_source_sha256
from src.methods.readability_model.llm_features.aggregate import _SourceLoss, _union
from src.methods.readability_model.llm_features.scoring import TraceConfiguration
from src.methods.readability_model.llm_features.source_spans import _parser, analyze_source
from src.methods.readability_model.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT, EXPERIMENT_RESULTS_ROOT, LLM_FEATURE_ROOT, LLM_SURPRISAL_CACHE_ROOT
from src.methods.readability_model.results import model_slug
from src.methods.readability_model.runners.llm_surprisal_features import _source_policy
from src.methods.readability_model.runners.supervised_ridge import fit_ridge

GROUPS = ("code_like", "separator", "metadata", "prose", "mixed_unknown", "unknown")
PREFIX = "llm__comment_content__"
CLASSIFIER_VERSION = 2
_WORDS = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_LICENSE = re.compile(r"copyright\b|SPDX-License-Identifier\s*:|licensed\s+under\b|GNU\s+(?:Lesser\s+)?General\s+Public\s+License|permission\s+is\s+hereby\s+granted|all\s+rights\s+reserved|Apache\s+License|MIT\s+License|redistribut(?:e|ion).*?license", re.I | re.S)
_PROVENANCE = re.compile(r"^\s*(?:@(?:author|version|since|date|file)\b|\$(?:Id|Revision|Date|Author)\s*:|generated\s+(?:by|on)\b|(?:author|version|last\s+modified|source(?:\s+file)?|file\s+name)\s*:)", re.I)
_FUNCTIONAL_TAG = re.compile(r"^\s*@(?:param|return|returns|throws|exception|brief|details)\b", re.I)
_ASSIGN = re.compile(r"\b[A-Za-z_$]\w*(?:\.[A-Za-z_$]\w*|\[[^\]\n]+\])*\s*(?:[+*/%&|^-]=|=(?!=))")
_OPERATION = re.compile(r"\b(?:return|break|continue|throw|assert|import|from|package|def|class|if|else|for|while|switch|try|with|raise|yield)\b|(?:\+\+|--|->|::)|^\s*#\s*(?:include|define|ifdef|ifndef|if|elif|else|endif|pragma)\b|\b(?:int|long|short|float|double|bool|boolean|char|void|String|auto|const|unsigned|signed)\s+[A-Za-z_$]", re.M)
_CALL = re.compile(r"\b[A-Za-z_$]\w*(?:(?:\.|::|->)[A-Za-z_$]\w*)*\s*\(")
_STATEMENT_FRAGMENT = re.compile(r"\b[A-Za-z_$]\w*(?:(?:\.|::|->)[A-Za-z_$]\w*)*\s*\([^;\n]*\)\s*;|\b[A-Za-z_$]\w*(?:\.[A-Za-z_$]\w*|\[[^\]\n]+\])*\s*(?:[+*/%&|^-]=|=(?!=))[^;\n]*;")
_FUNCTIONAL_VERB = re.compile(r"^\s*(?:compute|calculate|return|returns|check|checks|set|sets|handle|handles|initialize|initializes|create|creates|remove|removes|add|adds|validate|validates|convert|converts)\b", re.I)


@dataclass(frozen=True)
class Classification:
    group: str
    reason: str
    body: str


def strip_comment_markers(text, language):
    """For classification only; original spans remain the scoring target."""
    body = text.strip()
    if body.startswith("/*") and body.endswith("*/"):
        body = body[2:-2]
        if body.startswith("*"):
            body = body[1:]
        body = "\n".join(re.sub(r"^\s*\*(?:\s|$)", "", line) for line in body.splitlines())
    elif body.startswith("//"):
        body = "\n".join(re.sub(r"^\s*//", "", line) for line in body.splitlines())
    elif language.lower() in {"python", "py"} and body.startswith("#"):
        body = "\n".join(re.sub(r"^\s*#", "", line) for line in body.splitlines())
    elif language.lower() in {"python", "py"}:
        match = re.match(r"(?i)^[ru]*('''|\"\"\")", body)
        if match and body.endswith(match.group(1)):
            body = body[match.end():-len(match.group(1))]
    return textwrap.dedent(body).strip()


@lru_cache(maxsize=4)
def _content_parser(language):
    return _parser(language)


def _complete_code(body, language):
    """Full syntax plus operational evidence; never semicolon-only detection."""
    if not (_ASSIGN.search(body) or _OPERATION.search(body) or _CALL.search(body)):
        return False
    normalized = {"py": "python", "c++": "cpp", "cuda": "cpp", "cu": "cpp"}.get(language.lower(), language.lower())
    if normalized == "python":
        try:
            module = ast.parse(body)
        except (SyntaxError, ValueError):
            return False
        significant = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return, ast.Raise, ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Assert, ast.Break, ast.Continue)
        return any(isinstance(node, significant) or isinstance(node, ast.Expr) and isinstance(node.value, (ast.Call, ast.Yield, ast.YieldFrom)) for node in module.body)
    if normalized not in {"java", "c", "cpp"}:
        return False
    parser = _content_parser(normalized)
    # A terminal newline is the lexical terminator of a C preprocessor
    # directive. Supplying it for classification does not repair code tokens,
    # append missing semicolons, or change original-source scoring intervals.
    candidates = [(body + "\n", 0)]
    prefix = "class __Content__ { void __body__() {\n" if normalized == "java" else "void __content__() {\n"
    suffix = "\n} }" if normalized == "java" else "\n}"
    candidates.append((prefix + body + suffix, len(prefix.encode("utf-8"))))
    if normalized == "java":
        candidates.append(("class __Content__ {\n" + body + "\n}", len("class __Content__ {\n")))
    constructs = {"declaration", "local_variable_declaration", "expression_statement", "return_statement", "if_statement", "for_statement", "while_statement", "do_statement", "switch_statement", "function_definition", "class_declaration", "method_declaration", "class_specifier", "template_declaration", "preproc_include", "preproc_def", "preproc_function_def", "preproc_if", "preproc_ifdef", "preproc_elif", "preproc_else", "supported_preproc_call", "import_declaration", "package_declaration", "break_statement", "continue_statement", "throw_statement", "try_statement", "call_expression", "assignment_expression", "update_expression"}
    body_bytes = len(body.encode("utf-8"))
    for candidate, left in candidates:
        tree = parser.parse(candidate.encode("utf-8"))
        if tree.root_node.has_error:
            continue
        nodes, stack = [], [tree.root_node]
        while stack:
            node = stack.pop()
            if left <= node.start_byte < node.end_byte <= left + body_bytes + 1:
                if node.type == "preproc_call":
                    # The grammar uses this generic node for arbitrary directives
                    # and even isolated #endif/#else. It is not by itself proof
                    # of a complete preprocessing construct. Recognize #pragma,
                    # already admitted by the operational-syntax gate, exactly.
                    directive = node.child_by_field_name("directive")
                    if directive is not None and re.fullmatch(rb"#\s*pragma", candidate.encode("utf-8")[directive.start_byte:directive.end_byte]):
                        nodes.append("supported_preproc_call")
                else:
                    nodes.append(node.type)
            stack.extend(node.named_children)
        if any(kind in constructs for kind in nodes):
            return True
    return False


def _prose_body(body):
    """Formatting tags and identifier references do not imply code programs."""
    lines = []
    functional = False
    for line in body.splitlines():
        if _FUNCTIONAL_TAG.match(line):
            functional = True
            line = re.sub(r"^\s*@(?:param|throws|exception)\s+\S+\s*", "", line, flags=re.I)
            line = re.sub(r"^\s*@(?:return|returns|brief|details)\s*", "", line, flags=re.I)
        line = re.sub(r"</?[A-Za-z][^>]*>", " ", line)
        line = re.sub(r"\{@(?:link|code|literal)\s+([^}]+)\}", r"\1", line)
        lines.append(line)
    return "\n".join(lines), functional


def _has_prose(body):
    clean, functional = _prose_body(body)
    if re.fullmatch(r"[\w.$:/<>-]+", clean.strip()):
        return False
    return len(_WORDS.findall(clean)) >= (2 if functional else 3)


def _explicit_code_fragment(body, language):
    if re.search(r"^\s*(?:>>>|\.\.\.|>\s+\w+\s*\(|```)", body, re.M):
        return True
    snippets = re.findall(r"`([^`]+)`|<code>(.*?)</code>", body, flags=re.I | re.S)
    if any(_complete_code(a or b, language) for a, b in snippets):
        return True
    return any(_complete_code(match.group(), language) for match in _STATEMENT_FRAGMENT.finditer(body))


def _nested_annotation(body, language):
    """Quoted '# note' or '// note' strings are code literals, not comments."""
    normalized = {"py": "python", "c++": "cpp", "cuda": "cpp", "cu": "cpp"}.get(language.lower(), language.lower())
    if normalized == "python":
        return any(token.type == tokenize.COMMENT and _WORDS.search(token.string) for token in tokenize.generate_tokens(io.StringIO(body).readline))
    tree = _content_parser(normalized).parse((body + "\n").encode("utf-8"))
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in {"comment", "line_comment", "block_comment"} and _WORDS.search(node.text.decode("utf-8")):
            return True
        if node.type == "preproc_arg":
            # C-family grammars can keep a macro's trailing line annotation
            # inside an opaque preproc_arg rather than exposing a comment node.
            # Reparse only that fragment lexically; quoted/character/raw-string
            # marker text remains a literal, never a regex-guessed comment.
            fragment = _content_parser(normalized).parse(node.text + b"\n")
            fragment_stack = [fragment.root_node]
            while fragment_stack:
                child = fragment_stack.pop()
                if child.type in {"comment", "line_comment", "block_comment"} and _WORDS.search(child.text.decode("utf-8")):
                    return True
                fragment_stack.extend(child.named_children)
        stack.extend(node.named_children)
    return False


def classify_comment_content(text, language, syntax_form=None):
    """Precedence: separators, standalone code, mixed, metadata, prose, unknown.

    This is a conservative operational grouping, not proof of author intent or
    documentation correctness. Syntax form is accepted as provenance only.
    """
    body = strip_comment_markers(text, language)
    if not body:
        return Classification("unknown", "empty normalized body", body)
    compact = re.sub(r"\s+", "", body)
    punctuation = sum(not character.isalnum() for character in compact)
    if len(compact) >= 3 and punctuation / len(compact) >= 0.9 and not _WORDS.search(body):
        return Classification("separator", "mostly punctuation with no alphabetic words", body)
    # Complete executable-looking content precedes prose-word counting, because
    # identifiers are not sufficient evidence of natural language.
    if _complete_code(body, language):
        # Explicit nested comment annotations or doc tags are mixed content.
        if _nested_annotation(body, language):
            return Classification("mixed_unknown", "code contains an embedded annotation", body)
        return Classification("code_like", "complete parse with operational code syntax", body)
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    code_lines = [line for line in lines if _complete_code(line, language)]
    prose_lines = [line for line in lines if not _complete_code(line, language) and _has_prose(line)]
    if code_lines and prose_lines or _explicit_code_fragment(body, language) and _has_prose(body):
        return Classification("mixed_unknown", "code/example material and explanatory words share one occurrence", body)
    if language.lower() in {"c", "cpp", "c++", "cuda", "cu"} and re.match(r"^\s*#\s*define\b", body):
        # A failed complete macro parse is not evidence for natural-language
        # prose. In particular, opaque preproc_arg handling can reject valid
        # quoted/raw-string block-comment markers. Do not repair source syntax
        # or guess the intended macro mechanism when this grammar cannot prove it.
        return Classification("unknown", "macro-looking syntax is incomplete or unsupported by the complete parser", body)
    provenance_lines = [line for line in lines if _PROVENANCE.match(line)]
    functional_lines = [line for line in lines if _FUNCTIONAL_TAG.match(line) or _FUNCTIONAL_VERB.match(line)]
    if provenance_lines and len(provenance_lines) < len(lines) and any(_has_prose(line) for line in lines if not _PROVENANCE.match(line)):
        return Classification("mixed_unknown", "explicit provenance and non-provenance prose share one occurrence", body)
    if _LICENSE.search(body):
        if functional_lines:
            return Classification("mixed_unknown", "license/provenance plus functional documentation", body)
        return Classification("metadata", "explicit license/copyright boilerplate", body)
    if provenance_lines and len(provenance_lines) == len(lines):
        return Classification("metadata", "explicit author/version/source provenance fields", body)
    if _has_prose(body):
        return Classification("prose", "descriptive natural-language word evidence, allowing functional documentation tags", body)
    return Classification("unknown", "insufficient evidence for pure code, metadata, separator, or explanatory prose", body)


def aggregate_content_groups(source, losses, spans, language):
    loss = _SourceLoss(source, losses)
    grouped = {group: [] for group in GROUPS}
    occurrences = []
    for number, span in enumerate(spans):
        raw = source[span.start:span.end]
        form = comment_form(source, span, language)
        classification = classify_comment_content(raw, language, form)
        grouped[classification.group].append((span.start, span.end))
        bits, covered_bytes = loss.totals([(span.start, span.end)])
        occurrences.append({"occurrence_index": number, "start": span.start, "end": span.end, "syntax_form": form, "content_group": classification.group, "reason": classification.reason, "bits": bits, "covered_bytes": covered_bytes, "bpb": bits / covered_bytes if covered_bytes else np.nan, "body": classification.body, "raw_comment": raw})
    values = {"detected_comment_count": len(spans)}
    for group, intervals in grouped.items():
        bits, covered_bytes = loss.totals(intervals)
        values[PREFIX + group + "__bpb_mean"] = bits / covered_bytes if covered_bytes else np.nan
        values[group + "__covered_bytes"] = covered_bytes
        values[group + "__bits"] = bits
        values[group + "__occurrence_count"] = len(intervals)
    all_intervals = [(span.start, span.end) for span in spans]
    values["all_comment_bpb"] = loss.q(all_intervals)
    values["all_comment_covered_bytes"] = loss.totals(all_intervals)[1]
    values["noncomment_original_trace_bpb"] = loss.q(noncomment_intervals(len(source), all_intervals))
    # Actual comment spans should be disjoint; a cross-group overlap would make
    # decomposition nonadditive and must not be silently called a partition.
    original_bytes = sum(loss.span_bytes(start, end) for start, end in _union(all_intervals))
    group_bytes = sum(sum(loss.span_bytes(start, end) for start, end in _union(intervals)) for intervals in grouped.values())
    if not np.isclose(original_bytes, group_bytes, rtol=0, atol=1e-9):
        raise ValueError("Content groups overlap across original comment bytes")
    return values, occurrences


def derive_statistics(frame, args):
    path = args.cache_root / model_slug(args.llm_model) / "traces.sqlite"
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    statistics, all_occurrences = [], []
    try:
        for dataset, part in frame.groupby("dataset", sort=False):
            items = {item.task_id: item for item in load_code_dataset(DATASETS[dataset].path)}
            metadata = json.loads((args.llm_root / dataset / model_slug(args.llm_model) / "metadata.json").read_text())
            config = TraceConfiguration(**metadata["configuration"]["trace"])
            stored_rows = {row["task_id"]: row for row in metadata["rows"]}
            for index, row in enumerate(part.to_dict("records"), 1):
                item, stored = items[row["task_id"]], stored_rows[row["task_id"]]
                source_hash = item_source_sha256(item)
                if source_hash != stored["source_sha256"]:
                    raise ValueError(f"Stale source: {dataset}/{item.task_id}")
                language, fragments, members = _source_policy(item, dataset)
                analysis = analyze_source(item.content, language, allow_fragments=fragments, allow_class_members=members)
                spans = [span for span in analysis.spans if span.role == "comment"]
                values = {"dataset": dataset, "task_id": item.task_id, "source_sha256": source_hash, "language": language, "comment_detection_available": "comment" in analysis.roles_available, "source_structural_available": analysis.metadata["structural_available"], "source_parse_mode": analysis.metadata["parse_mode"], "docstring_detection_uncertain": language == "python" and not analysis.metadata["structural_available"], "whole_source_utf8_bytes": len(item.content.encode("utf-8")), "detected_comment_count": len(spans)}
                for group in GROUPS:
                    values[PREFIX + group + "__bpb_mean"] = np.nan
                    for field in ("covered_bytes", "bits", "occurrence_count"):
                        values[group + "__" + field] = 0.0
                values["all_comment_bpb"], values["all_comment_covered_bytes"] = np.nan, 0.0
                values["noncomment_original_trace_bpb"] = np.nan
                if spans:
                    losses = read_trace(
                        connection,
                        source_hash,
                        config,
                        stored["token_count"],
                        trace_sha256=getattr(args, "trace_sha256_override", None),
                    )
                    aggregate, occurrences = aggregate_content_groups(item.content, losses, spans, language)
                    if aggregate["all_comment_bpb"] is None:
                        raise ValueError(f"Comment spans have no covered trace bytes: {item.task_id}")
                    # Older diagnostic tables retained the generic comment-BPB
                    # column.  The production 47-feature inventory no longer
                    # does, but both inventories use the same immutable trace.
                    if COMMENT in row and not np.isclose(
                        aggregate["all_comment_bpb"], row[COMMENT], rtol=1e-9, atol=1e-9
                    ):
                        raise ValueError(f"Existing comment BPB differs from trace: {item.task_id}")
                    values.update(aggregate)
                    for occurrence in occurrences:
                        all_occurrences.append({"dataset": dataset, "task_id": item.task_id, "source_sha256": source_hash, "language": language, **occurrence})
                elif COMMENT in row and pd.notna(row[COMMENT]):
                    raise ValueError("Existing comment BPB without original comment spans")
                statistics.append(values)
                if index % 50 == 0 or index == len(part):
                    print(f"Content classification/global-cache aggregation: {dataset} {index}/{len(part)}", flush=True)
    finally:
        connection.close()
    return pd.DataFrame(statistics), pd.DataFrame(all_occurrences)


def attach(frame, statistics):
    result = frame.merge(statistics.drop(columns="source_sha256"), on=["dataset", "task_id"], validate="one_to_one")
    if len(result) != len(frame):
        raise ValueError("Content statistics lost feature rows")
    return result


def evaluate(frame, features, probes, args):
    fold_ids = np.full(len(frame), -1, int)
    for index, dataset in enumerate(CORE_DATASETS):
        indices = np.flatnonzero(frame.dataset.to_numpy() == dataset)
        fold_ids[indices] = fold_assignments(frame.iloc[indices], args.folds, args.seed + index)
    if (fold_ids < 0).any():
        raise ValueError("Missing folds")
    pooled, lodo = np.full(len(frame), np.nan), np.full(len(frame), np.nan)
    fold_coefs = {"pooled": [], "lodo": []}
    for kind, predictions, tests in (("pooled", pooled, [fold_ids == fold for fold in range(args.folds)]), ("lodo", lodo, [frame.dataset.to_numpy() == dataset for dataset in CORE_DATASETS])):
        for index, test in enumerate(tests):
            train, validation = frame.loc[~test].reset_index(drop=True), frame.loc[test].reset_index(drop=True)
            missing = [name for name in features if train[name].isna().all()]
            if missing:
                raise ValueError(f"Unavailable training-only group calibration: {kind}/{index}/{missing}")
            fit = fit_ridge(train, np.ones(len(train), bool), args.alpha, features)
            predictions[test] = fit.predict(validation[features].to_numpy(float))
            fold_coefs[kind].append({"fold": index if kind == "pooled" else CORE_DATASETS[index], "coefficients": {name: float(fit.named_steps["ridge"].coef_[features.index(name)]) for name in features}})
    fit = fit_ridge(frame, np.ones(len(frame), bool), args.alpha, features)
    diagnostics = {}
    for name in probes:
        single = fit_ridge(frame, np.ones(len(frame), bool), args.alpha, [name])
        correlations = {}
        for dataset, part in frame.groupby("dataset", sort=False):
            available = part.loc[part[name].notna()]
            correlations[dataset] = {"n": len(available), "rho": spearman(available[name].tolist(), available.readability_score.tolist()) if len(available) > 1 and available[name].nunique() > 1 else None}
        diagnostics[name] = {"coefficient": float(fit.named_steps["ridge"].coef_[features.index(name)]), "single_feature_coefficient": float(single.named_steps["ridge"].coef_[0]), "n_available": int(frame[name].notna().sum()), "missing_ratio": float(frame[name].isna().mean()), "single_correlations": correlations, "pooled_positive_fold_count": sum(row["coefficients"][name] > 1e-12 for row in fold_coefs["pooled"]), "lodo_positive_fold_count": sum(row["coefficients"][name] > 1e-12 for row in fold_coefs["lodo"])}
    predictions = frame[["dataset", "task_id", "readability_score"]].copy()
    predictions["pooled_fold"], predictions["pooled_score"], predictions["lodo_score"] = fold_ids, pooled, lodo
    result = {"features": features, "feature_count": len(features), "pooled_cv": metric_summary(frame, pooled), "lodo": metric_summary(frame, lodo), "probes": diagnostics, "fold_coefficients": fold_coefs}
    return result, fit, predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-summary", type=Path, default=EXPERIMENT_RESULTS_ROOT / "comment_feature_probes/summary.json")
    parser.add_argument("--output", type=Path, default=EXPERIMENT_RESULTS_ROOT / "comment_content_groups")
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument("--llm-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--cache-root", type=Path, default=LLM_SURPRISAL_CACHE_ROOT)
    parser.add_argument("--reuse-statistics", action="store_true")
    args = parser.parse_args()
    prior = json.loads(args.reference_summary.read_text())
    screen = json.loads(Path(prior["screen_summary"]).read_text())
    args.llm_model, args.embedding_models = screen["llm_model"], list(COGNASCORE_EMBEDDING_MODELS)
    args.alpha, args.seed, args.folds = prior["parameters"]["alpha"], prior["parameters"]["seed"], prior["parameters"]["folds"]
    selected = prior["results"]["original"]["features"]
    other = [name for name in selected if name != COMMENT]
    if len(selected) != 24 or len(other) != 23:
        raise ValueError("Expected fixed original24/other23")
    matrices, _, _, checksums = load_matrices(args)
    predictor_model = screen["predictor_embedding_model"]
    args.output.mkdir(parents=True, exist_ok=True)
    if args.reuse_statistics:
        saved = json.loads((args.output / "summary.json").read_text())
        if saved["classifier_source_sha256"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
            raise ValueError("Classifier changed since saved statistics; strict reaggregation required")
        statistics = pd.read_csv(args.output / "comment_content_statistics.csv")
        occurrences = pd.read_csv(args.output / "comment_occurrences.csv")
        for dataset, part in statistics.groupby("dataset"):
            items = {item.task_id: item_source_sha256(item) for item in load_code_dataset(DATASETS[dataset].path)}
            if any(items[row.task_id] != row.source_sha256 for row in part.itertuples()):
                raise ValueError("Reused statistics have stale sources")
    else:
        statistics, occurrences = derive_statistics(matrices[predictor_model], args)
        statistics.to_csv(args.output / "comment_content_statistics.csv", index=False)
        occurrences.to_csv(args.output / "comment_occurrences.csv", index=False)
    frames = {model: attach(matrix, statistics) for model, matrix in matrices.items()}
    reference = frames[predictor_model]
    dataset = "java_comparative_obfuscation"
    items = {item.task_id: item for item in load_code_dataset(DATASETS[dataset].path)}
    tables = []
    for family, root, model in (("base", args.base_root, predictor_model), ("embedding", args.embedding_root, predictor_model), ("llm", args.llm_root, args.llm_model)):
        path = root / dataset / model_slug(model) / "features.csv"
        tables.append(load_table(path, family, items, dataset=dataset, llm=family == "llm"))
        checksums[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    if any(checksums.get(path) != value for path, value in prior["input_csv_sha256"].items()):
        raise ValueError("Reference input hashes changed")
    constructed = tables[0]
    for table in tables[1:]:
        constructed = constructed.merge(table.drop(columns="readability_score"), on=["dataset", "task_id"], validate="one_to_one")
    if args.reuse_statistics:
        constructed_statistics = pd.read_csv(args.output / "java_comment_content_statistics.csv")
        for row in constructed_statistics.itertuples():
            if item_source_sha256(items[row.task_id]) != row.source_sha256:
                raise ValueError("Reused Java statistics have stale source")
        constructed_occurrences = pd.read_csv(args.output / "java_comment_occurrences.csv")
    else:
        constructed_statistics, constructed_occurrences = derive_statistics(constructed, args)
        constructed_statistics.to_csv(args.output / "java_comment_content_statistics.csv", index=False)
        constructed_occurrences.to_csv(args.output / "java_comment_occurrences.csv", index=False)
    constructed = attach(constructed, constructed_statistics)
    prose = PREFIX + "prose__bpb_mean"
    decomposition = [PREFIX + group + "__bpb_mean" for group in GROUPS]
    experiments = (("original24", selected, [COMMENT]), ("without_comment", other, []), ("prose_only", other + [prose], [prose]), ("content_decomposition", other + decomposition, decomposition))
    payload = {"classifier_version": CLASSIFIER_VERSION, "classifier_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "parameters": {"alpha": args.alpha, "seed": args.seed, "folds": args.folds}, "input_csv_sha256": checksums, "reference_input_csv_sha256": prior["input_csv_sha256"], "reference_summary": str(args.reference_summary), "reference_summary_sha256": hashlib.sha256(args.reference_summary.read_bytes()).hexdigest(), "inference_performed": False, "production_or_frozen_modified": False, "classification_uses_readability_labels": False, "expected_direction": {"prose": -1, **{group: None for group in GROUPS if group != "prose"}}, "prospective_hypotheses": {"prose": "Explanatory prose BPB is intended negative prediction difficulty, unchanged after outcomes.", "code_like": "Standalone operational code-like content conflates code-expression difficulty with comment language difficulty; no explanatory-load direction assigned.", "separator_metadata": "Punctuation separators and explicit license/provenance are not explanatory cognitive load; treat as nuisance groups, not automatically valid readability signals.", "mixed_unknown": "Occurrences with mixed mechanisms or insufficient evidence remain separate; do not force an explanatory label."}, "classifier_precedence": "separator -> complete operational code -> mixed code/prose or provenance/prose -> explicit license/provenance -> descriptive prose -> unknown. Syntax form is provenance only. Full parse plus operational syntax prevents semicolon-alone code classification; documentation @param/@return descriptions are not metadata merely because they have a tag.", "measurement": "Existing global original-source token loss reaggregated over whole original comment intervals, including markers. Group mean is union-covered UTF-8 byte-weighted BPB; classification-normalized body is never rescored. Missing groups are NaN/absent applicability, not zero BPB; predictor medians fit within each training fold.", "limitations": "Conservative English-word prose evidence, not proof of author intent/explanatory validity. Pure code-like can be an example, not necessarily disabled code. Parser lexical-only Python fragments retain AST docstring false-negative uncertainty; no guessed roles. Some valid code fragments and short explanatory labels remain unknown. Development-data diagnostic, not independent validation.", "group_counts": {group: {"occurrences": int((occurrences.content_group == group).sum()), "core_samples": int((statistics[group + '__occurrence_count'] > 0).sum()), "covered_bytes": float(statistics[group + '__covered_bytes'].sum())} for group in GROUPS}, "group_counts_by_dataset": occurrences.groupby(["dataset", "content_group"]).size().reset_index(name="occurrences").to_dict("records"), "comment_detection_status": {"unavailable": int((~statistics.comment_detection_available).sum()), "available_no_detected_comments": int((statistics.comment_detection_available & (statistics.detected_comment_count == 0)).sum())}, "first_actual_examples": {group: occurrences.loc[occurrences.content_group == group, ["dataset", "task_id", "source_sha256", "language", "start", "end", "syntax_form", "reason", "raw_comment"]].head(5).to_dict("records") for group in GROUPS}, "results": {}}
    (args.output / "coverage.json").write_text(json.dumps({key: payload[key] for key in ("classifier_version", "group_counts", "group_counts_by_dataset", "comment_detection_status", "first_actual_examples")}, indent=2, allow_nan=False) + "\n")
    for name, features, probes in experiments:
        result, fit, predictions = evaluate(reference, features, probes, args)
        baseline_name = "original" if name == "original24" else "without_comment" if name == "without_comment" else None
        if baseline_name and any(result[metric] != prior["results"][baseline_name][metric] for metric in ("pooled_cv", "lodo")):
            raise ValueError("Fixed baseline no longer exactly reproduced")
        predictions.to_csv(args.output / f"{name}_predictions.csv", index=False)
        rows = prediction_rows(constructed, fit.predict(constructed[features].to_numpy(float)), items)
        pd.DataFrame(rows).to_csv(args.output / f"{name}_java_predictions.csv", index=False)
        result["constructed"] = {dataset: summarize_paired_variants(rows)}
        result["full_five_embedding_fits"] = {}
        for model, frame in frames.items():
            model_fit = fit if model == predictor_model else fit_ridge(frame, np.ones(len(frame), bool), args.alpha, features)
            coefficients = {feature: float(value) for feature, value in zip(features, model_fit.named_steps["ridge"].coef_)}
            baseline = coefficients if name == "original24" else payload["results"]["original24"]["full_five_embedding_fits"][model]["coefficients"]
            result["full_five_embedding_fits"][model] = {"coefficients": coefficients, "probe_coefficients": {feature: coefficients[feature] for feature in probes}, "retained_sign_changes": {feature: {"original": baseline[feature], "candidate": coefficients[feature]} for feature in other if baseline[feature] * coefficients[feature] < 0}}
        payload["results"][name] = result
        (args.output / "summary.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
        print(f"{name}: pooled={result['pooled_cv']['unweighted_mean']:.6f}, LODO={result['lodo']['unweighted_mean']:.6f}, coefs={ {feature: diagnostic['coefficient'] for feature, diagnostic in result['probes'].items()} }", flush=True)


if __name__ == "__main__":
    main()
