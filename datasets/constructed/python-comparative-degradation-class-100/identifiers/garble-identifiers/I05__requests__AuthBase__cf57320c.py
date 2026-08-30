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

class AuthBase:
    """Base class that all auth implementations derive from"""

    def __call__(self, a: PreparedRequest) -> PreparedRequest:
        raise NotImplementedError("Auth hooks must be callable.")
