from __future__ import annotations

from typing import Protocol

from .java import LexemeExtractor as JavaLexemeExtractor
from .python_ast import PythonAstLexemeExtractor

JAVA_FAMILY_LANGUAGES = {"java", "c", "cpp", "c++", "cuda"}


class ChunkExtractor(Protocol):
    def extract_with_member_fallback(self, source: str): ...


def extractor_for_language(
    language: str | None,
    *,
    allow_fragments: bool = False,
) -> ChunkExtractor:
    normalized = str(language or "java").strip().lower()
    if normalized in {"python", "py"}:
        return PythonAstLexemeExtractor(allow_fragments=allow_fragments)
    if normalized in JAVA_FAMILY_LANGUAGES:
        return JavaLexemeExtractor()
    raise ValueError(f"Unsupported CognaScore language: {language!r}")
