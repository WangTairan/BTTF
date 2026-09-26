"""End-to-end table/cache behavior with deterministic, source-aligned losses."""

import csv
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.datasets import DatasetItem, load_code_dataset
from src.experiments.paths import dataset_name_for_path
from src.methods.readability_model.llm_features.cache import LLMTraceCache
from src.methods.readability_model.llm_features.inventory import LLM_FEATURE_NAMES
from src.methods.readability_model.llm_features.scoring import (
    CommentEffect,
    CommentTarget,
    TokenizedSource,
    TraceConfiguration,
)
from src.methods.readability_model.llm_features.types import TokenLoss
from src.methods.readability_model.runners import llm_surprisal_features as runner


class FakeScorer:
    def __init__(self):
        self.tokenizations = 0
        self.windows = 0

    def tokenize(self, source):
        self.tokenizations += 1
        return TokenizedSource(
            [1] * len(source), [(i, i + 1) for i in range(len(source))], 0
        )

    def score_trace(self, tokenized, *, kind, existing_losses, checkpoint):
        rows = list(existing_losses)
        for start in range(len(rows), len(tokenized.input_ids), 8):
            stop = min(start + 8, len(tokenized.input_ids))
            losses = [
                TokenLoss(
                    i,
                    *tokenized.offsets[i],
                    {"global": 1.0, "short": 1.2, "long": 1.0}[kind],
                )
                for i in range(start, stop)
            ]
            checkpoint(kind, stop, losses)
            rows.extend(losses)
            self.windows += 1
        return rows

    def score_comment_effects(
        self, source, tokenized, targets, *, existing_effects, checkpoint
    ):
        assert not targets
        return []


def setup_dataset(monkeypatch, tmp_path):
    items = [
        DatasetItem(
            "one", "def f(a):\n    return a + 1\n", 0.1, metadata={"language": "python"}
        ),
        DatasetItem(
            "two", "def f(a):\n    return a + 1\n", 0.9, metadata={"language": "python"}
        ),
    ]
    monkeypatch.setattr(runner, "load_code_dataset", lambda path: items)
    monkeypatch.setattr(runner, "dataset_name_for_path", lambda path: "unit")
    args = SimpleNamespace(
        task_id=None,
        limit=None,
        output_root=tmp_path / "features",
        recompute_features=False,
        quiet_reuse=True,
        checkpoint_every=1,
        local_block_tokens=4,
        tail_fraction=0.2,
    )
    config = TraceConfiguration(
        window_tokens=32,
        stride_tokens=24,
        context_target_tokens=8,
        comment_target_tokens=8,
        short_context_tokens=2,
        long_context_tokens=16,
    )
    return items, args, config


def test_source_reuse_preserves_current_labels_and_schema(monkeypatch, tmp_path):
    items, args, config = setup_dataset(monkeypatch, tmp_path)
    with LLMTraceCache(tmp_path / "traces.sqlite") as cache:
        first = FakeScorer()
        runner._process_dataset(Path("unit.jsonl"), args, first, config, cache)
        assert first.tokenizations == 1
        assert first.windows > 0
        items[0] = DatasetItem(
            "one", items[0].content, 0.8, metadata={"language": "python"}
        )
        second = FakeScorer()
        runner._process_dataset(Path("unit.jsonl"), args, second, config, cache)
        assert second.tokenizations == second.windows == 0
        args.recompute_features = True
        runner._process_dataset(Path("unit.jsonl"), args, second, config, cache)
        assert second.tokenizations == second.windows == 0
    directory = args.output_root / "unit" / "Qwen-Qwen2.5-Coder-0.5B"
    with (directory / "features.csv").open() as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == [
            "dataset",
            "task_id",
            "readability_score",
            *LLM_FEATURE_NAMES,
        ]
        rows = list(reader)
    assert rows[0]["readability_score"] == "0.8"
    assert "llm__comment__bpb_mean" not in rows[0]
    metadata = json.loads((directory / "metadata.json").read_text())
    assert metadata["complete"] is True
    assert metadata["feature_count"] == 47
    assert "llm__comment__bpb_mean" not in metadata["nonmissing_feature_counts"]


def test_sample_run_cannot_overwrite_complete_table(monkeypatch, tmp_path):
    _, args, config = setup_dataset(monkeypatch, tmp_path)
    with LLMTraceCache(tmp_path / "traces.sqlite") as cache:
        scorer = FakeScorer()
        runner._process_dataset(Path("unit.jsonl"), args, scorer, config, cache)
        complete = (
            args.output_root / "unit" / "Qwen-Qwen2.5-Coder-0.5B" / "features.csv"
        )
        before = complete.read_bytes()
        args.limit = 1
        runner._process_dataset(Path("unit.jsonl"), args, scorer, config, cache)
        assert complete.read_bytes() == before
        metadata = json.loads(
            (complete.parent / "samples" / "metadata.json").read_text()
        )
        assert metadata["complete"] is False
        assert metadata["completed_rows"] == 1


def test_parse_error_is_recorded_and_not_swallowed(monkeypatch, tmp_path):
    items, args, config = setup_dataset(monkeypatch, tmp_path)
    items[:] = [
        DatasetItem(
            "broken", "def f():\n    if:\n", 0.1, metadata={"language": "python"}
        )
    ]
    with LLMTraceCache(tmp_path / "traces.sqlite") as cache, pytest.raises(ValueError):
        runner._process_dataset(Path("unit.jsonl"), args, FakeScorer(), config, cache)
    failure = args.output_root / "unit" / "Qwen-Qwen2.5-Coder-0.5B" / "failures.jsonl"
    assert json.loads(failure.read_text())["task_id"] == "broken"


def test_scalabrino_constructor_uses_raw_source_and_resumes(monkeypatch, tmp_path):
    items, args, config = setup_dataset(monkeypatch, tmp_path)
    source = "public ChartPanel(JFreeChart chart) { this(chart, true); }"
    items[:] = [DatasetItem("Scalabrio4", source, 3.5, metadata={"language": "java"})]
    monkeypatch.setattr(runner, "dataset_name_for_path", lambda path: "scalabrino")

    class RawSourceScorer(FakeScorer):
        def tokenize(self, text):
            assert text == source
            return super().tokenize(text)

    with LLMTraceCache(tmp_path / "traces.sqlite") as cache:
        first = RawSourceScorer()
        runner._process_dataset(Path("unit.jsonl"), args, first, config, cache)
        assert first.tokenizations == 1
        assert first.windows > 0
        second = RawSourceScorer()
        runner._process_dataset(Path("unit.jsonl"), args, second, config, cache)
        assert second.tokenizations == second.windows == 0
    metadata_path = (
        args.output_root / "scalabrino" / "Qwen-Qwen2.5-Coder-0.5B" / "metadata.json"
    )
    metadata = json.loads(metadata_path.read_text())
    assert metadata["completed_rows"] == 1
    assert metadata["complete"] is True


def test_source_form_policy_does_not_enable_lexical_fallback_for_methods():
    item = DatasetItem("method", "public void f() {}", metadata={"language": "java"})
    assert runner._source_policy(item, "scalabrino") == ("java", False, True)
    assert runner._source_policy(item, "schnappinger") == ("java", False, False)
    item.metadata["source_form"] = "method"
    assert runner._source_policy(item, "unit") == ("java", False, True)
    item.metadata["source_form"] = "program"
    assert runner._source_policy(item, "scalabrino") == ("java", False, False)


def test_member_policy_change_reuses_existing_inference_traces(monkeypatch, tmp_path):
    items, args, config = setup_dataset(monkeypatch, tmp_path)
    items[:] = [
        DatasetItem(
            "method",
            "public int f(int a) { return a + 1; }",
            3.5,
            metadata={"language": "java"},
        )
    ]
    with LLMTraceCache(tmp_path / "traces.sqlite") as cache:
        first = FakeScorer()
        runner._process_dataset(Path("unit.jsonl"), args, first, config, cache)
        assert first.tokenizations == 1
        assert first.windows > 0
        monkeypatch.setattr(runner, "dataset_name_for_path", lambda path: "scalabrino")
        second = FakeScorer()
        runner._process_dataset(Path("unit.jsonl"), args, second, config, cache)
        assert second.tokenizations == second.windows == 0


@pytest.mark.parametrize(
    ("dataset", "directory_name", "module", "language", "template"),
    [
        (
            "java_comparative_obfuscation",
            "java-comparative-obfuscation-class-100",
            "source-interference",
            "java",
            "class Demo {{ int f(int a) {{ int value = a + {number}; return value; }} }}",
        ),
        (
            "python_comparative_degradation",
            "python-comparative-degradation-class-100",
            "python-source-interference",
            "python",
            "def f(a):\n    value = a + {number}\n    return value\n",
        ),
    ],
)
def test_constructed_features_cover_pairs_and_incremental_changes(
    monkeypatch, tmp_path, dataset, directory_name, module, language, template
):
    _, args, config = setup_dataset(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "load_code_dataset", load_code_dataset)
    monkeypatch.setattr(runner, "dataset_name_for_path", dataset_name_for_path)
    directory = tmp_path / directory_name
    directory.mkdir()
    rows = []
    for group, position, number in [
        ("g1", 0, 1),
        ("g1", 1, 1),
        ("g2", 0, 2),
        ("g2", 1, 3),
    ]:
        content = template.format(number=number)
        local_path = f"{group}-{position}.{'java' if language == 'java' else 'py'}"
        (directory / local_path).write_text(content, encoding="utf-8")
        rows.append(
            {
                "variant_id": f"{group}-{position}",
                "group_id": group,
                "order": position,
                "stage": "original" if position == 0 else "variant",
                "local_path": local_path,
                "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "source": {"project": "fixture"},
            }
        )

    def write_manifest():
        (directory / "manifest.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )
        (directory / "provenance.json").write_text(
            json.dumps(
                {
                    "module": module,
                    "language": language,
                    "application_mode": "independent-interference",
                    "interference_count": 1,
                    "variant_count_including_originals": len(rows),
                }
            ),
            encoding="utf-8",
        )

    write_manifest()
    items = load_code_dataset(directory)
    assert all(item.readability_score is None for item in items)
    assert all(
        runner._source_policy(item, dataset) == (language, False, False)
        for item in items
    )
    output = args.output_root / dataset / "Qwen-Qwen2.5-Coder-0.5B"
    with LLMTraceCache(tmp_path / "traces.sqlite") as cache:
        first = FakeScorer()
        runner._process_dataset(directory, args, first, config, cache)
        assert first.tokenizations == 3  # Unchanged variant reuses its original.
        with (output / "features.csv").open() as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == [
                "dataset",
                "task_id",
                "readability_score",
                *LLM_FEATURE_NAMES,
            ]
            generated = list(reader)
        assert {row["task_id"] for row in generated} == {
            row["variant_id"] for row in rows
        }
        assert all(row["readability_score"] == "" for row in generated)
        assert all(row["dataset"] == dataset for row in generated)

        # Changing one variant infers only its new content.
        content = template.format(number=4)
        (directory / rows[1]["local_path"]).write_text(content, encoding="utf-8")
        rows[1]["content_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        write_manifest()
        update = FakeScorer()
        runner._process_dataset(directory, args, update, config, cache)
        assert update.tokenizations == 1

        # Dropping a complete source group removes its output rows, not its cache.
        rows[:] = rows[:2]
        write_manifest()
        final = FakeScorer()
        runner._process_dataset(directory, args, final, config, cache)
        assert final.tokenizations == final.windows == 0
        with (output / "features.csv").open() as handle:
            assert {row["task_id"] for row in csv.DictReader(handle)} == {
                "g1-0",
                "g1-1",
            }
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["feature_count"] == 47
    assert metadata["complete"] is True
    assert metadata["completed_rows"] == metadata["expected_rows"] == 2


def test_comment_gain_uses_matching_targets_and_utf8_union():
    target = CommentTarget(0, 1, 1, 2)
    effect = CommentEffect(
        target,
        [TokenLoss(0, 1, 2, 0.5), TokenLoss(1, 1, 2, 0.5)],
        [TokenLoss(0, 1, 2, 1.5), TokenLoss(1, 1, 2, 1.5)],
        1,
    )
    gain, metadata = runner._comment_gain("#é", [effect])
    assert gain == pytest.approx(2 / math.log(2) / 2)
    assert metadata["scored_target_bytes"] == 2
    assert runner._comment_gain("abc", [])[0] is None
