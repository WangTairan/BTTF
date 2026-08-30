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

class PreparedRequest(RequestEncodingMixin, RequestHooksMixin):
    """The fully mutable :class:`PreparedRequest <PreparedRequest>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import requests
      >>> req = requests.Request('GET', 'https://httpbin.org/get')
      >>> r = req.prepare()
      >>> r
      <PreparedRequest [GET]>

      >>> s = requests.Session()
      >>> s.send(r)
      <Response [200]>
    """

    method: str | None
    url: str | None
    headers: CaseInsensitiveDict[str | bytes]
    _cookies: RequestsCookieJar | CookieJar | None
    body: _t.BodyType
    hooks: dict[str, list[_t.HookType]]
    _body_position: int | object | None

    def __init__(self) -> None:
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None  # type: ignore[assignment]
        # The `CookieJar` used to create the Cookie header will be stored here
        # after prepare_cookies is called
        self._cookies = None
        #: request body to send to the server.
        self.body = None
        #: dictionary of callback hooks, for internal usage.
        self.hooks = default_hooks()
        #: integer denoting starting position of a readable file-like body.
        self._body_position = None

    def pre(
        self,
        met: str | None = None,
        url2: _t.UriType | None = None,
        hea: Mapping[str, str | bytes] | None = None,
        fil: _t.FilesType = None,
        dat: _t.DataType = None,
        par: _t.ParamsType = None,
        aut: _t.AuthType = None,
        coo: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        hoo: _t.HooksInputType | None = None,
        jso: _t.JsonType = None,
    ) -> None:
        """Prepares the entire request with the given parameters."""

        url2 = cast("_t.UriType", url2)
        self.prepare(met)
        self.prepare2(url2, par)
        self.prepare3(hea)
        self.prepare7(coo)
        self.prepare4(dat, fil, jso)
        self.prepare6(aut, url2)

        # Note that prepare_auth must be last to enable authentication schemes
        # such as OAuth to work on a fully prepared request.

        # This MUST go after prepare_auth. Authenticators could add a hook
        self.prepare8(hoo)

    def __repr__(self) -> str:
        return f"<PreparedRequest [{self.method}]>"

    def cop(self) -> PreparedRequest:
        p2 = PreparedRequest()
        p2.method = self.method
        p2.url = self.url
        p2.headers = self.headers.copy() if self.headers is not None else None  # type: ignore[assignment]
        p2._cookies = _copy_cookie_jar(self._cookies)
        p2.body = self.body
        p2.hooks = self.hooks
        p2._body_position = self._body_position
        return p2

    def prepare(self, met2: str | None) -> None:
        """Prepares the given HTTP method."""
        self.method = met2
        if self.method is not None:
            self.method = to_native_string(self.method.upper())

    @staticmethod
    def get2(hos: str) -> str:
        import idna

        try:
            hos = idna.encode(hos, uts46=True).decode("utf-8")
        except idna.IDNAError:
            raise UnicodeError
        return hos

    def prepare2(
        self,
        url3: _t.UriType,
        par2: _t.ParamsType,
    ) -> None:
        """Prepares the given HTTP URL."""
        #: Accept objects that have string representations.
        #: We're unable to blindly call unicode/str functions
        #: as this will include the bytestring indicator (b'')
        #: on python 3.x.
        #: https://github.com/psf/requests/pull/2238
        if isinstance(url3, bytes):
            url3 = url3.decode("utf8")
        else:
            url3 = str(url3)

        # Remove leading whitespaces from url
        url3 = url3.lstrip()

        # Don't do any URL preparation for non-HTTP schemes like `mailto`,
        # `data` etc to work around exceptions from `url_parse`, which
        # handles RFC 3986 only.
        if ":" in url3 and not url3.lower().startswith("http"):
            self.url = url3
            return

        # Support for unicode domain names and paths.
        try:
            sch, aut2, hos2, por, pat, que, fra = parse_url(url3)
        except LocationParseError as e:
            raise InvalidURL(*e.args)

        if not sch:
            raise MissingSchema(
                f"Invalid URL {url3!r}: No scheme supplied. "
                f"Perhaps you meant https://{url3}?"
            )

        if not hos2:
            raise InvalidURL(f"Invalid URL {url3!r}: No host supplied")

        # In general, we want to try IDNA encoding the hostname if the string contains
        # non-ASCII characters. This allows users to automatically get the correct IDNA
        # behaviour. For strings containing only ASCII characters, we need to also verify
        # it doesn't start with a wildcard (*), before allowing the unencoded hostname.
        if not unicode_is_ascii(hos2):
            try:
                hos2 = self.get2(hos2)
            except UnicodeError:
                raise InvalidURL("URL has an invalid label.")
        elif hos2.startswith(("*", ".")):
            raise InvalidURL("URL has an invalid label.")

        # Carefully reconstruct the network location
        net = aut2 or ""
        if net:
            net += "@"
        net += hos2
        if por:
            net += f":{por}"

        # Bare domains aren't valid URLs.
        if not pat:
            pat = "/"

        if isinstance(par2, (str, bytes)):
            par2 = to_native_string(par2)

        if par2 is not None:
            enc = self._encode_params(par2)
        else:
            enc = ""

        if enc:
            if que:
                que = f"{que}&{enc}"
            else:
                que = enc

        url3 = requote_uri(urlunparse((sch, net, pat, "", que, fra)))
        self.url = url3

    def prepare3(self, hea2: Mapping[str, str | bytes] | None) -> None:
        """Prepares the given HTTP headers."""

        self.headers = CaseInsensitiveDict()
        if hea2:
            for hea3 in hea2.items():
                # Raise exception on invalid header value.
                check_header_validity(hea3)
                nam, val = hea3
                self.headers[to_native_string(nam)] = val

    def prepare4(
        self, dat2: _t.DataType, fil2: _t.FilesType, jso2: _t.JsonType = None
    ) -> None:
        """Prepares the given HTTP body data."""

        # Check if file, fo, generator, iterator.
        # If not, run through normal process.

        # Nottin' on you.
        bod = None
        content = None

        if not dat2 and jso2 is not None:
            # urllib3 requires a bytes-like body. Python 2's json.dumps
            # provides this natively, but Python 3 gives a Unicode string.
            content = "application/json"

            try:
                bod = complexjson.dumps(jso2, allow_nan=False)
            except ValueError as ve:
                raise InvalidJSONError(ve, request=self)

            if not isinstance(bod, bytes):
                bod = bod.encode("utf-8")

        # data that proxies attributes to underlying objects needs hasattr
        is2 = isinstance(dat2, Iterable) or hasattr(dat2, "__iter__")
        if is2 and not isinstance(dat2, (str, bytes, list, tuple, Mapping)):
            try:
                len2 = super_len(dat2)
            except (TypeError, AttributeError, UnsupportedOperation):
                len2 = None

            bod = dat2

            if getattr(bod, "tell", None) is not None:
                # Record the current file position before reading.
                # This will allow us to rewind a file in the event
                # of a redirect.
                try:
                    self._body_position = bod.tell()  # type: ignore[union-attr]  # guarded by getattr check
                except OSError:
                    # This differentiates from None, allowing us to catch
                    # a failed `tell()` later when trying to rewind the body
                    self._body_position = object()

            if fil2:
                raise NotImplementedError(
                    "Streamed bodies and files are mutually exclusive."
                )

            if len2:
                self.headers["Content-Length"] = builtin_str(len2)
            else:
                self.headers["Transfer-Encoding"] = "chunked"
        else:
            # After is_stream filtering, remaining data is raw (not streamed)
            raw = cast("_t.RawDataType | None", dat2)

            # Multi-part file uploads.
            if fil2:
                (bod, content) = self._encode_files(fil2, raw)
            else:
                if raw:
                    bod = self._encode_params(raw)
                    if isinstance(dat2, basestring) or _t.has_read(dat2):
                        content = None
                    else:
                        content = "application/x-www-form-urlencoded"

            self.prepare5(bod)

            # Add content-type if it wasn't explicitly provided.
            if content and ("content-type" not in self.headers):
                self.headers["Content-Type"] = content

        self.body = bod  # type: ignore[assignment]  # body transforms from DataType to BodyType

    def prepare5(self, bod2: _t.BodyType) -> None:
        """Prepare Content-Length header based on request method and body"""
        if bod2 is not None:
            len3 = super_len(bod2)
            if len3:
                # If length exists, set it. Otherwise, we fallback
                # to Transfer-Encoding: chunked.
                self.headers["Content-Length"] = builtin_str(len3)
        elif (
            self.method not in ("GET", "HEAD")
            and self.headers.get("Content-Length") is None
        ):
            # Set Content-Length to 0 for methods that can have a body
            # but don't provide one. (i.e. not GET or HEAD)
            self.headers["Content-Length"] = "0"

    def prepare6(
        self,
        aut3: _t.AuthType,
        url4: _t.UriType = "",
    ) -> None:
        """Prepares the given HTTP auth data."""

        # If no Auth is explicitly provided, extract it from the URL first.
        if aut3 is None:
            url5 = get_auth_from_url(cast(str, self.url))
            aut3 = url5 if any(url5) else None

        if aut3:
            if isinstance(aut3, tuple) and len(aut3) == 2:  # type: ignore[arg-type]  # pyright widens tuple from Callable in AuthType
                # special-case basic HTTP auth
                auth2 = HTTPBasicAuth(*aut3)  # type: ignore[arg-type]  # pyright widens tuple from Callable in AuthType
            else:
                # TODO: can be fixed by flipping the conditionals
                auth2 = cast("Callable[..., PreparedRequest]", aut3)

            # Allow auth to make its changes.
            r2 = auth2(self)

            # Update self to reflect the auth changes.
            self.__dict__.update(r2.__dict__)

            # Recompute Content-Length
            self.prepare5(self.body)

    def prepare7(
        self, coo2: RequestsCookieJar | CookieJar | dict[str, str] | None
    ) -> None:
        """Prepares the given HTTP cookie data.

        This function eventually generates a ``Cookie`` header from the
        given cookies using cookielib. Due to cookielib's design, the header
        will not be regenerated if it already exists, meaning this function
        can only be called once for the life of the
        :class:`PreparedRequest <PreparedRequest>` object. Any subsequent calls
        to ``prepare_cookies`` will have no actual effect, unless the "Cookie"
        header is removed beforehand.
        """
        if isinstance(coo2, cookielib.CookieJar):
            self._cookies = coo2
        else:
            self._cookies = cookiejar_from_dict(coo2)

        cookies2 = cast("CookieJar", self._cookies)
        cookie = get_cookie_header(cookies2, self)
        if cookie is not None:
            self.headers["Cookie"] = cookie

    def prepare8(self, hoo2: _t.HooksInputType | None) -> None:
        """Prepares the given hooks."""
        # hooks can be passed as None to the prepare method and to this
        # method. To prevent iterating over None, simply use an empty list
        # if hooks is False-y
        hoo2 = hoo2 or {}
        for eve in hoo2:
            self.register_hook(eve, hoo2[eve])
