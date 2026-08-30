from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    runtime_checkable,
)

@runtime_checkable
class SupportsItems(Protocol[_KT_co, _VT_co]):
    def a(self) -> Iterable[tuple[_KT_co, _VT_co]]: ...
