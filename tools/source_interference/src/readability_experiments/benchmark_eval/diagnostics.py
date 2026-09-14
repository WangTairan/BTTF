"""Extract compact repair evidence from the benchmarks' released artifacts."""

from __future__ import annotations

import ast
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_java
from tree_sitter import Language, Parser

from .static_validation import DEFECTS4J_REPOSITORIES, _git_blob

MAX_TEST_CODE_CHARS = 12_000
MAX_FAILURE_CHARS = 4_000


@dataclass(frozen=True)
class RepairEvidence:
    test_code: str
    failure_output: str


def _git_paths(repository: Path, revision: str) -> list[str]:
    completed = subprocess.run(
        ("git", "--git-dir", str(repository), "ls-tree", "-r", "--name-only", revision),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise FileNotFoundError(completed.stderr.strip())
    return completed.stdout.splitlines()


def _method_names(values: list[str]) -> set[str]:
    names = set()
    for value in values:
        pytest_parts = re.findall(r"::([A-Za-z_$][\w$]*)", value)
        if pytest_parts:
            names.add(pytest_parts[-1])
            continue
        match = re.search(r"\.([A-Za-z_][\w]*)\s*$", value)
        if match:
            names.add(match.group(1))
    return names


def _java_methods(source: str, names: set[str]) -> list[str]:
    data = source.encode("utf-8")
    tree = Parser(Language(tree_sitter_java.language())).parse(data)
    found = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == "method_declaration":
            name = node.child_by_field_name("name")
            if (
                name is not None
                and data[name.start_byte : name.end_byte].decode() in names
            ):
                found.append(data[node.start_byte : node.end_byte].decode("utf-8"))
        stack.extend(reversed(node.children))
    return found


def _python_methods(source: str, names: set[str]) -> list[str]:
    tree = ast.parse(source)
    return [
        ast.get_source_segment(source, node) or ""
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in names
    ]


def _compact(
    values: list[tuple[str, str]], file_comment: str, limit: int = MAX_TEST_CODE_CHARS
) -> str:
    blocks = []
    for path, source in values:
        block = f"{file_comment} File: {path}\n{source.strip()}"
        if not blocks and len(block) > limit:
            blocks.append(block[:limit].rstrip())
            break
        if sum(len(item) + 2 for item in blocks) + len(block) > limit:
            break
        blocks.append(block)
    return "\n\n".join(blocks)


def _normalize_failure(value: str) -> str:
    value = re.sub(r"/[^\s:]+/(?:readability-d4j|tmp)[^\s:]*", "<TEMP_PATH>", value)
    lines = [line.rstrip() for line in value.splitlines()]
    # The assertion/error and the nearest frames are useful; framework runner
    # internals at the tail are not.
    return "\n".join(lines[:24]).strip()[:MAX_FAILURE_CHARS]


def _defects4j_evidence(
    record: dict[str, object], workspace: Path, repositories: Path
) -> RepairEvidence:
    triggers = [str(value) for value in record.get("trigger_tests", [])]
    names = _method_names(triggers)
    repository = repositories / DEFECTS4J_REPOSITORIES[str(record["project"])]
    revision = str(record.get("fixed_commit") or record["fixed_revision"])
    paths = _git_paths(repository, revision)
    test_classes = {
        trigger.split("::", 1)[0].split("$", 1)[0].replace(".", "/") + ".java"
        for trigger in triggers
    }
    candidates = [
        path for path in paths if any(path.endswith(value) for value in test_classes)
    ]
    snippets = []
    for path in candidates:
        source = _git_blob(repository, revision, path).decode("utf-8", errors="replace")
        methods = _java_methods(source, names)
        snippets.append((path, "\n\n".join(methods) if methods else source))
    metadata = workspace / str(record["metadata_path"])
    failure_file = next(
        (
            path
            for path in (
                metadata / "trigger_tests" / str(record["bug_id"]),
                metadata / "trigger_tests" / f"{record['bug_id']}.tests",
            )
            if path.is_file()
        ),
        None,
    )
    failure = (
        failure_file.read_text(encoding="utf-8", errors="replace")
        if failure_file
        else ""
    )
    return RepairEvidence(_compact(snippets, "//"), _normalize_failure(failure))


def _cached_test_path(workspace: Path, record: dict[str, object], path: str) -> Path:
    return (
        workspace
        / "data/benchmarks/cache/test-sources"
        / str(record["instance_id"])
        / path
    )


def fetch_bugsinpy_test_sources(
    records: list[dict[str, object]], workspace: Path
) -> int:
    """Download only released test blobs needed by the selected BugsInPy tasks."""
    written = 0
    for record in records:
        if record.get("benchmark") != "bugsinpy":
            continue
        repository_url = str(record.get("repository_url") or "").rstrip("/")
        match = re.match(
            r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repository_url
        )
        if match is None:
            raise ValueError(f"unsupported BugsInPy repository URL: {repository_url}")
        revision = str(record["fixed_revision"])
        for path in map(str, record.get("test_files", [])):
            destination = _cached_test_path(workspace, record, path)
            if destination.is_file():
                continue
            url = f"https://raw.githubusercontent.com/{match.group(1)}/{match.group(2)}/{revision}/{path}"
            request = urllib.request.Request(
                url, headers={"User-Agent": "readability-experiments/0.1"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                content = response.read()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            written += 1
    return written


def _bugsinpy_evidence(
    record: dict[str, object], repositories: Path, workspace: Path
) -> RepairEvidence:
    repository = repositories / f"{record['project']}.git"
    revision = str(record.get("fixed_commit") or record["fixed_revision"])
    commands = [str(value) for value in record.get("test_commands", [])]
    names = _method_names(commands)
    snippets = []
    for path in map(str, record.get("test_files", [])):
        cached = _cached_test_path(workspace, record, path)
        if cached.is_file():
            source = cached.read_text(encoding="utf-8", errors="replace")
        else:
            try:
                source = _git_blob(repository, revision, path).decode(
                    "utf-8", errors="replace"
                )
            except FileNotFoundError:
                continue
        methods = _python_methods(source, names)
        snippets.append((path, "\n\n".join(methods) if methods else source))
    # BugsInPy releases the test command and environment but no captured
    # failing stdout/stderr. Never fabricate an observed failure.
    return RepairEvidence(_compact(snippets, "#"), "")


def repair_evidence(
    record: dict[str, object],
    workspace: Path,
    defects4j_repositories: Path,
    bugsinpy_repositories: Path,
) -> RepairEvidence:
    if record["benchmark"] == "defects4j":
        return _defects4j_evidence(record, workspace, defects4j_repositories)
    return _bugsinpy_evidence(record, bugsinpy_repositories, workspace)
