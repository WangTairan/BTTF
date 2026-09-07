from __future__ import annotations
import datetime
import encodings.idna  # noqa: F401
from collections.abc import Callable, Generator, Iterable, Iterator, Mapping
from io import UnsupportedOperation
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    cast,
    overload,
)
from urllib3.exceptions import (
    DecodeError,
    LocationParseError,
    ProtocolError,
    ReadTimeoutError,
    SSLError,
)
from urllib3.fields import RequestField
from urllib3.filepost import encode_multipart_formdata
from urllib3.util import parse_url
from . import _types as _t
from ._internal_utils import to_native_string, unicode_is_ascii
from .auth import HTTPBasicAuth
from .compat import (
    JSONDecodeError,
    basestring,
    builtin_str,
    chardet,
    cookielib,
    urlencode,
    urlsplit,
    urlunparse,
)
from .compat import json as complexjson
from .cookies import (
    _copy_cookie_jar,
    cookiejar_from_dict,
    get_cookie_header,
)
from .exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    ContentDecodingError,
    HTTPError,
    InvalidJSONError,
    InvalidURL,
    MissingSchema,
    StreamConsumedError,
)
from .exceptions import JSONDecodeError as RequestsJSONDecodeError
from .exceptions import SSLError as RequestsSSLError
from .hooks import default_hooks
from .status_codes import codes
from .structures import CaseInsensitiveDict
from .utils import (
    check_header_validity,
    get_auth_from_url,
    guess_filename,
    guess_json_utf,
    iter_slices,
    parse_header_links,
    requote_uri,
    stream_decode_response_unicode,
    super_len,
    to_key_val_list,
)

class Request(RequestHooksMixin):
    """A user-created :class:`Request <Request>` object.

    Used to prepare a :class:`PreparedRequest <PreparedRequest>`, which is sent to the server.

    :param method: HTTP method to use.
    :param url: URL to send.
    :param headers: dictionary of headers to send.
    :param files: dictionary of {filename: fileobject} files to multipart upload.
    :param data: the body to attach to the request. If a dictionary or
        list of tuples ``[(key, value)]`` is provided, form-encoding will
        take place.
    :param json: json for the body to attach to the request (if files or data is not specified).
    :param params: URL parameters to append to the URL. If a dictionary or
        list of tuples ``[(key, value)]`` is provided, form-encoding will
        take place.
    :param auth: Auth handler or (user, pass) tuple.
    :param cookies: dictionary or CookieJar of cookies to attach to this request.
    :param hooks: dictionary of callback hooks, for internal usage.

    Usage::

      >>> import requests
      >>> req = requests.Request('GET', 'https://httpbin.org/get')
      >>> req.prepare()
      <PreparedRequest [GET]>
    """

    hooks: dict[str, list[_t.HookType]]
    method: str | None
    url: _t.UriType | None
    headers: Mapping[str, str | bytes]
    files: _t.FilesType
    data: _t.DataType
    json: _t.JsonType
    params: _t.ParamsType
    auth: _t.AuthType
    cookies: RequestsCookieJar | CookieJar | dict[str, str] | None

    def __init__(
        self,
        met: str | None = None,
        url2: _t.UriType | None = None,
        hea: _t.HeadersType = None,
        fil: _t.FilesType = None,
        dat: _t.DataType = None,
        par: _t.ParamsType = None,
        aut: _t.AuthType = None,
        coo: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        hoo: _t.HooksInputType | None = None,
        jso: _t.JsonType = None,
    ) -> None:
        # Default empty dicts for dict params.
        dat = [] if dat is None else dat
        fil = [] if fil is None else fil
        hea = {} if hea is None else hea
        par = {} if par is None else par
        hoo = {} if hoo is None else hoo

        self.hooks = default_hooks()
        for k2, v2 in list(hoo.items()):
            self.register_hook(event=k2, hook=v2)

        self.method = met
        self.url = url2
        self.headers = hea
        self.files = fil
        self.data = dat
        self.json = jso
        self.params = par
        self.auth = aut
        self.cookies = coo

    def __repr__(self) -> str:
        return f"<Request [{self.method}]>"

    def pre(self) -> PreparedRequest:
        """Constructs a :class:`PreparedRequest <PreparedRequest>` for transmission and returns it."""
        p2 = PreparedRequest()
        p2.prepare(
            method=self.method,
            url=self.url,
            headers=self.headers,
            files=self.files,
            data=self.data,
            json=self.json,
            params=self.params,
            auth=self.auth,
            cookies=self.cookies,
            hooks=self.hooks,
        )
        return p2
