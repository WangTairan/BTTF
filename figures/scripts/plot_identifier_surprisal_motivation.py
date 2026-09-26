#!/usr/bin/env python3
"""Measure and plot identifier surprisal under one fixed code context.

Each candidate replaces the complete variable binding, but only its declaration
occurrence is measured, so every prediction sees exactly the same preceding
source text. BPB normalizes the measured information by the identifier's UTF-8
length. By default the script performs causal-LM inference, writes the auditable
measurements to CSV, and renders the publication PDF. Use ``--render-only`` to
redraw the stored measurements without loading a model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "readability_matplotlib")
)

import matplotlib.pyplot as plt
from matplotlib import colors as mpl_colors
from matplotlib.patches import FancyBboxPatch

from src.methods.readability_model.llm_features.scoring import (
    LazyCausalScorer,
    TraceConfiguration,
)
from src.methods.readability_model.llm_features.types import (
    DEFAULT_CAUSAL_LM,
    DEFAULT_CAUSAL_LM_REVISION,
    TokenLoss,
)


SOURCE_PATH = (
    ROOT
    / "datasets"
    / "schnappinger"
    / "aoi"
    / "sourcefiles"
    / "ArtOfIllusion"
    / "src"
    / "artofillusion"
    / "CreatePolygonTool.java"
)
ORIGINAL_METHOD = textwrap.dedent(
    """\
    public void mouseDragged(WidgetMouseEvent e, ViewerCanvas view)
    {
      findPoints(e.getPoint(), e.isShiftDown());
      int x[] = new int [points.length], y[] = new int [points.length];
      for (int i = 0; i < points.length; i++)
      {
        x[i] = (int) points[i].x;
        y[i] = (int) points[i].y;
      }
      view.drawDraggedShape(new Polygon(x, y, x.length));
    }
    """
)
PREFIX = (
    "public void mouseDragged(WidgetMouseEvent e, ViewerCanvas view)\n"
    "{\n"
    "  findPoints(e.getPoint(), e.isShiftDown());\n"
    "  int "
)
SUFFIX_TEMPLATE = (
    "[] = new int [points.length], y[] = new int [points.length];\n"
    "  for (int i = 0; i < points.length; i++)\n"
    "  {\n"
    "    {identifier}[i] = (int) points[i].x;\n"
    "    y[i] = (int) points[i].y;\n"
    "  }\n"
    "  view.drawDraggedShape(new Polygon({identifier}, y, {identifier}.length));\n"
    "}\n"
)
EXAMPLES = (
    ("Descriptive", "xPositions"),
    ("Concise", "x"),
    ("Related", "screenXPos"),
    ("Generic", "arrayValue"),
    ("Meaningless", "tmp"),
    ("Misleading", "invoiceSum"),
    ("Obfuscated", "var_x9z"),
)

INK = "#172033"
MUTED = "#667085"
LINE = "#D6DEE8"
GRID = "#E9EEF4"
DEFAULT_DATA = ROOT / "figures" / "data" / "identifier_surprisal_motivation.csv"
DEFAULT_OUTPUT = (
    ROOT / "figures" / "publication" / "identifier_surprisal_motivation.pdf"
)


@dataclass(frozen=True)
class Measurement:
    semantic_fit: str
    identifier: str
    utf8_bytes: int
    token_count: int
    allocated_bits: float
    bits_per_byte: float
    model: str
    revision: str
    prefix_sha256: str
    source_path: str
    source_sha256: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_CAUSAL_LM)
    parser.add_argument("--revision", default=DEFAULT_CAUSAL_LM_REVISION)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--data-output", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.render_only:
        measurements = read_measurements(args.data_output)
    else:
        measurements = measure(args)
        write_measurements(args.data_output, measurements)
    validate_measurements(measurements)
    render(args.output, measurements)
    print(f"Wrote {args.output}")
    if not args.render_only:
        print(f"Wrote {args.data_output}")


def measure(args: argparse.Namespace) -> list[Measurement]:
    repository_source = SOURCE_PATH.read_text(encoding="utf-8")
    if textwrap.indent(ORIGINAL_METHOD, "  ") not in repository_source:
        raise ValueError(f"The pinned source method was not found in {SOURCE_PATH}")
    source_hash = hashlib.sha256(ORIGINAL_METHOD.encode("utf-8")).hexdigest()
    source_path = str(SOURCE_PATH.relative_to(ROOT))
    configuration = TraceConfiguration(
        model_name=args.model,
        revision=args.revision,
        compute_dtype="float32",
    )
    scorer = LazyCausalScorer(
        configuration,
        device=args.device,
        cache_dir=args.cache_dir,
        local_files_only=not args.allow_download,
    )
    prefix_hash = hashlib.sha256(PREFIX.encode("utf-8")).hexdigest()
    rows = []
    for semantic_fit, identifier in EXAMPLES:
        source = PREFIX + identifier + SUFFIX_TEMPLATE.replace(
            "{identifier}", identifier
        )
        start = len(PREFIX)
        end = start + len(identifier)
        tokenized = scorer.tokenize(source)
        losses = scorer.score_trace(tokenized, kind="global")
        bits, covered_bytes, token_count = span_information(
            source, losses, start, end
        )
        rows.append(
            Measurement(
                semantic_fit=semantic_fit,
                identifier=identifier,
                utf8_bytes=len(identifier.encode("utf-8")),
                token_count=token_count,
                allocated_bits=bits,
                bits_per_byte=bits / covered_bytes,
                model=args.model,
                revision=args.revision,
                prefix_sha256=prefix_hash,
                source_path=source_path,
                source_sha256=source_hash,
            )
        )
    return rows


def span_information(
    source: str, losses: list[TokenLoss], start: int, end: int
) -> tuple[float, int, int]:
    """Allocate each overlapping token's loss uniformly over its source bytes."""
    bits = 0.0
    covered_bytes = 0
    token_count = 0
    for row in losses:
        left, right = max(start, row.start), min(end, row.end)
        if left >= right:
            continue
        token_bytes = len(source[row.start : row.end].encode("utf-8"))
        overlap_bytes = len(source[left:right].encode("utf-8"))
        if token_bytes <= 0:
            raise ValueError("A scored token covers no UTF-8 source bytes")
        bits += row.nll / math.log(2.0) * overlap_bytes / token_bytes
        covered_bytes += overlap_bytes
        token_count += 1
    expected_bytes = len(source[start:end].encode("utf-8"))
    if covered_bytes != expected_bytes:
        raise ValueError(
            f"Identifier coverage mismatch: expected {expected_bytes}, got {covered_bytes}"
        )
    return bits, covered_bytes, token_count


def write_measurements(path: Path, rows: list[Measurement]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=Measurement.__dataclass_fields__)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def read_measurements(path: Path) -> list[Measurement]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            Measurement(
                semantic_fit=row["semantic_fit"],
                identifier=row["identifier"],
                utf8_bytes=int(row["utf8_bytes"]),
                token_count=int(row["token_count"]),
                allocated_bits=float(row["allocated_bits"]),
                bits_per_byte=float(row["bits_per_byte"]),
                model=row["model"],
                revision=row["revision"],
                prefix_sha256=row["prefix_sha256"],
                source_path=row["source_path"],
                source_sha256=row["source_sha256"],
            )
            for row in csv.DictReader(handle)
        ]


def validate_measurements(rows: list[Measurement]) -> None:
    if [row.identifier for row in rows] != [name for _, name in EXAMPLES]:
        raise ValueError("Stored rows do not match the fixed motivating examples")
    provenance = {
        (row.model, row.revision, row.prefix_sha256, row.source_path, row.source_sha256)
        for row in rows
    }
    if len(provenance) != 1:
        raise ValueError("All measurements must use one model and one source context")
    if any(not math.isfinite(row.bits_per_byte) or row.bits_per_byte < 0 for row in rows):
        raise ValueError("BPB values must be finite and nonnegative")


def render(path: Path, rows: list[Measurement]) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig = plt.figure(figsize=(7.2, 2.72), facecolor="white")
    layout_ax = fig.add_axes((0, 0, 1, 1))
    layout_ax.set_xlim(0, 1)
    layout_ax.set_ylim(0, 1)
    layout_ax.axis("off")
    layout_ax.text(0.04, 0.92, "REAL METHOD CONTEXT", color=MUTED, fontsize=7.5,
                   fontweight="bold", va="center")
    layout_ax.text(0.535, 0.92, "ALTERNATIVE NAMING STYLES", color=MUTED, fontsize=7.5,
                   fontweight="bold", va="center")
    layout_ax.plot((0.04, 0.435), (0.88, 0.88), color="#7B9FC4", linewidth=1.25)
    layout_ax.plot((0.535, 0.96), (0.88, 0.88), color="#7B9FC4", linewidth=1.25)
    layout_ax.plot((0.485, 0.485), (0.07, 0.93), color=LINE, linewidth=0.75)

    code_ax = fig.add_axes((0.04, 0.06, 0.395, 0.78))
    code_ax.set_xlim(0, 1)
    code_ax.set_ylim(0, 1)
    code_ax.axis("off")
    code_ax.add_patch(
        FancyBboxPatch(
            (0.0, 0.02),
            0.985,
            0.96,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor="#F7F9FC",
            edgecolor="#DDE4EC",
            linewidth=0.7,
        )
    )
    mono = "DejaVu Sans Mono"
    display_lines = (
        "public void mouseDragged(WidgetMouseEvent e, ...)",
        "{",
        "  findPoints(e.getPoint(), e.isShiftDown());",
        "  int x[] = new int[points.length], ...;",
        "  for (int i = 0; i < points.length; i++)",
        "  {",
        "    x[i] = (int) points[i].x;",
        "    y[i] = (int) points[i].y;",
        "  }",
        "  view.drawDraggedShape(new Polygon(x, y, ...));",
        "}",
    )
    top, step, font_size = 0.875, 0.070, 5.75

    for index, line in enumerate(display_lines):
        y = top - index * step
        if line.startswith("  int x[]"):
            code_ax.text(0.045, y, "  int", family=mono, fontsize=font_size,
                         color=INK, va="center")
            code_ax.add_patch(
                FancyBboxPatch(
                    (0.142, y - 0.0195), 0.075, 0.039,
                    boxstyle="round,pad=0.002,rounding_size=0.006",
                    facecolor="#FFF3DE", edgecolor="#E3A23C", linewidth=0.65,
                )
            )
            code_ax.text(0.1795, y, "<id>", family=mono, fontsize=font_size,
                         color="#9A5A00", fontweight="bold", ha="center",
                         va="center")
            code_ax.text(0.226, y,
                         "[] = new int[points.length], ...;",
                         family=mono, fontsize=font_size,
                         color=INK, va="center")
        else:
            code_ax.text(0.045, y, line, family=mono, fontsize=font_size,
                         color=INK, va="center")

    chart_ax = fig.add_axes((0.66, 0.16, 0.29, 0.66))
    values = [row.bits_per_byte for row in rows]
    positions = list(range(len(rows)))
    # A monotone power normalization keeps the large garbled-name outlier from
    # collapsing all lower, but distinct, BPB values into the same green tone.
    color_norm = mpl_colors.PowerNorm(
        gamma=0.45, vmin=min(values), vmax=max(values)
    )
    color_map = plt.get_cmap("RdYlGn_r")
    value_colors = [color_map(color_norm(value)) for value in values]
    chart_ax.barh(
        positions, values, color=value_colors, height=0.67, edgecolor="none"
    )
    chart_ax.invert_yaxis()
    chart_ax.set_axisbelow(True)
    chart_ax.xaxis.grid(True, color=GRID, linewidth=0.7)
    chart_ax.yaxis.grid(False)
    chart_ax.set_xlim(0, max(values) * 1.19)
    chart_ax.set_yticks(positions)
    chart_ax.set_yticklabels([])
    chart_ax.set_xlabel("")
    chart_ax.text(
        1.0,
        1.025,
        "Surprisal (BPB)",
        transform=chart_ax.transAxes,
        ha="right",
        va="bottom",
        color=MUTED,
        fontsize=7.0,
        fontweight="bold",
    )
    chart_ax.set_facecolor("none")
    for spine in ("top", "right", "left"):
        chart_ax.spines[spine].set_visible(False)
    chart_ax.spines["bottom"].set_color(LINE)
    chart_ax.tick_params(axis="y", length=0, pad=8)
    chart_ax.tick_params(axis="x", colors=MUTED, labelsize=7.4)
    chart_ax.set_xticks((0, 2, 4, 6))
    for index, (row, value) in enumerate(zip(rows, values)):
        chart_ax.text(-0.07, index - 0.22, row.semantic_fit.upper(),
                      transform=chart_ax.get_yaxis_transform(), ha="right",
                      va="center", color="#54769A", fontsize=5.4,
                      fontweight="bold", clip_on=False)
        chart_ax.text(-0.07, index + 0.17, row.identifier,
                      transform=chart_ax.get_yaxis_transform(), ha="right",
                      va="center", color=INK, fontsize=7.6, family=mono,
                      clip_on=False)
        chart_ax.text(value + max(values) * 0.025, index, f"{value:.2f}",
                      va="center", ha="left", color=INK, fontsize=7.8,
                      fontweight="bold")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="pdf", facecolor="white", bbox_inches="tight",
                pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    main()
