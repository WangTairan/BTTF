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

    def __init_subclass__(cls, **kwa: t.Any) -> None:
        import warnings

        # These method signatures were updated to take a ctx param. Detect
        # overridden methods in subclasses that still have the old signature.
        # Show a deprecation warning and wrap to call with correct args.
        for met in (
            cls.handle,
            cls.handle2,
            cls.handle3,
            cls.log,
            cls.dispatch,
            cls.full,
            cls.finalize,
            cls.make2,
            cls.preprocess,
            cls.process,
            cls.do,
            cls.do2,
        ):
            base = getattr(Flask, met.__name__)

            if met is base:
                # not overridden
                continue

            # get the second parameter (first is self)
            iter2 = iter(inspect.signature(met).parameters.values())
            next(iter2)
            par = next(iter2, None)

            # must have second parameter named ctx or annotated AppContext
            if par is None or not (
                # no annotation, match name
                (par.annotation is inspect.Parameter.empty and par.name == "ctx")
                or (
                    # string annotation, access path ends with AppContext
                    isinstance(par.annotation, str)
                    and par.annotation.rpartition(".")[2] == "AppContext"
                )
                or (
                    # class annotation
                    inspect.isclass(par.annotation)
                    and issubclass(par.annotation, AppContext)
                )
            ):
                warnings.warn(
                    f"The '{met.__name__}' method now takes 'ctx: AppContext'"
                    " as the first parameter. The old signature is deprecated"
                    " and will not be supported in Flask 4.0.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                setattr(cls, met.__name__, remove_ctx(met))
                setattr(Flask, met.__name__, add_ctx(base))

    def __init__(
        self,
        import2: str,
        static: str | None = None,
        static2: str | os.PathLike[str] | None = "static",
        static3: str | None = None,
        host2: bool = False,
        subdomain2: bool = False,
        template: str | os.PathLike[str] | None = "templates",
        instance: str | None = None,
        instance2: bool = False,
        root: str | None = None,
    ):
        super().__init__(
            import_name=import2,
            static_url_path=static,
            static_folder=static2,
            static_host=static3,
            host_matching=host2,
            subdomain_matching=subdomain2,
            template_folder=template,
            instance_path=instance,
            instance_relative_config=instance2,
            root_path=root,
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
            assert bool(static3) == host2, (
                "Invalid static_host/host_matching combination"
            )
            # Use a weakref to avoid creating a reference cycle between the app
            # and the view function (see #3761).
            self2 = weakref.ref(self)
            self.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                endpoint="static",
                host=static3,
                view_func=lambda **kw: self2().send_static_file(**kw),  # type: ignore
            )

    def get2(self, fil: str | None) -> int | None:
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
        val = self.config["SEND_FILE_MAX_AGE_DEFAULT"]

        if val is None:
            return None

        if isinstance(val, timedelta):
            return int(val.total_seconds())

        return val  # type: ignore[no-any-return]

    def send2(self, fil2: str) -> Response:
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
        max = self.get2(fil2)
        return send_from_directory(
            t.cast(str, self.static_folder), fil2, max_age=max
        )

    def open2(
        self, res: str, mod: str = "rb", enc: str | None = None
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
        if mod not in {"r", "rt", "rb"}:
            raise ValueError("Resources can only be opened for reading.")

        pat = os.path.join(self.root_path, res)

        if mod == "rb":
            return open(pat, mod)  # pyright: ignore

        return open(pat, mod, encoding=enc)

    def open3(
        self, res2: str, mod2: str = "rb", enc2: str | None = "utf-8"
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
        pat2 = os.path.join(self.instance_path, res2)

        if "b" in mod2:
            return open(pat2, mod2)

        return open(pat2, mod2, encoding=enc2)

    def create(self) -> Environment:
        """Create the Jinja environment based on :attr:`jinja_options`
        and the various Jinja-related methods of the app. Changing
        :attr:`jinja_options` after this will have no effect. Also adds
        Flask-related globals and filters to the environment.

        .. versionchanged:: 0.11
           ``Environment.auto_reload`` set in accordance with
           ``TEMPLATES_AUTO_RELOAD`` configuration option.

        .. versionadded:: 0.5
        """
        opt = dict(self.jinja_options)

        if "autoescape" not in opt:
            opt["autoescape"] = self.select_jinja_autoescape

        if "auto_reload" not in opt:
            auto = self.config["TEMPLATES_AUTO_RELOAD"]

            if auto is None:
                auto = self.debug

            opt["auto_reload"] = auto

        rv2 = self.jinja_environment(self, **opt)
        rv2.globals.update(
            url_for=self.url,
            get_flashed_messages=get_flashed_messages,
            config=self.config,
            # request, session and g are normally added with the
            # context processor for efficiency reasons but for imported
            # templates we also want the proxies in there.
            request=request,
            session=session,
            g=g,
        )
        rv2.policies["json.dumps_function"] = self.json.dumps
        return rv2

    def create2(self, req2: Request | None) -> MapAdapter | None:
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
        if req2 is not None:
            if (trusted := self.config["TRUSTED_HOSTS"]) is not None:
                req2.trusted_hosts = trusted

            # Check trusted_hosts here until bind_to_environ does.
            req2.host = get_host(req2.environ, req2.trusted_hosts)  # pyright: ignore
            sub = None
            server = self.config["SERVER_NAME"]

            if self.url_map.host_matching:
                # Don't pass SERVER_NAME, otherwise it's used and the actual
                # host is ignored, which breaks host matching.
                server = None
            elif not self.subdomain_matching:
                # Werkzeug doesn't implement subdomain matching yet. Until then,
                # disable it by forcing the current subdomain to the default, or
                # the empty string.
                sub = self.url_map.default_subdomain or ""

            return self.url_map.bind_to_environ(
                req2.environ, server_name=server, subdomain=sub
            )

        # Need at least SERVER_NAME to match/build outside a request.
        if self.config["SERVER_NAME"] is not None:
            return self.url_map.bind(
                self.config["SERVER_NAME"],
                script_name=self.config["APPLICATION_ROOT"],
                url_scheme=self.config["PREFERRED_URL_SCHEME"],
            )

        return None

    def raise2(self, req3: Request) -> t.NoReturn:
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
            or not isinstance(req3.routing_exception, RequestRedirect)
            or req3.routing_exception.code in {307, 308}
            or req3.method in {"GET", "HEAD", "OPTIONS"}
        ):
            raise req3.routing_exception  # type: ignore[misc]

        from .debughelpers import FormDataRoutingRedirect

        raise FormDataRoutingRedirect(req3)

    def update2(
        self, ctx2: AppContext, con: dict[str, t.Any]
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
        nam: t.Iterable[str | None] = (None,)

        # A template may be rendered outside a request context.
        if ctx2.has_request:
            nam = chain(nam, reversed(ctx2.request.blueprints))

        # The values passed to render_template take precedence. Keep a
        # copy to re-apply after all context functions.
        orig = con.copy()

        for nam2 in nam:
            if nam2 in self.template_context_processors:
                for fun in self.template_context_processors[nam2]:
                    con.update(self.ensure(fun)())

        con.update(orig)

    def make(self) -> dict[str, t.Any]:
        """Returns the shell context for an interactive shell for this
        application.  This runs all the registered shell context
        processors.

        .. versionadded:: 0.11
        """
        rv3 = {"app": self, "g": g}
        for pro in self.shell_context_processors:
            rv3.update(pro())
        return rv3

    def run(
        self,
        hos: str | None = None,
        por: int | None = None,
        deb: bool | None = None,
        load: bool = True,
        **opt2: t.Any,
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

        if get_load_dotenv(load):
            cli.load_dotenv()

            # if set, env var overrides existing value
            if "FLASK_DEBUG" in os.environ:
                self.debug = get_debug_flag()

        # debug passed to method overrides all other sources
        if deb is not None:
            self.debug = bool(deb)

        server2 = self.config.get("SERVER_NAME")
        sn = sn2 = None

        if server2:
            server3 = urlsplit(f"//{server2}")
            sn = server3.hostname
            sn2 = server3.port

        if not hos:
            if sn:
                hos = sn
            else:
                hos = "127.0.0.1"

        if por or por == 0:
            por = int(por)
        elif sn2 is not None:
            por = sn2
        else:
            por = 5000

        opt2.setdefault("use_reloader", self.debug)
        opt2.setdefault("use_debugger", self.debug)
        opt2.setdefault("threaded", True)

        cli.show_server_banner(self.debug, self.name)

        from werkzeug.serving import run_simple

        try:
            run_simple(hos, por, self, **opt2)
        finally:
            # reset the first request information if the development server
            # reset normally.  This makes it possible to restart the server
            # without reloader and that stuff from an interactive shell.
            self._got_first_request = False

    def test(self, use: bool = True, **kwa2: t.Any) -> FlaskClient:
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
        cls2 = self.test_client_class
        if cls2 is None:
            from .testing import FlaskClient as cls
        return cls2(  # type: ignore
            self, self.response_class, use_cookies=use, **kwa2
        )

    def test2(self, **kwa3: t.Any) -> FlaskCliRunner:
        """Create a CLI runner for testing CLI commands.
        See :ref:`testing-cli`.

        Returns an instance of :attr:`test_cli_runner_class`, by default
        :class:`~flask.testing.FlaskCliRunner`. The Flask app object is
        passed as the first argument.

        .. versionadded:: 1.0
        """
        cls3 = self.test_cli_runner_class

        if cls3 is None:
            from .testing import FlaskCliRunner as cls

        return cls3(self, **kwa3)  # type: ignore

    def handle(
        self, ctx3: AppContext, e2: HTTPException
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
        if e2.code is None:
            return e2

        # RoutingExceptions are used internally to trigger routing
        # actions, such as slash redirects raising RequestRedirect. They
        # are not raised or handled in user code.
        if isinstance(e2, RoutingException):
            return e2

        han = self._find_error_handler(e2, ctx3.request.blueprints)
        if han is None:
            return e2
        return self.ensure(han)(e2)  # type: ignore[no-any-return]

    def handle2(
        self, ctx4: AppContext, e3: Exception
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
        if isinstance(e3, BadRequestKeyError) and (
            self.debug or self.config["TRAP_BAD_REQUEST_ERRORS"]
        ):
            e3.show_exception = True

        if isinstance(e3, HTTPException) and not self.trap_http_exception(e3):
            return self.handle(ctx4, e3)

        han2 = self._find_error_handler(e3, ctx4.request.blueprints)

        if han2 is None:
            raise

        return self.ensure(han2)(e3)  # type: ignore[no-any-return]

    def handle3(self, ctx5: AppContext, e4: Exception) -> Response:
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
        exc2 = sys.exc_info()
        got_request_exception.send(self, _async_wrapper=self.ensure, exception=e4)
        pro2 = self.config["PROPAGATE_EXCEPTIONS"]

        if pro2 is None:
            pro2 = self.testing or self.debug

        if pro2:
            # Re-raise if called with an active exception, otherwise
            # raise the passed in exception.
            if exc2[1] is e4:
                raise

            raise e4

        self.log(ctx5, exc2)
        server4: InternalServerError | ft.ResponseReturnValue
        server4 = InternalServerError(original_exception=e4)
        han3 = self._find_error_handler(server4, ctx5.request.blueprints)

        if han3 is not None:
            server4 = self.ensure(han3)(server4)

        return self.finalize(ctx5, server4, from_error_handler=True)

    def log(
        self,
        ctx6: AppContext,
        exc3: tuple[type, BaseException, TracebackType] | tuple[None, None, None],
    ) -> None:
        """Logs an exception.  This is called by :meth:`handle_exception`
        if debugging is disabled and right before the handler is called.
        The default implementation logs the exception as error on the
        :attr:`logger`.

        .. versionadded:: 0.8
        """
        self.logger.error(
            f"Exception on {ctx6.request.path} [{ctx6.request.method}]", exc_info=exc3
        )

    def dispatch(self, ctx7: AppContext) -> ft.ResponseReturnValue:
        """Does the request dispatching.  Matches the URL and returns the
        return value of the view or error handler.  This does not have to
        be a response object.  In order to convert the return value to a
        proper response object, call :func:`make_response`.

        .. versionchanged:: 0.7
           This no longer does the exception handling, this code was
           moved to the new :meth:`full_dispatch_request`.
        """
        req4 = ctx7.request

        if req4.routing_exception is not None:
            self.raise2(req4)
        rul: Rule = req4.url_rule  # type: ignore[assignment]
        # if we provide automatic options for this URL and the
        # request came with the OPTIONS method, reply automatically
        if (
            getattr(rul, "provide_automatic_options", False)
            and req4.method == "OPTIONS"
        ):
            return self.make2(ctx7)
        # otherwise dispatch to the handler for that endpoint
        view: dict[str, t.Any] = req4.view_args  # type: ignore[assignment]
        return self.ensure(self.view_functions[rul.endpoint])(**view)  # type: ignore[no-any-return]

    def full(self, ctx8: AppContext) -> Response:
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
            request_started.send(self, _async_wrapper=self.ensure)
            rv4 = self.preprocess(ctx8)
            if rv4 is None:
                rv4 = self.dispatch(ctx8)
        except Exception as e:
            rv4 = self.handle2(ctx8, e)
        return self.finalize(ctx8, rv4)

    def finalize(
        self,
        ctx9: AppContext,
        rv5: ft.ResponseReturnValue | HTTPException,
        from2: bool = False,
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
        res3 = self.make3(rv5)
        try:
            res3 = self.process(ctx9, res3)
            request_finished.send(
                self, _async_wrapper=self.ensure, response=res3
            )
        except Exception:
            if not from2:
                raise
            self.logger.exception(
                "Request finalizing failed with an error while handling an error"
            )
        return res3

    def make2(self, ctx10: AppContext) -> Response:
        """This method is called to create the default ``OPTIONS`` response.
        This can be changed through subclassing to change the default
        behavior of ``OPTIONS`` responses.

        .. versionadded:: 0.7
        """
        met2 = ctx10.url_adapter.allowed_methods()  # type: ignore[union-attr]
        rv6 = self.response_class()
        rv6.allow.update(met2)
        return rv6

    def ensure(self, fun2: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        """Ensure that the function is synchronous for WSGI workers.
        Plain ``def`` functions are returned as-is. ``async def``
        functions are wrapped to run and wait for the response.

        Override this method to change how the app runs async views.

        .. versionadded:: 2.0
        """
        if iscoroutinefunction(fun2):
            return self.async2(fun2)

        return fun2

    def async2(
        self, fun3: t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]]
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

        return asgiref_async_to_sync(fun3)

    def url(
        self,
        /,
        end: str,
        *,
        anc: str | None = None,
        met3: str | None = None,
        sch: str | None = None,
        ext: bool | None = None,
        **val2: t.Any,
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
        if (ctx11 := _cv_app.get(None)) is not None and ctx11.has_request:
            url2 = ctx11.url_adapter
            blueprint2 = ctx11.request.blueprint

            # If the endpoint starts with "." and the request matches a
            # blueprint, the endpoint is relative to the blueprint.
            if end[:1] == ".":
                if blueprint2 is not None:
                    end = f"{blueprint2}{end}"
                else:
                    end = end[1:]

            # When in a request, generate a URL without scheme and
            # domain by default, unless a scheme is given.
            if ext is None:
                ext = sch is not None
        else:
            # If called by helpers.url_for, an app context is active,
            # use its url_adapter. Otherwise, app.url_for was called
            # directly, build an adapter.
            if ctx11 is not None:
                url2 = ctx11.url_adapter
            else:
                url2 = self.create2(None)

            if url2 is None:
                raise RuntimeError(
                    "Unable to build URLs outside an active request"
                    " without 'SERVER_NAME' configured. Also configure"
                    " 'APPLICATION_ROOT' and 'PREFERRED_URL_SCHEME' as"
                    " needed."
                )

            # When outside a request, generate a URL with scheme and
            # domain by default.
            if ext is None:
                ext = True

        # It is an error to set _scheme when _external=False, in order
        # to avoid accidental insecure URLs.
        if sch is not None and not ext:
            raise ValueError("When specifying '_scheme', '_external' must be True.")

        self.inject_url_defaults(end, val2)

        try:
            rv7 = url2.build(  # type: ignore[union-attr]
                end,
                val2,
                method=met3,
                url_scheme=sch,
                force_external=ext,
            )
        except BuildError as error:
            val2.update(
                _anchor=anc, _method=met3, _scheme=sch, _external=ext
            )
            return self.handle_url_build_error(error, end, val2)

        if anc is not None:
            anc = _url_quote(anc, safe="%!#$&'()*+,/:;=?@")
            rv7 = f"{rv7}#{anc}"

        return rv7

    def make3(self, rv8: ft.ResponseReturnValue) -> Response:
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

        sta: int | None = None
        hea: HeadersValue | None = None

        # unpack tuple returns
        if isinstance(rv8, tuple):
            len2 = len(rv8)

            # a 3-tuple is unpacked directly
            if len2 == 3:
                rv8, sta, hea = rv8  # type: ignore[misc]
            # decide if a 2-tuple has status or headers
            elif len2 == 2:
                if isinstance(rv8[1], (Headers, dict, tuple, list)):
                    rv8, hea = rv8  # pyright: ignore
                else:
                    rv8, sta = rv8  # type: ignore[assignment,misc]
            # other sized tuples are not allowed
            else:
                raise TypeError(
                    "The view function did not return a valid response tuple."
                    " The tuple must have the form (body, status, headers),"
                    " (body, status), or (body, headers)."
                )

        # the body must not be None
        if rv8 is None:
            raise TypeError(
                f"The view function for {request.endpoint!r} did not"
                " return a valid response. The function either returned"
                " None or ended without a return statement."
            )

        # make sure the body is an instance of the response class
        if not isinstance(rv8, self.response_class):
            if isinstance(rv8, (str, bytes, bytearray)) or isinstance(rv8, cabc.Iterator):
                # let the response class set the status and headers instead of
                # waiting to do it manually, so that the class can handle any
                # special logic
                rv8 = self.response_class(
                    rv8,  # pyright: ignore
                    status=sta,
                    headers=hea,  # type: ignore[arg-type]
                )
                sta = hea = None
            elif isinstance(rv8, (dict, list)):
                rv8 = self.json.response(rv8)
            elif isinstance(rv8, BaseResponse) or callable(rv8):
                # evaluate a WSGI callable, or coerce a different response
                # class to the correct type
                try:
                    rv8 = self.response_class.force_type(
                        rv8,  # type: ignore[arg-type]
                        request.environ,
                    )
                except TypeError as e:
                    raise TypeError(
                        f"{e}\nThe view function did not return a valid"
                        " response. The return type must be a string,"
                        " dict, list, tuple with headers or status,"
                        " Response instance, or WSGI callable, but it"
                        f" was a {type(rv8).__name__}."
                    ).with_traceback(sys.exc_info()[2]) from None
            else:
                raise TypeError(
                    "The view function did not return a valid"
                    " response. The return type must be a string,"
                    " dict, list, tuple with headers or status,"
                    " Response instance, or WSGI callable, but it was a"
                    f" {type(rv8).__name__}."
                )

        rv8 = t.cast(Response, rv8)
        # prefer the status if it was provided
        if sta is not None:
            if isinstance(sta, (str, bytes, bytearray)):
                rv8.status = sta
            else:
                rv8.status_code = sta

        # extend existing headers with provided headers
        if hea:
            rv8.headers.update(hea)

        return rv8

    def preprocess(self, ctx12: AppContext) -> ft.ResponseReturnValue | None:
        """Called before the request is dispatched. Calls
        :attr:`url_value_preprocessors` registered with the app and the
        current blueprint (if any). Then calls :attr:`before_request_funcs`
        registered with the app and the blueprint.

        If any :meth:`before_request` handler returns a non-None value, the
        value is handled as if it was the return value from the view, and
        further request handling is stopped.
        """
        req5 = ctx12.request
        nam3 = (None, *reversed(req5.blueprints))

        for nam4 in nam3:
            if nam4 in self.url_value_preprocessors:
                for url3 in self.url_value_preprocessors[nam4]:
                    url3(req5.endpoint, req5.view_args)

        for nam4 in nam3:
            if nam4 in self.before_request_funcs:
                for before in self.before_request_funcs[nam4]:
                    rv9 = self.ensure(before)()

                    if rv9 is not None:
                        return rv9  # type: ignore[no-any-return]

        return None

    def process(self, ctx13: AppContext, res4: Response) -> Response:
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
        for fun4 in ctx13._after_request_functions:
            res4 = self.ensure(fun4)(res4)

        for nam5 in chain(ctx13.request.blueprints, (None,)):
            if nam5 in self.after_request_funcs:
                for fun4 in reversed(self.after_request_funcs[nam5]):
                    res4 = self.ensure(fun4)(res4)

        if not self.session_interface.is_null_session(ctx13._get_session()):
            self.session_interface.save_session(self, ctx13._get_session(), res4)

        return res4

    def do(
        self, ctx14: AppContext, exc4: BaseException | None = None
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
        collect = _CollectErrors()

        for nam6 in chain(ctx14.request.blueprints, (None,)):
            if nam6 in self.teardown_request_funcs:
                for fun5 in reversed(self.teardown_request_funcs[nam6]):
                    with collect:
                        self.ensure(fun5)(exc4)

        with collect:
            request_tearing_down.send(self, _async_wrapper=self.ensure, exc=exc4)

        collect.raise_any("Errors during request teardown")

    def do2(
        self, ctx15: AppContext, exc5: BaseException | None = None
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
        collect2 = _CollectErrors()

        for fun6 in reversed(self.teardown_appcontext_funcs):
            with collect2:
                self.ensure(fun6)(exc5)

        with collect2:
            appcontext_tearing_down.send(self, _async_wrapper=self.ensure, exc=exc5)

        collect2.raise_any("Errors during app teardown")

    def app(self) -> AppContext:
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

    def request2(self, env: WSGIEnvironment) -> AppContext:
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
        return AppContext.from_environ(self, env)

    def test3(self, *arg: t.Any, **kwa4: t.Any) -> AppContext:
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

        bui = EnvironBuilder(self, *arg, **kwa4)

        try:
            env2 = bui.get_environ()
        finally:
            bui.close()

        return self.request2(env2)

    def wsgi(
        self, env3: WSGIEnvironment, start: StartResponse
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
        ctx16 = self.request2(env3)
        err: BaseException | None = None
        try:
            try:
                ctx16.push()
                res5 = self.full(ctx16)
            except Exception as e:
                err = e
                res5 = self.handle3(ctx16, e)
            except:
                err = sys.exc_info()[1]
                raise
            return res5(env3, start)
        finally:
            if "werkzeug.debug.preserve_context" in env3:
                env3["werkzeug.debug.preserve_context"](ctx16)

            if (
                err is not None
                and self.should_ignore_error is not None
                and self.should_ignore_error(err)
            ):
                err = None

            ctx16.pop(err)

    def __call__(
        self, env4: WSGIEnvironment, start2: StartResponse
    ) -> cabc.Iterable[bytes]:
        """The WSGI server calls the Flask application object as the
        WSGI application. This calls :meth:`wsgi_app`, which can be
        wrapped to apply middleware.
        """
        return self.wsgi(env4, start2)
