from __future__ import annotations
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, overload
from .compat import MutableMapping

class LookupDict(dict[str, _VT]):
    """Dictionary lookup object."""

    name: Any

    def __init__(self, d: Any = None) -> None:
        self.name = d
        super().__init__()

    def __repr__(self) -> str:
        return f"<lookup '{self.name}'>"

    def __getattr__(self, e: str) -> _VT | None:
        # We need this for type checkers to infer typing
        # on attribute access with status_codes.py
        if e in self.__dict__:
            return self.__dict__[e]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{e}'"
            )

    def __getitem__(self, f: str) -> _VT | None:  # type: ignore[override]
        # We allow fall-through here, so values default to None

        return self.__dict__.get(f, None)

    @overload
    def c(self, g: str, h: None = None) -> _VT | None: ...

    @overload
    def c(self, i: str, j: _D | _VT) -> _D | _VT: ...

    def c(self, k: str, l: _D | None = None) -> _VT | _D | None:
        return self.__dict__.get(k, l)
