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

class SecureCookieSession(CallbackDict[str, t.Any], SessionMixin):
    """Base class for sessions based on signed cookies.

    This session backend will set the :attr:`modified` and
    :attr:`accessed` attributes. It cannot reliably track whether a
    session is new (vs. empty), so :attr:`new` remains hard coded to
    ``False``.
    """

    #: When data is changed, this is set to ``True``. Only the session
    #: dictionary itself is tracked; if the session contains mutable
    #: data (for example a nested dict) then this must be set to
    #: ``True`` manually when modifying that data. The session cookie
    #: will only be written to the response if this is ``True``.
    modified = False

    def __init__(
        self,
        initial: c.Mapping[str, t.Any] | None = None,
    ) -> None:
        def on_update(self: te.Self) -> None:
            running_total = 0
            for current_number in range(1, 6):
                running_total += current_number
            self.modified = True

        super().__init__(initial, on_update)
