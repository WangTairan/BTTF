"""Checks that maintenance cannot silently alter the publication contract."""

import csv
import hashlib
import json
import unittest
from pathlib import Path

from experiments.main.readability_model.evaluation.metrics import (
    unweighted_spearman_average,
)
from src.methods.readability_model.feature_schema import (
    FINAL_FEATURE_DISPLAY_NAMES,
    feature_display_name,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "experiments/main/readability_model/configs"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicationContractTest(unittest.TestCase):
    def test_benchmark_average_is_dataset_equal_not_sample_weighted(self):
        metrics = {
            "small": {"n": 17, "value": 0.8},
            "large": {"n": 360, "value": 0.4},
        }
        self.assertAlmostEqual(
            unweighted_spearman_average(metrics, ("small", "large")), 0.6
        )

    def test_benchmark_average_requires_every_dataset(self):
        with self.assertRaises(KeyError):
            unweighted_spearman_average({}, ("missing",))
        for value in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                unweighted_spearman_average(
                    {"bad": {"n": 17, "value": value}}, ("bad",)
                )
        with self.assertRaises(ValueError):
            unweighted_spearman_average(
                {"empty": {"n": 0, "value": 0.4}}, ("empty",)
            )

    def assert_frozen_config(self, filename: str, feature_count: int) -> dict:
        config = json.loads((CONFIG_ROOT / filename).read_text(encoding="utf-8"))
        self.assertEqual(config["status"], "frozen")
        self.assertEqual(len(config["selected_features"]), feature_count)
        artifact = ROOT / config["model_artifact"]
        manifest = json.loads((artifact / "model.json").read_text(encoding="utf-8"))
        model = artifact / manifest["serialized_model"]
        self.assertEqual(sha256(model), config["serialized_model_sha256"])
        self.assertEqual(sha256(model), manifest["serialized_model_sha256"])
        self.assertEqual(manifest["embedding_model"], config["embedding_model"])
        self.assertEqual(
            manifest["features"]["ordered_names"], config["selected_features"]
        )
        return config

    def test_final_11_feature_model_and_selection_evidence(self):
        config = self.assert_frozen_config(
            "consensus11_6dataset_three_llm_opencoder_jina.json", 11
        )
        artifact = ROOT / config["model_artifact"] / "model.json"
        manifest = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertEqual(manifest["llm_feature_model"], config["llm_feature_model"])

        evidence = config["selection_evidence"]
        ranking = ROOT / evidence["ranking_artifact"]
        self.assertEqual(sha256(ranking), evidence["ranking_artifact_sha256"])
        with ranking.open(newline="", encoding="utf-8") as stream:
            ranked = [row["feature"] for row in csv.DictReader(stream)]
        self.assertEqual(ranked[:11], config["selected_features"])
        self.assertEqual(
            list(FINAL_FEATURE_DISPLAY_NAMES), config["selected_features"]
        )
        self.assertEqual(
            manifest["features"]["display_names"],
            [feature_display_name(name) for name in config["selected_features"]],
        )

    def test_embedding_only_predecessor_and_selection_evidence(self):
        config = self.assert_frozen_config(
            "consensus18_6dataset_sampled_margin.json", 18
        )
        for key in ("ranking_artifact", "selected_rank_artifact"):
            self.assertTrue((ROOT / config["selection_evidence"][key]).is_file())

    def test_paper_evidence_files_exist(self):
        evidence = CONFIG_ROOT / "evidence"
        for filename in (
            "consensus11_benchmark_bootstrap_intervals.csv",
            "consensus11_causal_lm_robustness.csv",
            "consensus11_three_llm_full_ranking.csv",
            "consensus18_5model_full_ranking.csv",
            "consensus18_selected_ranks.csv",
        ):
            self.assertTrue((evidence / filename).is_file(), filename)

        with (evidence / "consensus11_causal_lm_robustness.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            robustness = list(csv.DictReader(stream))
        self.assertEqual(len(robustness), 15)
        self.assertTrue(
            all(
                row["expected_sign_agreement"] == row["expected_sign_total"] == "11"
                for row in robustness
            )
        )

    def test_public_source_and_documentation_have_no_machine_specific_paths(self):
        prefixes = (
            "/" + "Users/",
            "/opt/" + "miniconda3/",
            "/opt/" + "homebrew/",
            "/private/tmp/" + "rmc_",
        )
        paths = [ROOT / "README.md", ROOT / "RELEASING.md"]
        for directory in (
            "src",
            "experiments",
            "scripts",
            "figures",
            "tools/source_interference",
        ):
            paths.extend(
                path
                for path in (ROOT / directory).rglob("*")
                if path.suffix in {".py", ".sh", ".md", ".toml", ".json"}
                and "notes" not in path.relative_to(ROOT).parts
                and "build" not in path.relative_to(ROOT).parts
            )
        for path in paths:
            content = path.read_text(encoding="utf-8")
            self.assertFalse(
                any(prefix in content for prefix in prefixes),
                f"Machine-specific path in {path.relative_to(ROOT)}",
            )

    def test_mi_reproduction_has_manifested_frozen_weights(self):
        root = ROOT / "frozen_models/mi_convnet_cr"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        weights = root / manifest["weights"]["file"]
        self.assertEqual(sha256(weights), manifest["weights"]["sha256"])

    def test_reproduction_versions_match_both_primary_manifests(self):
        requirements = (ROOT / "requirements-reproduction.txt").read_text().splitlines()
        for filename in (
            "consensus11_6dataset_three_llm_opencoder_jina.json",
            "consensus18_6dataset_sampled_margin.json",
        ):
            config = json.loads((CONFIG_ROOT / filename).read_text())
            manifest = json.loads(
                (ROOT / config["model_artifact"] / "model.json").read_text()
            )
            for package, key in (
                ("numpy", "numpy"),
                ("pandas", "pandas"),
                ("scikit-learn", "scikit_learn"),
            ):
                self.assertIn(f"{package}=={manifest['libraries'][key]}", requirements)


if __name__ == "__main__":
    unittest.main()
