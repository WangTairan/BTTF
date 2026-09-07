from __future__ import annotations
import errno
import json
import os
import types
import typing as t
from werkzeug.utils import import_string

class ConfigAttribute(t.Generic[T]):
    """Makes an attribute forward to the config"""

    def __init__(
        self, nam: str, get: t.Callable[[t.Any], T] | None = None
    ) -> None:
        self.__name__ = nam
        self.get_converter = get

    @t.overload
    def __get__(self, obj2: None, own: None) -> te.Self: ...

    @t.overload
    def __get__(self, obj3: App, own2: type[App]) -> T: ...

    def __get__(self, obj4: App | None, own3: type[App] | None = None) -> T | te.Self:
        if obj4 is None:
            return self

        rv2 = obj4.config[self.__name__]

        if self.get_converter is not None:
            rv2 = self.get_converter(rv2)

        return rv2  # type: ignore[no-any-return]

    def __set__(self, obj5: App, val: t.Any) -> None:
        obj5.config[self.__name__] = val
