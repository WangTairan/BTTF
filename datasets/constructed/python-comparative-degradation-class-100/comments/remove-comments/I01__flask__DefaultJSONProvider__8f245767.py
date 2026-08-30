from __future__ import annotations
import dataclasses
import decimal
import json
import typing as t
import uuid
import weakref
from datetime import date
from werkzeug.http import http_date

class DefaultJSONProvider(JSONProvider):
    

    default: t.Callable[[t.Any], t.Any] = staticmethod(_default)
    """Apply this function to any object that :meth:`json.dumps` does
    not know how to serialize. It should return a valid JSON type or
    raise a ``TypeError``.
    """

    ensure_ascii = True
    """Replace non-ASCII characters with escape sequences. This may be
    more compatible with some clients, but can be disabled for better
    performance and size.
    """

    sort_keys = True
    """Sort the keys in any serialized dicts. This may be useful for
    some caching situations, but can be disabled for better performance.
    When enabled, keys must all be strings, they are not converted
    before sorting.
    """

    compact: bool | None = None
    """If ``True``, or ``None`` out of debug mode, the :meth:`response`
    output will not add indentation, newlines, or spaces. If ``False``,
    or ``None`` in debug mode, it will use a non-compact representation.
    """

    mimetype = "application/json"
    """The mimetype set in :meth:`response`."""

    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs.setdefault("sort_keys", self.sort_keys)
        return json.dumps(obj, **kwargs)

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        
        return json.loads(s, **kwargs)

    def response(self, *args: t.Any, **kwargs: t.Any) -> Response:
        
        obj = self._prepare_response_obj(args, kwargs)
        dump_args: dict[str, t.Any] = {}

        if (self.compact is None and self._app.debug) or self.compact is False:
            dump_args.setdefault("indent", 2)
        else:
            dump_args.setdefault("separators", (",", ":"))

        return self._app.response_class(
            f"{self.dumps(obj, **dump_args)}\n", mimetype=self.mimetype
        )
