"""Language-neutral member-access complexity features.

The scanner intentionally avoids parser-specific AST node names.  It recognizes
the common member/namespace access operators ``.``, ``?.``, ``::``, and ``->``
after removing declarations, comments, strings, and numeric literals from
consideration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


ACCESS_OPERATORS = ("?.", "::", "->", ".")
DECLARATION_LINE_RE = re.compile(
    r"^\s*(?:"
    r"import\b|package\b|from\b.*\bimport\b|"
    r"using\s+(?:namespace\b)?|namespace\b|"
    r"#\s*(?:include|import)\b"
    r")"
)


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str


def member_access_features(source: str) -> dict[str, float]:
    """Return member-access frequency and average maximal chain depth.

    Density is the number of validated member-access edges divided by non-empty
    source LOC.  Mean depth is computed over maximal access chains, so
    ``request.user.profile.name`` contributes one chain of depth three rather
    than three independent chains of depth one.
    """
    loc = sum(1 for line in source.splitlines() if line.strip())
    tokens = _tokenize(_remove_declaration_lines(source))
    matching = _matching_brackets(tokens)
    valid_edges = {
        index
        for index, token in enumerate(tokens)
        if token.kind == "access" and _is_valid_access_edge(tokens, index)
    }
    depths = _maximal_chain_depths(tokens, matching, valid_edges)
    return {
        "member_access_density": len(valid_edges) / max(loc, 1),
        "member_access_chain_depth_mean": (
            sum(depths) / len(depths) if depths else 0.0
        ),
    }


def _remove_declaration_lines(source: str) -> str:
    """Blank non-executable qualification declarations while preserving lines."""
    return "\n".join(
        "" if DECLARATION_LINE_RE.match(line) else line
        for line in source.splitlines()
    )


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if source.startswith("//", index):
            index = _line_end(source, index + 2)
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if char == "#":
            index = _line_end(source, index + 1)
            continue
        if char in {'"', "'", "`"}:
            index = _skip_string(source, index, char)
            continue
        if _identifier_start(char):
            end = index + 1
            while end < len(source) and _identifier_part(source[end]):
                end += 1
            tokens.append(_Token("identifier", source[index:end]))
            index = end
            continue
        if char.isdigit():
            index = _skip_number(source, index)
            tokens.append(_Token("number", "number"))
            continue
        operator = next(
            (candidate for candidate in ACCESS_OPERATORS if source.startswith(candidate, index)),
            None,
        )
        if operator is not None:
            tokens.append(_Token("access", operator))
            index += len(operator)
            continue
        kind = "bracket" if char in "()[]{}" else "other"
        tokens.append(_Token(kind, char))
        index += 1
    return tokens


def _line_end(source: str, start: int) -> int:
    end = source.find("\n", start)
    return len(source) if end < 0 else end + 1


def _skip_string(source: str, start: int, quote: str) -> int:
    delimiter = quote * 3 if source.startswith(quote * 3, start) else quote
    index = start + len(delimiter)
    while index < len(source):
        if source.startswith(delimiter, index):
            return index + len(delimiter)
        if source[index] == "\\":
            index += 2
        else:
            index += 1
    return len(source)


def _skip_number(source: str, start: int) -> int:
    """Skip a conservative numeric literal, including decimal/exponent dots."""
    index = start + 1
    while index < len(source):
        char = source[index]
        if char.isalnum() or char in "_.'":
            index += 1
            continue
        if char in "+-" and index > start and source[index - 1] in "eEpP":
            index += 1
            continue
        break
    return index


def _identifier_start(char: str) -> bool:
    return char == "_" or char == "$" or char.isalpha()


def _identifier_part(char: str) -> bool:
    return _identifier_start(char) or char.isdigit()


def _matching_brackets(tokens: list[_Token]) -> dict[int, int]:
    pairs = {"(": ")", "[": "]"}
    stack: list[tuple[str, int]] = []
    matching: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.text in pairs:
            stack.append((token.text, index))
        elif token.text in pairs.values() and stack and pairs[stack[-1][0]] == token.text:
            _, opening = stack.pop()
            matching[opening] = index
    return matching


def _is_valid_access_edge(tokens: list[_Token], index: int) -> bool:
    if index <= 0 or index + 1 >= len(tokens):
        return False
    left = tokens[index - 1]
    right = tokens[index + 1]
    return (
        (left.kind == "identifier" or left.text in {")", "]"})
        and right.kind == "identifier"
    )


def _maximal_chain_depths(
    tokens: list[_Token],
    matching: dict[int, int],
    valid_edges: set[int],
) -> list[int]:
    depths: list[int] = []
    for start, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        if start > 0 and tokens[start - 1].kind == "access":
            continue
        position = _after_postfix(tokens, matching, start + 1)
        depth = 0
        while position in valid_edges:
            depth += 1
            position = _after_postfix(tokens, matching, position + 2)
        if depth:
            depths.append(depth)
    return depths


def _after_postfix(
    tokens: list[_Token],
    matching: dict[int, int],
    position: int,
) -> int:
    while position < len(tokens) and tokens[position].text in {"(", "["}:
        closing = matching.get(position)
        if closing is None:
            break
        position = closing + 1
    return position
