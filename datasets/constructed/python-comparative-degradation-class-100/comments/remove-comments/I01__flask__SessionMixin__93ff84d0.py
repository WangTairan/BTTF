from __future__ import annotations
import collections.abc as c
import hashlib
import typing as t
from collections.abc import MutableMapping
from datetime import datetime
from datetime import timezone
from itsdangerous import BadSignature
from itsdangerous import URLSafeTimedSerializer
from werkzeug.datastructures import CallbackDict
from .json.tag import TaggedJSONSerializer

class SessionMixin(MutableMapping[str, t.Any]):
    

    @property
    def permanent(self) -> bool:
        
        return self.get("_permanent", False)   

    @permanent.setter
    def permanent(self, value: bool) -> None:
        self["_permanent"] = bool(value)

     
     
     
    new = False

     
     
     
    modified = True

    accessed = False
    """Indicates if the session was accessed, even if it was not modified. This
    is set when the session object is accessed through the request context,
    including the global :data:`.session` proxy. A ``Vary: cookie`` header will
    be added if this is ``True``.

    .. versionchanged:: 3.1.3
        This is tracked by the request context.
    """
