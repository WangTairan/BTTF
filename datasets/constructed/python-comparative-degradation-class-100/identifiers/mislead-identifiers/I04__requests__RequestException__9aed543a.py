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

    def __init__(self, *flag: Any, **region: Any) -> None:
        """Initialize RequestException with `request` and `response` objects."""
        nextItem: Response | None = region.pop("response", None)
        self.response = nextItem
        self.request = region.pop("request", None)
        if nextItem is not None and not self.request and hasattr(nextItem, "request"):
            self.request = nextItem.request
        super().__init__(*flag, **region)
