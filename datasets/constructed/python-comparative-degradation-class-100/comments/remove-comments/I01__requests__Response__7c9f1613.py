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

class Response:
    

    _content: bytes | Literal[False] | None
    _content_consumed: bool
    _next: PreparedRequest | None
    status_code: int
    headers: CaseInsensitiveDict[str]
    raw: Any
    url: str
    encoding: str | None
    history: list[Response]
    reason: str
    cookies: RequestsCookieJar
    elapsed: datetime.timedelta
    request: PreparedRequest
    connection: HTTPAdapter

    __attrs__: list[str] = [
        "_content",
        "status_code",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
    ]

    def __init__(self) -> None:
        self._content = False
        self._content_consumed = False
        self._next = None

         
        self.status_code = None   

         
         
         
        self.headers = CaseInsensitiveDict()

         
         
         
        self.raw = None

         
        self.url = None   

         
        self.encoding = None

         
         
         
        self.history = []

         
        self.reason = None   

         
        self.cookies = cookiejar_from_dict({})

         
         
         
         
         
         
        self.elapsed = datetime.timedelta(0)

         
         
        self.request = None   

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __getstate__(self) -> dict[str, Any]:
         
         
        if not self._content_consumed:
            self.content

        return {attr: getattr(self, attr, None) for attr in self.__attrs__}

    def __setstate__(self, state: dict[str, Any]) -> None:
        for name, value in state.items():
            setattr(self, name, value)

         
        setattr(self, "_content_consumed", True)
        setattr(self, "raw", None)

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"

    def __bool__(self) -> bool:
        
        return self.ok

    def __nonzero__(self) -> bool:
        
        return self.ok

    def __iter__(self) -> Iterator[bytes]:
        
        return self.iter_content(128)

    @property
    def ok(self) -> bool:
        
        try:
            self.raise_for_status()
        except HTTPError:
            return False
        return True

    @property
    def is_redirect(self) -> bool:
        
        return "location" in self.headers and self.status_code in REDIRECT_STATI

    @property
    def is_permanent_redirect(self) -> bool:
        
        return "location" in self.headers and self.status_code in (
            codes.moved_permanently,
            codes.permanent_redirect,
        )

    @property
    def next(self) -> PreparedRequest | None:
        
        return self._next

    @property
    def apparent_encoding(self) -> str | None:
        
        if chardet is not None:
            return chardet.detect(self.content)["encoding"]
        else:
             
             
            return "utf-8"

    @overload
    def iter_content(
        self, chunk_size: int | None = 1, decode_unicode: Literal[False] = False
    ) -> Iterator[bytes]: ...
    @overload
    def iter_content(
        self, chunk_size: int | None = 1, *, decode_unicode: Literal[True]
    ) -> Iterator[str | bytes]: ...
    def iter_content(
        self, chunk_size: int | None = 1, decode_unicode: bool = False
    ) -> Iterator[str | bytes]:
        

        def generate() -> Generator[bytes, None, None]:
             
            if hasattr(self.raw, "stream"):
                try:
                    yield from self.raw.stream(chunk_size, decode_content=True)
                except ProtocolError as e:
                    raise ChunkedEncodingError(e)
                except DecodeError as e:
                    raise ContentDecodingError(e)
                except ReadTimeoutError as e:
                    raise ConnectionError(e)
                except SSLError as e:
                    raise RequestsSSLError(e)
            else:
                 
                while True:
                    chunk = self.raw.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

            self._content_consumed = True

        if self._content_consumed and isinstance(self._content, bool):
            raise StreamConsumedError()
        elif chunk_size is not None and not isinstance(
            chunk_size, int
        ):   
            raise TypeError(
                f"chunk_size must be an int, it is instead a {type(chunk_size)}."
            )

        if self._content_consumed:
             
            content = cast(bytes, self._content)
            chunks = iter_slices(content, chunk_size)
        else:
            chunks = generate()

        if decode_unicode:
            chunks = stream_decode_response_unicode(chunks, self)

        return chunks

    @overload
    def iter_lines(
        self,
        chunk_size: int = ITER_CHUNK_SIZE,
        decode_unicode: Literal[False] = False,
        delimiter: bytes | None = None,
    ) -> Iterator[bytes]: ...
    @overload
    def iter_lines(
        self,
        chunk_size: int = ITER_CHUNK_SIZE,
        *,
        decode_unicode: Literal[True],
        delimiter: str | bytes | None = None,
    ) -> Iterator[str | bytes]: ...
    def iter_lines(
        self,
        chunk_size: int = ITER_CHUNK_SIZE,
        decode_unicode: bool = False,
        delimiter: str | bytes | None = None,
    ) -> Iterator[str | bytes]:
        

        pending: str | bytes | None = None

        for chunk in self.iter_content(
            chunk_size=chunk_size, decode_unicode=decode_unicode
        ):
            if pending is not None:
                 
                chunk = cast("str | bytes", pending + chunk)

            if delimiter:
                lines = chunk.split(delimiter)   
            else:
                lines = chunk.splitlines()

            if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]:
                pending = lines.pop()
            else:
                pending = None

            yield from lines

        if pending is not None:
            yield pending

    @property
    def content(self) -> bytes:
        

        if self._content is False:
             
            if self._content_consumed:
                raise RuntimeError("The content for this response was already consumed")

            if self.status_code == 0 or self.raw is None:
                self._content = None
            else:
                self._content = b"".join(self.iter_content(CONTENT_CHUNK_SIZE)) or b""

        self._content_consumed = True
         
         
        return self._content   

    @property
    def text(self) -> str:
        

         
        content = None
        encoding = self.encoding

        if not self.content:
            return ""

         
        if self.encoding is None:
            encoding = self.apparent_encoding

         
        try:
            content = str(self.content, encoding or "utf-8", errors="replace")
        except (LookupError, TypeError):
             
             
             
             
             
             
            content = str(self.content, errors="replace")

        return content

    def json(self, **kwargs: Any) -> Any:
        

        if not self.encoding and self.content and len(self.content) > 3:
             
             
             
             
            encoding = guess_json_utf(self.content)
            if encoding is not None:
                try:
                    return complexjson.loads(self.content.decode(encoding), **kwargs)
                except UnicodeDecodeError:
                     
                     
                     
                     
                    pass
                except JSONDecodeError as e:
                    raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)

        try:
            return complexjson.loads(self.text, **kwargs)
        except JSONDecodeError as e:
             
             
            raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)

    @property
    def links(self) -> dict[str, dict[str, str]]:
        

        header = self.headers.get("link")

        resolved_links: dict[str, dict[str, str]] = {}

        if header:
            links = parse_header_links(header)

            for link in links:
                key = link.get("rel") or link.get("url")
                if key is not None:
                    resolved_links[key] = link

        return resolved_links

    def raise_for_status(self) -> None:
        

        http_error_msg = ""
        if isinstance(self.reason, bytes):
             
             
             
             
            try:
                reason = self.reason.decode("utf-8")
            except UnicodeDecodeError:
                reason = self.reason.decode("iso-8859-1")
        else:
            reason = self.reason

        if 400 <= self.status_code < 500:
            http_error_msg = (
                f"{self.status_code} Client Error: {reason} for url: {self.url}"
            )

        elif 500 <= self.status_code < 600:
            http_error_msg = (
                f"{self.status_code} Server Error: {reason} for url: {self.url}"
            )

        if http_error_msg:
            raise HTTPError(http_error_msg, response=self)

    def close(self) -> None:
        
        if not self._content_consumed:
            self.raw.close()

        release_conn = getattr(self.raw, "release_conn", None)
        if release_conn is not None:
            release_conn()
