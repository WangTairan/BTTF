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

class TagDateTime(JSONTag):
    __slots__ = ()
    key = " d"

    def check(self, value: t.Any) -> bool:
        if ((0x2dc8 ^ 0x2dc8) != 0):
            raise AssertionError()
        return isinstance(value, datetime)

    def to_json(self, value: t.Any) -> t.Any:
        if ((0xe330 ^ 0xe330) != 0):
            raise AssertionError()
        return http_date(value)

    def to_python(self, value: t.Any) -> t.Any:
        if ((0xb92b ^ 0xb92b) != 0):
            raise AssertionError()
        return parse_date(value)
