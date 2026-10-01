#!/usr/bin/env python3
"""Render the motivating counterexample for explicit readability features.

The example is a behavior-preserving adaptation of Sakamoto's ASCII month-
offset encoding. The plotted measurements come from the frozen comparison
methods and final 11-feature model. The script validates the source hash, the
month-offset invariant, and the exact feature-contribution decomposition before
rendering the publication PDF.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "readability_matplotlib")
)

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pygments import lex
from pygments.lexers.jvm import JavaLexer
from pygments.token import Comment, Keyword, Literal, Name, Number, Operator, String, Token

from src.methods.readability_model.feature_schema import feature_display_name


SOURCE = """class MonthOffsets {
    static int offset(int month) {
        int value = "-ilkDwlu2thk5".charAt(month);
        return value % 7;
    }
}
"""
CANONICAL_ENCODING = "-bed=pen+mad."
SHIFTED_ENCODING = "-ilkDwlu2thk5"
EXPECTED_OFFSETS = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
EXPECTED_SOURCE_SHA256 = "f0321bebb4d087b5fa9479880a3b1e2cc27658ccca16dee530c839228a46749c"

DEFAULT_DATA = ROOT / "figures" / "data" / "opaque_month_offset_motivation.csv"
DEFAULT_OUTPUT = ROOT / "figures" / "publication" / "opaque_month_offset_motivation.pdf"

INK = "#172033"
MUTED = "#667085"
LINE = "#D6DEE8"
GRID = "#E8EDF3"
BLUE = "#4C78A8"
BLUE_LIGHT = "#DCE9F5"
RED = "#C84A53"
RED_LIGHT = "#F9E3E4"
AMBER = "#C66A1B"
AMBER_LIGHT = "#FBE9D7"


@dataclass(frozen=True)
class Row:
    kind: str
    key: str
    label: str
    score: float | None
    readability_percentile: float | None
    reference_count: int | None
    contribution: float | None
    source_sha256: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def optional_float(value: str) -> float | None:
    return float(value) if value.strip() else None


def optional_int(value: str) -> int | None:
    return int(value) if value.strip() else None


def load_rows(path: Path) -> list[Row]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            Row(
                kind=row["kind"],
                key=row["key"],
                label=row["label"],
                score=optional_float(row["score"]),
                readability_percentile=optional_float(row["readability_percentile"]),
                reference_count=optional_int(row["reference_count"]),
                contribution=optional_float(row["contribution"]),
                source_sha256=row["source_sha256"],
            )
            for row in csv.DictReader(handle)
        ]


def validate(rows: list[Row]) -> None:
    source_hash = hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Source hash changed: {source_hash}")
    if {row.source_sha256 for row in rows} != {source_hash}:
        raise ValueError("Plotted measurements do not match the displayed source")

    canonical = tuple(ord(CANONICAL_ENCODING[month]) % 7 for month in range(1, 13))
    shifted = tuple(ord(SHIFTED_ENCODING[month]) % 7 for month in range(1, 13))
    if canonical != EXPECTED_OFFSETS or shifted != EXPECTED_OFFSETS:
        raise ValueError("The displayed encoding is not behavior-equivalent")
    if any(
        ord(SHIFTED_ENCODING[index]) - ord(CANONICAL_ENCODING[index]) != 7
        for index in range(1, 13)
    ):
        raise ValueError("The shifted encoding is no longer the pinned +7 adaptation")

    model_rows = [row for row in rows if row.kind == "model"]
    human_rows = [row for row in rows if row.kind == "human"]
    if len(human_rows) != 1:
        raise ValueError("Expected one human-rating row")
    human = human_rows[0]
    if (
        human.score != 1
        or human.readability_percentile != 0
        or human.reference_count != 5
    ):
        raise ValueError("The motivating example requires the unanimous 1/5 human rating")
    if [row.key for row in model_rows] != [
        "posnett",
        "scalabrino",
        "dorn",
        "mi_convnet_cr",
        "deepseek_v4_pro",
        "ours",
    ]:
        raise ValueError("Unexpected model order")
    feature_rows = [row for row in rows if row.kind == "feature"]
    summary = {row.key: row for row in rows if row.kind == "summary"}
    ours = next(row for row in model_rows if row.key == "ours")
    reconstructed = (
        summary["intercept"].contribution
        + summary["remaining"].contribution
        + sum(row.contribution for row in feature_rows)
    )
    if ours.score is None or abs(reconstructed - ours.score) > 1e-12:
        raise ValueError("Feature contributions do not reproduce the final score")


def rounded_panel(ax: plt.Axes, *, facecolor: str = "white") -> None:
    ax.add_patch(
        FancyBboxPatch(
            (0.008, 0.012),
            0.984,
            0.976,
            boxstyle="round,pad=0.010,rounding_size=0.026",
            facecolor=facecolor,
            edgecolor=LINE,
            linewidth=0.75,
            transform=ax.transAxes,
            clip_on=False,
        )
    )


def setup_panel(ax: plt.Axes) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def panel_heading(ax: plt.Axes, title: str, subtitle: str | None = None) -> None:
    ax.text(0.045, 0.925, title, fontsize=9.2, fontweight="bold", color=INK, va="center")
    if subtitle:
        ax.text(0.955, 0.925, subtitle, fontsize=6.6, color=MUTED, ha="right", va="center")
    ax.plot((0.04, 0.96), (0.865, 0.865), color=LINE, linewidth=0.65)


def java_style(token_type: Token) -> tuple[str, str]:
    if token_type in Comment:
        return "#16803A", "normal"
    if token_type in Keyword.Type or token_type in Name.Class:
        return "#0369A1", "bold"
    if token_type in Keyword:
        return "#6D28D9", "bold"
    if token_type in Name.Function:
        return "#1D4ED8", "bold"
    if token_type in String or token_type in Literal.String:
        return "#B45309", "normal"
    if token_type in Number or token_type in Literal.Number:
        return "#C2410C", "normal"
    if token_type in Operator:
        return "#BE185D", "normal"
    if token_type in Token.Punctuation:
        return "#475569", "normal"
    return INK, "normal"


def draw_code(ax: plt.Axes) -> None:
    rounded_panel(ax, facecolor="#F5F8FC")
    panel_heading(ax, "A month-offset table hidden in a string")

    lines = SOURCE.rstrip().splitlines()
    font_size = 7.15
    panel_points = ax.figure.get_figwidth() * ax.get_position().width * 72
    char_step = 0.61 * font_size / panel_points
    left = 0.065
    top = 0.755
    line_step = 0.068

    target_line = 2
    phrase = '"-ilkDwlu2thk5".charAt(month)'
    column = lines[target_line].find(phrase)
    ax.add_patch(
        FancyBboxPatch(
            (left + column * char_step - 0.008, top - target_line * line_step - 0.031),
            len(phrase) * char_step + 0.016,
            0.062,
            boxstyle="round,pad=0.003,rounding_size=0.010",
            facecolor=AMBER_LIGHT,
            edgecolor="none",
            transform=ax.transAxes,
        )
    )

    lexer = JavaLexer()
    for line_number, line in enumerate(lines):
        yy = top - line_number * line_step
        current_column = 0
        for token_type, value in lex(line, lexer):
            value = value.rstrip("\n")
            if not value:
                continue
            color, weight = java_style(token_type)
            ax.text(
                left + current_column * char_step,
                yy,
                value,
                family="DejaVu Sans Mono",
                fontsize=font_size,
                fontweight=weight,
                color=color,
                va="center",
                transform=ax.transAxes,
            )
            current_column += len(value)

    ax.text(0.055, 0.342, "Triggered source regions", fontsize=7.0,
            fontweight="bold", color=RED, va="center", transform=ax.transAxes)

    triggers = (
        (0.055, 0.190, "Assignment-value surprisal", '"-ilkDwlu2thk5".charAt(month)'),
        (0.515, 0.190, "Literal-tail surprisal", '"-ilkDwlu2thk5"'),
        (0.055, 0.058, "Declaration-surprisal variation", "int value = ..."),
        (0.515, 0.058, "Identifier-onset surprisal", "value"),
    )
    for x, y, label, source_region in triggers:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                0.420,
                0.105,
                boxstyle="round,pad=0.008,rounding_size=0.014",
                facecolor="white",
                edgecolor=LINE,
                linewidth=0.65,
                transform=ax.transAxes,
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (x + 0.008, y + 0.015),
                0.010,
                0.075,
                boxstyle="round,pad=0.001,rounding_size=0.005",
                facecolor=RED,
                edgecolor="none",
                transform=ax.transAxes,
            )
        )
        ax.text(x + 0.030, y + 0.074, label, fontsize=5.25,
                fontweight="bold", color=INK, va="center", transform=ax.transAxes)
        ax.text(x + 0.030, y + 0.032, source_region, fontsize=4.95,
                family="DejaVu Sans Mono", color=AMBER, va="center",
                transform=ax.transAxes)


def draw_model_judgments(ax: plt.Axes, rows: list[Row]) -> None:
    rounded_panel(ax)
    panel_heading(ax, "Relative readability")
    model_rows = [row for row in rows if row.kind == "model"]
    human_rows = [row for row in rows if row.kind == "human"]
    judgment_rows = [*model_rows, *human_rows]

    chart = ax.inset_axes((0.26, 0.13, 0.68, 0.67))
    chart.set_xlim(0, 100)
    chart.set_ylim(-0.55, len(judgment_rows) - 0.45)
    chart.axvline(50, color="#AAB4C1", linewidth=0.8, linestyle=(0, (2.2, 2.2)))
    chart.set_xticks((0, 50, 100), labels=("0", "50", "100"))
    chart.tick_params(axis="x", colors=MUTED, labelsize=6.0, length=0, pad=2)
    chart.set_yticks([])
    for spine in chart.spines.values():
        spine.set_visible(False)
    chart.grid(axis="x", color=GRID, linewidth=0.5, zorder=0)

    for position, row in enumerate(reversed(judgment_rows)):
        percentile = row.readability_percentile
        assert percentile is not None and row.score is not None
        if row.kind == "human":
            color, pale = INK, "#EAECF0"
        elif row.key in {"deepseek_v4_pro", "ours"}:
            color, pale = RED, RED_LIGHT
        else:
            color, pale = BLUE, BLUE_LIGHT
        chart.barh(position, 100, height=0.55, color=pale, edgecolor="none", zorder=1)
        chart.barh(position, percentile, height=0.55, color=color, edgecolor="none", zorder=2)
        display_label = "Human" if row.kind == "human" else row.label
        chart.text(-3.0, position, display_label, ha="right", va="center", fontsize=6.5,
                   color=INK, fontweight="bold" if row.key == "ours" else "normal")
        if percentile >= 60:
            label_x, alignment, label_color = percentile - 2.0, "right", "white"
        else:
            label_x, alignment, label_color = percentile + 2.0, "left", color
        chart.text(label_x, position, f"{percentile:.1f}",
                   ha=alignment, va="center", fontsize=6.7,
                   color=label_color, fontweight="bold")


def draw_feature_contributions(ax: plt.Axes, rows: list[Row]) -> None:
    rounded_panel(ax)
    panel_heading(ax, "Largest negative feature contributions")
    feature_rows = [row for row in rows if row.kind == "feature"]

    chart = ax.inset_axes((0.50, 0.16, 0.43, 0.62))
    chart.set_xlim(-0.28, 0.0)
    chart.set_ylim(-0.55, len(feature_rows) - 0.45)
    chart.axvline(0, color="#AAB4C1", linewidth=0.7)
    chart.set_xticks((-0.25, -0.10, 0.0), labels=("−0.25", "−0.10", "0"))
    chart.tick_params(axis="x", colors=MUTED, labelsize=5.8, length=0, pad=2)
    chart.set_yticks([])
    for spine in chart.spines.values():
        spine.set_visible(False)
    chart.grid(axis="x", color=GRID, linewidth=0.5, zorder=0)

    for position, row in enumerate(reversed(feature_rows)):
        contribution = row.contribution
        assert contribution is not None
        chart.barh(position, contribution, height=0.58, color=RED, edgecolor="none", zorder=2)
        chart.text(-0.292, position, feature_display_name(row.key), ha="right", va="center",
                   fontsize=5.9, color=INK, clip_on=False)
        if abs(contribution) < 0.055:
            value_x, alignment, value_color = contribution - 0.006, "right", RED
        else:
            value_x, alignment, value_color = -0.006, "right", "white"
        chart.text(value_x, position, f"{contribution:.3f}",
                   ha=alignment, va="center", fontsize=5.7, color=value_color,
                   fontweight="bold", clip_on=False)

def render(output: Path, rows: list[Row]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig = plt.figure(figsize=(7.25, 3.25), facecolor="white")
    code_ax = fig.add_axes((0.015, 0.045, 0.455, 0.91))
    judgment_ax = fig.add_axes((0.49, 0.515, 0.495, 0.44))
    feature_ax = fig.add_axes((0.49, 0.045, 0.495, 0.44))
    for axis in (code_ax, judgment_ax, feature_ax):
        setup_panel(axis)
    draw_code(code_ax)
    draw_model_judgments(judgment_ax, rows)
    draw_feature_contributions(feature_ax, rows)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.025)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    rows = load_rows(args.data)
    validate(rows)
    render(args.output, rows)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
