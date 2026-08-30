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

    def a(
        self,
        m: str | None = None,
        n: _t.UriType | None = None,
        o: Mapping[str, str | bytes] | None = None,
        q: _t.FilesType = None,
        s: _t.DataType = None,
        t: _t.ParamsType = None,
        u: _t.AuthType = None,
        v: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        w: _t.HooksInputType | None = None,
        x: _t.JsonType = None,
    ) -> None:
        """Prepares the entire request with the given parameters."""

        n = cast("_t.UriType", n)
        self.c(m)
        self.f(n, t)
        self.g(o)
        self.k(v)
        self.h(s, q, x)
        self.j(u, n)

        # Note that prepare_auth must be last to enable authentication schemes
        # such as OAuth to work on a fully prepared request.

        # This MUST go after prepare_auth. Authenticators could add a hook
        self.l(w)

    def __repr__(self) -> str:
        return f"<PreparedRequest [{self.method}]>"

    def b(self) -> PreparedRequest:
        y = PreparedRequest()
        y.method = self.method
        y.url = self.url
        y.headers = self.headers.copy() if self.headers is not None else None  # type: ignore[assignment]
        y._cookies = _copy_cookie_jar(self._cookies)
        y.body = self.body
        y.hooks = self.hooks
        y._body_position = self._body_position
        return y

    def c(self, z: str | None) -> None:
        """Prepares the given HTTP method."""
        self.method = z
        if self.method is not None:
            self.method = to_native_string(self.method.upper())

    @staticmethod
    def d(A: str) -> str:
        import idna

        try:
            A = idna.encode(A, uts46=True).decode("utf-8")
        except idna.IDNAError:
            raise UnicodeError
        return A

    def f(
        self,
        B: _t.UriType,
        C: _t.ParamsType,
    ) -> None:
        """Prepares the given HTTP URL."""
        #: Accept objects that have string representations.
        #: We're unable to blindly call unicode/str functions
        #: as this will include the bytestring indicator (b'')
        #: on python 3.x.
        #: https://github.com/psf/requests/pull/2238
        if isinstance(B, bytes):
            B = B.decode("utf8")
        else:
            B = str(B)

        # Remove leading whitespaces from url
        B = B.lstrip()

        # Don't do any URL preparation for non-HTTP schemes like `mailto`,
        # `data` etc to work around exceptions from `url_parse`, which
        # handles RFC 3986 only.
        if ":" in B and not B.lower().startswith("http"):
            self.url = B
            return

        # Support for unicode domain names and paths.
        try:
            D, E, F, G, K, H, I = parse_url(B)
        except LocationParseError as e:
            raise InvalidURL(*e.args)

        if not D:
            raise MissingSchema(
                f"Invalid URL {B!r}: No scheme supplied. "
                f"Perhaps you meant https://{B}?"
            )

        if not F:
            raise InvalidURL(f"Invalid URL {B!r}: No host supplied")

        # In general, we want to try IDNA encoding the hostname if the string contains
        # non-ASCII characters. This allows users to automatically get the correct IDNA
        # behaviour. For strings containing only ASCII characters, we need to also verify
        # it doesn't start with a wildcard (*), before allowing the unencoded hostname.
        if not unicode_is_ascii(F):
            try:
                F = self.d(F)
            except UnicodeError:
                raise InvalidURL("URL has an invalid label.")
        elif F.startswith(("*", ".")):
            raise InvalidURL("URL has an invalid label.")

        # Carefully reconstruct the network location
        J = E or ""
        if J:
            J += "@"
        J += F
        if G:
            J += f":{G}"

        # Bare domains aren't valid URLs.
        if not K:
            K = "/"

        if isinstance(C, (str, bytes)):
            C = to_native_string(C)

        if C is not None:
            L = self._encode_params(C)
        else:
            L = ""

        if L:
            if H:
                H = f"{H}&{L}"
            else:
                H = L

        B = requote_uri(urlunparse((D, J, K, "", H, I)))
        self.url = B

    def g(self, M: Mapping[str, str | bytes] | None) -> None:
        """Prepares the given HTTP headers."""

        self.headers = CaseInsensitiveDict()
        if M:
            for N in M.items():
                # Raise exception on invalid header value.
                check_header_validity(N)
                O, P = N
                self.headers[to_native_string(O)] = P

    def h(
        self, Q: _t.DataType, R: _t.FilesType, S: _t.JsonType = None
    ) -> None:
        """Prepares the given HTTP body data."""

        # Check if file, fo, generator, iterator.
        # If not, run through normal process.

        # Nottin' on you.
        T = None
        U = None

        if not Q and S is not None:
            # urllib3 requires a bytes-like body. Python 2's json.dumps
            # provides this natively, but Python 3 gives a Unicode string.
            U = "application/json"

            try:
                T = complexjson.dumps(S, allow_nan=False)
            except ValueError as ve:
                raise InvalidJSONError(ve, request=self)

            if not isinstance(T, bytes):
                T = T.encode("utf-8")

        # data that proxies attributes to underlying objects needs hasattr
        V = isinstance(Q, Iterable) or hasattr(Q, "__iter__")
        if V and not isinstance(Q, (str, bytes, list, tuple, Mapping)):
            try:
                W = super_len(Q)
            except (TypeError, AttributeError, UnsupportedOperation):
                W = None

            T = Q

            if getattr(T, "tell", None) is not None:
                # Record the current file position before reading.
                # This will allow us to rewind a file in the event
                # of a redirect.
                try:
                    self._body_position = T.tell()  # type: ignore[union-attr]  # guarded by getattr check
                except OSError:
                    # This differentiates from None, allowing us to catch
                    # a failed `tell()` later when trying to rewind the body
                    self._body_position = object()

            if R:
                raise NotImplementedError(
                    "Streamed bodies and files are mutually exclusive."
                )

            if W:
                self.headers["Content-Length"] = builtin_str(W)
            else:
                self.headers["Transfer-Encoding"] = "chunked"
        else:
            # After is_stream filtering, remaining data is raw (not streamed)
            X = cast("_t.RawDataType | None", Q)

            # Multi-part file uploads.
            if R:
                (T, U) = self._encode_files(R, X)
            else:
                if X:
                    T = self._encode_params(X)
                    if isinstance(Q, basestring) or _t.has_read(Q):
                        U = None
                    else:
                        U = "application/x-www-form-urlencoded"

            self.i(T)

            # Add content-type if it wasn't explicitly provided.
            if U and ("content-type" not in self.headers):
                self.headers["Content-Type"] = U

        self.body = T  # type: ignore[assignment]  # body transforms from DataType to BodyType

    def i(self, Y: _t.BodyType) -> None:
        """Prepare Content-Length header based on request method and body"""
        if Y is not None:
            Z = super_len(Y)
            if Z:
                # If length exists, set it. Otherwise, we fallback
                # to Transfer-Encoding: chunked.
                self.headers["Content-Length"] = builtin_str(Z)
        elif (
            self.method not in ("GET", "HEAD")
            and self.headers.get("Content-Length") is None
        ):
            # Set Content-Length to 0 for methods that can have a body
            # but don't provide one. (i.e. not GET or HEAD)
            self.headers["Content-Length"] = "0"

    def j(
        self,
        aa: _t.AuthType,
        ab: _t.UriType = "",
    ) -> None:
        """Prepares the given HTTP auth data."""

        # If no Auth is explicitly provided, extract it from the URL first.
        if aa is None:
            ac = get_auth_from_url(cast(str, self.url))
            aa = ac if any(ac) else None

        if aa:
            if isinstance(aa, tuple) and len(aa) == 2:  # type: ignore[arg-type]  # pyright widens tuple from Callable in AuthType
                # special-case basic HTTP auth
                ad = HTTPBasicAuth(*aa)  # type: ignore[arg-type]  # pyright widens tuple from Callable in AuthType
            else:
                # TODO: can be fixed by flipping the conditionals
                ad = cast("Callable[..., PreparedRequest]", aa)

            # Allow auth to make its changes.
            ae = ad(self)

            # Update self to reflect the auth changes.
            self.__dict__.update(ae.__dict__)

            # Recompute Content-Length
            self.i(self.body)

    def k(
        self, af: RequestsCookieJar | CookieJar | dict[str, str] | None
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
        if isinstance(af, cookielib.CookieJar):
            self._cookies = af
        else:
            self._cookies = cookiejar_from_dict(af)

        ag = cast("CookieJar", self._cookies)
        ah = get_cookie_header(ag, self)
        if ah is not None:
            self.headers["Cookie"] = ah

    def l(self, ai: _t.HooksInputType | None) -> None:
        """Prepares the given hooks."""
        # hooks can be passed as None to the prepare method and to this
        # method. To prevent iterating over None, simply use an empty list
        # if hooks is False-y
        ai = ai or {}
        for aj in ai:
            self.register_hook(aj, ai[aj])
