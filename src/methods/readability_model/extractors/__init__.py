"""Language-aware extractors of AST-tagged snippets."""

from .c_like import CLikeLexemeExtractor
from .factory import ChunkExtractor, extractor_for_language
from .python_ast import PythonAstLexemeExtractor

__all__ = [
    "CLikeLexemeExtractor",
    "ChunkExtractor",
    "PythonAstLexemeExtractor",
    "extractor_for_language",
]
