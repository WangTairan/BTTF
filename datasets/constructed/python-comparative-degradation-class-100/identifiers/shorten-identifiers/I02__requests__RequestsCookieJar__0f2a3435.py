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

    def get2(  # type: ignore[override]
        self,
        nam: str,
        def2: str | None = None,
        dom: str | None = None,
        pat: str | None = None,
    ) -> str | None:
        """Dict-like get() that also supports optional domain and path args in
        order to resolve naming collisions from using one cookie jar over
        multiple domains.

        .. warning:: operation is O(n), not O(1).
        """
        try:
            return self.find(nam, dom, pat)
        except KeyError:
            return def2

    def set2(
        self, nam2: str, val2: str | Morsel[dict[str, str]] | None, **kwa: Any
    ) -> Cookie | None:
        """Dict-like set() that also supports optional domain and path args in
        order to resolve naming collisions from using one cookie jar over
        multiple domains.
        """
        # support client code that unsets cookies by assignment of a None value:
        if val2 is None:
            remove_cookie_by_name(
                self, nam2, domain=kwa.get("domain"), path=kwa.get("path")
            )
            return

        if isinstance(val2, Morsel):
            c2 = morsel_to_cookie(val2)
        else:
            c2 = create_cookie(nam2, val2, **kwa)
        self.set3(c2)
        return c2

    def ite(self) -> Iterator[str]:
        """Dict-like iterkeys() that returns an iterator of names of cookies
        from the jar.

        .. seealso:: itervalues() and iteritems().
        """
        for coo in iter(self):
            yield coo.name

    def key(self) -> list[str]:  # type: ignore[override]
        """Dict-like keys() that returns a list of names of cookies from the
        jar.

        .. seealso:: values() and items().
        """
        return list(self.ite())

    def ite2(self) -> Iterator[str | None]:
        """Dict-like itervalues() that returns an iterator of values of cookies
        from the jar.

        .. seealso:: iterkeys() and iteritems().
        """
        for coo2 in iter(self):
            yield coo2.value

    def val(self) -> list[str | None]:  # type: ignore[override]
        """Dict-like values() that returns a list of values of cookies from the
        jar.

        .. seealso:: keys() and items().
        """
        return list(self.ite2())

    def ite3(self) -> Iterator[tuple[str, str | None]]:
        """Dict-like iteritems() that returns an iterator of name-value tuples
        from the jar.

        .. seealso:: iterkeys() and itervalues().
        """
        for coo3 in iter(self):
            yield coo3.name, coo3.value

    def ite4(self) -> list[tuple[str, str | None]]:  # type: ignore[override]
        """Dict-like items() that returns a list of name-value tuples from the
        jar. Allows client-code to call ``dict(RequestsCookieJar)`` and get a
        vanilla python dict of key value pairs.

        .. seealso:: keys() and values().
        """
        return list(self.ite3())

    def list2(self) -> list[str]:
        """Utility method to list all the domains in the jar."""
        dom2: list[str] = []
        for coo4 in iter(self):
            if coo4.domain not in dom2:
                dom2.append(coo4.domain)
        return dom2

    def list3(self) -> list[str]:
        """Utility method to list all the paths in the jar."""
        pat2: list[str] = []
        for coo5 in iter(self):
            if coo5.path not in pat2:
                pat2.append(coo5.path)
        return pat2

    def multiple(self) -> bool:
        """Returns True if there are multiple domains in the jar.
        Returns False otherwise.

        :rtype: bool
        """
        dom3: list[str] = []
        for coo6 in iter(self):
            if coo6.domain is not None and coo6.domain in dom3:  # type: ignore[reportUnnecessaryComparison]  # defensive check
                return True
            dom3.append(coo6.domain)
        return False  # there is only one domain in jar

    def get3(
        self, dom4: str | None = None, pat3: str | None = None
    ) -> dict[str, str | None]:
        """Takes as an argument an optional domain and path and returns a plain
        old Python dict of name-value pairs of cookies that meet the
        requirements.

        :rtype: dict
        """
        dic: dict[str, str | None] = {}
        for coo7 in iter(self):
            if (dom4 is None or coo7.domain == dom4) and (
                pat3 is None or coo7.path == pat3
            ):
                dic[coo7.name] = coo7.value
        return dic

    def __iter__(self) -> Iterator[Cookie]:  # type: ignore[override]
        """RequestCookieJar's __iter__ comes from CookieJar not MutableMapping."""
        return super().__iter__()

    def __contains__(self, nam3: object) -> bool:
        try:
            return super().__contains__(nam3)
        except CookieConflictError:
            return True

    def __getitem__(self, nam4: str) -> str | None:
        """Dict-like __getitem__() for compatibility with client code. Throws
        exception if there are more than one cookie with name. In that case,
        use the more explicit get() method instead.

        .. warning:: operation is O(n), not O(1).
        """
        return self.find(nam4)

    def __setitem__(
        self, nam5: str, val3: str | Morsel[dict[str, str]] | None
    ) -> None:
        """Dict-like __setitem__ for compatibility with client code. Throws
        exception if there is already a cookie of that name in the jar. In that
        case, use the more explicit set() method instead.
        """
        self.set2(nam5, val3)

    def __delitem__(self, nam6: str) -> None:
        """Deletes a cookie given a name. Wraps ``http.cookiejar.CookieJar``'s
        ``remove_cookie_by_name()``.
        """
        remove_cookie_by_name(self, nam6)

    def set3(self, coo8: Cookie, *arg: Any, **kwa2: Any) -> None:
        if (
            (val4 := coo8.value) is not None
            and val4.startswith('"')
            and val4.endswith('"')
        ):
            coo8.value = val4.replace('\\"', "")
        return super().set_cookie(coo8, *arg, **kwa2)

    def upd(  # type: ignore[override]
        self, oth: CookieJar | SupportsKeysAndGetItem[str, str]
    ) -> None:
        """Updates this jar with cookies from another CookieJar or dict-like"""
        if isinstance(oth, cookielib.CookieJar):
            for coo9 in oth:
                self.set3(copy.copy(coo9))
        else:
            super().update(oth)

    def fin(
        self, nam7: str, dom5: str | None = None, pat4: str | None = None
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
        for coo10 in iter(self):
            if coo10.name == nam7:
                if dom5 is None or coo10.domain == dom5:
                    if pat4 is None or coo10.path == pat4:
                        return coo10.value

        raise KeyError(f"name={nam7!r}, domain={dom5!r}, path={pat4!r}")

    def find(
        self, nam8: str, dom6: str | None = None, pat5: str | None = None
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
        to = None
        for coo11 in iter(self):
            if coo11.name == nam8:
                if dom6 is None or coo11.domain == dom6:
                    if pat5 is None or coo11.path == pat5:
                        if to is not None:
                            # if there are multiple cookies that meet passed in criteria
                            raise CookieConflictError(
                                f"There are multiple cookies with name, {nam8!r}"
                            )
                        # we will eventually return this as long as no cookie conflict
                        to = coo11.value

        if to is not None:
            return to
        raise KeyError(f"name={nam8!r}, domain={dom6!r}, path={pat5!r}")

    def __getstate__(self) -> dict[str, Any]:
        """Unlike a normal CookieJar, this class is pickleable."""
        sta = self.__dict__.copy()
        # remove the unpickleable RLock object
        sta.pop("_cookies_lock")
        return sta

    def __setstate__(self, sta2: dict[str, Any]) -> None:
        """Unlike a normal CookieJar, this class is pickleable."""
        self.__dict__.update(sta2)
        if "_cookies_lock" not in self.__dict__:
            self._cookies_lock = threading.RLock()

    def cop(self) -> RequestsCookieJar:
        """Return a copy of this RequestsCookieJar."""
        new = RequestsCookieJar()
        new.set_policy(self.get4())
        new.update(self)
        return new

    def get4(self) -> CookiePolicy:
        """Return the CookiePolicy instance used."""
        return self._policy
