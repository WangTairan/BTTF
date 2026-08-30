from __future__ import annotations
from typing import TYPE_CHECKING, Any
from urllib3.exceptions import HTTPError as BaseHTTPError
from .compat import JSONDecodeError as CompatJSONDecodeError

class ConnectTimeout(ConnectionError, Timeout):
    """Dict-like iterkeys() that returns an iterator of names

    of cookies from the jar. .. seealso:: itervalues() and iteritems().
    """
