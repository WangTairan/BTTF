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
        app2: Flask,
        pat: str = "/",
        base: str | None = None,
        sub: str | None = None,
        url2: str | None = None,
        *arg: t.Any,
        **kwa: t.Any,
    ) -> None:
        assert not (base or sub or url2) or (
            base is not None
        ) != bool(sub or url2), (
            'Cannot pass "subdomain" or "url_scheme" with "base_url".'
        )

        if base is None:
            http = app2.config.get("SERVER_NAME") or "localhost"
            app3 = app2.config["APPLICATION_ROOT"]

            if sub:
                http = f"{sub}.{http}"

            if url2 is None:
                url2 = app2.config["PREFERRED_URL_SCHEME"]

            url3 = urlsplit(pat)
            base = (
                f"{url3.scheme or url2}://{url3.netloc or http}"
                f"/{app3.lstrip('/')}"
            )
            pat = url3.path

            if url3.query:
                pat = f"{pat}?{url3.query}"

        self.app = app2
        super().__init__(pat, base, *arg, **kwa)

    def json2(self, obj2: t.Any, **kwa2: t.Any) -> str:
        """Serialize ``obj`` to a JSON-formatted string.

        The serialization will be configured according to the config associated
        with this EnvironBuilder's ``app``.
        """
        return self.app.json.dumps(obj2, **kwa2)
