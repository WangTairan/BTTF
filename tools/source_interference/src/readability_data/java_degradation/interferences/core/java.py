from __future__ import annotations

from typing import Iterable

import tree_sitter_java
from tree_sitter import Language, Node, Parser, Tree

from readability_data.shared.determinism import stable_mask


def parser() -> Parser:
    return Parser(Language(tree_sitter_java.language()))


def tree(source: bytes) -> Tree:
    return parser().parse(source)


def validate_java(source: bytes, identity: str, stage: str) -> None:
    try:
        source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{identity}: {stage} output is not UTF-8") from error
    if tree(source).root_node.has_error:
        raise ValueError(f"{identity}: {stage} produced invalid Java")


def walk(node: Node) -> Iterable[Node]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.named_children))


def ancestor(node: Node, types: set[str]) -> Node | None:
    current = node.parent
    while current is not None:
        if current.type in types:
            return current
        current = current.parent
    return None


def apply_edits(source: bytes, edits: list[tuple[int, int, bytes]]) -> bytes:
    result = source
    last_start = len(source) + 1
    for start, end, replacement in sorted(
        edits, key=lambda item: (item[0], item[1]), reverse=True
    ):
        if end > last_start:
            raise ValueError("overlapping Java transformation edits")
        result = result[:start] + replacement + result[end:]
        last_start = start
    return result


def literal_end(text: str, start: int, delimiter: str) -> int:
    index = start + len(delimiter)
    while index < len(text):
        if text.startswith(delimiter, index):
            return index + len(delimiter)
        if delimiter != '"""' and text[index] == "\\":
            index += 2
        else:
            index += 1
    return len(text)


def seeded_mask(seed: int, identity: str, offset: int, namespace: str) -> int:
    """Compatibility name for the shared deterministic mask function."""
    return stable_mask(seed, identity, offset, namespace)
