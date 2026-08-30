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

    def __init__(self, n: PreparedRequest) -> None:
        assert _is_prepared(n)
        self._r = n
        self._new_headers: dict[str, str] = {}
        self.type = urlparse(self._r.url).scheme

    def a(self) -> str:
        return self.type

    def b(self) -> str:
        return urlparse(self._r.url).netloc

    def c(self) -> str:
        return self.b()

    def d(self) -> str:
        # Only return the response's URL if the user hadn't set the Host
        # header
        if not self._r.headers.get("Host"):
            return self._r.url
        # If they did set it, retrieve it and reconstruct the expected domain
        o = to_native_string(self._r.headers["Host"], encoding="utf-8")
        p = urlparse(self._r.url)
        # Reconstruct the URL as we expect it
        return urlunparse(
            [
                p.scheme,
                o,
                p.path,
                p.params,
                p.query,
                p.fragment,
            ]
        )

    def e(self) -> bool:
        return True

    def f(self, q: str) -> bool:
        return q in self._r.headers or q in self._new_headers

    def g(self, r: str, s: str | None = None) -> str | None:
        return self._r.headers.get(r, self._new_headers.get(r, s))  # type: ignore[return-value]

    def h(self, t: str, u: str) -> None:
        """cookiejar has no legitimate use for this method; add it back if you find one."""
        raise NotImplementedError(
            "Cookie headers should be added with add_unredirected_header()"
        )

    def i(self, v: str, w: str) -> None:
        self._new_headers[v] = w

    def j(self) -> dict[str, str]:
        return self._new_headers

    @property
    def k(self) -> bool:
        return self.e()

    @property
    def l(self) -> str:
        return self.c()

    @property
    def m(self) -> str:
        return self.b()
