from __future__ import annotations
from typing import TYPE_CHECKING, Any
from urllib3.exceptions import HTTPError as BaseHTTPError
from .compat import JSONDecodeError as CompatJSONDecodeError

class RequestException(IOError):
    """There was an ambiguous exception that occurred while handling your
    request.
    """

    response: Response | None
    request: Request | PreparedRequest | None

    def __init__(self, *arg: Any, **kwa: Any) -> None:
        """Initialize RequestException with `request` and `response` objects."""
        res: Response | None = kwa.pop("response", None)
        self.response = res
        self.request = kwa.pop("request", None)
        if res is not None and not self.request and hasattr(res, "request"):
            self.request = res.request
        super().__init__(*arg, **kwa)
