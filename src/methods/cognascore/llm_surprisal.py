"""Four causal-LM features computed from the original, unmodified source.

Masking here is private lexical bookkeeping for identifier alignment: comments
and string literals are blanked in a temporary, offset-preserving copy only
when locating identifiers. That copy is never passed to the language model.
The boolean token-overlap mask only selects losses for identifier aggregation.
Neither mechanism uses RMC masking or constructed-dataset interventions, and
neither is an experimental source-code transformation.
"""

from __future__ import annotations

import hashlib
import io
import json
import keyword
import math
import re
import sqlite3
import tokenize
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time
from typing import Sequence

import numpy as np

from src.methods.posnett.method import C_LIKE_KEYWORDS, C_LIKE_LANGUAGES


LLM_SURPRISAL_BUILD_VERSION = 2
DEFAULT_CAUSAL_LM = "Qwen/Qwen2.5-Coder-0.5B"
DEFAULT_CAUSAL_LM_REVISION = "8123ea2e9354afb7ffcc6c8641d1b2f5ecf18301"
LLM_SURPRISAL_FEATURE_NAMES = (
    "llm__code_perplexity",
    "llm__code_bits_per_byte",
    "llm__local_surprisal_concentration",
    "llm__identifier_excess_surprisal",
)


@dataclass(frozen=True)
class SurprisalConfiguration:
    model_name: str
    resolved_revision: str
    window_tokens: int
    stride_tokens: int
    local_block_tokens: int
    tail_fraction: float
    build_version: int = LLM_SURPRISAL_BUILD_VERSION

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TokenLoss:
    token_index: int
    start: int
    end: int
    nll: float


def aggregate_surprisal_features(
    source: str,
    token_losses: Sequence[TokenLoss],
    *,
    identifier_spans: Sequence[tuple[int, int]],
    local_block_tokens: int,
    tail_fraction: float,
) -> dict[str, float]:
    """Aggregate one causal-LM loss trace into four scalar features."""
    if not token_losses:
        raise ValueError("At least one scored token is required.")
    if local_block_tokens < 1:
        raise ValueError("local_block_tokens must be positive.")
    if not 0.0 < tail_fraction <= 1.0:
        raise ValueError("tail_fraction must be in (0, 1].")

    losses = np.asarray([row.nll for row in token_losses], dtype=np.float64)
    if not np.isfinite(losses).all():
        raise ValueError("The causal language model produced a non-finite token loss.")

    mean_nll = float(np.mean(losses))
    if mean_nll >= math.log(np.finfo(np.float64).max):
        raise OverflowError("Mean token loss is too large to represent perplexity.")

    byte_weights = np.asarray(
        [_span_byte_length(source, row.start, row.end) for row in token_losses],
        dtype=np.float64,
    )
    scored_bytes = float(np.sum(byte_weights))
    if scored_bytes <= 0:
        raise ValueError("Scored tokens do not cover any source bytes.")
    loss_bits = losses / math.log(2.0)
    code_bits_per_byte = float(np.sum(loss_bits) / scored_bytes)

    block_values = []
    for start in range(0, len(token_losses), local_block_tokens):
        stop = min(start + local_block_tokens, len(token_losses))
        block_bytes = float(np.sum(byte_weights[start:stop]))
        if block_bytes > 0:
            block_values.append(float(np.sum(loss_bits[start:stop]) / block_bytes))
    if not block_values:
        raise ValueError("No non-empty local token blocks were available.")
    tail_count = max(1, math.ceil(len(block_values) * tail_fraction))
    local_concentration = float(np.mean(sorted(block_values, reverse=True)[:tail_count]))

    # Select already-computed losses; do not mask or rescore model inputs.
    identifier_mask = _overlap_mask(token_losses, identifier_spans)
    identifier_bytes = float(np.sum(byte_weights[identifier_mask]))
    if identifier_bytes > 0:
        identifier_bits_per_byte = float(np.sum(loss_bits[identifier_mask]) / identifier_bytes)
        identifier_excess = identifier_bits_per_byte - code_bits_per_byte
    else:
        identifier_excess = 0.0

    return {
        "llm__code_perplexity": math.exp(mean_nll),
        "llm__code_bits_per_byte": code_bits_per_byte,
        "llm__local_surprisal_concentration": local_concentration,
        "llm__identifier_excess_surprisal": identifier_excess,
    }


def identifier_spans(
    source: str,
    *,
    language: str,
    allow_fragments: bool = False,
) -> list[tuple[int, int]]:
    """Locate lexical identifiers in original-source character coordinates.

    Java/Python normally use tokenizers; C-like code and the Python fragment
    fallback use local comment/string blanking. This feature-internal logic
    is independent of experimental masking and does not modify LM input.
    """
    normalized = str(language or "java").strip().lower()
    if normalized in {"python", "py"}:
        return _python_identifier_spans(source, allow_fragments=allow_fragments)
    if normalized == "java":
        return _java_identifier_spans(source)
    if normalized in C_LIKE_LANGUAGES:
        return _c_like_identifier_spans(source)
    raise ValueError(f"Unsupported language for LLM surprisal features: {language!r}")


class SurprisalFeatureCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS features (
                source_sha256 TEXT NOT NULL,
                configuration_sha256 TEXT NOT NULL,
                model_name TEXT NOT NULL,
                resolved_revision TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                code_perplexity REAL NOT NULL,
                code_bits_per_byte REAL NOT NULL,
                local_surprisal_concentration REAL NOT NULL,
                identifier_excess_surprisal REAL NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (source_sha256, configuration_sha256)
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SurprisalFeatureCache":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def get(self, source_sha256: str, configuration_sha256: str) -> dict[str, float] | None:
        row = self.connection.execute(
            """
            SELECT code_perplexity, code_bits_per_byte,
                   local_surprisal_concentration, identifier_excess_surprisal
            FROM features
            WHERE source_sha256 = ? AND configuration_sha256 = ?
            """,
            (source_sha256, configuration_sha256),
        ).fetchone()
        if row is None:
            return None
        return dict(zip(LLM_SURPRISAL_FEATURE_NAMES, map(float, row)))

    def upsert(
        self,
        *,
        source_sha256: str,
        configuration: SurprisalConfiguration,
        token_count: int,
        features: dict[str, float],
    ) -> None:
        values = [float(features[name]) for name in LLM_SURPRISAL_FEATURE_NAMES]
        self.connection.execute(
            """
            INSERT OR REPLACE INTO features (
                source_sha256, configuration_sha256, model_name,
                resolved_revision, token_count, code_perplexity,
                code_bits_per_byte, local_surprisal_concentration,
                identifier_excess_surprisal, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_sha256,
                configuration.fingerprint,
                configuration.model_name,
                configuration.resolved_revision,
                int(token_count),
                *values,
                time(),
            ),
        )
        self.connection.commit()


def _span_byte_length(source: str, start: int, end: int) -> int:
    if end <= start:
        return 0
    return len(source[max(start, 0):max(end, 0)].encode("utf-8"))


def _overlap_mask(
    token_losses: Sequence[TokenLoss],
    spans: Sequence[tuple[int, int]],
) -> np.ndarray:
    """Select existing token losses by span overlap; never alter source text.

    Runs in linear time for source-ordered inputs. This aggregation mask is
    unrelated to RMC or constructed-dataset masking experiments.
    """
    ordered_spans = sorted(spans)
    mask = np.zeros(len(token_losses), dtype=bool)
    span_index = 0
    for token_index, token in enumerate(token_losses):
        while span_index < len(ordered_spans) and ordered_spans[span_index][1] <= token.start:
            span_index += 1
        probe = span_index
        while probe < len(ordered_spans) and ordered_spans[probe][0] < token.end:
            left, right = ordered_spans[probe]
            if token.start < right and token.end > left:
                mask[token_index] = True
                break
            probe += 1
    return mask


def _line_starts(source: str) -> list[int]:
    starts = [0]
    starts.extend(index + 1 for index, char in enumerate(source) if char == "\n")
    return starts


def _absolute_offset(line_starts: Sequence[int], line: int, column: int) -> int:
    if line < 1 or line > len(line_starts):
        raise ValueError(f"Token position has invalid line number: {line}")
    return int(line_starts[line - 1] + column)


def _python_identifier_spans(
    source: str,
    *,
    allow_fragments: bool,
) -> list[tuple[int, int]]:
    starts = _line_starts(source)
    spans = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type != tokenize.NAME or keyword.iskeyword(token.string):
                continue
            start = _absolute_offset(starts, token.start[0], token.start[1])
            end = _absolute_offset(starts, token.end[0], token.end[1])
            spans.append((start, end))
    except (IndentationError, SyntaxError, tokenize.TokenError) as exc:
        if not allow_fragments:
            raise ValueError("Python tokenization failed while locating identifiers.") from exc
        masked = _mask_python_comments_and_strings(source)
        return [
            match.span()
            for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", masked)
            if not keyword.iskeyword(match.group(0))
        ]
    return spans


def _java_identifier_spans(source: str) -> list[tuple[int, int]]:
    import javalang.tokenizer

    starts = _line_starts(source)
    spans = []
    try:
        for token in javalang.tokenizer.tokenize(source):
            if not isinstance(token, javalang.tokenizer.Identifier):
                continue
            line, one_based_column = token.position
            start = _absolute_offset(starts, int(line), int(one_based_column) - 1)
            spans.append((start, start + len(token.value)))
    except (javalang.tokenizer.LexerError, TypeError, ValueError) as exc:
        raise ValueError("Java tokenization failed while locating identifiers.") from exc
    return spans


def _c_like_identifier_spans(source: str) -> list[tuple[int, int]]:
    masked = _mask_c_like_comments_and_strings(source)
    return [
        match.span()
        for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", masked)
        if match.group(0) not in C_LIKE_KEYWORDS
    ]


def _mask_c_like_comments_and_strings(source: str) -> str:
    """Blank comments/strings only for feature-local identifier lookup.

    Preserves character offsets in a temporary copy; the LM scores the
    original source, including comments and strings. Do not replace this
    helper with an experimental code-masking or intervention pipeline.
    """
    chars = list(source)
    index = 0
    state = "code"
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if char == "/" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if char == "/" and next_char == "*":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if char in {'"', "'"}:
                chars[index] = " "
                state = "double_string" if char == '"' else "single_string"
            index += 1
            continue
        if state == "line_comment":
            if char == "\n":
                state = "code"
            else:
                chars[index] = " "
            index += 1
            continue
        if state == "block_comment":
            if char == "*" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "code"
            else:
                if char != "\n":
                    chars[index] = " "
                index += 1
            continue
        chars[index] = " "
        if char == "\\" and index + 1 < len(source):
            chars[index + 1] = " "
            index += 2
            continue
        if (state == "double_string" and char == '"') or (
            state == "single_string" and char == "'"
        ):
            state = "code"
        index += 1
    return "".join(chars)


def _mask_python_comments_and_strings(source: str) -> str:
    """Blank comments/strings only for feature-local identifier lookup.

    Preserves character offsets in a temporary copy; the LM scores the
    original source, including comments and strings. Do not replace this
    helper with an experimental code-masking or intervention pipeline.
    """
    chars = list(source)
    index = 0
    quote: str | None = None
    triple = False
    while index < len(source):
        char = source[index]
        if quote is not None:
            delimiter = quote * (3 if triple else 1)
            if source.startswith(delimiter, index):
                for offset in range(len(delimiter)):
                    chars[index + offset] = " "
                index += len(delimiter)
                quote = None
                triple = False
                continue
            if char == "\\" and index + 1 < len(source):
                chars[index] = chars[index + 1] = " "
                index += 2
                continue
            if char != "\n":
                chars[index] = " "
            index += 1
            continue
        if source.startswith("'''", index) or source.startswith('\"\"\"', index):
            quote = char
            triple = True
            chars[index:index + 3] = [" ", " ", " "]
            index += 3
            continue
        if char in {"'", '"'}:
            quote = char
            chars[index] = " "
            index += 1
            continue
        if char == "#":
            end = source.find("\n", index)
            end = len(source) if end < 0 else end
            chars[index:end] = [" "] * (end - index)
            index = end
            continue
        index += 1
    return "".join(chars)
