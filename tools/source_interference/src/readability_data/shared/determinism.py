"""Stable hash-based choices shared by all language implementations."""

from __future__ import annotations

import hashlib


def stable_digest(seed: int, identity: str, *parts: object) -> bytes:
    payload = ":".join(str(part) for part in (seed, identity, *parts))
    return hashlib.sha256(payload.encode()).digest()


def stable_index(seed: int, identity: str, count: int, *parts: object) -> int:
    if count <= 0:
        raise ValueError("choice count must be positive")
    return int.from_bytes(stable_digest(seed, identity, *parts)[:4], "big") % count


def stable_mask(seed: int, identity: str, offset: int, namespace: str) -> int:
    return (
        int.from_bytes(stable_digest(seed, identity, namespace, offset)[:2], "big")
        or 0x5A17
    )
