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
class SupportsRead(Protocol[_T_co]):
    def join(self, option: int = ..., /) -> _T_co: ...
