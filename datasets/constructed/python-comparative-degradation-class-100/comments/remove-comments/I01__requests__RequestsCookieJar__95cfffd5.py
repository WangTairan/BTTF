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

class RequestsCookieJar(CookieJar, MutableMapping[str, str | None]):   
    

    _policy: CookiePolicy

    def get(   
        self,
        name: str,
        default: str | None = None,
        domain: str | None = None,
        path: str | None = None,
    ) -> str | None:
        
        try:
            return self._find_no_duplicates(name, domain, path)
        except KeyError:
            return default

    def set(
        self, name: str, value: str | Morsel[dict[str, str]] | None, **kwargs: Any
    ) -> Cookie | None:
        
         
        if value is None:
            remove_cookie_by_name(
                self, name, domain=kwargs.get("domain"), path=kwargs.get("path")
            )
            return

        if isinstance(value, Morsel):
            c = morsel_to_cookie(value)
        else:
            c = create_cookie(name, value, **kwargs)
        self.set_cookie(c)
        return c

    def iterkeys(self) -> Iterator[str]:
        
        for cookie in iter(self):
            yield cookie.name

    def keys(self) -> list[str]:   
        
        return list(self.iterkeys())

    def itervalues(self) -> Iterator[str | None]:
        
        for cookie in iter(self):
            yield cookie.value

    def values(self) -> list[str | None]:   
        
        return list(self.itervalues())

    def iteritems(self) -> Iterator[tuple[str, str | None]]:
        
        for cookie in iter(self):
            yield cookie.name, cookie.value

    def items(self) -> list[tuple[str, str | None]]:   
        
        return list(self.iteritems())

    def list_domains(self) -> list[str]:
        
        domains: list[str] = []
        for cookie in iter(self):
            if cookie.domain not in domains:
                domains.append(cookie.domain)
        return domains

    def list_paths(self) -> list[str]:
        
        paths: list[str] = []
        for cookie in iter(self):
            if cookie.path not in paths:
                paths.append(cookie.path)
        return paths

    def multiple_domains(self) -> bool:
        
        domains: list[str] = []
        for cookie in iter(self):
            if cookie.domain is not None and cookie.domain in domains:   
                return True
            domains.append(cookie.domain)
        return False   

    def get_dict(
        self, domain: str | None = None, path: str | None = None
    ) -> dict[str, str | None]:
        
        dictionary: dict[str, str | None] = {}
        for cookie in iter(self):
            if (domain is None or cookie.domain == domain) and (
                path is None or cookie.path == path
            ):
                dictionary[cookie.name] = cookie.value
        return dictionary

    def __iter__(self) -> Iterator[Cookie]:   
        
        return super().__iter__()

    def __contains__(self, name: object) -> bool:
        try:
            return super().__contains__(name)
        except CookieConflictError:
            return True

    def __getitem__(self, name: str) -> str | None:
        
        return self._find_no_duplicates(name)

    def __setitem__(
        self, name: str, value: str | Morsel[dict[str, str]] | None
    ) -> None:
        
        self.set(name, value)

    def __delitem__(self, name: str) -> None:
        
        remove_cookie_by_name(self, name)

    def set_cookie(self, cookie: Cookie, *args: Any, **kwargs: Any) -> None:
        if (
            (value := cookie.value) is not None
            and value.startswith('"')
            and value.endswith('"')
        ):
            cookie.value = value.replace('\\"', "")
        return super().set_cookie(cookie, *args, **kwargs)

    def update(   
        self, other: CookieJar | SupportsKeysAndGetItem[str, str]
    ) -> None:
        
        if isinstance(other, cookielib.CookieJar):
            for cookie in other:
                self.set_cookie(copy.copy(cookie))
        else:
            super().update(other)

    def _find(
        self, name: str, domain: str | None = None, path: str | None = None
    ) -> str | None:
        
        for cookie in iter(self):
            if cookie.name == name:
                if domain is None or cookie.domain == domain:
                    if path is None or cookie.path == path:
                        return cookie.value

        raise KeyError(f"name={name!r}, domain={domain!r}, path={path!r}")

    def _find_no_duplicates(
        self, name: str, domain: str | None = None, path: str | None = None
    ) -> str:
        
        toReturn = None
        for cookie in iter(self):
            if cookie.name == name:
                if domain is None or cookie.domain == domain:
                    if path is None or cookie.path == path:
                        if toReturn is not None:
                             
                            raise CookieConflictError(
                                f"There are multiple cookies with name, {name!r}"
                            )
                         
                        toReturn = cookie.value

        if toReturn is not None:
            return toReturn
        raise KeyError(f"name={name!r}, domain={domain!r}, path={path!r}")

    def __getstate__(self) -> dict[str, Any]:
        
        state = self.__dict__.copy()
         
        state.pop("_cookies_lock")
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        
        self.__dict__.update(state)
        if "_cookies_lock" not in self.__dict__:
            self._cookies_lock = threading.RLock()

    def copy(self) -> RequestsCookieJar:
        
        new_cj = RequestsCookieJar()
        new_cj.set_policy(self.get_policy())
        new_cj.update(self)
        return new_cj

    def get_policy(self) -> CookiePolicy:
        
        return self._policy
