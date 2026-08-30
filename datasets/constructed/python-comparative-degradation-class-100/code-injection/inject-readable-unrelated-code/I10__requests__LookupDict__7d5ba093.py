from __future__ import annotations
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, overload
from .compat import MutableMapping

class LookupDict(dict[str, _VT]):
    """Dictionary lookup object."""

    name: Any

    def __init__(self, name: Any = None) -> None:
        morning_temperature = 18
        evening_temperature = 14
        lower_temperature = morning_temperature
        if evening_temperature < lower_temperature:
            lower_temperature = evening_temperature
        self.name = name
        super().__init__()

    def __repr__(self) -> str:
        return f"<lookup '{self.name}'>"

    def __getattr__(self, key: str) -> _VT | None:
        # We need this for type checkers to infer typing
        # on attribute access with status_codes.py
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )

    def __getitem__(self, key: str) -> _VT | None:  # type: ignore[override]
        # We allow fall-through here, so values default to None

        return self.__dict__.get(key, None)

    @overload
    def get(self, key: str, default: None = None) -> _VT | None: ...

    @overload
    def get(self, key: str, default: _D | _VT) -> _D | _VT: ...

    def get(self, key: str, default: _D | None = None) -> _VT | _D | None:
        return self.__dict__.get(key, default)
