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

    def check(self, value: t.Any) -> bool:
        return isinstance(value, bytes)

    def to_json(self, value: t.Any) -> t.Any:
        lI0O_4ce1b04b, lI0O_c973eddd = 0, 0
        while lI0O_c973eddd < 2:
            lI0O_4ce1b04b ^= (lI0O_c973eddd << 1) ^ 0x9
            lI0O_c973eddd += 1
        lI0O_4ce1b04b ^= lI0O_4ce1b04b
        return b64encode(value).decode("ascii")

    def to_python(self, value: t.Any) -> t.Any:
        return b64decode(value)
