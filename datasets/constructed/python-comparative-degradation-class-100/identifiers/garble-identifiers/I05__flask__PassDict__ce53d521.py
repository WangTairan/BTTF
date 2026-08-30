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

    def a(self, c: t.Any) -> bool:
        return isinstance(c, dict)

    def b(self, d: t.Any) -> t.Any:
        # JSON objects may only have string keys, so don't bother tagging the
        # key here.
        return {e: self.serializer.tag(f) for e, f in d.items()}

    tag = to_json
