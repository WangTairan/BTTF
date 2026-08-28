from pathlib import Path

import math

from src.datasets import load_code_dataset
from src.experiments.paths import dataset_name_for_path
from experiments.cognascore.evaluate_constructed_variants import summarize_paired_variants


CONSTRUCTED_ROOT = Path("datasets/constructed")


def test_comparative_obfuscation_dataset() -> None:
    path = CONSTRUCTED_ROOT / "java-comparative-obfuscation-class-100"
    items = load_code_dataset(path)

    assert dataset_name_for_path(path) == "java_comparative_obfuscation"
    assert len(items) == 1300
    assert len({item.metadata["group_id"] for item in items}) == 100
    assert {item.metadata["order"] for item in items} == set(range(13))
    assert sum(item.metadata["is_baseline_variant"] for item in items) == 100
    assert all(item.readability_score is None for item in items)


def test_original_progressive_dataset_remains_ordinal() -> None:
    path = CONSTRUCTED_ROOT / "java-progressive-obfuscation-class-100"
    items = load_code_dataset(path)

    assert dataset_name_for_path(path) == "java_progressive_obfuscation"
    assert len(items) == 700
    scores = sorted({item.readability_score for item in items})
    assert len(scores) == 7
    assert all(
        math.isclose(actual, expected)
        for actual, expected in zip(scores, (index / 6.0 for index in range(7)))
    )


def test_paired_summary_does_not_treat_interference_order_as_severity() -> None:
    rows = [
        {
            "task_id": "source",
            "group_id": "g",
            "position": 0,
            "stage": "original",
            "interference": None,
            "category": "source",
            "is_baseline": True,
            "score": 0.8,
            "content_sha256": "a",
        },
        {
            "task_id": "first",
            "group_id": "g",
            "position": 1,
            "stage": "first",
            "interference": "first",
            "category": "names",
            "is_baseline": False,
            "score": 0.5,
            "content_sha256": "b",
        },
        {
            "task_id": "second",
            "group_id": "g",
            "position": 2,
            "stage": "second",
            "interference": "second",
            "category": "layout",
            "is_baseline": False,
            "score": 0.9,
            "content_sha256": "c",
        },
    ]

    summary = summarize_paired_variants(rows)
    assert summary["overall"]["score_decrease_rate"] == 0.5
    assert math.isclose(summary["by_interference"]["first"]["mean_original_minus_variant"], 0.3)
    assert math.isclose(summary["by_interference"]["second"]["mean_original_minus_variant"], -0.1)
