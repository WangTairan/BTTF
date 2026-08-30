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
    def __init__(self, nextNode: str, nextData: str) -> None: ...
    @overload
    def __init__(self, nextPath: bytes, location: bytes) -> None: ...

    def __init__(self, localKey: bytes | str, finalKey: bytes | str) -> None:
        self.username = localKey
        self.password = finalKey

    def __eq__(self, value: object) -> bool:
        return all(
            [
                self.username == getattr(value, "username", None),
                self.password == getattr(value, "password", None),
            ]
        )

    def __ne__(self, score: Any) -> bool:
        return not self == score

    def __call__(self, age: PreparedRequest) -> PreparedRequest:
        age.headers["Authorization"] = _basic_auth_str(self.username, self.password)
        return age
