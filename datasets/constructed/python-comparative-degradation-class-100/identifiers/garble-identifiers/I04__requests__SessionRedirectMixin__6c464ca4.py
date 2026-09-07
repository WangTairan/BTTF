from __future__ import annotations
import os
import sys
import time
from collections import OrderedDict
from collections.abc import Generator, Mapping, MutableMapping
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast
from ._internal_utils import to_native_string
from ._types import is_prepared as _is_prepared
from .adapters import HTTPAdapter
from .auth import _basic_auth_str
from .compat import cookielib, urljoin, urlparse
from .cookies import (
    RequestsCookieJar,
    cookiejar_from_dict,
    extract_cookies_to_jar,
    merge_cookies,
)
from .exceptions import (
    ChunkedEncodingError,
    ContentDecodingError,
    InvalidSchema,
    TooManyRedirects,
)
from .hooks import default_hooks, dispatch_hook
from .models import (  # noqa: F401
    DEFAULT_REDIRECT_LIMIT,
    REDIRECT_STATI,
    PreparedRequest,
    Request,
    Response,
)
from .status_codes import codes
from .structures import CaseInsensitiveDict
from .utils import (  # noqa: F401
    DEFAULT_PORTS,
    default_headers,
    get_auth_from_url,
    get_environ_proxies,
    get_netrc_auth,
    requote_uri,
    resolve_proxies,
    rewind_body,
    should_bypass_proxies,  # re-export for external consumers
    to_key_val_list,
)

class SessionRedirectMixin:
    max_redirects: int
    trust_env: bool
    cookies: RequestsCookieJar

    def a(self, h: PreparedRequest, **i: Any) -> Response: ...

    def b(self, j: Response) -> str | None:
        """Receives a Response. Returns a redirect URI or ``None``"""
        # Due to the nature of how requests processes redirects this method will
        # be called at least once upon the original response and at least twice
        # on each subsequent redirect response (if any).
        # If a custom mixin is used to handle this logic, it may be advantageous
        # to cache the redirect location onto the response object as a private
        # attribute.
        if j.is_redirect:
            k = j.headers["location"]
            # Currently the underlying http module on py3 decode headers
            # in latin1, but empirical evidence suggests that latin1 is very
            # rarely used with non-ASCII characters in HTTP headers.
            # It is more likely to get UTF8 header rather than latin1.
            # This causes incorrect handling of UTF8 encoded location headers.
            # To solve this, we re-encode the location in latin1.
            k = k.encode("latin1")
            return to_native_string(k, "utf8")
        return None

    def c(self, l: str, m: str) -> bool:
        """Decide whether Authorization header should be removed when redirecting"""
        n = urlparse(l)
        o = urlparse(m)
        if n.hostname != o.hostname:
            return True
        # Special case: allow http -> https redirect when using the standard
        # ports. This isn't specified by RFC 7235, but is kept to avoid
        # breaking backwards compatibility with older versions of requests
        # that allowed any redirects on the same host.
        if (
            n.scheme == "http"
            and n.port in (80, None)
            and o.scheme == "https"
            and o.port in (443, None)
        ):
            return False

        # Handle default port usage corresponding to scheme.
        p = n.port != o.port
        q = n.scheme != o.scheme
        r = (DEFAULT_PORTS.get(n.scheme, None), None)
        if (
            not q
            and n.port in r
            and o.port in r
        ):
            return False

        # Standard case: root URI must match
        return p or q

    def d(
        self,
        s: Response,
        t: PreparedRequest,
        u: bool = False,
        v: _t.TimeoutType = None,
        w: _t.VerifyType = True,
        x: _t.CertType = None,
        y: dict[str, str] | None = None,
        z: bool = False,
        **A: Any,
    ) -> Generator[Response, None, None]:
        """Receives a Response. Returns a generator of Responses or Requests."""

        B: list[Response] = []  # keep track of history

        C = self.b(s)
        D = urlparse(t.url).fragment
        while C:
            E = t.copy()

            # Update history and keep track of redirects.
            s.history = B[:]
            B.append(s)

            try:
                s.content  # Consume socket so it can be released
            except (ChunkedEncodingError, ContentDecodingError, RuntimeError):
                s.raw.read(decode_content=False)

            if len(s.history) >= self.max_redirects:
                raise TooManyRedirects(
                    f"Exceeded {self.max_redirects} redirects.", response=s
                )

            # Release the connection back into the pool.
            s.close()

            # Handle redirection without scheme (see: RFC 1808 Section 4)
            if C.startswith("//"):
                F = urlparse(s.url)
                C = ":".join([to_native_string(F.scheme), C])

            # Normalize url case and attach previous fragment if needed (RFC 7231 7.1.2)
            G = urlparse(C)
            if G.fragment == "" and D:
                G = G._replace(fragment=D)
            elif G.fragment:
                D = G.fragment
            C = G.geturl()

            # Facilitate relative 'location' headers, as allowed by RFC 7231.
            # (e.g. '/path/to/resource' instead of 'http://domain.tld/path/to/resource')
            # Compliant with RFC3986, we percent encode the url.
            if not G.netloc:
                C = urljoin(s.url, requote_uri(C))
            else:
                C = requote_uri(C)

            E.url = to_native_string(C)

            self.g(E, s)

            # https://github.com/psf/requests/issues/1084
            if s.status_code not in (
                codes.temporary_redirect,
                codes.permanent_redirect,
            ):
                # https://github.com/psf/requests/issues/3490
                H = ("Content-Length", "Content-Type", "Transfer-Encoding")
                for I in H:
                    E.headers.pop(I, None)
                E.body = None

            J = E.headers
            J.pop("Cookie", None)

            # Extract any cookies sent on the response to the cookiejar
            # in the new request. Because we've mutated our copied prepared
            # request, use the old one that we haven't yet touched.
            K = cast("CookieJar", E._cookies)
            extract_cookies_to_jar(K, t, s.raw)
            merge_cookies(K, self.cookies)
            E.prepare_cookies(K)

            # Rebuild auth and proxy information.
            y = self.f(E, y)
            self.e(E, s)

            # A failed tell() sets `_body_position` to `object()`. This non-None
            # value ensures `rewindable` will be True, allowing us to raise an
            # UnrewindableBodyError, instead of hanging the connection.
            L = E._body_position is not None and (
                "Content-Length" in J or "Transfer-Encoding" in J
            )

            # Attempt to rewind consumed file-like object.
            if L:
                rewind_body(E)

            # Override the original request.
            t = E

            if z:
                yield t  # type: ignore[misc]  # Internal use only, returns PreparedRequest
            else:
                s = self.a(
                    t,
                    stream=u,
                    timeout=v,
                    verify=w,
                    cert=x,
                    proxies=y,
                    allow_redirects=False,
                    **A,
                )

                extract_cookies_to_jar(self.cookies, E, s.raw)

                # extract redirect url, if any, for the next loop
                C = self.b(s)
                yield s

    def e(
        self, M: PreparedRequest, N: Response
    ) -> None:
        """When being redirected we may want to strip authentication from the
        request to avoid leaking credentials. This method intelligently removes
        and reapplies authentication where possible to avoid credential loss.
        """
        O = N.request
        assert _is_prepared(O)
        assert _is_prepared(M)

        P = M.headers
        Q = O.url
        R = M.url

        if "Authorization" in P and self.c(Q, R):
            # If we get redirected to a new host, we should strip out any
            # authentication headers.
            del P["Authorization"]

        # .netrc might have more auth for us on our new host.
        S = get_netrc_auth(R) if self.trust_env else None
        if S is not None:
            M.prepare_auth(S)

    def f(
        self,
        T: PreparedRequest,
        U: dict[str, str] | None,
    ) -> dict[str, str]:
        """This method re-evaluates the proxy configuration by considering the
        environment variables. If we are redirected to a URL covered by
        NO_PROXY, we strip the proxy configuration. Otherwise, we set missing
        proxy keys for this URL (in case they were stripped by a previous
        redirect).

        This method also replaces the Proxy-Authorization header where
        necessary.

        :rtype: dict
        """
        assert _is_prepared(T)
        V = T.headers
        W = urlparse(T.url).scheme
        X = resolve_proxies(T, U, self.trust_env)

        if "Proxy-Authorization" in V:
            del V["Proxy-Authorization"]

        try:
            Y, Z = get_auth_from_url(X[W])
        except KeyError:
            Y, Z = None, None

        # urllib3 handles proxy authorization for us in the standard adapter.
        # Avoid appending this to TLS tunneled requests where it may be leaked.
        if not W.startswith("https") and Y and Z:
            V["Proxy-Authorization"] = _basic_auth_str(Y, Z)

        return X

    def g(
        self, aa: PreparedRequest, ab: Response
    ) -> None:
        """When being redirected we may want to change the method of the request
        based on certain specs or browser behavior.
        """
        ac = aa.method

        # https://tools.ietf.org/html/rfc7231#section-6.4.4
        if ab.status_code == codes.see_other and ac != "HEAD":
            ac = "GET"

        # Do what the browsers do, despite standards...
        # First, turn 302s into GETs.
        if ab.status_code == codes.found and ac != "HEAD":
            ac = "GET"

        # Second, if a POST is responded to with a 301, turn it into a GET.
        # This bizarre behaviour is explained in Issue 1704.
        if ab.status_code == codes.moved and ac == "POST":
            ac = "GET"

        aa.method = ac
