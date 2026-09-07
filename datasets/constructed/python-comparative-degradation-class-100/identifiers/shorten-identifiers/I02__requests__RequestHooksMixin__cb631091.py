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

class RequestHooksMixin:
    hooks: dict[str, list[_t.HookType]]

    def register(
        self, eve: str, hoo: Iterable[_t.HookType] | _t.HookType
    ) -> None:
        """Properly register a hook."""

        if eve not in self.hooks:
            raise ValueError(f'Unsupported event specified, with event name "{eve}"')

        if isinstance(hoo, Callable):
            self.hooks[eve].append(hoo)
        elif hasattr(hoo, "__iter__"):
            self.hooks[eve].extend(
                h2 for h2 in hoo if isinstance(h2, Callable)
            )  # defensive runtime filter

    def deregister(self, eve2: str, hoo2: _t.HookType) -> bool:
        """Deregister a previously registered hook.
        Returns True if the hook existed, False if not.
        """

        try:
            self.hooks[eve2].remove(hoo2)
            return True
        except ValueError:
            return False
