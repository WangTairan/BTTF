"""Shared source-span helpers for the content-aware comment analysis."""

from __future__ import annotations

from src.methods.readability_model.llm_features.aggregate import _union
from src.methods.readability_model.llm_features.cache import _unpack
from src.methods.readability_model.llm_features.types import TokenLoss

COMMENT = "llm__comment__bpb_mean"


def comment_form(source: str, span, language: str) -> str:
    text = source[span.start : span.end]
    if language == "python":
        return "line" if text.startswith("#") else "documentation"
    if text.startswith("//"):
        return "line"
    if text.startswith("/**"):
        return "documentation"
    if text.startswith("/*"):
        return "block"
    raise ValueError(f"Unexpected comment representation: {text[:40]!r}")


def noncomment_intervals(length: int, comments) -> list[tuple[int, int]]:
    result, start = [], 0
    for left, right in _union(comments):
        if start < left:
            result.append((start, left))
        start = right
    if start < length:
        result.append((start, length))
    return result


def read_trace(
    connection, source_hash, configuration, expected_count, *, trace_sha256=None
):
    fingerprint = trace_sha256 or configuration.fingerprint_for("global")
    rows = connection.execute(
        "SELECT token_start, token_stop, payload FROM trace_windows "
        "WHERE source_sha256=? AND trace_sha256=? AND kind='global' "
        "ORDER BY token_start",
        (source_hash, fingerprint),
    )
    losses = []
    for start, stop, payload in rows:
        window = [TokenLoss(*values) for values in _unpack(payload)]
        if start != len(losses) or stop != start + len(window):
            raise ValueError("Cached global trace has a gap or overlap")
        if [value.token_index for value in window] != list(range(start, stop)):
            raise ValueError("Cached global trace has inconsistent token indices")
        losses.extend(window)
    if len(losses) != expected_count:
        raise ValueError(f"Incomplete cached trace: {len(losses)}/{expected_count}")
    return losses
