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
        self.o("https://", HTTPAdapter())
        self.o("http://", HTTPAdapter())

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *q: Any) -> None:
        self.n()

    def a(self, s: Request) -> PreparedRequest:
        """Constructs a :class:`PreparedRequest <PreparedRequest>` for
        transmission and returns it. The :class:`PreparedRequest` has settings
        merged from the :class:`Request <Request>` instance and those of the
        :class:`Session`.

        :param request: :class:`Request` instance to prepare with this
            session's settings.
        :rtype: requests.PreparedRequest
        """
        t = cast("_t.UriType", s.url)
        u = cast(str, s.method)

        w = s.cookies or {}

        # Bootstrap CookieJar.
        if not isinstance(w, cookielib.CookieJar):
            w = cookiejar_from_dict(w)

        # Merge with session cookies
        x = merge_cookies(
            merge_cookies(RequestsCookieJar(), self.cookies), w
        )

        # Set environment's basic authentication if not explicitly set.
        y = s.auth
        if self.trust_env and not y and not self.auth:
            y = get_netrc_auth(t)

        z = PreparedRequest()
        z.prepare(
            method=u.upper(),
            url=t,
            files=s.files,
            data=s.data,
            json=s.json,
            headers=merge_setting(
                s.headers, self.headers, dict_class=CaseInsensitiveDict
            ),
            params=merge_setting(s.params, self.params),
            auth=merge_setting(y, self.auth),
            cookies=x,
            hooks=merge_hooks(s.hooks, self.hooks),
        )
        return z

    def b(
        self,
        A: str,
        B: _t.UriType,
        C: _t.ParamsType = None,
        D: _t.DataType = None,
        E: _t.HeadersType = None,
        F: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        G: _t.FilesType = None,
        H: _t.AuthType = None,
        I: _t.TimeoutType = None,
        J: bool = True,
        K: dict[str, str] | None = None,
        L: _t.HooksInputType | None = None,
        M: bool | None = None,
        N: _t.VerifyType | None = None,
        O: _t.CertType = None,
        P: _t.JsonType = None,
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
        if isinstance(B, bytes):
            B = B.decode("utf-8")

        # Create the Request.
        Q = Request(
            method=A.upper(),
            url=B,
            headers=E,
            files=G,
            data=D or {},
            json=P,
            params=C or {},
            auth=H,
            cookies=F,
            hooks=L,
        )
        R = self.a(Q)

        assert _is_prepared(R)

        K = K or {}

        S = self.l(
            R.url, K, M, N, O
        )

        # Send the request.
        T = {
            "timeout": I,
            "allow_redirects": J,
        }
        T.update(S)
        U = self.j(R, **T)

        return U

    def c(
        self,
        V: _t.UriType,
        W: _t.ParamsType = None,
        **X: Unpack[_t.GetKwargs],
    ) -> Response:
        r"""Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        X.setdefault("allow_redirects", True)
        return self.b("GET", V, params=W, **X)

    def d(self, Y: _t.UriType, **Z: Unpack[_t.RequestKwargs]) -> Response:
        r"""Sends a OPTIONS request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        Z.setdefault("allow_redirects", True)
        return self.b("OPTIONS", Y, **Z)

    def e(self, aa: _t.UriType, **ab: Unpack[_t.RequestKwargs]) -> Response:
        r"""Sends a HEAD request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        ab.setdefault("allow_redirects", False)
        return self.b("HEAD", aa, **ab)

    def f(
        self,
        ac: _t.UriType,
        ad: _t.DataType = None,
        ae: _t.JsonType = None,
        **af: Unpack[_t.PostKwargs],
    ) -> Response:
        r"""Sends a POST request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.b("POST", ac, data=ad, json=ae, **af)

    def g(
        self, ag: _t.UriType, ah: _t.DataType = None, **ai: Unpack[_t.DataKwargs]
    ) -> Response:
        r"""Sends a PUT request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.b("PUT", ag, data=ah, **ai)

    def h(
        self, aj: _t.UriType, ak: _t.DataType = None, **al: Unpack[_t.DataKwargs]
    ) -> Response:
        r"""Sends a PATCH request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.b("PATCH", aj, data=ak, **al)

    def i(self, am: _t.UriType, **an: Unpack[_t.RequestKwargs]) -> Response:
        r"""Sends a DELETE request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        return self.b("DELETE", am, **an)

    def j(self, ao: PreparedRequest, **ap: Any) -> Response:
        """Send a given PreparedRequest.

        :rtype: requests.Response
        """
        # Set defaults that the hooks can utilize to ensure they always have
        # the correct parameters to reproduce the previous request.
        ap.setdefault("stream", self.stream)
        ap.setdefault("verify", self.verify)
        ap.setdefault("cert", self.cert)
        if "proxies" not in ap:
            ap["proxies"] = resolve_proxies(ao, self.proxies, self.trust_env)

        # It's possible that users might accidentally send a Request object.
        # Guard against that specific failure case.
        if isinstance(ao, Request):
            raise ValueError("You can only send PreparedRequests.")

        assert _is_prepared(ao)

        # Set up variables needed for resolve_redirects and dispatching of hooks
        aq = ap.pop("allow_redirects", True)
        ar = ap.get("stream")
        at = ao.hooks

        # Get the appropriate adapter to use
        au = self.m(url=ao.url)

        # Start time (approximately) of the request
        av = preferred_clock()

        # Send the request
        aw = au.send(ao, **ap)

        # Total elapsed time of the request (approximately)
        ax = preferred_clock() - av
        aw.elapsed = timedelta(seconds=ax)

        # Response manipulation hooks
        aw = dispatch_hook("response", at, aw, **ap)

        # Persist cookies
        if aw.history:
            # If the hooks create history then we want those cookies too
            for ay in aw.history:
                extract_cookies_to_jar(self.cookies, ay.request, ay.raw)

        extract_cookies_to_jar(self.cookies, ao, aw.raw)

        # Resolve redirects if allowed.
        if aq:
            # Redirect resolving generator.
            az = self.resolve_redirects(aw, ao, **ap)
            aA = [ay for ay in az]
        else:
            aA = []

        # Shuffle things around if there's history.
        if aA:
            # Insert the first (original) request at the start
            aA.insert(0, aw)
            # Get the last request made
            aw = aA.pop()
            aw.history = aA

        # If redirects aren't being followed, store the response on the Request for Response.next().
        if not aq:
            try:
                aw._next = next(  # type: ignore[assignment]  # yield_requests=True returns PreparedRequest
                    self.resolve_redirects(aw, ao, yield_requests=True, **ap)
                )
            except StopIteration:
                pass

        if not ar:
            aw.content

        return aw

    def l(
        self,
        aB: str,
        aC: dict[str, str] | None,
        aD: bool | None,
        aE: _t.VerifyType | None,
        aF: _t.CertType,
    ) -> dict[str, Any]:
        """
        Check the environment and merge it with some settings.

        :rtype: dict
        """
        # Gather clues from the surrounding environment.
        if self.trust_env:
            # Set environment's proxies.
            aG = aC.get("no_proxy") if aC is not None else None
            aH = get_environ_proxies(aB, no_proxy=aG)
            if aC is not None:
                for aI, aJ in aH.items():
                    aC.setdefault(aI, aJ)

            # Look for requests environment configuration
            # and be compatible with cURL.
            if aE is True or aE is None:
                aE = (
                    os.environ.get("REQUESTS_CA_BUNDLE")
                    or os.environ.get("CURL_CA_BUNDLE")
                    or aE
                )

        # Merge all the kwargs.
        aC = merge_setting(aC, self.proxies)
        aD = merge_setting(aD, self.stream)
        aE = merge_setting(aE, self.verify)
        aF = merge_setting(aF, self.cert)

        return {"proxies": aC, "stream": aD, "verify": aE, "cert": aF}

    def m(self, aK: str) -> BaseAdapter:
        """
        Returns the appropriate connection adapter for the given URL.

        :rtype: requests.adapters.BaseAdapter
        """
        for aL, aM in self.adapters.items():
            if aK.lower().startswith(aL.lower()):
                return aM

        # Nothing matches :-/
        raise InvalidSchema(f"No connection adapters were found for {aK!r}")

    def n(self) -> None:
        """Closes all adapters and as such the session"""
        for aN in self.adapters.values():
            aN.close()

    def o(self, aO: str, aP: BaseAdapter) -> None:
        """Registers a connection adapter to a prefix.

        Adapters are sorted in descending order by prefix length.
        """
        self.adapters[aO] = aP
        aQ = [aR for aR in self.adapters if len(aR) < len(aO)]

        for aS in aQ:
            self.adapters[aS] = self.adapters.pop(aS)

    def __getstate__(self) -> dict[str, Any]:
        aT = {aU: getattr(self, aU, None) for aU in self.__attrs__}
        return aT

    def __setstate__(self, aV: dict[str, Any]) -> None:
        for aW, aX in aV.items():
            setattr(self, aW, aX)
