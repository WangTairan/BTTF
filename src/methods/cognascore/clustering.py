from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddedLexeme:
    line: int
    type: str
    lexeme: str
    embedding: list[float]


class DBSCAN:
    def __init__(self, eps: float, min_pts: int) -> None:
        self.eps = eps
        self.min_pts = min_pts

    def fit(self, records: list[EmbeddedLexeme]) -> list[int]:
        labels: list[int | None] = [None] * len(records)
        cluster_id = 0

        for idx in range(len(records)):
            if labels[idx] is not None:
                continue

            neighbors = self._region_query(idx, records)
            if len(neighbors) < self.min_pts:
                labels[idx] = -1
                continue

            self._expand_cluster(idx, neighbors, cluster_id, labels, records)
            cluster_id += 1

        return [label if label is not None else -1 for label in labels]

    def _expand_cluster(
        self,
        idx: int,
        neighbors: list[int],
        cluster_id: int,
        labels: list[int | None],
        records: list[EmbeddedLexeme],
    ) -> None:
        labels[idx] = cluster_id
        queue = list(neighbors)

        while queue:
            current = queue.pop(0)

            if labels[current] is not None and labels[current] != -1:
                continue

            labels[current] = cluster_id
            current_neighbors = self._region_query(current, records)
            if len(current_neighbors) >= self.min_pts:
                queue.extend(current_neighbors)

    def _region_query(self, idx: int, records: list[EmbeddedLexeme]) -> list[int]:
        return [
            other_idx
            for other_idx in range(len(records))
            if cosine_distance(records[idx].embedding, records[other_idx].embedding) <= self.eps
        ]


def cosine_distance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same length.")

    dot = 0.0
    norm_left = 0.0
    norm_right = 0.0
    for a, b in zip(left, right):
        dot += a * b
        norm_left += a * a
        norm_right += b * b

    if norm_left == 0.0 or norm_right == 0.0:
        return 1.0
    return 1.0 - dot / ((norm_left ** 0.5) * (norm_right ** 0.5))


def group_by_label(records: list[EmbeddedLexeme], labels: list[int]) -> dict[int, list[EmbeddedLexeme]]:
    groups: dict[int, list[EmbeddedLexeme]] = {}
    for record, label in zip(records, labels):
        groups.setdefault(label, []).append(record)
    return groups


def cluster_diameter(records: list[EmbeddedLexeme]) -> float:
    if len(records) <= 1:
        return 0.0

    max_distance = 0.0
    for i, left in enumerate(records):
        for right in records[i + 1:]:
            max_distance = max(max_distance, cosine_distance(left.embedding, right.embedding))
    return max_distance


def cluster_diameters(groups: dict[int, list[EmbeddedLexeme]]) -> dict[int, float]:
    return {
        label: cluster_diameter(records)
        for label, records in groups.items()
        if label >= 0
    }


def mean_cluster_diameter(diameters: dict[int, float]) -> float:
    if not diameters:
        return 0.0
    return sum(diameters.values()) / len(diameters)
