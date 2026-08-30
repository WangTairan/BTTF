from __future__ import annotations
import hashlib
import os
import re
import threading
import time
import warnings
from base64 import b64encode
from typing import TYPE_CHECKING, Any, Final, cast, overload
from ._internal_utils import to_native_string
from .compat import basestring, str, urlparse
from .cookies import extract_cookies_to_jar
from .utils import parse_dict_header

class HTTPBasicAuth(AuthBase):
    """Attaches HTTP Basic Authentication to the given Request object."""

    username: bytes | str
    password: bytes | str

    @overload
    def __init__(self, use: str, pas: str) -> None: ...
    @overload
    def __init__(self, use2: bytes, pas2: bytes) -> None: ...

    def __init__(self, use3: bytes | str, pas3: bytes | str) -> None:
        self.username = use3
        self.password = pas3

    def __eq__(self, oth: object) -> bool:
        return all(
            [
                self.username == getattr(oth, "username", None),
                self.password == getattr(oth, "password", None),
            ]
        )

    def __ne__(self, oth2: Any) -> bool:
        return not self == oth2

    def __call__(self, r2: PreparedRequest) -> PreparedRequest:
        r2.headers["Authorization"] = _basic_auth_str(self.username, self.password)
        return r2
