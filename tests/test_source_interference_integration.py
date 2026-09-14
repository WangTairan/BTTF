"""Contract between independent source generation and CognaScore evaluation."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from readability_data.java_degradation import construct_interference_dataset
from readability_data.java_degradation.registry import interference_registry
from readability_data.python_degradation import construct_python_dataset
from readability_data.python_degradation.registry import INTERFERENCES
from readability_experiments.cli import build_parser
from readability_experiments.common.paths import (
    constructed_dataset,
    default_results,
    default_workspace,
    repository_root,
)
from src.datasets.constructed_variants.loader import load_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_defaults_do_not_depend_on_current_directory(monkeypatch, tmp_path):
    monkeypatch.delenv("READABILITY_REPOSITORY_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)
    args = build_parser().parse_args([])
    assert repository_root() == ROOT
    assert (
        args.workspace == default_workspace() == ROOT / "artifacts/source_interference"
    )
    assert args.java_dataset == constructed_dataset("java")
    assert args.python_dataset == constructed_dataset("python")
    assert (
        default_results("deepseek")
        == ROOT / "results/experiments/source_interference/deepseek"
    )


def test_invalid_explicit_repository_root_is_not_silently_ignored(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("READABILITY_REPOSITORY_ROOT", str(tmp_path))
    with pytest.raises(RuntimeError, match="Cannot locate"):
        repository_root()


@pytest.mark.parametrize("language", ["java", "python"])
def test_formal_dataset_matches_generator_catalog(language):
    catalog = interference_registry() if language == "java" else INTERFERENCES
    provenance = json.loads(
        (constructed_dataset(language) / "provenance.json").read_text()
    )
    assert [item["slug"] for item in provenance["interferences"]] == list(catalog)
    assert len(catalog) == provenance["interference_count"] == 13
    items = load_dataset(constructed_dataset(language))
    assert len(items) == provenance["variant_count_including_originals"] == 1400
    assert sum(item.metadata["is_baseline_variant"] for item in items) == 100


def test_generated_java_is_readable_by_evaluation_adapter(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "Example.java").write_text(
        "/** Calculate a total. */\npublic class Example {\n"
        "  int total(int count) { int value = count + 7; return value; }\n}\n"
    )
    output = tmp_path / "generated"
    provenance = construct_interference_dataset(source, output, seed=7)
    assert not Path(provenance["input"]["root"]).is_absolute()
    assert provenance["input"]["path_base"] == "invocation-working-directory"
    items = load_dataset(output)
    assert len(items) == 14
    assert {item.metadata["language"] for item in items} == {"java"}
    assert sum(item.metadata["is_baseline_variant"] for item in items) == 1
    with pytest.raises(ValueError, match="already exists"):
        construct_interference_dataset(source, output, seed=7)


def test_generated_python_is_readable_by_evaluation_adapter(tmp_path):
    roots = {}
    for project in ("django", "flask", "requests", "attrs"):
        repository = tmp_path / project
        repository.mkdir()
        (repository / "module.py").write_text(
            'class Example:\n    """Calculate a total."""\n'
            "    def total(self, count):\n        value = count + 7\n        return value\n"
        )
        roots[project] = repository
    output = tmp_path / "generated"
    with patch(
        "readability_data.python_degradation.sampling._commit", return_value="a" * 40
    ):
        construct_python_dataset(roots, output, per_project=1, seed=7)
    items = load_dataset(output)
    assert len(items) == 56
    assert {item.metadata["language"] for item in items} == {"python"}
    assert sum(item.metadata["is_baseline_variant"] for item in items) == 4
