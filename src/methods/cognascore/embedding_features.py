from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans, OPTICS
from sklearn.metrics import pairwise_distances
from sklearn.metrics import silhouette_score

from .semantic_context import (
    WHOLE_CODE_CONTEXT_TYPE,
    semantic_context_feature_names,
    semantic_context_features,
)

OPTICS_XI = 0.05
AUTO_KMEANS_K_VALUES = (2, 3, 4, 6, 8, 12, 16)

SEMANTIC_CORE_CHUNK_TYPES = frozenset(("IDENTIFIER", "DECLARATION", "CALL", "LITERAL"))
STRUCTURAL_CORE_CHUNK_TYPES = frozenset(("CONTROL_FLOW", "ASSIGNMENT", "ARITHMETIC", "COMPARISON", "LOGICAL", "BITWISE"))

CHUNK_VIEW_RULES: tuple[tuple[str, str, frozenset[str] | None], ...] = (
    ("all", "All chunk types.", None),
    ("only_identifier", "Identifier chunks only.", frozenset(("IDENTIFIER",))),
    ("semantic_core", "Identifier, declaration, call, and literal chunks.", SEMANTIC_CORE_CHUNK_TYPES),
    ("structural_core", "Control-flow and operator-like chunks.", STRUCTURAL_CORE_CHUNK_TYPES),
)

VIEW_COVERAGE_SUFFIXES = (
    "coverage_ratio",
)

VIEW_FAMILY_SUFFIXES: dict[str, tuple[str, ...]] = {
    "embedding": (
        "mean_cosine_to_centroid",
        "pairwise_cosine_std",
        "effective_rank",
        "first_pc_explained_variance",
    ),
    "optics": (
        "noise_ratio",
        "cluster_size_cv",
        "cluster_diameter_max",
        "reachability_mean",
        "cluster_type_entropy_mean",
    ),
    "hdbscan": (
        "noise_ratio",
        "largest_cluster_ratio",
        "cluster_size_cv",
        "cluster_diameter_max",
        "cluster_type_entropy_mean",
    ),
    "auto_kmeans": (
        "selected_k",
        "silhouette",
        "largest_cluster_ratio",
        "cluster_size_cv",
        "cluster_diameter_max",
    ),
    "auto_agglo": (
        "cluster_count",
        "largest_cluster_ratio",
        "cluster_size_cv",
        "cluster_diameter_max",
        "cluster_type_entropy_mean",
    ),
}


IDENTITY_COLUMNS = ("dataset", "task_id", "readability_score")


@dataclass(frozen=True)
class EmbeddingFeatureDefinition:
    name: str
    group: str
    description: str


def embedding_feature_names() -> list[str]:
    names = [
        "embedding_coverage_ratio",
        "embedding_mean_cosine_to_centroid",
        "embedding_pairwise_cosine_std",
        "embedding_effective_rank",
        "embedding_first_pc_explained_variance",
    ]
    names.extend(semantic_context_feature_names())
    names.extend(view_clustering_feature_names())
    return names


def view_clustering_feature_names() -> list[str]:
    names: list[str] = []
    for view_name, _, _ in CHUNK_VIEW_RULES:
        for suffix in VIEW_COVERAGE_SUFFIXES:
            names.append(f"{view_name}__{suffix}")
        for family, suffixes in VIEW_FAMILY_SUFFIXES.items():
            for suffix in suffixes:
                names.append(f"{view_name}__{family}_{suffix}")
    return names


def _feature_group(name: str) -> str:
    if "__" not in name:
        return "embedding_coverage" if name.endswith("coverage_ratio") else "embedding_geometry"
    _, feature = name.split("__", 1)
    if feature == "coverage_ratio":
        return "chunk_view_coverage"
    family = feature.split("_", 1)[0]
    if feature.startswith("auto_kmeans_"):
        family = "auto_kmeans"
    elif feature.startswith("auto_agglo_"):
        family = "auto_agglo"
    return f"chunk_view_{family}"


def _feature_description(name: str) -> str:
    if "__" not in name:
        return f"Global embedding feature: {name}."
    view, feature = name.split("__", 1)
    return f"{feature} computed over the {view} chunk view."


def embedding_feature_definitions() -> list[EmbeddingFeatureDefinition]:
    definitions = [
        EmbeddingFeatureDefinition("embedding_coverage_ratio", "embedding_coverage", "Available embedded chunk count divided by total chunk source count."),
        EmbeddingFeatureDefinition("embedding_mean_cosine_to_centroid", "embedding_geometry", "Weighted mean cosine distance to the task centroid."),
        EmbeddingFeatureDefinition("embedding_pairwise_cosine_std", "embedding_geometry", "Weighted standard deviation of pairwise cosine distance."),
        EmbeddingFeatureDefinition("embedding_effective_rank", "embedding_geometry", "Entropy-based effective rank of the weighted embedding covariance."),
        EmbeddingFeatureDefinition("embedding_first_pc_explained_variance", "embedding_geometry", "Variance ratio explained by the first principal component."),
        EmbeddingFeatureDefinition("short_identifier_candidate_ratio", "semantic_context_gate", "Mathematical-style short identifiers divided by identifier chunks."),
        EmbeddingFeatureDefinition("short_identifier_math_gate_delta", "semantic_context_gate", "Whole-code math-context similarity minus the stronger non-math/business similarity."),
        EmbeddingFeatureDefinition("short_identifier_non_math_risk", "semantic_context_gate", "short_identifier_candidate_ratio multiplied by max(0, -short_identifier_math_gate_delta)."),
    ]
    defined = {definition.name for definition in definitions}
    for name in embedding_feature_names():
        if name not in defined:
            definitions.append(EmbeddingFeatureDefinition(name, _feature_group(name), _feature_description(name)))
    return definitions


def extract_embedding_feature_row(
    *,
    dataset: str,
    task_id: str,
    readability_score: float | None,
    total_source_count: int,
    vector_rows: Sequence[tuple[str, str, int, np.ndarray]],
    code_vector: np.ndarray | None = None,
    code_segment_vectors: list[tuple[str, np.ndarray]] | None = None,
    math_centroid: np.ndarray | None = None,
    business_centroid: np.ndarray | None = None,
    non_math_centroid: np.ndarray | None = None,
    max_vectors: int | None = 512,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "dataset": dataset,
        "task_id": task_id,
        "readability_score": readability_score,
    }
    row.update({name: 0.0 for name in embedding_feature_names()})
    chunk_vector_rows = [
        row_tuple for row_tuple in vector_rows
        if row_tuple[0] != WHOLE_CODE_CONTEXT_TYPE
    ]
    identifier_lexemes = [
        text for chunk_type, text, count, _ in chunk_vector_rows
        for _ in range(max(int(count), 0))
        if _normalize_chunk_type(chunk_type) == "IDENTIFIER"
    ]
    row.update(
        semantic_context_features(
            code_vector=code_vector,
            code_segment_vectors=code_segment_vectors,
            identifier_lexemes=identifier_lexemes,
            math_centroid=math_centroid,
            business_centroid=business_centroid,
            non_math_centroid=non_math_centroid,
        )
    )
    if not chunk_vector_rows:
        return row

    original_available_weight = float(sum(count for _, _, count, _ in chunk_vector_rows))
    if max_vectors is not None and len(chunk_vector_rows) > max_vectors:
        chunk_vector_rows = sorted(chunk_vector_rows, key=lambda item: (-item[2], item[0], item[1]))[:max_vectors]

    vectors = np.stack([vector for _, _, _, vector in chunk_vector_rows]).astype(np.float64)
    weights = np.asarray([count for _, _, count, _ in chunk_vector_rows], dtype=np.float64)
    total_weight = float(max(total_source_count, 1))
    normalized = _normalize_rows(vectors)

    row["embedding_coverage_ratio"] = original_available_weight / total_weight
    row.update(_geometry_features(normalized, weights))
    row.update(_view_clustering_features(chunk_vector_rows, total_source_count=total_source_count, max_vectors=max_vectors))
    return row


def write_embedding_feature_database(
    *,
    rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
    metadata: Mapping[str, Any],
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "features.csv"
    metadata_path = output_dir / "metadata.json"
    columns = list(IDENTITY_COLUMNS) + embedding_feature_names()
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, 0.0 if column not in IDENTITY_COLUMNS else "") for column in columns})
    metadata_payload = {
        **metadata,
        "row_count": len(rows),
        "columns": columns,
        "feature_definitions": [asdict(definition) for definition in embedding_feature_definitions()],
        "hyperparameters": {
            "view_clustering": {
                "chunk_views": {
                    name: {
                        "description": description,
                        "include_types": sorted(include) if include is not None else None,
                    }
                    for name, description, include in CHUNK_VIEW_RULES
                },
                "families": sorted(VIEW_FAMILY_SUFFIXES),
                "optics": {
                    "min_samples_rule": "max(2, round(log2(n_vectors)))",
                    "xi": OPTICS_XI,
                    "metric": "cosine",
                },
                "hdbscan": {
                    "min_cluster_size_rule": "max(2, round(log2(n_vectors)))",
                    "min_samples_rule": "min_cluster_size",
                    "metric": "precomputed cosine distance",
                    "dependency": "hdbscan",
                },
                "auto_kmeans": {
                    "candidate_k": AUTO_KMEANS_K_VALUES,
                    "selection_rule": "highest cosine silhouette among valid k values",
                },
                "auto_agglo": {
                    "threshold_rule": "median pairwise cosine distance",
                    "metric": "cosine",
                    "linkage": "average",
                },
            },
        },
    }
    metadata_path.write_text(json.dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, metadata_path


def _geometry_features(x: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    centroid = np.average(x, axis=0, weights=weights)
    centroid_norm = float(np.linalg.norm(centroid))
    centroid_unit = centroid / max(centroid_norm, 1e-12)
    distances = 1.0 - x @ centroid_unit
    pairwise_mean, pairwise_std = _weighted_pairwise_cosine_stats(x, weights)
    effective_rank, first_pc = _effective_rank_features(x, weights)
    return {
        "embedding_mean_cosine_to_centroid": _weighted_mean(distances, weights),
        "embedding_pairwise_cosine_std": pairwise_std,
        "embedding_effective_rank": effective_rank,
        "embedding_first_pc_explained_variance": first_pc,
    }


def _view_clustering_features(
    vector_rows: Sequence[tuple[str, str, int, np.ndarray]],
    *,
    total_source_count: int,
    max_vectors: int | None,
) -> dict[str, float]:
    features: dict[str, float] = {}
    type_rows = [
        (_normalize_chunk_type(chunk_type), text, count, vector)
        for chunk_type, text, count, vector in vector_rows
    ]
    for view_name, _, include_types in CHUNK_VIEW_RULES:
        selected_rows = [
            (chunk_type, text, count, vector)
            for chunk_type, text, count, vector in type_rows
            if _chunk_type_in_view(chunk_type, include_types=include_types)
        ]
        features.update(
            _single_view_clustering_features(
                view_name,
                selected_rows,
                total_source_count=total_source_count,
                max_vectors=max_vectors,
            )
        )
    return features


def _single_view_clustering_features(
    view_name: str,
    vector_rows: Sequence[tuple[str, str, int, np.ndarray]],
    *,
    total_source_count: int,
    max_vectors: int | None,
) -> dict[str, float]:
    features = _empty_view_features(view_name)
    source_count = float(sum(count for _, _, count, _ in vector_rows))
    features[f"{view_name}__coverage_ratio"] = source_count / max(float(total_source_count), 1.0)

    if max_vectors is not None and len(vector_rows) > max_vectors:
        vector_rows = sorted(vector_rows, key=lambda item: (-item[2], item[0], item[1]))[:max_vectors]
    if not vector_rows:
        return features

    x = _normalize_rows(np.stack([vector for _, _, _, vector in vector_rows]).astype(np.float64))
    weights = np.asarray([count for _, _, count, _ in vector_rows], dtype=np.float64)
    chunk_types = [chunk_type for chunk_type, _, _, _ in vector_rows]

    features.update(_rename_feature_prefix(_geometry_features(x, weights), "embedding", f"{view_name}__embedding"))
    features.update(_optics_view_features(view_name, x, weights, chunk_types))
    features.update(_hdbscan_view_features(view_name, x, weights, chunk_types))
    features.update(_auto_kmeans_view_features(view_name, x, weights, chunk_types))
    features.update(_auto_agglo_view_features(view_name, x, weights, chunk_types))
    return features


def _empty_view_features(view_name: str) -> dict[str, float]:
    return {
        f"{view_name}__{suffix}": 0.0
        for suffix in VIEW_COVERAGE_SUFFIXES
    } | {
        f"{view_name}__{family}_{suffix}": 0.0
        for family, suffixes in VIEW_FAMILY_SUFFIXES.items()
        for suffix in suffixes
    }


def _optics_view_features(view_name: str, x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = f"{view_name}__optics"
    values = {f"{prefix}_{suffix}": 0.0 for suffix in VIEW_FAMILY_SUFFIXES["optics"]}
    if len(x) < 2:
        return values
    min_samples = max(2, int(round(math.log2(max(len(x), 2)))))
    min_samples = min(min_samples, len(x))
    model = OPTICS(min_samples=min_samples, xi=OPTICS_XI, metric="cosine")
    labels = model.fit_predict(x)
    values[f"{prefix}_min_samples"] = float(min_samples)
    values[f"{prefix}_xi"] = OPTICS_XI
    values.update(_cluster_summary_features(prefix, x, labels, weights, chunk_types, noise_label=-1))
    reachability = np.asarray(getattr(model, "reachability_", []), dtype=float)
    finite_reachability = reachability[np.isfinite(reachability)]
    values[f"{prefix}_reachability_mean"] = float(np.mean(finite_reachability)) if finite_reachability.size else 0.0
    values[f"{prefix}_reachability_std"] = float(np.std(finite_reachability)) if finite_reachability.size else 0.0
    values[f"{prefix}_reachability_max"] = float(np.max(finite_reachability)) if finite_reachability.size else 0.0
    return _filter_family_features(prefix, values, "optics")


def _hdbscan_view_features(view_name: str, x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = f"{view_name}__hdbscan"
    values = {f"{prefix}_{suffix}": 0.0 for suffix in VIEW_FAMILY_SUFFIXES["hdbscan"]}
    if len(x) < 2:
        return values

    import hdbscan  # type: ignore

    min_cluster_size = max(2, int(round(math.log2(max(len(x), 2)))))
    min_cluster_size = min(min_cluster_size, len(x))
    distances = pairwise_distances(x, metric="cosine").astype(np.float64)
    model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_cluster_size,
        metric="precomputed",
    )
    labels = model.fit_predict(distances)
    values.update(_cluster_summary_features(prefix, x, labels, weights, chunk_types, noise_label=-1))
    return _filter_family_features(prefix, values, "hdbscan")


def _auto_kmeans_view_features(view_name: str, x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = f"{view_name}__auto_kmeans"
    values = {f"{prefix}_{suffix}": 0.0 for suffix in VIEW_FAMILY_SUFFIXES["auto_kmeans"]}
    total = float(np.sum(weights))
    distinct_vector_count = len(np.unique(x, axis=0)) if len(x) else 0
    best: tuple[float, int, np.ndarray, KMeans] | None = None
    for k in AUTO_KMEANS_K_VALUES:
        if len(x) <= k or distinct_vector_count < k or total <= 0.0:
            continue
        model = KMeans(n_clusters=k, n_init=10, random_state=0)
        labels = model.fit_predict(x, sample_weight=weights)
        score = _safe_silhouette(x, labels)
        if best is None or score > best[0]:
            best = (score, k, labels, model)
    if best is None:
        return values
    score, k, labels, model = best
    values[f"{prefix}_selected_k"] = float(k)
    values[f"{prefix}_silhouette"] = score
    values[f"{prefix}_inertia"] = float(model.inertia_)
    values[f"{prefix}_inertia_per_weight"] = float(model.inertia_ / max(total, 1e-12))
    values.update(_cluster_summary_features(prefix, x, labels, weights, chunk_types, noise_label=None))
    return _filter_family_features(prefix, values, "auto_kmeans")


def _auto_agglo_view_features(view_name: str, x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = f"{view_name}__auto_agglo"
    values = {f"{prefix}_{suffix}": 0.0 for suffix in VIEW_FAMILY_SUFFIXES["auto_agglo"]}
    if len(x) < 2:
        return values
    distances = pairwise_distances(x, metric="cosine")
    upper = distances[np.triu_indices(len(x), k=1)]
    positive = upper[upper > 0.0]
    threshold = float(np.median(positive)) if positive.size else 1e-12
    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=threshold,
        metric="cosine",
        linkage="average",
    ).fit_predict(x)
    values[f"{prefix}_threshold"] = threshold
    values.update(_cluster_summary_features(prefix, x, labels, weights, chunk_types, noise_label=None))
    return _filter_family_features(prefix, values, "auto_agglo")


def _cluster_summary_features(
    prefix: str,
    x: np.ndarray,
    labels: np.ndarray,
    weights: np.ndarray,
    chunk_types: Sequence[str],
    *,
    noise_label: int | None,
) -> dict[str, float]:
    values: dict[str, float] = {}
    values.update(_cluster_features_from_labels(prefix, labels, weights, noise_label=noise_label))
    values.update(_cluster_diameter_features(prefix, x, labels, weights, noise_label=noise_label))
    values.update(_cluster_type_features(prefix, labels, weights, chunk_types, noise_label=noise_label))
    values.update(_control_flow_cluster_features(prefix, x, labels, weights, chunk_types, noise_label=noise_label))
    return values


def _filter_family_features(prefix: str, values: Mapping[str, float], family: str) -> dict[str, float]:
    allowed = {f"{prefix}_{suffix}" for suffix in VIEW_FAMILY_SUFFIXES[family]}
    return {name: float(values.get(name, 0.0)) for name in sorted(allowed)}


def _rename_feature_prefix(features: Mapping[str, float], old_prefix: str, new_prefix: str) -> dict[str, float]:
    renamed: dict[str, float] = {}
    for key, value in features.items():
        if key.startswith(f"{old_prefix}_"):
            renamed[f"{new_prefix}_{key[len(old_prefix) + 1:]}"] = value
    return renamed


def _normalize_chunk_type(chunk_type: str) -> str:
    return str(chunk_type).strip().upper()


def _chunk_type_in_view(
    chunk_type: str,
    *,
    include_types: frozenset[str] | None,
) -> bool:
    if include_types is not None and chunk_type not in include_types:
        return False
    return True


def _cluster_features_from_labels(
    prefix: str,
    labels: np.ndarray,
    weights: np.ndarray,
    *,
    noise_label: int | None,
) -> dict[str, float]:
    total = float(np.sum(weights))
    noise_weight = 0.0
    cluster_weights: list[float] = []
    for label in sorted(set(int(label) for label in labels)):
        weight = float(np.sum(weights[labels == label]))
        if noise_label is not None and label == noise_label:
            noise_weight = weight
        else:
            cluster_weights.append(weight)
    return _cluster_feature_values(prefix, cluster_weights, noise_weight, total, include_noise=noise_label is not None)


def _cluster_feature_values(
    prefix: str,
    cluster_weights: Sequence[float],
    noise_weight: float,
    total: float,
    *,
    include_noise: bool = True,
) -> dict[str, float]:
    values = {
        f"{prefix}_cluster_count": float(len(cluster_weights)),
        f"{prefix}_largest_cluster_ratio": max(cluster_weights, default=0.0) / max(total, 1.0),
        f"{prefix}_mean_cluster_size": float(np.mean(cluster_weights)) if cluster_weights else 0.0,
        f"{prefix}_cluster_size_cv": _coefficient_of_variation(cluster_weights),
    }
    if include_noise:
        values[f"{prefix}_noise_ratio"] = noise_weight / max(total, 1.0)
    return values


def _cluster_diameter_features(
    prefix: str,
    x: np.ndarray,
    labels: np.ndarray,
    weights: np.ndarray,
    *,
    noise_label: int | None,
) -> dict[str, float]:
    diameters: list[float] = []
    cluster_weights: list[float] = []
    for label in sorted(set(int(label) for label in labels)):
        if noise_label is not None and label == noise_label:
            continue
        mask = labels == label
        cluster_weights.append(float(np.sum(weights[mask])))
        diameters.append(_cluster_diameter(x[mask]))
    if not diameters:
        return {
            f"{prefix}_cluster_diameter_mean": 0.0,
            f"{prefix}_cluster_diameter_max": 0.0,
        }
    return {
        f"{prefix}_cluster_diameter_mean": _weighted_mean(np.asarray(diameters), np.asarray(cluster_weights)),
        f"{prefix}_cluster_diameter_max": float(max(diameters)),
    }


def _cluster_type_features(
    prefix: str,
    labels: np.ndarray,
    weights: np.ndarray,
    chunk_types: Sequence[str],
    *,
    noise_label: int | None,
) -> dict[str, float]:
    purities: list[float] = []
    entropies: list[float] = []
    cluster_weights: list[float] = []
    mixed_count = 0
    type_array = np.asarray([str(chunk_type).lower() for chunk_type in chunk_types], dtype=object)
    for label in sorted(set(int(label) for label in labels)):
        if noise_label is not None and label == noise_label:
            continue
        mask = labels == label
        cluster_weight = float(np.sum(weights[mask]))
        if cluster_weight <= 0.0:
            continue
        type_weights: dict[str, float] = {}
        for chunk_type, weight in zip(type_array[mask], weights[mask]):
            type_weights[chunk_type] = type_weights.get(chunk_type, 0.0) + float(weight)
        probabilities = np.asarray(list(type_weights.values()), dtype=float) / cluster_weight
        purities.append(float(np.max(probabilities)))
        entropies.append(_normalized_entropy(probabilities))
        cluster_weights.append(cluster_weight)
        if len(type_weights) > 1:
            mixed_count += 1
    if not cluster_weights:
        return {
            f"{prefix}_cluster_type_purity_mean": 0.0,
            f"{prefix}_cluster_type_entropy_mean": 0.0,
            f"{prefix}_mixed_cluster_ratio": 0.0,
        }
    return {
        f"{prefix}_cluster_type_purity_mean": _weighted_mean(np.asarray(purities), np.asarray(cluster_weights)),
        f"{prefix}_cluster_type_entropy_mean": _weighted_mean(np.asarray(entropies), np.asarray(cluster_weights)),
        f"{prefix}_mixed_cluster_ratio": mixed_count / max(len(cluster_weights), 1),
    }


def _control_flow_cluster_features(
    prefix: str,
    x: np.ndarray,
    labels: np.ndarray,
    weights: np.ndarray,
    chunk_types: Sequence[str],
    *,
    noise_label: int | None,
) -> dict[str, float]:
    type_array = np.asarray([str(chunk_type).upper() for chunk_type in chunk_types], dtype=object)
    control_mask = type_array == "CONTROL_FLOW"
    total_control_weight = float(np.sum(weights[control_mask]))
    if total_control_weight <= 0.0:
        return {
            f"{prefix}_control_flow_cluster_count": 0.0,
            f"{prefix}_control_flow_noise_ratio": 0.0,
            f"{prefix}_control_flow_cluster_diameter_mean": 0.0,
            f"{prefix}_control_flow_cluster_diameter_max": 0.0,
        }
    noise_weight = float(np.sum(weights[control_mask & (labels == noise_label)])) if noise_label is not None else 0.0
    diameters: list[float] = []
    control_weights: list[float] = []
    for label in sorted(set(int(label) for label in labels[control_mask])):
        if noise_label is not None and label == noise_label:
            continue
        cluster_mask = labels == label
        cluster_control_weight = float(np.sum(weights[cluster_mask & control_mask]))
        if cluster_control_weight <= 0.0:
            continue
        diameters.append(_cluster_diameter(x[cluster_mask]))
        control_weights.append(cluster_control_weight)
    return {
        f"{prefix}_control_flow_cluster_count": float(len(control_weights)),
        f"{prefix}_control_flow_noise_ratio": noise_weight / total_control_weight,
        f"{prefix}_control_flow_cluster_diameter_mean": (
            _weighted_mean(np.asarray(diameters), np.asarray(control_weights)) if diameters else 0.0
        ),
        f"{prefix}_control_flow_cluster_diameter_max": float(max(diameters)) if diameters else 0.0,
    }


def _cluster_diameter(x: np.ndarray) -> float:
    if len(x) < 2:
        return 0.0
    distances = pairwise_distances(x, metric="cosine")
    return float(np.max(distances))


def _weighted_pairwise_cosine_stats(x: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    if len(x) < 2:
        return 0.0, 0.0
    sims = x @ x.T
    distances = 1.0 - sims
    pair_weights = np.outer(weights, weights)
    mask = ~np.eye(len(x), dtype=bool)
    d = distances[mask]
    w = pair_weights[mask]
    avg = _weighted_mean(d, w)
    return avg, _weighted_std(d, w, mean_value=avg)


def _effective_rank_features(x: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    if len(x) < 2:
        return 0.0, 0.0
    centered = x - np.average(x, axis=0, weights=weights)
    weighted = centered * np.sqrt(weights[:, None] / max(float(np.sum(weights)), 1e-12))
    singular_values = np.linalg.svd(weighted, compute_uv=False)
    variances = singular_values ** 2
    total = float(np.sum(variances))
    if total <= 0.0:
        return 0.0, 0.0
    probabilities = variances / total
    entropy = -float(np.sum(probabilities * np.log(np.maximum(probabilities, 1e-12))))
    return float(math.exp(entropy)), float(probabilities[0])


def _cluster_weights(labels: np.ndarray, weights: np.ndarray) -> list[float]:
    return [float(np.sum(weights[labels == label])) for label in sorted(set(int(label) for label in labels))]


def _safe_silhouette(x: np.ndarray, labels: np.ndarray) -> float:
    if len(set(int(label) for label in labels)) < 2 or len(set(int(label) for label in labels)) >= len(x):
        return 0.0
    try:
        return float(silhouette_score(x, labels, metric="cosine"))
    except ValueError:
        return 0.0


def _normalize_rows(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(norms, 1e-12)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    total = float(np.sum(weights))
    if total <= 0.0:
        return 0.0
    return float(np.sum(values * weights) / total)


def _weighted_std(values: np.ndarray, weights: np.ndarray, *, mean_value: float | None = None) -> float:
    total = float(np.sum(weights))
    if total <= 0.0:
        return 0.0
    avg = _weighted_mean(values, weights) if mean_value is None else mean_value
    return float(np.sqrt(np.sum(weights * (values - avg) ** 2) / total))


def _coefficient_of_variation(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    array = np.asarray(values, dtype=float)
    avg = float(np.mean(array))
    if avg == 0.0:
        return 0.0
    return float(np.std(array) / avg)


def _normalized_entropy(probabilities: np.ndarray) -> float:
    probabilities = probabilities[probabilities > 0.0]
    if len(probabilities) <= 1:
        return 0.0
    entropy = -float(np.sum(probabilities * np.log(probabilities)))
    return entropy / math.log(len(probabilities))


def _slug_float(value: float) -> str:
    return f"{value:g}".replace(".", "_")
