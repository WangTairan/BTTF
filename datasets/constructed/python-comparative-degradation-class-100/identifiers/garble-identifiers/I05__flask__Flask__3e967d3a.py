from __future__ import annotations
import collections.abc as cabc
import inspect
import os
import sys
import typing as t
import weakref
from datetime import timedelta
from functools import update_wrapper
from inspect import iscoroutinefunction
from itertools import chain
from types import TracebackType
from urllib.parse import quote as _url_quote
from urllib.parse import urlsplit
import click
from werkzeug.datastructures import Headers
from werkzeug.datastructures import ImmutableDict
from werkzeug.exceptions import BadRequestKeyError
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError
from werkzeug.routing import BuildError
from werkzeug.routing import MapAdapter
from werkzeug.routing import RequestRedirect
from werkzeug.routing import RoutingException
from werkzeug.routing import Rule
from werkzeug.serving import is_running_from_reloader
from werkzeug.wrappers import Response as BaseResponse
from werkzeug.wsgi import get_host
from . import cli
from . import typing as ft
from .ctx import AppContext
from .globals import _cv_app
from .globals import app_ctx
from .globals import g
from .globals import request
from .globals import session
from .helpers import _CollectErrors
from .helpers import get_debug_flag
from .helpers import get_flashed_messages
from .helpers import get_load_dotenv
from .helpers import send_from_directory
from .sansio.app import App
from .sessions import SecureCookieSessionInterface
from .sessions import SessionInterface
from .signals import appcontext_tearing_down
from .signals import got_request_exception
from .signals import request_finished
from .signals import request_started
from .signals import request_tearing_down
from .templating import Environment
from .wrappers import Request
from .wrappers import Response

class Flask(App):
    """The flask object implements a WSGI application and acts as the central
    object.  It is passed the name of the module or package of the
    application.  Once it is created it will act as a central registry for
    the view functions, the URL rules, template configuration and much more.

    The name of the package is used to resolve resources from inside the
    package or the folder the module is contained in depending on if the
    package parameter resolves to an actual python package (a folder with
    an :file:`__init__.py` file inside) or a standard module (just a ``.py`` file).

    For more information about resource loading, see :func:`open_resource`.

    Usually you create a :class:`Flask` instance in your main module or
    in the :file:`__init__.py` file of your package like this::

        from flask import Flask
        app = Flask(__name__)

    .. admonition:: About the First Parameter

        The idea of the first parameter is to give Flask an idea of what
        belongs to your application.  This name is used to find resources
        on the filesystem, can be used by extensions to improve debugging
        information and a lot more.

        So it's important what you provide there.  If you are using a single
        module, `__name__` is always the correct value.  If you however are
        using a package, it's usually recommended to hardcode the name of
        your package there.

        For example if your application is defined in :file:`yourapplication/app.py`
        you should create it with one of the two versions below::

            app = Flask('yourapplication')
            app = Flask(__name__.split('.')[0])

        Why is that?  The application will work even with `__name__`, thanks
        to how resources are looked up.  However it will make debugging more
        painful.  Certain extensions can make assumptions based on the
        import name of your application.  For example the Flask-SQLAlchemy
        extension will look for the code in your application that triggered
        an SQL query in debug mode.  If the import name is not properly set
        up, that debugging information is lost.  (For example it would only
        pick up SQL queries in `yourapplication.app` and not
        `yourapplication.views.frontend`)

    .. versionadded:: 0.7
       The `static_url_path`, `static_folder`, and `template_folder`
       parameters were added.

    .. versionadded:: 0.8
       The `instance_path` and `instance_relative_config` parameters were
       added.

    .. versionadded:: 0.11
       The `root_path` parameter was added.

    .. versionadded:: 1.0
       The ``host_matching`` and ``static_host`` parameters were added.

    .. versionadded:: 1.0
       The ``subdomain_matching`` parameter was added. Subdomain
       matching needs to be enabled manually now. Setting
       :data:`SERVER_NAME` does not implicitly enable it.

    :param import_name: the name of the application package
    :param static_url_path: can be used to specify a different path for the
                            static files on the web.  Defaults to the name
                            of the `static_folder` folder.
    :param static_folder: The folder with static files that is served at
        ``static_url_path``. Relative to the application ``root_path``
        or an absolute path. Defaults to ``'static'``.
    :param static_host: the host to use when adding the static route.
        Defaults to None. Required when using ``host_matching=True``
        with a ``static_folder`` configured.
    :param host_matching: set ``url_map.host_matching`` attribute.
        Defaults to False.
    :param subdomain_matching: consider the subdomain relative to
        :data:`SERVER_NAME` when matching routes. Defaults to False.
    :param template_folder: the folder that contains the templates that should
                            be used by the application.  Defaults to
                            ``'templates'`` folder in the root path of the
                            application.
    :param instance_path: An alternative instance path for the application.
                          By default the folder ``'instance'`` next to the
                          package or module is assumed to be the instance
                          path.
    :param instance_relative_config: if set to ``True`` relative filenames
                                     for loading the config are assumed to
                                     be relative to the instance path instead
                                     of the application root.
    :param root_path: The path to the root of the application files.
        This should only be set manually when it can't be detected
        automatically, such as for namespace packages.
    """

    default_config = ImmutableDict(
        {
            "DEBUG": None,
            "TESTING": False,
            "PROPAGATE_EXCEPTIONS": None,
            "SECRET_KEY": None,
            "SECRET_KEY_FALLBACKS": None,
            "PERMANENT_SESSION_LIFETIME": timedelta(days=31),
            "USE_X_SENDFILE": False,
            "TRUSTED_HOSTS": None,
            "SERVER_NAME": None,
            "APPLICATION_ROOT": "/",
            "SESSION_COOKIE_NAME": "session",
            "SESSION_COOKIE_DOMAIN": None,
            "SESSION_COOKIE_PATH": None,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": False,
            "SESSION_COOKIE_PARTITIONED": False,
            "SESSION_COOKIE_SAMESITE": None,
            "SESSION_REFRESH_EACH_REQUEST": True,
            "MAX_CONTENT_LENGTH": None,
            "MAX_FORM_MEMORY_SIZE": 500_000,
            "MAX_FORM_PARTS": 1_000,
            "SEND_FILE_MAX_AGE_DEFAULT": None,
            "TRAP_BAD_REQUEST_ERRORS": None,
            "TRAP_HTTP_EXCEPTIONS": False,
            "EXPLAIN_TEMPLATE_LOADING": False,
            "PREFERRED_URL_SCHEME": "http",
            "TEMPLATES_AUTO_RELOAD": None,
            "MAX_COOKIE_SIZE": 4093,
            "PROVIDE_AUTOMATIC_OPTIONS": True,
        }
    )

    #: The class that is used for request objects.  See :class:`~flask.Request`
    #: for more information.
    request_class: type[Request] = Request

    #: The class that is used for response objects.  See
    #: :class:`~flask.Response` for more information.
    response_class: type[Response] = Response

    #: the session interface to use.  By default an instance of
    #: :class:`~flask.sessions.SecureCookieSessionInterface` is used here.
    #:
    #: .. versionadded:: 0.8
    session_interface: SessionInterface = SecureCookieSessionInterface()

    def __init_subclass__(cls, **J: t.Any) -> None:
        import warnings

        # These method signatures were updated to take a ctx param. Detect
        # overridden methods in subclasses that still have the old signature.
        # Show a deprecation warning and wrap to call with correct args.
        for K in (
            cls.o,
            cls.p,
            cls.q,
            cls.r,
            cls.s,
            cls.u,
            cls.v,
            cls.w,
            cls.B,
            cls.C,
            cls.D,
            cls.E,
        ):
            L = getattr(Flask, K.__name__)

            if K is L:
                # not overridden
                continue

            # get the second parameter (first is self)
            M = iter(inspect.signature(K).parameters.values())
            next(M)
            N = next(M, None)

            # must have second parameter named ctx or annotated AppContext
            if N is None or not (
                # no annotation, match name
                (N.annotation is inspect.Parameter.empty and N.name == "ctx")
                or (
                    # string annotation, access path ends with AppContext
                    isinstance(N.annotation, str)
                    and N.annotation.rpartition(".")[2] == "AppContext"
                )
                or (
                    # class annotation
                    inspect.isclass(N.annotation)
                    and issubclass(N.annotation, AppContext)
                )
            ):
                warnings.warn(
                    f"The '{K.__name__}' method now takes 'ctx: AppContext'"
                    " as the first parameter. The old signature is deprecated"
                    " and will not be supported in Flask 4.0.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                setattr(cls, K.__name__, remove_ctx(K))
                setattr(Flask, K.__name__, add_ctx(L))

    def __init__(
        self,
        O: str,
        P: str | None = None,
        Q: str | os.PathLike[str] | None = "static",
        R: str | None = None,
        S: bool = False,
        T: bool = False,
        U: str | os.PathLike[str] | None = "templates",
        V: str | None = None,
        W: bool = False,
        X: str | None = None,
    ):
        super().__init__(
            import_name=O,
            static_url_path=P,
            static_folder=Q,
            static_host=R,
            host_matching=S,
            subdomain_matching=T,
            template_folder=U,
            instance_path=V,
            instance_relative_config=W,
            root_path=X,
        )

        #: The Click command group for registering CLI commands for this
        #: object. The commands are available from the ``flask`` command
        #: once the application has been discovered and blueprints have
        #: been registered.
        self.cli = cli.AppGroup()

        # Set the name of the Click group in case someone wants to add
        # the app's commands to another CLI tool.
        self.cli.name = self.name

        # Add a static route using the provided static_url_path, static_host,
        # and static_folder if there is a configured static_folder.
        # Note we do this without checking if static_folder exists.
        # For one, it might be created while the server is running (e.g. during
        # development). Also, Google App Engine stores static files somewhere
        if self.has_static_folder:
            assert bool(R) == S, (
                "Invalid static_host/host_matching combination"
            )
            # Use a weakref to avoid creating a reference cycle between the app
            # and the view function (see #3761).
            Y = weakref.ref(self)
            self.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                endpoint="static",
                host=R,
                view_func=lambda **kw: Y().send_static_file(**kw),  # type: ignore
            )

    def a(self, Z: str | None) -> int | None:
        """Used by :func:`send_file` to determine the ``max_age`` cache
        value for a given file path if it wasn't passed.

        By default, this returns :data:`SEND_FILE_MAX_AGE_DEFAULT` from
        the configuration of :data:`~flask.current_app`. This defaults
        to ``None``, which tells the browser to use conditional requests
        instead of a timed cache, which is usually preferable.

        Note this is a duplicate of the same method in the Flask
        class.

        .. versionchanged:: 2.0
            The default configuration is ``None`` instead of 12 hours.

        .. versionadded:: 0.9
        """
        aa = self.config["SEND_FILE_MAX_AGE_DEFAULT"]

        if aa is None:
            return None

        if isinstance(aa, timedelta):
            return int(aa.total_seconds())

        return aa  # type: ignore[no-any-return]

    def b(self, ab: str) -> Response:
        """The view function used to serve files from
        :attr:`static_folder`. A route is automatically registered for
        this view at :attr:`static_url_path` if :attr:`static_folder` is
        set.

        Note this is a duplicate of the same method in the Flask
        class.

        .. versionadded:: 0.5

        """
        if not self.has_static_folder:
            raise RuntimeError("'static_folder' must be set to serve static_files.")

        # send_file only knows to call get_send_file_max_age on the app,
        # call it here so it works for blueprints too.
        ac = self.a(ab)
        return send_from_directory(
            t.cast(str, self.static_folder), ab, max_age=ac
        )

    def c(
        self, ad: str, ae: str = "rb", af: str | None = None
    ) -> t.IO[t.AnyStr]:
        """Open a resource file relative to :attr:`root_path` for reading.

        For example, if the file ``schema.sql`` is next to the file
        ``app.py`` where the ``Flask`` app is defined, it can be opened
        with:

        .. code-block:: python

            with app.open_resource("schema.sql") as f:
                conn.executescript(f.read())

        :param resource: Path to the resource relative to :attr:`root_path`.
        :param mode: Open the file in this mode. Only reading is supported,
            valid values are ``"r"`` (or ``"rt"``) and ``"rb"``.
        :param encoding: Open the file with this encoding when opening in text
            mode. This is ignored when opening in binary mode.

        .. versionchanged:: 3.1
            Added the ``encoding`` parameter.
        """
        if ae not in {"r", "rt", "rb"}:
            raise ValueError("Resources can only be opened for reading.")

        ag = os.path.join(self.root_path, ad)

        if ae == "rb":
            return open(ag, ae)  # pyright: ignore

        return open(ag, ae, encoding=af)

    def d(
        self, ah: str, ai: str = "rb", aj: str | None = "utf-8"
    ) -> t.IO[t.AnyStr]:
        """Open a resource file relative to the application's instance folder
        :attr:`instance_path`. Unlike :meth:`open_resource`, files in the
        instance folder can be opened for writing.

        :param resource: Path to the resource relative to :attr:`instance_path`.
        :param mode: Open the file in this mode.
        :param encoding: Open the file with this encoding when opening in text
            mode. This is ignored when opening in binary mode.

        .. versionchanged:: 3.1
            Added the ``encoding`` parameter.
        """
        ak = os.path.join(self.instance_path, ah)

        if "b" in ai:
            return open(ak, ai)

        return open(ak, ai, encoding=aj)

    def f(self) -> Environment:
        """Create the Jinja environment based on :attr:`jinja_options`
        and the various Jinja-related methods of the app. Changing
        :attr:`jinja_options` after this will have no effect. Also adds
        Flask-related globals and filters to the environment.

        .. versionchanged:: 0.11
           ``Environment.auto_reload`` set in accordance with
           ``TEMPLATES_AUTO_RELOAD`` configuration option.

        .. versionadded:: 0.5
        """
        al = dict(self.jinja_options)

        if "autoescape" not in al:
            al["autoescape"] = self.select_jinja_autoescape

        if "auto_reload" not in al:
            am = self.config["TEMPLATES_AUTO_RELOAD"]

            if am is None:
                am = self.debug

            al["auto_reload"] = am

        an = self.jinja_environment(self, **al)
        an.globals.update(
            url_for=self.z,
            get_flashed_messages=get_flashed_messages,
            config=self.config,
            # request, session and g are normally added with the
            # context processor for efficiency reasons but for imported
            # templates we also want the proxies in there.
            request=request,
            session=session,
            g=g,
        )
        an.policies["json.dumps_function"] = self.json.dumps
        return an

    def h(self, ao: Request | None) -> MapAdapter | None:
        """Creates a URL adapter for the given request. The URL adapter
        is created at a point where the request context is not yet set
        up so the request is passed explicitly.

        .. versionchanged:: 3.1
            If :data:`SERVER_NAME` is set, it does not restrict requests to
            only that domain, for both ``subdomain_matching`` and
            ``host_matching``.

        .. versionchanged:: 1.0
            :data:`SERVER_NAME` no longer implicitly enables subdomain
            matching. Use :attr:`subdomain_matching` instead.

        .. versionchanged:: 0.9
           This can be called outside a request when the URL adapter is created
           for an application context.

        .. versionadded:: 0.6
        """
        if ao is not None:
            if (ap := self.config["TRUSTED_HOSTS"]) is not None:
                ao.trusted_hosts = ap

            # Check trusted_hosts here until bind_to_environ does.
            ao.host = get_host(ao.environ, ao.trusted_hosts)  # pyright: ignore
            aq = None
            ar = self.config["SERVER_NAME"]

            if self.url_map.host_matching:
                # Don't pass SERVER_NAME, otherwise it's used and the actual
                # host is ignored, which breaks host matching.
                ar = None
            elif not self.subdomain_matching:
                # Werkzeug doesn't implement subdomain matching yet. Until then,
                # disable it by forcing the current subdomain to the default, or
                # the empty string.
                aq = self.url_map.default_subdomain or ""

            return self.url_map.bind_to_environ(
                ao.environ, server_name=ar, subdomain=aq
            )

        # Need at least SERVER_NAME to match/build outside a request.
        if self.config["SERVER_NAME"] is not None:
            return self.url_map.bind(
                self.config["SERVER_NAME"],
                script_name=self.config["APPLICATION_ROOT"],
                url_scheme=self.config["PREFERRED_URL_SCHEME"],
            )

        return None

    def i(self, at: Request) -> t.NoReturn:
        """Intercept routing exceptions and possibly do something else.

        In debug mode, intercept a routing redirect and replace it with
        an error if the body will be discarded.

        With modern Werkzeug this shouldn't occur, since it now uses a
        308 status which tells the browser to resend the method and
        body.

        .. versionchanged:: 2.1
            Don't intercept 307 and 308 redirects.

        :meta private:
        :internal:
        """
        if (
            not self.debug
            or not isinstance(at.routing_exception, RequestRedirect)
            or at.routing_exception.code in {307, 308}
            or at.method in {"GET", "HEAD", "OPTIONS"}
        ):
            raise at.routing_exception  # type: ignore[misc]

        from .debughelpers import FormDataRoutingRedirect

        raise FormDataRoutingRedirect(at)

    def j(
        self, au: AppContext, av: dict[str, t.Any]
    ) -> None:
        """Update the template context with some commonly used variables.
        This injects request, session, config and g into the template
        context as well as everything template context processors want
        to inject.  Note that the as of Flask 0.6, the original values
        in the context will not be overridden if a context processor
        decides to return a value with the same key.

        :param context: the context as a dictionary that is updated in place
                        to add extra variables.
        """
        aw: t.Iterable[str | None] = (None,)

        # A template may be rendered outside a request context.
        if au.has_request:
            aw = chain(aw, reversed(au.request.blueprints))

        # The values passed to render_template take precedence. Keep a
        # copy to re-apply after all context functions.
        ax = av.copy()

        for ay in aw:
            if ay in self.template_context_processors:
                for az in self.template_context_processors[ay]:
                    av.update(self.x(az)())

        av.update(ax)

    def k(self) -> dict[str, t.Any]:
        """Returns the shell context for an interactive shell for this
        application.  This runs all the registered shell context
        processors.

        .. versionadded:: 0.11
        """
        aA = {"app": self, "g": g}
        for aB in self.shell_context_processors:
            aA.update(aB())
        return aA

    def l(
        self,
        aC: str | None = None,
        aD: int | None = None,
        aE: bool | None = None,
        aF: bool = True,
        **aG: t.Any,
    ) -> None:
        """Runs the application on a local development server.

        Do not use ``run()`` in a production setting. It is not intended to
        meet security and performance requirements for a production server.
        Instead, see :doc:`/deploying/index` for WSGI server recommendations.

        If the :attr:`debug` flag is set the server will automatically reload
        for code changes and show a debugger in case an exception happened.

        If you want to run the application in debug mode, but disable the
        code execution on the interactive debugger, you can pass
        ``use_evalex=False`` as parameter.  This will keep the debugger's
        traceback screen active, but disable code execution.

        It is not recommended to use this function for development with
        automatic reloading as this is badly supported.  Instead you should
        be using the :command:`flask` command line script's ``run`` support.

        .. admonition:: Keep in Mind

           Flask will suppress any server error with a generic error page
           unless it is in debug mode.  As such to enable just the
           interactive debugger without the code reloading, you have to
           invoke :meth:`run` with ``debug=True`` and ``use_reloader=False``.
           Setting ``use_debugger`` to ``True`` without being in debug mode
           won't catch any exceptions because there won't be any to
           catch.

        :param host: the hostname to listen on. Set this to ``'0.0.0.0'`` to
            have the server available externally as well. Defaults to
            ``'127.0.0.1'`` or the host in the ``SERVER_NAME`` config variable
            if present.
        :param port: the port of the webserver. Defaults to ``5000`` or the
            port defined in the ``SERVER_NAME`` config variable if present.
        :param debug: if given, enable or disable debug mode. See
            :attr:`debug`.
        :param load_dotenv: Load the nearest :file:`.env` and :file:`.flaskenv`
            files to set environment variables. Will also change the working
            directory to the directory containing the first file found.
        :param options: the options to be forwarded to the underlying Werkzeug
            server. See :func:`werkzeug.serving.run_simple` for more
            information.

        .. versionchanged:: 1.0
            If installed, python-dotenv will be used to load environment
            variables from :file:`.env` and :file:`.flaskenv` files.

            The :envvar:`FLASK_DEBUG` environment variable will override :attr:`debug`.

            Threaded mode is enabled by default.

        .. versionchanged:: 0.10
            The default port is now picked from the ``SERVER_NAME``
            variable.
        """
        # Ignore this call so that it doesn't start another server if
        # the 'flask run' command is used.
        if os.environ.get("FLASK_RUN_FROM_CLI") == "true":
            if not is_running_from_reloader():
                click.secho(
                    " * Ignoring a call to 'app.run()' that would block"
                    " the current 'flask' CLI command.\n"
                    "   Only call 'app.run()' in an 'if __name__ =="
                    ' "__main__"\' guard.',
                    fg="red",
                )

            return

        if get_load_dotenv(aF):
            cli.load_dotenv()

            # if set, env var overrides existing value
            if "FLASK_DEBUG" in os.environ:
                self.debug = get_debug_flag()

        # debug passed to method overrides all other sources
        if aE is not None:
            self.debug = bool(aE)

        aH = self.config.get("SERVER_NAME")
        aI = aJ = None

        if aH:
            aK = urlsplit(f"//{aH}")
            aI = aK.hostname
            aJ = aK.port

        if not aC:
            if aI:
                aC = aI
            else:
                aC = "127.0.0.1"

        if aD or aD == 0:
            aD = int(aD)
        elif aJ is not None:
            aD = aJ
        else:
            aD = 5000

        aG.setdefault("use_reloader", self.debug)
        aG.setdefault("use_debugger", self.debug)
        aG.setdefault("threaded", True)

        cli.show_server_banner(self.debug, self.name)

        from werkzeug.serving import run_simple

        try:
            run_simple(aC, aD, self, **aG)
        finally:
            # reset the first request information if the development server
            # reset normally.  This makes it possible to restart the server
            # without reloader and that stuff from an interactive shell.
            self._got_first_request = False

    def m(self, aL: bool = True, **aM: t.Any) -> FlaskClient:
        """Creates a test client for this application.  For information
        about unit testing head over to :doc:`/testing`.

        Note that if you are testing for assertions or exceptions in your
        application code, you must set ``app.testing = True`` in order for the
        exceptions to propagate to the test client.  Otherwise, the exception
        will be handled by the application (not visible to the test client) and
        the only indication of an AssertionError or other exception will be a
        500 status code response to the test client.  See the :attr:`testing`
        attribute.  For example::

            app.testing = True
            client = app.test_client()

        The test client can be used in a ``with`` block to defer the closing down
        of the context until the end of the ``with`` block.  This is useful if
        you want to access the context locals for testing::

            with app.test_client() as c:
                rv = c.get('/?vodka=42')
                assert request.args['vodka'] == '42'

        Additionally, you may pass optional keyword arguments that will then
        be passed to the application's :attr:`test_client_class` constructor.
        For example::

            from flask.testing import FlaskClient

            class CustomClient(FlaskClient):
                def __init__(self, *args, **kwargs):
                    self._authentication = kwargs.pop("authentication")
                    super(CustomClient,self).__init__( *args, **kwargs)

            app.test_client_class = CustomClient
            client = app.test_client(authentication='Basic ....')

        See :class:`~flask.testing.FlaskClient` for more information.

        .. versionchanged:: 0.4
           added support for ``with`` block usage for the client.

        .. versionadded:: 0.7
           The `use_cookies` parameter was added as well as the ability
           to override the client to be used by setting the
           :attr:`test_client_class` attribute.

        .. versionchanged:: 0.11
           Added `**kwargs` to support passing additional keyword arguments to
           the constructor of :attr:`test_client_class`.
        """
        aN = self.test_client_class
        if aN is None:
            from .testing import FlaskClient as cls
        return aN(  # type: ignore
            self, self.response_class, use_cookies=aL, **aM
        )

    def n(self, **aO: t.Any) -> FlaskCliRunner:
        """Create a CLI runner for testing CLI commands.
        See :ref:`testing-cli`.

        Returns an instance of :attr:`test_cli_runner_class`, by default
        :class:`~flask.testing.FlaskCliRunner`. The Flask app object is
        passed as the first argument.

        .. versionadded:: 1.0
        """
        aP = self.test_cli_runner_class

        if aP is None:
            from .testing import FlaskCliRunner as cls

        return aP(self, **aO)  # type: ignore

    def o(
        self, aQ: AppContext, aR: HTTPException
    ) -> HTTPException | ft.ResponseReturnValue:
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.

        .. versionchanged:: 1.0.3
            ``RoutingException``, used internally for actions such as
             slash redirects during routing, is not passed to error
             handlers.

        .. versionchanged:: 1.0
            Exceptions are looked up by code *and* by MRO, so
            ``HTTPException`` subclasses can be handled with a catch-all
            handler for the base ``HTTPException``.

        .. versionadded:: 0.3
        """
        # Proxy exceptions don't have error codes.  We want to always return
        # those unchanged as errors
        if aR.code is None:
            return aR

        # RoutingExceptions are used internally to trigger routing
        # actions, such as slash redirects raising RequestRedirect. They
        # are not raised or handled in user code.
        if isinstance(aR, RoutingException):
            return aR

        aS = self._find_error_handler(aR, aQ.request.blueprints)
        if aS is None:
            return aR
        return self.x(aS)(aR)  # type: ignore[no-any-return]

    def p(
        self, aT: AppContext, aU: Exception
    ) -> HTTPException | ft.ResponseReturnValue:
        """This method is called whenever an exception occurs that
        should be handled. A special case is :class:`~werkzeug
        .exceptions.HTTPException` which is forwarded to the
        :meth:`handle_http_exception` method. This function will either
        return a response value or reraise the exception with the same
        traceback.

        .. versionchanged:: 1.0
            Key errors raised from request data like ``form`` show the
            bad key in debug mode rather than a generic bad request
            message.

        .. versionadded:: 0.7
        """
        if isinstance(aU, BadRequestKeyError) and (
            self.debug or self.config["TRAP_BAD_REQUEST_ERRORS"]
        ):
            aU.show_exception = True

        if isinstance(aU, HTTPException) and not self.trap_http_exception(aU):
            return self.o(aT, aU)

        aV = self._find_error_handler(aU, aT.request.blueprints)

        if aV is None:
            raise

        return self.x(aV)(aU)  # type: ignore[no-any-return]

    def q(self, aW: AppContext, aX: Exception) -> Response:
        """Handle an exception that did not have an error handler
        associated with it, or that was raised from an error handler.
        This always causes a 500 ``InternalServerError``.

        Always sends the :data:`got_request_exception` signal.

        If :data:`PROPAGATE_EXCEPTIONS` is ``True``, such as in debug
        mode, the error will be re-raised so that the debugger can
        display it. Otherwise, the original exception is logged, and
        an :exc:`~werkzeug.exceptions.InternalServerError` is returned.

        If an error handler is registered for ``InternalServerError`` or
        ``500``, it will be used. For consistency, the handler will
        always receive the ``InternalServerError``. The original
        unhandled exception is available as ``e.original_exception``.

        .. versionchanged:: 1.1.0
            Always passes the ``InternalServerError`` instance to the
            handler, setting ``original_exception`` to the unhandled
            error.

        .. versionchanged:: 1.1.0
            ``after_request`` functions and other finalization is done
            even for the default 500 response when there is no handler.

        .. versionadded:: 0.3
        """
        aY = sys.exc_info()
        got_request_exception.send(self, _async_wrapper=self.x, exception=aX)
        aZ = self.config["PROPAGATE_EXCEPTIONS"]

        if aZ is None:
            aZ = self.testing or self.debug

        if aZ:
            # Re-raise if called with an active exception, otherwise
            # raise the passed in exception.
            if aY[1] is aX:
                raise

            raise aX

        self.r(aW, aY)
        ba: InternalServerError | ft.ResponseReturnValue
        ba = InternalServerError(original_exception=aX)
        bb = self._find_error_handler(ba, aW.request.blueprints)

        if bb is not None:
            ba = self.x(bb)(ba)

        return self.v(aW, ba, from_error_handler=True)

    def r(
        self,
        bc: AppContext,
        bd: tuple[type, BaseException, TracebackType] | tuple[None, None, None],
    ) -> None:
        """Logs an exception.  This is called by :meth:`handle_exception`
        if debugging is disabled and right before the handler is called.
        The default implementation logs the exception as error on the
        :attr:`logger`.

        .. versionadded:: 0.8
        """
        self.logger.error(
            f"Exception on {bc.request.path} [{bc.request.method}]", exc_info=bd
        )

    def s(self, be: AppContext) -> ft.ResponseReturnValue:
        """Does the request dispatching.  Matches the URL and returns the
        return value of the view or error handler.  This does not have to
        be a response object.  In order to convert the return value to a
        proper response object, call :func:`make_response`.

        .. versionchanged:: 0.7
           This no longer does the exception handling, this code was
           moved to the new :meth:`full_dispatch_request`.
        """
        bf = be.request

        if bf.routing_exception is not None:
            self.i(bf)
        bg: Rule = bf.url_rule  # type: ignore[assignment]
        # if we provide automatic options for this URL and the
        # request came with the OPTIONS method, reply automatically
        if (
            getattr(bg, "provide_automatic_options", False)
            and bf.method == "OPTIONS"
        ):
            return self.w(be)
        # otherwise dispatch to the handler for that endpoint
        bh: dict[str, t.Any] = bf.view_args  # type: ignore[assignment]
        return self.x(self.view_functions[bg.endpoint])(**bh)  # type: ignore[no-any-return]

    def u(self, bi: AppContext) -> Response:
        """Dispatches the request and on top of that performs request
        pre and postprocessing as well as HTTP exception catching and
        error handling.

        .. versionadded:: 0.7
        """
        if not self._got_first_request and self.should_ignore_error is not None:
            import warnings

            warnings.warn(
                "The 'should_ignore_error' method is deprecated and will"
                " be removed in Flask 3.3. Handle errors as needed in"
                " teardown handlers instead.",
                DeprecationWarning,
                stacklevel=1,
            )

        self._got_first_request = True

        try:
            request_started.send(self, _async_wrapper=self.x)
            bj = self.B(bi)
            if bj is None:
                bj = self.s(bi)
        except Exception as e:
            bj = self.p(bi, e)
        return self.v(bi, bj)

    def v(
        self,
        bk: AppContext,
        bl: ft.ResponseReturnValue | HTTPException,
        bm: bool = False,
    ) -> Response:
        """Given the return value from a view function this finalizes
        the request by converting it into a response and invoking the
        postprocessing functions.  This is invoked for both normal
        request dispatching as well as error handlers.

        Because this means that it might be called as a result of a
        failure a special safe mode is available which can be enabled
        with the `from_error_handler` flag.  If enabled, failures in
        response processing will be logged and otherwise ignored.

        :internal:
        """
        bn = self.A(bl)
        try:
            bn = self.C(bk, bn)
            request_finished.send(
                self, _async_wrapper=self.x, response=bn
            )
        except Exception:
            if not bm:
                raise
            self.logger.exception(
                "Request finalizing failed with an error while handling an error"
            )
        return bn

    def w(self, bo: AppContext) -> Response:
        """This method is called to create the default ``OPTIONS`` response.
        This can be changed through subclassing to change the default
        behavior of ``OPTIONS`` responses.

        .. versionadded:: 0.7
        """
        bp = bo.url_adapter.allowed_methods()  # type: ignore[union-attr]
        bq = self.response_class()
        bq.allow.update(bp)
        return bq

    def x(self, br: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        """Ensure that the function is synchronous for WSGI workers.
        Plain ``def`` functions are returned as-is. ``async def``
        functions are wrapped to run and wait for the response.

        Override this method to change how the app runs async views.

        .. versionadded:: 2.0
        """
        if iscoroutinefunction(br):
            return self.y(br)

        return br

    def y(
        self, bs: t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]]
    ) -> t.Callable[..., t.Any]:
        """Return a sync function that will run the coroutine function.

        .. code-block:: python

            result = app.async_to_sync(func)(*args, **kwargs)

        Override this method to change how the app converts async code
        to be synchronously callable.

        .. versionadded:: 2.0
        """
        try:
            from asgiref.sync import async_to_sync as asgiref_async_to_sync
        except ImportError:
            raise RuntimeError(
                "Install Flask with the 'async' extra in order to use async views."
            ) from None

        return asgiref_async_to_sync(bs)

    def z(
        self,
        /,
        bt: str,
        *,
        bu: str | None = None,
        bv: str | None = None,
        bw: str | None = None,
        bx: bool | None = None,
        **by: t.Any,
    ) -> str:
        """Generate a URL to the given endpoint with the given values.

        This is called by :func:`flask.url_for`, and can be called
        directly as well.

        An *endpoint* is the name of a URL rule, usually added with
        :meth:`@app.route() <route>`, and usually the same name as the
        view function. A route defined in a :class:`~flask.Blueprint`
        will prepend the blueprint's name separated by a ``.`` to the
        endpoint.

        In some cases, such as email messages, you want URLs to include
        the scheme and domain, like ``https://example.com/hello``. When
        not in an active request, URLs will be external by default, but
        this requires setting :data:`SERVER_NAME` so Flask knows what
        domain to use. :data:`APPLICATION_ROOT` and
        :data:`PREFERRED_URL_SCHEME` should also be configured as
        needed. This config is only used when not in an active request.

        Functions can be decorated with :meth:`url_defaults` to modify
        keyword arguments before the URL is built.

        If building fails for some reason, such as an unknown endpoint
        or incorrect values, the app's :meth:`handle_url_build_error`
        method is called. If that returns a string, that is returned,
        otherwise a :exc:`~werkzeug.routing.BuildError` is raised.

        :param endpoint: The endpoint name associated with the URL to
            generate. If this starts with a ``.``, the current blueprint
            name (if any) will be used.
        :param _anchor: If given, append this as ``#anchor`` to the URL.
        :param _method: If given, generate the URL associated with this
            method for the endpoint.
        :param _scheme: If given, the URL will have this scheme if it
            is external.
        :param _external: If given, prefer the URL to be internal
            (False) or require it to be external (True). External URLs
            include the scheme and domain. When not in an active
            request, URLs are external by default.
        :param values: Values to use for the variable parts of the URL
            rule. Unknown keys are appended as query string arguments,
            like ``?a=b&c=d``.

        .. versionadded:: 2.2
            Moved from ``flask.url_for``, which calls this method.
        """
        if (bz := _cv_app.get(None)) is not None and bz.has_request:
            bA = bz.url_adapter
            bB = bz.request.blueprint

            # If the endpoint starts with "." and the request matches a
            # blueprint, the endpoint is relative to the blueprint.
            if bt[:1] == ".":
                if bB is not None:
                    bt = f"{bB}{bt}"
                else:
                    bt = bt[1:]

            # When in a request, generate a URL without scheme and
            # domain by default, unless a scheme is given.
            if bx is None:
                bx = bw is not None
        else:
            # If called by helpers.url_for, an app context is active,
            # use its url_adapter. Otherwise, app.url_for was called
            # directly, build an adapter.
            if bz is not None:
                bA = bz.url_adapter
            else:
                bA = self.h(None)

            if bA is None:
                raise RuntimeError(
                    "Unable to build URLs outside an active request"
                    " without 'SERVER_NAME' configured. Also configure"
                    " 'APPLICATION_ROOT' and 'PREFERRED_URL_SCHEME' as"
                    " needed."
                )

            # When outside a request, generate a URL with scheme and
            # domain by default.
            if bx is None:
                bx = True

        # It is an error to set _scheme when _external=False, in order
        # to avoid accidental insecure URLs.
        if bw is not None and not bx:
            raise ValueError("When specifying '_scheme', '_external' must be True.")

        self.inject_url_defaults(bt, by)

        try:
            bC = bA.build(  # type: ignore[union-attr]
                bt,
                by,
                method=bv,
                url_scheme=bw,
                force_external=bx,
            )
        except BuildError as error:
            by.update(
                _anchor=bu, _method=bv, _scheme=bw, _external=bx
            )
            return self.handle_url_build_error(error, bt, by)

        if bu is not None:
            bu = _url_quote(bu, safe="%!#$&'()*+,/:;=?@")
            bC = f"{bC}#{bu}"

        return bC

    def A(self, bD: ft.ResponseReturnValue) -> Response:
        """Convert the return value from a view function to an instance of
        :attr:`response_class`.

        :param rv: the return value from the view function. The view function
            must return a response. Returning ``None``, or the view ending
            without returning, is not allowed. The following types are allowed
            for ``view_rv``:

            ``str``
                A response object is created with the string encoded to UTF-8
                as the body.

            ``bytes``
                A response object is created with the bytes as the body.

            ``dict``
                Converted to a JSON response.

            ``list``
                Converted to a JSON response.

            ``generator`` or ``iterator``
                A generator that returns ``str`` or ``bytes`` to be
                streamed as the response.

            ``tuple``
                Either ``(body, status, headers)``, ``(body, status)``, or
                ``(body, headers)``, where ``body`` is any of the other types
                allowed here, ``status`` is a string or an integer, and
                ``headers`` is a dictionary or a list of ``(key, value)``
                tuples. If ``body`` is a :attr:`response_class` instance,
                ``status`` overwrites the exiting value and ``headers`` are
                extended.

            :attr:`response_class`
                The object is returned unchanged.

            other :class:`~werkzeug.wrappers.Response` class
                The object is coerced to :attr:`response_class`.

            :func:`callable`
                The function is called as a WSGI application. The result is
                used to create a response object.

        .. versionchanged:: 2.2
            A generator will be converted to a streaming response.
            A list will be converted to a JSON response.

        .. versionchanged:: 1.1
            A dict will be converted to a JSON response.

        .. versionchanged:: 0.9
           Previously a tuple was interpreted as the arguments for the
           response object.
        """

        bE: int | None = None
        bF: HeadersValue | None = None

        # unpack tuple returns
        if isinstance(bD, tuple):
            bG = len(bD)

            # a 3-tuple is unpacked directly
            if bG == 3:
                bD, bE, bF = bD  # type: ignore[misc]
            # decide if a 2-tuple has status or headers
            elif bG == 2:
                if isinstance(bD[1], (Headers, dict, tuple, list)):
                    bD, bF = bD  # pyright: ignore
                else:
                    bD, bE = bD  # type: ignore[assignment,misc]
            # other sized tuples are not allowed
            else:
                raise TypeError(
                    "The view function did not return a valid response tuple."
                    " The tuple must have the form (body, status, headers),"
                    " (body, status), or (body, headers)."
                )

        # the body must not be None
        if bD is None:
            raise TypeError(
                f"The view function for {request.endpoint!r} did not"
                " return a valid response. The function either returned"
                " None or ended without a return statement."
            )

        # make sure the body is an instance of the response class
        if not isinstance(bD, self.response_class):
            if isinstance(bD, (str, bytes, bytearray)) or isinstance(bD, cabc.Iterator):
                # let the response class set the status and headers instead of
                # waiting to do it manually, so that the class can handle any
                # special logic
                bD = self.response_class(
                    bD,  # pyright: ignore
                    status=bE,
                    headers=bF,  # type: ignore[arg-type]
                )
                bE = bF = None
            elif isinstance(bD, (dict, list)):
                bD = self.json.response(bD)
            elif isinstance(bD, BaseResponse) or callable(bD):
                # evaluate a WSGI callable, or coerce a different response
                # class to the correct type
                try:
                    bD = self.response_class.force_type(
                        bD,  # type: ignore[arg-type]
                        request.environ,
                    )
                except TypeError as e:
                    raise TypeError(
                        f"{e}\nThe view function did not return a valid"
                        " response. The return type must be a string,"
                        " dict, list, tuple with headers or status,"
                        " Response instance, or WSGI callable, but it"
                        f" was a {type(bD).__name__}."
                    ).with_traceback(sys.exc_info()[2]) from None
            else:
                raise TypeError(
                    "The view function did not return a valid"
                    " response. The return type must be a string,"
                    " dict, list, tuple with headers or status,"
                    " Response instance, or WSGI callable, but it was a"
                    f" {type(bD).__name__}."
                )

        bD = t.cast(Response, bD)
        # prefer the status if it was provided
        if bE is not None:
            if isinstance(bE, (str, bytes, bytearray)):
                bD.status = bE
            else:
                bD.status_code = bE

        # extend existing headers with provided headers
        if bF:
            bD.headers.update(bF)

        return bD

    def B(self, bH: AppContext) -> ft.ResponseReturnValue | None:
        """Called before the request is dispatched. Calls
        :attr:`url_value_preprocessors` registered with the app and the
        current blueprint (if any). Then calls :attr:`before_request_funcs`
        registered with the app and the blueprint.

        If any :meth:`before_request` handler returns a non-None value, the
        value is handled as if it was the return value from the view, and
        further request handling is stopped.
        """
        bI = bH.request
        bJ = (None, *reversed(bI.blueprints))

        for bK in bJ:
            if bK in self.url_value_preprocessors:
                for bL in self.url_value_preprocessors[bK]:
                    bL(bI.endpoint, bI.view_args)

        for bK in bJ:
            if bK in self.before_request_funcs:
                for bM in self.before_request_funcs[bK]:
                    bN = self.x(bM)()

                    if bN is not None:
                        return bN  # type: ignore[no-any-return]

        return None

    def C(self, bO: AppContext, bP: Response) -> Response:
        """Can be overridden in order to modify the response object
        before it's sent to the WSGI server.  By default this will
        call all the :meth:`after_request` decorated functions.

        .. versionchanged:: 0.5
           As of Flask 0.5 the functions registered for after request
           execution are called in reverse order of registration.

        :param response: a :attr:`response_class` object.
        :return: a new response object or the same, has to be an
                 instance of :attr:`response_class`.
        """
        for bQ in bO._after_request_functions:
            bP = self.x(bQ)(bP)

        for bR in chain(bO.request.blueprints, (None,)):
            if bR in self.after_request_funcs:
                for bQ in reversed(self.after_request_funcs[bR]):
                    bP = self.x(bQ)(bP)

        if not self.session_interface.is_null_session(bO._get_session()):
            self.session_interface.save_session(self, bO._get_session(), bP)

        return bP

    def D(
        self, bS: AppContext, bT: BaseException | None = None
    ) -> None:
        """Called after the request is dispatched and the response is finalized,
        right before the request context is popped. Called by
        :meth:`.AppContext.pop`.

        This calls all functions decorated with :meth:`teardown_request`, and
        :meth:`Blueprint.teardown_request` if a blueprint handled the request.
        Finally, the :data:`request_tearing_down` signal is sent.

        :param exc: An unhandled exception raised while dispatching the request.
            Passed to each teardown function.

        .. versionchanged:: 3.2
            All callbacks are called rather than stopping on the first error.

        .. versionchanged:: 0.9
            Added the ``exc`` argument.
        """
        bU = _CollectErrors()

        for bV in chain(bS.request.blueprints, (None,)):
            if bV in self.teardown_request_funcs:
                for bW in reversed(self.teardown_request_funcs[bV]):
                    with bU:
                        self.x(bW)(bT)

        with bU:
            request_tearing_down.send(self, _async_wrapper=self.x, exc=bT)

        bU.raise_any("Errors during request teardown")

    def E(
        self, bX: AppContext, bY: BaseException | None = None
    ) -> None:
        """Called right before the application context is popped. Called by
        :meth:`.AppContext.pop`.

        This calls all functions decorated with :meth:`teardown_appcontext`.
        Then the :data:`appcontext_tearing_down` signal is sent.

        :param exc: An unhandled exception raised while the context was active.
            Passed to each teardown function.

        .. versionchanged:: 3.2
            All callbacks are called rather than stopping on the first error.

        .. versionadded:: 0.9
        """
        bZ = _CollectErrors()

        for ca in reversed(self.teardown_appcontext_funcs):
            with bZ:
                self.x(ca)(bY)

        with bZ:
            appcontext_tearing_down.send(self, _async_wrapper=self.x, exc=bY)

        bZ.raise_any("Errors during app teardown")

    def F(self) -> AppContext:
        """Create an :class:`.AppContext`. When the context is pushed,
        :data:`.current_app` and :data:`.g` become available.

        A context is automatically pushed when handling each request, and when
        running any ``flask`` CLI command. Use this as a ``with`` block to
        manually push a context outside of those situations, such as during
        setup or testing.

        .. code-block:: python

            with app.app_context():
                init_db()

        See :doc:`/appcontext`.

        .. versionadded:: 0.9
        """
        return AppContext(self)

    def G(self, cb: WSGIEnvironment) -> AppContext:
        """Create an :class:`.AppContext` with request information representing
        the given WSGI environment. A context is automatically pushed when
        handling each request. When the context is pushed, :data:`.request`,
        :data:`.session`, :data:`g:, and :data:`.current_app` become available.

        This method should not be used in your own code. Creating a valid WSGI
        environ is not trivial. Use :meth:`test_request_context` to correctly
        create a WSGI environ and request context instead.

        See :doc:`/appcontext`.

        :param environ: A WSGI environment.
        """
        return AppContext.from_environ(self, cb)

    def H(self, *cc: t.Any, **cd: t.Any) -> AppContext:
        """Create an :class:`.AppContext` with request information created from
        the given arguments. When the context is pushed, :data:`.request`,
        :data:`.session`, :data:`g:, and :data:`.current_app` become available.

        This is useful during testing to run a function that uses request data
        without dispatching a full request. Use this as a ``with`` block to push
        a context.

        .. code-block:: python

            with app.test_request_context(...):
                generate_report()

        See :doc:`/appcontext`.

        Takes the same arguments as Werkzeug's
        :class:`~werkzeug.test.EnvironBuilder`, with some defaults from
        the application. See the linked Werkzeug docs for most of the
        available arguments. Flask-specific behavior is listed here.

        :param path: URL path being requested.
        :param base_url: Base URL where the app is being served, which
            ``path`` is relative to. If not given, built from
            :data:`PREFERRED_URL_SCHEME`, ``subdomain``, :data:`SERVER_NAME`,
            and :data:`APPLICATION_ROOT`.
        :param subdomain: Subdomain name to prepend to :data:`SERVER_NAME`.
        :param url_scheme: Scheme to use instead of
            :data:`PREFERRED_URL_SCHEME`.
        :param data: The request body text or bytes,or a dict of form data.
        :param json: If given, this is serialized as JSON and passed as
            ``data``. Also defaults ``content_type`` to
            ``application/json``.
        :param args: Other positional arguments passed to
            :class:`~werkzeug.test.EnvironBuilder`.
        :param kwargs: Other keyword arguments passed to
            :class:`~werkzeug.test.EnvironBuilder`.
        """
        from .testing import EnvironBuilder

        ce = EnvironBuilder(self, *cc, **cd)

        try:
            cf = ce.get_environ()
        finally:
            ce.close()

        return self.G(cf)

    def I(
        self, cg: WSGIEnvironment, ch: StartResponse
    ) -> cabc.Iterable[bytes]:
        """The actual WSGI application. This is not implemented in
        :meth:`__call__` so that middlewares can be applied without
        losing a reference to the app object. Instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        .. versionchanged:: 0.7
            Teardown events for the request and app contexts are called
            even if an unhandled error occurs. Other events may not be
            called depending on when an error occurs during dispatch.

        :param environ: A WSGI environment.
        :param start_response: A callable accepting a status code,
            a list of headers, and an optional exception context to
            start the response.
        """
        ci = self.G(cg)
        cj: BaseException | None = None
        try:
            try:
                ci.push()
                ck = self.u(ci)
            except Exception as e:
                cj = e
                ck = self.q(ci, e)
            except:
                cj = sys.exc_info()[1]
                raise
            return ck(cg, ch)
        finally:
            if "werkzeug.debug.preserve_context" in cg:
                cg["werkzeug.debug.preserve_context"](ci)

            if (
                cj is not None
                and self.should_ignore_error is not None
                and self.should_ignore_error(cj)
            ):
                cj = None

            ci.pop(cj)

    def __call__(
        self, cl: WSGIEnvironment, cm: StartResponse
    ) -> cabc.Iterable[bytes]:
        """The WSGI server calls the Flask application object as the
        WSGI application. This calls :meth:`wsgi_app`, which can be
        wrapped to apply middleware.
        """
        return self.I(cl, cm)
