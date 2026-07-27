from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans, OPTICS
from sklearn.metrics import pairwise_distances
from sklearn.metrics import silhouette_score


KMEANS_K_VALUES = (2, 4, 8, 16)
AUTO_DBSCAN_K_DISTANCE_QUANTILE = 0.75
OPTICS_XI = 0.05
AUTO_GRAPH_SIMILARITY_QUANTILE = 0.75
AUTO_KMEANS_K_VALUES = (2, 3, 4, 6, 8, 12, 16)

OPERATOR_CHUNK_TYPES = frozenset(("ASSIGNMENT", "ARITHMETIC", "COMPARISON", "LOGICAL", "BITWISE"))
SYNTAX_CHUNK_TYPES = frozenset(("CONTROL_FLOW", "ASSIGNMENT", "ARITHMETIC", "COMPARISON", "LOGICAL", "BITWISE", "IMPORT"))
SEMANTIC_CORE_CHUNK_TYPES = frozenset(("IDENTIFIER", "DECLARATION", "CALL", "LITERAL"))
STRUCTURAL_CORE_CHUNK_TYPES = frozenset(("CONTROL_FLOW", "ASSIGNMENT", "ARITHMETIC", "COMPARISON", "LOGICAL", "BITWISE"))
LOGIC_CORE_CHUNK_TYPES = frozenset(("CONTROL_FLOW", "COMPARISON", "LOGICAL"))
DATA_CORE_CHUNK_TYPES = frozenset(("IDENTIFIER", "DECLARATION", "LITERAL", "ASSIGNMENT"))
API_CORE_CHUNK_TYPES = frozenset(("CALL", "IDENTIFIER"))
NONSEMANTIC_NOISE_CHUNK_TYPES = frozenset(("JUNK", "REGEX", "COMMENT"))

CHUNK_VIEW_RULES: tuple[tuple[str, str, frozenset[str] | None, frozenset[str] | None], ...] = (
    ("all", "All chunk types.", None, None),
    ("no_junk", "All chunk types except extraction junk.", None, frozenset(("JUNK",))),
    ("no_control_flow", "All chunk types except control-flow chunks.", None, frozenset(("CONTROL_FLOW",))),
    ("no_identifier", "All chunk types except identifiers.", None, frozenset(("IDENTIFIER",))),
    ("no_literal", "All chunk types except literals.", None, frozenset(("LITERAL",))),
    ("no_call", "All chunk types except calls.", None, frozenset(("CALL",))),
    ("no_operator", "All chunk types except operator-like chunks.", None, OPERATOR_CHUNK_TYPES),
    ("no_syntax", "All chunk types except syntax/control/operator chunks.", None, SYNTAX_CHUNK_TYPES),
    ("only_identifier", "Identifier chunks only.", frozenset(("IDENTIFIER",)), None),
    ("only_call", "Call chunks only.", frozenset(("CALL",)), None),
    ("only_control_flow", "Control-flow chunks only.", frozenset(("CONTROL_FLOW",)), None),
    ("only_operator", "Operator-like chunks only.", OPERATOR_CHUNK_TYPES, None),
    ("only_literal", "Literal chunks only.", frozenset(("LITERAL",)), None),
    ("only_declaration", "Declaration chunks only.", frozenset(("DECLARATION",)), None),
    ("semantic_core", "Identifier, declaration, call, and literal chunks.", SEMANTIC_CORE_CHUNK_TYPES, None),
    ("structural_core", "Control-flow and operator-like chunks.", STRUCTURAL_CORE_CHUNK_TYPES, None),
    ("logic_core", "Control-flow, comparison, and logical chunks.", LOGIC_CORE_CHUNK_TYPES, None),
    ("data_core", "Identifier, declaration, literal, and assignment chunks.", DATA_CORE_CHUNK_TYPES, None),
    ("api_core", "Call and identifier chunks.", API_CORE_CHUNK_TYPES, None),
    ("nonsemantic_noise", "Junk, regex, and comment chunks.", NONSEMANTIC_NOISE_CHUNK_TYPES, None),
)

VIEW_COVERAGE_SUFFIXES = (
    "source_count",
    "unique_text_count",
    "coverage_ratio",
    "algorithm_unique_text_count",
)

VIEW_FAMILY_SUFFIXES: dict[str, tuple[str, ...]] = {
    "embedding": (
        "centroid_norm",
        "mean_cosine_to_centroid",
        "std_cosine_to_centroid",
        "max_cosine_to_centroid",
        "pairwise_cosine_mean",
        "pairwise_cosine_std",
        "effective_rank",
        "first_pc_explained_variance",
    ),
    "auto_dbscan": (
        "min_samples",
        "eps",
        "cluster_count",
        "noise_ratio",
        "largest_cluster_ratio",
        "mean_cluster_size",
        "cluster_size_cv",
        "cluster_diameter_mean",
        "cluster_diameter_max",
        "cluster_type_purity_mean",
        "cluster_type_entropy_mean",
        "mixed_cluster_ratio",
        "control_flow_cluster_count",
        "control_flow_noise_ratio",
        "control_flow_cluster_diameter_mean",
        "control_flow_cluster_diameter_max",
    ),
    "hdbscan": (
        "min_cluster_size",
        "min_samples",
        "cluster_count",
        "noise_ratio",
        "largest_cluster_ratio",
        "mean_cluster_size",
        "cluster_size_cv",
        "cluster_diameter_mean",
        "cluster_diameter_max",
        "cluster_type_purity_mean",
        "cluster_type_entropy_mean",
        "mixed_cluster_ratio",
        "control_flow_cluster_count",
        "control_flow_noise_ratio",
        "control_flow_cluster_diameter_mean",
        "control_flow_cluster_diameter_max",
        "persistence_mean",
        "persistence_max",
        "membership_strength_mean",
        "membership_strength_std",
    ),
    "optics": (
        "min_samples",
        "xi",
        "cluster_count",
        "noise_ratio",
        "largest_cluster_ratio",
        "mean_cluster_size",
        "cluster_size_cv",
        "cluster_diameter_mean",
        "cluster_diameter_max",
        "cluster_type_purity_mean",
        "cluster_type_entropy_mean",
        "mixed_cluster_ratio",
        "control_flow_cluster_count",
        "control_flow_noise_ratio",
        "control_flow_cluster_diameter_mean",
        "control_flow_cluster_diameter_max",
        "reachability_mean",
        "reachability_std",
        "reachability_max",
    ),
    "auto_kmeans": (
        "selected_k",
        "silhouette",
        "inertia",
        "inertia_per_weight",
        "cluster_count",
        "largest_cluster_ratio",
        "mean_cluster_size",
        "cluster_size_cv",
        "cluster_diameter_mean",
        "cluster_diameter_max",
        "cluster_type_purity_mean",
        "cluster_type_entropy_mean",
        "mixed_cluster_ratio",
        "control_flow_cluster_count",
        "control_flow_cluster_diameter_mean",
        "control_flow_cluster_diameter_max",
    ),
    "auto_agglo": (
        "threshold",
        "cluster_count",
        "largest_cluster_ratio",
        "mean_cluster_size",
        "cluster_size_cv",
        "cluster_diameter_mean",
        "cluster_diameter_max",
        "cluster_type_purity_mean",
        "cluster_type_entropy_mean",
        "mixed_cluster_ratio",
        "control_flow_cluster_count",
        "control_flow_cluster_diameter_mean",
        "control_flow_cluster_diameter_max",
    ),
    "graph": (
        "similarity_threshold",
        "edge_density",
        "component_count",
        "largest_component_ratio",
        "mean_component_size",
        "component_size_cv",
        "isolate_ratio",
        "component_diameter_mean",
        "component_diameter_max",
        "component_type_purity_mean",
        "component_type_entropy_mean",
        "mixed_component_ratio",
        "control_flow_component_count",
        "control_flow_isolate_ratio",
        "control_flow_component_diameter_mean",
        "control_flow_component_diameter_max",
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
        "embedding_source_count",
        "embedding_available_source_count",
        "embedding_unique_text_count",
        "embedding_coverage_ratio",
        "embedding_algorithm_unique_text_count",
        "embedding_dim",
        "embedding_centroid_norm",
        "embedding_mean_cosine_to_centroid",
        "embedding_std_cosine_to_centroid",
        "embedding_max_cosine_to_centroid",
        "embedding_pairwise_cosine_mean",
        "embedding_pairwise_cosine_std",
        "embedding_effective_rank",
        "embedding_first_pc_explained_variance",
        "auto_dbscan_min_samples",
        "auto_dbscan_eps",
        "auto_dbscan_cluster_count",
        "auto_dbscan_noise_ratio",
        "auto_dbscan_largest_cluster_ratio",
        "auto_dbscan_mean_cluster_size",
        "auto_dbscan_cluster_size_cv",
        "auto_dbscan_cluster_diameter_mean",
        "auto_dbscan_cluster_diameter_max",
        "auto_dbscan_cluster_type_purity_mean",
        "auto_dbscan_cluster_type_entropy_mean",
        "auto_dbscan_mixed_cluster_ratio",
        "auto_dbscan_control_flow_cluster_count",
        "auto_dbscan_control_flow_noise_ratio",
        "auto_dbscan_control_flow_cluster_diameter_mean",
        "auto_dbscan_control_flow_cluster_diameter_max",
    ]
    for k in KMEANS_K_VALUES:
        prefix = f"kmeans_k_{k}"
        names.extend(
            (
                f"{prefix}_inertia",
                f"{prefix}_inertia_per_weight",
                f"{prefix}_largest_cluster_ratio",
                f"{prefix}_cluster_size_cv",
                f"{prefix}_silhouette",
            )
        )
    names.extend(view_clustering_feature_names())
    return names


def view_clustering_feature_names() -> list[str]:
    names: list[str] = []
    for view_name, _, _, _ in CHUNK_VIEW_RULES:
        for suffix in VIEW_COVERAGE_SUFFIXES:
            names.append(f"{view_name}__{suffix}")
        for family, suffixes in VIEW_FAMILY_SUFFIXES.items():
            for suffix in suffixes:
                names.append(f"{view_name}__{family}_{suffix}")
    return names


def embedding_feature_definitions() -> list[EmbeddingFeatureDefinition]:
    definitions = [
        EmbeddingFeatureDefinition("embedding_source_count", "embedding_coverage", "Total chunk source count recorded for this task."),
        EmbeddingFeatureDefinition("embedding_available_source_count", "embedding_coverage", "Chunk source count whose text has a cached embedding."),
        EmbeddingFeatureDefinition("embedding_unique_text_count", "embedding_coverage", "Number of unique embedded chunk texts available for this task."),
        EmbeddingFeatureDefinition("embedding_coverage_ratio", "embedding_coverage", "Available embedded chunk count divided by total chunk source count."),
        EmbeddingFeatureDefinition("embedding_algorithm_unique_text_count", "embedding_coverage", "Number of unique embedded chunk texts used by the embedding algorithms after deterministic capping."),
        EmbeddingFeatureDefinition("embedding_dim", "embedding_coverage", "Embedding vector dimension."),
        EmbeddingFeatureDefinition("embedding_centroid_norm", "embedding_geometry", "L2 norm of the weighted embedding centroid."),
        EmbeddingFeatureDefinition("embedding_mean_cosine_to_centroid", "embedding_geometry", "Weighted mean cosine distance to the task centroid."),
        EmbeddingFeatureDefinition("embedding_std_cosine_to_centroid", "embedding_geometry", "Weighted standard deviation of cosine distance to centroid."),
        EmbeddingFeatureDefinition("embedding_max_cosine_to_centroid", "embedding_geometry", "Maximum cosine distance to centroid."),
        EmbeddingFeatureDefinition("embedding_pairwise_cosine_mean", "embedding_geometry", "Weighted mean pairwise cosine distance among chunk embeddings."),
        EmbeddingFeatureDefinition("embedding_pairwise_cosine_std", "embedding_geometry", "Weighted standard deviation of pairwise cosine distance."),
        EmbeddingFeatureDefinition("embedding_effective_rank", "embedding_geometry", "Entropy-based effective rank of the weighted embedding covariance."),
        EmbeddingFeatureDefinition("embedding_first_pc_explained_variance", "embedding_geometry", "Variance ratio explained by the first principal component."),
        EmbeddingFeatureDefinition("auto_dbscan_min_samples", "embedding_auto_dbscan", "Automatically selected DBSCAN min_samples for this task."),
        EmbeddingFeatureDefinition("auto_dbscan_eps", "embedding_auto_dbscan", "Automatically selected DBSCAN eps from the k-distance distribution."),
        EmbeddingFeatureDefinition("auto_dbscan_cluster_count", "embedding_auto_dbscan", "Auto-DBSCAN non-noise cluster count."),
        EmbeddingFeatureDefinition("auto_dbscan_noise_ratio", "embedding_auto_dbscan", "Auto-DBSCAN noise weight divided by total chunk weight."),
        EmbeddingFeatureDefinition("auto_dbscan_largest_cluster_ratio", "embedding_auto_dbscan", "Auto-DBSCAN largest cluster weight divided by total chunk weight."),
        EmbeddingFeatureDefinition("auto_dbscan_mean_cluster_size", "embedding_auto_dbscan", "Auto-DBSCAN mean non-noise cluster weight."),
        EmbeddingFeatureDefinition("auto_dbscan_cluster_size_cv", "embedding_auto_dbscan", "Auto-DBSCAN coefficient of variation of non-noise cluster weights."),
        EmbeddingFeatureDefinition("auto_dbscan_cluster_diameter_mean", "embedding_auto_dbscan", "Mean cosine diameter of Auto-DBSCAN non-noise clusters."),
        EmbeddingFeatureDefinition("auto_dbscan_cluster_diameter_max", "embedding_auto_dbscan", "Maximum cosine diameter of Auto-DBSCAN non-noise clusters."),
        EmbeddingFeatureDefinition("auto_dbscan_cluster_type_purity_mean", "embedding_auto_dbscan", "Weighted mean dominant chunk-type purity of Auto-DBSCAN clusters."),
        EmbeddingFeatureDefinition("auto_dbscan_cluster_type_entropy_mean", "embedding_auto_dbscan", "Weighted mean chunk-type entropy of Auto-DBSCAN clusters."),
        EmbeddingFeatureDefinition("auto_dbscan_mixed_cluster_ratio", "embedding_auto_dbscan", "Fraction of Auto-DBSCAN clusters containing more than one chunk type."),
        EmbeddingFeatureDefinition("auto_dbscan_control_flow_cluster_count", "embedding_auto_dbscan", "Number of Auto-DBSCAN clusters containing control-flow chunks."),
        EmbeddingFeatureDefinition("auto_dbscan_control_flow_noise_ratio", "embedding_auto_dbscan", "Control-flow chunk weight labelled as Auto-DBSCAN noise divided by all control-flow chunk weight."),
        EmbeddingFeatureDefinition("auto_dbscan_control_flow_cluster_diameter_mean", "embedding_auto_dbscan", "Mean cosine diameter of Auto-DBSCAN clusters containing control-flow chunks."),
        EmbeddingFeatureDefinition("auto_dbscan_control_flow_cluster_diameter_max", "embedding_auto_dbscan", "Maximum cosine diameter of Auto-DBSCAN clusters containing control-flow chunks."),
    ]
    for name in embedding_feature_names():
        if name.startswith("kmeans_"):
            definitions.append(EmbeddingFeatureDefinition(name, "embedding_kmeans", f"KMeans embedding feature: {name}."))
    return definitions


def extract_embedding_feature_row(
    *,
    dataset: str,
    task_id: str,
    readability_score: float | None,
    total_source_count: int,
    vector_rows: Sequence[tuple[str, str, int, np.ndarray]],
    max_vectors: int | None = 512,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "dataset": dataset,
        "task_id": task_id,
        "readability_score": readability_score,
    }
    row.update({name: 0.0 for name in embedding_feature_names()})
    if not vector_rows:
        row["embedding_source_count"] = total_source_count
        return row

    original_unique_count = len(vector_rows)
    original_available_weight = float(sum(count for _, _, count, _ in vector_rows))
    if max_vectors is not None and len(vector_rows) > max_vectors:
        vector_rows = sorted(vector_rows, key=lambda item: (-item[2], item[0], item[1]))[:max_vectors]

    vectors = np.stack([vector for _, _, _, vector in vector_rows]).astype(np.float64)
    weights = np.asarray([count for _, _, count, _ in vector_rows], dtype=np.float64)
    chunk_types = [chunk_type for chunk_type, _, _, _ in vector_rows]
    total_weight = float(max(total_source_count, 1))
    normalized = _normalize_rows(vectors)

    row["embedding_source_count"] = total_source_count
    row["embedding_available_source_count"] = original_available_weight
    row["embedding_unique_text_count"] = original_unique_count
    row["embedding_coverage_ratio"] = original_available_weight / total_weight
    row["embedding_algorithm_unique_text_count"] = len(vector_rows)
    row["embedding_dim"] = vectors.shape[1]
    row.update(_geometry_features(normalized, weights))
    row.update(_auto_dbscan_features(normalized, weights, chunk_types))
    row.update(_kmeans_features(normalized, weights))
    row.update(_view_clustering_features(vector_rows, total_source_count=total_source_count, max_vectors=max_vectors))
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
            "kmeans_k": KMEANS_K_VALUES,
            "auto_dbscan": {
                "min_samples_rule": "max(2, round(log2(n_vectors)))",
                "eps_rule": "quantile(k-distance, 0.75)",
                "k_distance_quantile": AUTO_DBSCAN_K_DISTANCE_QUANTILE,
                "metric": "cosine",
            },
            "view_clustering": {
                "chunk_views": {
                    name: {
                        "description": description,
                        "include_types": sorted(include) if include is not None else None,
                        "exclude_types": sorted(exclude) if exclude is not None else None,
                    }
                    for name, description, include, exclude in CHUNK_VIEW_RULES
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
                "graph": {
                    "similarity_threshold_rule": "quantile(pairwise cosine similarity, 0.75)",
                    "similarity_quantile": AUTO_GRAPH_SIMILARITY_QUANTILE,
                    "community_rule": "connected components",
                },
            },
        },
    }
    metadata_path.write_text(json.dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, metadata_path


def _geometry_features(x: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    total = float(np.sum(weights))
    centroid = np.average(x, axis=0, weights=weights)
    centroid_norm = float(np.linalg.norm(centroid))
    centroid_unit = centroid / max(centroid_norm, 1e-12)
    distances = 1.0 - x @ centroid_unit
    pairwise_mean, pairwise_std = _weighted_pairwise_cosine_stats(x, weights)
    effective_rank, first_pc = _effective_rank_features(x, weights)
    return {
        "embedding_centroid_norm": centroid_norm,
        "embedding_mean_cosine_to_centroid": _weighted_mean(distances, weights),
        "embedding_std_cosine_to_centroid": _weighted_std(distances, weights),
        "embedding_max_cosine_to_centroid": float(np.max(distances)) if distances.size else 0.0,
        "embedding_pairwise_cosine_mean": pairwise_mean,
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
    type_rows = [(_normalize_chunk_type(chunk_type), text, count, vector) for chunk_type, text, count, vector in vector_rows]
    for view_name, _, include_types, exclude_types in CHUNK_VIEW_RULES:
        selected_rows = [
            (chunk_type, text, count, vector)
            for chunk_type, text, count, vector in type_rows
            if _chunk_type_in_view(chunk_type, include_types=include_types, exclude_types=exclude_types)
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
    features[f"{view_name}__source_count"] = source_count
    features[f"{view_name}__unique_text_count"] = float(len(vector_rows))
    features[f"{view_name}__coverage_ratio"] = source_count / max(float(total_source_count), 1.0)

    if max_vectors is not None and len(vector_rows) > max_vectors:
        vector_rows = sorted(vector_rows, key=lambda item: (-item[2], item[0], item[1]))[:max_vectors]
    features[f"{view_name}__algorithm_unique_text_count"] = float(len(vector_rows))
    if not vector_rows:
        return features

    x = _normalize_rows(np.stack([vector for _, _, _, vector in vector_rows]).astype(np.float64))
    weights = np.asarray([count for _, _, count, _ in vector_rows], dtype=np.float64)
    chunk_types = [chunk_type for chunk_type, _, _, _ in vector_rows]

    features.update(_rename_feature_prefix(_geometry_features(x, weights), "embedding", f"{view_name}__embedding"))
    features.update(_rename_feature_prefix(_auto_dbscan_features(x, weights, chunk_types), "auto_dbscan", f"{view_name}__auto_dbscan"))
    features.update(_hdbscan_view_features(view_name, x, weights, chunk_types))
    features.update(_optics_view_features(view_name, x, weights, chunk_types))
    features.update(_auto_kmeans_view_features(view_name, x, weights, chunk_types))
    features.update(_auto_agglo_view_features(view_name, x, weights, chunk_types))
    features.update(_graph_view_features(view_name, x, weights, chunk_types))
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


def _hdbscan_view_features(view_name: str, x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = f"{view_name}__hdbscan"
    values = {f"{prefix}_{suffix}": 0.0 for suffix in VIEW_FAMILY_SUFFIXES["hdbscan"]}
    import hdbscan  # type: ignore

    if len(x) < 2:
        return values

    min_cluster_size = max(2, int(round(math.log2(max(len(x), 2)))))
    min_cluster_size = min(min_cluster_size, len(x))
    min_samples = min_cluster_size
    distances = pairwise_distances(x, metric="cosine").astype(np.float64)
    model = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="precomputed",
    )
    labels = model.fit_predict(distances)
    values[f"{prefix}_min_cluster_size"] = float(min_cluster_size)
    values[f"{prefix}_min_samples"] = float(min_samples)
    values.update(_cluster_summary_features(prefix, x, labels, weights, chunk_types, noise_label=-1))
    persistence = np.asarray(getattr(model, "cluster_persistence_", []), dtype=float)
    probabilities = np.asarray(getattr(model, "probabilities_", []), dtype=float)
    values[f"{prefix}_persistence_mean"] = float(np.mean(persistence)) if persistence.size else 0.0
    values[f"{prefix}_persistence_max"] = float(np.max(persistence)) if persistence.size else 0.0
    if probabilities.size:
        values[f"{prefix}_membership_strength_mean"] = _weighted_mean(probabilities, weights)
        values[f"{prefix}_membership_strength_std"] = _weighted_std(probabilities, weights)
    return values


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
    return values


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
    return values


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
    return values


def _graph_view_features(view_name: str, x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = f"{view_name}__graph"
    values = {f"{prefix}_{suffix}": 0.0 for suffix in VIEW_FAMILY_SUFFIXES["graph"]}
    if len(x) < 2:
        return values
    similarities = x @ x.T
    upper = similarities[np.triu_indices(len(x), k=1)]
    threshold = float(np.quantile(upper, AUTO_GRAPH_SIMILARITY_QUANTILE)) if upper.size else 1.0
    adjacency = (similarities >= threshold) & (~np.eye(len(x), dtype=bool))
    labels = _connected_component_labels(adjacency)
    edge_count = int(np.sum(np.triu(adjacency, k=1)))
    possible_edges = len(x) * (len(x) - 1) / 2
    component_sizes = _cluster_weights(labels, weights)
    isolate_weight = 0.0
    for label in sorted(set(int(label) for label in labels)):
        mask = labels == label
        if int(np.sum(mask)) == 1:
            isolate_weight += float(np.sum(weights[mask]))
    values[f"{prefix}_similarity_threshold"] = threshold
    values[f"{prefix}_edge_density"] = edge_count / max(possible_edges, 1.0)
    values[f"{prefix}_component_count"] = float(len(component_sizes))
    values[f"{prefix}_largest_component_ratio"] = max(component_sizes, default=0.0) / max(float(np.sum(weights)), 1.0)
    values[f"{prefix}_mean_component_size"] = float(np.mean(component_sizes)) if component_sizes else 0.0
    values[f"{prefix}_component_size_cv"] = _coefficient_of_variation(component_sizes)
    values[f"{prefix}_isolate_ratio"] = isolate_weight / max(float(np.sum(weights)), 1.0)
    diameter_features = _cluster_diameter_features(prefix, x, labels, weights, noise_label=None)
    type_features = _cluster_type_features(prefix, labels, weights, chunk_types, noise_label=None)
    values[f"{prefix}_component_diameter_mean"] = diameter_features.get(f"{prefix}_cluster_diameter_mean", 0.0)
    values[f"{prefix}_component_diameter_max"] = diameter_features.get(f"{prefix}_cluster_diameter_max", 0.0)
    values[f"{prefix}_component_type_purity_mean"] = type_features.get(f"{prefix}_cluster_type_purity_mean", 0.0)
    values[f"{prefix}_component_type_entropy_mean"] = type_features.get(f"{prefix}_cluster_type_entropy_mean", 0.0)
    values[f"{prefix}_mixed_component_ratio"] = type_features.get(f"{prefix}_mixed_cluster_ratio", 0.0)
    values.update(_graph_control_flow_features(prefix, x, labels, weights, chunk_types))
    return values


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
    exclude_types: frozenset[str] | None,
) -> bool:
    if include_types is not None and chunk_type not in include_types:
        return False
    if exclude_types is not None and chunk_type in exclude_types:
        return False
    return True


def _connected_component_labels(adjacency: np.ndarray) -> np.ndarray:
    n = adjacency.shape[0]
    labels = np.full(n, -1, dtype=int)
    current_label = 0
    for start in range(n):
        if labels[start] != -1:
            continue
        stack = [start]
        labels[start] = current_label
        while stack:
            node = stack.pop()
            for neighbor in np.flatnonzero(adjacency[node]):
                if labels[neighbor] == -1:
                    labels[neighbor] = current_label
                    stack.append(int(neighbor))
        current_label += 1
    return labels


def _graph_control_flow_features(
    prefix: str,
    x: np.ndarray,
    labels: np.ndarray,
    weights: np.ndarray,
    chunk_types: Sequence[str],
) -> dict[str, float]:
    type_array = np.asarray([str(chunk_type).upper() for chunk_type in chunk_types], dtype=object)
    control_mask = type_array == "CONTROL_FLOW"
    total_control_weight = float(np.sum(weights[control_mask]))
    if total_control_weight <= 0.0:
        return {
            f"{prefix}_control_flow_component_count": 0.0,
            f"{prefix}_control_flow_isolate_ratio": 0.0,
            f"{prefix}_control_flow_component_diameter_mean": 0.0,
            f"{prefix}_control_flow_component_diameter_max": 0.0,
        }
    control_component_labels = set(int(label) for label in labels[control_mask])
    isolate_control_weight = 0.0
    diameters: list[float] = []
    control_weights: list[float] = []
    for label in control_component_labels:
        component_mask = labels == label
        if int(np.sum(component_mask)) == 1:
            isolate_control_weight += float(np.sum(weights[component_mask & control_mask]))
        cluster_control_weight = float(np.sum(weights[component_mask & control_mask]))
        if cluster_control_weight > 0.0:
            diameters.append(_cluster_diameter(x[component_mask]))
            control_weights.append(cluster_control_weight)
    return {
        f"{prefix}_control_flow_component_count": float(len(control_component_labels)),
        f"{prefix}_control_flow_isolate_ratio": isolate_control_weight / total_control_weight,
        f"{prefix}_control_flow_component_diameter_mean": (
            _weighted_mean(np.asarray(diameters), np.asarray(control_weights)) if diameters else 0.0
        ),
        f"{prefix}_control_flow_component_diameter_max": float(max(diameters)) if diameters else 0.0,
    }


def _auto_dbscan_features(x: np.ndarray, weights: np.ndarray, chunk_types: Sequence[str]) -> dict[str, float]:
    prefix = "auto_dbscan"
    empty = {
        f"{prefix}_min_samples": 0.0,
        f"{prefix}_eps": 0.0,
        f"{prefix}_cluster_count": 0.0,
        f"{prefix}_noise_ratio": 0.0,
        f"{prefix}_largest_cluster_ratio": 0.0,
        f"{prefix}_mean_cluster_size": 0.0,
        f"{prefix}_cluster_size_cv": 0.0,
        f"{prefix}_cluster_diameter_mean": 0.0,
        f"{prefix}_cluster_diameter_max": 0.0,
        f"{prefix}_cluster_type_purity_mean": 0.0,
        f"{prefix}_cluster_type_entropy_mean": 0.0,
        f"{prefix}_mixed_cluster_ratio": 0.0,
        f"{prefix}_control_flow_cluster_count": 0.0,
        f"{prefix}_control_flow_noise_ratio": 0.0,
        f"{prefix}_control_flow_cluster_diameter_mean": 0.0,
        f"{prefix}_control_flow_cluster_diameter_max": 0.0,
    }
    if len(x) < 2:
        return empty

    min_samples = max(2, int(round(math.log2(max(len(x), 2)))))
    min_samples = min(min_samples, len(x))
    distances = pairwise_distances(x, metric="cosine")
    sorted_distances = np.sort(distances, axis=1)
    kth_index = min(min_samples, sorted_distances.shape[1] - 1)
    k_distances = sorted_distances[:, kth_index]
    eps = float(np.quantile(k_distances, AUTO_DBSCAN_K_DISTANCE_QUANTILE))
    if not math.isfinite(eps) or eps <= 0.0:
        positive = k_distances[k_distances > 0]
        eps = float(np.median(positive)) if positive.size else 1e-12

    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit_predict(x, sample_weight=weights)
    values = {
        f"{prefix}_min_samples": float(min_samples),
        f"{prefix}_eps": eps,
    }
    values.update(_cluster_features_from_labels(prefix, labels, weights, noise_label=-1))
    values.update(_cluster_diameter_features(prefix, x, labels, weights, noise_label=-1))
    values.update(_cluster_type_features(prefix, labels, weights, chunk_types, noise_label=-1))
    values.update(_control_flow_cluster_features(prefix, x, labels, weights, chunk_types, noise_label=-1))
    return values


def _kmeans_features(x: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    features: dict[str, float] = {}
    total = float(np.sum(weights))
    distinct_vector_count = len(np.unique(x, axis=0)) if len(x) else 0
    for k in KMEANS_K_VALUES:
        prefix = f"kmeans_k_{k}"
        if len(x) < k or distinct_vector_count < k or total <= 0:
            features.update(
                {
                    f"{prefix}_inertia": 0.0,
                    f"{prefix}_inertia_per_weight": 0.0,
                    f"{prefix}_largest_cluster_ratio": 0.0,
                    f"{prefix}_cluster_size_cv": 0.0,
                    f"{prefix}_silhouette": 0.0,
                }
            )
            continue
        model = KMeans(n_clusters=k, n_init=10, random_state=0)
        labels = model.fit_predict(x, sample_weight=weights)
        cluster_weights = _cluster_weights(labels, weights)
        features[f"{prefix}_inertia"] = float(model.inertia_)
        features[f"{prefix}_inertia_per_weight"] = float(model.inertia_ / total)
        features[f"{prefix}_largest_cluster_ratio"] = max(cluster_weights, default=0.0) / total
        features[f"{prefix}_cluster_size_cv"] = _coefficient_of_variation(cluster_weights)
        features[f"{prefix}_silhouette"] = _safe_silhouette(x, labels)
    return features


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
