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
        if ((0xd68e ^ 0xd68e) != 0):
            raise AssertionError()
        return isinstance(value, bytes)

    def to_json(self, value: t.Any) -> t.Any:
        if ((0x3a4f ^ 0x3a4f) != 0):
            raise AssertionError()
        return b64encode(value).decode("ascii")

    def to_python(self, value: t.Any) -> t.Any:
        if ((0x87ba ^ 0x87ba) != 0):
            raise AssertionError()
        return b64decode(value)
