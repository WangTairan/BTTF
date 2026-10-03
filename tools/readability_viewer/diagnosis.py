"""Use the published feature extractors and frozen 11-feature coefficients.

Source highlights identify the regions measured by a feature. They do not
allocate a global feature's Ridge contribution among individual tokens.
"""
from __future__ import annotations

import hashlib
import json
import math
import bisect
from collections import Counter
from pathlib import Path

import numpy as np

from src.datasets.types import DatasetItem
from src.methods.readability_model.feature_schema import feature_display_name, namespaced_feature

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "frozen_models/cognascore/consensus11_6dataset_three_llm_opencoder_jina/jinaai-jina-embeddings-v2-base-code/model.json"

# These explain measured properties, rather than asserting causal repairs.
DESCRIPTIONS = {
    "operator_density": ("How many operations are packed into each non-empty line.", "Consider separating dense computations into clearer steps."),
    "decision_density": ("How many comparisons are packed into each non-empty line.", "Consider separating tightly packed comparisons into clearer conditions."),
    "expression_literal_density": ("How many operations the code contains relative to literal values such as numbers and strings.", "Check whether computations and their values clearly convey the intended logic."),
    "longest_line_length": ("The length of the longest line, including comments and indentation.", "Consider breaking a long line at a natural boundary."),
    "computation_control_pattern_count": ("How many distinct groups of related computations and control decisions the code contains. These groups are identified by clustering their embedding vectors.", "Check whether related computations and decisions are grouped clearly."),
    "only_identifier__embedding_dispersion": ("How spread out the identifier names are in embedding space. Names that the embedding model represents similarly lie closer together.", "Check whether names make related concepts and responsibilities clear."),
    "assignment_value_surprisal": ("How unexpected the assigned values are given the preceding code.", "Consider explaining an opaque assigned value or naming its intermediate steps."),
    "literal_tail_surprisal": ("How unexpected the most unusual numbers and strings are given the preceding code.", "Consider explaining an unusual value or replacing an encoded value with a clearer form."),
    "identifier_onset_surprisal": ("How hard it is to anticipate the beginning of an identifier name from the preceding code.", "Check whether unexpected or generic names clearly convey their purpose."),
    "declaration_surprisal_variation": ("How much declarations differ in how easy they are to anticipate from preceding code.", "Check declarations that stand out from those around them."),
    "short_identifier_context_dependence": ("How much short names depend on information farther back in the code.", "Consider clarifying a short name near its use or choosing a more informative name."),
}


def model_metadata():
    return json.loads(ARTIFACT.read_text())


def decompose(values: dict, manifest: dict | None = None) -> dict:
    """Exactly replay the frozen imputation, clipping, scaling and Ridge score."""
    manifest = manifest or model_metadata()
    parameters = manifest["pipeline"]
    names = manifest["features"]["ordered_names"]
    raw = [values.get(name) for name in names]
    if any(name not in values for name in names):
        raise ValueError("All 11 feature keys must be present, including explicit missing values.")
    if any(value is not None and math.isinf(float(value)) for value in raw):
        raise ValueError("Feature extraction returned an infinite value.")
    missing = [value is None or math.isnan(float(value)) for value in raw]
    x = np.array([parameters["imputer_statistics"][i] if missing[i] else float(value)
                  for i, value in enumerate(raw)])
    clipped = np.clip(x, parameters["training_feature_min"], parameters["training_feature_max"])
    z = (clipped - parameters["scaler_mean"]) / parameters["scaler_scale"]
    contributions = z * parameters["ridge_coefficients"]
    unbounded = float(parameters["ridge_intercept"] + contributions.sum())
    score = float(np.clip(unbounded, *parameters["prediction_bounds"]))
    features = []
    for i, name in enumerate(names):
        description, suggestion = DESCRIPTIONS[name.split("__", 1)[1]]
        features.append({"key": name, "name": feature_display_name(name),
                         "family": name.split("__", 1)[0],
                         "value": None if missing[i] else float(raw[i]),
                         "standardized_value": float(z[i]),
                         "coefficient": parameters["ridge_coefficients"][i],
                         "contribution": float(contributions[i]),
                         "imputed": missing[i], "clipped": bool(x[i] != clipped[i]),
                         "description": description, "suggestion": suggestion})
    return {"score": score, "unbounded_score": unbounded,
            "intercept": parameters["ridge_intercept"],
            "output_clipped": score != unbounded, "features": features}


def source_regions(source, analysis, losses, feature):
    """Provide source-aligned evidence, separate from score attribution."""
    from src.methods.readability_model.llm_features.aggregate import _SourceLoss

    key = feature["key"].split("__", 1)[1]
    roles = {"assignment_value_surprisal": "assignment_rhs", "literal_tail_surprisal": "literal",
             "identifier_onset_surprisal": "identifier", "declaration_surprisal_variation": "declaration_header",
             "short_identifier_context_dependence": "identifier", "only_identifier__embedding_dispersion": "identifier"}
    loss = _SourceLoss(source, losses) if losses else None
    token_ends = [row.end for row in losses]
    spans = [span for span in analysis.spans if span.role == roles.get(key)]
    if key == "longest_line_length":
        lines = source.splitlines(keepends=True)
        index = max(range(len(lines)), key=lambda i: len(lines[i].rstrip("\r\n")))
        start = sum(len(line) for line in lines[:index])
        intervals = [(start, start + len(lines[index].rstrip("\r\n")), None)]
    elif key in {"operator_density", "decision_density"}:
        from src.methods.readability_model.visual_features import _tokens_by_line, _token_categories
        language = analysis.metadata["language"]
        _, operators, comparisons, literal_words = _token_categories(language)
        counted = operators if key == "operator_density" else comparisons
        line_numbers = {number for number, token in _tokens_by_line(source, language=language)
                        if token in counted and token not in literal_words}
        intervals = []
        start = 0
        for number, line in enumerate(source.splitlines(keepends=True), 1):
            if number in line_numbers:
                intervals.append((start, start + len(line.rstrip("\r\n")), None))
            start += len(line)
    elif key == "short_identifier_context_dependence" and feature["imputed"]:
        intervals = []
    elif key in roles:
        intervals = []
        for span in spans:
            if key == "short_identifier_context_dependence":
                from src.methods.readability_model.semantic_context import SHORT_IDENTIFIER_CANDIDATES
                if source[span.start:span.end] not in SHORT_IDENTIFIER_CANDIDATES:
                    continue
                cursor = bisect.bisect_right(token_ends, span.start)
                if any(row.start < span.end and (row.token_index // 32) * 32 <= 32
                       for row in losses[cursor:cursor + 64]):
                    continue
            start, end = span.start, span.end
            if key == "identifier_onset_surprisal":
                cursor = bisect.bisect_right(token_ends, start)
                first = losses[cursor] if cursor < len(losses) and losses[cursor].start < end else None
                if first is not None:
                    end = min(end, first.end)
            intervals.append((start, end, loss.q([(start, end)]) if loss else None))
        if key == "literal_tail_surprisal":
            if loss:
                intervals = sorted(intervals, key=lambda row: row[2] or 0, reverse=True)
                intervals = intervals[:max(1, math.ceil(len(intervals) * .2))]
    elif key in {"computation_control_pattern_count", "expression_literal_density"}:
        selected = {"computation_control_pattern_count": {"expression", "control_header"},
                    "expression_literal_density": {"expression", "literal"}}[key]
        intervals = [(span.start, span.end, None) for span in analysis.spans if span.role in selected]
    else:
        intervals = []
    return [{"start": start, "end": end, "line": source.count("\n", 0, start) + 1,
             "text": source[start:end], "bpb": bpb}
            for start, end, bpb in intervals]


class Analyzer:
    """Lazy local model loading; inference is serialized by the server."""
    def __init__(self, device="cpu"):
        self.device = device
        self.embedder = None
        self.scorer = None

    def analyze(self, source: str, language="java", fragments=False, *, allow_class_members=False):
        from src.methods.readability_model.feature_database import extract_feature_row
        from src.methods.readability_model.extractors.factory import extractor_for_language
        from src.methods.readability_model.embedding_features import _view_clustering_features
        from src.methods.readability_model.embeddings import NomicEmbedder
        from src.methods.readability_model.llm_features.scoring import LazyCausalScorer, TraceConfiguration
        from src.methods.readability_model.llm_features.source_spans import analyze_source
        from src.methods.readability_model.llm_features.aggregate import aggregate_features
        from src.methods.readability_model.runners.llm_surprisal_features import _has_context_targets
        from src.methods.readability_model.llm_features.cache import LLMTraceCache

        if not source.strip():
            raise ValueError("Enter non-empty source code.")
        if language not in {"java", "python", "c", "cpp", "cuda"}:
            raise ValueError("Choose Java, Python, C/C++ or CUDA.")
        if len(source.encode()) > 50_000:
            raise ValueError("The interactive viewer accepts up to 50 KB of source.")
        manifest = model_metadata()
        analysis = analyze_source(source, language, allow_fragments=fragments, allow_class_members=allow_class_members)
        item = DatasetItem("viewer", source, metadata={"language": language, "source_form": "snippet" if fragments else "program"})
        base = extract_feature_row(dataset="viewer", item=item)
        values = {namespaced_feature("base", key): value for key, value in base.items()}
        chunks, _ = extractor_for_language(language, allow_fragments=fragments).extract_with_member_fallback(source)
        counts = Counter((chunk.type, chunk.lexeme) for chunk in chunks)
        ordered = sorted(counts)
        if self.embedder is None:
            self.embedder = NomicEmbedder(manifest["embedding_model"], device=self.device, cache_dir=ROOT / "models")
        vectors = []
        for start in range(0, len(ordered), 32):
            vectors.extend(self.embedder.embed_texts([text for _, text in ordered[start:start + 32]]))
        vector_rows = [(kind, text, counts[(kind, text)], np.array(vector))
                       for (kind, text), vector in zip(ordered, vectors)]
        embedding = _view_clustering_features(vector_rows, total_source_count=len(chunks), max_vectors=512)
        values.update({namespaced_feature("embedding", key): value for key, value in embedding.items()})
        configuration = TraceConfiguration(model_name=manifest["llm_feature_model"],
            revision="32c4ba568028ffbacc81440697418304bac7f8e2", compute_dtype="float32", trust_remote_code=True)
        if self.scorer is None:
            self.scorer = LazyCausalScorer(configuration, device=self.device,
                                          cache_dir=ROOT / "models", local_files_only=True)
        source_hash = hashlib.sha256(source.encode()).hexdigest()
        from src.methods.readability_model.paths import LLM_SURPRISAL_CACHE_ROOT
        from src.methods.readability_model.results import model_slug
        traces = {"short": None, "long": None}
        with LLMTraceCache(LLM_SURPRISAL_CACHE_ROOT / model_slug(configuration.model_name) / "traces.sqlite") as cache:
            tokenized = self.scorer.tokenize(source)
            kinds = ("global", "short", "long") if _has_context_targets(analysis, tokenized, configuration) else ("global",)
            for kind in kinds:
                traces[kind] = self.scorer.score_trace(tokenized, kind=kind,
                    existing_losses=cache.get_trace(source_hash, configuration.fingerprint_for(kind), kind),
                    checkpoint=lambda trace_kind, next_token, losses: cache.append_window(
                        source_hash, configuration.fingerprint_for(trace_kind), trace_kind, next_token, losses))
        causal, metadata = aggregate_features(source, traces["global"], analysis,
            short_context_losses=traces["short"], long_context_losses=traces["long"])
        values.update(causal)
        result = decompose(values, manifest)
        for feature in result["features"]:
            feature["regions"] = source_regions(source, analysis, traces["global"], feature)
        result.update(source=source, language=language, source_sha256=source_hash,
                      model=manifest["name"], embedding_model=manifest["embedding_model"],
                      causal_model=manifest["llm_feature_model"],
                      manifest_sha256=hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
                      evidence_note="Highlights show measured source regions. Contributions belong to whole features, not individual tokens.",
                      parse_diagnostics=analysis.metadata, measurement_metadata=metadata)
        return result
