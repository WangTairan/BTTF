"""Checks that maintenance cannot silently alter the publication contract."""

import hashlib
import json
import unittest
from pathlib import Path

from experiments.cognascore.evaluation.metrics import unweighted_spearman_average


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
            unweighted_spearman_average({"empty": {"n": 0, "value": 0.4}}, ("empty",))

    def test_frozen_model_checksum_and_evidence_paths(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads(
            (
                root
                / "experiments/cognascore/configs/consensus18_6dataset_sampled_margin.json"
            ).read_text()
        )
        model = root / config["model_artifact"] / "model.joblib"
        self.assertEqual(
            hashlib.sha256(model.read_bytes()).hexdigest(),
            config["serialized_model_sha256"],
        )
        evidence = config["selection_evidence"]
        for key in ("ranking_artifact", "selected_rank_artifact"):
            self.assertTrue((root / evidence[key]).is_file())

    def test_public_source_and_documentation_have_no_machine_specific_paths(self):
        root = Path(__file__).resolve().parents[1]
        prefixes = (
            "/" + "Users/",
            "/opt/" + "miniconda3/",
            "/opt/" + "homebrew/",
            "/private/tmp/" + "rmc_",
        )
        paths = [root / "README.md"]
        for directory in (
            "src",
            "experiments",
            "scripts",
            "figures",
            "tools/source_interference",
        ):
            paths.extend(
                path
                for path in (root / directory).rglob("*")
                if path.suffix in {".py", ".sh", ".md", ".toml", ".json"}
                and "notes" not in path.relative_to(root).parts
                and "build" not in path.relative_to(root).parts
            )
        for path in paths:
            content = path.read_text(encoding="utf-8")
            self.assertFalse(
                any(prefix in content for prefix in prefixes),
                f"Machine-specific path in {path.relative_to(root)}",
            )

    def test_mi_reproduction_has_the_manifested_frozen_weights(self):
        root = Path(__file__).resolve().parents[1] / "frozen_models/mi_convnet_cr"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        weights = root / manifest["weights"]["file"]
        self.assertEqual(
            hashlib.sha256(weights.read_bytes()).hexdigest(),
            manifest["weights"]["sha256"],
        )

    def test_reproduction_versions_match_frozen_manifest(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads(
            (
                root
                / "experiments/cognascore/configs/consensus18_6dataset_sampled_margin.json"
            ).read_text()
        )
        manifest = json.loads(
            (root / config["model_artifact"] / "model.json").read_text()
        )
        requirements = (root / "requirements-reproduction.txt").read_text().splitlines()
        for package, key in (
            ("numpy", "numpy"),
            ("pandas", "pandas"),
            ("scikit-learn", "scikit_learn"),
        ):
            self.assertIn(f"{package}=={manifest['libraries'][key]}", requirements)


if __name__ == "__main__":
    unittest.main()
