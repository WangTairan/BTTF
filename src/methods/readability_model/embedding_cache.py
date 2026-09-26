from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Iterable, Sequence

import numpy as np

from .results import model_slug


SCHEMA_VERSION = 3


@dataclass(frozen=True)
class SourceReference:
    dataset: str
    task_id: str
    chunk_type: str
    text: str
    count: int = 1

    def __post_init__(self) -> None:
        # Java permits isolated UTF-16 surrogate code units in character
        # literals.  Python strings can represent them, but UTF-8, SQLite,
        # and model tokenizers cannot.  Preserve the code unit explicitly as
        # its Java-style escape instead of dropping or replacing it.
        object.__setattr__(self, "text", canonical_embedding_text(self.text))


def embedding_cache_path(root: Path, model_name: str) -> Path:
    return root / model_slug(model_name) / "embeddings.sqlite"


def canonical_embedding_text(text: str) -> str:
    if not any(0xD800 <= ord(character) <= 0xDFFF for character in text):
        return text
    return "".join(
        f"\\u{ord(character):04X}"
        if 0xD800 <= ord(character) <= 0xDFFF
        else character
        for character in text
    )


def text_hash(text: str) -> str:
    return hashlib.sha256(canonical_embedding_text(text).encode("utf-8")).hexdigest()


class EmbeddingCache:
    def __init__(self, path: Path, *, model_name: str) -> None:
        self.path = path
        self.model_name = model_name
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "EmbeddingCache":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def existing_hashes(self, texts: Iterable[str]) -> set[str]:
        hashes = [text_hash(text) for text in texts]
        if not hashes:
            return set()
        existing: set[str] = set()
        for start in range(0, len(hashes), 900):
            batch = hashes[start:start + 900]
            placeholders = ",".join("?" for _ in batch)
            rows = self.connection.execute(
                f"SELECT text_hash FROM embeddings WHERE text_hash IN ({placeholders})",
                batch,
            )
            existing.update(row[0] for row in rows)
        return existing

    def missing_texts(self, texts: Sequence[str]) -> list[str]:
        existing = self.existing_hashes(texts)
        return [text for text in texts if text_hash(text) not in existing]

    def upsert_embeddings(self, texts: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        now = time()
        rows = []
        for text, vector in zip(texts, vectors):
            array = np.asarray(vector, dtype=np.float32)
            rows.append(
                (
                    text_hash(text),
                    self.model_name,
                    text,
                    int(array.shape[0]),
                    "float32",
                    array.tobytes(),
                    now,
                )
            )
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO embeddings
                (text_hash, model_name, text, dim, dtype, vector, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def upsert_sources(self, references: Sequence[SourceReference]) -> None:
        rows = self._source_rows(references)
        with self.connection:
            self._upsert_source_rows(rows)

    def replace_sources_for_datasets(
        self,
        datasets: Sequence[str],
        references: Sequence[SourceReference],
    ) -> None:
        """Atomically replace source references for selected datasets.

        Source rows are fully validated before the transaction starts.  A
        malformed reference therefore cannot leave a dataset with its old
        references deleted and no replacements inserted.
        """
        rows = self._source_rows(references)
        with self.connection:
            self._delete_sources_for_datasets(datasets)
            self._upsert_source_rows(rows)

    def delete_sources_for_datasets(self, datasets: Sequence[str]) -> None:
        if not datasets:
            return
        with self.connection:
            self._delete_sources_for_datasets(datasets)

    def _delete_sources_for_datasets(self, datasets: Sequence[str]) -> None:
        for start in range(0, len(datasets), 900):
            batch = list(datasets[start:start + 900])
            placeholders = ",".join("?" for _ in batch)
            self.connection.execute(
                f"DELETE FROM sources WHERE dataset IN ({placeholders})",
                batch,
            )

    @staticmethod
    def _source_rows(references: Sequence[SourceReference]) -> list[tuple[str, str, str, str, int]]:
        grouped: Counter[tuple[str, str, str, str]] = Counter()
        for ref in references:
            text = canonical_embedding_text(ref.text)
            grouped[(ref.dataset, ref.task_id, ref.chunk_type, text)] += ref.count
        return [
            (dataset, task_id, chunk_type, text_hash(text), int(count))
            for (dataset, task_id, chunk_type, text), count in grouped.items()
        ]

    def _upsert_source_rows(self, rows: Sequence[tuple[str, str, str, str, int]]) -> None:
        self.connection.executemany(
            """
            INSERT INTO sources (dataset, task_id, chunk_type, text_hash, count)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(dataset, task_id, chunk_type, text_hash)
            DO UPDATE SET count = excluded.count
            """,
            rows,
        )

    def delete_sources_for_datasets_and_chunk_types(
        self,
        datasets: Sequence[str],
        chunk_types: Sequence[str],
    ) -> None:
        if not datasets or not chunk_types:
            return
        for dataset in datasets:
            for start in range(0, len(chunk_types), 900):
                batch = list(chunk_types[start:start + 900])
                placeholders = ",".join("?" for _ in batch)
                self.connection.execute(
                    f"DELETE FROM sources WHERE dataset = ? AND chunk_type IN ({placeholders})",
                    [dataset, *batch],
                )
        self.connection.commit()

    def counts(self) -> dict[str, int]:
        embedding_count = self.connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        source_count = self.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        dataset_count = self.connection.execute("SELECT COUNT(DISTINCT dataset) FROM sources").fetchone()[0]
        return {
            "embeddings": int(embedding_count),
            "sources": int(source_count),
            "datasets": int(dataset_count),
        }

    def task_vectors(
        self,
        dataset: str,
        task_id: str,
        *,
        exclude_chunk_types: Sequence[str] = (),
    ) -> list[tuple[str, str, int, np.ndarray]]:
        excluded = tuple(exclude_chunk_types)
        excluded_clause = ""
        params: list[str] = [dataset, task_id]
        if excluded:
            placeholders = ",".join("?" for _ in excluded)
            excluded_clause = f"AND s.chunk_type NOT IN ({placeholders})"
            params.extend(excluded)
        rows = self.connection.execute(
            f"""
            SELECT s.chunk_type, e.text, s.count, e.dim, e.dtype, e.vector
            FROM sources AS s
            JOIN embeddings AS e ON e.text_hash = s.text_hash
            WHERE s.dataset = ? AND s.task_id = ?
            {excluded_clause}
            ORDER BY s.chunk_type, e.text
            """,
            params,
        )
        vectors: list[tuple[str, str, int, np.ndarray]] = []
        for chunk_type, text, count, dim, dtype, blob in rows:
            array = np.frombuffer(blob, dtype=np.dtype(dtype)).copy()
            vectors.append((str(chunk_type), str(text), int(count), array.reshape(int(dim))))
        return vectors

    def task_source_counts(
        self,
        dataset: str,
        task_id: str,
        *,
        exclude_chunk_types: Sequence[str] = (),
    ) -> tuple[int, int]:
        excluded = tuple(exclude_chunk_types)
        excluded_clause = ""
        params: list[str] = [dataset, task_id]
        if excluded:
            placeholders = ",".join("?" for _ in excluded)
            excluded_clause = f"AND chunk_type NOT IN ({placeholders})"
            params.extend(excluded)
        total = self.connection.execute(
            f"""
            SELECT COALESCE(SUM(count), 0)
            FROM sources
            WHERE dataset = ? AND task_id = ?
            {excluded_clause}
            """,
            params,
        ).fetchone()[0]
        available_params: list[str] = [dataset, task_id]
        available_excluded_clause = ""
        if excluded:
            placeholders = ",".join("?" for _ in excluded)
            available_excluded_clause = f"AND s.chunk_type NOT IN ({placeholders})"
            available_params.extend(excluded)
        available = self.connection.execute(
            f"""
            SELECT COALESCE(SUM(s.count), 0)
            FROM sources AS s
            JOIN embeddings AS e ON e.text_hash = s.text_hash
            WHERE s.dataset = ? AND s.task_id = ?
            {available_excluded_clause}
            """,
            available_params,
        ).fetchone()[0]
        return int(total), int(available)

    def task_single_vector(self, dataset: str, task_id: str, chunk_type: str) -> np.ndarray | None:
        vectors = self.task_vectors(dataset, task_id)
        for row_chunk_type, _, _, vector in vectors:
            if row_chunk_type == chunk_type:
                return vector
        return None

    def task_vectors_for_chunk_type(self, dataset: str, task_id: str, chunk_type: str) -> list[tuple[str, np.ndarray]]:
        rows = self.connection.execute(
            """
            SELECT e.text, e.dim, e.dtype, e.vector
            FROM sources AS s
            JOIN embeddings AS e ON e.text_hash = s.text_hash
            WHERE s.dataset = ? AND s.task_id = ? AND s.chunk_type = ?
            ORDER BY e.text
            """,
            (dataset, task_id, chunk_type),
        )
        vectors: list[tuple[str, np.ndarray]] = []
        for text, dim, dtype, blob in rows:
            array = np.frombuffer(blob, dtype=np.dtype(dtype)).copy()
            vectors.append((str(text), array.reshape(int(dim))))
        return vectors

    def vectors_for_texts(self, texts: Sequence[str]) -> dict[str, np.ndarray]:
        if not texts:
            return {}
        hashes = [text_hash(text) for text in texts]
        by_hash = dict(zip(hashes, texts))
        vectors: dict[str, np.ndarray] = {}
        for start in range(0, len(hashes), 900):
            batch = hashes[start:start + 900]
            placeholders = ",".join("?" for _ in batch)
            rows = self.connection.execute(
                f"""
                SELECT text_hash, dim, dtype, vector
                FROM embeddings
                WHERE text_hash IN ({placeholders})
                """,
                batch,
            )
            for row_hash, dim, dtype, blob in rows:
                array = np.frombuffer(blob, dtype=np.dtype(dtype)).copy()
                vectors[by_hash[str(row_hash)]] = array.reshape(int(dim))
        return vectors

    def _init_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS embeddings (
                text_hash TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                text TEXT NOT NULL,
                dim INTEGER NOT NULL,
                dtype TEXT NOT NULL,
                vector BLOB NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_embeddings_text
                ON embeddings(text);

            CREATE TABLE IF NOT EXISTS sources (
                dataset TEXT NOT NULL,
                task_id TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                text_hash TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (dataset, task_id, chunk_type, text_hash),
                FOREIGN KEY (text_hash) REFERENCES embeddings(text_hash)
            );

            CREATE INDEX IF NOT EXISTS idx_sources_text_hash
                ON sources(text_hash);

            CREATE INDEX IF NOT EXISTS idx_sources_dataset
                ON sources(dataset);
            """
        )
        self.connection.executemany(
            """
            INSERT OR REPLACE INTO metadata (key, value)
            VALUES (?, ?)
            """,
            (
                ("schema_version", str(SCHEMA_VERSION)),
                ("model_name", self.model_name),
            ),
        )
        self.connection.commit()
