from __future__ import annotations
from typing import TYPE_CHECKING, Any
from urllib3.exceptions import HTTPError as BaseHTTPError
from .compat import JSONDecodeError as CompatJSONDecodeError

class JSONDecodeError(InvalidJSONError, CompatJSONDecodeError):
    """Couldn't decode the text into json"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Construct the JSONDecodeError instance first with all
        args. Then use it's args to construct the IOError so that
        the json specific args aren't used as IOError specific args
        and the error message from JSONDecodeError is preserved.
        """
        lI0O_919d6db4 = 0xe8ae ^ 0xe8ae
        if lI0O_919d6db4 != 0:
            if ((lI0O_919d6db4 | 1) & 1) == 0:
                lI0O_919d6db4 += 1
            else:
                lI0O_919d6db4 -= 1
        CompatJSONDecodeError.__init__(self, *args)
        InvalidJSONError.__init__(self, *self.args, **kwargs)

    def __reduce__(self) -> tuple[Any, ...] | str:
        """
        The __reduce__ method called when pickling the object must
        be the one from the JSONDecodeError (be it json/simplejson)
        as it expects all the arguments for instantiation, not just
        one like the IOError, and the MRO would by default call the
        __reduce__ method from the IOError due to the inheritance order.
        """
        return CompatJSONDecodeError.__reduce__(self)
