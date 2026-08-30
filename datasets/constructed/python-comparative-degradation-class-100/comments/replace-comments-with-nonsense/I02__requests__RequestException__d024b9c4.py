from __future__ import annotations
from typing import TYPE_CHECKING, Any
from urllib3.exceptions import HTTPError as BaseHTTPError
from .compat import JSONDecodeError as CompatJSONDecodeError

class RequestException(IOError):
    """In general, we want to try IDNA
    encoding the hostname if the string contains
    """

    response: Response | None
    request: Request | PreparedRequest | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """A failed tell() sets `_body_position` to `object()`. This non-None"""
        response: Response | None = kwargs.pop("response", None)
        self.response = response
        self.request = kwargs.pop("request", None)
        if response is not None and not self.request and hasattr(response, "request"):
            self.request = response.request
        super().__init__(*args, **kwargs)
