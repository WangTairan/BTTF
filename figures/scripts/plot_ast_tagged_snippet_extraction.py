#!/usr/bin/env python3
"""Render the AST-tagged snippet overview used in the paper.

The displayed snippets are validated against the production Java extractor so
that the conceptual figure cannot silently drift away from the implementation.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "readability_model_matplotlib")
)

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pygments import lex
from pygments.lexers.jvm import JavaLexer
from pygments.token import Comment, Keyword, Literal, Name, Number, Operator, String, Token

from src.methods.readability_model.extractors.factory import (  # noqa: E402
    extractor_for_language,
)
from src.datasets.code import load_code_dataset  # noqa: E402


DEFAULT_DATASET = ROOT / "datasets" / "scalabrino" / "dataset"
DEFAULT_TASK_ID = "Scalabrio141"

DISPLAYED_GROUPS = (
    ("DECLARATION", ("int_PRIME", "def_PRIME", "def_PRIME_31")),
    ("IDENTIFIER", ("hashCode", "PRIME", "result", "name", "num")),
    ("LITERAL", ("literal_31", "literal_1")),
    ("CONTROL_FLOW", ("if_name!=null", "if_num!=null")),
    ("COMPARISON", ("name!=null", "num!=null")),
    ("ASSIGNMENT", ("result+=name.hashCode()", "result*=PRIME", "result+=num.hashCode()")),
    ("CALL", ("name.hashCode", "num.hashCode")),
)

INK = "#1E293B"
MUTED = "#64748B"
LINE = "#CBD5E1"
BLUE = "#DCEBFA"
BLUE_DARK = "#2563EB"
PURPLE = "#EEE7FA"
PURPLE_DARK = "#7C3AED"
ORANGE = "#FCE8D4"
ORANGE_DARK = "#C2410C"
GREEN = "#DDF3E8"
GREEN_DARK = "#16815A"
TEAL = "#DDF2F3"
TEAL_DARK = "#0F7C82"
GRAY = "#E9EEF5"
JAVA_LEXER = JavaLexer()

TYPE_STYLE = {
    "DECLARATION": (BLUE, BLUE_DARK),
    "COMMENT": (TEAL, TEAL_DARK),
    "CONTROL_FLOW": (PURPLE, PURPLE_DARK),
    "COMPARISON": (GREEN, GREEN_DARK),
    "IDENTIFIER": (GRAY, "#475569"),
    "LITERAL": ("#F4E8D5", "#9A6700"),
    "LOGICAL": ("#E5F4DC", "#3F7D20"),
    "ASSIGNMENT": (ORANGE, ORANGE_DARK),
    "ARITHMETIC": (GREEN, GREEN_DARK),
    "CALL": (TEAL, TEAL_DARK),
}


def rounded_box(ax, xy, width, height, *, fc="white", ec=LINE, lw=0.6, radius=0.018):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
    )
    ax.add_patch(box)
    return box


def validate_example(source: str) -> None:
    chunks, _ = extractor_for_language("java").extract_with_member_fallback(source)
    observed = {(chunk.type, chunk.lexeme) for chunk in chunks}
    expected = {
        (chunk_type, lexeme)
        for chunk_type, lexemes in DISPLAYED_GROUPS
        for lexeme in lexemes
    }
    missing = expected - observed
    if missing:
        raise RuntimeError(
            "Figure example no longer matches the production extractor: "
            f"missing {sorted(missing)}"
        )


def setup_panel(axis: plt.Axes) -> None:
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")


def draw_panel_shell(axis: plt.Axes, facecolor: str) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (0.014, 0.024),
            0.962,
            0.962,
            boxstyle="round,pad=0.012,rounding_size=0.032",
            facecolor=facecolor,
            edgecolor="#C9D3DF",
            linewidth=0.6,
        )
    )


def panel_heading(axis: plt.Axes, title: str) -> None:
    axis.text(0.04, 0.931, title, color=INK, fontsize=8.6,
              fontweight="bold", va="center")
    axis.plot((0.035, 0.965), (0.875, 0.875), color=LINE, linewidth=0.55)


def draw_source(ax: plt.Axes, source: str) -> None:
    draw_panel_shell(ax, "#F3F7FC")
    panel_heading(ax, "Source code")

    lines = source.strip().expandtabs(4).splitlines()
    top = 0.79
    step = 0.062
    font_size = 5.9
    panel_width_points = ax.figure.get_figwidth() * ax.get_position().width * 72
    char_step = 0.61 * font_size / panel_width_points
    highlight_spans = {
        0: ("hashCode", BLUE),
        1: ("int PRIME = 31", BLUE),
        3: ("if ( name != null )", PURPLE),
        4: ("result += name.hashCode()", ORANGE),
        7: ("if ( num != null )", PURPLE),
        8: ("result += num.hashCode()", ORANGE),
    }
    for index, line in enumerate(lines):
        yy = top - index * step
        if index in highlight_spans:
            phrase, color = highlight_spans[index]
            column = line.find(phrase)
            rounded_box(
                ax,
                (0.046 + column * char_step, yy - 0.032),
                len(phrase) * char_step + 0.008,
                0.064,
                fc=color,
                ec="none",
                lw=0,
                radius=0.009,
            ).set_alpha(0.72)
        column = 0
        for text, color, weight in highlighted_java_line(line):
            ax.text(
                0.05 + column * char_step,
                yy,
                text,
                family="DejaVu Sans Mono",
                fontsize=font_size,
                fontweight=weight,
                color=color,
                va="center",
            )
            column += len(text)


def highlighted_java_line(line: str) -> list[tuple[str, str, str]]:
    segments: list[tuple[str, str, str]] = []
    for token_type, value in lex(line, JAVA_LEXER):
        value = value.rstrip("\n")
        if value:
            segments.append((value, java_token_color(token_type), java_token_weight(token_type)))
    return segments


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



def draw_chunks(ax: plt.Axes) -> None:
    draw_panel_shell(ax, "#F2F8F5")
    panel_heading(ax, "AST-tagged snippets")

    start = 0.78
    step = 0.105
    for index, (chunk_type, lexemes) in enumerate(DISPLAYED_GROUPS):
        yy = start - index * step
        fc, tc = TYPE_STYLE[chunk_type]
        rounded_box(ax, (0.04, yy - 0.033), 0.26, 0.066,
                    fc=fc, ec="none", lw=0, radius=0.009)
        ax.text(0.17, yy - 0.001, chunk_type, fontsize=5.75,
                color=tc, fontweight="bold", ha="center", va="center")
        ax.text(
            0.32,
            yy - 0.001,
            chunk_display_line(chunk_type, lexemes),
            fontsize=6.05,
            color=INK,
            family="DejaVu Sans Mono",
            va="center",
        )


def chunk_display_line(chunk_type: str, lexemes: tuple[str, ...]) -> str:
    text = ", ".join(lexemes)
    max_characters = 44
    if len(text) <= max_characters:
        return text
    return text[: max_characters - 1].rstrip() + "…"


def draw(source: str, output: Path) -> None:
    validate_example(source)
    fig = plt.figure(figsize=(7.2, 2.55), facecolor="white")
    source_ax = fig.add_axes((0.012, 0.055, 0.40, 0.89))
    chunks_ax = fig.add_axes((0.51, 0.055, 0.478, 0.89))
    setup_panel(source_ax)
    setup_panel(chunks_ax)

    draw_source(source_ax, source)
    draw_chunks(chunks_ax)

    fig.add_artist(FancyArrowPatch(
        (0.425, 0.5),
        (0.495, 0.5),
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.45,
        color="#374151",
    ))
    fig.text(0.46, 0.45, "extract", ha="center", va="top", fontsize=7.5,
             color=MUTED)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.018)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "figures" / "publication" / "ast_tagged_snippet_extraction.pdf",
    )
    args = parser.parse_args()
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    item = next(
        (item for item in load_code_dataset(args.dataset) if item.task_id == args.task_id),
        None,
    )
    if item is None:
        raise SystemExit(f"Task {args.task_id!r} was not found in {args.dataset}")
    draw(item.content, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
