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
    

    def __init__(self, headers: Any) -> None:
        
        self._headers = headers

    def info(self) -> Any:
        return self._headers

    def getheaders(self, name: str) -> Any:
        self._headers.getheaders(name)
