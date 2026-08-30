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

class Response:
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.
    """

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

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None  # type: ignore[assignment]

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-encoding']`` will return the
        #: value of a ``'Content-Encoding'`` response header.
        self.headers = CaseInsensitiveDict()

        #: File-like object representation of response (for advanced usage).
        #: Use of ``raw`` requires that ``stream=True`` be set on the request.
        #: This requirement does not apply for use internally to Requests.
        self.raw = None

        #: Final URL location of Response.
        self.url = None  # type: ignore[assignment]

        #: Encoding to decode with when accessing r.text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request. Any redirect responses will end
        #: up here. The list is sorted from the oldest to the most recent request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None  # type: ignore[assignment]

        #: A CookieJar of Cookies the server sent back.
        self.cookies = cookiejar_from_dict({})

        #: The amount of time elapsed between sending the request
        #: and the arrival of the response (as a timedelta).
        #: This property specifically measures the time taken between sending
        #: the first byte of the request and finishing parsing the headers. It
        #: is therefore unaffected by consuming the response content or the
        #: value of the ``stream`` keyword argument.
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None  # type: ignore[assignment]

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *arg: Any) -> None:
        self.clo()

    def __getstate__(self) -> dict[str, Any]:
        # Consume everything; accessing the content attribute makes
        # sure the content has been fully read.
        if not self._content_consumed:
            self.con

        return {att: getattr(self, att, None) for att in self.__attrs__}

    def __setstate__(self, sta: dict[str, Any]) -> None:
        for nam, val in sta.items():
            setattr(self, nam, val)

        # pickled objects do not have .raw
        setattr(self, "_content_consumed", True)
        setattr(self, "raw", None)

    def __repr__(self) -> str:
        return f"<Response [{self.status_code}]>"

    def __bool__(self) -> bool:
        """Returns True if :attr:`status_code` is less than 400.

        This attribute checks if the status code of the response is between
        400 and 600 to see if there was a client error or a server error. If
        the status code, is between 200 and 400, this will return True. This
        is **not** a check to see if the response code is ``200 OK``.
        """
        return self.ok2

    def __nonzero__(self) -> bool:
        """Returns True if :attr:`status_code` is less than 400.

        This attribute checks if the status code of the response is between
        400 and 600 to see if there was a client error or a server error. If
        the status code, is between 200 and 400, this will return True. This
        is **not** a check to see if the response code is ``200 OK``.
        """
        return self.ok2

    def __iter__(self) -> Iterator[bytes]:
        """Allows you to use a response as an iterator."""
        return self.iter3(128)

    @property
    def ok2(self) -> bool:
        """Returns True if :attr:`status_code` is less than 400, False if not.

        This attribute checks if the status code of the response is between
        400 and 600 to see if there was a client error or a server error. If
        the status code is between 200 and 400, this will return True. This
        is **not** a check to see if the response code is ``200 OK``.
        """
        try:
            self.raise2()
        except HTTPError:
            return False
        return True

    @property
    def is2(self) -> bool:
        """True if this Response is a well-formed HTTP redirect that could have
        been processed automatically (by :meth:`Session.resolve_redirects`).
        """
        return "location" in self.headers and self.status_code in REDIRECT_STATI

    @property
    def is3(self) -> bool:
        """True if this Response one of the permanent versions of redirect."""
        return "location" in self.headers and self.status_code in (
            codes.moved_permanently,
            codes.permanent_redirect,
        )

    @property
    def nex(self) -> PreparedRequest | None:
        """Returns a PreparedRequest for the next request in a redirect chain, if there is one."""
        return self._next

    @property
    def apparent(self) -> str | None:
        """The apparent encoding, provided by the charset_normalizer or chardet libraries."""
        if chardet is not None:
            return chardet.detect(self.con)["encoding"]
        else:
            # If no character detection library is available, we'll fall back
            # to a standard Python utf-8 str.
            return "utf-8"

    @overload
    def iter3(
        self, chunk2: int | None = 1, decode2: Literal[False] = False
    ) -> Iterator[bytes]: ...
    @overload
    def iter3(
        self, chunk3: int | None = 1, *, decode3: Literal[True]
    ) -> Iterator[str | bytes]: ...
    def iter3(
        self, chunk4: int | None = 1, decode4: bool = False
    ) -> Iterator[str | bytes]:
        """Iterates over the response data.  When stream=True is set on the
        request, this avoids reading the content at once into memory for
        large responses.  The chunk size is the number of bytes it should
        read into memory.  This is not necessarily the length of each item
        returned as decoding can take place.

        chunk_size must be of type int or None. A value of None will
        function differently depending on the value of `stream`.
        stream=True will read data as it arrives in whatever size the
        chunks are received. If stream=False, data is returned as
        a single chunk.

        If decode_unicode is True, content will be decoded using encoding
        information from the response. If no encoding information is available,
        bytes will be returned. This can be bypassed by manually setting
        `encoding` on the response.
        """

        def generate() -> Generator[bytes, None, None]:
            # Special case for urllib3.
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
                # Standard file-like object.
                while True:
                    chu2 = self.raw.read(chunk_size)
                    if not chu2:
                        break
                    yield chu2

            self._content_consumed = True

        if self._content_consumed and isinstance(self._content, bool):
            raise StreamConsumedError()
        elif chunk4 is not None and not isinstance(
            chunk4, int
        ):  # runtime guard for untyped callers
            raise TypeError(
                f"chunk_size must be an int, it is instead a {type(chunk4)}."
            )

        if self._content_consumed:
            # simulate reading small chunks of the content
            con2 = cast(bytes, self._content)
            chu = iter_slices(con2, chunk4)
        else:
            chu = generate()

        if decode4:
            chu = stream_decode_response_unicode(chu, self)

        return chu

    @overload
    def iter6(
        self,
        chunk5: int = ITER_CHUNK_SIZE,
        decode5: Literal[False] = False,
        del2: bytes | None = None,
    ) -> Iterator[bytes]: ...
    @overload
    def iter6(
        self,
        chunk6: int = ITER_CHUNK_SIZE,
        *,
        decode6: Literal[True],
        del3: str | bytes | None = None,
    ) -> Iterator[str | bytes]: ...
    def iter6(
        self,
        chunk7: int = ITER_CHUNK_SIZE,
        decode7: bool = False,
        del4: str | bytes | None = None,
    ) -> Iterator[str | bytes]:
        """Iterates over the response data, one line at a time.  When
        stream=True is set on the request, this avoids reading the
        content at once into memory for large responses.

        The decode_unicode param works the same as in `iter_content`, with the
        same caveats.

        .. note:: This method is not reentrant safe.
        """

        pen: str | bytes | None = None

        for chu3 in self.iter3(
            chunk_size=chunk7, decode_unicode=decode7
        ):
            if pen is not None:
                # TODO: remove cast after iter_lines rewrite
                chu3 = cast("str | bytes", pen + chu3)

            if del4:
                lin2 = chu3.split(del4)  # type: ignore[arg-type]
            else:
                lin2 = chu3.splitlines()

            if lin2 and lin2[-1] and chu3 and lin2[-1][-1] == chu3[-1]:
                pen = lin2.pop()
            else:
                pen = None

            yield from lin2

        if pen is not None:
            yield pen

    @property
    def con(self) -> bytes:
        """Content of the response, in bytes."""

        if self._content is False:
            # Read the contents.
            if self._content_consumed:
                raise RuntimeError("The content for this response was already consumed")

            if self.status_code == 0 or self.raw is None:
                self._content = None
            else:
                self._content = b"".join(self.iter3(CONTENT_CHUNK_SIZE)) or b""

        self._content_consumed = True
        # don't need to release the connection; that's been handled by urllib3
        # since we exhausted the data.
        return self._content  # type: ignore[return-value]

    @property
    def tex(self) -> str:
        """Content of the response, in unicode.

        If Response.encoding is None, encoding will be guessed using
        ``charset_normalizer`` or ``chardet``.

        The encoding of the response content is determined based solely on HTTP
        headers, following RFC 2616 to the letter. If you can take advantage of
        non-HTTP knowledge to make a better guess at the encoding, you should
        set ``r.encoding`` appropriately before accessing this property.
        """

        # Try charset from content-type
        con3 = None
        enc = self.encoding

        if not self.con:
            return ""

        # Fallback to auto-detected encoding.
        if self.encoding is None:
            enc = self.apparent

        # Decode unicode from given encoding.
        try:
            con3 = str(self.con, enc or "utf-8", errors="replace")
        except (LookupError, TypeError):
            # A LookupError is raised if the encoding was not found which could
            # indicate a misspelling or similar mistake.
            #
            # A TypeError can be raised if encoding is None
            #
            # So we try blindly encoding.
            con3 = str(self.con, errors="replace")

        return con3

    def jso(self, **kwa: Any) -> Any:
        r"""Decodes the JSON response body (if any) as a Python object.

        This may return a dictionary, list, etc. depending on what is in the response.

        :param \*\*kwargs: Optional arguments that ``json.loads`` takes.
        :raises requests.exceptions.JSONDecodeError: If the response body does not
            contain valid json.
        """

        if not self.encoding and self.con and len(self.con) > 3:
            # No encoding set. JSON RFC 4627 section 3 states we should expect
            # UTF-8, -16 or -32. Detect which one to use; If the detection or
            # decoding fails, fall back to `self.text` (using charset_normalizer to make
            # a best guess).
            enc2 = guess_json_utf(self.con)
            if enc2 is not None:
                try:
                    return complexjson.loads(self.con.decode(enc2), **kwa)
                except UnicodeDecodeError:
                    # Wrong UTF codec detected; usually because it's not UTF-8
                    # but some other 8-bit codec.  This is an RFC violation,
                    # and the server didn't bother to tell us what codec *was*
                    # used.
                    pass
                except JSONDecodeError as e:
                    raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)

        try:
            return complexjson.loads(self.tex, **kwa)
        except JSONDecodeError as e:
            # Catch JSON-related errors and raise as requests.JSONDecodeError
            # This aliases json.JSONDecodeError and simplejson.JSONDecodeError
            raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)

    @property
    def lin(self) -> dict[str, dict[str, str]]:
        """Returns the parsed header links of the response, if any."""

        hea = self.headers.get("link")

        resolved: dict[str, dict[str, str]] = {}

        if hea:
            lin3 = parse_header_links(hea)

            for lin4 in lin3:
                key2 = lin4.get("rel") or lin4.get("url")
                if key2 is not None:
                    resolved[key2] = lin4

        return resolved

    def raise2(self) -> None:
        """Raises :class:`HTTPError`, if one occurred."""

        http = ""
        if isinstance(self.reason, bytes):
            # We attempt to decode utf-8 first because some servers
            # choose to localize their reason strings. If the string
            # isn't utf-8, we fall back to iso-8859-1 for all other
            # encodings. (See PR #3538)
            try:
                rea = self.reason.decode("utf-8")
            except UnicodeDecodeError:
                rea = self.reason.decode("iso-8859-1")
        else:
            rea = self.reason

        if 400 <= self.status_code < 500:
            http = (
                f"{self.status_code} Client Error: {rea} for url: {self.url}"
            )

        elif 500 <= self.status_code < 600:
            http = (
                f"{self.status_code} Server Error: {rea} for url: {self.url}"
            )

        if http:
            raise HTTPError(http, response=self)

    def clo(self) -> None:
        """Releases the connection back to the pool. Once this method has been
        called the underlying ``raw`` object must not be accessed again.

        *Note: Should not normally need to be called explicitly.*
        """
        if not self._content_consumed:
            self.raw.close()

        release = getattr(self.raw, "release_conn", None)
        if release is not None:
            release()
