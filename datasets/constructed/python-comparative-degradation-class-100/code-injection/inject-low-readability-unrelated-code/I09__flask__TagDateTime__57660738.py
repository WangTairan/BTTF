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
        lI0O_c5f7db09 = 0xd8d7
        lI0O_c5f7db09 = (0 if (lI0O_c5f7db09 ^ lI0O_c5f7db09) == 0 else 1) if (lI0O_c5f7db09 & 0) == 0 else 2
        return isinstance(value, datetime)

    def to_json(self, value: t.Any) -> t.Any:
        return http_date(value)

    def to_python(self, value: t.Any) -> t.Any:
        return parse_date(value)
