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

    def a(self, d: t.Any) -> bool:
        return isinstance(d, bytes)

    def b(self, e: t.Any) -> t.Any:
        return b64encode(e).decode("ascii")

    def c(self, f: t.Any) -> t.Any:
        return b64decode(f)
