from __future__ import annotations
import importlib.metadata
import typing as t
from contextlib import contextmanager
from contextlib import ExitStack
from copy import copy
from types import TracebackType
from urllib.parse import urlsplit
import werkzeug.test
from click.testing import CliRunner
from click.testing import Result
from werkzeug.test import Client
from werkzeug.wrappers import Request as BaseRequest
from .cli import ScriptInfo
from .sessions import SessionMixin

class EnvironBuilder(werkzeug.test.EnvironBuilder):
    """An :class:`~werkzeug.test.EnvironBuilder`, that takes defaults from the
    application.

    :param app: The Flask application to configure the environment from.
    :param path: URL path being requested.
    :param base_url: Base URL where the app is being served, which
        ``path`` is relative to. If not given, built from
        :data:`PREFERRED_URL_SCHEME`, ``subdomain``,
        :data:`SERVER_NAME`, and :data:`APPLICATION_ROOT`.
    :param subdomain: Subdomain name to append to :data:`SERVER_NAME`.
    :param url_scheme: Scheme to use instead of
        :data:`PREFERRED_URL_SCHEME`.
    :param json: If given, this is serialized as JSON and passed as
        ``data``. Also defaults ``content_type`` to
        ``application/json``.
    :param args: other positional arguments passed to
        :class:`~werkzeug.test.EnvironBuilder`.
    :param kwargs: other keyword arguments passed to
        :class:`~werkzeug.test.EnvironBuilder`.
    """

    def __init__(
        self,
        b: Flask,
        c: str = "/",
        d: str | None = None,
        e: str | None = None,
        f: str | None = None,
        *g: t.Any,
        **h: t.Any,
    ) -> None:
        assert not (d or e or f) or (
            d is not None
        ) != bool(e or f), (
            'Cannot pass "subdomain" or "url_scheme" with "base_url".'
        )

        if d is None:
            i = b.config.get("SERVER_NAME") or "localhost"
            j = b.config["APPLICATION_ROOT"]

            if e:
                i = f"{e}.{i}"

            if f is None:
                f = b.config["PREFERRED_URL_SCHEME"]

            k = urlsplit(c)
            d = (
                f"{k.scheme or f}://{k.netloc or i}"
                f"/{j.lstrip('/')}"
            )
            c = k.path

            if k.query:
                c = f"{c}?{k.query}"

        self.app = b
        super().__init__(c, d, *g, **h)

    def a(self, l: t.Any, **m: t.Any) -> str:
        """Serialize ``obj`` to a JSON-formatted string.

        The serialization will be configured according to the config associated
        with this EnvironBuilder's ``app``.
        """
        return self.app.json.dumps(l, **m)
