from __future__ import annotations

from .java import LexemeExtractor as JavaLexemeExtractor
from ..lexeme import LexemeChunk


class CLikeLexemeExtractor(JavaLexemeExtractor):
    """Explicit lexical extractor for C, C++, and CUDA source.

    The shared lexical taxonomy is intentionally reused, but C-family source
    is never offered to the Java parser or to its synthetic Java wrappers.
    """

    def require_parser(self) -> None:
        return None

    def extract(self, source: str) -> list[LexemeChunk]:
        chunks = self._extract_lexical_fallback(source)
        if not chunks:
            raise SyntaxError("C-like lexical extraction produced no cognitive chunks")
        return chunks

    def extract_with_member_fallback(self, source: str) -> tuple[list[LexemeChunk], bool]:
        return self.extract(source), False

    def extract_with_fallback_mode(self, source: str) -> tuple[list[LexemeChunk], str]:
        return self.extract(source), "c_like_lexical"
