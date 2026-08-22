from __future__ import annotations

from statistics import mean, pstdev
from typing import Sequence

import numpy as np

from src.methods.posnett.method import JAVA_KEYWORDS, JAVA_OPERATORS, TOKEN_PATTERN, strip_comments

from .lexeme import LexemeChunk


def visual_layout_features(
    code: str,
    chunks: Sequence[LexemeChunk],
) -> dict[str, float]:
    lines = code.splitlines()
    loc = len([line for line in lines if line.strip()])
    physical_line_count = max(len(lines), 1)
    stripped_code = strip_comments(code)
    tokens_by_line = _tokens_by_line(stripped_code)
    non_whitespace_area = sum(len(line.strip()) for line in lines)

    identifier_positions: list[int] = []
    keyword_positions: list[int] = []
    operator_positions: list[int] = []
    number_positions: list[int] = []
    period_positions: list[int] = []
    comma_positions: list[int] = []
    identifier_area = 0
    keyword_area = 0
    operator_area = 0
    per_line_identifier_counts = [0.0 for _ in range(physical_line_count)]
    per_line_keyword_counts = [0.0 for _ in range(physical_line_count)]
    per_line_period_counts = [0.0 for _ in range(physical_line_count)]

    for line_number, token in tokens_by_line:
        index = min(max(line_number - 1, 0), physical_line_count - 1)
        if token in JAVA_KEYWORDS:
            keyword_positions.append(line_number)
            keyword_area += len(token)
            per_line_keyword_counts[index] += 1.0
        elif token in JAVA_OPERATORS:
            operator_positions.append(line_number)
            operator_area += len(token)
            if token == ".":
                period_positions.append(line_number)
                per_line_period_counts[index] += 1.0
            elif token == ",":
                comma_positions.append(line_number)
        elif _is_number_token(token):
            number_positions.append(line_number)
        elif _is_identifier_token(token):
            identifier_positions.append(line_number)
            identifier_area += len(token)
            per_line_identifier_counts[index] += 1.0

    line_lengths = [float(len(line)) for line in lines] or [0.0]
    space_counts = [float(sum(1 for char in line if char.isspace())) for line in lines] or [0.0]
    chunk_span = _chunk_line_span(chunks)

    return {
        "visual_token_density": len(tokens_by_line) / max(loc, 1),
        "visual_identifier_density": len(identifier_positions) / max(loc, 1),
        "visual_keyword_density": len(keyword_positions) / max(loc, 1),
        "visual_operator_density": len(operator_positions) / max(loc, 1),
        "visual_number_density": len(number_positions) / max(loc, 1),
        "visual_period_density": len(period_positions) / max(loc, 1),
        "visual_comma_density": len(comma_positions) / max(loc, 1),
        "visual_identifier_area_ratio": identifier_area / max(non_whitespace_area, 1),
        "visual_keyword_area_ratio": keyword_area / max(non_whitespace_area, 1),
        "visual_operator_area_ratio": operator_area / max(non_whitespace_area, 1),
        "visual_keyword_identifier_area_ratio": keyword_area / max(identifier_area, 1),
        "visual_identifier_y_mean": _normalized_position_mean(identifier_positions, physical_line_count),
        "visual_identifier_y_std": _normalized_position_std(identifier_positions, physical_line_count),
        "visual_keyword_y_mean": _normalized_position_mean(keyword_positions, physical_line_count),
        "visual_keyword_y_std": _normalized_position_std(keyword_positions, physical_line_count),
        "visual_operator_y_mean": _normalized_position_mean(operator_positions, physical_line_count),
        "visual_operator_y_std": _normalized_position_std(operator_positions, physical_line_count),
        "visual_period_y_mean": _normalized_position_mean(period_positions, physical_line_count),
        "visual_period_y_std": _normalized_position_std(period_positions, physical_line_count),
        "visual_line_length_dft_energy": _low_frequency_dft_energy(line_lengths),
        "visual_space_dft_energy": _low_frequency_dft_energy(space_counts),
        "visual_identifier_dft_energy": _low_frequency_dft_energy(per_line_identifier_counts),
        "visual_keyword_dft_energy": _low_frequency_dft_energy(per_line_keyword_counts),
        "visual_period_dft_energy": _low_frequency_dft_energy(per_line_period_counts),
        "chunk_y_mean": _chunk_y_mean(chunks, physical_line_count),
        "chunk_y_std": _chunk_y_std(chunks, physical_line_count),
        "chunk_line_span": chunk_span,
        "chunk_line_span_ratio": chunk_span / max(loc, 1),
    }


def _tokens_by_line(code: str) -> list[tuple[int, str]]:
    line_starts = [0]
    for index, char in enumerate(code):
        if char == "\n":
            line_starts.append(index + 1)
    line_starts_array = np.asarray(line_starts, dtype=int)
    tokens: list[tuple[int, str]] = []
    for match in TOKEN_PATTERN.finditer(code):
        line_number = int(np.searchsorted(line_starts_array, match.start(), side="right"))
        tokens.append((line_number, match.group(0)))
    return tokens


def _is_identifier_token(token: str) -> bool:
    return bool(token) and (token[0].isalpha() or token[0] in "_$")


def _is_number_token(token: str) -> bool:
    return bool(token) and token[0].isdigit()


def _normalized_position_mean(positions: Sequence[int], line_count: int) -> float:
    if not positions:
        return 0.0
    denominator = max(line_count - 1, 1)
    return float(mean((line - 1) / denominator for line in positions))


def _normalized_position_std(positions: Sequence[int], line_count: int) -> float:
    if len(positions) <= 1:
        return 0.0
    denominator = max(line_count - 1, 1)
    normalized = [(line - 1) / denominator for line in positions]
    return float(pstdev(normalized))


def _low_frequency_dft_energy(values: Sequence[float], bins: int = 4) -> float:
    series = np.asarray(values, dtype=float)
    if series.size <= 1:
        return 0.0
    centered = series - float(np.mean(series))
    total = float(np.sum(centered ** 2))
    if total <= 0.0:
        return 0.0
    spectrum = np.abs(np.fft.rfft(centered)) ** 2
    if spectrum.size <= 1:
        return 0.0
    low = spectrum[1 : min(spectrum.size, bins + 1)]
    return float(np.sum(low) / np.sum(spectrum[1:]))


def _chunk_y_mean(chunks: Sequence[LexemeChunk], line_count: int) -> float:
    positions = [chunk.line for chunk in chunks if chunk.line > 0]
    return _normalized_position_mean(positions, line_count)


def _chunk_y_std(chunks: Sequence[LexemeChunk], line_count: int) -> float:
    positions = [chunk.line for chunk in chunks if chunk.line > 0]
    return _normalized_position_std(positions, line_count)


def _chunk_line_span(chunks: Sequence[LexemeChunk]) -> int:
    positions = [chunk.line for chunk in chunks if chunk.line > 0]
    if not positions:
        return 0
    return max(positions) - min(positions) + 1
