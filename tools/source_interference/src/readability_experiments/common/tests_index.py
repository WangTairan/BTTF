from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

TOKEN = re.compile(r"\b[A-Za-z_]\w*\b")
IGNORED_DIRECTORIES = {".git", ".venv", "build", "dist", "target", "node_modules"}


def is_test_file(path: Path, language: str) -> bool:
    suffix = ".java" if language == "java" else ".py"
    if path.suffix != suffix or any(part in IGNORED_DIRECTORIES for part in path.parts):
        return False
    lowered = path.as_posix().lower()
    name = path.name.lower()
    return (
        "/test/" in lowered
        or "/tests/" in lowered
        or name.startswith("test")
        or (
            language == "java"
            and (name.endswith("test.java") or name.endswith("tests.java"))
        )
    )


def find_test_references(
    repository: Path,
    language: str,
    unit_names: set[str],
) -> tuple[dict[str, list[str]], int]:
    references: dict[str, list[str]] = defaultdict(list)
    files_scanned = 0
    for path in repository.rglob("*"):
        if not path.is_file() or not is_test_file(path, language):
            continue
        files_scanned += 1
        try:
            tokens = set(
                TOKEN.findall(path.read_text(encoding="utf-8", errors="ignore"))
            )
        except OSError:
            continue
        relative = path.relative_to(repository).as_posix()
        for name in unit_names & tokens:
            references[name].append(relative)
    return {name: sorted(paths) for name, paths in references.items()}, files_scanned
