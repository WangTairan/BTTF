"""Content-addressed token traces and versioned feature summaries.

A transaction commits after each inference window. Changing aggregation rules
does not discard token traces; changing a model or scoring protocol creates a
new trace namespace. Dataset labels and task IDs are not inference-cache keys.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import zlib
from collections.abc import Sequence
from pathlib import Path
from time import time

from .types import TokenLoss


def fingerprint(payload: dict) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _pack(payload) -> bytes:
    return zlib.compress(
        json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    )


def _unpack(payload: bytes):
    return json.loads(zlib.decompress(payload))


class LLMTraceCache:
    """SQLite store with independently reusable tokenization, traces and summaries."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tokenizations (
                source_sha256 TEXT NOT NULL, trace_sha256 TEXT NOT NULL,
                token_count INTEGER NOT NULL, payload BLOB NOT NULL,
                PRIMARY KEY (source_sha256, trace_sha256)
            );
            CREATE TABLE IF NOT EXISTS trace_windows (
                source_sha256 TEXT NOT NULL, trace_sha256 TEXT NOT NULL,
                kind TEXT NOT NULL, token_start INTEGER NOT NULL,
                token_stop INTEGER NOT NULL, payload BLOB NOT NULL,
                PRIMARY KEY (source_sha256, trace_sha256, kind, token_start)
            );
            CREATE TABLE IF NOT EXISTS comment_effects (
                source_sha256 TEXT NOT NULL, trace_sha256 TEXT NOT NULL,
                target_key TEXT NOT NULL, payload BLOB NOT NULL,
                PRIMARY KEY (source_sha256, trace_sha256, target_key)
            );
            CREATE TABLE IF NOT EXISTS feature_rows (
                source_sha256 TEXT NOT NULL, feature_sha256 TEXT NOT NULL,
                payload BLOB NOT NULL, updated_at REAL NOT NULL,
                PRIMARY KEY (source_sha256, feature_sha256)
            );
            """
        )
        self.connection.commit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.connection.close()

    def get_tokenization(self, source_sha256: str, trace_sha256: str) -> dict | None:
        row = self.connection.execute(
            "SELECT payload FROM tokenizations WHERE source_sha256=? AND trace_sha256=?",
            (source_sha256, trace_sha256),
        ).fetchone()
        return _unpack(row[0]) if row else None

    def put_tokenization(self, source_sha256: str, trace_sha256: str, payload: dict):
        if len(payload["input_ids"]) != len(payload["offsets"]):
            raise ValueError("Token IDs and offsets have different lengths.")
        existing = self.get_tokenization(source_sha256, trace_sha256)
        if existing is not None and existing != payload:
            raise ValueError("Tokenization changed within a pinned trace namespace.")
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO tokenizations VALUES (?, ?, ?, ?)",
                (
                    source_sha256,
                    trace_sha256,
                    len(payload["input_ids"]),
                    _pack(payload),
                ),
            )

    def get_trace(
        self, source_sha256: str, trace_sha256: str, kind: str
    ) -> list[TokenLoss]:
        windows = self.connection.execute(
            "SELECT token_start, token_stop, payload FROM trace_windows "
            "WHERE source_sha256=? AND trace_sha256=? AND kind=? ORDER BY token_start",
            (source_sha256, trace_sha256, kind),
        )
        result = []
        for start, stop, payload in windows:
            rows = [TokenLoss(*values) for values in _unpack(payload)]
            if start != len(result) or stop != start + len(rows):
                raise ValueError("Cached token trace has a gap or overlapping windows.")
            if [row.token_index for row in rows] != list(range(start, stop)):
                raise ValueError(
                    "Cached token indices are inconsistent with their window."
                )
            result.extend(rows)
        return result

    def append_window(
        self,
        source_sha256: str,
        trace_sha256: str,
        kind: str,
        next_token_index: int,
        losses: Sequence[TokenLoss],
    ):
        if not losses:
            raise ValueError("Cannot checkpoint an empty trace window.")
        start = losses[0].token_index
        if [row.token_index for row in losses] != list(range(start, next_token_index)):
            raise ValueError(
                "A checkpoint must contain exactly one contiguous token window."
            )
        if any(not math.isfinite(row.nll) or row.nll < 0 for row in losses):
            raise ValueError("A checkpoint contains an invalid token loss.")
        previous_row = self.connection.execute(
            "SELECT token_stop FROM trace_windows "
            "WHERE source_sha256=? AND trace_sha256=? AND kind=? "
            "ORDER BY token_start DESC LIMIT 1",
            (source_sha256, trace_sha256, kind),
        ).fetchone()
        previous = previous_row[0] if previous_row else 0
        if previous != start:
            raise ValueError("Trace checkpoint does not continue the stored prefix.")
        values = [[row.token_index, row.start, row.end, row.nll] for row in losses]
        with self.connection:
            self.connection.execute(
                "INSERT INTO trace_windows VALUES (?, ?, ?, ?, ?, ?)",
                (
                    source_sha256,
                    trace_sha256,
                    kind,
                    start,
                    next_token_index,
                    _pack(values),
                ),
            )

    def get_comment_effects(
        self, source_sha256: str, trace_sha256: str
    ) -> dict[str, dict]:
        return {
            key: _unpack(payload)
            for key, payload in self.connection.execute(
                "SELECT target_key, payload FROM comment_effects "
                "WHERE source_sha256=? AND trace_sha256=?",
                (source_sha256, trace_sha256),
            )
        }

    def put_comment_effect(
        self, source_sha256: str, trace_sha256: str, key: str, payload: dict
    ):
        with self.connection:
            self.connection.execute(
                "INSERT INTO comment_effects VALUES (?, ?, ?, ?) "
                "ON CONFLICT(source_sha256, trace_sha256, target_key) "
                "DO UPDATE SET payload=excluded.payload",
                (source_sha256, trace_sha256, key, _pack(payload)),
            )

    def get_features(self, source_sha256: str, feature_sha256: str) -> dict | None:
        row = self.connection.execute(
            "SELECT payload FROM feature_rows WHERE source_sha256=? AND feature_sha256=?",
            (source_sha256, feature_sha256),
        ).fetchone()
        return _unpack(row[0]) if row else None

    def put_features(
        self, source_sha256: str, feature_sha256: str, features: dict, metadata: dict
    ):
        payload = {"features": features, "metadata": metadata}
        with self.connection:
            self.connection.execute(
                "INSERT INTO feature_rows VALUES (?, ?, ?, ?) "
                "ON CONFLICT(source_sha256, feature_sha256) "
                "DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (source_sha256, feature_sha256, _pack(payload), time()),
            )
