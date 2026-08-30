from __future__ import annotations
import os.path
import socket  # noqa: F401
import typing
import warnings
from typing import Any
from urllib3.exceptions import (
    ClosedPoolError,
    ConnectTimeoutError,
    LocationValueError,
    MaxRetryError,
    NewConnectionError,
    ProtocolError,
    ReadTimeoutError,
    ResponseError,
)
from urllib3.exceptions import HTTPError as _HTTPError
from urllib3.exceptions import InvalidHeader as _InvalidHeader
from urllib3.exceptions import ProxyError as _ProxyError
from urllib3.exceptions import SSLError as _SSLError
from urllib3.poolmanager import PoolManager, proxy_from_url
from urllib3.util import Timeout as TimeoutSauce
from urllib3.util import parse_url
from urllib3.util.retry import Retry
from .auth import _basic_auth_str
from .compat import basestring, urlparse
from .cookies import extract_cookies_to_jar
from .exceptions import (
    ConnectionError,
    ConnectTimeout,
    InvalidHeader,
    InvalidProxyURL,
    InvalidSchema,
    InvalidURL,
    ProxyError,
    ReadTimeout,
    RetryError,
    SSLError,
)
from .models import Response
from .structures import CaseInsensitiveDict
from .utils import (
    DEFAULT_CA_BUNDLE_PATH,
    get_auth_from_url,
    get_encoding_from_headers,
    prepend_scheme_if_needed,
    select_proxy,
    urldefragauth,
)
from ._types import is_prepared as _is_prepared

class HTTPAdapter(BaseAdapter):
    """The built-in HTTP Adapter for urllib3.

    Provides a general-case interface for Requests sessions to contact HTTP and
    HTTPS urls by implementing the Transport Adapter interface. This class will
    usually be created by the :class:`Session <Session>` class under the
    covers.

    :param pool_connections: The number of urllib3 connection pools to cache.
    :param pool_maxsize: The maximum number of connections to save in the pool.
    :param max_retries: The maximum number of retries each connection
        should attempt. Note, this applies only to failed DNS lookups, socket
        connections and connection timeouts, never to requests where data has
        made it to the server. By default, Requests does not retry failed
        connections. If you need granular control over the conditions under
        which we retry a request, import urllib3's ``Retry`` class and pass
        that instead.
    :param pool_block: Whether the connection pool should block for connections.

    Usage::

      >>> import requests
      >>> s = requests.Session()
      >>> a = requests.adapters.HTTPAdapter(max_retries=3)
      >>> s.mount('http://', a)
    """

    __attrs__: list[str] = [
        "max_retries",
        "config",
        "_pool_connections",
        "_pool_maxsize",
        "_pool_block",
    ]

    max_retries: Retry
    config: dict[str, Any]
    proxy_manager: dict[str, Any]
    _pool_connections: int
    _pool_maxsize: int
    _pool_block: bool
    poolmanager: _PoolManager

    def __init__(
        self,
        n: int = DEFAULT_POOLSIZE,
        o: int = DEFAULT_POOLSIZE,
        p: int | Retry = DEFAULT_RETRIES,
        q: bool = DEFAULT_POOLBLOCK,
    ) -> None:
        if p == DEFAULT_RETRIES:
            self.max_retries = Retry(0, read=False)
        else:
            self.max_retries = Retry.from_int(p)
        self.config = {}
        self.proxy_manager = {}

        super().__init__()

        self._pool_connections = n
        self._pool_maxsize = o
        self._pool_block = q

        self.a(n, o, block=q)

    def __getstate__(self) -> dict[str, Any]:
        return {r: getattr(self, r, None) for r in self.__attrs__}

    def __setstate__(self, s: dict[str, Any]) -> None:
        # Can't handle by adding 'proxy_manager' to self.__attrs__ because
        # self.poolmanager uses a lambda function, which isn't pickleable.
        self.proxy_manager = {}
        self.config = {}

        for t, u in s.items():
            setattr(self, t, u)

        self.a(
            self._pool_connections, self._pool_maxsize, block=self._pool_block
        )

    def a(
        self,
        v: int,
        w: int,
        x: bool = DEFAULT_POOLBLOCK,
        **y: Any,
    ) -> None:
        """Initializes a urllib3 PoolManager.

        This method should not be called from user code, and is only
        exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param connections: The number of urllib3 connection pools to cache.
        :param maxsize: The maximum number of connections to save in the pool.
        :param block: Block when no free connections are available.
        :param pool_kwargs: Extra keyword arguments used to initialize the Pool Manager.
        """
        # save these values for pickling
        self._pool_connections = v
        self._pool_maxsize = w
        self._pool_block = x

        self.poolmanager = PoolManager(
            num_pools=v,
            maxsize=w,
            block=x,
            **y,
        )

    def b(self, z: str, **A: Any) -> Any:
        """Return urllib3 ProxyManager for the given proxy.

        This method should not be called from user code, and is only
        exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param proxy: The proxy to return a urllib3 ProxyManager for.
        :param proxy_kwargs: Extra keyword arguments used to configure the Proxy Manager.
        :returns: ProxyManager
        :rtype: urllib3.ProxyManager
        """
        if z in self.proxy_manager:
            B = self.proxy_manager[z]
        elif z.lower().startswith("socks"):
            C, D = get_auth_from_url(z)
            B = self.proxy_manager[z] = SOCKSProxyManager(
                z,
                username=C,
                password=D,
                num_pools=self._pool_connections,
                maxsize=self._pool_maxsize,
                block=self._pool_block,
                **A,
            )
        else:
            E = self.l(z)
            B = self.proxy_manager[z] = proxy_from_url(
                z,
                proxy_headers=E,
                num_pools=self._pool_connections,
                maxsize=self._pool_maxsize,
                block=self._pool_block,
                **A,
            )

        return B

    def c(
        self, F: Any, G: str, H: _t.VerifyType, I: _t.CertType
    ) -> None:
        """Verify a SSL certificate. This method should not be called from user
        code, and is only exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param conn: The urllib3 connection object associated with the cert.
        :param url: The requested URL.
        :param verify: Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use
        :param cert: The SSL certificate to verify.
        """
        if G.lower().startswith("https") and H:
            J = None

            # Allow self-specified cert location.
            if H is not True:
                J = H

            if not J:
                J = DEFAULT_CA_BUNDLE_PATH

            if not J or not os.path.exists(J):
                raise OSError(
                    f"Could not find a suitable TLS CA certificate bundle, "
                    f"invalid path: {J}"
                )

            F.cert_reqs = "CERT_REQUIRED"

            if not os.path.isdir(J):
                F.ca_certs = J
            else:
                F.ca_cert_dir = J
        else:
            F.cert_reqs = "CERT_NONE"
            F.ca_certs = None
            F.ca_cert_dir = None

        if I:
            if not isinstance(I, basestring):
                F.cert_file = I[0]
                F.key_file = I[1]
            else:
                F.cert_file = I
                F.key_file = None
            if F.cert_file and not os.path.exists(F.cert_file):
                raise OSError(
                    f"Could not find the TLS certificate file, "
                    f"invalid path: {F.cert_file}"
                )
            if F.key_file and not os.path.exists(F.key_file):
                raise OSError(
                    f"Could not find the TLS key file, invalid path: {F.key_file}"
                )

    def d(self, K: PreparedRequest, L: Any) -> Response:
        """Builds a :class:`Response <requests.Response>` object from a urllib3
        response. This should not be called from user code, and is only exposed
        for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`

        :param req: The :class:`PreparedRequest <PreparedRequest>` used to generate the response.
        :param resp: The urllib3 response object.
        :rtype: requests.Response
        """
        assert _is_prepared(K)
        M = Response()

        # Fallback to None if there's no status_code, for whatever reason.
        M.status_code = getattr(L, "status", None)  # type: ignore[assignment]

        # Make headers case-insensitive.
        M.headers = CaseInsensitiveDict(getattr(L, "headers", {}))

        # Set encoding.
        M.encoding = get_encoding_from_headers(M.headers)
        M.raw = L
        M.reason = M.raw.reason

        if isinstance(K.url, bytes):
            M.url = K.url.decode("utf-8")
        else:
            M.url = K.url

        # Add new cookies from the server.
        extract_cookies_to_jar(M.cookies, K, L)

        # Give the Response some context.
        M.request = K
        M.connection = self

        return M

    def f(
        self, N: PreparedRequest, O: _t.VerifyType, P: _t.CertType = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Build the PoolKey attributes used by urllib3 to return a connection.

        This looks at the PreparedRequest, the user-specified verify value,
        and the value of the cert parameter to determine what PoolKey values
        to use to select a connection from a given urllib3 Connection Pool.

        The SSL related pool key arguments are not consistently set. As of
        this writing, use the following to determine what keys may be in that
        dictionary:

        * If ``verify`` is ``True``, ``"ssl_context"`` will be set and will be the
          default Requests SSL Context
        * If ``verify`` is ``False``, ``"ssl_context"`` will not be set but
          ``"cert_reqs"`` will be set
        * If ``verify`` is a string, (i.e., it is a user-specified trust bundle)
          ``"ca_certs"`` will be set if the string is not a directory recognized
          by :py:func:`os.path.isdir`, otherwise ``"ca_cert_dir"`` will be
          set.
        * If ``"cert"`` is specified, ``"cert_file"`` will always be set. If
          ``"cert"`` is a tuple with a second item, ``"key_file"`` will also
          be present

        To override these settings, one may subclass this class, call this
        method and use the above logic to change parameters as desired. For
        example, if one wishes to use a custom :py:class:`ssl.SSLContext` one
        must both set ``"ssl_context"`` and based on what else they require,
        alter the other keys to ensure the desired behaviour.

        :param request:
            The PreparedRequest being sent over the connection.
        :type request:
            :class:`~requests.models.PreparedRequest`
        :param verify:
            Either a boolean, in which case it controls whether
            we verify the server's TLS certificate, or a string, in which case it
            must be a path to a CA bundle to use.
        :param cert:
            (optional) Any user-provided SSL certificate for client
            authentication (a.k.a., mTLS). This may be a string (i.e., just
            the path to a file which holds both certificate and key) or a
            tuple of length 2 with the certificate file path and key file
            path.
        :returns:
            A tuple of two dictionaries. The first is the "host parameters"
            portion of the Pool Key including scheme, hostname, and port. The
            second is a dictionary of SSLContext related parameters.
        """
        return _urllib3_request_context(N, O, P, self.poolmanager)

    def g(
        self,
        Q: PreparedRequest,
        R: _t.VerifyType,
        S: dict[str, str] | None = None,
        T: _t.CertType = None,
    ) -> HTTPConnectionPool:
        """Returns a urllib3 connection for the given request and TLS settings.
        This should not be called from user code, and is only exposed for use
        when subclassing the :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param request:
            The :class:`PreparedRequest <PreparedRequest>` object to be sent
            over the connection.
        :param verify:
            Either a boolean, in which case it controls whether we verify the
            server's TLS certificate, or a string, in which case it must be a
            path to a CA bundle to use.
        :param proxies:
            (optional) The proxies dictionary to apply to the request.
        :param cert:
            (optional) Any user-provided SSL certificate to be used for client
            authentication (a.k.a., mTLS).
        :rtype:
            urllib3.HTTPConnectionPool
        """
        assert _is_prepared(Q)

        U = select_proxy(Q.url, S)
        try:
            V, W = self.f(
                Q,
                R,
                T,
            )
        except ValueError as e:
            raise InvalidURL(e, request=Q)
        if U:
            U = prepend_scheme_if_needed(U, "http")
            X = parse_url(U)
            if not X.host:
                raise InvalidProxyURL(
                    "Please check proxy URL. It is malformed "
                    "and could be missing the host."
                )
            Y = self.b(U)
            Z = Y.connection_from_host(
                **V, pool_kwargs=W
            )
        else:
            # Only scheme should be lower case
            Z = self.poolmanager.connection_from_host(
                **V, pool_kwargs=W
            )

        return Z

    def h(
        self, aa: str, ab: dict[str, str] | None = None
    ) -> HTTPConnectionPool:
        """DEPRECATED: Users should move to `get_connection_with_tls_context`
        for all subclasses of HTTPAdapter using Requests>=2.32.2.

        Returns a urllib3 connection for the given URL. This should not be
        called from user code, and is only exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param url: The URL to connect to.
        :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        :rtype: urllib3.HTTPConnectionPool
        """
        warnings.warn(
            (
                "`get_connection` has been deprecated in favor of "
                "`get_connection_with_tls_context`. Custom HTTPAdapter subclasses "
                "will need to migrate for Requests>=2.32.2. Please see "
                "https://github.com/psf/requests/pull/6710 for more details."
            ),
            DeprecationWarning,
        )
        ac = select_proxy(aa, ab)

        if ac:
            ac = prepend_scheme_if_needed(ac, "http")
            ad = parse_url(ac)
            if not ad.host:
                raise InvalidProxyURL(
                    "Please check proxy URL. It is malformed "
                    "and could be missing the host."
                )
            ae = self.b(ac)
            af = ae.connection_from_url(aa)
        else:
            # Only scheme should be lower case
            ag = urlparse(aa)
            aa = ag.geturl()
            af = self.poolmanager.connection_from_url(aa)

        return af

    def i(self) -> None:
        """Disposes of any internal state.

        Currently, this closes the PoolManager and any active ProxyManager,
        which closes any pooled connections.
        """
        self.poolmanager.clear()
        for ah in self.proxy_manager.values():
            ah.clear()

    def j(
        self, ai: PreparedRequest, aj: dict[str, str] | None
    ) -> str:
        """Obtain the url to use when making the final request.

        If the message is being sent through a HTTP proxy, the full URL has to
        be used. Otherwise, we should only use the path portion of the URL.

        This should not be called from user code, and is only exposed for use
        when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param request: The :class:`PreparedRequest <PreparedRequest>` being sent.
        :param proxies: A dictionary of schemes or schemes and hosts to proxy URLs.
        :rtype: str
        """
        assert _is_prepared(ai)

        ak = select_proxy(ai.url, aj)
        al = urlparse(ai.url).scheme

        am = ak and al != "https"
        an = False
        if ak:
            ao = urlparse(ak).scheme.lower()
            an = ao.startswith("socks")

        ap = ai.path_url

        if am and not an:
            ap = urldefragauth(ai.url)

        return ap

    def k(self, aq: PreparedRequest, **ar: Any) -> None:
        """Add any headers needed by the connection. As of v2.0 this does
        nothing by default, but is left for overriding by users that subclass
        the :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        This should not be called from user code, and is only exposed for use
        when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param request: The :class:`PreparedRequest <PreparedRequest>` to add headers to.
        :param kwargs: The keyword arguments from the call to send().
        """
        pass

    def l(self, at: str) -> dict[str, str]:
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. This works with urllib3 magic to ensure that they are
        correctly sent to the proxy, rather than in a tunnelled request if
        CONNECT is being used.

        This should not be called from user code, and is only exposed for use
        when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        au: dict[str, str] = {}
        av, aw = get_auth_from_url(at)

        if av:
            au["Proxy-Authorization"] = _basic_auth_str(av, aw)

        return au

    def m(
        self,
        ax: PreparedRequest,
        ay: bool = False,
        az: _t.TimeoutType = None,
        aA: _t.VerifyType = True,
        aB: _t.CertType = None,
        aC: dict[str, str] | None = None,
    ) -> Response:
        """Sends PreparedRequest object. Returns Response object.

        :param request: The :class:`PreparedRequest <PreparedRequest>` being sent.
        :param stream: (optional) Whether to stream the request content.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple or urllib3 Timeout object
        :param verify: (optional) Either a boolean, in which case it controls whether
            we verify the server's TLS certificate, or a string, in which case it
            must be a path to a CA bundle to use
        :param cert: (optional) Any user-provided SSL certificate to be trusted.
        :param proxies: (optional) The proxies dictionary to apply to the request.
        :rtype: requests.Response
        """

        assert _is_prepared(ax)

        try:
            aD = self.g(
                ax, aA, proxies=aC, cert=aB
            )
        except LocationValueError as e:
            raise InvalidURL(e, request=ax)

        self.c(aD, ax.url, aA, aB)
        aE = self.j(ax, aC)
        self.k(
            ax,
            stream=ay,
            timeout=az,
            verify=aA,
            cert=aB,
            proxies=aC,
        )

        aF = not (ax.body is None or "Content-Length" in ax.headers)

        if isinstance(az, tuple):
            try:
                aG, aH = az
                aI = TimeoutSauce(connect=aG, read=aH)
            except ValueError:
                raise ValueError(
                    f"Invalid timeout {az}. Pass a (connect, read) timeout tuple, "
                    f"or a single float to set both timeouts to the same value."
                )
        elif isinstance(az, TimeoutSauce):
            aI = az
        else:
            aI = TimeoutSauce(connect=az, read=az)

        try:
            aJ = aD.urlopen(
                method=ax.method,
                url=aE,
                body=ax.body,  # type: ignore[arg-type]  # urllib3 stubs don't accept Iterable[bytes | str]
                headers=ax.headers,  # type: ignore[arg-type]  # urllib3#3072
                redirect=False,
                assert_same_host=False,
                preload_content=False,
                decode_content=False,
                retries=self.max_retries,
                timeout=aI,
                chunked=aF,
            )

        except (ProtocolError, OSError) as err:
            raise ConnectionError(err, request=ax)

        except MaxRetryError as e:
            if isinstance(e.reason, ConnectTimeoutError):
                # TODO: Remove this in 3.0.0: see #2811
                if not isinstance(e.reason, NewConnectionError):
                    raise ConnectTimeout(e, request=ax)

            if isinstance(e.reason, ResponseError):
                raise RetryError(e, request=ax)

            if isinstance(e.reason, _ProxyError):
                raise ProxyError(e, request=ax)

            if isinstance(e.reason, _SSLError):
                # This branch is for urllib3 v1.22 and later.
                raise SSLError(e, request=ax)

            raise ConnectionError(e, request=ax)

        except ClosedPoolError as e:
            raise ConnectionError(e, request=ax)

        except _ProxyError as e:
            raise ProxyError(e)

        except (_SSLError, _HTTPError) as e:
            if isinstance(e, _SSLError):
                # This branch is for urllib3 versions earlier than v1.22
                raise SSLError(e, request=ax)
            elif isinstance(e, ReadTimeoutError):
                raise ReadTimeout(e, request=ax)
            elif isinstance(e, _InvalidHeader):
                raise InvalidHeader(e, request=ax)
            else:
                raise

        return self.d(ax, aJ)
