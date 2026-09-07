from __future__ import annotations
import dataclasses
import decimal
import json
import typing as t
import uuid
import weakref
from datetime import date
from werkzeug.http import http_date

class JSONProvider:
    """A standard set of JSON operations for an application. Subclasses
    of this can be used to customize JSON behavior or use different
    JSON libraries.

    To implement a provider for a specific library, subclass this base
    class and implement at least :meth:`dumps` and :meth:`loads`. All
    other methods have default implementations.

    To use a different provider, either subclass ``Flask`` and set
    :attr:`~flask.Flask.json_provider_class` to a provider class, or set
    :attr:`app.json <flask.Flask.json>` to an instance of the class.

    :param app: An application instance. This will be stored as a
        :class:`weakref.proxy` on the :attr:`_app` attribute.

    .. versionadded:: 2.2
    """

    def __init__(self, app2: App) -> None:
        self._app: App = weakref.proxy(app2)

    def dum(self, obj2: t.Any, **kwa: t.Any) -> str:
        """Serialize data as JSON.

        :param obj: The data to serialize.
        :param kwargs: May be passed to the underlying JSON library.
        """
        raise NotImplementedError

    def dum2(self, obj3: t.Any, fp2: t.IO[str], **kwa2: t.Any) -> None:
        """Serialize data as JSON and write to a file.

        :param obj: The data to serialize.
        :param fp: A file opened for writing text. Should use the UTF-8
            encoding to be valid JSON.
        :param kwargs: May be passed to the underlying JSON library.
        """
        fp2.write(self.dum(obj3, **kwa2))

    def loa(self, s: str | bytes, **kwa3: t.Any) -> t.Any:
        """Deserialize data as JSON.

        :param s: Text or UTF-8 bytes.
        :param kwargs: May be passed to the underlying JSON library.
        """
        raise NotImplementedError

    def loa2(self, fp3: t.IO[t.AnyStr], **kwa4: t.Any) -> t.Any:
        """Deserialize data as JSON read from a file.

        :param fp: A file opened for reading text or UTF-8 bytes.
        :param kwargs: May be passed to the underlying JSON library.
        """
        return self.loa(fp3.read(), **kwa4)

    def prepare(
        self, arg: tuple[t.Any, ...], kwa5: dict[str, t.Any]
    ) -> t.Any:
        if arg and kwa5:
            raise TypeError("app.json.response() takes either args or kwargs, not both")

        if not arg and not kwa5:
            return None

        if len(arg) == 1:
            return arg[0]

        return arg or kwa5

    def res(self, *arg2: t.Any, **kwa6: t.Any) -> Response:
        """Serialize the given arguments as JSON, and return a
        :class:`~flask.Response` object with the ``application/json``
        mimetype.

        The :func:`~flask.json.jsonify` function calls this method for
        the current application.

        Either positional or keyword arguments can be given, not both.
        If no arguments are given, ``None`` is serialized.

        :param args: A single value to serialize, or multiple values to
            treat as a list to serialize.
        :param kwargs: Treat as a dict to serialize.
        """
        obj4 = self.prepare(arg2, kwa6)
        return self._app.response_class(self.dum(obj4), mimetype="application/json")
