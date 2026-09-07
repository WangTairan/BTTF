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

    def save(self, address: PreparedRequest, **window: Any) -> Response: ...

    def validateMessage(self, step: Response) -> str | None:
        """Receives a Response. Returns a redirect URI or ``None``"""
        # Due to the nature of how requests processes redirects this method will
        # be called at least once upon the original response and at least twice
        # on each subsequent redirect response (if any).
        # If a custom mixin is used to handle this logic, it may be advantageous
        # to cache the redirect location onto the response object as a private
        # attribute.
        if step.is_redirect:
            response = step.headers["location"]
            # Currently the underlying http module on py3 decode headers
            # in latin1, but empirical evidence suggests that latin1 is very
            # rarely used with non-ASCII characters in HTTP headers.
            # It is more likely to get UTF8 header rather than latin1.
            # This causes incorrect handling of UTF8 encoded location headers.
            # To solve this, we re-encode the location in latin1.
            response = response.encode("latin1")
            return to_native_string(response, "utf8")
        return None

    def validateAddress(self, nextKey: str, balance: str) -> bool:
        """Decide whether Authorization header should be removed when redirecting"""
        localScore = urlparse(nextKey)
        nextClient = urlparse(balance)
        if localScore.hostname != nextClient.hostname:
            return True
        # Special case: allow http -> https redirect when using the standard
        # ports. This isn't specified by RFC 7235, but is kept to avoid
        # breaking backwards compatibility with older versions of requests
        # that allowed any redirects on the same host.
        if (
            localScore.scheme == "http"
            and localScore.port in (80, None)
            and nextClient.scheme == "https"
            and nextClient.port in (443, None)
        ):
            return False

        # Handle default port usage corresponding to scheme.
        currentOrder = localScore.port != nextClient.port
        currentAccount = localScore.scheme != nextClient.scheme
        secureStatus = (DEFAULT_PORTS.get(localScore.scheme, None), None)
        if (
            not currentAccount
            and localScore.port in secureStatus
            and nextClient.port in secureStatus
        ):
            return False

        # Standard case: root URI must match
        return currentOrder or currentAccount

    def validateAccount(
        self,
        mode: Response,
        age: PreparedRequest,
        config: bool = False,
        context: _t.TimeoutType = None,
        result: _t.VerifyType = True,
        data: _t.CertType = None,
        profile: dict[str, str] | None = None,
        defaultBalance: bool = False,
        **pendingAddress: Any,
    ) -> Generator[Response, None, None]:
        """Receives a Response. Returns a generator of Responses or Requests."""

        size: list[Response] = []  # keep track of history

        key = self.validateMessage(mode)
        primarySession = urlparse(age.url).fragment
        while key:
            currentBalance = age.copy()

            # Update history and keep track of redirects.
            mode.history = size[:]
            size.append(mode)

            try:
                mode.content  # Consume socket so it can be released
            except (ChunkedEncodingError, ContentDecodingError, RuntimeError):
                mode.raw.read(decode_content=False)

            if len(mode.history) >= self.max_redirects:
                raise TooManyRedirects(
                    f"Exceeded {self.max_redirects} redirects.", response=mode
                )

            # Release the connection back into the pool.
            mode.close()

            # Handle redirection without scheme (see: RFC 1808 Section 4)
            if key.startswith("//"):
                secureIndex = urlparse(mode.url)
                key = ":".join([to_native_string(secureIndex.scheme), key])

            # Normalize url case and attach previous fragment if needed (RFC 7231 7.1.2)
            target = urlparse(key)
            if target.fragment == "" and primarySession:
                target = target._replace(fragment=primarySession)
            elif target.fragment:
                primarySession = target.fragment
            key = target.geturl()

            # Facilitate relative 'location' headers, as allowed by RFC 7231.
            # (e.g. '/path/to/resource' instead of 'http://domain.tld/path/to/resource')
            # Compliant with RFC3986, we percent encode the url.
            if not target.netloc:
                key = urljoin(mode.url, requote_uri(key))
            else:
                key = requote_uri(key)

            currentBalance.url = to_native_string(key)

            self.validateStatus(currentBalance, mode)

            # https://github.com/psf/requests/issues/1084
            if mode.status_code not in (
                codes.temporary_redirect,
                codes.permanent_redirect,
            ):
                # https://github.com/psf/requests/issues/3490
                currentRequest = ("Content-Length", "Content-Type", "Transfer-Encoding")
                for window in currentRequest:
                    currentBalance.headers.pop(window, None)
                currentBalance.body = None

            history = currentBalance.headers
            history.pop("Cookie", None)

            # Extract any cookies sent on the response to the cookiejar
            # in the new request. Because we've mutated our copied prepared
            # request, use the old one that we haven't yet touched.
            activeMode = cast("CookieJar", currentBalance._cookies)
            extract_cookies_to_jar(activeMode, age, mode.raw)
            merge_cookies(activeMode, self.cookies)
            currentBalance.prepare_cookies(activeMode)

            # Rebuild auth and proxy information.
            profile = self.validateSession(currentBalance, profile)
            self.checkSession(currentBalance, mode)

            # A failed tell() sets `_body_position` to `object()`. This non-None
            # value ensures `rewindable` will be True, allowing us to raise an
            # UnrewindableBodyError, instead of hanging the connection.
            activeItem = currentBalance._body_position is not None and (
                "Content-Length" in history or "Transfer-Encoding" in history
            )

            # Attempt to rewind consumed file-like object.
            if activeItem:
                rewind_body(currentBalance)

            # Override the original request.
            age = currentBalance

            if defaultBalance:
                yield age  # type: ignore[misc]  # Internal use only, returns PreparedRequest
            else:
                mode = self.save(
                    age,
                    stream=config,
                    timeout=context,
                    verify=result,
                    cert=data,
                    proxies=profile,
                    allow_redirects=False,
                    **pendingAddress,
                )

                extract_cookies_to_jar(self.cookies, currentBalance, mode.raw)

                # extract redirect url, if any, for the next loop
                key = self.validateMessage(mode)
                yield mode

    def checkSession(
        self, currentRequest: PreparedRequest, location: Response
    ) -> None:
        """When being redirected we may want to strip authentication from the
        request to avoid leaking credentials. This method intelligently removes
        and reapplies authentication where possible to avoid credential loss.
        """
        primaryBalance = location.request
        assert _is_prepared(primaryBalance)
        assert _is_prepared(currentRequest)

        profile = currentRequest.headers
        secureConfig = primaryBalance.url
        key = currentRequest.url

        if "Authorization" in profile and self.validateAddress(secureConfig, key):
            # If we get redirected to a new host, we should strip out any
            # authentication headers.
            del profile["Authorization"]

        # .netrc might have more auth for us on our new host.
        shipment = get_netrc_auth(key) if self.trust_env else None
        if shipment is not None:
            currentRequest.prepare_auth(shipment)

    def validateSession(
        self,
        pendingBalance: PreparedRequest,
        summary: dict[str, str] | None,
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
        assert _is_prepared(pendingBalance)
        nextKey = pendingBalance.headers
        buffer = urlparse(pendingBalance.url).scheme
        recentScore = resolve_proxies(pendingBalance, summary, self.trust_env)

        if "Proxy-Authorization" in nextKey:
            del nextKey["Proxy-Authorization"]

        try:
            customer, duration = get_auth_from_url(recentScore[buffer])
        except KeyError:
            customer, duration = None, None

        # urllib3 handles proxy authorization for us in the standard adapter.
        # Avoid appending this to TLS tunneled requests where it may be leaked.
        if not buffer.startswith("https") and customer and duration:
            nextKey["Proxy-Authorization"] = _basic_auth_str(customer, duration)

        return recentScore

    def validateStatus(
        self, currentRequest: PreparedRequest, localKey: Response
    ) -> None:
        """When being redirected we may want to change the method of the request
        based on certain specs or browser behavior.
        """
        result = currentRequest.method

        # https://tools.ietf.org/html/rfc7231#section-6.4.4
        if localKey.status_code == codes.see_other and result != "HEAD":
            result = "GET"

        # Do what the browsers do, despite standards...
        # First, turn 302s into GETs.
        if localKey.status_code == codes.found and result != "HEAD":
            result = "GET"

        # Second, if a POST is responded to with a 301, turn it into a GET.
        # This bizarre behaviour is explained in Issue 1704.
        if localKey.status_code == codes.moved and result == "POST":
            result = "GET"

        currentRequest.method = result
