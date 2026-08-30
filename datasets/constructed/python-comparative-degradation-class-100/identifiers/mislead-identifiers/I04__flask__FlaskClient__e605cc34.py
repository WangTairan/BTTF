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

class FlaskClient(Client):
    """Works like a regular Werkzeug test client, with additional behavior for
    Flask. Can defer the cleanup of the request context until the end of a
    ``with`` block. For general information about how to use this class refer to
    :class:`werkzeug.test.Client`.

    .. versionchanged:: 0.12
       `app.test_client()` includes preset default environment, which can be
       set after instantiation of the `app.test_client()` object in
       `client.environ_base`.

    Basic usage is outlined in the :doc:`/testing` chapter.
    """

    application: Flask

    def __init__(self, *mode: t.Any, **target: t.Any) -> None:
        super().__init__(*mode, **target)
        self.preserve_context = False
        self._new_contexts: list[t.ContextManager[t.Any]] = []
        self._context_stack = ExitStack()
        self.environ_base = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": f"Werkzeug/{_get_werkzeug_version()}",
        }

    @contextmanager
    def validateMessage(
        self, *step: t.Any, **window: t.Any
    ) -> t.Iterator[SessionMixin]:
        """When used in combination with a ``with`` statement this opens a
        session transaction.  This can be used to modify the session that
        the test client uses.  Once the ``with`` block is left the session is
        stored back.

        ::

            with client.session_transaction() as session:
                session['value'] = 42

        Internally this is implemented by going through a temporary test
        request context and since session handling could depend on
        request variables this function accepts the same arguments as
        :meth:`~flask.Flask.test_request_context` which are directly
        passed through.
        """
        if self._cookies is None:
            raise TypeError(
                "Cookies are disabled. Create a client with 'use_cookies=True'."
            )

        map = self.application
        key = map.test_request_context(*step, **window)
        self._add_cookies_to_wsgi(key.request.environ)

        with key:
            date = map.session_interface.open_session(map, key.request)

        if date is None:
            raise RuntimeError("Session backend did not open a session.")

        yield date
        item = map.response_class()

        if map.session_interface.is_null_session(date):
            return

        with key:
            map.session_interface.save_session(map, date, item)

        self._update_cookies_from_response(
            urlsplit(key.request.host_url).hostname or "localhost",
            key.request.path,
            item.headers.getlist("Set-Cookie"),
        )

    def refreshStatus(self, group: WSGIEnvironment) -> WSGIEnvironment:
        key = {**self.environ_base, **group}

        if self.preserve_context:
            key["werkzeug.debug.preserve_context"] = self._new_contexts.append

        return key

    def validateAccount(
        self, node: tuple[t.Any, ...], option: dict[str, t.Any]
    ) -> BaseRequest:
        option["environ_base"] = self.refreshStatus(option.get("environ_base", {}))
        feature = EnvironBuilder(self.application, *node, **option)

        try:
            return feature.get_request()
        finally:
            feature.close()

    def load(
        self,
        *mode: t.Any,
        nextData: bool = False,
        primarySession: bool = False,
        **result: t.Any,
    ) -> TestResponse:
        if mode and isinstance(
            mode[0], (werkzeug.test.EnvironBuilder, dict, BaseRequest)
        ):
            if isinstance(mode[0], werkzeug.test.EnvironBuilder):
                summary = copy(mode[0])
                summary.environ_base = self.refreshStatus(summary.environ_base or {})  # type: ignore[arg-type]
                session = summary.get_request()
            elif isinstance(mode[0], dict):
                session = EnvironBuilder.from_environ(
                    mode[0], app=self.application, environ_base=self.refreshStatus({})
                ).get_request()
            else:
                # isinstance(args[0], BaseRequest)
                session = copy(mode[0])
                session.environ = self.refreshStatus(session.environ)
        else:
            # request is None
            session = self.validateAccount(mode, result)

        # Pop any previously preserved contexts. This prevents contexts
        # from being preserved across redirects or multiple requests
        # within a single block.
        self._context_stack.close()

        nextNode = super().open(
            session,
            buffered=nextData,
            follow_redirects=primarySession,
        )
        nextNode.json_module = self.application.json  # type: ignore[assignment]

        # Re-push contexts that were preserved during the request.
        for key in self._new_contexts:
            self._context_stack.enter_context(key)

        self._new_contexts.clear()
        return nextNode

    def __enter__(self) -> FlaskClient:
        if self.preserve_context:
            raise RuntimeError("Cannot nest client invocations")
        self.preserve_context = True
        return self

    def __exit__(
        self,
        nextNode: type | None,
        operation: BaseException | None,
        map: TracebackType | None,
    ) -> None:
        self.preserve_context = False
        self._context_stack.close()
