from __future__ import annotations
import datetime
import encodings.idna   
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

class PreparedRequest(RequestEncodingMixin, RequestHooksMixin):
    

    method: str | None
    url: str | None
    headers: CaseInsensitiveDict[str | bytes]
    _cookies: RequestsCookieJar | CookieJar | None
    body: _t.BodyType
    hooks: dict[str, list[_t.HookType]]
    _body_position: int | object | None

    def __init__(self) -> None:
         
        self.method = None
         
        self.url = None
         
        self.headers = None   
         
         
        self._cookies = None
         
        self.body = None
         
        self.hooks = default_hooks()
         
        self._body_position = None

    def prepare(
        self,
        method: str | None = None,
        url: _t.UriType | None = None,
        headers: Mapping[str, str | bytes] | None = None,
        files: _t.FilesType = None,
        data: _t.DataType = None,
        params: _t.ParamsType = None,
        auth: _t.AuthType = None,
        cookies: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        hooks: _t.HooksInputType | None = None,
        json: _t.JsonType = None,
    ) -> None:
        

        url = cast("_t.UriType", url)
        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_cookies(cookies)
        self.prepare_body(data, files, json)
        self.prepare_auth(auth, url)

         
         

         
        self.prepare_hooks(hooks)

    def __repr__(self) -> str:
        return f"<PreparedRequest [{self.method}]>"

    def copy(self) -> PreparedRequest:
        p = PreparedRequest()
        p.method = self.method
        p.url = self.url
        p.headers = self.headers.copy() if self.headers is not None else None   
        p._cookies = _copy_cookie_jar(self._cookies)
        p.body = self.body
        p.hooks = self.hooks
        p._body_position = self._body_position
        return p

    def prepare_method(self, method: str | None) -> None:
        
        self.method = method
        if self.method is not None:
            self.method = to_native_string(self.method.upper())

    @staticmethod
    def _get_idna_encoded_host(host: str) -> str:
        import idna

        try:
            host = idna.encode(host, uts46=True).decode("utf-8")
        except idna.IDNAError:
            raise UnicodeError
        return host

    def prepare_url(
        self,
        url: _t.UriType,
        params: _t.ParamsType,
    ) -> None:
        
         
         
         
         
         
        if isinstance(url, bytes):
            url = url.decode("utf8")
        else:
            url = str(url)

         
        url = url.lstrip()

         
         
         
        if ":" in url and not url.lower().startswith("http"):
            self.url = url
            return

         
        try:
            scheme, auth, host, port, path, query, fragment = parse_url(url)
        except LocationParseError as e:
            raise InvalidURL(*e.args)

        if not scheme:
            raise MissingSchema(
                f"Invalid URL {url!r}: No scheme supplied. "
                f"Perhaps you meant https://{url}?"
            )

        if not host:
            raise InvalidURL(f"Invalid URL {url!r}: No host supplied")

         
         
         
         
        if not unicode_is_ascii(host):
            try:
                host = self._get_idna_encoded_host(host)
            except UnicodeError:
                raise InvalidURL("URL has an invalid label.")
        elif host.startswith(("*", ".")):
            raise InvalidURL("URL has an invalid label.")

         
        netloc = auth or ""
        if netloc:
            netloc += "@"
        netloc += host
        if port:
            netloc += f":{port}"

         
        if not path:
            path = "/"

        if isinstance(params, (str, bytes)):
            params = to_native_string(params)

        if params is not None:
            enc_params = self._encode_params(params)
        else:
            enc_params = ""

        if enc_params:
            if query:
                query = f"{query}&{enc_params}"
            else:
                query = enc_params

        url = requote_uri(urlunparse((scheme, netloc, path, "", query, fragment)))
        self.url = url

    def prepare_headers(self, headers: Mapping[str, str | bytes] | None) -> None:
        

        self.headers = CaseInsensitiveDict()
        if headers:
            for header in headers.items():
                 
                check_header_validity(header)
                name, value = header
                self.headers[to_native_string(name)] = value

    def prepare_body(
        self, data: _t.DataType, files: _t.FilesType, json: _t.JsonType = None
    ) -> None:
        

         
         

         
        body = None
        content_type = None

        if not data and json is not None:
             
             
            content_type = "application/json"

            try:
                body = complexjson.dumps(json, allow_nan=False)
            except ValueError as ve:
                raise InvalidJSONError(ve, request=self)

            if not isinstance(body, bytes):
                body = body.encode("utf-8")

         
        is_iterable = isinstance(data, Iterable) or hasattr(data, "__iter__")
        if is_iterable and not isinstance(data, (str, bytes, list, tuple, Mapping)):
            try:
                length = super_len(data)
            except (TypeError, AttributeError, UnsupportedOperation):
                length = None

            body = data

            if getattr(body, "tell", None) is not None:
                 
                 
                 
                try:
                    self._body_position = body.tell()   
                except OSError:
                     
                     
                    self._body_position = object()

            if files:
                raise NotImplementedError(
                    "Streamed bodies and files are mutually exclusive."
                )

            if length:
                self.headers["Content-Length"] = builtin_str(length)
            else:
                self.headers["Transfer-Encoding"] = "chunked"
        else:
             
            raw_data = cast("_t.RawDataType | None", data)

             
            if files:
                (body, content_type) = self._encode_files(files, raw_data)
            else:
                if raw_data:
                    body = self._encode_params(raw_data)
                    if isinstance(data, basestring) or _t.has_read(data):
                        content_type = None
                    else:
                        content_type = "application/x-www-form-urlencoded"

            self.prepare_content_length(body)

             
            if content_type and ("content-type" not in self.headers):
                self.headers["Content-Type"] = content_type

        self.body = body   

    def prepare_content_length(self, body: _t.BodyType) -> None:
        
        if body is not None:
            length = super_len(body)
            if length:
                 
                 
                self.headers["Content-Length"] = builtin_str(length)
        elif (
            self.method not in ("GET", "HEAD")
            and self.headers.get("Content-Length") is None
        ):
             
             
            self.headers["Content-Length"] = "0"

    def prepare_auth(
        self,
        auth: _t.AuthType,
        url: _t.UriType = "",
    ) -> None:
        

         
        if auth is None:
            url_auth = get_auth_from_url(cast(str, self.url))
            auth = url_auth if any(url_auth) else None

        if auth:
            if isinstance(auth, tuple) and len(auth) == 2:   
                 
                auth_handler = HTTPBasicAuth(*auth)   
            else:
                 
                auth_handler = cast("Callable[..., PreparedRequest]", auth)

             
            r = auth_handler(self)

             
            self.__dict__.update(r.__dict__)

             
            self.prepare_content_length(self.body)

    def prepare_cookies(
        self, cookies: RequestsCookieJar | CookieJar | dict[str, str] | None
    ) -> None:
        
        if isinstance(cookies, cookielib.CookieJar):
            self._cookies = cookies
        else:
            self._cookies = cookiejar_from_dict(cookies)

        cookies_jar = cast("CookieJar", self._cookies)
        cookie_header = get_cookie_header(cookies_jar, self)
        if cookie_header is not None:
            self.headers["Cookie"] = cookie_header

    def prepare_hooks(self, hooks: _t.HooksInputType | None) -> None:
        
         
         
         
        hooks = hooks or {}
        for event in hooks:
            self.register_hook(event, hooks[event])
