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

class RequestsCookieJar(CookieJar, MutableMapping[str, str | None]):  # type: ignore[misc]
    """Compatibility class; is a http.cookiejar.CookieJar, but exposes a dict
    interface.

    This is the CookieJar we create by default for requests and sessions that
    don't specify one, since some clients may expect response.cookies and
    session.cookies to support dict operations.

    Requests does not use the dict interface internally; it's just for
    compatibility with external client code. All requests code should work
    out of the box with externally provided instances of ``CookieJar``, e.g.
    ``LWPCookieJar`` and ``FileCookieJar``.

    Unlike a regular CookieJar, this class is pickleable.

    .. warning:: dictionary operations that are normally O(1) may be O(n).
    """

    _policy: CookiePolicy

    def a(  # type: ignore[override]
        self,
        t: str,
        u: str | None = None,
        v: str | None = None,
        w: str | None = None,
    ) -> str | None:
        """Dict-like get() that also supports optional domain and path args in
        order to resolve naming collisions from using one cookie jar over
        multiple domains.

        .. warning:: operation is O(n), not O(1).
        """
        try:
            return self.q(t, v, w)
        except KeyError:
            return u

    def b(
        self, x: str, y: str | Morsel[dict[str, str]] | None, **z: Any
    ) -> Cookie | None:
        """Dict-like set() that also supports optional domain and path args in
        order to resolve naming collisions from using one cookie jar over
        multiple domains.
        """
        # support client code that unsets cookies by assignment of a None value:
        if y is None:
            remove_cookie_by_name(
                self, x, domain=z.get("domain"), path=z.get("path")
            )
            return

        if isinstance(y, Morsel):
            A = morsel_to_cookie(y)
        else:
            A = create_cookie(x, y, **z)
        self.n(A)
        return A

    def d(self) -> Iterator[str]:
        """Dict-like iterkeys() that returns an iterator of names of cookies
        from the jar.

        .. seealso:: itervalues() and iteritems().
        """
        for B in iter(self):
            yield B.name

    def e(self) -> list[str]:  # type: ignore[override]
        """Dict-like keys() that returns a list of names of cookies from the
        jar.

        .. seealso:: values() and items().
        """
        return list(self.d())

    def f(self) -> Iterator[str | None]:
        """Dict-like itervalues() that returns an iterator of values of cookies
        from the jar.

        .. seealso:: iterkeys() and iteritems().
        """
        for C in iter(self):
            yield C.value

    def g(self) -> list[str | None]:  # type: ignore[override]
        """Dict-like values() that returns a list of values of cookies from the
        jar.

        .. seealso:: keys() and items().
        """
        return list(self.f())

    def h(self) -> Iterator[tuple[str, str | None]]:
        """Dict-like iteritems() that returns an iterator of name-value tuples
        from the jar.

        .. seealso:: iterkeys() and itervalues().
        """
        for D in iter(self):
            yield D.name, D.value

    def i(self) -> list[tuple[str, str | None]]:  # type: ignore[override]
        """Dict-like items() that returns a list of name-value tuples from the
        jar. Allows client-code to call ``dict(RequestsCookieJar)`` and get a
        vanilla python dict of key value pairs.

        .. seealso:: keys() and values().
        """
        return list(self.h())

    def j(self) -> list[str]:
        """Utility method to list all the domains in the jar."""
        E: list[str] = []
        for F in iter(self):
            if F.domain not in E:
                E.append(F.domain)
        return E

    def k(self) -> list[str]:
        """Utility method to list all the paths in the jar."""
        G: list[str] = []
        for H in iter(self):
            if H.path not in G:
                G.append(H.path)
        return G

    def l(self) -> bool:
        """Returns True if there are multiple domains in the jar.
        Returns False otherwise.

        :rtype: bool
        """
        I: list[str] = []
        for J in iter(self):
            if J.domain is not None and J.domain in I:  # type: ignore[reportUnnecessaryComparison]  # defensive check
                return True
            I.append(J.domain)
        return False  # there is only one domain in jar

    def m(
        self, K: str | None = None, L: str | None = None
    ) -> dict[str, str | None]:
        """Takes as an argument an optional domain and path and returns a plain
        old Python dict of name-value pairs of cookies that meet the
        requirements.

        :rtype: dict
        """
        M: dict[str, str | None] = {}
        for N in iter(self):
            if (K is None or N.domain == K) and (
                L is None or N.path == L
            ):
                M[N.name] = N.value
        return M

    def __iter__(self) -> Iterator[Cookie]:  # type: ignore[override]
        """RequestCookieJar's __iter__ comes from CookieJar not MutableMapping."""
        return super().__iter__()

    def __contains__(self, O: object) -> bool:
        try:
            return super().__contains__(O)
        except CookieConflictError:
            return True

    def __getitem__(self, P: str) -> str | None:
        """Dict-like __getitem__() for compatibility with client code. Throws
        exception if there are more than one cookie with name. In that case,
        use the more explicit get() method instead.

        .. warning:: operation is O(n), not O(1).
        """
        return self.q(P)

    def __setitem__(
        self, Q: str, R: str | Morsel[dict[str, str]] | None
    ) -> None:
        """Dict-like __setitem__ for compatibility with client code. Throws
        exception if there is already a cookie of that name in the jar. In that
        case, use the more explicit set() method instead.
        """
        self.b(Q, R)

    def __delitem__(self, S: str) -> None:
        """Deletes a cookie given a name. Wraps ``http.cookiejar.CookieJar``'s
        ``remove_cookie_by_name()``.
        """
        remove_cookie_by_name(self, S)

    def n(self, T: Cookie, *U: Any, **V: Any) -> None:
        if (
            (W := T.value) is not None
            and W.startswith('"')
            and W.endswith('"')
        ):
            T.value = W.replace('\\"', "")
        return super().set_cookie(T, *U, **V)

    def o(  # type: ignore[override]
        self, X: CookieJar | SupportsKeysAndGetItem[str, str]
    ) -> None:
        """Updates this jar with cookies from another CookieJar or dict-like"""
        if isinstance(X, cookielib.CookieJar):
            for Y in X:
                self.n(copy.copy(Y))
        else:
            super().update(X)

    def p(
        self, Z: str, aa: str | None = None, ab: str | None = None
    ) -> str | None:
        """Requests uses this method internally to get cookie values.

        If there are conflicting cookies, _find arbitrarily chooses one.
        See _find_no_duplicates if you want an exception thrown if there are
        conflicting cookies.

        :param name: a string containing name of cookie
        :param domain: (optional) string containing domain of cookie
        :param path: (optional) string containing path of cookie
        :return: cookie.value
        """
        for ac in iter(self):
            if ac.name == Z:
                if aa is None or ac.domain == aa:
                    if ab is None or ac.path == ab:
                        return ac.value

        raise KeyError(f"name={Z!r}, domain={aa!r}, path={ab!r}")

    def q(
        self, ad: str, ae: str | None = None, af: str | None = None
    ) -> str:
        """Both ``__get_item__`` and ``get`` call this function: it's never
        used elsewhere in Requests.

        :param name: a string containing name of cookie
        :param domain: (optional) string containing domain of cookie
        :param path: (optional) string containing path of cookie
        :raises KeyError: if cookie is not found
        :raises CookieConflictError: if there are multiple cookies
            that match name and optionally domain and path
        :return: cookie.value
        """
        ag = None
        for ah in iter(self):
            if ah.name == ad:
                if ae is None or ah.domain == ae:
                    if af is None or ah.path == af:
                        if ag is not None:
                            # if there are multiple cookies that meet passed in criteria
                            raise CookieConflictError(
                                f"There are multiple cookies with name, {ad!r}"
                            )
                        # we will eventually return this as long as no cookie conflict
                        ag = ah.value

        if ag is not None:
            return ag
        raise KeyError(f"name={ad!r}, domain={ae!r}, path={af!r}")

    def __getstate__(self) -> dict[str, Any]:
        """Unlike a normal CookieJar, this class is pickleable."""
        ai = self.__dict__.copy()
        # remove the unpickleable RLock object
        ai.pop("_cookies_lock")
        return ai

    def __setstate__(self, aj: dict[str, Any]) -> None:
        """Unlike a normal CookieJar, this class is pickleable."""
        self.__dict__.update(aj)
        if "_cookies_lock" not in self.__dict__:
            self._cookies_lock = threading.RLock()

    def r(self) -> RequestsCookieJar:
        """Return a copy of this RequestsCookieJar."""
        ak = RequestsCookieJar()
        ak.set_policy(self.s())
        ak.update(self)
        return ak

    def s(self) -> CookiePolicy:
        """Return the CookiePolicy instance used."""
        return self._policy
