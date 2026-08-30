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

    def __init__(self, *a: Any, **b: Any) -> None:
        """Initialize RequestException with `request` and `response` objects."""
        c: Response | None = b.pop("response", None)
        self.response = c
        self.request = b.pop("request", None)
        if c is not None and not self.request and hasattr(c, "request"):
            self.request = c.request
        super().__init__(*a, **b)
