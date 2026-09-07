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
        self, a: str, b: t.Callable[[t.Any], T] | None = None
    ) -> None:
        self.__name__ = a
        self.get_converter = b

    @t.overload
    def __get__(self, c: None, d: None) -> te.Self: ...

    @t.overload
    def __get__(self, e: App, f: type[App]) -> T: ...

    def __get__(self, g: App | None, h: type[App] | None = None) -> T | te.Self:
        if g is None:
            return self

        i = g.config[self.__name__]

        if self.get_converter is not None:
            i = self.get_converter(i)

        return i  # type: ignore[no-any-return]

    def __set__(self, j: App, k: t.Any) -> None:
        j.config[self.__name__] = k
