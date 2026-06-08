from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LexemeChunk:
    lexeme: str
    line: int
    type: str = "NORMAL"
