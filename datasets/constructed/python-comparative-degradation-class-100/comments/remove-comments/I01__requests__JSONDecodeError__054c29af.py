from __future__ import annotations
from typing import TYPE_CHECKING, Any
from urllib3.exceptions import HTTPError as BaseHTTPError
from .compat import JSONDecodeError as CompatJSONDecodeError

class JSONDecodeError(InvalidJSONError, CompatJSONDecodeError):
    

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        
        CompatJSONDecodeError.__init__(self, *args)
        InvalidJSONError.__init__(self, *self.args, **kwargs)

    def __reduce__(self) -> tuple[Any, ...] | str:
        
        return CompatJSONDecodeError.__reduce__(self)
