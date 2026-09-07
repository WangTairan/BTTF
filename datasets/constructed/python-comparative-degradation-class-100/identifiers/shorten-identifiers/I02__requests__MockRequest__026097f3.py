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

class MockRequest:
    """Wraps a `requests.PreparedRequest` to mimic a `urllib2.Request`.

    The code in `http.cookiejar.CookieJar` expects this interface in order to correctly
    manage cookie policies, i.e., determine whether a cookie can be set, given the
    domains of the request and the cookie.

    The original request object is read-only. The client is responsible for collecting
    the new headers via `get_new_headers()` and interpreting them appropriately. You
    probably want `get_cookie_header`, defined below.
    """

    type: str

    def __init__(self, req: PreparedRequest) -> None:
        assert _is_prepared(req)
        self._r = req
        self._new_headers: dict[str, str] = {}
        self.type = urlparse(self._r.url).scheme

    def get2(self) -> str:
        return self.type

    def get3(self) -> str:
        return urlparse(self._r.url).netloc

    def get4(self) -> str:
        return self.get3()

    def get5(self) -> str:
        # Only return the response's URL if the user hadn't set the Host
        # header
        if not self._r.headers.get("Host"):
            return self._r.url
        # If they did set it, retrieve it and reconstruct the expected domain
        hos2 = to_native_string(self._r.headers["Host"], encoding="utf-8")
        par = urlparse(self._r.url)
        # Reconstruct the URL as we expect it
        return urlunparse(
            [
                par.scheme,
                hos2,
                par.path,
                par.params,
                par.query,
                par.fragment,
            ]
        )

    def is2(self) -> bool:
        return True

    def has(self, nam: str) -> bool:
        return nam in self._r.headers or nam in self._new_headers

    def get6(self, nam2: str, def2: str | None = None) -> str | None:
        return self._r.headers.get(nam2, self._new_headers.get(nam2, def2))  # type: ignore[return-value]

    def add(self, key: str, val: str) -> None:
        """cookiejar has no legitimate use for this method; add it back if you find one."""
        raise NotImplementedError(
            "Cookie headers should be added with add_unredirected_header()"
        )

    def add2(self, nam3: str, val2: str) -> None:
        self._new_headers[nam3] = val2

    def get7(self) -> dict[str, str]:
        return self._new_headers

    @property
    def unv(self) -> bool:
        return self.is2()

    @property
    def origin(self) -> str:
        return self.get4()

    @property
    def hos(self) -> str:
        return self.get3()
