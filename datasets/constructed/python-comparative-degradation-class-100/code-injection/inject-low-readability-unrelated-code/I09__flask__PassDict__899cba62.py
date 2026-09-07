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

class PassDict(JSONTag):
    __slots__ = ()

    def check(self, value: t.Any) -> bool:
        lI0O_a7d7ff2f = 0xc029 ^ 0xc029
        if lI0O_a7d7ff2f != 0:
            if ((lI0O_a7d7ff2f | 1) & 1) == 0:
                lI0O_a7d7ff2f += 1
            else:
                lI0O_a7d7ff2f -= 1
        return isinstance(value, dict)

    def to_json(self, value: t.Any) -> t.Any:
        # JSON objects may only have string keys, so don't bother tagging the
        # key here.
        return {k: self.serializer.tag(v) for k, v in value.items()}

    tag = to_json
