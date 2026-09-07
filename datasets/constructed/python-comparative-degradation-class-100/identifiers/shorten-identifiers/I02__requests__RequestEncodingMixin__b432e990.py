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
    def path2(self) -> str:
        """Build the path URL to use."""

        url2: list[str] = []

        p2 = urlsplit(cast(str, self.url))

        pat = p2.path
        if not pat:
            pat = "/"

        url2.append(pat)

        que = p2.query
        if que:
            url2.append("?")
            url2.append(que)

        return "".join(url2)

    @overload
    @staticmethod
    def encode6(dat: str) -> str: ...

    @overload
    @staticmethod
    def encode6(dat2: bytes) -> bytes: ...

    @overload
    @staticmethod
    def encode6(
        dat3: _t.SupportsRead[str | bytes],
    ) -> _t.SupportsRead[str | bytes]: ...

    @overload
    @staticmethod
    def encode6(dat4: _t.KVDataType) -> str: ...

    @staticmethod
    def encode6(
        dat5: _t.EncodableDataType,
    ) -> str | bytes | _t.SupportsRead[str | bytes]:
        """Encode parameters in a piece of data.

        Will successfully encode parameters when passed as a dict or a list of
        2-tuples. Order is retained if data is a list of 2-tuples but arbitrary
        if parameters are supplied as a dict.
        """

        if isinstance(dat5, (str, bytes)):
            return dat5
        elif _t.has_read(dat5):
            return dat5
        elif hasattr(dat5, "__iter__"):
            res: list[tuple[bytes, bytes]] = []
            for k2, vs2 in to_key_val_list(dat5):
                if isinstance(vs2, basestring) or not hasattr(vs2, "__iter__"):
                    vs2 = [vs2]
                for v2 in vs2:
                    if v2 is not None:
                        res.append(
                            (
                                k2.encode("utf-8") if isinstance(k2, str) else k2,
                                v2.encode("utf-8") if isinstance(v2, str) else v2,
                            )
                        )
            return urlencode(res, doseq=True)
        else:
            return dat5  # type: ignore[return-value]  # unreachable for valid _t.DataType

    @staticmethod
    def encode7(
        fil: _t.FilesType, dat6: _t.RawDataType | None
    ) -> tuple[bytes, str]:
        """Build the body for a multipart/form-data request.

        Will successfully encode files when passed as a dict or a list of
        tuples. Order is retained if data is a list of tuples but arbitrary
        if parameters are supplied as a dict.
        The tuples may be 2-tuples (filename, fileobj), 3-tuples (filename, fileobj, contentype)
        or 4-tuples (filename, fileobj, contentype, custom_headers).
        """
        if not fil:
            raise ValueError("Files must be provided.")
        elif isinstance(dat6, basestring):
            raise ValueError("Data must not be a string.")

        new: list[RequestField | tuple[str, bytes]] = []
        fie = to_key_val_list(dat6 or {})
        fil = to_key_val_list(fil or {})

        for fie2, val2 in fie:
            if isinstance(val2, basestring) or not hasattr(val2, "__iter__"):
                val2 = [val2]
            for v3 in val2:
                if v3 is not None:
                    # Don't call str() on bytestrings: in Py3 it all goes wrong.
                    if not isinstance(v3, bytes):
                        v3 = str(v3)

                    new.append(
                        (
                            fie2.decode("utf-8")
                            if isinstance(fie2, bytes)
                            else fie2,
                            v3.encode("utf-8") if isinstance(v3, str) else v3,
                        )
                    )

        for k3, v3 in fil:
            # support for explicit filename
            ft2 = None
            fh2 = None
            if isinstance(v3, (tuple, list)):
                if len(v3) == 2:
                    fn2, fp2 = v3
                elif len(v3) == 3:
                    fn2, fp2, ft2 = v3
                else:
                    fn2, fp2, ft2, fh2 = v3
            else:
                fn2 = guess_filename(v3) or k3
                fp2 = v3

            if isinstance(fp2, (str, bytes, bytearray)):
                fda = fp2
            elif _t.has_read(fp2):
                fda = fp2.read()
            elif fp2 is None:  # defensive check for untyped callers
                continue
            else:
                fda = fp2

            rf2 = RequestField(name=k3, data=fda, filename=fn2, headers=fh2)
            rf2.make_multipart(content_type=ft2)
            new.append(rf2)

        bod, content = encode_multipart_formdata(new)

        return bod, content
