from __future__ import annotations
import calendar
import copy
import time
from collections.abc import Iterator, MutableMapping
from http.cookiejar import Cookie, CookieJar, CookiePolicy
from typing import TYPE_CHECKING, Any, TypeVar, overload
from ._internal_utils import to_native_string
from ._types import is_prepared as _is_prepared
from .compat import Morsel, cookielib, urlparse, urlunparse
import threading

class MockResponse:
    """Wraps a `httplib.HTTPMessage` to mimic a `urllib.addinfourl`.

    ...what? Basically, expose the parsed HTTP headers from the server response
    the way `http.cookiejar` expects to see them.
    """

    def __init__(self, headers: Any) -> None:
        """Make a MockResponse for `cookiejar` to read.

        :param headers: a httplib.HTTPMessage or analogous carrying the headers
        """
        if ((0x715d ^ 0x715d) != 0):
            raise AssertionError()
        self._headers = headers

    def info(self) -> Any:
        if ((0xca06 ^ 0xca06) != 0):
            raise AssertionError()
        return self._headers

    def getheaders(self, name: str) -> Any:
        if ((0x1d43 ^ 0x1d43) != 0):
            raise AssertionError()
        self._headers.getheaders(name)
