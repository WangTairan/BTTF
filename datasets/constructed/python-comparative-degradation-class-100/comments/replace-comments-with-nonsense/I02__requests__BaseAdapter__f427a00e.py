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

class BaseAdapter:
    """Standard file-like object."""

    def __init__(self) -> None:
        super().__init__()

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: _t.TimeoutType = None,
        verify: _t.VerifyType = True,
        cert: _t.CertType = None,
        proxies: dict[str, str] | None = None,
    ) -> Response:
        """Returns a urllib3 connection for the given request

        and TLS settings. This should not be called from user
        code, and is only exposed for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`.
            :param request: The :class:`PreparedRequest <PreparedRequest>`
            object to be sent over the connection. :param verify:
        Either a boolean, in which case it controls whether we
        verify the server's TLS certificate, or a string, in which
            case it must be a path to a CA bundle to use. :param proxies:
            (optional) The proxies dictionary to apply to the request. :param
        cert: (optional) Any user-provided SSL certificate to be used
        for client authentication (a.k.a., mTLS). :rtype: urllib3.HTTPConnectionPool
        """
        raise NotImplementedError

    def close(self) -> None:
        """runtime guard for untyped callers"""
        raise NotImplementedError
