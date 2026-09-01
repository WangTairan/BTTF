import json
import unittest
from pathlib import Path

from src.datasets.schnappinger import load_dataset as load_schnappinger_dataset
from src.methods.cognascore.embedding_features import embedding_feature_names
from src.methods.cognascore.feature_database import BASE_FEATURE_NAMES, TYPE_STAT_NAMES
from src.methods.cognascore.feature_schema import namespaced_feature
from src.methods.cognascore.runners.supervised_ridge import SELECTED_FEATURES


class CognaScoreFeatureSchemaTest(unittest.TestCase):
    def test_current_feature_schema_is_unique_and_pruned(self) -> None:
        base_names = [*BASE_FEATURE_NAMES, *TYPE_STAT_NAMES]
        embedding_names = embedding_feature_names()

        self.assertEqual(len(base_names), len(set(base_names)))
        self.assertFalse(
            {"chunk_y_std", "chunk_line_span_ratio"}
            & set(base_names)
        )
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

    def test_frozen_model_uses_only_current_features(self) -> None:
        available = {
            *(namespaced_feature("base", name) for name in [*BASE_FEATURE_NAMES, *TYPE_STAT_NAMES]),
            *(namespaced_feature("embedding", name) for name in embedding_feature_names()),
        }
        self.assertTrue(set(SELECTED_FEATURES).issubset(available))

    def test_schnappinger_source_files_have_unique_task_ids(self) -> None:
        items = load_schnappinger_dataset(Path("datasets/schnappinger"))
        task_ids = [item.task_id for item in items]
        self.assertEqual(len(task_ids), 304)
        self.assertEqual(len(task_ids), len(set(task_ids)))

    def test_frozen_model_and_research_config_match_production_list(self) -> None:
        config = json.loads(
            Path(
                "experiments/cognascore/configs/"
                "consensus18_6dataset_sampled_margin.json"
            ).read_text(encoding="utf-8")
        )
        manifest = json.loads(
            Path(
                "frozen_models/cognascore/"
                "consensus18_6dataset_sampled_margin_nomic/"
                "nomic-ai-nomic-embed-text-v1.5/model.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(config["selected_features"], SELECTED_FEATURES)
        self.assertEqual(manifest["features"]["ordered_names"], SELECTED_FEATURES)


if __name__ == "__main__":
    unittest.main()
