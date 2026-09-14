"""Reproducible end-to-end validation for one Java and one Python bug."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from ..common.paths import default_workspace
from .external_validation import _java_home
from .validation import PreparedInstance, validate_prepared_instance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-benchmark-pilot",
        description="Validate all readability interferences on prepared Lang-1 and PySnooper-2 worktrees.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--seed", type=int, default=20260823)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--maven", default="mvn", help="Maven executable or path")
    parser.add_argument("--java-home", type=Path, help="JDK 11 installation directory")
    parser.add_argument(
        "--python-bin", type=Path, help="Prepared BugsInPy Python interpreter"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/experiments/agent-readability/validation-pilot"),
    )
    return parser


def validate_pilots(
    workspace: Path,
    output: Path,
    seed: int,
    timeout: int,
    *,
    maven: str = "mvn",
    java_home: Path | None = None,
    python_bin: Path | None = None,
) -> dict[str, object]:
    benchmark_root = workspace / "data" / "benchmarks"
    java_worktree = benchmark_root / "worktrees" / "defects4j__Lang__1"
    python_worktree = benchmark_root / "worktrees" / "bugsinpy__PySnooper__2"
    maven_cache = benchmark_root / "cache" / "m2"
    python = python_bin or benchmark_root / "envs" / "python-3.8" / "bin" / "python"
    maven_executable = shutil.which(maven)
    if maven_executable is None:
        raise ValueError(f"Maven executable not found: {maven}; provide --maven")
    detected_java_home = str(java_home) if java_home is not None else _java_home()
    if not detected_java_home or not (Path(detected_java_home) / "bin/java").is_file():
        raise ValueError("JDK 11 not found; provide --java-home or configure JAVA_HOME")
    if not python.is_file():
        raise ValueError(
            f"BugsInPy interpreter not found: {python}; provide --python-bin"
        )
    java = PreparedInstance(
        instance_id="defects4j__Lang__1",
        language="java",
        class_name="NumberUtils",
        source_path=Path(
            "src/main/java/org/apache/commons/lang3/math/NumberUtils.java"
        ),
        buggy_root=java_worktree / "buggy",
        fixed_root=java_worktree / "fixed",
        test_command=(
            maven_executable,
            "-q",
            f"-Dmaven.repo.local={maven_cache}",
            "-Dtest=org.apache.commons.lang3.math.NumberUtilsTest#TestLang747",
            "test",
        ),
        environment={
            "JAVA_HOME": detected_java_home,
            "TZ": "America/Los_Angeles",
        },
        expected_failure_markers=("TestLang747", "NumberFormatException"),
    )
    python_instance = PreparedInstance(
        instance_id="bugsinpy__PySnooper__2",
        language="python",
        class_name="Tracer",
        source_path=Path("pysnooper/tracer.py"),
        buggy_root=python_worktree / "buggy",
        fixed_root=python_worktree / "fixed",
        test_command=(
            str(python),
            "-m",
            "pytest",
            "-q",
            "-s",
            "tests/test_pysnooper.py::test_custom_repr_single",
        ),
        environment={"PYTHONDONTWRITEBYTECODE": "1"},
        expected_failure_markers=(
            "test_custom_repr_single",
            "unexpected keyword argument 'custom_repr'",
        ),
    )
    reports = {
        "java": validate_prepared_instance(
            java, output / java.instance_id, seed=seed, timeout=timeout
        ),
        "python": validate_prepared_instance(
            python_instance,
            output / python_instance.instance_id,
            seed=seed,
            timeout=timeout,
        ),
    }
    summary = {
        "schema_version": 1,
        "seed": seed,
        "instances": reports,
        "valid_condition_count_including_originals": sum(
            int(report["valid_condition_count_including_original"])
            for report in reports.values()
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()
    output = args.output if args.output.is_absolute() else workspace / args.output
    print(
        json.dumps(
            validate_pilots(
                workspace,
                output,
                args.seed,
                args.timeout,
                maven=args.maven,
                java_home=args.java_home,
                python_bin=args.python_bin,
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
