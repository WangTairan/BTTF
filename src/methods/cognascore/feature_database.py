from __future__ import annotations

import csv
import bz2
import json
import lzma
import math
import re
import zlib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Sequence

from src.datasets import DatasetItem
from src.methods.posnett.method import posnett_model

from .extractors.python import LexemeExtractor
from .visual_features import visual_layout_features


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    group: str
    description: str


IDENTITY_COLUMNS = (
    "dataset",
    "task_id",
    "readability_score",
)


def feature_definitions() -> list[FeatureDefinition]:
    return [
        FeatureDefinition("log_vocabulary_size", "code_halstead", "log(1 + vocabulary_size)."),
        FeatureDefinition("vocabulary_size", "code_halstead", "Number of distinct operators and operands."),
        FeatureDefinition("lexeme_count", "cognascore_chunk", "Number of extracted CognaScore chunks."),
        FeatureDefinition("log_lexeme_count", "cognascore_chunk", "log(1 + lexeme_count)."),
        FeatureDefinition("loc", "code_layout", "Number of non-empty source lines."),
        FeatureDefinition("log_loc", "code_layout", "log(1 + loc)."),
        FeatureDefinition("blank_line_count", "code_layout", "Number of blank source lines."),
        FeatureDefinition("mean_line_length", "code_layout", "Mean non-empty line length."),
        FeatureDefinition("std_line_length", "code_layout", "Standard deviation of non-empty line length."),
        FeatureDefinition("max_line_length", "code_layout", "Maximum non-empty line length."),
        FeatureDefinition("mean_indent", "code_layout", "Mean leading whitespace count over non-empty lines."),
        FeatureDefinition("std_indent", "code_layout", "Standard deviation of leading whitespace count."),
        FeatureDefinition("max_indent", "code_layout", "Maximum leading whitespace count."),
        FeatureDefinition("line_length_cv", "code_visual_layout", "Coefficient of variation of non-empty source line lengths."),
        FeatureDefinition("indent_cv", "code_visual_layout", "Coefficient of variation of leading whitespace indentation."),
        FeatureDefinition("indent_transition_mean", "code_visual_layout", "Mean absolute indentation change between adjacent non-empty lines."),
        FeatureDefinition("indent_transition_std", "code_visual_layout", "Standard deviation of absolute indentation changes between adjacent non-empty lines."),
        FeatureDefinition("indent_transition_max", "code_visual_layout", "Maximum absolute indentation change between adjacent non-empty lines."),
        FeatureDefinition("blank_line_ratio", "code_visual_layout", "Blank source lines divided by all physical source lines."),
        FeatureDefinition("long_line_ratio_80", "code_visual_layout", "Non-empty source lines longer than 80 characters divided by non-empty LOC."),
        FeatureDefinition("long_line_ratio_100", "code_visual_layout", "Non-empty source lines longer than 100 characters divided by non-empty LOC."),
        FeatureDefinition("visual_token_density", "code_visual_token", "Java-style lexical tokens per non-empty source line."),
        FeatureDefinition("visual_identifier_density", "code_visual_token", "Identifier tokens per non-empty source line."),
        FeatureDefinition("visual_keyword_density", "code_visual_token", "Keyword tokens per non-empty source line."),
        FeatureDefinition("visual_operator_density", "code_visual_token", "Operator tokens per non-empty source line."),
        FeatureDefinition("visual_number_density", "code_visual_token", "Numeric literal tokens per non-empty source line."),
        FeatureDefinition("visual_period_density", "code_visual_token", "Period/member-access tokens per non-empty source line."),
        FeatureDefinition("visual_comma_density", "code_visual_token", "Comma tokens per non-empty source line."),
        FeatureDefinition("visual_identifier_area_ratio", "code_visual_area", "Approximate visual area occupied by identifier tokens divided by non-whitespace code area."),
        FeatureDefinition("visual_keyword_area_ratio", "code_visual_area", "Approximate visual area occupied by keyword tokens divided by non-whitespace code area."),
        FeatureDefinition("visual_operator_area_ratio", "code_visual_area", "Approximate visual area occupied by operator tokens divided by non-whitespace code area."),
        FeatureDefinition("visual_keyword_identifier_area_ratio", "code_visual_area", "Approximate keyword visual area divided by identifier visual area."),
        FeatureDefinition("visual_identifier_y_mean", "code_visual_position", "Normalized mean vertical position of identifier tokens."),
        FeatureDefinition("visual_identifier_y_std", "code_visual_position", "Normalized standard deviation of identifier token vertical positions."),
        FeatureDefinition("visual_keyword_y_mean", "code_visual_position", "Normalized mean vertical position of keyword tokens."),
        FeatureDefinition("visual_keyword_y_std", "code_visual_position", "Normalized standard deviation of keyword token vertical positions."),
        FeatureDefinition("visual_operator_y_mean", "code_visual_position", "Normalized mean vertical position of operator tokens."),
        FeatureDefinition("visual_operator_y_std", "code_visual_position", "Normalized standard deviation of operator token vertical positions."),
        FeatureDefinition("visual_period_y_mean", "code_visual_position", "Normalized mean vertical position of period/member-access tokens."),
        FeatureDefinition("visual_period_y_std", "code_visual_position", "Normalized standard deviation of period/member-access token vertical positions."),
        FeatureDefinition("visual_line_length_dft_energy", "code_visual_dft", "Normalized low-frequency DFT energy of the per-line length series."),
        FeatureDefinition("visual_space_dft_energy", "code_visual_dft", "Normalized low-frequency DFT energy of the per-line whitespace count series."),
        FeatureDefinition("visual_identifier_dft_energy", "code_visual_dft", "Normalized low-frequency DFT energy of the per-line identifier count series."),
        FeatureDefinition("visual_keyword_dft_energy", "code_visual_dft", "Normalized low-frequency DFT energy of the per-line keyword count series."),
        FeatureDefinition("visual_period_dft_energy", "code_visual_dft", "Normalized low-frequency DFT energy of the per-line period/member-access count series."),
        FeatureDefinition("chunk_y_mean", "cognascore_visual_chunk", "Normalized mean vertical position of CognaScore chunks."),
        FeatureDefinition("chunk_y_std", "cognascore_visual_chunk", "Normalized standard deviation of CognaScore chunk vertical positions."),
        FeatureDefinition("chunk_line_span", "cognascore_visual_chunk", "Number of source lines spanned by all CognaScore chunks."),
        FeatureDefinition("chunk_line_span_ratio", "cognascore_visual_chunk", "CognaScore chunk line span divided by non-empty LOC."),
        FeatureDefinition("chunks_per_loc", "cognascore_chunk", "CognaScore chunks divided by non-empty LOC."),
        FeatureDefinition("mean_chunks_per_source_line", "cognascore_chunk", "Mean chunk count on source lines that contain chunks."),
        FeatureDefinition("std_chunks_per_source_line", "cognascore_chunk", "Standard deviation of per-line chunk count."),
        FeatureDefinition("max_chunks_per_source_line", "cognascore_chunk", "Maximum chunks on one source line."),
        FeatureDefinition("unique_lexeme_ratio", "cognascore_chunk", "Distinct chunk lexemes divided by all chunks."),
        FeatureDefinition("lexeme_entropy", "cognascore_chunk", "Shannon entropy of chunk lexeme frequencies."),
        FeatureDefinition("log_avg_chunk_chars", "cognascore_chunk", "log(1 + average chunk character length)."),
        FeatureDefinition("chunk_chars_cv", "cognascore_chunk", "Coefficient of variation for chunk character length."),
        FeatureDefinition("log_max_chunk_chars", "cognascore_chunk", "log(1 + maximum chunk character length)."),
        FeatureDefinition("log_avg_chunk_tokens", "cognascore_chunk", "log(1 + average token count inside a chunk)."),
        FeatureDefinition("chunk_tokens_cv", "cognascore_chunk", "Coefficient of variation for token count inside chunks."),
        FeatureDefinition("identifier_count", "cognascore_identifier_quality", "Number of identifier chunks."),
        FeatureDefinition("identifier_mean_length", "cognascore_identifier_quality", "Mean character length of identifier chunks."),
        FeatureDefinition("identifier_std_length", "cognascore_identifier_quality", "Standard deviation of identifier character length."),
        FeatureDefinition("identifier_max_length", "cognascore_identifier_quality", "Maximum character length among identifier chunks."),
        FeatureDefinition("identifier_length_cv", "cognascore_identifier_quality", "Coefficient of variation for identifier character length."),
        FeatureDefinition("identifier_single_letter_ratio", "cognascore_identifier_quality", "Single-letter identifiers divided by identifier chunks."),
        FeatureDefinition("identifier_repeated_char_ratio", "cognascore_identifier_quality", "Identifiers dominated by repeated characters divided by identifier chunks."),
        FeatureDefinition("identifier_digit_char_ratio", "cognascore_identifier_quality", "Digit characters divided by all identifier characters."),
        FeatureDefinition("identifier_subtoken_count_mean", "cognascore_identifier_quality", "Mean number of camel/snake-case subtokens per identifier."),
        FeatureDefinition("halstead_volume", "code_halstead", "Primitive Halstead volume from Java-style tokenization."),
        FeatureDefinition("log_halstead_volume", "code_halstead", "log(1 + Halstead volume)."),
        FeatureDefinition("byte_entropy", "code_text", "Byte-level Shannon entropy of the source text."),
        FeatureDefinition("token_count", "code_halstead", "Java-style token count."),
        FeatureDefinition("log_token_count", "code_halstead", "log(1 + token_count)."),
        FeatureDefinition("compression_zlib_ratio", "code_compression", "zlib-compressed byte length divided by raw byte length."),
        FeatureDefinition("compression_bz2_ratio", "code_compression", "bz2-compressed byte length divided by raw byte length."),
        FeatureDefinition("compression_lzma_ratio", "code_compression", "lzma-compressed byte length divided by raw byte length."),
        FeatureDefinition("compression_zlib_line_ratio_mean", "code_compression", "Mean zlib compression ratio over non-empty source lines."),
        FeatureDefinition("compression_zlib_line_ratio_std", "code_compression", "Standard deviation of zlib compression ratio over non-empty source lines."),
        FeatureDefinition("compression_lzma_block5_ratio_mean", "code_compression", "Mean lzma compression ratio over five-line non-empty source blocks."),
        FeatureDefinition("compression_cross_line_redundancy_zlib", "code_compression", "Line-wise zlib compression ratio minus whole-snippet zlib compression ratio."),
        FeatureDefinition("compression_cross_line_redundancy_lzma", "code_compression", "Five-line-block lzma compression ratio minus whole-snippet lzma compression ratio."),
        FeatureDefinition("compression_algorithm_ratio_range", "code_compression", "Range between zlib, bz2, and lzma whole-snippet compression ratios."),
    ]


BASE_FEATURE_NAMES = tuple(definition.name for definition in feature_definitions())


CLUSTER_STAT_NAMES: tuple[str, ...] = ()

SEMANTIC_CHUNK_TYPES = (
    "COMMENT",
    "IMPORT",
    "UNUSED_IMPORT",
    "REGEX",
    "BITWISE",
    "IDENTIFIER",
    "DECLARATION",
    "LITERAL",
    "CALL",
    "CONTROL_FLOW",
    "ASSIGNMENT",
    "ARITHMETIC",
    "COMPARISON",
    "LOGICAL",
)

TYPE_STAT_SUFFIXES = (
    "count",
    "ratio",
)

TYPE_STAT_NAMES = tuple(
    f"type_{chunk_type.lower()}_{suffix}"
    for chunk_type in SEMANTIC_CHUNK_TYPES
    for suffix in TYPE_STAT_SUFFIXES
)


def extract_feature_row(
    *,
    dataset: str,
    item: DatasetItem,
    extractor: LexemeExtractor | None = None,
) -> dict[str, Any]:
    active_extractor = extractor or LexemeExtractor()
    chunks, _ = active_extractor.extract_with_member_fallback(item.content)
    chunks.sort(key=lambda chunk: (chunk.line, chunk.lexeme))
    lexemes = [chunk.lexeme for chunk in chunks]
    lexeme_counts = Counter(lexemes)
    chunks_by_line = Counter(chunk.line for chunk in chunks)
    nonblank_lines = [line for line in item.content.splitlines() if line.strip()]
    blank_line_count = len(item.content.splitlines()) - len(nonblank_lines)
    loc = len(nonblank_lines)
    line_lengths = [len(line) for line in nonblank_lines] or [0]
    indents = [len(line) - len(line.lstrip()) for line in nonblank_lines] or [0]
    indent_transitions = [abs(right - left) for left, right in zip(indents, indents[1:])]
    per_line = list(chunks_by_line.values()) or [0]
    chunk_char_lengths = [len(lexeme) for lexeme in lexemes] or [0]
    chunk_token_lengths = [_chunk_token_count(lexeme) for lexeme in lexemes] or [0]
    identifier_lexemes = [chunk.lexeme for chunk in chunks if chunk.type.upper() == "IDENTIFIER"]
    identifier_lengths = [len(lexeme) for lexeme in identifier_lexemes] or [0]
    identifier_char_count = sum(identifier_lengths)
    identifier_digit_count = sum(sum(1 for char in lexeme if char.isdigit()) for lexeme in identifier_lexemes)
    identifier_subtoken_counts = [_identifier_subtoken_count(lexeme) for lexeme in identifier_lexemes] or [0]

    posnett = posnett_model(item.content)
    lexeme_count = len(chunks)
    vocabulary_size = int(posnett.vocabulary_size)
    type_counts = Counter(chunk.type.upper() for chunk in chunks)
    visual_features = visual_layout_features(item.content, chunks)

    row: dict[str, Any] = {
        "dataset": dataset,
        "task_id": item.task_id,
        "readability_score": item.readability_score,
        "log_vocabulary_size": math.log1p(vocabulary_size),
        "vocabulary_size": vocabulary_size,
        "lexeme_count": lexeme_count,
        "log_lexeme_count": math.log1p(lexeme_count),
        "loc": loc,
        "log_loc": math.log1p(loc),
        "blank_line_count": blank_line_count,
        "mean_line_length": mean(line_lengths),
        "std_line_length": pstdev(line_lengths) if len(line_lengths) > 1 else 0.0,
        "max_line_length": max(line_lengths, default=0),
        "mean_indent": mean(indents),
        "std_indent": pstdev(indents) if len(indents) > 1 else 0.0,
        "max_indent": max(indents, default=0),
        "line_length_cv": _coefficient_of_variation(line_lengths),
        "indent_cv": _coefficient_of_variation(indents),
        "indent_transition_mean": mean(indent_transitions) if indent_transitions else 0.0,
        "indent_transition_std": pstdev(indent_transitions) if len(indent_transitions) > 1 else 0.0,
        "indent_transition_max": max(indent_transitions, default=0),
        "blank_line_ratio": blank_line_count / max(len(item.content.splitlines()), 1),
        "long_line_ratio_80": sum(1 for length in line_lengths if length > 80) / max(loc, 1),
        "long_line_ratio_100": sum(1 for length in line_lengths if length > 100) / max(loc, 1),
        **visual_features,
        "chunks_per_loc": len(chunks) / max(loc, 1),
        "mean_chunks_per_source_line": mean(per_line),
        "std_chunks_per_source_line": pstdev(per_line) if len(per_line) > 1 else 0.0,
        "max_chunks_per_source_line": max(per_line, default=0),
        "unique_lexeme_ratio": len(lexeme_counts) / max(len(chunks), 1),
        "lexeme_entropy": _entropy(lexeme_counts),
        "log_avg_chunk_chars": math.log1p(mean(chunk_char_lengths)),
        "chunk_chars_cv": _coefficient_of_variation(chunk_char_lengths),
        "log_max_chunk_chars": math.log1p(max(chunk_char_lengths, default=0)),
        "log_avg_chunk_tokens": math.log1p(mean(chunk_token_lengths)),
        "chunk_tokens_cv": _coefficient_of_variation(chunk_token_lengths),
        "identifier_count": len(identifier_lexemes),
        "identifier_mean_length": mean(identifier_lengths),
        "identifier_std_length": pstdev(identifier_lengths) if len(identifier_lengths) > 1 else 0.0,
        "identifier_max_length": max(identifier_lengths, default=0),
        "identifier_length_cv": _coefficient_of_variation(identifier_lengths),
        "identifier_single_letter_ratio": sum(1 for lexeme in identifier_lexemes if len(lexeme) == 1) / max(len(identifier_lexemes), 1),
        "identifier_repeated_char_ratio": sum(1 for lexeme in identifier_lexemes if _is_repeated_char_identifier(lexeme)) / max(len(identifier_lexemes), 1),
        "identifier_digit_char_ratio": identifier_digit_count / max(identifier_char_count, 1),
        "identifier_subtoken_count_mean": mean(identifier_subtoken_counts),
        "halstead_volume": posnett.halstead_volume,
        "log_halstead_volume": math.log1p(posnett.halstead_volume),
        "byte_entropy": posnett.byte_entropy,
        "token_count": posnett.token_count,
        "log_token_count": math.log1p(posnett.token_count),
        **compression_features(item.content),
    }
    for name in CLUSTER_STAT_NAMES:
        row[name] = 0.0
    for chunk_type in SEMANTIC_CHUNK_TYPES:
        count = float(type_counts.get(chunk_type, 0))
        prefix = f"type_{chunk_type.lower()}"
        row[f"{prefix}_count"] = count
        row[f"{prefix}_ratio"] = count / max(float(lexeme_count), 1.0)
    return row


def write_feature_database(
    *,
    rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
    metadata: Mapping[str, Any],
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "features.csv"
    metadata_path = output_dir / "metadata.json"
    columns = _ordered_columns(rows)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    definitions = _definitions_for_columns(columns)
    metadata_payload = {
        **metadata,
        "row_count": len(rows),
        "columns": columns,
        "feature_definitions": [asdict(definition) for definition in definitions],
    }
    metadata_path.write_text(json.dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, metadata_path


def _ordered_columns(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    discovered = set()
    for row in rows:
        discovered.update(row.keys())
    columns = list(IDENTITY_COLUMNS)
    for name in BASE_FEATURE_NAMES:
        if name in discovered and name not in columns:
            columns.append(name)
    for name in CLUSTER_STAT_NAMES:
        if name in discovered and name not in columns:
            columns.append(name)
    columns.extend(name for name in TYPE_STAT_NAMES if name not in columns)
    columns.extend(sorted(name for name in discovered if name not in columns))
    return columns


def _definitions_for_columns(columns: Sequence[str]) -> list[FeatureDefinition]:
    known = {definition.name: definition for definition in feature_definitions()}
    definitions: list[FeatureDefinition] = []
    for column in columns:
        if column in IDENTITY_COLUMNS:
            definitions.append(FeatureDefinition(column, "identity", f"Dataset identity column: {column}."))
        elif column in known:
            definitions.append(known[column])
        elif column in CLUSTER_STAT_NAMES:
            definitions.append(FeatureDefinition(column, "cognascore_cluster_removed", f"Removed legacy cluster statistic: {column}."))
        elif column in TYPE_STAT_NAMES:
            definitions.append(FeatureDefinition(column, "cognascore_type_inventory", f"Per-chunk-type CognaScore inventory statistic: {column}."))
        elif column.startswith("type_"):
            definitions.append(FeatureDefinition(column, "extra_type_inventory", f"Additional non-schema chunk-type inventory statistic: {column}."))
        else:
            definitions.append(FeatureDefinition(column, "extra", f"Additional feature: {column}."))
    return definitions


def _entropy(counts: Mapping[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((count / total) * math.log(count / total) for count in counts.values())


def _chunk_token_count(text: str) -> int:
    return len([part for part in text.replace("_", " ").split() if part]) or int(bool(text))


def _identifier_subtoken_count(identifier: str) -> int:
    subtokens = _identifier_subtokens(identifier)
    return len(subtokens) or int(bool(identifier))


def _identifier_subtokens(identifier: str) -> list[str]:
    parts = re.split(r"[_$\W]+", identifier)
    subtokens: list[str] = []
    for part in parts:
        if not part:
            continue
        subtokens.extend(
            token.lower()
            for token in re.findall(
                r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
                part,
            )
            if token
        )
    return subtokens


def _is_repeated_char_identifier(identifier: str) -> bool:
    letters = [char.lower() for char in identifier if char.isalpha()]
    if len(letters) < 3:
        return False
    counts = Counter(letters)
    return max(counts.values()) / len(letters) >= 0.8


def compression_features(source: str) -> dict[str, float]:
    raw = source.encode("utf-8")
    zlib_ratio = _compression_ratio(raw, zlib.compress)
    bz2_ratio = _compression_ratio(raw, bz2.compress)
    lzma_ratio = _compression_ratio(raw, lzma.compress)

    nonempty_lines = [line.encode("utf-8") for line in source.splitlines() if line.strip()]
    zlib_line_ratios = [_compression_ratio(line, zlib.compress) for line in nonempty_lines if len(line) >= 12]

    block_texts = [
        b"\n".join(nonempty_lines[index : index + 5])
        for index in range(0, len(nonempty_lines), 5)
    ]
    lzma_block5_ratios = [_compression_ratio(block, lzma.compress) for block in block_texts if len(block) >= 12]

    zlib_line_mean = mean(zlib_line_ratios) if zlib_line_ratios else 0.0
    lzma_block5_mean = mean(lzma_block5_ratios) if lzma_block5_ratios else 0.0
    whole_ratios = [zlib_ratio, bz2_ratio, lzma_ratio]
    return {
        "compression_zlib_ratio": zlib_ratio,
        "compression_bz2_ratio": bz2_ratio,
        "compression_lzma_ratio": lzma_ratio,
        "compression_zlib_line_ratio_mean": zlib_line_mean,
        "compression_zlib_line_ratio_std": pstdev(zlib_line_ratios) if len(zlib_line_ratios) > 1 else 0.0,
        "compression_lzma_block5_ratio_mean": lzma_block5_mean,
        "compression_cross_line_redundancy_zlib": zlib_line_mean - zlib_ratio,
        "compression_cross_line_redundancy_lzma": lzma_block5_mean - lzma_ratio,
        "compression_algorithm_ratio_range": max(whole_ratios) - min(whole_ratios),
    }


def _compression_ratio(raw: bytes, compressor) -> float:
    if not raw:
        return 0.0
    return len(compressor(raw)) / len(raw)


def _coefficient_of_variation(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    avg = mean(values)
    if avg == 0.0:
        return 0.0
    variance = mean([(value - avg) ** 2 for value in values])
    return math.sqrt(variance) / avg
