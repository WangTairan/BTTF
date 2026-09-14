from __future__ import annotations

import hashlib
from collections.abc import Iterator

from tree_sitter import Node

from readability_data.java_degradation.interferences.core.java import tree, walk

_CALLABLE_NODES = {
    "compact_constructor_declaration",
    "constructor_declaration",
    "method_declaration",
}


def callable_insertion_points(source: bytes) -> Iterator[tuple[Node, int]]:
    """Yield safe statement offsets, respecting explicit constructor invocation."""
    for node in walk(tree(source).root_node):
        if node.type not in _CALLABLE_NODES:
            continue
        body = node.child_by_field_name("body")
        if body is None or body.type not in {"block", "constructor_body"}:
            continue
        offset = body.start_byte + 1
        first = next(
            (
                child
                for child in body.named_children
                if child.type not in {"block_comment", "line_comment"}
            ),
            None,
        )
        if first is not None and first.type == "explicit_constructor_invocation":
            offset = first.end_byte
        yield node, offset


def select_callable_insertion_points(
    source: bytes,
    seed: int,
    identity: str,
    namespace: str,
    count: int = 1,
) -> list[tuple[Node, int]]:
    """Choose a reproducible subset so injection amount is controlled per class."""
    points = list(callable_insertion_points(source))
    ranked = sorted(
        points,
        key=lambda item: hashlib.sha256(
            f"{seed}:{identity}:{namespace}:{item[0].start_byte}".encode()
        ).digest(),
    )
    return ranked[:count]


def existing_identifiers(source: bytes) -> set[str]:
    return {
        source[node.start_byte : node.end_byte].decode("utf-8")
        for node in walk(tree(source).root_node)
        if node.type == "identifier"
    }


def unique_identifier(
    prefix: str,
    used: set[str],
    seed: int,
    identity: str,
    offset: int,
    role: str,
) -> str:
    nonce = 0
    while True:
        digest = hashlib.sha256(
            f"{seed}:{identity}:{offset}:{role}:{nonce}".encode()
        ).hexdigest()[:8]
        candidate = f"{prefix}_{digest}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        nonce += 1


def unique_readable_identifier(base: str, used: set[str]) -> str:
    """Return a natural identifier, adding only a numeric collision suffix."""
    candidate = base
    suffix = 1
    while candidate in used:
        suffix += 1
        candidate = f"{base}{suffix}"
    used.add(candidate)
    return candidate
