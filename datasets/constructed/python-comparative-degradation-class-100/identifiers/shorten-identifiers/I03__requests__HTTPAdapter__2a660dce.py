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
        pool: int = DEFAULT_POOLSIZE,
        pool2: int = DEFAULT_POOLSIZE,
        max: int | Retry = DEFAULT_RETRIES,
        pool3: bool = DEFAULT_POOLBLOCK,
    ) -> None:
        if max == DEFAULT_RETRIES:
            self.max_retries = Retry(0, read=False)
        else:
            self.max_retries = Retry.from_int(max)
        self.config = {}
        self.proxy_manager = {}

        super().__init__()

        self._pool_connections = pool
        self._pool_maxsize = pool2
        self._pool_block = pool3

        self.init(pool, pool2, block=pool3)

    def __getstate__(self) -> dict[str, Any]:
        return {att: getattr(self, att, None) for att in self.__attrs__}

    def __setstate__(self, sta: dict[str, Any]) -> None:
        # Can't handle by adding 'proxy_manager' to self.__attrs__ because
        # self.poolmanager uses a lambda function, which isn't pickleable.
        self.proxy_manager = {}
        self.config = {}

        for att2, val in sta.items():
            setattr(self, att2, val)

        self.init(
            self._pool_connections, self._pool_maxsize, block=self._pool_block
        )

    def init(
        self,
        con: int,
        max2: int,
        blo: bool = DEFAULT_POOLBLOCK,
        **pool4: Any,
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
        self._pool_connections = con
        self._pool_maxsize = max2
        self._pool_block = blo

        self.poolmanager = PoolManager(
            num_pools=con,
            maxsize=max2,
            block=blo,
            **pool4,
        )

    def proxy2(self, pro: str, **proxy4: Any) -> Any:
        """Return urllib3 ProxyManager for the given proxy.

        This method should not be called from user code, and is only
        exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.

        :param proxy: The proxy to return a urllib3 ProxyManager for.
        :param proxy_kwargs: Extra keyword arguments used to configure the Proxy Manager.
        :returns: ProxyManager
        :rtype: urllib3.ProxyManager
        """
        if pro in self.proxy_manager:
            man = self.proxy_manager[pro]
        elif pro.lower().startswith("socks"):
            use, pas = get_auth_from_url(pro)
            man = self.proxy_manager[pro] = SOCKSProxyManager(
                pro,
                username=use,
                password=pas,
                num_pools=self._pool_connections,
                maxsize=self._pool_maxsize,
                block=self._pool_block,
                **proxy4,
            )
        else:
            proxy5 = self.proxy3(pro)
            man = self.proxy_manager[pro] = proxy_from_url(
                pro,
                proxy_headers=proxy5,
                num_pools=self._pool_connections,
                maxsize=self._pool_maxsize,
                block=self._pool_block,
                **proxy4,
            )

        return man

    def cert2(
        self, con2: Any, url2: str, ver: _t.VerifyType, cer: _t.CertType
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
        if url2.lower().startswith("https") and ver:
            cert3 = None

            # Allow self-specified cert location.
            if ver is not True:
                cert3 = ver

            if not cert3:
                cert3 = DEFAULT_CA_BUNDLE_PATH

            if not cert3 or not os.path.exists(cert3):
                raise OSError(
                    f"Could not find a suitable TLS CA certificate bundle, "
                    f"invalid path: {cert3}"
                )

            con2.cert_reqs = "CERT_REQUIRED"

            if not os.path.isdir(cert3):
                con2.ca_certs = cert3
            else:
                con2.ca_cert_dir = cert3
        else:
            con2.cert_reqs = "CERT_NONE"
            con2.ca_certs = None
            con2.ca_cert_dir = None

        if cer:
            if not isinstance(cer, basestring):
                con2.cert_file = cer[0]
                con2.key_file = cer[1]
            else:
                con2.cert_file = cer
                con2.key_file = None
            if con2.cert_file and not os.path.exists(con2.cert_file):
                raise OSError(
                    f"Could not find the TLS certificate file, "
                    f"invalid path: {con2.cert_file}"
                )
            if con2.key_file and not os.path.exists(con2.key_file):
                raise OSError(
                    f"Could not find the TLS key file, invalid path: {con2.key_file}"
                )

    def build(self, req2: PreparedRequest, res: Any) -> Response:
        """Builds a :class:`Response <requests.Response>` object from a urllib3
        response. This should not be called from user code, and is only exposed
        for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`

        :param req: The :class:`PreparedRequest <PreparedRequest>` used to generate the response.
        :param resp: The urllib3 response object.
        :rtype: requests.Response
        """
        assert _is_prepared(req2)
        res2 = Response()

        # Fallback to None if there's no status_code, for whatever reason.
        res2.status_code = getattr(res, "status", None)  # type: ignore[assignment]

        # Make headers case-insensitive.
        res2.headers = CaseInsensitiveDict(getattr(res, "headers", {}))

        # Set encoding.
        res2.encoding = get_encoding_from_headers(res2.headers)
        res2.raw = res
        res2.reason = res2.raw.reason

        if isinstance(req2.url, bytes):
            res2.url = req2.url.decode("utf-8")
        else:
            res2.url = req2.url

        # Add new cookies from the server.
        extract_cookies_to_jar(res2.cookies, req2, res)

        # Give the Response some context.
        res2.request = req2
        res2.connection = self

        return res2

    def build2(
        self, req3: PreparedRequest, ver2: _t.VerifyType, cer2: _t.CertType = None
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
        return _urllib3_request_context(req3, ver2, cer2, self.poolmanager)

    def get(
        self,
        req4: PreparedRequest,
        ver3: _t.VerifyType,
        pro2: dict[str, str] | None = None,
        cer3: _t.CertType = None,
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
        assert _is_prepared(req4)

        pro3 = select_proxy(req4.url, pro2)
        try:
            host2, pool5 = self.build2(
                req4,
                ver3,
                cer3,
            )
        except ValueError as e:
            raise InvalidURL(e, request=req4)
        if pro3:
            pro3 = prepend_scheme_if_needed(pro3, "http")
            proxy6 = parse_url(pro3)
            if not proxy6.host:
                raise InvalidProxyURL(
                    "Please check proxy URL. It is malformed "
                    "and could be missing the host."
                )
            proxy7 = self.proxy2(pro3)
            con3 = proxy7.connection_from_host(
                **host2, pool_kwargs=pool5
            )
        else:
            # Only scheme should be lower case
            con3 = self.poolmanager.connection_from_host(
                **host2, pool_kwargs=pool5
            )

        return con3

    def get2(
        self, url3: str, pro4: dict[str, str] | None = None
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
        pro5 = select_proxy(url3, pro4)

        if pro5:
            pro5 = prepend_scheme_if_needed(pro5, "http")
            proxy8 = parse_url(pro5)
            if not proxy8.host:
                raise InvalidProxyURL(
                    "Please check proxy URL. It is malformed "
                    "and could be missing the host."
                )
            proxy9 = self.proxy2(pro5)
            con4 = proxy9.connection_from_url(url3)
        else:
            # Only scheme should be lower case
            par = urlparse(url3)
            url3 = par.geturl()
            con4 = self.poolmanager.connection_from_url(url3)

        return con4

    def clo(self) -> None:
        """Disposes of any internal state.

        Currently, this closes the PoolManager and any active ProxyManager,
        which closes any pooled connections.
        """
        self.poolmanager.clear()
        for pro6 in self.proxy_manager.values():
            pro6.clear()

    def request2(
        self, req5: PreparedRequest, pro7: dict[str, str] | None
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
        assert _is_prepared(req5)

        pro8 = select_proxy(req5.url, pro7)
        sch = urlparse(req5.url).scheme

        is2 = pro8 and sch != "https"
        using = False
        if pro8:
            proxy10 = urlparse(pro8).scheme.lower()
            using = proxy10.startswith("socks")

        url4 = req5.path_url

        if is2 and not using:
            url4 = urldefragauth(req5.url)

        return url4

    def add(self, req6: PreparedRequest, **kwa: Any) -> None:
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

    def proxy3(self, pro9: str) -> dict[str, str]:
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
        hea: dict[str, str] = {}
        use2, pas2 = get_auth_from_url(pro9)

        if use2:
            hea["Proxy-Authorization"] = _basic_auth_str(use2, pas2)

        return hea

    def sen(
        self,
        req7: PreparedRequest,
        str2: bool = False,
        tim: _t.TimeoutType = None,
        ver4: _t.VerifyType = True,
        cer4: _t.CertType = None,
        pro10: dict[str, str] | None = None,
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

        assert _is_prepared(req7)

        try:
            con5 = self.get(
                req7, ver4, proxies=pro10, cert=cer4
            )
        except LocationValueError as e:
            raise InvalidURL(e, request=req7)

        self.cert2(con5, req7.url, ver4, cer4)
        url5 = self.request2(req7, pro10)
        self.add(
            req7,
            stream=str2,
            timeout=tim,
            verify=ver4,
            cert=cer4,
            proxies=pro10,
        )

        chu = not (req7.body is None or "Content-Length" in req7.headers)

        if isinstance(tim, tuple):
            try:
                con6, rea = tim
                resolved = TimeoutSauce(connect=con6, read=rea)
            except ValueError:
                raise ValueError(
                    f"Invalid timeout {tim}. Pass a (connect, read) timeout tuple, "
                    f"or a single float to set both timeouts to the same value."
                )
        elif isinstance(tim, TimeoutSauce):
            resolved = tim
        else:
            resolved = TimeoutSauce(connect=tim, read=tim)

        try:
            res3 = con5.urlopen(
                method=req7.method,
                url=url5,
                body=req7.body,  # type: ignore[arg-type]  # urllib3 stubs don't accept Iterable[bytes | str]
                headers=req7.headers,  # type: ignore[arg-type]  # urllib3#3072
                redirect=False,
                assert_same_host=False,
                preload_content=False,
                decode_content=False,
                retries=self.max_retries,
                timeout=resolved,
                chunked=chu,
            )

        except (ProtocolError, OSError) as err:
            raise ConnectionError(err, request=req7)

        except MaxRetryError as e:
            if isinstance(e.reason, ConnectTimeoutError):
                # TODO: Remove this in 3.0.0: see #2811
                if not isinstance(e.reason, NewConnectionError):
                    raise ConnectTimeout(e, request=req7)

            if isinstance(e.reason, ResponseError):
                raise RetryError(e, request=req7)

            if isinstance(e.reason, _ProxyError):
                raise ProxyError(e, request=req7)

            if isinstance(e.reason, _SSLError):
                # This branch is for urllib3 v1.22 and later.
                raise SSLError(e, request=req7)

            raise ConnectionError(e, request=req7)

        except ClosedPoolError as e:
            raise ConnectionError(e, request=req7)

        except _ProxyError as e:
            raise ProxyError(e)

        except (_SSLError, _HTTPError) as e:
            if isinstance(e, _SSLError):
                # This branch is for urllib3 versions earlier than v1.22
                raise SSLError(e, request=req7)
            elif isinstance(e, ReadTimeoutError):
                raise ReadTimeout(e, request=req7)
            elif isinstance(e, _InvalidHeader):
                raise InvalidHeader(e, request=req7)
            else:
                raise

        return self.build(req7, res3)
