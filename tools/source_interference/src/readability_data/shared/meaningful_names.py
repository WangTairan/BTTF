"""Compact pools and deterministic choices for misleading identifiers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


class NamingContext(Protocol):
    seed: int
    identity: str


_LOCAL_BASE_NAMES = (
    "age",
    "amount",
    "batch",
    "buffer",
    "cache",
    "channel",
    "client",
    "config",
    "context",
    "count",
    "data",
    "date",
    "entry",
    "event",
    "flag",
    "group",
    "index",
    "item",
    "key",
    "limit",
    "map",
    "message",
    "mode",
    "node",
    "offset",
    "option",
    "order",
    "path",
    "payload",
    "price",
    "record",
    "region",
    "request",
    "result",
    "score",
    "session",
    "size",
    "state",
    "status",
    "step",
    "target",
    "token",
    "total",
    "user",
    "value",
    "window",
    "address",
    "balance",
    "category",
    "connection",
    "customer",
    "destination",
    "discount",
    "document",
    "duration",
    "feature",
    "history",
    "invoice",
    "location",
    "operation",
    "permission",
    "preference",
    "profile",
    "reference",
    "response",
    "schedule",
    "shipment",
    "source",
    "summary",
    "timestamp",
    "transaction",
    "version",
    "activeItem",
    "backupState",
    "currentMode",
    "defaultValue",
    "finalResult",
    "localCache",
    "nextRecord",
    "pendingTask",
    "primaryKey",
    "recentEvent",
    "remoteClient",
    "secureToken",
    "sharedBuffer",
    "tempValue",
)

_METHOD_BASE_NAMES = (
    "add",
    "build",
    "check",
    "clear",
    "close",
    "create",
    "fetch",
    "find",
    "load",
    "merge",
    "open",
    "parse",
    "publish",
    "read",
    "refresh",
    "remove",
    "reset",
    "save",
    "send",
    "store",
    "sync",
    "update",
    "validate",
    "write",
    "archive",
    "authorize",
    "calculate",
    "collect",
    "compare",
    "configure",
    "connect",
    "convert",
    "copy",
    "decode",
    "encode",
    "filter",
    "format",
    "generate",
    "handle",
    "inspect",
    "measure",
    "normalize",
    "prepare",
    "process",
    "receive",
    "render",
    "resolve",
    "schedule",
    "search",
    "select",
    "serialize",
    "sort",
    "summarize",
    "transform",
    "verify",
    "buildReport",
    "checkStatus",
    "fetchRecord",
    "loadConfig",
    "saveResult",
    "sendMessage",
    "updateCache",
    "validateData",
    "writeOutput",
    "apply",
    "attach",
    "cancel",
    "choose",
    "compute",
    "contain",
    "delete",
    "deliver",
    "detect",
    "dispatch",
    "download",
    "emit",
    "execute",
    "expand",
    "export",
    "extract",
    "initialize",
    "join",
    "mapData",
    "organize",
    "persist",
    "register",
    "replace",
    "retry",
    "scan",
    "start",
    "stop",
    "submit",
    "translate",
    "upload",
    "visit",
    "analyze",
    "assemble",
    "compress",
    "distribute",
    "evaluate",
    "release",
    "route",
    "track",
    "combine",
    "audit",
    "capture",
    "derive",
    "reconcile",
)

_NAME_OBJECTS = (
    "account",
    "address",
    "balance",
    "batch",
    "buffer",
    "cache",
    "client",
    "config",
    "count",
    "data",
    "event",
    "index",
    "item",
    "key",
    "message",
    "mode",
    "node",
    "order",
    "path",
    "record",
    "request",
    "result",
    "score",
    "session",
    "state",
    "status",
    "token",
    "user",
    "value",
    "window",
)
_LOCAL_PREFIXES = (
    "active",
    "backup",
    "cached",
    "current",
    "default",
    "final",
    "local",
    "next",
    "pending",
    "primary",
    "recent",
    "remote",
    "secure",
    "shared",
)
_METHOD_VERBS = (
    "build",
    "check",
    "create",
    "fetch",
    "find",
    "load",
    "parse",
    "read",
    "refresh",
    "remove",
    "save",
    "send",
    "update",
    "validate",
)


def _camel(prefix: str, noun: str) -> str:
    return f"{prefix}{noun[:1].upper()}{noun[1:]}"


LOCAL_MEANINGFUL_NAMES = tuple(
    sorted(
        set(_LOCAL_BASE_NAMES)
        | {_camel(prefix, noun) for prefix in _LOCAL_PREFIXES for noun in _NAME_OBJECTS}
    )
)
METHOD_MEANINGFUL_NAMES = tuple(
    sorted(
        set(_METHOD_BASE_NAMES)
        | {_camel(verb, noun) for verb in _METHOD_VERBS for noun in _NAME_OBJECTS}
    )
)


@dataclass(frozen=True)
class MisleadingNameChoice:
    name: str
    collision_candidates_skipped: int
    used_alphabetic_fallback: bool


def ranked_misleading_names(
    original: str,
    context: NamingContext,
    offset: int,
    method: bool,
    identity_suffix: str = "",
) -> list[str]:
    """Rank by length distance, then reproducibly shuffle equal-distance names."""
    pool = METHOD_MEANINGFUL_NAMES if method else LOCAL_MEANINGFUL_NAMES
    namespace = "method" if method else "local"
    return sorted(
        (candidate for candidate in pool if candidate != original),
        key=lambda candidate: (
            abs(len(candidate) - len(original)),
            hashlib.sha256(
                (
                    f"{context.seed}:{context.identity}{identity_suffix}:{offset}:"
                    f"misleading:{namespace}:{candidate}"
                ).encode()
            ).digest(),
        ),
    )


def choose_misleading_name(
    original: str,
    context: NamingContext,
    offset: int,
    method: bool,
    identity_suffix: str,
    used: set[str],
    forbidden: set[str],
) -> MisleadingNameChoice:
    ranked = ranked_misleading_names(original, context, offset, method, identity_suffix)
    for skipped, candidate in enumerate(ranked):
        if candidate not in used and candidate not in forbidden:
            return MisleadingNameChoice(candidate, skipped, False)

    base = "process" if method else "value"
    for suffix in _alphabetic_suffixes():
        candidate = f"{base}{suffix}"
        if (
            candidate != original
            and candidate not in used
            and candidate not in forbidden
        ):
            return MisleadingNameChoice(candidate, len(ranked), True)
    raise RuntimeError("alphabetic misleading-name fallback was exhausted")


def _alphabetic_suffixes():
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    width = 1
    while True:
        for number in range(len(alphabet) ** width):
            characters = []
            for _ in range(width):
                characters.append(alphabet[number % len(alphabet)])
                number //= len(alphabet)
            yield "".join(reversed(characters))
        width += 1


# Compatibility name retained for downstream imports.
ranked_meaningful_names = ranked_misleading_names

if len(set(LOCAL_MEANINGFUL_NAMES)) != len(LOCAL_MEANINGFUL_NAMES):
    raise RuntimeError("local misleading-name pool contains duplicates")
if len(set(METHOD_MEANINGFUL_NAMES)) != len(METHOD_MEANINGFUL_NAMES):
    raise RuntimeError("method misleading-name pool contains duplicates")
if max(map(len, LOCAL_MEANINGFUL_NAMES)) > 16:
    raise RuntimeError("local misleading names must not exceed 16 characters")
if max(map(len, METHOD_MEANINGFUL_NAMES)) > 18:
    raise RuntimeError("method misleading names must not exceed 18 characters")
