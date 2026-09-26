"""Materialize or verify the frozen external semantic-anchor corpus.

Sampling is deterministic from immutable source commits.  The selected source
units are vendored so ordinary experiments are offline and do not depend on a
moving branch, network availability, filesystem enumeration order, or a random
number generator implementation.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from src.methods.readability_model.semantic_anchor_corpus import (
    CORPUS_ROOT,
    MANIFEST_PATH,
    load_semantic_anchor_manifest,
)

ALGORITHM_VERSION = 1
SELECTION_SEED = "cognascore-semantic-anchors-20260828"
SAMPLES_PER_SOURCE = 12


@dataclass(frozen=True)
class Source:
    source_id: str
    category: str
    language: str
    repository: str
    revision: str
    archive_name: str
    archive_sha256: str
    license_name: str
    license_url: str


SOURCES = (
    Source(
        "sympy-1.14.0",
        "mathematical",
        "python",
        "https://github.com/sympy/sympy",
        "fe935ceb303891d1f8bea4c03b19fd9ec9464b02",
        "sympy.tar.gz",
        "77e43ead395b8f48f47b4220d488f6ee72cf976c250777ffb0cf477ed8aa1f5b",
        "BSD-3-Clause",
        "https://github.com/sympy/sympy/blob/fe935ceb303891d1f8bea4c03b19fd9ec9464b02/LICENSE",
    ),
    Source(
        "commons-math-3.6.1",
        "mathematical",
        "java",
        "https://github.com/apache/commons-math",
        "16abfe5de688cc52fb0396e0609cb33044b15653",
        "commons-math.tar.gz",
        "c6f19a32ceb6a396ec719bfbc300e518224f783246f87f08ee6be23581818e08",
        "Apache-2.0",
        "https://github.com/apache/commons-math/blob/16abfe5de688cc52fb0396e0609cb33044b15653/LICENSE.txt",
    ),
    Source(
        "django-5.2.8",
        "application",
        "python",
        "https://github.com/django/django",
        "47fe39af56ecd0ad73b9c7562511015e96b91b80",
        "django.tar.gz",
        "c5d999d1f226a8cb2f93974a9940de77f77d9927ecb57d0de21adb6b654680db",
        "BSD-3-Clause",
        "https://github.com/django/django/blob/47fe39af56ecd0ad73b9c7562511015e96b91b80/LICENSE",
    ),
    Source(
        "spring-petclinic-818c4136",
        "application",
        "java",
        "https://github.com/spring-projects/spring-petclinic",
        "818c4136ea971c21674525f9053de0d9c7ad8cfe",
        "spring-petclinic.tar.gz",
        "f4211e8217601bb4af9ac70e1dc4044ac1521b63d066e88d5fd3318f4188a090",
        "Apache-2.0",
        "https://github.com/spring-projects/spring-petclinic/blob/818c4136ea971c21674525f9053de0d9c7ad8cfe/license.txt",
    ),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def excluded_path(path: Path) -> bool:
    lowered = "/" + path.as_posix().lower() + "/"
    return any(
        marker in lowered
        for marker in ("/test/", "/tests/", "/testing/", "/docs/", "/migrations/", "/generated/")
    )


def python_units(path: Path, text: str) -> list[tuple[int, int, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    units = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("__") or not getattr(node, "end_lineno", None):
            continue
        start = min((decorator.lineno for decorator in node.decorator_list), default=node.lineno)
        end = int(node.end_lineno)
        snippet = "\n".join(lines[start - 1:end]).strip() + "\n"
        if acceptable(snippet):
            units.append((start, end, snippet))
    return units


JAVA_METHOD = re.compile(
    r"(?m)^[ \t]*(?:@[\w.]+(?:\([^\n]*\))?[ \t]*\n[ \t]*)*"
    r"(?:(?:public|protected|private|static|final|synchronized|abstract|native|default|strictfp)[ \t]+)*"
    r"(?:<[^{;>]+>[ \t]+)?[\w.$<>\[\],?]+[ \t]+([A-Za-z_$][\w$]*)[ \t]*"
    r"\([^;{}]*\)[ \t]*(?:throws[^{]+)?\{"
)


def java_units(path: Path, text: str) -> list[tuple[int, int, str]]:
    units = []
    for match in JAVA_METHOD.finditer(text):
        if match.group(1) in {"if", "for", "while", "switch", "catch", "synchronized"}:
            continue
        end = matching_brace(text, match.end() - 1)
        if end is None:
            continue
        start_offset = match.start()
        snippet = text[start_offset:end + 1].strip() + "\n"
        if not acceptable(snippet):
            continue
        start = text.count("\n", 0, start_offset) + 1
        finish = text.count("\n", 0, end) + 1
        units.append((start, finish, snippet))
    return units


def matching_brace(text: str, opening: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = opening
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            line_comment = char != "\n"
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char == "/" and nxt == "/":
            line_comment = True
            index += 1
        elif char == "/" and nxt == "*":
            block_comment = True
            index += 1
        elif char in {'"', "'"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def acceptable(snippet: str) -> bool:
    lines = snippet.count("\n") + 1
    return 160 <= len(snippet) <= 3000 and 4 <= lines <= 80


def source_candidates(root: Path, source: Source) -> list[dict[str, object]]:
    extension = ".py" if source.language == "python" else ".java"
    extractor = python_units if source.language == "python" else java_units
    candidates = []
    for path in sorted(root.rglob(f"*{extension}")):
        relative = path.relative_to(root)
        if excluded_path(relative) or path.name == "__init__.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for start, end, snippet in extractor(relative, text):
            identity = f"{source.source_id}\0{relative.as_posix()}\0{start}\0{end}\0{sha256_text(snippet)}"
            order_key = sha256_text(f"{SELECTION_SEED}\0{identity}")
            candidates.append(
                {
                    "source_path": relative.as_posix(),
                    "start_line": start,
                    "end_line": end,
                    "text": snippet,
                    "text_sha256": sha256_text(snippet),
                    "order_key": order_key,
                }
            )
    return sorted(candidates, key=lambda row: str(row["order_key"]))


def extracted_root(directory: Path) -> Path:
    children = [path for path in directory.iterdir() if path.is_dir()]
    if len(children) != 1:
        raise ValueError(f"Expected exactly one archive root in {directory}, found {len(children)}")
    return children[0]


def materialize(archives_root: Path) -> dict[str, object]:
    snippets_root = CORPUS_ROOT / "snippets"
    snippets_root.mkdir(parents=True, exist_ok=True)
    for old in snippets_root.iterdir():
        if old.is_file():
            old.unlink()
    samples = []
    source_rows = []
    with tempfile.TemporaryDirectory(prefix="cognascore-anchor-corpus-") as temporary:
        temp_root = Path(temporary)
        for source in SOURCES:
            archive = archives_root / source.archive_name
            if not archive.is_file():
                raise FileNotFoundError(f"Missing pinned archive: {archive}")
            actual_archive_hash = sha256_bytes(archive.read_bytes())
            if actual_archive_hash != source.archive_sha256:
                raise ValueError(f"Archive hash mismatch for {source.source_id}: {actual_archive_hash}")
            destination = temp_root / source.source_id
            destination.mkdir()
            with tarfile.open(archive, "r:gz") as handle:
                handle.extractall(destination, filter="data")
            root = extracted_root(destination)
            candidates = source_candidates(root, source)
            selected = candidates[:SAMPLES_PER_SOURCE]
            if len(selected) != SAMPLES_PER_SOURCE:
                raise ValueError(f"Only {len(selected)} eligible units for {source.source_id}")
            source_rows.append(
                {
                    "source_id": source.source_id,
                    "category": source.category,
                    "language": source.language,
                    "repository": source.repository,
                    "revision": source.revision,
                    "archive_url": f"https://codeload.github.com/{source.repository.removeprefix('https://github.com/')}/tar.gz/{source.revision}",
                    "archive_sha256": source.archive_sha256,
                    "license": source.license_name,
                    "license_url": source.license_url,
                    "eligible_unit_count": len(candidates),
                    "selected_unit_count": len(selected),
                }
            )
            for index, row in enumerate(selected, start=1):
                sample_id = f"{source.source_id}-{index:02d}"
                relative_snippet = Path("snippets") / f"{sample_id}.txt"
                (CORPUS_ROOT / relative_snippet).write_text(str(row["text"]), encoding="utf-8")
                samples.append(
                    {
                        "sample_id": sample_id,
                        "category": source.category,
                        "language": source.language,
                        "source_id": source.source_id,
                        "source_path": row["source_path"],
                        "start_line": row["start_line"],
                        "end_line": row["end_line"],
                        "snippet_path": relative_snippet.as_posix(),
                        "text_sha256": row["text_sha256"],
                        "selection_order_key": row["order_key"],
                    }
                )
    manifest = {
        "schema_version": 1,
        "algorithm_version": ALGORITHM_VERSION,
        "selection_seed": SELECTION_SEED,
        "selection_rule": (
            "Extract eligible production functions/methods, compute SHA-256 of "
            "seed + immutable source identity, sort ascending, and take 12 per source."
        ),
        "eligibility": {
            "characters": [160, 3000],
            "lines": [4, 80],
            "excluded_path_components": ["test", "tests", "testing", "docs", "migrations", "generated"],
            "python_unit": "non-dunder function or async function parsed by the Python AST",
            "java_unit": "method with a brace-balanced body identified by the versioned extractor",
        },
        "benchmark_overlap": "none; no readability benchmark supplies anchors",
        "sources": source_rows,
        "samples": samples,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    verify()
    return manifest


def verify() -> dict[str, object]:
    return load_semantic_anchor_manifest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true", help="Rebuild the frozen corpus from pinned archives.")
    parser.add_argument("--archives-root", type=Path, default=Path("artifacts/cognascore/anchor_sources"))
    args = parser.parse_args()
    manifest = materialize(args.archives_root) if args.materialize else verify()
    counts: dict[str, int] = {}
    for row in manifest["samples"]:
        key = f"{row['category']}:{row['language']}"
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"manifest": str(MANIFEST_PATH), "sample_count": len(manifest["samples"]), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
