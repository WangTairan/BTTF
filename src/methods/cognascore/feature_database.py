from __future__ import annotations

import csv
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

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
        FeatureDefinition("generalized_score", "cognascore_formula", "Frozen two-feature CognaScore formula output."),
        FeatureDefinition("log_vocabulary_size", "cognascore_formula", "log(1 + vocabulary_size)."),
        FeatureDefinition("vocabulary_size", "code_halstead", "Number of distinct operators and operands."),
        FeatureDefinition("noise_ratio", "cognascore_cluster_legacy", "Legacy unclustered CognaScore chunks divided by all chunks, including junk."),
        FeatureDefinition("semantic_chunk_count", "cognascore_semantic_chunk", "Number of non-junk CognaScore chunks."),
        FeatureDefinition("log_semantic_chunk_count", "cognascore_semantic_chunk", "log(1 + semantic_chunk_count)."),
        FeatureDefinition("semantic_chunk_ratio", "cognascore_semantic_chunk", "Non-junk chunks divided by all chunks."),
        FeatureDefinition("semantic_noise_lexeme_count", "cognascore_semantic_cluster", "Estimated number of non-junk chunks labelled as DBSCAN noise."),
        FeatureDefinition("semantic_noise_ratio", "cognascore_semantic_cluster", "Estimated non-junk noise chunks divided by non-junk chunks."),
        FeatureDefinition("junk_count", "cognascore_junk", "Number of chunks labelled JUNK by CognaScore extraction."),
        FeatureDefinition("log_junk_count", "cognascore_junk", "log(1 + junk_count)."),
        FeatureDefinition("junk_ratio", "cognascore_junk", "JUNK chunks divided by all chunks."),
        FeatureDefinition("junk_unique_ratio", "cognascore_junk", "Distinct JUNK lexemes divided by all JUNK chunks."),
        FeatureDefinition("junk_noise_lexeme_count", "cognascore_junk", "Estimated number of JUNK chunks labelled as DBSCAN noise."),
        FeatureDefinition("junk_noise_ratio", "cognascore_junk", "JUNK chunks labelled as DBSCAN noise divided by all JUNK chunks."),
        FeatureDefinition("junk_cluster_count", "cognascore_junk", "Number of DBSCAN cluster labels containing JUNK chunks."),
        FeatureDefinition("lexeme_count", "cognascore_chunk", "Number of extracted CognaScore chunks."),
        FeatureDefinition("log_lexeme_count", "cognascore_chunk", "log(1 + lexeme_count)."),
        FeatureDefinition("noise_lexeme_count", "cognascore_cluster", "Number of chunks labelled as DBSCAN noise."),
        FeatureDefinition("cluster_count", "cognascore_cluster", "Number of non-noise DBSCAN clusters."),
        FeatureDefinition("log_cluster_count", "cognascore_cluster", "log(1 + cluster_count)."),
        FeatureDefinition("avg_cluster_diameter", "cognascore_cluster", "Mean within-cluster cosine diameter."),
        FeatureDefinition("chunks_per_cluster", "cognascore_cluster", "lexeme_count divided by non-noise cluster count."),
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
        FeatureDefinition("semantic_chunk_y_mean", "cognascore_visual_chunk", "Normalized mean vertical position of non-junk CognaScore chunks."),
        FeatureDefinition("semantic_chunk_y_std", "cognascore_visual_chunk", "Normalized standard deviation of non-junk CognaScore chunk vertical positions."),
        FeatureDefinition("junk_chunk_y_mean", "cognascore_visual_chunk", "Normalized mean vertical position of JUNK chunks."),
        FeatureDefinition("junk_chunk_y_std", "cognascore_visual_chunk", "Normalized standard deviation of JUNK chunk vertical positions."),
        FeatureDefinition("chunk_line_span", "cognascore_visual_chunk", "Number of source lines spanned by all CognaScore chunks."),
        FeatureDefinition("chunk_line_span_ratio", "cognascore_visual_chunk", "CognaScore chunk line span divided by non-empty LOC."),
        FeatureDefinition("semantic_chunk_line_span", "cognascore_visual_chunk", "Number of source lines spanned by non-junk CognaScore chunks."),
        FeatureDefinition("semantic_chunk_line_span_ratio", "cognascore_visual_chunk", "Non-junk CognaScore chunk line span divided by non-empty LOC."),
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
        FeatureDefinition("halstead_volume", "code_halstead", "Primitive Halstead volume from Java-style tokenization."),
        FeatureDefinition("log_halstead_volume", "code_halstead", "log(1 + Halstead volume)."),
        FeatureDefinition("byte_entropy", "code_text", "Byte-level Shannon entropy of the source text."),
        FeatureDefinition("token_count", "code_halstead", "Java-style token count."),
        FeatureDefinition("log_token_count", "code_halstead", "log(1 + token_count)."),
    ]


BASE_FEATURE_NAMES = tuple(definition.name for definition in feature_definitions())


CLUSTER_STAT_NAMES = (
    "cluster_size_mean",
    "cluster_size_std",
    "cluster_size_max",
    "cluster_diameter_mean",
    "cluster_diameter_std",
    "cluster_diameter_max",
)

SEMANTIC_CHUNK_TYPES = (
    "NORMAL",
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
    "noise_ratio",
    "cluster_count",
    "cluster_size_mean",
    "cluster_size_std",
    "cluster_size_max",
    "cluster_diameter_mean",
    "cluster_diameter_std",
    "cluster_diameter_max",
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
    cognascore_result: Mapping[str, Any],
    extractor: LexemeExtractor | None = None,
) -> dict[str, Any]:
    active_extractor = extractor or LexemeExtractor()
    chunks, _ = active_extractor.extract_with_member_fallback(item.content)
    chunks.sort(key=lambda chunk: (chunk.line, chunk.lexeme))
    lexemes = [chunk.lexeme for chunk in chunks]
    lexeme_counts = Counter(lexemes)
    junk_chunks = [chunk for chunk in chunks if chunk.type == "JUNK"]
    semantic_chunks = [chunk for chunk in chunks if chunk.type != "JUNK"]
    junk_lexeme_counts = Counter(chunk.lexeme for chunk in junk_chunks)
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

    posnett = posnett_model(item.content)
    statistics = cognascore_result.get("statistics", {})
    if not isinstance(statistics, Mapping):
        statistics = {}

    lexeme_count = int(cognascore_result.get("lexeme_count", len(chunks)) or 0)
    noise_count = int(cognascore_result.get("noise_lexeme_count", 0) or 0)
    cluster_count = int(cognascore_result.get("cluster_count", 0) or 0)
    noise_ratio = float(cognascore_result.get("noise_ratio", noise_count / max(lexeme_count, 1)) or 0.0)
    vocabulary_size = int(cognascore_result.get("vocabulary_size", posnett.vocabulary_size) or 0)
    junk_count = len(junk_chunks)
    semantic_count = len(semantic_chunks)
    junk_noise_ratio = float(statistics.get("type_junk_noise_ratio", 0.0))
    junk_noise_count = junk_count * junk_noise_ratio
    semantic_noise_count = max(float(noise_count) - junk_noise_count, 0.0)
    visual_features = visual_layout_features(item.content, chunks, semantic_chunks, junk_chunks)

    row: dict[str, Any] = {
        "dataset": dataset,
        "task_id": item.task_id,
        "readability_score": item.readability_score,
        "generalized_score": _float_or_default(
            cognascore_result.get("score", cognascore_result.get("generalized_score")),
        ),
        "log_vocabulary_size": _float_or_default(
            cognascore_result.get("log_vocabulary_size"),
            math.log1p(vocabulary_size),
        ),
        "vocabulary_size": vocabulary_size,
        "noise_ratio": noise_ratio,
        "semantic_chunk_count": semantic_count,
        "log_semantic_chunk_count": math.log1p(semantic_count),
        "semantic_chunk_ratio": semantic_count / max(len(chunks), 1),
        "semantic_noise_lexeme_count": semantic_noise_count,
        "semantic_noise_ratio": semantic_noise_count / max(semantic_count, 1),
        "junk_count": junk_count,
        "log_junk_count": math.log1p(junk_count),
        "junk_ratio": junk_count / max(len(chunks), 1),
        "junk_unique_ratio": len(junk_lexeme_counts) / max(junk_count, 1),
        "junk_noise_lexeme_count": junk_noise_count,
        "junk_noise_ratio": junk_noise_ratio,
        "junk_cluster_count": float(statistics.get("type_junk_cluster_count", 0.0)),
        "lexeme_count": lexeme_count,
        "log_lexeme_count": math.log1p(lexeme_count),
        "noise_lexeme_count": noise_count,
        "cluster_count": cluster_count,
        "log_cluster_count": math.log1p(cluster_count),
        "avg_cluster_diameter": _float_or_default(
            cognascore_result.get("avg_cluster_diameter"),
            _float_or_default(cognascore_result.get("avg_diameter")),
        ),
        "chunks_per_cluster": lexeme_count / max(cluster_count, 1),
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
        "halstead_volume": posnett.halstead_volume,
        "log_halstead_volume": math.log1p(posnett.halstead_volume),
        "byte_entropy": posnett.byte_entropy,
        "token_count": posnett.token_count,
        "log_token_count": math.log1p(posnett.token_count),
    }
    for name in CLUSTER_STAT_NAMES:
        row[name] = float(statistics.get(name, 0.0))
    for name in TYPE_STAT_NAMES:
        row[name] = float(statistics.get(name, 0.0))
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
            definitions.append(FeatureDefinition(column, "cognascore_cluster", f"CognaScore cluster statistic: {column}."))
        elif column in TYPE_STAT_NAMES:
            definitions.append(FeatureDefinition(column, "cognascore_type_cluster", f"Per-chunk-type CognaScore statistic: {column}."))
        elif column.startswith("type_junk_"):
            definitions.append(FeatureDefinition(column, "deprecated_junk_type", f"Deprecated JUNK type statistic excluded from the stable schema: {column}."))
        elif column.startswith("type_"):
            definitions.append(FeatureDefinition(column, "extra_type_cluster", f"Additional non-schema chunk-type statistic: {column}."))
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


def _coefficient_of_variation(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    avg = mean(values)
    if avg == 0.0:
        return 0.0
    variance = mean([(value - avg) ** 2 for value in values])
    return math.sqrt(variance) / avg


def _float_or_default(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
