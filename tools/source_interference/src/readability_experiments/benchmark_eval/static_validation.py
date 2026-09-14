"""Static, reproducible validation of interference applicability on repair bugs.

This stage deliberately does not compile projects, run tests, or call an LLM.  It
reads the buggy and fixed source blobs directly from the benchmark repositories,
locates the single changed top-level class, and applies every registered
interference independently with a fixed seed.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

from readability_data.java_degradation.registry import (
    INTERFERENCE_CATALOG as JAVA_INTERFERENCES,
)
from readability_data.python_degradation.registry import ORDERED as PYTHON_INTERFERENCES
from readability_data.shared.contracts import InterferenceContext

from .class_source import transform_java_class, transform_python_class

DEFECTS4J_REPOSITORIES = {
    "Chart": "jfreechart.git",
    "Cli": "commons-cli.git",
    "Closure": "closure-compiler.git",
    "Codec": "commons-codec.git",
    "Collections": "commons-collections.git",
    "Compress": "commons-compress.git",
    "Csv": "commons-csv.git",
    "Gson": "gson.git",
    "JacksonCore": "jackson-core.git",
    "JacksonDatabind": "jackson-databind.git",
    "JacksonXml": "jackson-dataformat-xml.git",
    "Jsoup": "jsoup.git",
    "JxPath": "commons-jxpath.git",
    "Lang": "commons-lang.git",
    "Math": "commons-math.git",
    "Mockito": "mockito.git",
    "Time": "joda-time.git",
}


@dataclass(frozen=True)
class SourcePair:
    buggy: bytes
    fixed: bytes
    path: str
    class_name: str


def _git_blob(repository: Path, revision: str, path: str) -> bytes:
    completed = subprocess.run(
        ("git", "--git-dir", str(repository), "show", f"{revision}:{path}"),
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise FileNotFoundError(f"cannot read {revision}:{path}: {message}")
    return completed.stdout


def _changed_lines(before: str, after: str) -> tuple[set[int], set[int]]:
    """Return one-based line numbers touched on each side of a textual diff."""
    left = before.splitlines()
    right = after.splitlines()
    left_lines: set[int] = set()
    right_lines: set[int] = set()
    for tag, i1, i2, j1, j2 in SequenceMatcher(
        None, left, right, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            continue
        left_lines.update(range(i1 + 1, i2 + 1))
        right_lines.update(range(j1 + 1, j2 + 1))
        # Insertions/deletions occur at a boundary; include the adjacent line so
        # class containment can still be determined on the empty side.
        if i1 == i2 and left:
            left_lines.add(min(i1 + 1, len(left)))
        if j1 == j2 and right:
            right_lines.add(min(j1 + 1, len(right)))
    return left_lines, right_lines


def _python_changed_class(before: str, after: str) -> str:
    before_tree = ast.parse(before)
    after_tree = ast.parse(after)
    before_lines, after_lines = _changed_lines(before, after)

    def overlap(module: ast.Module, changed: set[int]) -> Counter[str]:
        counts: Counter[str] = Counter()
        for node in module.body:
            if not isinstance(node, ast.ClassDef):
                continue
            counts[node.name] += sum(
                node.lineno <= line <= (node.end_lineno or node.lineno)
                for line in changed
            )
        return counts

    overlaps = overlap(before_tree, before_lines) + overlap(after_tree, after_lines)
    if not overlaps:
        raise ValueError("the developer change does not touch a top-level class")
    # A single-file patch may also touch helpers or another class.  Select the
    # class containing the most changed lines, with a lexical tie-break, so the
    # rule is deterministic and requires no manual labels.
    return min(overlaps, key=lambda name: (-overlaps[name], name))


def _java_class_name(record: dict[str, object]) -> str:
    names = {
        str(name).split("$")[0].rsplit(".", 1)[-1]
        for name in record.get("modified_classes", [])
    }
    if len(names) == 1:
        return next(iter(names))
    path = str(record["production_source_paths"][0])
    fallback = Path(path).stem
    if not names:
        return fallback
    if fallback in names:
        return fallback
    raise ValueError(f"ambiguous modified classes: {sorted(names)!r}")


def _repository(
    record: dict[str, object], defects4j_repos: Path, bugsinpy_repos: Path
) -> Path:
    if record["benchmark"] == "defects4j":
        return defects4j_repos / DEFECTS4J_REPOSITORIES[str(record["project"])]
    return bugsinpy_repos / f"{record['project']}.git"


def load_source_pair(
    record: dict[str, object],
    defects4j_repos: Path,
    bugsinpy_repos: Path,
    source_cache: Path | None = None,
) -> SourcePair:
    paths = list(record["production_source_paths"])
    if len(paths) != 1:
        raise ValueError(f"expected one production source path, found {len(paths)}")
    path = str(paths[0])
    cached = source_cache / str(record["instance_id"]) if source_cache else None
    if cached and (cached / "buggy").is_file() and (cached / "fixed").is_file():
        buggy = (cached / "buggy").read_bytes()
        fixed = (cached / "fixed").read_bytes()
    else:
        repository = _repository(record, defects4j_repos, bugsinpy_repos)
        if not repository.is_dir():
            raise FileNotFoundError(f"repository not materialized: {repository}")
        buggy_revision = record.get("buggy_commit") or record["buggy_revision"]
        fixed_revision = record.get("fixed_commit") or record["fixed_revision"]
        buggy = _git_blob(repository, str(buggy_revision), path)
        fixed = _git_blob(repository, str(fixed_revision), path)
    if record["language"] == "java":
        class_name = _java_class_name(record)
        # Parsing and exact top-level containment are checked by this identity transform.
        transform_java_class(buggy, class_name, lambda value: value)
        transform_java_class(fixed, class_name, lambda value: value)
    else:
        class_name = _python_changed_class(buggy.decode("utf-8"), fixed.decode("utf-8"))
        transform_python_class(buggy.decode("utf-8"), class_name, lambda value: value)
        transform_python_class(fixed.decode("utf-8"), class_name, lambda value: value)
    return SourcePair(buggy, fixed, path, class_name)


def _apply(
    language: str,
    source: bytes,
    class_name: str,
    plugin: object,
    context: InterferenceContext,
) -> bytes:
    if language == "java":
        return transform_java_class(
            source, class_name, lambda unit: plugin.apply(unit, context).content
        )
    text = source.decode("utf-8")
    return transform_python_class(
        text, class_name, lambda unit: plugin.apply(unit, context).content
    ).encode("utf-8")


def validate_record_static(
    record: dict[str, object],
    defects4j_repos: Path,
    bugsinpy_repos: Path,
    seed: int,
    source_cache: Path | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": 1,
        "instance_id": record["instance_id"],
        "benchmark": record["benchmark"],
        "language": record["language"],
        "project": record["project"],
        "seed": seed,
    }
    if not record.get("single_production_source_file"):
        result.update(status="excluded", reason="not_single_production_source_file")
        return result
    try:
        pair = load_source_pair(record, defects4j_repos, bugsinpy_repos, source_cache)
    except Exception as error:
        result.update(
            status="source_error", reason=type(error).__name__, error=str(error)
        )
        return result

    plugins = (
        JAVA_INTERFERENCES if record["language"] == "java" else PYTHON_INTERFERENCES
    )
    identity = f"{record['instance_id']}:{pair.path}:{pair.class_name}"
    conditions = []
    for plugin in plugins:
        condition: dict[str, object] = {"interference": str(plugin.slug)}
        try:
            buggy = _apply(
                str(record["language"]),
                pair.buggy,
                pair.class_name,
                plugin,
                InterferenceContext(seed, identity),
            )
            fixed = _apply(
                str(record["language"]),
                pair.fixed,
                pair.class_name,
                plugin,
                InterferenceContext(seed, identity),
            )
            buggy_changed = buggy != pair.buggy
            fixed_changed = fixed != pair.fixed
            condition.update(
                status="usable"
                if buggy_changed and fixed_changed
                else "not_applicable",
                buggy_changed=buggy_changed,
                fixed_changed=fixed_changed,
                buggy_sha256=hashlib.sha256(buggy).hexdigest(),
                fixed_sha256=hashlib.sha256(fixed).hexdigest(),
            )
        except Exception as error:
            condition.update(
                status="transform_error",
                error_type=type(error).__name__,
                error=str(error),
            )
        conditions.append(condition)
    result.update(
        status="usable",
        source_path=pair.path,
        class_name=pair.class_name,
        condition_counts=dict(Counter(str(item["status"]) for item in conditions)),
        conditions=conditions,
    )
    return result


def _read_jsonl(path: Path) -> Iterable[dict[str, object]]:
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def summarize(records: list[dict[str, object]], seed: int) -> dict[str, object]:
    by_benchmark: dict[str, Counter[str]] = defaultdict(Counter)
    by_interference: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        by_benchmark[str(record["benchmark"])][str(record["status"])] += 1
        for condition in record.get("conditions", []):
            by_interference[str(condition["interference"])][
                str(condition["status"])
            ] += 1
    return {
        "schema_version": 1,
        "seed": seed,
        "task_count": len(records),
        "task_status_by_benchmark": {
            key: dict(sorted(value.items()))
            for key, value in sorted(by_benchmark.items())
        },
        "condition_status_by_interference": {
            key: dict(sorted(value.items()))
            for key, value in sorted(by_interference.items())
        },
        "usable_task_count": sum(record["status"] == "usable" for record in records),
        "usable_condition_count": sum(
            condition["status"] == "usable"
            for record in records
            for condition in record.get("conditions", [])
        ),
    }
