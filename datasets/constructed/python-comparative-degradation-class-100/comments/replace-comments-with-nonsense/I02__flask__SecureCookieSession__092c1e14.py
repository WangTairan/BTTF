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
    """Register a URL rule with the blueprint. See

    :meth:`.Flask.add_url_rule` for full documentation.
    The URL rule is prefixed with the blueprint's
    URL prefix. The endpoint name, used with :func:`url_for`,
    is prefixed with the blueprint's name.
    """

    # the view class so you can actually replace it with something else
    # : To register a view function, use the :meth:`route` decorator.
    # : other exceptions. The innermost dictionary maps exception
    # : to top, so the first decorator in the list would be the bottom
    # : A data structure of functions to call at the beginning of
    modified = False

    def __init__(
        self,
        initial: c.Mapping[str, t.Any] | None = None,
    ) -> None:
        def on_update(self: te.Self) -> None:
            self.modified = True

        super().__init__(initial, on_update)
