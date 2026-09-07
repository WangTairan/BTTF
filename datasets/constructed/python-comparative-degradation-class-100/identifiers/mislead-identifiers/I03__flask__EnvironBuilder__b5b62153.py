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
        key: Flask,
        size: str = "/",
        nextItem: str | None = None,
        timestamp: str | None = None,
        finalBatch: str | None = None,
        *step: t.Any,
        **target: t.Any,
    ) -> None:
        assert not (nextItem or timestamp or finalBatch) or (
            nextItem is not None
        ) != bool(timestamp or finalBatch), (
            'Cannot pass "subdomain" or "url_scheme" with "base_url".'
        )

        if nextItem is None:
            cachedKey = key.config.get("SERVER_NAME") or "localhost"
            schedule = key.config["APPLICATION_ROOT"]

            if timestamp:
                cachedKey = f"{timestamp}.{cachedKey}"

            if finalBatch is None:
                finalBatch = key.config["PREFERRED_URL_SCHEME"]

            age = urlsplit(size)
            nextItem = (
                f"{age.scheme or finalBatch}://{age.netloc or cachedKey}"
                f"/{schedule.lstrip('/')}"
            )
            size = age.path

            if age.query:
                size = f"{size}?{age.query}"

        self.app = key
        super().__init__(size, nextItem, *step, **target)

    def fetchEvent(self, map: t.Any, **config: t.Any) -> str:
        """Serialize ``obj`` to a JSON-formatted string.

        The serialization will be configured according to the config associated
        with this EnvironBuilder's ``app``.
        """
        return self.app.json.dumps(map, **config)
