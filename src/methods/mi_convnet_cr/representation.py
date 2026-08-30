"""Character-matrix representation used by the Mi ConvNetCR reproduction."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


PAD_VALUE = -1.0
UNKNOWN_CODEPOINT = 256
CODEPOINT_SCALE = 256.0


@dataclass(frozen=True)
class CharacterMatrixSpec:
    max_lines: int
    max_line_width: int

    def __post_init__(self) -> None:
        if self.max_lines < 2:
            raise ValueError("max_lines must be at least 2 for the published filters")
        if self.max_line_width < 1:
            raise ValueError("max_line_width must be positive")

    def to_dict(self) -> dict[str, int]:
        return {
            "max_lines": self.max_lines,
            "max_line_width": self.max_line_width,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "CharacterMatrixSpec":
        return cls(
            max_lines=int(payload["max_lines"]),
            max_line_width=int(payload["max_line_width"]),
        )


def fit_character_matrix_spec(codes: list[str]) -> CharacterMatrixSpec:
    if not codes:
        raise ValueError("Cannot fit a character matrix without source code")
    lines_by_code = [source_lines(code) for code in codes]
    return CharacterMatrixSpec(
        max_lines=max(2, max(len(lines) for lines in lines_by_code)),
        max_line_width=max(1, max(len(line) for lines in lines_by_code for line in lines)),
    )


def encode_character_matrix(code: str, spec: CharacterMatrixSpec) -> np.ndarray:
    """Encode one snippet as a fixed line-by-character matrix.

    Mi et al. preserve whitespace and map characters to integer matrices. Their
    released repository does not contain the character dictionary used by the
    paper. This independent reproduction therefore uses Unicode code points for
    the byte range, maps other characters to a documented unknown value, scales
    non-padding values to [0, 1], and retains -1 as padding.
    """
    matrix = np.full(
        (spec.max_lines, spec.max_line_width),
        PAD_VALUE,
        dtype=np.float32,
    )
    for row, line in enumerate(source_lines(code)[: spec.max_lines]):
        for column, character in enumerate(line[: spec.max_line_width]):
            codepoint = ord(character)
            if codepoint > 255:
                codepoint = UNKNOWN_CODEPOINT
            matrix[row, column] = codepoint / CODEPOINT_SCALE
    return matrix


def source_lines(code: str) -> list[str]:
    # split("\n") preserves a final empty row and all horizontal whitespace.
    normalized = code.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.split("\n")
