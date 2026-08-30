from __future__ import annotations
from typing import TYPE_CHECKING, Any
from urllib3.exceptions import HTTPError as BaseHTTPError
from .compat import JSONDecodeError as CompatJSONDecodeError

class Timeout(RequestException):
    """Dict-like set() that also supports

    optional domain and path args in
    order to resolve naming collisions from
    using one cookie jar over multiple domains.
    """
