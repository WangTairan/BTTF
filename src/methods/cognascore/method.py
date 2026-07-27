from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from statistics import mean, pstdev

from src.methods.posnett.method import posnett_model

from .clustering import (
    DBSCAN,
    EmbeddedLexeme,
    cluster_diameters,
    group_by_label,
    mean_cluster_diameter,
)
from .embeddings import NomicEmbedder, embed_lexemes
from .extractors.python import LexemeExtractor
from .generalized import FORMULA, score_from_values
from .visualization import VisualChunk, VisualizationRecord


@dataclass(frozen=True)
class CognaScoreResult:
    score: float
    formula: str
    log_vocabulary_size: float
    noise_ratio: float
    avg_cluster_diameter: float
    cluster_count: int
    lexeme_count: int
    noise_lexeme_count: int
    wrapped_snippet: bool
    statistics: dict[str, float]


class CognaScoreScorer:
    def __init__(
        self,
        model_name: str = NomicEmbedder.DEFAULT_MODEL,
        eps: float = 0.18,
        min_pts: int = 2,
        batch_size: int = 32,
        device: str | None = None,
        cache_dir: Path | str | None = NomicEmbedder.DEFAULT_CACHE_DIR,
    ) -> None:
        self.model_name = model_name
        self.eps = eps
        self.min_pts = min_pts
        self.batch_size = batch_size
        self.extractor = LexemeExtractor()
        self.extractor.require_parser()
        self.embedder = NomicEmbedder(model_name=model_name, device=device, cache_dir=cache_dir)

    def process(self, code: str, task_id: str = "single-file") -> VisualizationRecord:
        chunks, wrapped_snippet = self.extractor.extract_with_member_fallback(code)
        chunks.sort(key=lambda chunk: (chunk.line, chunk.lexeme))
        vectors = embed_lexemes(chunks, self.embedder, batch_size=self.batch_size)
        embedded = [
            EmbeddedLexeme(
                line=chunk.line,
                type=chunk.type,
                lexeme=chunk.lexeme,
                embedding=vector,
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        labels = DBSCAN(eps=self.eps, min_pts=self.min_pts).fit(embedded)
        groups = group_by_label(embedded, labels)
        diameters = cluster_diameters(groups)
        statistics = _cluster_statistics(embedded, labels, groups, diameters)
        noise_count = len(groups.get(-1, []))
        noise_ratio = noise_count / len(embedded) if embedded else 0.0
        vocabulary_size = posnett_model(code).vocabulary_size
        generalized_score = score_from_values(vocabulary_size, noise_ratio)
        return VisualizationRecord(
            task_id=task_id,
            source=code,
            chunks=[VisualChunk(line=item.line, type=item.type, lexeme=item.lexeme) for item in chunks],
            clusters={
                label: [
                    VisualChunk(line=item.line, type=item.type, lexeme=item.lexeme)
                    for item in items
                ]
                for label, items in groups.items()
            },
            tsne=[],
            avg_diameter=mean_cluster_diameter(diameters),
            cluster_diameters=diameters,
            metadata={
                "wrapped_snippet": wrapped_snippet,
                "statistics": statistics,
                "generalized_score": generalized_score,
                "generalized_formula": FORMULA,
                "vocabulary_size": vocabulary_size,
                "log_vocabulary_size": math.log1p(vocabulary_size),
                "noise_ratio": noise_ratio,
            },
        )

    def score(self, code: str) -> CognaScoreResult:
        record = self.process(code)
        clusters = {key: values for key, values in record.clusters.items() if key >= 0}
        return CognaScoreResult(
            score=float(record.metadata["generalized_score"]),
            formula=str(record.metadata["generalized_formula"]),
            log_vocabulary_size=float(record.metadata["log_vocabulary_size"]),
            noise_ratio=float(record.metadata["noise_ratio"]),
            avg_cluster_diameter=record.avg_diameter,
            cluster_count=len(clusters),
            lexeme_count=len(record.chunks),
            noise_lexeme_count=len(record.clusters.get(-1, [])),
            wrapped_snippet=bool(record.metadata["wrapped_snippet"]),
            statistics=dict(record.metadata["statistics"]),
        )


def cognascore_model(code: str, **kwargs) -> CognaScoreResult:
    return CognaScoreScorer(**kwargs).score(code)


def _cluster_statistics(embedded, labels, groups, diameters) -> dict[str, float]:
    statistics: dict[str, float] = {}
    cluster_sizes = [len(items) for label, items in groups.items() if label >= 0]
    diameter_values = list(diameters.values())
    _add_distribution(statistics, "cluster_size", cluster_sizes)
    _add_distribution(statistics, "cluster_diameter", diameter_values)

    types = sorted({item.type for item in embedded})
    for chunk_type in types:
        prefix = f"type_{chunk_type.lower()}"
        typed = [(item, label) for item, label in zip(embedded, labels) if item.type == chunk_type]
        typed_groups: dict[int, list[EmbeddedLexeme]] = {}
        for item, label in typed:
            typed_groups.setdefault(label, []).append(item)
        typed_cluster_sizes = [len(items) for label, items in typed_groups.items() if label >= 0]
        typed_diameters = cluster_diameters(typed_groups)
        statistics[f"{prefix}_count"] = float(len(typed))
        statistics[f"{prefix}_noise_ratio"] = (
            len(typed_groups.get(-1, [])) / len(typed) if typed else 0.0
        )
        statistics[f"{prefix}_cluster_count"] = float(len(typed_cluster_sizes))
        _add_distribution(statistics, f"{prefix}_cluster_size", typed_cluster_sizes)
        _add_distribution(statistics, f"{prefix}_cluster_diameter", list(typed_diameters.values()))
    return statistics


def _add_distribution(target: dict[str, float], prefix: str, values) -> None:
    numeric = [float(value) for value in values]
    target[f"{prefix}_mean"] = mean(numeric) if numeric else 0.0
    target[f"{prefix}_std"] = pstdev(numeric) if len(numeric) > 1 else 0.0
    target[f"{prefix}_max"] = max(numeric, default=0.0)
