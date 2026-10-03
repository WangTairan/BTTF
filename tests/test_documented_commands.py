"""Smoke-test documented CLI entry points without running experiments or APIs."""

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [ROOT / "README.md"]
for directory in ("experiments", "src/methods", "tools/source_interference"):
    DOCUMENTS.extend(
        path
        for path in (ROOT / directory).rglob("*.md")
        if "notes" not in path.parts and "build" not in path.parts
    )

MODULES = sorted(
    {
        module
        for document in DOCUMENTS
        for module in re.findall(r"python\s+-m\s+([\w.]+)", document.read_text())
    }
)
TOOL_PROJECT = tomllib.loads(
    (ROOT / "tools/source_interference/pyproject.toml").read_text()
)
MODULES = sorted(
    set(MODULES)
    | {entry.split(":")[0] for entry in TOOL_PROJECT["project"]["scripts"].values()}
)


@pytest.mark.parametrize("module", MODULES)
def test_documented_module_help(module, tmp_path):
    env = dict(os.environ)
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["MPLBACKEND"] = "Agg"
    env["PYTHONPATH"] = os.pathsep.join(
        filter(
            None, (str(ROOT / "tools/source_interference/src"), env.get("PYTHONPATH"))
        )
    )
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower(), result.stdout


@pytest.mark.parametrize(
    "script",
    (
        "figures/scripts/plot_ast_tagged_snippet_extraction.py",
        "figures/scripts/plot_identifier_clustering_motivation.py",
        "figures/scripts/plot_identifier_surprisal_motivation.py",
        "figures/scripts/plot_opaque_month_offset_motivation.py",
    ),
)
def test_documented_direct_figure_command(script, tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    env["MPLBACKEND"] = "Agg"
    result = subprocess.run(
        [sys.executable, script, "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


def test_documented_shell_scripts_exist():
    for document in DOCUMENTS:
        for script in re.findall(r"bash\s+(scripts/[\w.-]+\.sh)", document.read_text()):
            assert (ROOT / script).is_file(), f"{document}: missing {script}"


def test_default_model_download_arguments_do_not_require_model_names(monkeypatch):
    from src.methods.readability_model.runners.download_embedding_model import parse_args

    monkeypatch.setattr(sys, "argv", ["download_embedding_model"])
    assert parse_args().models == []


def test_model_download_arguments_reject_unknown_names(monkeypatch):
    from src.methods.readability_model.runners.download_embedding_model import parse_args

    monkeypatch.setattr(sys, "argv", ["download_embedding_model", "unknown-model"])
    with pytest.raises(SystemExit) as error:
        parse_args()
    assert error.value.code == 2
