from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .clustering import (
    DBSCAN,
    EmbeddedLexeme,
    cluster_diameters,
    group_by_label,
    mean_cluster_diameter,
)
from .embeddings import NomicEmbedder, embed_lexemes
from .extractors.python import LexemeExtractor
from .visualization import VisualChunk, VisualizationRecord


@dataclass(frozen=True)
class CognaScoreResult:
    score: float
    avg_cluster_diameter: float
    cluster_count: int
    lexeme_count: int
    noise_lexeme_count: int
    wrapped_snippet: bool


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
            metadata={"wrapped_snippet": wrapped_snippet},
        )

    def score(self, code: str) -> CognaScoreResult:
        record = self.process(code)
        clusters = {key: values for key, values in record.clusters.items() if key >= 0}
        return CognaScoreResult(
            score=record.avg_diameter,
            avg_cluster_diameter=record.avg_diameter,
            cluster_count=len(clusters),
            lexeme_count=len(record.chunks),
            noise_lexeme_count=len(record.clusters.get(-1, [])),
            wrapped_snippet=bool(record.metadata["wrapped_snippet"]),
        )


def cognascore_model(code: str, **kwargs) -> CognaScoreResult:
    return CognaScoreScorer(**kwargs).score(code)
