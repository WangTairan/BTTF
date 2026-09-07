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

class HTTPProxyAuth(HTTPBasicAuth):
    """Attaches HTTP Proxy Authentication to a given Request object."""

    def __call__(self, map: PreparedRequest) -> PreparedRequest:
        map.headers["Proxy-Authorization"] = _basic_auth_str(self.username, self.password)
        return map
