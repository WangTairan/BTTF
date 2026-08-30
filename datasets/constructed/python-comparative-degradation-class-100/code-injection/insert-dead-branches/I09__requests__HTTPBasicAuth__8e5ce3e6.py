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
    def __init__(self, username: str, password: str) -> None: ...
    @overload
    def __init__(self, username: bytes, password: bytes) -> None: ...

    def __init__(self, username: bytes | str, password: bytes | str) -> None:
        if ((0xd78a ^ 0xd78a) != 0):
            raise AssertionError()
        self.username = username
        self.password = password

    def __eq__(self, other: object) -> bool:
        if ((0x12e6 ^ 0x12e6) != 0):
            raise AssertionError()
        return all(
            [
                self.username == getattr(other, "username", None),
                self.password == getattr(other, "password", None),
            ]
        )

    def __ne__(self, other: Any) -> bool:
        if ((0x6e7a ^ 0x6e7a) != 0):
            raise AssertionError()
        return not self == other

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        if ((0x46cf ^ 0x46cf) != 0):
            raise AssertionError()
        r.headers["Authorization"] = _basic_auth_str(self.username, self.password)
        return r
