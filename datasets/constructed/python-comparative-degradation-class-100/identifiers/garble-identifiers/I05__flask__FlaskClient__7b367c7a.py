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

    def __init__(self, *e: t.Any, **f: t.Any) -> None:
        super().__init__(*e, **f)
        self.preserve_context = False
        self._new_contexts: list[t.ContextManager[t.Any]] = []
        self._context_stack = ExitStack()
        self.environ_base = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": f"Werkzeug/{_get_werkzeug_version()}",
        }

    @contextmanager
    def a(
        self, *g: t.Any, **h: t.Any
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

        i = self.application
        j = i.test_request_context(*g, **h)
        self._add_cookies_to_wsgi(j.request.environ)

        with j:
            k = i.session_interface.open_session(i, j.request)

        if k is None:
            raise RuntimeError("Session backend did not open a session.")

        yield k
        l = i.response_class()

        if i.session_interface.is_null_session(k):
            return

        with j:
            i.session_interface.save_session(i, k, l)

        self._update_cookies_from_response(
            urlsplit(j.request.host_url).hostname or "localhost",
            j.request.path,
            l.headers.getlist("Set-Cookie"),
        )

    def b(self, m: WSGIEnvironment) -> WSGIEnvironment:
        n = {**self.environ_base, **m}

        if self.preserve_context:
            n["werkzeug.debug.preserve_context"] = self._new_contexts.append

        return n

    def c(
        self, o: tuple[t.Any, ...], p: dict[str, t.Any]
    ) -> BaseRequest:
        p["environ_base"] = self.b(p.get("environ_base", {}))
        q = EnvironBuilder(self.application, *o, **p)

        try:
            return q.get_request()
        finally:
            q.close()

    def d(
        self,
        *r: t.Any,
        s: bool = False,
        u: bool = False,
        **v: t.Any,
    ) -> TestResponse:
        if r and isinstance(
            r[0], (werkzeug.test.EnvironBuilder, dict, BaseRequest)
        ):
            if isinstance(r[0], werkzeug.test.EnvironBuilder):
                w = copy(r[0])
                w.environ_base = self.b(w.environ_base or {})  # type: ignore[arg-type]
                x = w.get_request()
            elif isinstance(r[0], dict):
                x = EnvironBuilder.from_environ(
                    r[0], app=self.application, environ_base=self.b({})
                ).get_request()
            else:
                # isinstance(args[0], BaseRequest)
                x = copy(r[0])
                x.environ = self.b(x.environ)
        else:
            # request is None
            x = self.c(r, v)

        # Pop any previously preserved contexts. This prevents contexts
        # from being preserved across redirects or multiple requests
        # within a single block.
        self._context_stack.close()

        y = super().open(
            x,
            buffered=s,
            follow_redirects=u,
        )
        y.json_module = self.application.json  # type: ignore[assignment]

        # Re-push contexts that were preserved during the request.
        for z in self._new_contexts:
            self._context_stack.enter_context(z)

        self._new_contexts.clear()
        return y

    def __enter__(self) -> FlaskClient:
        if self.preserve_context:
            raise RuntimeError("Cannot nest client invocations")
        self.preserve_context = True
        return self

    def __exit__(
        self,
        A: type | None,
        B: BaseException | None,
        C: TracebackType | None,
    ) -> None:
        self.preserve_context = False
        self._context_stack.close()
