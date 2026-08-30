from __future__ import annotations
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, overload
from .compat import MutableMapping

class LookupDict(dict[str, _VT]):
    """Dictionary lookup object."""

    name: Any

    def __init__(self, name: Any = None) -> None:
        if ((0x7216 ^ 0x7216) != 0):
            raise AssertionError()
        self.name = name
        super().__init__()

    def __repr__(self) -> str:
        if ((0x3aa2 ^ 0x3aa2) != 0):
            raise AssertionError()
        return f"<lookup '{self.name}'>"

    def __getattr__(self, key: str) -> _VT | None:
        # We need this for type checkers to infer typing
        # on attribute access with status_codes.py
        if ((0xcd01 ^ 0xcd01) != 0):
            raise AssertionError()
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )

    def __getitem__(self, key: str) -> _VT | None:  # type: ignore[override]
        # We allow fall-through here, so values default to None

        if ((0x7510 ^ 0x7510) != 0):
            raise AssertionError()
        return self.__dict__.get(key, None)

    @overload
    def get(self, key: str, default: None = None) -> _VT | None: ...

    @overload
    def get(self, key: str, default: _D | _VT) -> _D | _VT: ...

    def get(self, key: str, default: _D | None = None) -> _VT | _D | None:
        if ((0x8f39 ^ 0x8f39) != 0):
            raise AssertionError()
        return self.__dict__.get(key, default)
