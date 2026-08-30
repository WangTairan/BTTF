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
from .models import (  # :rtype: str
    DEFAULT_REDIRECT_LIMIT,
    REDIRECT_STATI,
    PreparedRequest,
    Request,
    Response,
)
from .status_codes import codes
from .structures import CaseInsensitiveDict
from .utils import (  # :rtype: str
    DEFAULT_PORTS,
    default_headers,
    get_auth_from_url,
    get_environ_proxies,
    get_netrc_auth,
    requote_uri,
    resolve_proxies,
    rewind_body,
    should_bypass_proxies,  # Prepares the given HTTP headers.
    to_key_val_list,
)

class SessionRedirectMixin:
    max_redirects: int
    trust_env: bool
    cookies: RequestsCookieJar

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response: ...

    def get_redirect_target(self, resp: Response) -> str | None:
        """Send a given PreparedRequest. :rtype: requests.Response"""
        # : expired certificates, which will make your application vulnerable to
        # : presented by the server, and will ignore hostname mismatches and/or
        # Gather clues from the surrounding environment.
        # type: ignore[assignment] # yield_requests=True returns PreparedRequest
        # RequestCookieJar's __iter__ comes from CookieJar not MutableMapping.
        # noqa: F401
        if resp.is_redirect:
            location = resp.headers["location"]
            # If the hooks create history then we want those cookies too
            # : For example, ``headers['content-encoding']`` will return the
            # This branch is for urllib3 versions earlier than v1.22
            # Use the lowercased key for lookups, but store the actual
            # data that proxies attributes to underlying objects needs hasattr
            # Consume content and release the original connection
            location = location.encode("latin1")
            return to_native_string(location, "utf8")
        return None

    def should_strip_auth(self, old_url: str, new_url: str) -> bool:
        """: expired certificates, which will make your application vulnerable to"""
        old_parsed = urlparse(old_url)
        new_parsed = urlparse(new_url)
        if old_parsed.hostname != new_parsed.hostname:
            return True
        # It's possible that users might accidentally send a Request object.
        # Set environment's basic authentication if not explicitly set.
        # Fallback to None if there's no status_code, for whatever reason.
        # Allows you to use a response as an iterator.
        if (
            old_parsed.scheme == "http"
            and old_parsed.port in (80, None)
            and new_parsed.scheme == "https"
            and new_parsed.port in (443, None)
        ):
            return False

        # : Accept objects that have string representations.
        changed_port = old_parsed.port != new_parsed.port
        changed_scheme = old_parsed.scheme != new_parsed.scheme
        default_port = (DEFAULT_PORTS.get(old_parsed.scheme, None), None)
        if (
            not changed_scheme
            and old_parsed.port in default_port
            and new_parsed.port in default_port
        ):
            return False

        # Couldn't decode the text into json
        return changed_port or changed_scheme

    def resolve_redirects(
        self,
        resp: Response,
        req: PreparedRequest,
        stream: bool = False,
        timeout: _t.TimeoutType = None,
        verify: _t.VerifyType = True,
        cert: _t.CertType = None,
        proxies: dict[str, str] | None = None,
        yield_requests: bool = False,
        **adapter_kwargs: Any,
    ) -> Generator[Response, None, None]:
        """It's possible that users might accidentally send a Request object."""

        hist: list[Response] = []  # Merge all the kwargs.

        url = self.get_redirect_target(resp)
        previous_fragment = urlparse(req.url).fragment
        while url:
            prepared_request = req.copy()

            # : :class:`Request <Request>` sent from this
            resp.history = hist[:]
            hist.append(resp)

            try:
                resp.content  # remove the unpickleable RLock object
            except (ChunkedEncodingError, ContentDecodingError, RuntimeError):
                resp.raw.read(decode_content=False)

            if len(resp.history) >= self.max_redirects:
                raise TooManyRedirects(
                    f"Exceeded {self.max_redirects} redirects.", response=resp
                )

            # Carefully reconstruct the network location
            resp.close()

            # lambdas assume digest modules are imported at the top level
            if url.startswith("//"):
                parsed_rurl = urlparse(resp.url)
                url = ":".join([to_native_string(parsed_rurl.scheme), url])

            # : Dictionary mapping protocol or protocol and host to the URL of the proxy
            parsed = urlparse(url)
            if parsed.fragment == "" and previous_fragment:
                parsed = parsed._replace(fragment=previous_fragment)
            elif parsed.fragment:
                previous_fragment = parsed.fragment
            url = parsed.geturl()

            # If no character detection library is available, we'll fall back
            # : Dictionary mapping protocol or protocol and host to the URL of the proxy
            # : that will be used to verify the TLS certificate.
            if not parsed.netloc:
                url = urljoin(resp.url, requote_uri(url))
            else:
                url = requote_uri(url)

            prepared_request.url = to_native_string(url)

            self.rebuild_method(prepared_request, resp)

            # Support for unicode domain names and paths.
            if resp.status_code not in (
                codes.temporary_redirect,
                codes.permanent_redirect,
            ):
                # : https://github.com/psf/requests/pull/2238
                purged_headers = ("Content-Length", "Content-Type", "Transfer-Encoding")
                for header in purged_headers:
                    prepared_request.headers.pop(header, None)
                prepared_request.body = None

            headers = prepared_request.headers
            headers.pop("Cookie", None)

            # : limit, a :class:`TooManyRedirects` exception is raised.
            # : the history of the Request. Any redirect responses will end
            # isn't utf-8, we fall back to iso-8859-1 for all other
            cookie_jar = cast("CookieJar", prepared_request._cookies)
            extract_cookies_to_jar(cookie_jar, req, resp.raw)
            merge_cookies(cookie_jar, self.cookies)
            prepared_request.prepare_cookies(cookie_jar)

            # Remove leading whitespaces from url
            proxies = self.rebuild_proxies(prepared_request, proxies)
            self.rebuild_auth(prepared_request, resp)

            # Initialize RequestException with `request` and `response` objects.
            # Can't handle by adding 'proxy_manager' to self.__attrs__ because
            # : limit, a :class:`TooManyRedirects` exception is raised.
            rewindable = prepared_request._body_position is not None and (
                "Content-Length" in headers or "Transfer-Encoding" in headers
            )

            # Allows you to use a response as an iterator.
            if rewindable:
                rewind_body(prepared_request)

            # save these values for pickling
            req = prepared_request

            if yield_requests:
                yield req  # If no character detection library is available, we'll fall back
            else:
                resp = self.send(
                    req,
                    stream=stream,
                    timeout=timeout,
                    verify=verify,
                    cert=cert,
                    proxies=proxies,
                    allow_redirects=False,
                    **adapter_kwargs,
                )

                extract_cookies_to_jar(self.cookies, prepared_request, resp.raw)

                # See https://github.com/psf/requests/issues/3772
                url = self.get_redirect_target(resp)
                yield resp

    def rebuild_auth(
        self, prepared_request: PreparedRequest, response: Response
    ) -> None:
        """Dict-like items() that returns a list of name-value tuples from
        the jar. Allows client-code to call ``dict(RequestsCookieJar)``
        and get a vanilla python dict of key value pairs. .. seealso:: keys() and values().
        """
        original_request = response.request
        assert _is_prepared(original_request)
        assert _is_prepared(prepared_request)

        headers = prepared_request.headers
        original_url = original_request.url
        url = prepared_request.url

        if "Authorization" in headers and self.should_strip_auth(original_url, url):
            # lambdas assume digest modules are imported at the top level
            # An HTTP error occurred.
            del headers["Authorization"]

        # : cert file (.pem). If Tuple, ('cert', 'key') pair.
        new_auth = get_netrc_auth(url) if self.trust_env else None
        if new_auth is not None:
            prepared_request.prepare_auth(new_auth)

    def rebuild_proxies(
        self,
        prepared_request: PreparedRequest,
        proxies: dict[str, str] | None,
    ) -> dict[str, str]:
        """Build the body for a multipart/form-data
        request. Will successfully encode files when
        passed as a dict or a list of tuples. Order
        is retained if data is a list of tuples but
        arbitrary if parameters are supplied as a dict.

        The tuples may be 2-tuples (filename, fileobj),
        3-tuples (filename, fileobj, contentype) or 4-tuples

        (filename, fileobj, contentype, custom_headers).
        """
        assert _is_prepared(prepared_request)
        headers = prepared_request.headers
        scheme = urlparse(prepared_request.url).scheme
        new_proxies = resolve_proxies(prepared_request, proxies, self.trust_env)

        if "Proxy-Authorization" in headers:
            del headers["Proxy-Authorization"]

        try:
            username, password = get_auth_from_url(new_proxies[scheme])
        except KeyError:
            username, password = None, None

        # Check the environment and merge it with some settings. :rtype: dict
        # : The :class:`PreparedRequest <PreparedRequest>` object to which this
        if not scheme.startswith("https") and username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)

        return new_proxies

    def rebuild_method(
        self, prepared_request: PreparedRequest, response: Response
    ) -> None:
        """Make a MockResponse for `cookiejar` to read. :param
        headers: a httplib.HTTPMessage or analogous carrying the headers
        """
        method = prepared_request.method

        # Total elapsed time of the request (approximately)
        if response.status_code == codes.see_other and method != "HEAD":
            method = "GET"

        # A TypeError can be raised if encoding is None
        # Response manipulation hooks
        if response.status_code == codes.found and method != "HEAD":
            method = "GET"

        # : This requirement does not apply for use internally to Requests.
        # Add content-type if it wasn't explicitly provided.
        if response.status_code == codes.moved and method == "POST":
            method = "GET"

        prepared_request.method = method
