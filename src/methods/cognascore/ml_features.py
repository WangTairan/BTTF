from __future__ import annotations

from collections import Counter
import math
from typing import Mapping, Sequence

import numpy as np

from src.methods.posnett.method import posnett_model

from .extractors.python import LexemeExtractor

try:
    import javalang
except ImportError:  # pragma: no cover
    javalang = None


CHUNK_TYPES = (
    "NORMAL",
    "COMMENT",
    "IMPORT",
    "UNUSED_IMPORT",
    "JUNK",
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

CLUSTER_STAT_SUFFIXES = (
    "noise_ratio",
    "cluster_count",
    "cluster_size_mean",
    "cluster_size_std",
    "cluster_size_max",
    "cluster_diameter_mean",
    "cluster_diameter_std",
    "cluster_diameter_max",
)

AST_NODE_TYPES = (
    "MethodDeclaration", "ConstructorDeclaration", "FormalParameter",
    "LocalVariableDeclaration", "MemberReference", "MethodInvocation",
    "Assignment", "BinaryOperation", "Literal", "IfStatement",
    "ForStatement", "WhileStatement", "DoStatement", "SwitchStatement",
    "SwitchStatementCase", "TryStatement", "CatchClause", "ThrowStatement",
    "ReturnStatement", "BreakStatement", "ContinueStatement", "ClassCreator",
    "LambdaExpression", "TernaryExpression", "Cast", "SynchronizedStatement",
    "ClassDeclaration", "InterfaceDeclaration", "EnumDeclaration", "Annotation",
)

JAVA_OPERATORS = ("+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "&", "|", "^", "<<", ">>")


def feature_names() -> list[str]:
    names = [
        "cognascore",
        "log_loc",
        "log_chunk_count",
        "chunks_per_loc",
        "log_cluster_count",
        "noise_ratio",
        "chunks_per_cluster",
        "unique_lexeme_ratio",
        "lexeme_entropy",
        "mean_line_length",
        "std_line_length",
        "max_line_length",
        "mean_indent",
        "std_indent",
        "max_indent",
        "mean_chunks_per_source_line",
        "std_chunks_per_source_line",
        "max_chunks_per_source_line",
    ]
    for chunk_type in CHUNK_TYPES:
        prefix = chunk_type.lower()
        names.extend((f"log_{prefix}_count", f"{prefix}_per_loc", f"{prefix}_unique_ratio"))
    names.extend(("log_halstead_volume", "byte_entropy", "log_token_count", "log_vocabulary_size"))
    names.extend(_cluster_stat_names())
    names.extend(("ast_node_count", "ast_max_depth", "ast_mean_depth"))
    for node_type in AST_NODE_TYPES:
        names.extend((f"ast_{node_type.lower()}_count", f"ast_{node_type.lower()}_per_loc"))
    names.extend(f"operator_{operator}_per_loc" for operator in JAVA_OPERATORS)
    return names


def _cluster_stat_names() -> list[str]:
    names = [
        "cluster_size_mean",
        "cluster_size_std",
        "cluster_size_max",
        "cluster_diameter_mean",
        "cluster_diameter_std",
        "cluster_diameter_max",
    ]
    for chunk_type in CHUNK_TYPES:
        names.extend(f"type_{chunk_type.lower()}_{suffix}" for suffix in CLUSTER_STAT_SUFFIXES)
    return names


def extract_features(
    code: str,
    cognascore_result: Mapping[str, object],
    *,
    extractor: LexemeExtractor | None = None,
) -> np.ndarray:
    active_extractor = extractor or LexemeExtractor()
    chunks, _ = active_extractor.extract_with_member_fallback(code)
    counts = Counter(chunk.type for chunk in chunks)
    lexemes = Counter(chunk.lexeme for chunk in chunks)
    chunks_by_line = Counter(chunk.line for chunk in chunks)
    nonblank_lines = [line for line in code.splitlines() if line.strip()]
    loc = len(nonblank_lines)
    chunk_count = len(chunks)
    cluster_count = int(cognascore_result.get("cluster_count", 0))
    noise_count = int(cognascore_result.get("noise_lexeme_count", 0))
    line_lengths = [len(line) for line in nonblank_lines] or [0]
    indents = [len(line) - len(line.lstrip()) for line in nonblank_lines] or [0]
    per_line = list(chunks_by_line.values()) or [0]

    values = [
        float(cognascore_result["score"]),
        math.log1p(loc),
        math.log1p(chunk_count),
        chunk_count / max(loc, 1),
        math.log1p(cluster_count),
        noise_count / max(chunk_count, 1),
        chunk_count / max(cluster_count, 1),
        len(lexemes) / max(chunk_count, 1),
        _entropy(lexemes),
        float(np.mean(line_lengths)),
        float(np.std(line_lengths)),
        float(max(line_lengths)),
        float(np.mean(indents)),
        float(np.std(indents)),
        float(max(indents)),
        float(np.mean(per_line)),
        float(np.std(per_line)),
        float(max(per_line)),
    ]
    for chunk_type in CHUNK_TYPES:
        typed = [chunk.lexeme for chunk in chunks if chunk.type == chunk_type]
        values.extend(
            (
                math.log1p(len(typed)),
                len(typed) / max(loc, 1),
                len(set(typed)) / max(len(typed), 1),
            )
        )

    posnett = posnett_model(code)
    values.extend(
        (
            math.log1p(posnett.halstead_volume),
            posnett.byte_entropy,
            math.log1p(posnett.token_count),
            math.log1p(posnett.vocabulary_size),
        )
    )
    statistics = cognascore_result.get("statistics", {})
    if not isinstance(statistics, Mapping):
        statistics = {}
    values.extend(float(statistics.get(name, 0.0)) for name in _cluster_stat_names())
    ast_counts, ast_depths = _ast_statistics(code)
    values.extend(
        (
            float(sum(ast_counts.values())),
            float(max(ast_depths, default=0)),
            float(np.mean(ast_depths)) if ast_depths else 0.0,
        )
    )
    for node_type in AST_NODE_TYPES:
        count = ast_counts[node_type]
        values.extend((math.log1p(count), count / max(loc, 1)))
    values.extend(code.count(operator) / max(loc, 1) for operator in JAVA_OPERATORS)
    return np.asarray(values, dtype=float)


def _entropy(counts: Mapping[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((count / total) * math.log(count / total) for count in counts.values())


def _ast_statistics(code: str) -> tuple[Counter[str], list[int]]:
    if javalang is None:
        return Counter(), []
    try:
        tree = javalang.parse.parse(code)
    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError):
        try:
            tree = javalang.parse.parse(f"class Snippet {{\n{code}\n}}")
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError):
            return Counter(), []
    counts: Counter[str] = Counter()
    depths: list[int] = []
    for path, node in tree:
        counts[node.__class__.__name__] += 1
        depths.append(sum(hasattr(parent, "attrs") for parent in path))
    return counts, depths
