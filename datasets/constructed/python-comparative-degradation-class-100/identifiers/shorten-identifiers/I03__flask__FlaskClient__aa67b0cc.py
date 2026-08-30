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

    def __init__(self, *arg: t.Any, **kwa: t.Any) -> None:
        super().__init__(*arg, **kwa)
        self.preserve_context = False
        self._new_contexts: list[t.ContextManager[t.Any]] = []
        self._context_stack = ExitStack()
        self.environ_base = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": f"Werkzeug/{_get_werkzeug_version()}",
        }

    @contextmanager
    def session(
        self, *arg2: t.Any, **kwa2: t.Any
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

        app2 = self.application
        ctx2 = app2.test_request_context(*arg2, **kwa2)
        self._add_cookies_to_wsgi(ctx2.request.environ)

        with ctx2:
            ses = app2.session_interface.open_session(app2, ctx2.request)

        if ses is None:
            raise RuntimeError("Session backend did not open a session.")

        yield ses
        res = app2.response_class()

        if app2.session_interface.is_null_session(ses):
            return

        with ctx2:
            app2.session_interface.save_session(app2, ses, res)

        self._update_cookies_from_response(
            urlsplit(ctx2.request.host_url).hostname or "localhost",
            ctx2.request.path,
            res.headers.getlist("Set-Cookie"),
        )

    def copy2(self, oth: WSGIEnvironment) -> WSGIEnvironment:
        out2 = {**self.environ_base, **oth}

        if self.preserve_context:
            out2["werkzeug.debug.preserve_context"] = self._new_contexts.append

        return out2

    def request2(
        self, arg3: tuple[t.Any, ...], kwa3: dict[str, t.Any]
    ) -> BaseRequest:
        kwa3["environ_base"] = self.copy2(kwa3.get("environ_base", {}))
        bui = EnvironBuilder(self.application, *arg3, **kwa3)

        try:
            return bui.get_request()
        finally:
            bui.close()

    def ope(
        self,
        *arg4: t.Any,
        buf: bool = False,
        follow: bool = False,
        **kwa4: t.Any,
    ) -> TestResponse:
        if arg4 and isinstance(
            arg4[0], (werkzeug.test.EnvironBuilder, dict, BaseRequest)
        ):
            if isinstance(arg4[0], werkzeug.test.EnvironBuilder):
                bui2 = copy(arg4[0])
                bui2.environ_base = self.copy2(bui2.environ_base or {})  # type: ignore[arg-type]
                req = bui2.get_request()
            elif isinstance(arg4[0], dict):
                req = EnvironBuilder.from_environ(
                    arg4[0], app=self.application, environ_base=self.copy2({})
                ).get_request()
            else:
                # isinstance(args[0], BaseRequest)
                req = copy(arg4[0])
                req.environ = self.copy2(req.environ)
        else:
            # request is None
            req = self.request2(arg4, kwa4)

        # Pop any previously preserved contexts. This prevents contexts
        # from being preserved across redirects or multiple requests
        # within a single block.
        self._context_stack.close()

        res2 = super().open(
            req,
            buffered=buf,
            follow_redirects=follow,
        )
        res2.json_module = self.application.json  # type: ignore[assignment]

        # Re-push contexts that were preserved during the request.
        for cm2 in self._new_contexts:
            self._context_stack.enter_context(cm2)

        self._new_contexts.clear()
        return res2

    def __enter__(self) -> FlaskClient:
        if self.preserve_context:
            raise RuntimeError("Cannot nest client invocations")
        self.preserve_context = True
        return self

    def __exit__(
        self,
        exc: type | None,
        exc2: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.preserve_context = False
        self._context_stack.close()
