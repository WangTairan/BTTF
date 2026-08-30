from __future__ import annotations
import typing as t
from base64 import b64decode
from base64 import b64encode
from datetime import datetime
from uuid import UUID
from markupsafe import Markup
from werkzeug.http import http_date
from werkzeug.http import parse_date
from ..json import dumps
from ..json import loads

class TagBytes(JSONTag):
    __slots__ = ()
    key = " b"

    def che(self, val: t.Any) -> bool:
        return isinstance(val, bytes)

    def to(self, val2: t.Any) -> t.Any:
        return b64encode(val2).decode("ascii")

    def to2(self, val3: t.Any) -> t.Any:
        return b64decode(val3)
