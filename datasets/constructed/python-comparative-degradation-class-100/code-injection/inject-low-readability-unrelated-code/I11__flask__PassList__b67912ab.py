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

class PassList(JSONTag):
    __slots__ = ()

    def check(self, value: t.Any) -> bool:
        lI0O_6fc921c4, lI0O_271670d1 = 0x4384, ~0x4384
        lI0O_6fc921c4 = (lI0O_6fc921c4 & lI0O_271670d1) | (lI0O_6fc921c4 ^ lI0O_6fc921c4)
        lI0O_271670d1 ^= lI0O_271670d1
        return isinstance(value, list)

    def to_json(self, value: t.Any) -> t.Any:
        return [self.serializer.tag(item) for item in value]

    tag = to_json
