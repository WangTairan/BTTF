import json
from pathlib import Path
import tempfile
import unittest

from src.methods.dorn.extractor import FEATURE_NAMES, extract_dorn_features
from src.methods.dorn.method import load_model, metric_value, stable_sigmoid


class DornTest(unittest.TestCase):
    def test_metric_name_maps_official_arff_to_extractor(self) -> None:
        self.assertEqual(
            metric_value(
                {"Dorn Areas Operators/Keywords": 0.25},
                "Dorn-Areas-Operators/Keywords",
            ),
            0.25,
        )

    def test_metric_name_accepts_arff_style_adapter_output(self) -> None:
        self.assertEqual(
            metric_value({"Dorn-DFT-Comments": 3.0}, "Dorn-DFT-Comments"),
            3.0,
        )

    def test_stable_sigmoid_is_monotonic(self) -> None:
        self.assertLess(stable_sigmoid(-1000.0), stable_sigmoid(0.0))
        self.assertLess(stable_sigmoid(0.0), stable_sigmoid(1000.0))

    def test_language_aware_extractor_supports_python(self) -> None:
        metrics = extract_dorn_features(
            "def total(values):\n    return sum(values)\n",
            "python",
        )
        self.assertEqual(tuple(metrics), FEATURE_NAMES)

    def test_model_loader_rejects_incomplete_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            path.write_text(json.dumps({"selected_features": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing"):
                load_model(path)


if __name__ == "__main__":
    unittest.main()
