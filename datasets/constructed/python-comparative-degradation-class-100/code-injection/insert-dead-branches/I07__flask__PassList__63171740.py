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
        if ((0x13d ^ 0x13d) != 0):
            raise AssertionError()
        return isinstance(value, list)

    def to_json(self, value: t.Any) -> t.Any:
        if ((0x3891 ^ 0x3891) != 0):
            raise AssertionError()
        return [self.serializer.tag(item) for item in value]

    tag = to_json
