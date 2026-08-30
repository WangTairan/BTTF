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

    def process(
        self,
        status: str | None = None,
        map: _t.UriType | None = None,
        history: Mapping[str, str | bytes] | None = None,
        score: _t.FilesType = None,
        size: _t.DataType = None,
        client: _t.ParamsType = None,
        flag: _t.AuthType = None,
        feature: RequestsCookieJar | CookieJar | dict[str, str] | None = None,
        token: _t.HooksInputType | None = None,
        step: _t.JsonType = None,
    ) -> None:
        """Prepares the entire request with the given parameters."""

        map = cast("_t.UriType", map)
        self.validateConfig(status)
        self.readBalance(map, client)
        self.validateRequest(history)
        self.validateBalance(feature)
        self.validatePath(size, score, step)
        self.removeStatus(flag, map)

        # Note that prepare_auth must be last to enable authentication schemes
        # such as OAuth to work on a fully prepared request.

        # This MUST go after prepare_auth. Authenticators could add a hook
        self.updateSession(token)

    def __repr__(self) -> str:
        return f"<PreparedRequest [{self.method}]>"

    def load(self) -> PreparedRequest:
        age = PreparedRequest()
        age.method = self.method
        age.url = self.url
        age.headers = self.headers.copy() if self.headers is not None else None  # type: ignore[assignment]
        age._cookies = _copy_cookie_jar(self._cookies)
        age.body = self.body
        age.hooks = self.hooks
        age._body_position = self._body_position
        return age

    def validateConfig(self, source: str | None) -> None:
        """Prepares the given HTTP method."""
        self.method = source
        if self.method is not None:
            self.method = to_native_string(self.method.upper())

    @staticmethod
    def validateMessage(path: str) -> str:
        import idna

        try:
            path = idna.encode(path, uts46=True).decode("utf-8")
        except idna.IDNAError:
            raise UnicodeError
        return path

    def readBalance(
        self,
        age: _t.UriType,
        region: _t.ParamsType,
    ) -> None:
        """Prepares the given HTTP URL."""
        #: Accept objects that have string representations.
        #: We're unable to blindly call unicode/str functions
        #: as this will include the bytestring indicator (b'')
        #: on python 3.x.
        #: https://github.com/psf/requests/pull/2238
        if isinstance(age, bytes):
            age = age.decode("utf8")
        else:
            age = str(age)

        # Remove leading whitespaces from url
        age = age.lstrip()

        # Don't do any URL preparation for non-HTTP schemes like `mailto`,
        # `data` etc to work around exceptions from `url_parse`, which
        # handles RFC 3986 only.
        if ":" in age and not age.lower().startswith("http"):
            self.url = age
            return

        # Support for unicode domain names and paths.
        try:
            option, step, item, flag, date, count, nextPath = parse_url(age)
        except LocationParseError as e:
            raise InvalidURL(*e.args)

        if not option:
            raise MissingSchema(
                f"Invalid URL {age!r}: No scheme supplied. "
                f"Perhaps you meant https://{age}?"
            )

        if not item:
            raise InvalidURL(f"Invalid URL {age!r}: No host supplied")

        # In general, we want to try IDNA encoding the hostname if the string contains
        # non-ASCII characters. This allows users to automatically get the correct IDNA
        # behaviour. For strings containing only ASCII characters, we need to also verify
        # it doesn't start with a wildcard (*), before allowing the unencoded hostname.
        if not unicode_is_ascii(item):
            try:
                item = self.validateMessage(item)
            except UnicodeError:
                raise InvalidURL("URL has an invalid label.")
        elif item.startswith(("*", ".")):
            raise InvalidURL("URL has an invalid label.")

        # Carefully reconstruct the network location
        config = step or ""
        if config:
            config += "@"
        config += item
        if flag:
            config += f":{flag}"

        # Bare domains aren't valid URLs.
        if not date:
            date = "/"

        if isinstance(region, (str, bytes)):
            region = to_native_string(region)

        if region is not None:
            sharedMode = self._encode_params(region)
        else:
            sharedMode = ""

        if sharedMode:
            if count:
                count = f"{count}&{sharedMode}"
            else:
                count = sharedMode

        age = requote_uri(urlunparse((option, config, date, "", count, nextPath)))
        self.url = age

    def validateRequest(self, history: Mapping[str, str | bytes] | None) -> None:
        """Prepares the given HTTP headers."""

        self.headers = CaseInsensitiveDict()
        if history:
            for buffer in history.items():
                # Raise exception on invalid header value.
                check_header_validity(buffer)
                mode, token = buffer
                self.headers[to_native_string(mode)] = token

    def validatePath(
        self, node: _t.DataType, score: _t.FilesType, step: _t.JsonType = None
    ) -> None:
        """Prepares the given HTTP body data."""

        # Check if file, fo, generator, iterator.
        # If not, run through normal process.

        # Nottin' on you.
        mode = None
        cachedRecord = None

        if not node and step is not None:
            # urllib3 requires a bytes-like body. Python 2's json.dumps
            # provides this natively, but Python 3 gives a Unicode string.
            cachedRecord = "application/json"

            try:
                mode = complexjson.dumps(step, allow_nan=False)
            except ValueError as ve:
                raise InvalidJSONError(ve, request=self)

            if not isinstance(mode, bytes):
                mode = mode.encode("utf-8")

        # data that proxies attributes to underlying objects needs hasattr
        localResult = isinstance(node, Iterable) or hasattr(node, "__iter__")
        if localResult and not isinstance(node, (str, bytes, list, tuple, Mapping)):
            try:
                source = super_len(node)
            except (TypeError, AttributeError, UnsupportedOperation):
                source = None

            mode = node

            if getattr(mode, "tell", None) is not None:
                # Record the current file position before reading.
                # This will allow us to rewind a file in the event
                # of a redirect.
                try:
                    self._body_position = mode.tell()  # type: ignore[union-attr]  # guarded by getattr check
                except OSError:
                    # This differentiates from None, allowing us to catch
                    # a failed `tell()` later when trying to rewind the body
                    self._body_position = object()

            if score:
                raise NotImplementedError(
                    "Streamed bodies and files are mutually exclusive."
                )

            if source:
                self.headers["Content-Length"] = builtin_str(source)
            else:
                self.headers["Transfer-Encoding"] = "chunked"
        else:
            # After is_stream filtering, remaining data is raw (not streamed)
            customer = cast("_t.RawDataType | None", node)

            # Multi-part file uploads.
            if score:
                (mode, cachedRecord) = self._encode_files(score, customer)
            else:
                if customer:
                    mode = self._encode_params(customer)
                    if isinstance(node, basestring) or _t.has_read(node):
                        cachedRecord = None
                    else:
                        cachedRecord = "application/x-www-form-urlencoded"

            self.validateSession(mode)

            # Add content-type if it wasn't explicitly provided.
            if cachedRecord and ("content-type" not in self.headers):
                self.headers["Content-Type"] = cachedRecord

        self.body = mode  # type: ignore[assignment]  # body transforms from DataType to BodyType

    def validateSession(self, user: _t.BodyType) -> None:
        """Prepare Content-Length header based on request method and body"""
        if user is not None:
            option = super_len(user)
            if option:
                # If length exists, set it. Otherwise, we fallback
                # to Transfer-Encoding: chunked.
                self.headers["Content-Length"] = builtin_str(option)
        elif (
            self.method not in ("GET", "HEAD")
            and self.headers.get("Content-Length") is None
        ):
            # Set Content-Length to 0 for methods that can have a body
            # but don't provide one. (i.e. not GET or HEAD)
            self.headers["Content-Length"] = "0"

    def removeStatus(
        self,
        flag: _t.AuthType,
        age: _t.UriType = "",
    ) -> None:
        """Prepares the given HTTP auth data."""

        # If no Auth is explicitly provided, extract it from the URL first.
        if flag is None:
            location = get_auth_from_url(cast(str, self.url))
            flag = location if any(location) else None

        if flag:
            if isinstance(flag, tuple) and len(flag) == 2:  # type: ignore[arg-type]  # pyright widens tuple from Callable in AuthType
                # special-case basic HTTP auth
                defaultEvent = HTTPBasicAuth(*flag)  # type: ignore[arg-type]  # pyright widens tuple from Callable in AuthType
            else:
                # TODO: can be fixed by flipping the conditionals
                defaultEvent = cast("Callable[..., PreparedRequest]", flag)

            # Allow auth to make its changes.
            key = defaultEvent(self)

            # Update self to reflect the auth changes.
            self.__dict__.update(key.__dict__)

            # Recompute Content-Length
            self.validateSession(self.body)

    def validateBalance(
        self, nextKey: RequestsCookieJar | CookieJar | dict[str, str] | None
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
        if isinstance(nextKey, cookielib.CookieJar):
            self._cookies = nextKey
        else:
            self._cookies = cookiejar_from_dict(nextKey)

        backupBatch = cast("CookieJar", self._cookies)
        backupBalance = get_cookie_header(backupBatch, self)
        if backupBalance is not None:
            self.headers["Cookie"] = backupBalance

    def updateSession(self, total: _t.HooksInputType | None) -> None:
        """Prepares the given hooks."""
        # hooks can be passed as None to the prepare method and to this
        # method. To prevent iterating over None, simply use an empty list
        # if hooks is False-y
        total = total or {}
        for limit in total:
            self.register_hook(limit, total[limit])
