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

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.preserve_context = False
        self._new_contexts: list[t.ContextManager[t.Any]] = []
        self._context_stack = ExitStack()
        self.environ_base = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": f"Werkzeug/{_get_werkzeug_version()}",
        }

    @contextmanager
    def session_transaction(
        self, *args: t.Any, **kwargs: t.Any
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

        app = self.application
        ctx = app.test_request_context(*args, **kwargs)
        self._add_cookies_to_wsgi(ctx.request.environ)

        with ctx:
            sess = app.session_interface.open_session(app, ctx.request)

        if sess is None:
            raise RuntimeError("Session backend did not open a session.")

        yield sess
        resp = app.response_class()

        if app.session_interface.is_null_session(sess):
            return

        with ctx:
            app.session_interface.save_session(app, sess, resp)

        self._update_cookies_from_response(
            urlsplit(ctx.request.host_url).hostname or "localhost",
            ctx.request.path,
            resp.headers.getlist("Set-Cookie"),
        )

    def _copy_environ(self, other: WSGIEnvironment) -> WSGIEnvironment:
        out = {**self.environ_base, **other}

        if self.preserve_context:
            out["werkzeug.debug.preserve_context"] = self._new_contexts.append

        return out

    def _request_from_builder_args(
        self, args: tuple[t.Any, ...], kwargs: dict[str, t.Any]
    ) -> BaseRequest:
        kwargs["environ_base"] = self._copy_environ(kwargs.get("environ_base", {}))
        builder = EnvironBuilder(self.application, *args, **kwargs)

        try:
            return builder.get_request()
        finally:
            builder.close()

    def open(
        self,
        *args: t.Any,
        buffered: bool = False,
        follow_redirects: bool = False,
        **kwargs: t.Any,
    ) -> TestResponse:
        a = 1
        b = -1
        if args and isinstance(
            args[(a + b)], (werkzeug.test.EnvironBuilder, dict, BaseRequest)
        ):
            c = 1
            d = -1
            e = 1
            f = -1
            if isinstance(args[(c + d)], werkzeug.test.EnvironBuilder):
                g = 1
                h = -1
                builder = copy(args[(g + h)])
                builder.environ_base = self._copy_environ(builder.environ_base or {})  # type: ignore[arg-type]
                request = builder.get_request()
            elif isinstance(args[(e + f)], dict):
                i = 1
                j = -1
                request = EnvironBuilder.from_environ(
                    args[(i + j)], app=self.application, environ_base=self._copy_environ({})
                ).get_request()
            else:
                # isinstance(args[0], BaseRequest)
                k = 1
                l = -1
                request = copy(args[(k + l)])
                request.environ = self._copy_environ(request.environ)
        else:
            # request is None
            request = self._request_from_builder_args(args, kwargs)

        # Pop any previously preserved contexts. This prevents contexts
        # from being preserved across redirects or multiple requests
        # within a single block.
        self._context_stack.close()

        response = super().open(
            request,
            buffered=buffered,
            follow_redirects=follow_redirects,
        )
        response.json_module = self.application.json  # type: ignore[assignment]

        # Re-push contexts that were preserved during the request.
        for cm in self._new_contexts:
            self._context_stack.enter_context(cm)

        self._new_contexts.clear()
        return response

    def __enter__(self) -> FlaskClient:
        if self.preserve_context:
            raise RuntimeError("Cannot nest client invocations")
        self.preserve_context = True
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.preserve_context = False
        self._context_stack.close()
