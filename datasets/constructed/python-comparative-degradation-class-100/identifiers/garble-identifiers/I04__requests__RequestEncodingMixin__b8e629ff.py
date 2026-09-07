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

class RequestEncodingMixin:
    url: str | None

    @property
    def a(self) -> str:
        """Build the path URL to use."""

        h: list[str] = []

        i = urlsplit(cast(str, self.url))

        j = i.path
        if not j:
            j = "/"

        h.append(j)

        l = i.query
        if l:
            h.append("?")
            h.append(l)

        return "".join(h)

    @overload
    @staticmethod
    def f(m: str) -> str: ...

    @overload
    @staticmethod
    def f(n: bytes) -> bytes: ...

    @overload
    @staticmethod
    def f(
        o: _t.SupportsRead[str | bytes],
    ) -> _t.SupportsRead[str | bytes]: ...

    @overload
    @staticmethod
    def f(q: _t.KVDataType) -> str: ...

    @staticmethod
    def f(
        r: _t.EncodableDataType,
    ) -> str | bytes | _t.SupportsRead[str | bytes]:
        """Encode parameters in a piece of data.

        Will successfully encode parameters when passed as a dict or a list of
        2-tuples. Order is retained if data is a list of 2-tuples but arbitrary
        if parameters are supplied as a dict.
        """

        if isinstance(r, (str, bytes)):
            return r
        elif _t.has_read(r):
            return r
        elif hasattr(r, "__iter__"):
            s: list[tuple[bytes, bytes]] = []
            for t, u in to_key_val_list(r):
                if isinstance(u, basestring) or not hasattr(u, "__iter__"):
                    u = [u]
                for w in u:
                    if w is not None:
                        s.append(
                            (
                                t.encode("utf-8") if isinstance(t, str) else t,
                                w.encode("utf-8") if isinstance(w, str) else w,
                            )
                        )
            return urlencode(s, doseq=True)
        else:
            return r  # type: ignore[return-value]  # unreachable for valid _t.DataType

    @staticmethod
    def g(
        x: _t.FilesType, y: _t.RawDataType | None
    ) -> tuple[bytes, str]:
        """Build the body for a multipart/form-data request.

        Will successfully encode files when passed as a dict or a list of
        tuples. Order is retained if data is a list of tuples but arbitrary
        if parameters are supplied as a dict.
        The tuples may be 2-tuples (filename, fileobj), 3-tuples (filename, fileobj, contentype)
        or 4-tuples (filename, fileobj, contentype, custom_headers).
        """
        if not x:
            raise ValueError("Files must be provided.")
        elif isinstance(y, basestring):
            raise ValueError("Data must not be a string.")

        z: list[RequestField | tuple[str, bytes]] = []
        A = to_key_val_list(y or {})
        x = to_key_val_list(x or {})

        for B, C in A:
            if isinstance(C, basestring) or not hasattr(C, "__iter__"):
                C = [C]
            for D in C:
                if D is not None:
                    # Don't call str() on bytestrings: in Py3 it all goes wrong.
                    if not isinstance(D, bytes):
                        D = str(D)

                    z.append(
                        (
                            B.decode("utf-8")
                            if isinstance(B, bytes)
                            else B,
                            D.encode("utf-8") if isinstance(D, str) else D,
                        )
                    )

        for E, D in x:
            # support for explicit filename
            F = None
            G = None
            if isinstance(D, (tuple, list)):
                if len(D) == 2:
                    H, I = D
                elif len(D) == 3:
                    H, I, F = D
                else:
                    H, I, F, G = D
            else:
                H = guess_filename(D) or E
                I = D

            if isinstance(I, (str, bytes, bytearray)):
                J = I
            elif _t.has_read(I):
                J = I.read()
            elif I is None:  # defensive check for untyped callers
                continue
            else:
                J = I

            K = RequestField(name=E, data=J, filename=H, headers=G)
            K.make_multipart(content_type=F)
            z.append(K)

        L, M = encode_multipart_formdata(z)

        return L, M
