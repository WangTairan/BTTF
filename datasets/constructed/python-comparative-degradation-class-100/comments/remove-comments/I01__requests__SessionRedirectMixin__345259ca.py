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
from .models import (   
    DEFAULT_REDIRECT_LIMIT,
    REDIRECT_STATI,
    PreparedRequest,
    Request,
    Response,
)
from .status_codes import codes
from .structures import CaseInsensitiveDict
from .utils import (   
    DEFAULT_PORTS,
    default_headers,
    get_auth_from_url,
    get_environ_proxies,
    get_netrc_auth,
    requote_uri,
    resolve_proxies,
    rewind_body,
    should_bypass_proxies,   
    to_key_val_list,
)

class SessionRedirectMixin:
    max_redirects: int
    trust_env: bool
    cookies: RequestsCookieJar

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response: ...

    def get_redirect_target(self, resp: Response) -> str | None:
        
         
         
         
         
         
         
        if resp.is_redirect:
            location = resp.headers["location"]
             
             
             
             
             
             
            location = location.encode("latin1")
            return to_native_string(location, "utf8")
        return None

    def should_strip_auth(self, old_url: str, new_url: str) -> bool:
        
        old_parsed = urlparse(old_url)
        new_parsed = urlparse(new_url)
        if old_parsed.hostname != new_parsed.hostname:
            return True
         
         
         
         
        if (
            old_parsed.scheme == "http"
            and old_parsed.port in (80, None)
            and new_parsed.scheme == "https"
            and new_parsed.port in (443, None)
        ):
            return False

         
        changed_port = old_parsed.port != new_parsed.port
        changed_scheme = old_parsed.scheme != new_parsed.scheme
        default_port = (DEFAULT_PORTS.get(old_parsed.scheme, None), None)
        if (
            not changed_scheme
            and old_parsed.port in default_port
            and new_parsed.port in default_port
        ):
            return False

         
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
        

        hist: list[Response] = []   

        url = self.get_redirect_target(resp)
        previous_fragment = urlparse(req.url).fragment
        while url:
            prepared_request = req.copy()

             
            resp.history = hist[:]
            hist.append(resp)

            try:
                resp.content   
            except (ChunkedEncodingError, ContentDecodingError, RuntimeError):
                resp.raw.read(decode_content=False)

            if len(resp.history) >= self.max_redirects:
                raise TooManyRedirects(
                    f"Exceeded {self.max_redirects} redirects.", response=resp
                )

             
            resp.close()

             
            if url.startswith("//"):
                parsed_rurl = urlparse(resp.url)
                url = ":".join([to_native_string(parsed_rurl.scheme), url])

             
            parsed = urlparse(url)
            if parsed.fragment == "" and previous_fragment:
                parsed = parsed._replace(fragment=previous_fragment)
            elif parsed.fragment:
                previous_fragment = parsed.fragment
            url = parsed.geturl()

             
             
             
            if not parsed.netloc:
                url = urljoin(resp.url, requote_uri(url))
            else:
                url = requote_uri(url)

            prepared_request.url = to_native_string(url)

            self.rebuild_method(prepared_request, resp)

             
            if resp.status_code not in (
                codes.temporary_redirect,
                codes.permanent_redirect,
            ):
                 
                purged_headers = ("Content-Length", "Content-Type", "Transfer-Encoding")
                for header in purged_headers:
                    prepared_request.headers.pop(header, None)
                prepared_request.body = None

            headers = prepared_request.headers
            headers.pop("Cookie", None)

             
             
             
            cookie_jar = cast("CookieJar", prepared_request._cookies)
            extract_cookies_to_jar(cookie_jar, req, resp.raw)
            merge_cookies(cookie_jar, self.cookies)
            prepared_request.prepare_cookies(cookie_jar)

             
            proxies = self.rebuild_proxies(prepared_request, proxies)
            self.rebuild_auth(prepared_request, resp)

             
             
             
            rewindable = prepared_request._body_position is not None and (
                "Content-Length" in headers or "Transfer-Encoding" in headers
            )

             
            if rewindable:
                rewind_body(prepared_request)

             
            req = prepared_request

            if yield_requests:
                yield req   
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

                 
                url = self.get_redirect_target(resp)
                yield resp

    def rebuild_auth(
        self, prepared_request: PreparedRequest, response: Response
    ) -> None:
        
        original_request = response.request
        assert _is_prepared(original_request)
        assert _is_prepared(prepared_request)

        headers = prepared_request.headers
        original_url = original_request.url
        url = prepared_request.url

        if "Authorization" in headers and self.should_strip_auth(original_url, url):
             
             
            del headers["Authorization"]

         
        new_auth = get_netrc_auth(url) if self.trust_env else None
        if new_auth is not None:
            prepared_request.prepare_auth(new_auth)

    def rebuild_proxies(
        self,
        prepared_request: PreparedRequest,
        proxies: dict[str, str] | None,
    ) -> dict[str, str]:
        
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

         
         
        if not scheme.startswith("https") and username and password:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)

        return new_proxies

    def rebuild_method(
        self, prepared_request: PreparedRequest, response: Response
    ) -> None:
        
        method = prepared_request.method

         
        if response.status_code == codes.see_other and method != "HEAD":
            method = "GET"

         
         
        if response.status_code == codes.found and method != "HEAD":
            method = "GET"

         
         
        if response.status_code == codes.moved and method == "POST":
            method = "GET"

        prepared_request.method = method
