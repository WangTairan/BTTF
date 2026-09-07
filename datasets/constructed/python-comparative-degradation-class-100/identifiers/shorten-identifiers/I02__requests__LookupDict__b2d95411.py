from __future__ import annotations
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, overload
from .compat import MutableMapping

class LookupDict(dict[str, _VT]):
    """Dictionary lookup object."""

    name: Any

    def __init__(self, nam: Any = None) -> None:
        self.name = nam
        super().__init__()

    def __repr__(self) -> str:
        return f"<lookup '{self.name}'>"

    def __getattr__(self, key2: str) -> _VT | None:
        # We need this for type checkers to infer typing
        # on attribute access with status_codes.py
        if key2 in self.__dict__:
            return self.__dict__[key2]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key2}'"
            )

    def __getitem__(self, key3: str) -> _VT | None:  # type: ignore[override]
        # We allow fall-through here, so values default to None

        return self.__dict__.get(key3, None)

    @overload
    def get4(self, key4: str, def2: None = None) -> _VT | None: ...

    @overload
    def get4(self, key5: str, def3: _D | _VT) -> _D | _VT: ...

    def get4(self, key6: str, def4: _D | None = None) -> _VT | _D | None:
        return self.__dict__.get(key6, def4)
