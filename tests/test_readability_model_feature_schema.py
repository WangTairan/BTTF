import json
import math
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

from src.datasets import DatasetItem
from src.datasets.schnappinger import load_dataset as load_schnappinger_dataset
from src.methods.readability_model.embedding_features import (
    _effective_rank_features,
    _geometry_features,
    embedding_feature_names,
)
from src.methods.readability_model.feature_database import (
    BASE_FEATURE_NAMES,
    TYPE_STAT_NAMES,
    extract_feature_row,
)
from src.methods.readability_model.feature_schema import (
    canonical_feature_name,
    feature_family,
    namespaced_feature,
)
from src.methods.readability_model.extractors import extractor_for_language
from src.methods.readability_model.runners.supervised_ridge import SELECTED_FEATURES


class ReadabilityModelFeatureSchemaTest(unittest.TestCase):
    def test_historical_selected_feature_names_migrate_to_canonical_keys(self) -> None:
        aliases = {
            "base__expression_complexity": "base__expression_literal_density",
            "embedding__structural_core__auto_kmeans_pattern_count": (
                "embedding__computation_control_pattern_count"
            ),
            "llm__literal_tail_difficulty": "llm__literal_tail_surprisal",
            "llm__identifier_onset_difficulty": "llm__identifier_onset_surprisal",
            "llm__assignment_value_difficulty": "llm__assignment_value_surprisal",
            "llm__declaration_difficulty_variation": (
                "llm__declaration_surprisal_variation"
            ),
        }
        for historical, canonical in aliases.items():
            self.assertEqual(canonical_feature_name(historical), canonical)
            family, raw_name = historical.split("__", 1)
            self.assertEqual(namespaced_feature(family, raw_name), canonical)

    def test_three_storage_families_preserve_model_namespaces(self) -> None:
        self.assertEqual(feature_family("base__operator_density"), "base")
        self.assertEqual(feature_family("compression__gzip_ratio"), "base")
        self.assertEqual(
            feature_family("embedding__all__embedding_effective_rank"), "embedding"
        )
        self.assertEqual(
            feature_family("semantic__short_identifier_prevalence"), "embedding"
        )
        self.assertEqual(feature_family("llm__code_bits_per_byte"), "llm")
        with self.assertRaises(ValueError):
            feature_family("unclassified")

    def test_current_feature_schema_is_unique_and_pruned(self) -> None:
        base_names = [*BASE_FEATURE_NAMES, *TYPE_STAT_NAMES]
        embedding_names = embedding_feature_names()

        self.assertEqual(len(base_names), len(set(base_names)))
        self.assertFalse({"chunk_y_std", "chunk_line_span_ratio"} & set(base_names))
        self.assertEqual(len(embedding_names), len(set(embedding_names)))
        self.assertEqual(len(embedding_names), 102)
        self.assertIn(
            "all__embedding_mean_cosine_distance_to_centroid",
            embedding_names,
        )
        self.assertNotIn(
            "all__embedding_mean_cosine_to_centroid",
            embedding_names,
        )
        self.assertIn("expression_literal_density", base_names)
        self.assertNotIn("literal_expression_log_balance", base_names)
        self.assertIn(
            "all__embedding_dispersion",
            embedding_names,
        )
        self.assertNotIn(
            "all__embedding_first_pc_explained_variance",
            embedding_names,
        )

    def test_frozen_model_uses_only_current_features(self) -> None:
        available = {
            *(
                namespaced_feature("base", name)
                for name in [*BASE_FEATURE_NAMES, *TYPE_STAT_NAMES]
            ),
            *(
                namespaced_feature("embedding", name)
                for name in embedding_feature_names()
            ),
        }
        self.assertTrue(set(SELECTED_FEATURES).issubset(available))

    def test_expression_literal_balance_is_oriented_toward_difficulty(self) -> None:
        row = extract_feature_row(
            dataset="test",
            item=DatasetItem(
                task_id="example",
                content="class A { int f(int x) { return (x + 1) * (x - 2); } }",
                metadata={"language": "java"},
            ),
        )
        chunks, _ = extractor_for_language("java").extract_with_member_fallback(
            "class A { int f(int x) { return (x + 1) * (x - 2); } }"
        )
        counts = Counter(chunk.type.upper() for chunk in chunks)
        expression_count = sum(
            counts[chunk_type]
            for chunk_type in ("ARITHMETIC", "BITWISE", "COMPARISON", "LOGICAL")
        )
        expected = math.log1p(expression_count) - math.log1p(counts["LITERAL"])
        self.assertAlmostEqual(row["expression_literal_density"], expected)

    def test_residual_variance_is_one_minus_first_pc_share(self) -> None:
        vectors = np.asarray(
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            dtype=float,
        )
        weights = np.ones(3, dtype=float)
        _, first_pc = _effective_rank_features(vectors, weights)
        features = _geometry_features(vectors, weights)
        self.assertAlmostEqual(
            features["embedding_dispersion"],
            1.0 - first_pc,
        )

    def test_schnappinger_source_files_have_unique_task_ids(self) -> None:
        items = load_schnappinger_dataset(Path("datasets/schnappinger"))
        task_ids = [item.task_id for item in items]
        self.assertEqual(len(task_ids), 304)
        self.assertEqual(len(task_ids), len(set(task_ids)))

    def test_frozen_model_and_research_config_match_production_list(self) -> None:
        config = json.loads(
            Path(
                "experiments/main/readability_model/configs/"
                "consensus18_6dataset_sampled_margin.json"
            ).read_text(encoding="utf-8")
        )
        manifest = json.loads(
            Path(
                "frozen_models/cognascore/"
                "consensus18_6dataset_sampled_margin_jina/"
                "jinaai-jina-embeddings-v2-base-code/model.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(config["selected_features"], SELECTED_FEATURES)
        self.assertEqual(manifest["features"]["ordered_names"], SELECTED_FEATURES)


if __name__ == "__main__":
    unittest.main()
