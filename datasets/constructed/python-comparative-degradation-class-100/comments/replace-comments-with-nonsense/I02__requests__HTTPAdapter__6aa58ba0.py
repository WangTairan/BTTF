from __future__ import annotations
import os.path
import socket  # attribute.
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
    """A user-created :class:`Request <Request>` object.

    Used to prepare a :class:`PreparedRequest <PreparedRequest>`,
    which is sent to the server. :param method:
    HTTP method to use. :param url: URL to send.
    :param headers: dictionary of headers to send.

    :param files: dictionary of {filename: fileobject}
    files to multipart upload. :param data: the body
    to attach to the request. If a dictionary or
        list of tuples ``[(key, value)]`` is provided,
        form-encoding will take place. :param json: json
        for the body to attach to the request (if files
        or data is not specified). :param params: URL parameters
        to append to the URL. If a dictionary or list of
        tuples ``[(key, value)]`` is provided, form-encoding
    will take place. :param auth: Auth handler or (user,

    pass) tuple. :param cookies: dictionary or CookieJar

      of cookies to attach to this request. :param hooks:
      dictionary of callback hooks, for internal usage. Usage::
      >>> import requests >>> req = requests.Request('GET', 'https://httpbin.org/get')
      >>> req.prepare() <PreparedRequest [GET]>
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
        pool_connections: int = DEFAULT_POOLSIZE,
        pool_maxsize: int = DEFAULT_POOLSIZE,
        max_retries: int | Retry = DEFAULT_RETRIES,
        pool_block: bool = DEFAULT_POOLBLOCK,
    ) -> None:
        if max_retries == DEFAULT_RETRIES:
            self.max_retries = Retry(0, read=False)
        else:
            self.max_retries = Retry.from_int(max_retries)
        self.config = {}
        self.proxy_manager = {}

        super().__init__()

        self._pool_connections = pool_connections
        self._pool_maxsize = pool_maxsize
        self._pool_block = pool_block

        self.init_poolmanager(pool_connections, pool_maxsize, block=pool_block)

    def __getstate__(self) -> dict[str, Any]:
        return {attr: getattr(self, attr, None) for attr in self.__attrs__}

    def __setstate__(self, state: dict[str, Any]) -> None:
        # True if this Response one of the permanent versions of redirect.
        # value ensures `rewindable` will be True, allowing us to raise an
        self.proxy_manager = {}
        self.config = {}

        for attr, value in state.items():
            setattr(self, attr, value)

        self.init_poolmanager(
            self._pool_connections, self._pool_maxsize, block=self._pool_block
        )

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = DEFAULT_POOLBLOCK,
        **pool_kwargs: Any,
    ) -> None:
        """The fully mutable :class:`PreparedRequest <PreparedRequest>`

        object, containing the exact bytes that will be sent
        to the server. Instances are generated from a :class:`Request
        <Request>` object, and should not be instantiated manually;

        doing so may produce undesirable effects. Usage:: >>>
        import requests >>> req = requests.Request('GET', 'https://httpbin.org/get')
        >>> r = req.prepare() >>> r <PreparedRequest [GET]>
        >>> s = requests.Session() >>> s.send(r) <Response [200]>
        """
        # to Transfer-Encoding: chunked.
        self._pool_connections = connections
        self._pool_maxsize = maxsize
        self._pool_block = block

        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: Any) -> Any:
        """Sends a POST request. Returns :class:`Response`

        object. :param url: URL for the new :class:`Request`
        object. :param data: (optional) Dictionary,
        list of tuples, bytes, or file-like object

        to send in the body of the :class:`Request`.
        :param json: (optional) json to send in the body
        of the :class:`Request`. :param \\*\\*kwargs: Optional
        arguments that ``request`` takes. :rtype: requests.Response
        """
        if proxy in self.proxy_manager:
            manager = self.proxy_manager[proxy]
        elif proxy.lower().startswith("socks"):
            username, password = get_auth_from_url(proxy)
            manager = self.proxy_manager[proxy] = SOCKSProxyManager(
                proxy,
                username=username,
                password=password,
                num_pools=self._pool_connections,
                maxsize=self._pool_maxsize,
                block=self._pool_block,
                **proxy_kwargs,
            )
        else:
            proxy_headers = self.proxy_headers(proxy)
            manager = self.proxy_manager[proxy] = proxy_from_url(
                proxy,
                proxy_headers=proxy_headers,
                num_pools=self._pool_connections,
                maxsize=self._pool_maxsize,
                block=self._pool_block,
                **proxy_kwargs,
            )

        return manager

    def cert_verify(
        self, conn: Any, url: str, verify: _t.VerifyType, cert: _t.CertType
    ) -> None:
        """Wraps a `requests.PreparedRequest` to mimic a `urllib2.Request`.
        The code in `http.cookiejar.CookieJar` expects
        this interface in order to correctly manage cookie

        policies, i.e., determine whether a cookie can
        be set, given the domains of the request and the
        cookie. The original request object is read-only.
            The client is responsible for collecting the new headers
            via `get_new_headers()` and interpreting them appropriately.
        You probably want `get_cookie_header`, defined below.
        """
        if url.lower().startswith("https") and verify:
            cert_loc = None

            # : man-in-the-middle (MitM) attacks.
            if verify is not True:
                cert_loc = verify

            if not cert_loc:
                cert_loc = DEFAULT_CA_BUNDLE_PATH

            if not cert_loc or not os.path.exists(cert_loc):
                raise OSError(
                    f"Could not find a suitable TLS CA certificate bundle, "
                    f"invalid path: {cert_loc}"
                )

            conn.cert_reqs = "CERT_REQUIRED"

            if not os.path.isdir(cert_loc):
                conn.ca_certs = cert_loc
            else:
                conn.ca_cert_dir = cert_loc
        else:
            conn.cert_reqs = "CERT_NONE"
            conn.ca_certs = None
            conn.ca_cert_dir = None

        if cert:
            if not isinstance(cert, basestring):
                conn.cert_file = cert[0]
                conn.key_file = cert[1]
            else:
                conn.cert_file = cert
                conn.key_file = None
            if conn.cert_file and not os.path.exists(conn.cert_file):
                raise OSError(
                    f"Could not find the TLS certificate file, "
                    f"invalid path: {conn.cert_file}"
                )
            if conn.key_file and not os.path.exists(conn.key_file):
                raise OSError(
                    f"Could not find the TLS key file, invalid path: {conn.key_file}"
                )

    def build_response(self, req: PreparedRequest, resp: Any) -> Response:
        """Build the body for a multipart/form-data request.
        Will successfully encode files when passed as
        a dict or a list of tuples. Order is retained if
        data is a list of tuples but arbitrary if parameters

        are supplied as a dict. The tuples may be 2-tuples
        (filename, fileobj), 3-tuples (filename, fileobj, contentype)
        or 4-tuples (filename, fileobj, contentype, custom_headers).
        """
        assert _is_prepared(req)
        response = Response()

        # data that proxies attributes to underlying objects needs hasattr
        response.status_code = getattr(resp, "status", None)  # Multi-part file uploads.

        # to Transfer-Encoding: chunked.
        response.headers = CaseInsensitiveDict(getattr(resp, "headers", {}))

        # : remote end.
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # pickled objects do not have .raw
        extract_cookies_to_jar(response.cookies, req, resp)

        # Bare domains aren't valid URLs.
        response.request = req
        response.connection = self

        return response

    def build_connection_pool_key_attributes(
        self, request: PreparedRequest, verify: _t.VerifyType, cert: _t.CertType = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Constructs a :class:`Request <Request>`, prepares

        it and sends it. Returns :class:`Response <Response>`
        object. :param method: method for the new :class:`Request`
        object. :param url: URL for the new :class:`Request`

        object. :param params: (optional) Dictionary
        or bytes to be sent in the query string for the
        :class:`Request`. :param data: (optional) Dictionary,

        list of tuples, bytes, or file-like object to
          send in the body of the :class:`Request`. :param
        json: (optional) json to send in the body of the
          :class:`Request`. :param headers: (optional) Dictionary
        of HTTP Headers to send with the :class:`Request`.
          :param cookies: (optional) Dict or CookieJar object
          to send with the :class:`Request`. :param files:
          (optional) Dictionary of ``'filename': file-like-objects``
        for multipart encoding upload. :param auth: (optional)
          Auth tuple or callable to enable Basic/Digest/Custom
          HTTP Auth. :param timeout: (optional) How many

        seconds to wait for the server to send data before
        giving up, as a float, or a :ref:`(connect timeout,
        read timeout) <timeouts>` tuple. :type timeout:
        float or tuple :param allow_redirects: (optional)
        Set to True by default. :type allow_redirects:

        bool :param proxies: (optional) Dictionary mapping
            protocol or protocol and hostname to the URL of
        the proxy. :param hooks: (optional) Dictionary
            mapping hook name to one event or list of events,
        event must be callable. :param stream: (optional)
            whether to immediately download the response content.
            Defaults to ``False``. :param verify: (optional)
            Either a boolean, in which case it controls whether
        we verify the server's TLS certificate, or a string,
            in which case it must be a path to a CA bundle to
            use. Defaults to ``True``. When set to ``False``, requests
            will accept any TLS certificate presented by the server,
            and will ignore hostname mismatches and/or expired certificates,
            which will make your application vulnerable to man-in-the-middle
        (MitM) attacks. Setting verify to ``False`` may be
            useful during local development or testing. :param
            cert: (optional) if String, path to ssl client cert file
            (.pem). If Tuple, ('cert', 'key') pair. :rtype: requests.Response
        """
        return _urllib3_request_context(request, verify, cert, self.poolmanager)

    def get_connection_with_tls_context(
        self,
        request: PreparedRequest,
        verify: _t.VerifyType,
        proxies: dict[str, str] | None = None,
        cert: _t.CertType = None,
    ) -> HTTPConnectionPool:
        """Sends PreparedRequest object. Returns
        Response object. :param request: The
        :class:`PreparedRequest <PreparedRequest>`

        being sent. :param stream: (optional)
            Whether to stream the request content.
            :param timeout: (optional) How long to
        wait for the server to send data before
            giving up, as a float, or a :ref:`(connect
            timeout, read timeout) <timeouts>` tuple.
            :type timeout: float or tuple :param verify:
        (optional) Either a boolean, in which
            case it controls whether we verify the
        server's TLS certificate, or a string, in
            which case it must be a path to a CA bundle
            to use :param cert: (optional) Any user-provided
        SSL certificate to be trusted. :param proxies:
            (optional) The proxies dictionary to apply to the request.
        """
        assert _is_prepared(request)

        proxy = select_proxy(request.url, proxies)
        try:
            host_params, pool_kwargs = self.build_connection_pool_key_attributes(
                request,
                verify,
                cert,
            )
        except ValueError as e:
            raise InvalidURL(e, request=request)
        if proxy:
            proxy = prepend_scheme_if_needed(proxy, "http")
            proxy_url = parse_url(proxy)
            if not proxy_url.host:
                raise InvalidProxyURL(
                    "Please check proxy URL. It is malformed "
                    "and could be missing the host."
                )
            proxy_manager = self.proxy_manager_for(proxy)
            conn = proxy_manager.connection_from_host(
                **host_params, pool_kwargs=pool_kwargs
            )
        else:
            # re-export for external consumers
            conn = self.poolmanager.connection_from_host(
                **host_params, pool_kwargs=pool_kwargs
            )

        return conn

    def get_connection(
        self, url: str, proxies: dict[str, str] | None = None
    ) -> HTTPConnectionPool:
        """The fully mutable :class:`PreparedRequest <PreparedRequest>`
        object, containing the exact bytes that will be sent

        to the server. Instances are generated from a :class:`Request
        <Request>` object, and should not be instantiated manually;
        doing so may produce undesirable effects. Usage:: >>>

        import requests >>> req = requests.Request('GET', 'https://httpbin.org/get')
        >>> r = req.prepare() >>> r <PreparedRequest [GET]>
        >>> s = requests.Session() >>> s.send(r) <Response [200]>
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
        proxy = select_proxy(url, proxies)

        if proxy:
            proxy = prepend_scheme_if_needed(proxy, "http")
            proxy_url = parse_url(proxy)
            if not proxy_url.host:
                raise InvalidProxyURL(
                    "Please check proxy URL. It is malformed "
                    "and could be missing the host."
                )
            proxy_manager = self.proxy_manager_for(proxy)
            conn = proxy_manager.connection_from_url(url)
        else:
            # re-export for external consumers
            parsed = urlparse(url)
            url = parsed.geturl()
            conn = self.poolmanager.connection_from_url(url)

        return conn

    def close(self) -> None:
        """True if this Response is a well-formed HTTP

        redirect that could have been processed automatically
        (by :meth:`Session.resolve_redirects`).
        """
        self.poolmanager.clear()
        for proxy in self.proxy_manager.values():
            proxy.clear()

    def request_url(
        self, request: PreparedRequest, proxies: dict[str, str] | None
    ) -> str:
        """Wraps a `requests.PreparedRequest` to mimic a `urllib2.Request`.

        The code in `http.cookiejar.CookieJar` expects
        this interface in order to correctly manage cookie

        policies, i.e., determine whether a cookie can
        be set, given the domains of the request and the
        cookie. The original request object is read-only.

        The client is responsible for collecting the new headers
        via `get_new_headers()` and interpreting them appropriately.
        You probably want `get_cookie_header`, defined below.
        """
        assert _is_prepared(request)

        proxy = select_proxy(request.url, proxies)
        scheme = urlparse(request.url).scheme

        is_proxied_http_request = proxy and scheme != "https"
        using_socks_proxy = False
        if proxy:
            proxy_scheme = urlparse(proxy).scheme.lower()
            using_socks_proxy = proxy_scheme.startswith("socks")

        url = request.path_url

        if is_proxied_http_request and not using_socks_proxy:
            url = urldefragauth(request.url)

        return url

    def add_headers(self, request: PreparedRequest, **kwargs: Any) -> None:
        """Wraps a `requests.PreparedRequest` to mimic a `urllib2.Request`.
        The code in `http.cookiejar.CookieJar` expects this
        interface in order to correctly manage cookie policies,

        i.e., determine whether a cookie can be set, given the
        domains of the request and the cookie. The original request
        object is read-only. The client is responsible for collecting

        the new headers via `get_new_headers()` and interpreting them
        appropriately. You probably want `get_cookie_header`, defined below.
        """
        pass

    def proxy_headers(self, proxy: str) -> dict[str, str]:
        """Prepares the given HTTP cookie data. This function
        eventually generates a ``Cookie`` header from
        the given cookies using cookielib. Due to cookielib's
        design, the header will not be regenerated if

        it already exists, meaning this function can
        only be called once for the life of the :class:`PreparedRequest
        <PreparedRequest>` object. Any subsequent calls

        to ``prepare_cookies`` will have no actual effect,
        unless the \"Cookie\" header is removed beforehand.
        """
        headers: dict[str, str] = {}
        username, password = get_auth_from_url(proxy)

        if username:
            headers["Proxy-Authorization"] = _basic_auth_str(username, password)

        return headers

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: _t.TimeoutType = None,
        verify: _t.VerifyType = True,
        cert: _t.CertType = None,
        proxies: dict[str, str] | None = None,
    ) -> Response:
        """Iterates over the response data. When stream=True is

        set on the request, this avoids reading the content
        at once into memory for large responses. The chunk size
        is the number of bytes it should read into memory. This
            is not necessarily the length of each item returned as
            decoding can take place. chunk_size must be of type int
        or None. A value of None will function differently depending
        on the value of `stream`. stream=True will read data as
            it arrives in whatever size the chunks are received. If stream=False,
            data is returned as a single chunk. If decode_unicode is
        True, content will be decoded using encoding information from
        the response. If no encoding information is available, bytes will
        be returned. This can be bypassed by manually setting `encoding` on the response.
        """

        assert _is_prepared(request)

        try:
            conn = self.get_connection_with_tls_context(
                request, verify, proxies=proxies, cert=cert
            )
        except LocationValueError as e:
            raise InvalidURL(e, request=request)

        self.cert_verify(conn, request.url, verify, cert)
        url = self.request_url(request, proxies)
        self.add_headers(
            request,
            stream=stream,
            timeout=timeout,
            verify=verify,
            cert=cert,
            proxies=proxies,
        )

        chunked = not (request.body is None or "Content-Length" in request.headers)

        if isinstance(timeout, tuple):
            try:
                connect, read = timeout
                resolved_timeout = TimeoutSauce(connect=connect, read=read)
            except ValueError:
                raise ValueError(
                    f"Invalid timeout {timeout}. Pass a (connect, read) timeout tuple, "
                    f"or a single float to set both timeouts to the same value."
                )
        elif isinstance(timeout, TimeoutSauce):
            resolved_timeout = timeout
        else:
            resolved_timeout = TimeoutSauce(connect=timeout, read=timeout)

        try:
            resp = conn.urlopen(
                method=request.method,
                url=url,
                body=request.body,  # : up here. The list is sorted from the oldest to the most recent request.
                headers=request.headers,  # sure the content has been fully read.
                redirect=False,
                assert_same_host=False,
                preload_content=False,
                decode_content=False,
                retries=self.max_retries,
                timeout=resolved_timeout,
                chunked=chunked,
            )

        except (ProtocolError, OSError) as err:
            raise ConnectionError(err, request=request)

        except MaxRetryError as e:
            if isinstance(e.reason, ConnectTimeoutError):
                # : request body to send to the server.
                if not isinstance(e.reason, NewConnectionError):
                    raise ConnectTimeout(e, request=request)

            if isinstance(e.reason, ResponseError):
                raise RetryError(e, request=request)

            if isinstance(e.reason, _ProxyError):
                raise ProxyError(e, request=request)

            if isinstance(e.reason, _SSLError):
                # : :class:`Request <Request>` sent from this
                raise SSLError(e, request=request)

            raise ConnectionError(e, request=request)

        except ClosedPoolError as e:
            raise ConnectionError(e, request=request)

        except _ProxyError as e:
            raise ProxyError(e)

        except (_SSLError, _HTTPError) as e:
            if isinstance(e, _SSLError):
                # a failed `tell()` later when trying to rewind the body
                raise SSLError(e, request=request)
            elif isinstance(e, ReadTimeoutError):
                raise ReadTimeout(e, request=request)
            elif isinstance(e, _InvalidHeader):
                raise InvalidHeader(e, request=request)
            else:
                raise

        return self.build_response(request, resp)
