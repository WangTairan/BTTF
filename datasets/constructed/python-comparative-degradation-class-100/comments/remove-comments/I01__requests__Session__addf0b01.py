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

class Session(SessionRedirectMixin):
    

    headers: CaseInsensitiveDict[str]
    auth: _t.AuthType
    proxies: dict[str, str]
    hooks: dict[str, list[_t.HookType]]
    params: MutableMapping[str, Any]
    stream: bool
    verify: _t.VerifyType
    cert: _t.CertType
    max_redirects: int
    trust_env: bool
    cookies: RequestsCookieJar
    adapters: MutableMapping[str, BaseAdapter]

    __attrs__: list[str] = [
        "headers",
        "cookies",
        "auth",
        "proxies",
        "hooks",
        "params",
        "verify",
        "cert",
        "adapters",
        "stream",
        "trust_env",
        "max_redirects",
    ]

    def __init__(self) -> None:
         
         
         
        self.headers = default_headers()

         
         
        self.auth = None

         
         
         
        self.proxies = {}

         
        self.hooks = default_hooks()

         
         
         
        self.params = {}

         
        self.stream = False

         
         
         
         
         
         
         
         
         
         
        self.verify = True

         
         
        self.cert = None

         
         
         
         
        self.max_redirects = DEFAULT_REDIRECT_LIMIT

         
         
        self.trust_env = True

         
         
         
         
        self.cookies = cookiejar_from_dict({})

         
        self.adapters = OrderedDict()
        self.mount("https://", HTTPAdapter())
        self.mount("http://", HTTPAdapter())

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def prepare_request(self, request: Request) -> PreparedRequest:
        
        url = cast("_t.UriType", request.url)
        method = cast(str, request.method)

        cookies = request.cookies or {}

         
        if not isinstance(cookies, cookielib.CookieJar):
            cookies = cookiejar_from_dict(cookies)

         
        merged_cookies = merge_cookies(
            merge_cookies(RequestsCookieJar(), self.cookies), cookies
        )

         
        auth = request.auth
        if self.trust_env and not auth and not self.auth:
            auth = get_netrc_auth(url)

        p = PreparedRequest()
        p.prepare(
            method=method.upper(),
            url=url,
            files=request.files,
            data=request.data,
            json=request.json,
            headers=merge_setting(
                request.headers, self.headers, dict_class=CaseInsensitiveDict
            ),
            params=merge_setting(request.params, self.params),
            auth=merge_setting(auth, self.auth),
            cookies=merged_cookies,
            hooks=merge_hooks(request.hooks, self.hooks),
        )
        return p

    def request(
        self,
        method: str,
        url: _t.UriType,
        params: _t.ParamsType = None,
        data: _t.DataType = None,
        headers: _t.HeadersType = None,
        cookies: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        files: _t.FilesType = None,
        auth: _t.AuthType = None,
        timeout: _t.TimeoutType = None,
        allow_redirects: bool = True,
        proxies: dict[str, str] | None = None,
        hooks: _t.HooksInputType | None = None,
        stream: bool | None = None,
        verify: _t.VerifyType | None = None,
        cert: _t.CertType = None,
        json: _t.JsonType = None,
    ) -> Response:
        
        if isinstance(url, bytes):
            url = url.decode("utf-8")

         
        req = Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            hooks=hooks,
        )
        prep = self.prepare_request(req)

        assert _is_prepared(prep)

        proxies = proxies or {}

        settings = self.merge_environment_settings(
            prep.url, proxies, stream, verify, cert
        )

         
        send_kwargs = {
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        }
        send_kwargs.update(settings)
        resp = self.send(prep, **send_kwargs)

        return resp

    def get(
        self,
        url: _t.UriType,
        params: _t.ParamsType = None,
        **kwargs: Unpack[_t.GetKwargs],
    ) -> Response:
        

        kwargs.setdefault("allow_redirects", True)
        return self.request("GET", url, params=params, **kwargs)

    def options(self, url: _t.UriType, **kwargs: Unpack[_t.RequestKwargs]) -> Response:
        

        kwargs.setdefault("allow_redirects", True)
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url: _t.UriType, **kwargs: Unpack[_t.RequestKwargs]) -> Response:
        

        kwargs.setdefault("allow_redirects", False)
        return self.request("HEAD", url, **kwargs)

    def post(
        self,
        url: _t.UriType,
        data: _t.DataType = None,
        json: _t.JsonType = None,
        **kwargs: Unpack[_t.PostKwargs],
    ) -> Response:
        

        return self.request("POST", url, data=data, json=json, **kwargs)

    def put(
        self, url: _t.UriType, data: _t.DataType = None, **kwargs: Unpack[_t.DataKwargs]
    ) -> Response:
        

        return self.request("PUT", url, data=data, **kwargs)

    def patch(
        self, url: _t.UriType, data: _t.DataType = None, **kwargs: Unpack[_t.DataKwargs]
    ) -> Response:
        

        return self.request("PATCH", url, data=data, **kwargs)

    def delete(self, url: _t.UriType, **kwargs: Unpack[_t.RequestKwargs]) -> Response:
        

        return self.request("DELETE", url, **kwargs)

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response:
        
         
         
        kwargs.setdefault("stream", self.stream)
        kwargs.setdefault("verify", self.verify)
        kwargs.setdefault("cert", self.cert)
        if "proxies" not in kwargs:
            kwargs["proxies"] = resolve_proxies(request, self.proxies, self.trust_env)

         
         
        if isinstance(request, Request):
            raise ValueError("You can only send PreparedRequests.")

        assert _is_prepared(request)

         
        allow_redirects = kwargs.pop("allow_redirects", True)
        stream = kwargs.get("stream")
        hooks = request.hooks

         
        adapter = self.get_adapter(url=request.url)

         
        start = preferred_clock()

         
        r = adapter.send(request, **kwargs)

         
        elapsed = preferred_clock() - start
        r.elapsed = timedelta(seconds=elapsed)

         
        r = dispatch_hook("response", hooks, r, **kwargs)

         
        if r.history:
             
            for resp in r.history:
                extract_cookies_to_jar(self.cookies, resp.request, resp.raw)

        extract_cookies_to_jar(self.cookies, request, r.raw)

         
        if allow_redirects:
             
            gen = self.resolve_redirects(r, request, **kwargs)
            history = [resp for resp in gen]
        else:
            history = []

         
        if history:
             
            history.insert(0, r)
             
            r = history.pop()
            r.history = history

         
        if not allow_redirects:
            try:
                r._next = next(   
                    self.resolve_redirects(r, request, yield_requests=True, **kwargs)
                )
            except StopIteration:
                pass

        if not stream:
            r.content

        return r

    def merge_environment_settings(
        self,
        url: str,
        proxies: dict[str, str] | None,
        stream: bool | None,
        verify: _t.VerifyType | None,
        cert: _t.CertType,
    ) -> dict[str, Any]:
        
         
        if self.trust_env:
             
            no_proxy = proxies.get("no_proxy") if proxies is not None else None
            env_proxies = get_environ_proxies(url, no_proxy=no_proxy)
            if proxies is not None:
                for k, v in env_proxies.items():
                    proxies.setdefault(k, v)

             
             
            if verify is True or verify is None:
                verify = (
                    os.environ.get("REQUESTS_CA_BUNDLE")
                    or os.environ.get("CURL_CA_BUNDLE")
                    or verify
                )

         
        proxies = merge_setting(proxies, self.proxies)
        stream = merge_setting(stream, self.stream)
        verify = merge_setting(verify, self.verify)
        cert = merge_setting(cert, self.cert)

        return {"proxies": proxies, "stream": stream, "verify": verify, "cert": cert}

    def get_adapter(self, url: str) -> BaseAdapter:
        
        for prefix, adapter in self.adapters.items():
            if url.lower().startswith(prefix.lower()):
                return adapter

         
        raise InvalidSchema(f"No connection adapters were found for {url!r}")

    def close(self) -> None:
        
        for v in self.adapters.values():
            v.close()

    def mount(self, prefix: str, adapter: BaseAdapter) -> None:
        
        self.adapters[prefix] = adapter
        keys_to_move = [k for k in self.adapters if len(k) < len(prefix)]

        for key in keys_to_move:
            self.adapters[key] = self.adapters.pop(key)

    def __getstate__(self) -> dict[str, Any]:
        state = {attr: getattr(self, attr, None) for attr in self.__attrs__}
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        for attr, value in state.items():
            setattr(self, attr, value)
