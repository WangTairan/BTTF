from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

PROJECTS = ("django", "flask", "requests", "attrs")
REPOSITORIES = {
    "django": "https://github.com/django/django.git",
    "flask": "https://github.com/pallets/flask.git",
    "requests": "https://github.com/psf/requests.git",
    "attrs": "https://github.com/python-attrs/attrs.git",
}
EXCLUDED_PARTS = {"test", "tests", "testing", "docs", "examples", "migrations"}


@dataclass(frozen=True)
class Candidate:
    project: str
    path: Path
    relative_path: str
    node: ast.ClassDef
    source: str

    @property
    def line_count(self) -> int:
        return self.node.end_lineno - self.node.lineno + 1

    @property
    def has_method(self) -> bool:
        return any(
            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            for item in self.node.body
        )


def extract_balanced_classes(
    roots: dict[str, Path], output: Path, per_project: int, seed: int
) -> list[dict[str, object]]:
    if output.exists():
        raise ValueError(f"output path already exists: {output}")
    records: list[dict[str, object]] = []
    for project in PROJECTS:
        root = roots[project].resolve()
        if not root.is_dir():
            raise ValueError(f"{project} repository not found: {root}")
        candidates = _candidates(project, root)
        if len(candidates) < per_project:
            raise ValueError(f"{project} has only {len(candidates)} eligible classes")
        ranked = sorted(
            candidates,
            key=lambda item: (
                not item.has_method,
                item.line_count < 5,
                hashlib.sha256(
                    f"{seed}:{project}:{item.relative_path}:{item.node.name}:{item.node.lineno}".encode()
                ).hexdigest(),
            ),
        )[:per_project]
        commit = _commit(root)
        for candidate in ranked:
            text = _extract(candidate)
            ast.parse(text)
            sample_id = (
                "py-"
                + hashlib.sha256(
                    f"{project}:{candidate.relative_path}:{candidate.node.lineno}:{commit}".encode()
                ).hexdigest()[:16]
            )
            filename = f"{project}__{candidate.node.name}__{sample_id[-8:]}.py"
            destination = output / "classes" / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8")
            records.append(
                {
                    "base_sample_id": sample_id,
                    "source": project,
                    "source_name": {
                        "django": "Django",
                        "flask": "Flask",
                        "requests": "Requests",
                        "attrs": "attrs",
                    }[project],
                    "source_commit": commit,
                    "source_repository": REPOSITORIES[project],
                    "source_path": f"{candidate.relative_path}#L{candidate.node.lineno}-L{candidate.node.end_lineno}",
                    "unit_kind": "class",
                    "unit_name": candidate.node.name,
                    "line_count": len(text.splitlines()),
                    "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "local_path": destination.relative_to(output).as_posix(),
                }
            )
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in records), encoding="utf-8"
    )
    return records


def _candidates(project: str, root: Path) -> list[Candidate]:
    result: list[Candidate] = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if any(part.lower() in EXCLUDED_PARTS for part in relative.parts) or any(
            part.startswith(".") for part in relative.parts
        ):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            module = ast.parse(source)
        except (UnicodeDecodeError, SyntaxError):
            continue
        for node in module.body:
            if isinstance(node, ast.ClassDef):
                result.append(
                    Candidate(project, path, relative.as_posix(), node, source)
                )
    return result


def _extract(candidate: Candidate) -> str:
    lines = candidate.source.splitlines(keepends=True)
    module = ast.parse(candidate.source)
    prelude: list[str] = []
    for node in module.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            prelude.extend(lines[node.lineno - 1 : node.end_lineno])
    start = min(
        [candidate.node.lineno] + [d.lineno for d in candidate.node.decorator_list]
    )
    body = "".join(lines[start - 1 : candidate.node.end_lineno])
    header = "".join(prelude)
    if header and not header.endswith("\n"):
        header += "\n"
    return header + ("\n" if header else "") + body.rstrip() + "\n"


def _commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()
