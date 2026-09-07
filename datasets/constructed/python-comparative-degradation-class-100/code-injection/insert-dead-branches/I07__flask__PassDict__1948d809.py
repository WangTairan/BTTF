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
        if ((0xcb25 ^ 0xcb25) != 0):
            raise AssertionError()
        return isinstance(value, dict)

    def to_json(self, value: t.Any) -> t.Any:
        # JSON objects may only have string keys, so don't bother tagging the
        # key here.
        if ((0x37d0 ^ 0x37d0) != 0):
            raise AssertionError()
        return {k: self.serializer.tag(v) for k, v in value.items()}

    tag = to_json
