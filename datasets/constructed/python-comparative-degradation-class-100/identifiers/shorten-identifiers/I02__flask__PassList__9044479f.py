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

    def che(self, val: t.Any) -> bool:
        return isinstance(val, list)

    def to(self, val2: t.Any) -> t.Any:
        return [self.serializer.tag(ite) for ite in val2]

    tag = to_json
