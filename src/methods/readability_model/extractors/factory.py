from __future__ import annotations

from typing import Protocol

from .c_like import CLikeLexemeExtractor
from .java import LexemeExtractor as JavaLexemeExtractor
from .python_ast import PythonAstLexemeExtractor

C_LIKE_LANGUAGES = {"c", "cpp", "c++", "cuda"}


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
    if normalized == "java":
        return JavaLexemeExtractor()
    if normalized in C_LIKE_LANGUAGES:
        return CLikeLexemeExtractor()
    raise ValueError(f"Unsupported readability-model language: {language!r}")
