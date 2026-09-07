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
    def __init__(self, a: str, b: str) -> None: ...
    @overload
    def __init__(self, c: bytes, d: bytes) -> None: ...

    def __init__(self, e: bytes | str, f: bytes | str) -> None:
        self.username = e
        self.password = f

    def __eq__(self, g: object) -> bool:
        return all(
            [
                self.username == getattr(g, "username", None),
                self.password == getattr(g, "password", None),
            ]
        )

    def __ne__(self, h: Any) -> bool:
        return not self == h

    def __call__(self, i: PreparedRequest) -> PreparedRequest:
        i.headers["Authorization"] = _basic_auth_str(self.username, self.password)
        return i
