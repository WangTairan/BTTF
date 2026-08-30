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

    def sen(self, req2: PreparedRequest, **kwa: Any) -> Response: ...

    def get2(self, res: Response) -> str | None:
        """Receives a Response. Returns a redirect URI or ``None``"""
        # Due to the nature of how requests processes redirects this method will
        # be called at least once upon the original response and at least twice
        # on each subsequent redirect response (if any).
        # If a custom mixin is used to handle this logic, it may be advantageous
        # to cache the redirect location onto the response object as a private
        # attribute.
        if res.is_redirect:
            loc = res.headers["location"]
            # Currently the underlying http module on py3 decode headers
            # in latin1, but empirical evidence suggests that latin1 is very
            # rarely used with non-ASCII characters in HTTP headers.
            # It is more likely to get UTF8 header rather than latin1.
            # This causes incorrect handling of UTF8 encoded location headers.
            # To solve this, we re-encode the location in latin1.
            loc = loc.encode("latin1")
            return to_native_string(loc, "utf8")
        return None

    def should(self, old: str, new: str) -> bool:
        """Decide whether Authorization header should be removed when redirecting"""
        old2 = urlparse(old)
        new2 = urlparse(new)
        if old2.hostname != new2.hostname:
            return True
        # Special case: allow http -> https redirect when using the standard
        # ports. This isn't specified by RFC 7235, but is kept to avoid
        # breaking backwards compatibility with older versions of requests
        # that allowed any redirects on the same host.
        if (
            old2.scheme == "http"
            and old2.port in (80, None)
            and new2.scheme == "https"
            and new2.port in (443, None)
        ):
            return False

        # Handle default port usage corresponding to scheme.
        changed = old2.port != new2.port
        changed2 = old2.scheme != new2.scheme
        default = (DEFAULT_PORTS.get(old2.scheme, None), None)
        if (
            not changed2
            and old2.port in default
            and new2.port in default
        ):
            return False

        # Standard case: root URI must match
        return changed or changed2

    def resolve(
        self,
        res2: Response,
        req3: PreparedRequest,
        str2: bool = False,
        tim: _t.TimeoutType = None,
        ver: _t.VerifyType = True,
        cer: _t.CertType = None,
        pro: dict[str, str] | None = None,
        yield2: bool = False,
        **adapter: Any,
    ) -> Generator[Response, None, None]:
        """Receives a Response. Returns a generator of Responses or Requests."""

        his: list[Response] = []  # keep track of history

        url2 = self.get2(res2)
        previous = urlparse(req3.url).fragment
        while url2:
            prepared = req3.copy()

            # Update history and keep track of redirects.
            res2.history = his[:]
            his.append(res2)

            try:
                res2.content  # Consume socket so it can be released
            except (ChunkedEncodingError, ContentDecodingError, RuntimeError):
                res2.raw.read(decode_content=False)

            if len(res2.history) >= self.max_redirects:
                raise TooManyRedirects(
                    f"Exceeded {self.max_redirects} redirects.", response=res2
                )

            # Release the connection back into the pool.
            res2.close()

            # Handle redirection without scheme (see: RFC 1808 Section 4)
            if url2.startswith("//"):
                parsed2 = urlparse(res2.url)
                url2 = ":".join([to_native_string(parsed2.scheme), url2])

            # Normalize url case and attach previous fragment if needed (RFC 7231 7.1.2)
            par = urlparse(url2)
            if par.fragment == "" and previous:
                par = par._replace(fragment=previous)
            elif par.fragment:
                previous = par.fragment
            url2 = par.geturl()

            # Facilitate relative 'location' headers, as allowed by RFC 7231.
            # (e.g. '/path/to/resource' instead of 'http://domain.tld/path/to/resource')
            # Compliant with RFC3986, we percent encode the url.
            if not par.netloc:
                url2 = urljoin(res2.url, requote_uri(url2))
            else:
                url2 = requote_uri(url2)

            prepared.url = to_native_string(url2)

            self.rebuild3(prepared, res2)

            # https://github.com/psf/requests/issues/1084
            if res2.status_code not in (
                codes.temporary_redirect,
                codes.permanent_redirect,
            ):
                # https://github.com/psf/requests/issues/3490
                purged = ("Content-Length", "Content-Type", "Transfer-Encoding")
                for hea in purged:
                    prepared.headers.pop(hea, None)
                prepared.body = None

            hea2 = prepared.headers
            hea2.pop("Cookie", None)

            # Extract any cookies sent on the response to the cookiejar
            # in the new request. Because we've mutated our copied prepared
            # request, use the old one that we haven't yet touched.
            cookie = cast("CookieJar", prepared._cookies)
            extract_cookies_to_jar(cookie, req3, res2.raw)
            merge_cookies(cookie, self.cookies)
            prepared.prepare_cookies(cookie)

            # Rebuild auth and proxy information.
            pro = self.rebuild2(prepared, pro)
            self.rebuild(prepared, res2)

            # A failed tell() sets `_body_position` to `object()`. This non-None
            # value ensures `rewindable` will be True, allowing us to raise an
            # UnrewindableBodyError, instead of hanging the connection.
            rew = prepared._body_position is not None and (
                "Content-Length" in hea2 or "Transfer-Encoding" in hea2
            )

            # Attempt to rewind consumed file-like object.
            if rew:
                rewind_body(prepared)

            # Override the original request.
            req3 = prepared

            if yield2:
                yield req3  # type: ignore[misc]  # Internal use only, returns PreparedRequest
            else:
                res2 = self.sen(
                    req3,
                    stream=str2,
                    timeout=tim,
                    verify=ver,
                    cert=cer,
                    proxies=pro,
                    allow_redirects=False,
                    **adapter,
                )

                extract_cookies_to_jar(self.cookies, prepared, res2.raw)

                # extract redirect url, if any, for the next loop
                url2 = self.get2(res2)
                yield res2

    def rebuild(
        self, prepared2: PreparedRequest, res3: Response
    ) -> None:
        """When being redirected we may want to strip authentication from the
        request to avoid leaking credentials. This method intelligently removes
        and reapplies authentication where possible to avoid credential loss.
        """
        original = res3.request
        assert _is_prepared(original)
        assert _is_prepared(prepared2)

        hea3 = prepared2.headers
        original2 = original.url
        url3 = prepared2.url

        if "Authorization" in hea3 and self.should(original2, url3):
            # If we get redirected to a new host, we should strip out any
            # authentication headers.
            del hea3["Authorization"]

        # .netrc might have more auth for us on our new host.
        new3 = get_netrc_auth(url3) if self.trust_env else None
        if new3 is not None:
            prepared2.prepare_auth(new3)

    def rebuild2(
        self,
        prepared3: PreparedRequest,
        pro2: dict[str, str] | None,
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
        assert _is_prepared(prepared3)
        hea4 = prepared3.headers
        sch = urlparse(prepared3.url).scheme
        new4 = resolve_proxies(prepared3, pro2, self.trust_env)

        if "Proxy-Authorization" in hea4:
            del hea4["Proxy-Authorization"]

        try:
            use, pas = get_auth_from_url(new4[sch])
        except KeyError:
            use, pas = None, None

        # urllib3 handles proxy authorization for us in the standard adapter.
        # Avoid appending this to TLS tunneled requests where it may be leaked.
        if not sch.startswith("https") and use and pas:
            hea4["Proxy-Authorization"] = _basic_auth_str(use, pas)

        return new4

    def rebuild3(
        self, prepared4: PreparedRequest, res4: Response
    ) -> None:
        """When being redirected we may want to change the method of the request
        based on certain specs or browser behavior.
        """
        met = prepared4.method

        # https://tools.ietf.org/html/rfc7231#section-6.4.4
        if res4.status_code == codes.see_other and met != "HEAD":
            met = "GET"

        # Do what the browsers do, despite standards...
        # First, turn 302s into GETs.
        if res4.status_code == codes.found and met != "HEAD":
            met = "GET"

        # Second, if a POST is responded to with a 301, turn it into a GET.
        # This bizarre behaviour is explained in Issue 1704.
        if res4.status_code == codes.moved and met == "POST":
            met = "GET"

        prepared4.method = met
