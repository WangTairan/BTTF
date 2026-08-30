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
    """Dict-like __setitem__ for compatibility with client code.

    Throws exception if there is already a cookie of that
    name in the jar. In that case, use the more explicit set() method instead.
    """

    def __init__(self, headers: Any) -> None:
        """When being redirected we may want to change the

        method of the request based on certain specs or browser behavior.
        """
        self._headers = headers

    def info(self) -> Any:
        return self._headers

    def getheaders(self, name: str) -> Any:
        self._headers.getheaders(name)
