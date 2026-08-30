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

class Session(SessionRedirectMixin):
    """A Requests session.

    Provides cookie persistence, connection-pooling, and configuration.

    Basic Usage::

      >>> import requests
      >>> s = requests.Session()
      >>> s.get('https://httpbin.org/get')
      <Response [200]>

    Or as a context manager::

      >>> with requests.Session() as s:
      ...     s.get('https://httpbin.org/get')
      <Response [200]>
    """

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
        #: A case-insensitive dictionary of headers to be sent on each
        #: :class:`Request <Request>` sent from this
        #: :class:`Session <Session>`.
        self.headers = default_headers()

        #: Default Authentication tuple or object to attach to
        #: :class:`Request <Request>`.
        self.auth = None

        #: Dictionary mapping protocol or protocol and host to the URL of the proxy
        #: (e.g. {'http': 'foo.bar:3128', 'http://host.name': 'foo.bar:4012'}) to
        #: be used on each :class:`Request <Request>`.
        self.proxies = {}

        #: Event-handling hooks.
        self.hooks = default_hooks()

        #: Dictionary of querystring data to attach to each
        #: :class:`Request <Request>`. The dictionary values may be lists for
        #: representing multivalued query parameters.
        self.params = {}

        #: Stream response content default.
        self.stream = False

        #: SSL Verification default.
        #: Defaults to `True`, requiring requests to verify the TLS certificate at the
        #: remote end.
        #: If verify is set to `False`, requests will accept any TLS certificate
        #: presented by the server, and will ignore hostname mismatches and/or
        #: expired certificates, which will make your application vulnerable to
        #: man-in-the-middle (MitM) attacks.
        #: Only set this to `False` for testing.
        #: If verify is set to a string, it must be the path to a CA bundle file
        #: that will be used to verify the TLS certificate.
        self.verify = True

        #: SSL client certificate default, if String, path to ssl client
        #: cert file (.pem). If Tuple, ('cert', 'key') pair.
        self.cert = None

        #: Maximum number of redirects allowed. If the request exceeds this
        #: limit, a :class:`TooManyRedirects` exception is raised.
        #: This defaults to requests.models.DEFAULT_REDIRECT_LIMIT, which is
        #: 30.
        self.max_redirects = DEFAULT_REDIRECT_LIMIT

        #: Trust environment settings for proxy configuration, default
        #: authentication and similar.
        self.trust_env = True

        #: A CookieJar containing all currently outstanding cookies set on this
        #: session. By default it is a
        #: :class:`RequestsCookieJar <requests.cookies.RequestsCookieJar>`, but
        #: may be any other ``cookielib.CookieJar`` compatible object.
        self.cookies = cookiejar_from_dict({})

        # Default connection adapters.
        self.adapters = OrderedDict()
        self.mou("https://", HTTPAdapter())
        self.mou("http://", HTTPAdapter())

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *arg: Any) -> None:
        self.clo()

    def prepare2(self, req3: Request) -> PreparedRequest:
        """Constructs a :class:`PreparedRequest <PreparedRequest>` for
        transmission and returns it. The :class:`PreparedRequest` has settings
        merged from the :class:`Request <Request>` instance and those of the
        :class:`Session`.

        :param request: :class:`Request` instance to prepare with this
            session's settings.
        :rtype: requests.PreparedRequest
        """
        url2 = cast("_t.UriType", req3.url)
        met = cast(str, req3.method)

        coo = req3.cookies or {}

        # Bootstrap CookieJar.
        if not isinstance(coo, cookielib.CookieJar):
            coo = cookiejar_from_dict(coo)

        # Merge with session cookies
        merged = merge_cookies(
            merge_cookies(RequestsCookieJar(), self.cookies), coo
        )

        # Set environment's basic authentication if not explicitly set.
        aut = req3.auth
        if self.trust_env and not aut and not self.auth:
            aut = get_netrc_auth(url2)

        p2 = PreparedRequest()
        p2.prepare(
            method=met.upper(),
            url=url2,
            files=req3.files,
            data=req3.data,
            json=req3.json,
            headers=merge_setting(
                req3.headers, self.headers, dict_class=CaseInsensitiveDict
            ),
            params=merge_setting(req3.params, self.params),
            auth=merge_setting(aut, self.auth),
            cookies=merged,
            hooks=merge_hooks(req3.hooks, self.hooks),
        )
        return p2

    def req2(
        self,
        met2: str,
        url3: _t.UriType,
        par: _t.ParamsType = None,
        dat: _t.DataType = None,
        hea2: _t.HeadersType = None,
        coo2: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        fil: _t.FilesType = None,
        aut2: _t.AuthType = None,
        tim: _t.TimeoutType = None,
        allow: bool = True,
        pro: dict[str, str] | None = None,
        hoo: _t.HooksInputType | None = None,
        str2: bool | None = None,
        ver: _t.VerifyType | None = None,
        cer: _t.CertType = None,
        jso: _t.JsonType = None,
    ) -> Response:
        """Constructs a :class:`Request <Request>`, prepares it and sends it.
        Returns :class:`Response <Response>` object.

        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query
            string for the :class:`Request`.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the
            :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the
            :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the
            :class:`Request`.
        :param files: (optional) Dictionary of ``'filename': file-like-objects``
            for multipart encoding upload.
        :param auth: (optional) Auth tuple or callable to enable
            Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How many seconds to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Set to True by default.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol or protocol and
            hostname to the URL of the proxy.
        :param hooks: (optional) Dictionary mapping hook name to one event or
            list of events, event must be callable.
        :param stream: (optional) whether to immediately download the response
            content. Defaults to ``False``.
        :param verify: (optional) Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to ``True``. When set to
            ``False``, requests will accept any TLS certificate presented by
            the server, and will ignore hostname mismatches and/or expired
            certificates, which will make your application vulnerable to
            man-in-the-middle (MitM) attacks. Setting verify to ``False``
            may be useful during local development or testing.
        :param cert: (optional) if String, path to ssl client cert file (.pem).
            If Tuple, ('cert', 'key') pair.
        :rtype: requests.Response
        """
        if isinstance(url3, bytes):
            url3 = url3.decode("utf-8")

        # Create the Request.
        req4 = Request(
            method=met2.upper(),
            url=url3,
            headers=hea2,
            files=fil,
            data=dat or {},
            json=jso,
            params=par or {},
            auth=aut2,
            cookies=coo2,
            hooks=hoo,
        )
        pre = self.prepare2(req4)

        assert _is_prepared(pre)

        pro = pro or {}

        set = self.merge(
            pre.url, pro, str2, ver, cer
        )

        # Send the request.
        send2 = {
            "timeout": tim,
            "allow_redirects": allow,
        }
        send2.update(set)
        res = self.sen(pre, **send2)

        return res

    def get2(
        self,
        url4: _t.UriType,
        par2: _t.ParamsType = None,
        **kwa: Unpack[_t.GetKwargs],
    ) -> Response:
        r"""Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        kwa.setdefault("allow_redirects", True)
        return self.req2("GET", url4, params=par2, **kwa)

    def opt(self, url5: _t.UriType, **kwa2: Unpack[_t.RequestKwargs]) -> Response:
        r"""Sends a OPTIONS request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        kwa2.setdefault("allow_redirects", True)
        return self.req2("OPTIONS", url5, **kwa2)

    def hea(self, url6: _t.UriType, **kwa3: Unpack[_t.RequestKwargs]) -> Response:
        r"""Sends a HEAD request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        kwa3.setdefault("allow_redirects", False)
        return self.req2("HEAD", url6, **kwa3)

    def pos(
        self,
        url7: _t.UriType,
        dat2: _t.DataType = None,
        jso2: _t.JsonType = None,
        **kwa4: Unpack[_t.PostKwargs],
    ) -> Response:
        r"""Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.req2("POST", url7, data=dat2, json=jso2, **kwa4)

    def put(
        self, url8: _t.UriType, dat3: _t.DataType = None, **kwa5: Unpack[_t.DataKwargs]
    ) -> Response:
        r"""Sends a PUT request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.req2("PUT", url8, data=dat3, **kwa5)

    def pat(
        self, url9: _t.UriType, dat4: _t.DataType = None, **kwa6: Unpack[_t.DataKwargs]
    ) -> Response:
        r"""Sends a PATCH request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.req2("PATCH", url9, data=dat4, **kwa6)

    def del2(self, url10: _t.UriType, **kwa7: Unpack[_t.RequestKwargs]) -> Response:
        r"""Sends a DELETE request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.req2("DELETE", url10, **kwa7)

    def sen(self, req5: PreparedRequest, **kwa8: Any) -> Response:
        """Send a given PreparedRequest.

        :rtype: requests.Response
        """
        # Set defaults that the hooks can utilize to ensure they always have
        # the correct parameters to reproduce the previous request.
        kwa8.setdefault("stream", self.stream)
        kwa8.setdefault("verify", self.verify)
        kwa8.setdefault("cert", self.cert)
        if "proxies" not in kwa8:
            kwa8["proxies"] = resolve_proxies(req5, self.proxies, self.trust_env)

        # It's possible that users might accidentally send a Request object.
        # Guard against that specific failure case.
        if isinstance(req5, Request):
            raise ValueError("You can only send PreparedRequests.")

        assert _is_prepared(req5)

        # Set up variables needed for resolve_redirects and dispatching of hooks
        allow2 = kwa8.pop("allow_redirects", True)
        str3 = kwa8.get("stream")
        hoo2 = req5.hooks

        # Get the appropriate adapter to use
        ada = self.get3(url=req5.url)

        # Start time (approximately) of the request
        sta = preferred_clock()

        # Send the request
        r2 = ada.send(req5, **kwa8)

        # Total elapsed time of the request (approximately)
        ela = preferred_clock() - sta
        r2.elapsed = timedelta(seconds=ela)

        # Response manipulation hooks
        r2 = dispatch_hook("response", hoo2, r2, **kwa8)

        # Persist cookies
        if r2.history:
            # If the hooks create history then we want those cookies too
            for res2 in r2.history:
                extract_cookies_to_jar(self.cookies, res2.request, res2.raw)

        extract_cookies_to_jar(self.cookies, req5, r2.raw)

        # Resolve redirects if allowed.
        if allow2:
            # Redirect resolving generator.
            gen2 = self.resolve_redirects(r2, req5, **kwa8)
            his = [res2 for res2 in gen2]
        else:
            his = []

        # Shuffle things around if there's history.
        if his:
            # Insert the first (original) request at the start
            his.insert(0, r2)
            # Get the last request made
            r2 = his.pop()
            r2.history = his

        # If redirects aren't being followed, store the response on the Request for Response.next().
        if not allow2:
            try:
                r2._next = next(  # type: ignore[assignment]  # yield_requests=True returns PreparedRequest
                    self.resolve_redirects(r2, req5, yield_requests=True, **kwa8)
                )
            except StopIteration:
                pass

        if not str3:
            r2.content

        return r2

    def merge(
        self,
        url11: str,
        pro2: dict[str, str] | None,
        str4: bool | None,
        ver2: _t.VerifyType | None,
        cer2: _t.CertType,
    ) -> dict[str, Any]:
        """
        Check the environment and merge it with some settings.

        :rtype: dict
        """
        # Gather clues from the surrounding environment.
        if self.trust_env:
            # Set environment's proxies.
            no = pro2.get("no_proxy") if pro2 is not None else None
            env = get_environ_proxies(url11, no_proxy=no)
            if pro2 is not None:
                for k2, v2 in env.items():
                    pro2.setdefault(k2, v2)

            # Look for requests environment configuration
            # and be compatible with cURL.
            if ver2 is True or ver2 is None:
                ver2 = (
                    os.environ.get("REQUESTS_CA_BUNDLE")
                    or os.environ.get("CURL_CA_BUNDLE")
                    or ver2
                )

        # Merge all the kwargs.
        pro2 = merge_setting(pro2, self.proxies)
        str4 = merge_setting(str4, self.stream)
        ver2 = merge_setting(ver2, self.verify)
        cer2 = merge_setting(cer2, self.cert)

        return {"proxies": pro2, "stream": str4, "verify": ver2, "cert": cer2}

    def get3(self, url12: str) -> BaseAdapter:
        """
        Returns the appropriate connection adapter for the given URL.

        :rtype: requests.adapters.BaseAdapter
        """
        for pre2, ada2 in self.adapters.items():
            if url12.lower().startswith(pre2.lower()):
                return ada2

        # Nothing matches :-/
        raise InvalidSchema(f"No connection adapters were found for {url12!r}")

    def clo(self) -> None:
        """Closes all adapters and as such the session"""
        for v3 in self.adapters.values():
            v3.close()

    def mou(self, pre3: str, ada3: BaseAdapter) -> None:
        """Registers a connection adapter to a prefix.

        Adapters are sorted in descending order by prefix length.
        """
        self.adapters[pre3] = ada3
        keys = [k3 for k3 in self.adapters if len(k3) < len(pre3)]

        for key2 in keys:
            self.adapters[key2] = self.adapters.pop(key2)

    def __getstate__(self) -> dict[str, Any]:
        sta2 = {att: getattr(self, att, None) for att in self.__attrs__}
        return sta2

    def __setstate__(self, sta3: dict[str, Any]) -> None:
        for att2, val in sta3.items():
            setattr(self, att2, val)
