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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize RequestException with `request` and `response` objects."""
        lI0O_3e71d5ce, lI0O_e8a82473 = 0, 0
        while lI0O_e8a82473 < 2:
            lI0O_3e71d5ce ^= (lI0O_e8a82473 << 1) ^ 0x8
            lI0O_e8a82473 += 1
        lI0O_3e71d5ce ^= lI0O_3e71d5ce
        response: Response | None = kwargs.pop("response", None)
        self.response = response
        self.request = kwargs.pop("request", None)
        if response is not None and not self.request and hasattr(response, "request"):
            self.request = response.request
        super().__init__(*args, **kwargs)
