"""Selection support, source identity, redundancy, and predictor evaluation."""

import json

import numpy as np
import pandas as pd
import pytest

from experiments.main.readability_model.selection import screen_llm_features as screen
from src.datasets import DatasetItem
from src.methods.readability_model.dataset_io import item_source_sha256
from src.methods.readability_model.llm_features.inventory import (
    LLM_FEATURE_BUILD_VERSION,
    LLM_FEATURE_NAMES,
)


def test_consensus_support_is_not_the_number_of_complete_rankings():
    rows = [
        {
            "feature": "llm__code_bits_per_byte",
            "rank": 1,
            "active": True,
            "selection_frequency": 0.7,
            "abs_coefficient": 0.5,
            "mean_stability_abs_coefficient": 0.3,
        },
        {
            "feature": "base__operator_density",
            "rank": 2,
            "active": False,
            "selection_frequency": 0.0,
            "abs_coefficient": 0.0,
            "mean_stability_abs_coefficient": 0.0,
        },
    ]
    second = [dict(row) for row in rows]
    second[0].update(active=False, selection_frequency=0.0, abs_coefficient=0.0)
    result = screen.consensus_ranking({"first": rows, "second": second})
    assert result[0]["feature"] == "llm__code_bits_per_byte"
    assert result[0]["active_model_count"] == 1
    assert result[0]["mean_selection_frequency"] == pytest.approx(0.35)
    assert result[1]["active_model_count"] == 0


def test_stability_uses_l1_and_keeps_never_selected_candidates_ranked():
    frame = pd.DataFrame(
        {
            "dataset": ["one"] * 20 + ["two"] * 20,
            "task_id": [str(i) for i in range(40)],
            "readability_score": list(range(20)) * 2,
            "base__signal": list(range(20)) * 2,
            "llm__empty": np.nan,
        }
    )
    first = screen.stability_ranking(
        frame, ["base__signal", "llm__empty"], c=1.0, rounds=5, fraction=0.7, seed=42
    )
    second = screen.stability_ranking(
        frame, ["base__signal", "llm__empty"], c=1.0, rounds=5, fraction=0.7, seed=42
    )
    assert first == second
    assert first[0]["feature"] == "base__signal"
    assert first[0]["active"] is True
    assert first[1]["active"] is False
    assert first[1]["selection_frequency"] == 0.0
    assert screen.binary_targets(frame)[9:11].tolist() == [0, 1]


def test_correlation_filter_skips_lower_ranked_duplicate_and_replaces():
    frame = pd.DataFrame(
        {
            "base__first": [0, 1, 2, 3, 4],
            "llm__duplicate": [0, -1, -2, -3, -4],
            "llm__different": [1, 0, 1, 0, 1],
        }
    )
    names = list(frame.columns)
    ranking = [{"feature": name, "rank": i + 1} for i, name in enumerate(names)]
    selected, rejected = screen.correlation_selection(
        ranking, frame, names, top=2, threshold=0.9
    )
    assert selected == ["base__first", "llm__different"]
    assert rejected[0]["feature"] == "llm__duplicate"
    assert rejected[0]["conflicts"][0]["pearson"] == pytest.approx(-1)


def test_llm_table_requires_current_hash_inventory_and_complete_build(tmp_path):
    item = DatasetItem("task", "def f(): return 1", 3.0)
    path = tmp_path / "features.csv"
    row = {
        "dataset": "unit",
        "task_id": "task",
        "readability_score": 3.0,
        **dict.fromkeys(LLM_FEATURE_NAMES, 0.5),
    }
    pd.DataFrame([row]).to_csv(path, index=False)
    metadata = {
        "complete": True,
        "feature_count": 47,
        "configuration": {"feature_build_version": LLM_FEATURE_BUILD_VERSION},
        "rows": [{"task_id": "task", "source_sha256": item_source_sha256(item)}],
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata))
    frame = screen.load_table(path, "llm", {"task": item}, dataset="unit", llm=True)
    assert set(LLM_FEATURE_NAMES).issubset(frame.columns)
    metadata["complete"] = False
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="incomplete"):
        screen.load_table(path, "llm", {"task": item}, dataset="unit", llm=True)
    metadata["complete"] = True
    metadata["rows"][0]["source_sha256"] = "outdated"
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="Outdated source"):
        screen.load_table(path, "llm", {"task": item}, dataset="unit", llm=True)


def test_unrated_constructed_table_preserves_absent_labels(tmp_path):
    item = DatasetItem("task", "class A {}", None)
    path = tmp_path / "features.csv"
    row = {
        "dataset": "constructed", "task_id": "task",
        "readability_score": np.nan, "operator_density": 1.0,
    }
    pd.DataFrame([row]).to_csv(path, index=False)
    path.with_name("metadata.json").write_text(json.dumps({
        "source_sha256_by_task": {"task": item_source_sha256(item)},
    }))
    frame = screen.load_table(path, "base", {"task": item}, dataset="constructed")
    assert pd.isna(frame.readability_score.iloc[0])
    row["readability_score"] = 0.0
    pd.DataFrame([row]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Invented readability label"):
        screen.load_table(path, "base", {"task": item}, dataset="constructed")


def test_evaluation_refits_predictors_without_reranking(monkeypatch):
    frame = pd.DataFrame(
        [
            {
                "dataset": dataset,
                "task_id": str(index),
                "readability_score": index + 1,
                "base__signal": index / 3,
            }
            for dataset in screen.CORE_DATASETS
            for index in range(4)
        ]
    )
    fits = []

    def fit(train, mask, alpha, features):
        fits.append(train.copy())
        assert mask.all()
        assert alpha == 200
        assert features == ["base__signal"]

        class Model:
            @staticmethod
            def predict(values):
                return values[:, 0]

        return Model()

    monkeypatch.setattr(screen, "fit_ridge", fit)
    result, rows = screen.evaluate_features(
        frame, ["base__signal"], folds=2, seed=42, alpha=200
    )
    assert result["pooled_cv"]["unweighted_mean"] == pytest.approx(1)
    assert result["lodo"]["unweighted_mean"] == pytest.approx(1)
    assert len(fits) == 2 + 6 + 1
    for fold in range(2):
        held_out = set(
            map(
                tuple,
                rows.loc[rows["cv_fold"] == fold, ["dataset", "task_id"]].to_numpy(),
            )
        )
        trained = set(map(tuple, fits[fold][["dataset", "task_id"]].to_numpy()))
        assert not held_out & trained
    for dataset, train in zip(screen.CORE_DATASETS, fits[2:8], strict=True):
        assert dataset not in set(train["dataset"])
