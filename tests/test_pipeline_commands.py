"""Verify maintenance command routing without computing embeddings or features."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("all_constructed", ("0", "1"))
def test_refresh_routes_models_and_rebuilds_after_embeddings(tmp_path, all_constructed):
    log = tmp_path / "commands.jsonl"
    interpreter = tmp_path / "capture-python"
    interpreter.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['COMMAND_LOG'], 'a') as handle:\n"
        "    handle.write(json.dumps(sys.argv[1:]) + '\\n')\n"
    )
    interpreter.chmod(0o755)
    env = dict(os.environ)
    env.update(
        PYTHON_BIN=str(interpreter),
        COMMAND_LOG=str(log),
        INCLUDE_CONSTRUCTED_ALL_MODELS=all_constructed,
        BASE_ONLY="0",
    )
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/refresh_readability_after_extractor_change.sh")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    modules = [command[1].rsplit(".", 1)[-1] for command in commands]
    embeddings = [
        cmd for cmd, module in zip(commands, modules) if module == "embeddings"
    ]
    features = [
        cmd for cmd, module in zip(commands, modules) if module == "embedding_features"
    ]
    expected_count = 5 if all_constructed == "1" else 6
    assert len(embeddings) == len(features) == expected_count
    assert max(i for i, module in enumerate(modules) if module == "embeddings") < min(
        i for i, module in enumerate(modules) if module == "features"
    )
    for command in embeddings + features:
        datasets = command[2 : command.index("--embedding-model")]
        if all_constructed == "1":
            assert len(datasets) == 8
            assert (
                sum(path.startswith("datasets/constructed/") for path in datasets) == 2
            )
        else:
            assert len(datasets) in (2, 6)
            if len(datasets) == 2:
                assert command[command.index("--embedding-model") + 1] == (
                    "jinaai/jina-embeddings-v2-base-code"
                )
    assert all("--replace-sources" in command for command in embeddings)
    assert all("--resume" in command for command in features)


def test_refresh_rejects_invalid_scope_before_running(tmp_path):
    env = dict(os.environ, INCLUDE_CONSTRUCTED_ALL_MODELS="invalid")
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/refresh_readability_after_extractor_change.sh")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2
    assert "must be 0 or 1" in result.stderr


@pytest.mark.parametrize(
    "requested_datasets",
    [
        [],
        ["datasets/constructed/python-comparative-degradation-class-100"],
        [
            "datasets/constructed/java-comparative-obfuscation-class-100",
            "datasets/constructed/python-comparative-degradation-class-100",
        ],
    ],
)
def test_llm_pipeline_only_generates_requested_llm_features(
    tmp_path, requested_datasets
):
    log = tmp_path / "commands.jsonl"
    interpreter = tmp_path / "capture-python"
    interpreter.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['COMMAND_LOG'], 'a') as handle:\n"
        "    handle.write(json.dumps(sys.argv[1:]) + '\\n')\n"
    )
    interpreter.chmod(0o755)
    command = ["bash", str(ROOT / "scripts/run_llm_feature_tables.sh")]
    command.extend(requested_datasets)
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=dict(os.environ, PYTHON_BIN=str(interpreter), COMMAND_LOG=str(log)),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(commands) == 1
    args = commands[0]
    assert args[:2] == ["-m", "src.methods.readability_model.runners.llm_surprisal_features"]
    datasets = args[2 : args.index("--model")]
    if requested_datasets:
        assert datasets == requested_datasets
    else:
        assert len(datasets) == 8
        assert datasets[-2:] == [
            "datasets/constructed/java-comparative-obfuscation-class-100",
            "datasets/constructed/python-comparative-degradation-class-100",
        ]
    assert args[args.index("--context-target-tokens") + 1] == "32"
    assert args[args.index("--comment-target-tokens") + 1] == "128"
    assert args[args.index("--checkpoint-every") + 1] == "1"
