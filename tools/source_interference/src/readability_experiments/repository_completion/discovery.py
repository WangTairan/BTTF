"""Discover recent, hash-pinned method and statement completion targets."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from readability_data.java_degradation.interferences.core.java import tree, walk
from readability_experiments.common.paths import default_workspace

from .catalog import REPOSITORIES, RepositorySpec

SCHEMA_VERSION = 1
DEFAULT_PER_LANGUAGE = 25
MIN_METHOD_LINES = 3
MAX_METHOD_LINES = 120
MAX_STATEMENT_LINES = 20


@dataclass(frozen=True)
class SourceSpan:
    start_byte: int
    end_byte: int
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True)
class FunctionCandidate:
    symbol: str
    qualified_name: str
    method: SourceSpan
    statements: tuple[SourceSpan, ...]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _verify_repo(repo: Path, spec: RepositorySpec) -> None:
    if not (repo / ".git").is_dir():
        raise FileNotFoundError(f"repository is not prepared: {repo}")
    head = _git(repo, "rev-parse", "HEAD")
    if head != spec.pinned_commit:
        raise ValueError(f"{spec.repository_id} is at {head}; expected {spec.pinned_commit}")
    status = _git(repo, "status", "--porcelain", "--untracked-files=no")
    if status:
        raise ValueError(f"tracked files are modified in {spec.repository_id}:\n{status}")


def _byte_offsets(source: str) -> list[int]:
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line.encode("utf-8")))
    return offsets


def _python_candidates(source: str) -> list[FunctionCandidate]:
    module = ast.parse(source)
    encoded = source.encode("utf-8")
    offsets = _byte_offsets(source)
    candidates: list[FunctionCandidate] = []

    def byte_position(line: int, column: int) -> int:
        return offsets[line - 1] + column

    def span(node: ast.AST) -> SourceSpan:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            raise ValueError("Python AST node has no source span")
        start = byte_position(node.lineno, node.col_offset)  # type: ignore[attr-defined]
        end = byte_position(node.end_lineno, node.end_col_offset)  # type: ignore[attr-defined]
        return SourceSpan(
            start_byte=start,
            end_byte=end,
            start_line=node.lineno,  # type: ignore[attr-defined]
            end_line=node.end_lineno,  # type: ignore[attr-defined]
            text=encoded[start:end].decode("utf-8"),
        )

    def statement_nodes(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
        found: list[ast.stmt] = []

        def visit(node: ast.AST) -> None:
            if node is not function and isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                return
            if isinstance(node, ast.stmt) and node is not function:
                if not (
                    isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    found.append(node)
            for child in ast.iter_child_nodes(node):
                visit(child)

        for item in function.body:
            visit(item)
        return found

    def traverse(body: Iterable[ast.stmt], parents: tuple[str, ...]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                traverse(node.body, (*parents, node.name))
                continue
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.body:
                continue
            method_start = byte_position(node.body[0].lineno, node.body[0].col_offset)
            last = node.body[-1]
            method_end = byte_position(last.end_lineno, last.end_col_offset)
            method = SourceSpan(
                start_byte=method_start,
                end_byte=method_end,
                start_line=node.body[0].lineno,
                end_line=last.end_lineno,
                text=encoded[method_start:method_end].decode("utf-8"),
            )
            statements = tuple(span(item) for item in statement_nodes(node))
            qualified = ".".join((*parents, node.name))
            candidates.append(FunctionCandidate(node.name, qualified, method, statements))
            # Nested functions are intentionally excluded: their runtime test mapping is
            # ambiguous, and they are already visible inside the enclosing completion.

    traverse(module.body, ())
    return candidates


JAVA_STATEMENT_TYPES = {
    "assert_statement",
    "break_statement",
    "continue_statement",
    "do_statement",
    "enhanced_for_statement",
    "expression_statement",
    "for_statement",
    "if_statement",
    "local_variable_declaration",
    "return_statement",
    "switch_expression",
    "synchronized_statement",
    "throw_statement",
    "try_statement",
    "while_statement",
}


def _java_candidates(source: str) -> list[FunctionCandidate]:
    encoded = source.encode("utf-8")
    root = tree(encoded).root_node
    if root.has_error:
        raise ValueError("Tree-sitter could not parse Java source")
    candidates: list[FunctionCandidate] = []
    for node in walk(root):
        if node.type != "method_declaration":
            continue
        name = node.child_by_field_name("name")
        body = node.child_by_field_name("body")
        if name is None or body is None or not body.named_children:
            continue
        symbol = encoded[name.start_byte : name.end_byte].decode("utf-8")
        method_start = body.named_children[0].start_byte
        method_end = body.named_children[-1].end_byte
        method = SourceSpan(
            start_byte=method_start,
            end_byte=method_end,
            start_line=body.named_children[0].start_point.row + 1,
            end_line=body.named_children[-1].end_point.row + 1,
            text=encoded[method_start:method_end].decode("utf-8"),
        )
        statements = []
        for item in walk(body):
            if item.type not in JAVA_STATEMENT_TYPES:
                continue
            statements.append(
                SourceSpan(
                    start_byte=item.start_byte,
                    end_byte=item.end_byte,
                    start_line=item.start_point.row + 1,
                    end_line=item.end_point.row + 1,
                    text=encoded[item.start_byte : item.end_byte].decode("utf-8"),
                )
            )
        signature = encoded[node.start_byte : body.start_byte].decode("utf-8")
        signature = " ".join(signature.split())
        candidates.append(FunctionCandidate(symbol, signature, method, tuple(statements)))
    return candidates


def discover_functions(source: str, language: str) -> list[FunctionCandidate]:
    if language == "python":
        return _python_candidates(source)
    if language == "java":
        return _java_candidates(source)
    raise ValueError(f"unsupported language: {language}")


def _recent_source_files(repo: Path, spec: RepositorySpec) -> list[str]:
    output = _git(
        repo,
        "log",
        f"--since={spec.since_date}",
        "--format=",
        "--name-only",
        "--diff-filter=AM",
        "--",
        *spec.source_roots,
    )
    suffix = ".java" if spec.language == "java" else ".py"
    return sorted(
        {
            line
            for line in output.splitlines()
            if line.endswith(suffix) and (repo / line).is_file()
        }
    )


def _blame(repo: Path, commit: str, source_path: str) -> dict[int, tuple[str, int]]:
    output = _git(repo, "blame", "--line-porcelain", commit, "--", source_path)
    result: dict[int, tuple[str, int]] = {}
    current_commit = ""
    final_line = 0
    authored = 0
    header = re.compile(r"^([0-9a-f^]{40}) \d+ (\d+)(?: \d+)?$")
    for line in output.splitlines():
        match = header.match(line)
        if match:
            current_commit = match.group(1).lstrip("^")
            final_line = int(match.group(2))
            authored = 0
        elif line.startswith("author-time "):
            authored = int(line.removeprefix("author-time "))
        elif line.startswith("\t"):
            if len(current_commit) != 40 or not authored:
                raise ValueError(f"incomplete blame record for {source_path}:{final_line}")
            result[final_line] = (current_commit, authored)
    return result


def _latest_touch(
    blame: dict[int, tuple[str, int]], start_line: int, end_line: int
) -> tuple[str, int]:
    touches = [blame[line] for line in range(start_line, end_line + 1) if line in blame]
    if not touches:
        raise ValueError(f"no blame information for lines {start_line}-{end_line}")
    return max(touches, key=lambda item: (item[1], item[0]))


def _select_statement(
    candidate: FunctionCandidate,
    blame: dict[int, tuple[str, int]],
    since_timestamp: int,
) -> tuple[SourceSpan, str, int] | None:
    ranked: list[tuple[int, int, int, SourceSpan, str]] = []
    for statement in candidate.statements:
        line_count = statement.end_line - statement.start_line + 1
        if line_count > MAX_STATEMENT_LINES or not statement.text.strip():
            continue
        commit, timestamp = _latest_touch(blame, statement.start_line, statement.end_line)
        if timestamp < since_timestamp:
            continue
        # Prefer the newest compact statement. A longer span is used only when it
        # is the recent semantic change itself rather than an enclosing block.
        ranked.append((timestamp, -line_count, len(statement.text), statement, commit))
    if not ranked:
        return None
    timestamp, _, _, statement, commit = max(
        ranked, key=lambda item: (item[0], item[1], item[2])
    )
    return statement, commit, timestamp


def _cochanged_test_paths(
    repo: Path, spec: RepositorySpec, commits: tuple[str, ...]
) -> list[str]:
    suffix = ".java" if spec.language == "java" else ".py"
    paths: list[str] = []
    for commit in commits:
        output = _git(
            repo,
            "show",
            "--format=",
            "--name-only",
            "--diff-filter=AM",
            commit,
            "--",
            *spec.test_roots,
        )
        paths.extend(
            line
            for line in output.splitlines()
            if line.endswith(suffix) and (repo / line).is_file()
        )
    return list(dict.fromkeys(paths))


def _test_paths(
    repo: Path,
    spec: RepositorySpec,
    source_path: str,
    symbol: str,
    origin_commits: tuple[str, ...],
) -> list[str]:
    escaped = re.compile(rf"\b{re.escape(symbol)}\b")
    source_stem = Path(source_path).stem
    cochanged = _cochanged_test_paths(repo, spec, origin_commits)
    referenced: list[str] = []
    same_module: list[str] = []
    for root_name in spec.test_roots:
        root = repo / root_name
        if not root.is_dir():
            continue
        suffix = "*.java" if spec.language == "java" else "*.py"
        for path in root.rglob(suffix):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if not escaped.search(text):
                continue
            relative = path.relative_to(repo).as_posix()
            same_class = path.stem in {source_stem, f"{source_stem}Test"}
            referenced.append(relative)
            if same_class:
                same_module.append(relative)
    referenced = list(dict.fromkeys(sorted(same_module) + sorted(referenced)))
    relevant_cochanged = [
        path
        for path in cochanged
        if path in referenced
        or Path(path).stem in {source_stem, f"{source_stem}Test"}
    ]
    # A broad refactor may touch many unrelated tests in the same commit.
    # Never mix those into a focused command when a module- or symbol-matched
    # regression test is available.
    if relevant_cochanged:
        return list(dict.fromkeys(relevant_cochanged + referenced))[:3]
    if referenced:
        return referenced[:3]
    return cochanged[:3]


def _test_command(spec: RepositorySpec, paths: list[str]) -> list[str]:
    if spec.language == "java":
        classes = ",".join(Path(path).stem for path in paths)
        return [
            "mvn",
            "-q",
            "-Dmaven.repo.local=${WORKSPACE}/data/cache/m2",
            "-Drat.skip=true",
            "-DskipTests=false",
            f"-Dtest={classes}",
            "test",
        ]
    return ["${REPOSITORY}/.venv/bin/python", "-m", "pytest", "-q", *paths]


def _span_record(span: SourceSpan, source: str) -> dict[str, Any]:
    encoded = source.encode("utf-8")
    holed = encoded[: span.start_byte] + b"<READABILITY_HOLE>" + encoded[span.end_byte :]
    return {
        "start_byte": span.start_byte,
        "end_byte": span.end_byte,
        "start_line": span.start_line,
        "end_line": span.end_line,
        "line_count": span.end_line - span.start_line + 1,
        "byte_count": len(span.text.encode("utf-8")),
        "completion_sha256": _sha256_text(span.text),
        "hole_context_sha256": _sha256_bytes(holed),
    }


def discover_repository(
    repo: Path, spec: RepositorySpec, *, limit: int
) -> list[dict[str, Any]]:
    _verify_repo(repo, spec)
    since = date.fromisoformat(spec.since_date)
    since_timestamp = int(
        datetime(since.year, since.month, since.day, tzinfo=timezone.utc).timestamp()
    )
    discovered: list[dict[str, Any]] = []
    commit_dates: dict[str, str] = {}
    for source_path in _recent_source_files(repo, spec):
        source = (repo / source_path).read_text(encoding="utf-8")
        source_hash = _sha256_text(source)
        blame = _blame(repo, spec.pinned_commit, source_path)
        for candidate in discover_functions(source, spec.language):
            method_lines = candidate.method.end_line - candidate.method.start_line + 1
            if not MIN_METHOD_LINES <= method_lines <= MAX_METHOD_LINES:
                continue
            method_commit, method_timestamp = _latest_touch(
                blame, candidate.method.start_line, candidate.method.end_line
            )
            if method_timestamp < since_timestamp:
                continue
            statement = _select_statement(candidate, blame, since_timestamp)
            if statement is None:
                continue
            statement_span, statement_commit, statement_timestamp = statement
            tests = _test_paths(
                repo,
                spec,
                source_path,
                candidate.symbol,
                (method_commit, statement_commit),
            )
            if not tests:
                continue
            for commit in (method_commit, statement_commit):
                commit_dates.setdefault(commit, _git(repo, "show", "-s", "--format=%cs", commit))
            target_key = (
                f"{spec.repository_id}:{spec.pinned_commit}:{source_path}:"
                f"{candidate.qualified_name}:{candidate.method.start_line}"
            )
            discovered.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "target_id": _sha256_text(target_key)[:16],
                    "repository_id": spec.repository_id,
                    "repository_url": spec.repository_url,
                    "license_spdx": spec.license_spdx,
                    "language": spec.language,
                    "pinned_commit": spec.pinned_commit,
                    "source_path": source_path,
                    "source_sha256": source_hash,
                    "symbol": candidate.symbol,
                    "qualified_name": candidate.qualified_name,
                    "method_origin_commit": method_commit,
                    "method_origin_date": commit_dates[method_commit],
                    "statement_origin_commit": statement_commit,
                    "statement_origin_date": commit_dates[statement_commit],
                    "method_span": _span_record(candidate.method, source),
                    "statement_span": _span_record(statement_span, source),
                    "test_paths": tests,
                    "test_selection": {
                        "cochanged_commit_tests_prioritized": True,
                        "symbol_reference_tests_used_as_fallback": True,
                    },
                    "test_command": _test_command(spec, tests),
                    "selection": {
                        "since_date": spec.since_date,
                        "method_last_touch_timestamp": method_timestamp,
                        "statement_last_touch_timestamp": statement_timestamp,
                    },
                }
            )
    discovered.sort(
        key=lambda row: (
            -int(row["selection"]["method_last_touch_timestamp"]),
            row["source_path"],
            int(row["method_span"]["start_line"]),
        )
    )
    # Repeated one-line delegators are common in utility libraries. Keep the
    # pool content-diverse so the same answer is not counted as a new target
    # merely because it occurs in another anonymous class or overload.
    unique: list[dict[str, Any]] = []
    method_hashes: set[str] = set()
    statement_hashes: set[str] = set()
    for row in discovered:
        method_hash = str(row["method_span"]["completion_sha256"])
        statement_hash = str(row["statement_span"]["completion_sha256"])
        if method_hash in method_hashes or statement_hash in statement_hashes:
            continue
        method_hashes.add(method_hash)
        statement_hashes.add(statement_hash)
        unique.append(row)
        if len(unique) == limit:
            break
    return unique


def verify_manifest(workspace: Path, manifest: Path) -> dict[str, Any]:
    """Verify repository pins and every source, completion, and hole hash."""
    specs = {spec.repository_id: spec for spec in REPOSITORIES}
    rows = [
        json.loads(line)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    target_ids: set[str] = set()
    verified_repositories: set[str] = set()
    source_cache: dict[tuple[str, str], tuple[str, bytes]] = {}
    for row in rows:
        repository_id = str(row["repository_id"])
        spec = specs.get(repository_id)
        if spec is None:
            raise ValueError(f"unknown repository in manifest: {repository_id}")
        repo = workspace / "data/raw/completion_pilot" / spec.directory
        if repository_id not in verified_repositories:
            _verify_repo(repo, spec)
            verified_repositories.add(repository_id)
        target_id = str(row["target_id"])
        if target_id in target_ids:
            raise ValueError(f"duplicate target_id: {target_id}")
        target_ids.add(target_id)
        source_path = str(row["source_path"])
        cache_key = (repository_id, source_path)
        if cache_key not in source_cache:
            source_text = (repo / source_path).read_text(encoding="utf-8")
            source_cache[cache_key] = (source_text, source_text.encode("utf-8"))
        source, encoded = source_cache[cache_key]
        if _sha256_text(source) != row["source_sha256"]:
            raise ValueError(f"source hash mismatch for {repository_id}:{source_path}")
        for granularity in ("method_span", "statement_span"):
            span = row[granularity]
            start = int(span["start_byte"])
            end = int(span["end_byte"])
            completion = encoded[start:end]
            if _sha256_bytes(completion) != span["completion_sha256"]:
                raise ValueError(
                    f"completion hash mismatch for {target_id}:{granularity}"
                )
            holed = encoded[:start] + b"<READABILITY_HOLE>" + encoded[end:]
            if _sha256_bytes(holed) != span["hole_context_sha256"]:
                raise ValueError(f"hole hash mismatch for {target_id}:{granularity}")
    return {
        "verified": True,
        "target_count": len(rows),
        "span_count": len(rows) * 2,
        "repository_count": len(verified_repositories),
        "manifest_sha256": _sha256_bytes(manifest.read_bytes()),
    }


def build_manifest(workspace: Path, output: Path, per_language: int) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    for spec in REPOSITORIES:
        repo = workspace / "data/raw/completion_pilot" / spec.directory
        targets.extend(discover_repository(repo, spec, limit=per_language))
    counts = {
        language: sum(row["language"] == language for row in targets)
        for language in ("java", "python")
    }
    if any(value < per_language for value in counts.values()):
        raise RuntimeError(
            f"insufficient recent validated candidates before native tests: {counts}; "
            f"requested {per_language} per language"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in targets),
        encoding="utf-8",
    )
    manifest_hash = _sha256_bytes(output.read_bytes())
    verification = verify_manifest(workspace, output)
    report = {
        "schema_version": SCHEMA_VERSION,
        "candidate_count": len(targets),
        "candidate_count_by_language": counts,
        "hole_granularities": ["method_body", "statement"],
        "maximum_hole_configuration_count": len(targets) * 2,
        "manifest_sha256": manifest_hash,
        "manifest": output.name,
        "verification": verification,
        "selection": {
            "since_date": min(spec.since_date for spec in REPOSITORIES),
            "earliest_selected_origin_date": min(
                row["method_origin_date"] for row in targets
            ),
            "latest_selected_origin_date": max(
                row["method_origin_date"] for row in targets
            ),
            "requires_test_reference": True,
            "unique_method_completions": len(
                {row["method_span"]["completion_sha256"] for row in targets}
            ),
            "unique_statement_completions": len(
                {row["statement_span"]["completion_sha256"] for row in targets}
            ),
        },
    }
    report_path = output.with_suffix(".report.json")
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover recent method and statement completion targets."
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--per-language", type=int, default=DEFAULT_PER_LANGUAGE)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="verify the existing output manifest without rediscovering targets",
    )
    args = parser.parse_args()
    if args.per_language < 1:
        parser.error("--per-language must be positive")
    workspace = args.workspace.resolve()
    output = args.output or (
        workspace
        / "data/experiments/recent-repository-completion/candidate_manifest.jsonl"
    )
    output = output.resolve()
    if args.verify_only:
        report = verify_manifest(workspace, output)
    else:
        report = build_manifest(workspace, output, args.per_language)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
