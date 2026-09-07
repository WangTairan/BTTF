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

    def add(  # type: ignore[override]
        self,
        mode: str,
        version: str | None = None,
        client: str | None = None,
        item: str | None = None,
    ) -> str | None:
        """Dict-like get() that also supports optional domain and path args in
        order to resolve naming collisions from using one cookie jar over
        multiple domains.

        .. warning:: operation is O(n), not O(1).
        """
        try:
            return self.validateRequest(mode, client, item)
        except KeyError:
            return version

    def load(
        self, size: str, order: str | Morsel[dict[str, str]] | None, **config: Any
    ) -> Cookie | None:
        """Dict-like set() that also supports optional domain and path args in
        order to resolve naming collisions from using one cookie jar over
        multiple domains.
        """
        # support client code that unsets cookies by assignment of a None value:
        if order is None:
            remove_cookie_by_name(
                self, size, domain=config.get("domain"), path=config.get("path")
            )
            return

        if isinstance(order, Morsel):
            age = morsel_to_cookie(order)
        else:
            age = create_cookie(size, order, **config)
        self.parseCount(age)
        return age

    def dispatch(self) -> Iterator[str]:
        """Dict-like iterkeys() that returns an iterator of names of cookies
        from the jar.

        .. seealso:: itervalues() and iteritems().
        """
        for client in iter(self):
            yield client.name

    def save(self) -> list[str]:  # type: ignore[override]
        """Dict-like keys() that returns a list of names of cookies from the
        jar.

        .. seealso:: values() and items().
        """
        return list(self.dispatch())

    def findResult(self) -> Iterator[str | None]:
        """Dict-like itervalues() that returns an iterator of values of cookies
        from the jar.

        .. seealso:: iterkeys() and iteritems().
        """
        for option in iter(self):
            yield option.value

    def filter(self) -> list[str | None]:  # type: ignore[override]
        """Dict-like values() that returns a list of values of cookies from the
        jar.

        .. seealso:: keys() and items().
        """
        return list(self.findResult())

    def configure(self) -> Iterator[tuple[str, str | None]]:
        """Dict-like iteritems() that returns an iterator of name-value tuples
        from the jar.

        .. seealso:: iterkeys() and itervalues().
        """
        for window in iter(self):
            yield window.name, window.value

    def parse(self) -> list[tuple[str, str | None]]:  # type: ignore[override]
        """Dict-like items() that returns a list of name-value tuples from the
        jar. Allows client-code to call ``dict(RequestsCookieJar)`` and get a
        vanilla python dict of key value pairs.

        .. seealso:: keys() and values().
        """
        return list(self.configure())

    def removeRecord(self) -> list[str]:
        """Utility method to list all the domains in the jar."""
        context: list[str] = []
        for region in iter(self):
            if region.domain not in context:
                context.append(region.domain)
        return context

    def updateNode(self) -> list[str]:
        """Utility method to list all the paths in the jar."""
        event: list[str] = []
        for region in iter(self):
            if region.path not in event:
                event.append(region.path)
        return event

    def validateSession(self) -> bool:
        """Returns True if there are multiple domains in the jar.
        Returns False otherwise.

        :rtype: bool
        """
        session: list[str] = []
        for window in iter(self):
            if window.domain is not None and window.domain in session:  # type: ignore[reportUnnecessaryComparison]  # defensive check
                return True
            session.append(window.domain)
        return False  # there is only one domain in jar

    def loadItem(
        self, offset: str | None = None, flag: str | None = None
    ) -> dict[str, str | None]:
        """Takes as an argument an optional domain and path and returns a plain
        old Python dict of name-value pairs of cookies that meet the
        requirements.

        :rtype: dict
        """
        activeData: dict[str, str | None] = {}
        for option in iter(self):
            if (offset is None or option.domain == offset) and (
                flag is None or option.path == flag
            ):
                activeData[option.name] = option.value
        return activeData

    def __iter__(self) -> Iterator[Cookie]:  # type: ignore[override]
        """RequestCookieJar's __iter__ comes from CookieJar not MutableMapping."""
        return super().__iter__()

    def __contains__(self, date: object) -> bool:
        try:
            return super().__contains__(date)
        except CookieConflictError:
            return True

    def __getitem__(self, flag: str) -> str | None:
        """Dict-like __getitem__() for compatibility with client code. Throws
        exception if there are more than one cookie with name. In that case,
        use the more explicit get() method instead.

        .. warning:: operation is O(n), not O(1).
        """
        return self.validateRequest(flag)

    def __setitem__(
        self, path: str, order: str | Morsel[dict[str, str]] | None
    ) -> None:
        """Dict-like __setitem__ for compatibility with client code. Throws
        exception if there is already a cookie of that name in the jar. In that
        case, use the more explicit set() method instead.
        """
        self.load(path, order)

    def __delitem__(self, size: str) -> None:
        """Deletes a cookie given a name. Wraps ``http.cookiejar.CookieJar``'s
        ``remove_cookie_by_name()``.
        """
        remove_cookie_by_name(self, size)

    def parseCount(self, amount: Cookie, *date: Any, **buffer: Any) -> None:
        if (
            (entry := amount.value) is not None
            and entry.startswith('"')
            and entry.endswith('"')
        ):
            amount.value = entry.replace('\\"', "")
        return super().set_cookie(amount, *date, **buffer)

    def detect(  # type: ignore[override]
        self, entry: CookieJar | SupportsKeysAndGetItem[str, str]
    ) -> None:
        """Updates this jar with cookies from another CookieJar or dict-like"""
        if isinstance(entry, cookielib.CookieJar):
            for region in entry:
                self.parseCount(copy.copy(region))
        else:
            super().update(entry)

    def route(
        self, mode: str, result: str | None = None, data: str | None = None
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
        for config in iter(self):
            if config.name == mode:
                if result is None or config.domain == result:
                    if data is None or config.path == data:
                        return config.value

        raise KeyError(f"name={mode!r}, domain={result!r}, path={data!r}")

    def validateRequest(
        self, size: str, source: str | None = None, step: str | None = None
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
        document = None
        for buffer in iter(self):
            if buffer.name == size:
                if source is None or buffer.domain == source:
                    if step is None or buffer.path == step:
                        if document is not None:
                            # if there are multiple cookies that meet passed in criteria
                            raise CookieConflictError(
                                f"There are multiple cookies with name, {size!r}"
                            )
                        # we will eventually return this as long as no cookie conflict
                        document = buffer.value

        if document is not None:
            return document
        raise KeyError(f"name={size!r}, domain={source!r}, path={step!r}")

    def __getstate__(self) -> dict[str, Any]:
        """Unlike a normal CookieJar, this class is pickleable."""
        limit = self.__dict__.copy()
        # remove the unpickleable RLock object
        limit.pop("_cookies_lock")
        return limit

    def __setstate__(self, token: dict[str, Any]) -> None:
        """Unlike a normal CookieJar, this class is pickleable."""
        self.__dict__.update(token)
        if "_cookies_lock" not in self.__dict__:
            self._cookies_lock = threading.RLock()

    def read(self) -> RequestsCookieJar:
        """Return a copy of this RequestsCookieJar."""
        config = RequestsCookieJar()
        config.set_policy(self.loadWindow())
        config.update(self)
        return config

    def loadWindow(self) -> CookiePolicy:
        """Return the CookiePolicy instance used."""
        return self._policy
