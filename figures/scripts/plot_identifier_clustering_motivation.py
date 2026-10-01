"""Render a real readability-model identifier-clustering example.

The source is an unchanged method from the official Scalabrino dataset.
Identifier chunks come from the readability-model Java extractor, embeddings come
from the existing cache, and clustering uses a production pipeline rule.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "readability_model_matplotlib")
)

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pygments import lex
from pygments.lexers.jvm import JavaLexer
from pygments.token import Comment, Keyword, Literal, Name, Number, Operator, String, Token
from sklearn.cluster import KMeans, OPTICS
from sklearn.metrics import silhouette_score

from src.datasets.code import load_code_dataset
from src.methods.readability_model.embedding_cache import EmbeddingCache, embedding_cache_path
from src.methods.readability_model.embedding_features import AUTO_KMEANS_K_VALUES
from src.methods.readability_model.extractors.factory import extractor_for_language

DEFAULT_DATASET = ROOT / "datasets" / "scalabrino" / "dataset"
DEFAULT_CACHE_ROOT = ROOT / "artifacts" / "cognascore" / "embeddings"
DEFAULT_OUTPUT = (
    ROOT / "figures" / "publication" / "identifier_clustering_motivation.pdf"
)
DEFAULT_MODEL = "nomic-ai/nomic-embed-text-v1.5"
DEFAULT_TASK_ID = "Scalabrio189"
DEFAULT_CLUSTERING_METHOD = "optics"

INK = "#172033"
MUTED = "#667085"
LINE = "#CBD5E1"
LIGHT_LINE = "#E7ECF2"
CLUSTER_COLORS = ("#0072B2", "#D97706", "#00875A", "#A8558E")
NOISE_COLOR = "#64748B"
JAVA_LEXER = JavaLexer()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--embedding-model", default=DEFAULT_MODEL)
    parser.add_argument("--embedding-cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--random-state", type=int, default=0)
    parser.add_argument(
        "--clustering-method",
        choices=("optics", "auto-kmeans"),
        default=DEFAULT_CLUSTERING_METHOD,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    item = next(
        (item for item in load_code_dataset(args.dataset) if item.task_id == args.task_id),
        None,
    )
    if item is None:
        raise SystemExit(f"Task {args.task_id!r} was not found in {args.dataset}")

    extractor = extractor_for_language(
        item.metadata.get("language"),
        allow_fragments=item.metadata.get("source_form") == "snippet",
    )
    chunks, _ = extractor.extract_with_member_fallback(item.content)
    identifier_chunks = unique_identifier_chunks(chunks)
    if len(identifier_chunks) < 3:
        raise SystemExit("The selected example has fewer than three unique identifier chunks")

    texts = [chunk.lexeme for chunk in identifier_chunks]
    cache_path = embedding_cache_path(args.embedding_cache_root, args.embedding_model)
    if not cache_path.is_file():
        raise SystemExit(f"Embedding cache not found: {cache_path}")
    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        vectors_by_text = cache.vectors_for_texts(texts)
    missing = [text for text in texts if text not in vectors_by_text]
    if missing:
        raise SystemExit(f"Missing cached embeddings for: {missing}")

    vectors = np.stack([vectors_by_text[text] for text in texts]).astype(np.float64)
    vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
    if args.clustering_method == "optics":
        min_samples, labels = automatic_optics(vectors)
        score = non_noise_silhouette(vectors, labels)
        console_detail = f"OPTICS · min_samples = {min_samples} · xi = 0.05"
    else:
        selected_k, score, labels = automatic_kmeans(
            vectors,
            candidate_k=AUTO_KMEANS_K_VALUES,
            random_state=args.random_state,
        )
        console_detail = f"automatic K-means · k = {selected_k}"
    labels = canonicalize_labels(labels)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    render_figure(
        source=item.content,
        task_id=item.task_id,
        chunks=identifier_chunks,
        labels=labels,
        output=args.output,
    )
    print(f"{console_detail}; non-noise cosine silhouette={score:.6f}")
    for label in sorted(set(labels)):
        members = [text for text, member_label in zip(texts, labels) if member_label == label]
        name = "Noise" if label == -1 else f"Cluster {label + 1}"
        print(f"{name}: {', '.join(members)}")
    print(f"Wrote {args.output}")


def unique_identifier_chunks(chunks: Sequence[object]) -> list[object]:
    """Retain first occurrences in source order for the identifier-only view."""
    seen: set[str] = set()
    selected = []
    for chunk in chunks:
        if chunk.type != "IDENTIFIER" or chunk.lexeme in seen:
            continue
        seen.add(chunk.lexeme)
        selected.append(chunk)
    return selected


def automatic_kmeans(
    vectors: np.ndarray,
    *,
    candidate_k: Sequence[int],
    random_state: int,
) -> tuple[int, float, np.ndarray]:
    """Use the production candidate grid and cosine-silhouette selection rule."""
    best: tuple[float, int, np.ndarray] | None = None
    distinct_vector_count = len(np.unique(vectors, axis=0))
    for k in candidate_k:
        if len(vectors) <= k or distinct_vector_count < k:
            continue
        labels = KMeans(n_clusters=k, n_init=10, random_state=random_state).fit_predict(vectors)
        score = float(silhouette_score(vectors, labels, metric="cosine"))
        candidate = (score, int(k), labels)
        if best is None or candidate[0] > best[0]:
            best = candidate
    if best is None:
        raise ValueError("No valid K-means candidate for the selected chunks")
    score, k, labels = best
    return k, score, labels


def automatic_optics(vectors: np.ndarray) -> tuple[int, np.ndarray]:
    """Apply the production OPTICS rule without selecting a cluster count."""
    min_samples = max(2, int(round(math.log2(max(len(vectors), 2)))))
    min_samples = min(min_samples, len(vectors))
    labels = OPTICS(min_samples=min_samples, xi=0.05, metric="cosine").fit_predict(vectors)
    return min_samples, labels


def non_noise_silhouette(vectors: np.ndarray, labels: np.ndarray) -> float:
    keep = labels != -1
    retained_labels = set(int(label) for label in labels[keep])
    if keep.sum() <= len(retained_labels) or len(retained_labels) < 2:
        return float("nan")
    return float(silhouette_score(vectors[keep], labels[keep], metric="cosine"))


def canonicalize_labels(labels: np.ndarray) -> np.ndarray:
    """Renumber non-noise labels by first source occurrence for display."""
    order: dict[int, int] = {}
    for label in (int(value) for value in labels):
        if label == -1:
            continue
        order.setdefault(label, len(order))
    return np.asarray([-1 if int(label) == -1 else order[int(label)] for label in labels], dtype=int)


def render_figure(
    *,
    source: str,
    task_id: str,
    chunks: Sequence[object],
    labels: np.ndarray,
    output: Path,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    display_source, is_excerpt = source_for_display(task_id, source)
    fig = plt.figure(figsize=(7.2, 2.55), facecolor="white")
    source_ax = fig.add_axes((0.012, 0.055, 0.445, 0.89))
    embedding_ax = fig.add_axes((0.533, 0.17, 0.06, 0.72))
    clusters_ax = fig.add_axes((0.663, 0.105, 0.325, 0.79))
    for axis in (source_ax, embedding_ax, clusters_ax):
        setup_panel(axis)

    draw_source_panel(
        source_ax,
        display_source,
        is_excerpt=is_excerpt,
        selected_lexemes={chunk.lexeme for chunk in chunks},
    )
    draw_embedding_panel(embedding_ax)
    draw_cluster_panel(clusters_ax, chunks, labels)
    draw_arrow(fig, 0.465, 0.50, 0.523, "snippets")
    draw_arrow(fig, 0.601, 0.50, 0.659, "vectors")
    fig.savefig(output, format="pdf", facecolor="white", bbox_inches="tight", pad_inches=0.018)
    plt.close(fig)


def setup_panel(axis: plt.Axes) -> None:
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")


def panel_heading(
    axis: plt.Axes,
    title: str,
    *,
    heading_y: float = 0.931,
    rule_y: float = 0.875,
    fontsize: float = 8.0,
) -> None:
    axis.text(
        0.04,
        heading_y,
        title,
        color=INK,
        fontsize=fontsize,
        fontweight="bold",
        va="center",
    )
    axis.plot((0.035, 0.965), (rule_y, rule_y), color=LINE, linewidth=0.55)


def draw_panel_shell(axis: plt.Axes, facecolor: str) -> None:
    """Draw one light rounded surface for a pipeline stage."""
    axis.add_patch(
        FancyBboxPatch(
            (0.014, 0.024),
            0.962,
            0.962,
            boxstyle="round,pad=0.012,rounding_size=0.032",
            facecolor=facecolor,
            edgecolor="#C9D3DF",
            linewidth=0.6,
            zorder=1,
        )
    )


def source_for_display(task_id: str, source: str) -> tuple[str, bool]:
    """Return a compact, explicitly marked excerpt for the long paper example."""
    if task_id != "Scalabrio189":
        return source, False
    excerpt = """@Test
@Priority(10)
public void initData() {
  EntityManager em = getEntityManager();
  PropertyOverrideEntity propertyEntity = ...;
  propertyEntityId = propertyEntity.getId();
  ...
  TransitiveOverrideEntity transitiveEntity = ...;
  transitiveEntityId = transitiveEntity.getId();
  ...
  AuditedSpecialEntity auditedEntity = ...;
  auditedEntityId = auditedEntity.getId();
  ...
  propertyTable = ...;
  transitiveTable = ...;
  auditedTable = ...;
}"""
    return excerpt, True


def draw_source_panel(
    axis: plt.Axes,
    source: str,
    *,
    is_excerpt: bool,
    selected_lexemes: set[str],
) -> None:
    draw_panel_shell(axis, "#F3F7FC")
    title = "Source excerpt" if is_excerpt else "Original source"
    panel_heading(axis, title)
    # Compress indentation only for display; source tokens are unchanged.
    display_source = source.expandtabs(2).strip()
    highlighted_lines = highlighted_java_lines(display_source)
    lines = display_source.splitlines()
    start_y = 0.84
    line_height = min(0.049, 0.79 / max(len(highlighted_lines) - 1, 1))
    panel_width_points = axis.figure.get_figwidth() * axis.get_position().width * 72
    max_columns = max((len(line) for line in lines), default=1)
    code_width = 0.95
    font_size = min(6.65, code_width * panel_width_points / (0.61 * max_columns))
    char_step = 0.61 * font_size / panel_width_points
    for index, segments in enumerate(highlighted_lines):
        y = start_y - index * line_height
        column = 0
        for text, color, weight in segments:
            if text:
                selected = text in selected_lexemes
                axis.text(
                    0.05 + column * char_step,
                    y,
                    text,
                    family="DejaVu Sans Mono",
                    fontsize=font_size,
                    fontweight="bold" if selected else weight,
                    color="#075985" if selected else color,
                    va="top",
                    clip_on=True,
                    bbox=(
                        {
                            "boxstyle": "round,pad=0.045",
                            "facecolor": "#DDF2FE",
                            "edgecolor": "#38BDF8",
                            "linewidth": 0.45,
                        }
                        if selected
                        else None
                    ),
                )
            column += len(text)


def highlighted_java_lines(source: str) -> list[list[tuple[str, str, str]]]:
    """Return Pygments-backed Java highlighting while preserving columns."""
    lines: list[list[tuple[str, str, str]]] = [[]]
    for token_type, value in lex(source, JAVA_LEXER):
        pieces = value.split("\n")
        for index, piece in enumerate(pieces):
            if piece:
                lines[-1].append((piece, java_token_color(token_type), java_token_weight(token_type)))
            if index < len(pieces) - 1:
                lines.append([])
    if lines and not lines[-1]:
        lines.pop()
    return lines


def java_token_color(token_type: Token) -> str:
    if token_type in Comment:
        return "#16803A"
    if token_type in Keyword.Type or token_type in Name.Class:
        return "#0369A1"
    if token_type in Keyword:
        return "#6D28D9"
    if token_type in Name.Function:
        return "#1D4ED8"
    if token_type in String or token_type in Literal.String:
        return "#B45309"
    if token_type in Number or token_type in Literal.Number:
        return "#C2410C"
    if token_type in Operator:
        return "#BE185D"
    if token_type in Token.Punctuation:
        return "#475569"
    return INK


def java_token_weight(token_type: Token) -> str:
    if token_type in Keyword or token_type in Name.Class or token_type in Name.Function:
        return "bold"
    return "normal"


def draw_embedding_panel(axis: plt.Axes) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (0.014, 0.024),
            0.962,
            0.962,
            boxstyle="round,pad=0.012,rounding_size=0.09",
            facecolor="#F1EDFA",
            edgecolor="#8B7BB8",
            linewidth=1.0,
        )
    )
    axis.text(
        0.5,
        0.50,
        "Embedding model",
        ha="center",
        va="center",
        fontsize=7.8,
        fontweight="bold",
        color="#4C3C78",
        rotation=90,
    )


def draw_cluster_panel(
    axis: plt.Axes,
    chunks: Sequence[object],
    labels: np.ndarray,
) -> None:
    draw_panel_shell(axis, "#F2F8F5")
    panel_heading(axis, "Automatic clustering", fontsize=8.6)
    ordered_labels = sorted(label for label in set(int(value) for value in labels) if label != -1)
    if -1 in labels:
        ordered_labels.append(-1)
    groups = [
        (label, [chunk.lexeme for chunk, member_label in zip(chunks, labels) if member_label == label])
        for label in ordered_labels
    ]
    for index, (label, members) in enumerate(groups):
        color = cluster_color(label)
        column = index % 2
        row = index // 2
        x = 0.055 + 0.455 * column
        y = 0.765 - 0.385 * row
        axis.add_patch(
            FancyBboxPatch(
                (x, y - 0.25),
                0.018,
                0.25,
                boxstyle="round,pad=0,rounding_size=0.006",
                facecolor=color,
                edgecolor="none",
            )
        )
        heading = "Noise" if label == -1 else f"Cluster {label + 1}"
        axis.text(
            x + 0.05,
            y,
            heading,
            fontsize=7.35,
            color=color,
            fontweight="bold",
            va="top",
        )
        member_lines = compact_member_lines(members)
        for member_index, member_line in enumerate(member_lines):
            axis.text(
                x + 0.05,
                y - 0.070 - member_index * 0.068,
                member_line,
                family="DejaVu Sans Mono",
                fontsize=6.25,
                color=INK,
                va="top",
                clip_on=True,
            )
    axis.plot((0.485, 0.485), (0.08, 0.825), color=LIGHT_LINE, linewidth=0.45)
    axis.plot((0.045, 0.955), (0.465, 0.465), color=LIGHT_LINE, linewidth=0.45)


def draw_arrow(fig: plt.Figure, x0: float, y: float, x1: float, label: str) -> None:
    arrow = FancyArrowPatch(
        (x0, y),
        (x1, y),
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.45,
        color="#374151",
    )
    fig.add_artist(arrow)
    fig.text(
        (x0 + x1) / 2,
        y - 0.050,
        label,
        ha="center",
        va="top",
        fontsize=7.5,
        color=MUTED,
        fontweight="normal",
    )


def draw_vertical_flow_arrow(
    fig: plt.Figure,
    x: float,
    y0: float,
    y1: float,
    label: str,
) -> None:
    arrow = FancyArrowPatch(
        (x, y0),
        (x, y1),
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.45,
        color="#374151",
    )
    fig.add_artist(arrow)
    fig.text(
        x + 0.016,
        (y0 + y1) / 2,
        label,
        ha="left",
        va="center",
        fontsize=7.5,
        color=MUTED,
    )


def compact_member_lines(members: Sequence[str]) -> list[str]:
    """Lay cluster members out compactly without shrinking the type."""
    return list(members)


def cluster_color(label: int) -> str:
    if label == -1:
        return NOISE_COLOR
    return CLUSTER_COLORS[label % len(CLUSTER_COLORS)]


if __name__ == "__main__":
    main()
