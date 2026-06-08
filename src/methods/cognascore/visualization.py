from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


TEMPLATE_PATH = Path(__file__).with_name("templates") / "visualize_template.html"


@dataclass(frozen=True)
class VisualChunk:
    line: int
    type: str
    lexeme: str

    def to_json(self) -> dict[str, Any]:
        return {"lexeme": self.lexeme, "line": self.line, "type": self.type}


@dataclass(frozen=True)
class VisualizationRecord:
    task_id: str
    source: str
    chunks: list[VisualChunk]
    clusters: dict[int, list[VisualChunk]]
    tsne: list[dict[str, Any]]
    avg_diameter: float = 0.0
    cluster_diameters: dict[int, float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "source": self.source,
            "chunks": [chunk.to_json() for chunk in self.chunks],
            "clusters": [
                {"id": cluster_id, "elements": [chunk.to_json() for chunk in elements]}
                for cluster_id, elements in sorted(self.clusters.items())
            ],
            "tsne": self.tsne,
            "avg_diameter": self.avg_diameter,
            "metadata": self.metadata,
            "cluster_diameters": {
                str(cluster_id): diameter
                for cluster_id, diameter in (self.cluster_diameters or {}).items()
                if cluster_id >= 0
            },
        }


def write_visualization(
    out_dir: Path,
    *,
    dataset: str = "single-file",
    description: str = "Python visualization",
    records: list[VisualizationRecord] | None = None,
    data_jsonl: Path | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    if data_jsonl is not None:
        jsonl = data_jsonl.read_text(encoding="utf-8")
    else:
        jsonl = build_jsonl(dataset, description, records or [])

    (out_dir / "data.jsonl").write_text(jsonl, encoding="utf-8")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace('"__COGNASCORE_JSONL__"', json.dumps(jsonl), 1)
    (out_dir / "visualize.html").write_text(html, encoding="utf-8")


def build_jsonl(dataset: str, description: str, records: list[VisualizationRecord]) -> str:
    lines = [json.dumps({"meta": {"dataset": dataset, "description": description}}, ensure_ascii=False)]
    lines.extend(json.dumps(record.to_json(), ensure_ascii=False) for record in records)
    return "\n".join(lines) + "\n"
