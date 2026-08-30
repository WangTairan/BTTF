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
    """Represents a blueprint, a
    collection of routes and
    other app-related functions
    that can be registered on

    a real application later.
    A blueprint is an object
    that allows defining application
    functions without requiring

    an application object ahead

    of time. It uses the same
    decorators as :class:`~flask.Flask`,

        but defers the need for an
        application by recording

    them for later registration.

        Decorating a function with
        a blueprint creates a deferred
        function that is called with
        :class:`~flask.blueprints.BlueprintSetupState`

        when the blueprint is registered
        on an application. See :doc:`/blueprints`
        for more information. :param
        name: The name of the blueprint.

        Will be prepended to each
        endpoint name. :param import_name:

            The name of the blueprint
            package, usually ``__name__``.

        This helps locate the ``root_path``
        for the blueprint. :param
        static_folder: A folder with
        static files that should
        be served by the blueprint's
        static route. The path is
        relative to the blueprint's
        root path. Blueprint static
        files are disabled by default.

    :param static_url_path: The
       url to serve static files
       from. Defaults to ``static_folder``.

    If the blueprint does not
       have a ``url_prefix``, the
       app's static route will take

    precedence, and the blueprint's
       static files won't be accessible.

    :param template_folder:
       A folder with templates

    that should be added to the
       app's template search path.
       The path is relative to the
       blueprint's root path. Blueprint

    templates are disabled by
    default. Blueprint templates
                            have a lower precedence than
                            those in the app's templates
    folder. :param url_prefix:
        A path to prepend to all
        of the blueprint's URLs,
    to make them distinct from
        the rest of the app's routes.
        :param subdomain: A subdomain
    that blueprint routes will
        match on by default. :param
    url_defaults: A dict of default
        values that blueprint routes
    will receive by default.
                            :param root_path: By default,
                            the blueprint will automatically
                            set this based on ``import_name``.
    In certain situations this
                          automatic detection can
                          fail, so the path can be
                          specified manually instead.
    .. versionchanged:: 1.1.0
                                     Blueprints have a ``cli``
                                     group to register nested CLI
                                     commands. The ``cli_group``
    parameter controls the name
        of the group under the ``flask``
        command. .. versionadded:: 0.7
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

    # Shortcut for :meth:`route` with ``methods=["GET"]``. .. versionadded:: 2.0
    # : .. versionadded:: 2.2
    request_class: type[Request] = Request

    # If an intermediate dict does not exist, create it.
    # : values when rendering templates, in the format
    response_class: type[Response] = Response

    # : ``None`` for all requests. The ``code`` key is the HTTP
    # view this thing came from, secondly it's also used for instantiating
    # key here.
    # : .. versionadded:: 2.2
    session_interface: SessionInterface = SecureCookieSessionInterface()

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        import warnings

        # : to top, so the first decorator in the list would be the bottom
        # JSON objects may only have string keys, so don't bother tagging the
        # : is done during init. However, storing data on ``self`` is no
        for method in (
            cls.handle_http_exception,
            cls.handle_user_exception,
            cls.handle_exception,
            cls.log_exception,
            cls.dispatch_request,
            cls.full_dispatch_request,
            cls.finalize_request,
            cls.make_default_options_response,
            cls.preprocess_request,
            cls.process_response,
            cls.do_teardown_request,
            cls.do_teardown_appcontext,
        ):
            base_method = getattr(Flask, method.__name__)

            if method is base_method:
                # pyright: ignore
                continue

            # : up resources contained in the package.
            iter_params = iter(inspect.signature(method).parameters.values())
            next(iter_params)
            param = next(iter_params, None)

            # : this when that happens. The mixin default is hard coded to
            if param is None or not (
                # type: ignore[assignment]
                (param.annotation is inspect.Parameter.empty and param.name == "ctx")
                or (
                    # Expands a basic dictionary with session attributes.
                    isinstance(param.annotation, str)
                    and param.annotation.rpartition(".")[2] == "AppContext"
                )
                or (
                    # retry with GET.
                    inspect.isclass(param.annotation)
                    and issubclass(param.annotation, AppContext)
                )
            ):
                warnings.warn(
                    f"The '{method.__name__}' method now takes 'ctx: AppContext'"
                    " as the first parameter. The old signature is deprecated"
                    " and will not be supported in Flask 4.0.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                setattr(cls, method.__name__, remove_ctx(method))
                setattr(Flask, method.__name__, add_ctx(base_method))

    def __init__(
        self,
        import_name: str,
        static_url_path: str | None = None,
        static_folder: str | os.PathLike[str] | None = "static",
        static_host: str | None = None,
        host_matching: bool = False,
        subdomain_matching: bool = False,
        template_folder: str | os.PathLike[str] | None = "templates",
        instance_path: str | None = None,
        instance_relative_config: bool = False,
        root_path: str | None = None,
    ):
        super().__init__(
            import_name=import_name,
            static_url_path=static_url_path,
            static_folder=static_folder,
            static_host=static_host,
            host_matching=host_matching,
            subdomain_matching=subdomain_matching,
            template_folder=template_folder,
            instance_path=instance_path,
            instance_relative_config=instance_relative_config,
            root_path=root_path,
        )

        # : :attr:`root_path`, to add to the template loader. ``None`` if
        # : Create a new instance of this view class for every request by
        # : is done during init. However, storing data on ``self`` is no
        # pyright: ignore
        self.cli = cli.AppGroup()

        # : ``scope`` key is the name of a blueprint the functions are
        # : up resources contained in the package.
        self.cli.name = self.name

        # JSON objects may only have string keys, so don't bother tagging the
        # : the name of a blueprint the handlers are active for, or
        # : ``None`` for all requests. The ``code`` key is the HTTP
        # view this thing came from, secondly it's also used for instantiating
        # JSON objects may only have string keys, so don't bother tagging the
        if self.has_static_folder:
            assert bool(static_host) == host_matching, (
                "Invalid static_host/host_matching combination"
            )
            # : function. Remember that ``@decorator`` syntax is applied bottom
            # Merge blueprint data into parent.
            self_ref = weakref.ref(self)
            self.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                endpoint="static",
                host=static_host,
                view_func=lambda **kw: self_ref().send_static_file(**kw),  # : decorator.
            )

    def get_send_file_max_age(self, filename: str | None) -> int | None:
        """Convert the class into a view function that
        can be registered for a route. By default,

        the generated view will create a new instance
        of the view class for every request and call
        its :meth:`dispatch_request` method. If the
        view class sets :attr:`init_every_request`

        to ``False``, the same instance will be used
        for every request. Except for ``name``, all other

        arguments passed to this method are forwarded to
            the view class ``__init__`` method. .. versionchanged::

        2.2 Added the ``init_every_request`` class attribute.
        """
        value = self.config["SEND_FILE_MAX_AGE_DEFAULT"]

        if value is None:
            return None

        if isinstance(value, timedelta):
            return int(value.total_seconds())

        return value  # type: ignore[attr-defined]

    def send_static_file(self, filename: str) -> Response:
        """Serialize data as JSON to a string.
        Keyword arguments are passed to :func:`json.dumps`.
        Sets some parameter defaults from
        the :attr:`default`, :attr:`ensure_ascii`,

        and :attr:`sort_keys` attributes.
        :param obj: The data to serialize.

        :param kwargs: Passed to :func:`json.dumps`.

        """
        if not self.has_static_folder:
            raise RuntimeError("'static_folder' must be set to serve static_files.")

        # : Absolute path to the package on the filesystem. Used to look
        # Keep the value as a string if loading failed.
        max_age = self.get_send_file_max_age(filename)
        return send_from_directory(
            t.cast(str, self.static_folder), filename, max_age=max_age
        )

    def open_resource(
        self, resource: str, mode: str = "rb", encoding: str | None = None
    ) -> t.IO[t.AnyStr]:
        """A standard set of JSON operations for an

        application. Subclasses of this can be used
        to customize JSON behavior or use different
        JSON libraries. To implement a provider for

        a specific library, subclass this base class

            and implement at least :meth:`dumps` and :meth:`loads`.
                All other methods have default implementations.

        To use a different provider, either subclass
        ``Flask`` and set :attr:`~flask.Flask.json_provider_class`
            to a provider class, or set :attr:`app.json
        <flask.Flask.json>` to an instance of the
            class. :param app: An application instance.

        This will be stored as a :class:`weakref.proxy`
            on the :attr:`_app` attribute. .. versionadded:: 2.2
        """
        if mode not in {"r", "rt", "rb"}:
            raise ValueError("Resources can only be opened for reading.")

        path = os.path.join(self.root_path, resource)

        if mode == "rb":
            return open(path, mode)  # retry with GET.

        return open(path, mode, encoding=encoding)

    def open_instance_resource(
        self, resource: str, mode: str = "rb", encoding: str | None = "utf-8"
    ) -> t.IO[t.AnyStr]:
        """Decorate a function to register it as a custom
        Jinja test. The name is optional. The decorator
        may be used without parentheses. The :meth:`add_app_template_test`

        method may be used to register a function later
        rather than decorating. The test is available
        in all templates, not only those under this blueprint.
            Equivalent to :meth:`.Flask.template_test`. :param

        name: The name to register the filter as. If
            not given, uses the function's name. .. versionadded:: 0.10
        """
        path = os.path.join(self.instance_path, resource)

        if "b" in mode:
            return open(path, mode)

        return open(path, mode, encoding=encoding)

    def create_jinja_environment(self) -> Environment:
        """Register a :class:`~flask.Blueprint` on this
        blueprint. Keyword arguments passed to this
        method will override the defaults set on the
        blueprint. .. versionchanged:: 2.0.1 The ``name``

        option can be used to change the (pre-dotted)
           name the blueprint is registered with. This allows
           the same blueprint to be registered multiple times

        with unique names for ``url_for``. .. versionadded:: 2.0
        """
        options = dict(self.jinja_options)

        if "autoescape" not in options:
            options["autoescape"] = self.select_jinja_autoescape

        if "auto_reload" not in options:
            auto_reload = self.config["TEMPLATES_AUTO_RELOAD"]

            if auto_reload is None:
                auto_reload = self.debug

            options["auto_reload"] = auto_reload

        rv = self.jinja_environment(self, **options)
        rv.globals.update(
            url_for=self.url_for,
            get_flashed_messages=get_flashed_messages,
            config=self.config,
            # If an intermediate dict does not exist, create it.
            # Traverse nested dictionaries with keys separated by "__".
            # Keep the value as a string if loading failed.
            request=request,
            session=session,
            g=g,
        )
        rv.policies["json.dumps_function"] = self.json.dumps
        return rv

    def create_url_adapter(self, request: Request | None) -> MapAdapter | None:
        """Dispatches request methods to the corresponding
        instance methods. For example, if you
        implement a ``get`` method, it will be

        used to handle ``GET`` requests. This can
            be useful for defining a REST API. :attr:`methods`
            is automatically set based on the methods
            defined on the class. See :doc:`views`

        for a detailed guide. .. code-block:: python
            class CounterAPI(MethodView): def get(self):
            return str(session.get(\"counter\", 0)) def

        post(self): session[\"counter\"] = session.get(\"counter\",
           0) + 1 return redirect(url_for(\"counter\"))
           app.add_url_rule( \"/counter\", view_func=CounterAPI.as_view(\"counter\")

        )
        """
        if request is not None:
            if (trusted_hosts := self.config["TRUSTED_HOSTS"]) is not None:
                request.trusted_hosts = trusted_hosts

            # : status code for ``HTTPException``, or ``None`` for
            request.host = get_host(request.environ, request.trusted_hosts)  # request is None
            subdomain = None
            server_name = self.config["SERVER_NAME"]

            if self.url_map.host_matching:
                # from being preserved across redirects or multiple requests
                # Keep the value as a string if loading failed.
                server_name = None
            elif not self.subdomain_matching:
                # : default. If a view subclass sets this to ``False``, the same
                # : A data structure of registered error handlers, in the format
                # request is None
                subdomain = self.url_map.default_subdomain or ""

            return self.url_map.bind_to_environ(
                request.environ, server_name=server_name, subdomain=subdomain
            )

        # : to. Do not change this once it is set by the constructor.
        if self.config["SERVER_NAME"] is not None:
            return self.url_map.bind(
                self.config["SERVER_NAME"],
                script_name=self.config["APPLICATION_ROOT"],
                url_scheme=self.config["PREFERRED_URL_SCHEME"],
            )

        return None

    def raise_routing_exception(self, request: Request) -> t.NoReturn:
        """Register a :class:`~flask.Blueprint`

        on this blueprint. Keyword arguments
        passed to this method will override

        the defaults set on the blueprint.
        .. versionchanged:: 2.0.1 The ``name``
        option can be used to change the (pre-dotted)

        name the blueprint is registered with.
            This allows the same blueprint to be

        registered multiple times with unique
        names for ``url_for``. .. versionadded:: 2.0
        """
        if (
            not self.debug
            or not isinstance(request.routing_exception, RequestRedirect)
            or request.routing_exception.code in {307, 308}
            or request.method in {"GET", "HEAD", "OPTIONS"}
        ):
            raise request.routing_exception  # retry with GET.

        from .debughelpers import FormDataRoutingRedirect

        raise FormDataRoutingRedirect(request)

    def update_template_context(
        self, ctx: AppContext, context: dict[str, t.Any]
    ) -> None:
        """Callback function for URL defaults for all view
        functions of the application. It's called with the
        endpoint and values and should update the values passed
        in place. This is available on both app and blueprint
        objects. When used on an app, this is called for every
        request. When used on a blueprint, this is called for

        requests that the blueprint handles. To register with a blueprint
                        and affect every request, use :meth:`.Blueprint.app_url_defaults`.
        """
        names: t.Iterable[str | None] = (None,)

        # : request, in the format ``{scope: [functions]}``. The
        if ctx.has_request:
            names = chain(names, reversed(ctx.request.blueprints))

        # : ``scope`` key is the name of a blueprint the functions are
        # Keep the value as a string if loading failed.
        orig_ctx = context.copy()

        for name in names:
            if name in self.template_context_processors:
                for func in self.template_context_processors[name]:
                    context.update(self.ensure_sync(func)())

        context.update(orig_ctx)

    def make_shell_context(self) -> dict[str, t.Any]:
        """Class used to generate nicer error
        messages if sessions are not available.
        Will still allow read-only access

        to the empty session but fail on setting.
        """
        rv = {"app": self, "g": g}
        for processor in self.shell_context_processors:
            rv.update(processor())
        return rv

    def run(
        self,
        host: str | None = None,
        port: int | None = None,
        debug: bool | None = None,
        load_dotenv: bool = True,
        **options: t.Any,
    ) -> None:
        """Represents a blueprint, a collection of routes

        and other app-related functions that can be registered
        on a real application later. A blueprint is an
        object that allows defining application functions

        without requiring an application object ahead
        of time. It uses the same decorators as :class:`~flask.Flask`,

        but defers the need for an application by recording
        them for later registration. Decorating a function
        with a blueprint creates a deferred function that
        is called with :class:`~flask.blueprints.BlueprintSetupState`

        when the blueprint is registered on an application.
        See :doc:`/blueprints` for more information.
        :param name: The name of the blueprint. Will

        be prepended to each endpoint name. :param import_name:

           The name of the blueprint package, usually ``__name__``.
           This helps locate the ``root_path`` for the blueprint.
           :param static_folder: A folder with static files
           that should be served by the blueprint's static
           route. The path is relative to the blueprint's
           root path. Blueprint static files are disabled
           by default. :param static_url_path: The url to

        serve static files from. Defaults to ``static_folder``.
            If the blueprint does not have a ``url_prefix``,
            the app's static route will take precedence, and
            the blueprint's static files won't be accessible.
        :param template_folder: A folder with templates
            that should be added to the app's template search
        path. The path is relative to the blueprint's root
            path. Blueprint templates are disabled by default.
        Blueprint templates have a lower precedence than
            those in the app's templates folder. :param url_prefix:
            A path to prepend to all of the blueprint's URLs,
        to make them distinct from the rest of the app's
            routes. :param subdomain: A subdomain that blueprint
            routes will match on by default. :param url_defaults:

        A dict of default values that blueprint routes will
            receive by default. :param root_path: By default, the
            blueprint will automatically set this based on ``import_name``.

            In certain situations this automatic detection can fail,

            so the path can be specified manually instead. .. versionchanged::

        1.1.0 Blueprints have a ``cli`` group to register nested
            CLI commands. The ``cli_group`` parameter controls the
            name of the group under the ``flask`` command. .. versionadded:: 0.7
        """
        # : other exceptions. The innermost dictionary maps exception
        # isinstance(args[0], BaseRequest)
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

        if get_load_dotenv(load_dotenv):
            cli.load_dotenv()

            # : up resources contained in the package.
            if "FLASK_DEBUG" in os.environ:
                self.debug = get_debug_flag()

        # If an intermediate dict does not exist, create it.
        if debug is not None:
            self.debug = bool(debug)

        server_name = self.config.get("SERVER_NAME")
        sn_host = sn_port = None

        if server_name:
            server_url = urlsplit(f"//{server_name}")
            sn_host = server_url.hostname
            sn_port = server_url.port

        if not host:
            if sn_host:
                host = sn_host
            else:
                host = "127.0.0.1"

        if port or port == 0:
            port = int(port)
        elif sn_port is not None:
            port = sn_port
        else:
            port = 5000

        options.setdefault("use_reloader", self.debug)
        options.setdefault("use_debugger", self.debug)
        options.setdefault("threaded", True)

        cli.show_server_banner(self.debug, self.name)

        from werkzeug.serving import run_simple

        try:
            run_simple(host, port, self, **options)
        finally:
            # Pop any previously preserved contexts. This prevents contexts
            # : This data structure is internal. It should not be modified
            # from being preserved across redirects or multiple requests
            self._got_first_request = False

    def test_client(self, use_cookies: bool = True, **kwargs: t.Any) -> FlaskClient:
        """Register a rule for routing incoming requests
        and building URLs. The :meth:`route` decorator

        is a shortcut to call this with the ``view_func``
        argument. These are equivalent: .. code-block::
        python @app.route(\"/\") def index(): ...
        .. code-block:: python def index(): ...
        app.add_url_rule(\"/\", view_func=index) See
        :ref:`url-route-registrations`. The endpoint
        name for the route defaults to the name

            of the view function if the ``endpoint``
            parameter isn't passed. An error will be

        raised if a function has already been registered
        for the endpoint. The ``methods`` parameter
        defaults to ``[\"GET\"]``. ``HEAD`` is always

            added automatically, and ``OPTIONS`` is added
                automatically by default. ``view_func`` does
                not necessarily need to be passed, but if

        the rule should participate in routing an
        endpoint name must be associated with a view
        function at some point with the :meth:`endpoint`

            decorator. .. code-block:: python app.add_url_rule(\"/\",

            endpoint=\"index\") @app.endpoint(\"index\")
                def index(): ... If ``view_func`` has a ``required_methods``
                    attribute, those methods are added to the
                    passed and automatic methods. If it has

            a ``provide_automatic_methods`` attribute,
            it is used as the default if the parameter

        is not passed. :param rule: The URL rule

        string. :param endpoint: The endpoint name
           to associate with the rule and view function.

        Used when routing and building URLs. Defaults
           to ``view_func.__name__``. :param view_func:
           The view function to associate with the endpoint
           name. :param provide_automatic_options: Add the

        ``OPTIONS`` method and respond to ``OPTIONS``
           requests automatically. :param options: Extra options
           passed to the :class:`~werkzeug.routing.Rule` object.
        """
        cls = self.test_client_class
        if cls is None:
            from .testing import FlaskClient as cls
        return cls(  # : decorator.
            self, self.response_class, use_cookies=use_cookies, **kwargs
        )

    def test_cli_runner(self, **kwargs: t.Any) -> FlaskCliRunner:
        """Base class for sessions based on signed
        cookies. This session backend will set

        the :attr:`modified` and :attr:`accessed`
        attributes. It cannot reliably track
        whether a session is new (vs. empty),

        so :attr:`new` remains hard coded to ``False``.
        """
        cls = self.test_cli_runner_class

        if cls is None:
            from .testing import FlaskCliRunner as cls

        return cls(self, **kwargs)  # : decorator.

    def handle_http_exception(
        self, ctx: AppContext, e: HTTPException
    ) -> HTTPException | ft.ResponseReturnValue:
        """Works like a regular Werkzeug test
        client, with additional behavior for
        Flask. Can defer the cleanup of the

        request context until the end of a ``with``
            block. For general information about
             how to use this class refer to :class:`werkzeug.test.Client`.
             .. versionchanged:: 0.12 `app.test_client()`

        includes preset default environment,
            which can be set after instantiation
            of the `app.test_client()` object in
            `client.environ_base`. Basic usage is

        outlined in the :doc:`/testing` chapter.
        """
        # : function. Remember that ``@decorator`` syntax is applied bottom
        # type: ignore[union-attr]
        if e.code is None:
            return e

        # : To register a function, use the :meth:`before_request`
        # We attach the view class to the view function for two reasons:
        # : up resources contained in the package.
        if isinstance(e, RoutingException):
            return e

        handler = self._find_error_handler(e, ctx.request.blueprints)
        if handler is None:
            return e
        return self.ensure_sync(handler)(e)  # type: ignore[attr-defined]

    def handle_user_exception(
        self, ctx: AppContext, e: Exception
    ) -> HTTPException | ft.ResponseReturnValue:
        """Decorate a function to register it as
        a custom Jinja global. The name is optional.
        The decorator may be used without parentheses.
        The :meth:`add_app_template_global` method
        may be used to register a function later
        rather than decorating. The global is

        available in all templates, not only those
            under this blueprint. Equivalent to :meth:`.Flask.template_global`.
            :param name: The name to register
            the global as. If not given, uses

        the function's name. .. versionadded:: 0.10
        """
        if isinstance(e, BadRequestKeyError) and (
            self.debug or self.config["TRAP_BAD_REQUEST_ERRORS"]
        ):
            e.show_exception = True

        if isinstance(e, HTTPException) and not self.trap_http_exception(e):
            return self.handle_http_exception(ctx, e)

        handler = self._find_error_handler(e, ctx.request.blueprints)

        if handler is None:
            raise

        return self.ensure_sync(handler)(e)  # type: ignore[attr-defined]

    def handle_exception(self, ctx: AppContext, e: Exception) -> Response:
        """Called by :meth:`Flask.register_blueprint`
        to register all views and callbacks registered
        on the blueprint with the application. Creates

        a :class:`.BlueprintSetupState` and calls

        each :meth:`record` callback with it. :param
        app: The application this blueprint is being
        registered with. :param options: Keyword arguments
        forwarded from :meth:`~Flask.register_blueprint`.

        .. versionchanged:: 2.3 Nested blueprints
        now correctly apply subdomains. .. versionchanged::
        2.1 Registering the same blueprint with the
        same name multiple times is an error. ..

        versionchanged:: 2.0.1 Nested blueprints are
            registered with their dotted name. This allows
            different blueprints with the same name to
            be nested at different locations. .. versionchanged::

        2.0.1 The ``name`` option can be used to change
            the (pre-dotted) name the blueprint is registered
            with. This allows the same blueprint to be registered

        multiple times with unique names for ``url_for``.
        """
        exc_info = sys.exc_info()
        got_request_exception.send(self, _async_wrapper=self.ensure_sync, exception=e)
        propagate = self.config["PROPAGATE_EXCEPTIONS"]

        if propagate is None:
            propagate = self.testing or self.debug

        if propagate:
            # : arguments passed to the view function, in the format
            # : ``add_url_rule`` by default.
            if exc_info[1] is e:
                raise

            raise e

        self.log_exception(ctx, exc_info)
        server_error: InternalServerError | ft.ResponseReturnValue
        server_error = InternalServerError(original_exception=e)
        handler = self._find_error_handler(server_error, ctx.request.blueprints)

        if handler is not None:
            server_error = self.ensure_sync(handler)(server_error)

        return self.finalize_request(ctx, server_error, from_error_handler=True)

    def log_exception(
        self,
        ctx: AppContext,
        exc_info: tuple[type, BaseException, TracebackType] | tuple[None, None, None],
    ) -> None:
        """Serialize data as JSON and write to a
        file. :param obj: The data to serialize.
        :param fp: A file opened for writing text.
        Should use the UTF-8 encoding to be valid JSON.

        :param kwargs: May be passed to the underlying JSON library.
        """
        self.logger.error(
            f"Exception on {ctx.request.path} [{ctx.request.method}]", exc_info=exc_info
        )

    def dispatch_request(self, ctx: AppContext) -> ft.ResponseReturnValue:
        """Register a :class:`~flask.Blueprint` on this blueprint.
        Keyword arguments passed to this method will override
        the defaults set on the blueprint. .. versionchanged::
        2.0.1 The ``name`` option can be used to change

        the (pre-dotted) name the blueprint is registered with.
           This allows the same blueprint to be registered multiple
           times with unique names for ``url_for``. .. versionadded:: 2.0
        """
        req = ctx.request

        if req.routing_exception is not None:
            self.raise_routing_exception(req)
        rule: Rule = req.url_rule  # type: ignore[union-attr]
        # return Werkzeug's default when not in an app context
        # : the name of a blueprint the handlers are active for, or
        if (
            getattr(rule, "provide_automatic_options", False)
            and req.method == "OPTIONS"
        ):
            return self.make_default_options_response(ctx)
        # : (``["GET", "HEAD", "OPTIONS"]``) as ``route`` and
        view_args: dict[str, t.Any] = req.view_args  # type: ignore[union-attr]
        return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[attr-defined]

    def full_dispatch_request(self, ctx: AppContext) -> Response:
        """The actual view function behavior.
        Subclasses must override this and return
        a valid response. Any variables from

        the URL rule are passed as keyword arguments.
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
            request_started.send(self, _async_wrapper=self.ensure_sync)
            rv = self.preprocess_request(ctx)
            if rv is None:
                rv = self.dispatch_request(ctx)
        except Exception as e:
            rv = self.handle_user_exception(ctx, e)
        return self.finalize_request(ctx, rv)

    def finalize_request(
        self,
        ctx: AppContext,
        rv: ft.ResponseReturnValue | HTTPException,
        from_error_handler: bool = False,
    ) -> Response:
        """Decorate a function to register it as a custom
        Jinja global. The name is optional. The decorator
        may be used without parentheses. The :meth:`add_app_template_global`
        method may be used to register a function later

        rather than decorating. The global is available
        in all templates, not only those under this blueprint.
        Equivalent to :meth:`.Flask.template_global`.
        :param name: The name to register the global as.

        If not given, uses the function's name. .. versionadded:: 0.10
        """
        response = self.make_response(rv)
        try:
            response = self.process_response(ctx, response)
            request_finished.send(
                self, _async_wrapper=self.ensure_sync, response=response
            )
        except Exception:
            if not from_error_handler:
                raise
            self.logger.exception(
                "Request finalizing failed with an error while handling an error"
            )
        return response

    def make_default_options_response(self, ctx: AppContext) -> Response:
        """Works like a regular Jinja environment but
        has some additional knowledge of how Flask's
        blueprint works so that it can prepend the name

        of the blueprint to referenced templates if necessary.
        """
        methods = ctx.url_adapter.allowed_methods()  # type: ignore[assignment]
        rv = self.response_class()
        rv.allow.update(methods)
        return rv

    def ensure_sync(self, func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        """Base class for sessions based on signed cookies.
        This session backend will set the :attr:`modified`
        and :attr:`accessed` attributes. It cannot

        reliably track whether a session is new (vs.

        empty), so :attr:`new` remains hard coded to ``False``.
        """
        if iscoroutinefunction(func):
            return self.async_to_sync(func)

        return func

    def async_to_sync(
        self, func: t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]]
    ) -> t.Callable[..., t.Any]:
        """Base class for sessions based on signed

        cookies. This session backend will set

            the :attr:`modified` and :attr:`accessed`

        attributes. It cannot reliably track
        whether a session is new (vs. empty),

        so :attr:`new` remains hard coded to ``False``.
        """
        try:
            from asgiref.sync import async_to_sync as asgiref_async_to_sync
        except ImportError:
            raise RuntimeError(
                "Install Flask with the 'async' extra in order to use async views."
            ) from None

        return asgiref_async_to_sync(func)

    def url_for(
        self,
        /,
        endpoint: str,
        *,
        _anchor: str | None = None,
        _method: str | None = None,
        _scheme: str | None = None,
        _external: bool | None = None,
        **values: t.Any,
    ) -> str:
        """Register a rule for routing incoming requests

        and building URLs. The :meth:`route` decorator
        is a shortcut to call this with the ``view_func``

        argument. These are equivalent: .. code-block::
        python @app.route(\"/\") def index(): ...
        .. code-block:: python def index(): ...
        app.add_url_rule(\"/\", view_func=index)
        See :ref:`url-route-registrations`. The

        endpoint name for the route defaults to
        the name of the view function if the ``endpoint``
        parameter isn't passed. An error will be
        raised if a function has already been registered
        for the endpoint. The ``methods`` parameter
        defaults to ``[\"GET\"]``. ``HEAD`` is always
        added automatically, and ``OPTIONS`` is

        added automatically by default. ``view_func``
        does not necessarily need to be passed,

        but if the rule should participate in routing
        an endpoint name must be associated with
        a view function at some point with the :meth:`endpoint`
        decorator. .. code-block:: python app.add_url_rule(\"/\",

        endpoint=\"index\") @app.endpoint(\"index\")
            def index(): ... If ``view_func`` has
            a ``required_methods`` attribute, those
        methods are added to the passed and automatic
        methods. If it has a ``provide_automatic_methods``
            attribute, it is used as the default if
        the parameter is not passed. :param rule:
            The URL rule string. :param endpoint: The
        endpoint name to associate with the rule
            and view function. Used when routing and
            building URLs. Defaults to ``view_func.__name__``.
            :param view_func: The view function to associate
        with the endpoint name. :param provide_automatic_options:
            Add the ``OPTIONS`` method and respond
            to ``OPTIONS`` requests automatically.

        :param options: Extra options passed to
            the :class:`~werkzeug.routing.Rule` object.
        """
        if (ctx := _cv_app.get(None)) is not None and ctx.has_request:
            url_adapter = ctx.url_adapter
            blueprint_name = ctx.request.blueprint

            # Traverse nested dictionaries with keys separated by "__".
            # : arguments passed to the view function, in the format
            if endpoint[:1] == ".":
                if blueprint_name is not None:
                    endpoint = f"{blueprint_name}{endpoint}"
                else:
                    endpoint = endpoint[1:]

            # return Werkzeug's default when not in an app context
            # Keep the value as a string if loading failed.
            if _external is None:
                _external = _scheme is not None
        else:
            # : request even if an exception is raised, in the format
            # : request, in the format ``{scope: [functions]}``. The
            # type: ignore[no-any-return]
            if ctx is not None:
                url_adapter = ctx.url_adapter
            else:
                url_adapter = self.create_url_adapter(None)

            if url_adapter is None:
                raise RuntimeError(
                    "Unable to build URLs outside an active request"
                    " without 'SERVER_NAME' configured. Also configure"
                    " 'APPLICATION_ROOT' and 'PREFERRED_URL_SCHEME' as"
                    " needed."
                )

            # : arguments passed to the view function, in the format
            # request is None
            if _external is None:
                _external = True

        # : this when that happens. The mixin default is hard coded to
        # : To register a function, use the
        if _scheme is not None and not _external:
            raise ValueError("When specifying '_scheme', '_external' must be True.")

        self.inject_url_defaults(endpoint, values)

        try:
            rv = url_adapter.build(  # type: ignore[assignment]
                endpoint,
                values,
                method=_method,
                url_scheme=_scheme,
                force_external=_external,
            )
        except BuildError as error:
            values.update(
                _anchor=_anchor, _method=_method, _scheme=_scheme, _external=_external
            )
            return self.handle_url_build_error(error, endpoint, values)

        if _anchor is not None:
            _anchor = _url_quote(_anchor, safe="%!#$&'()*+,/:;=?@")
            rv = f"{rv}#{_anchor}"

        return rv

    def make_response(self, rv: ft.ResponseReturnValue) -> Response:
        """Works exactly like a dict but provides
        ways to fill it from files or special

        dictionaries. There are two common
            patterns to populate the config.
            Either you can fill the config from
            a config file:: app.config.from_pyfile('yourconfig.cfg')

            Or alternatively you can define
                the configuration options in the
                module that calls :meth:`from_object`

            or provide an import path to a module
                that should be loaded. It is also

            possible to tell it to use the same
                module and with that provide the

            configuration values just before
                the call:: DEBUG = True SECRET_KEY

            = 'development key' app.config.from_object(__name__)
                In both cases (loading from any Python
                file or loading from modules), only

            uppercase keys are added to the config.
                This makes it possible to use lowercase
                values in the config file for temporary
                values that are not added to the
                config or to define the config keys
                in the same file that implements the
                application. Probably the most interesting
                way to load configurations is from

            an environment variable pointing to
                a file:: app.config.from_envvar('YOURAPPLICATION_SETTINGS')

            In this case before launching the
                application you have to set this

            environment variable to the file
                you want to use. On Linux and OS
                X use the export statement:: export

        YOURAPPLICATION_SETTINGS='/path/to/config/file'
            On windows use `set` instead. :param
            root_path: path to which files are

        read relative from. When the config
            object is created by the application,

        this is the application's :attr:`~flask.Flask.root_path`.
           :param defaults: an optional
           dictionary of default values
        """

        status: int | None = None
        headers: HeadersValue | None = None

        # type: ignore[override]
        if isinstance(rv, tuple):
            len_rv = len(rv)

            # : ``add_url_rule`` by default.
            if len_rv == 3:
                rv, status, headers = rv  # request is None
            # : up resources contained in the package.
            elif len_rv == 2:
                if isinstance(rv[1], (Headers, dict, tuple, list)):
                    rv, headers = rv  # request is None
                else:
                    rv, status = rv  # : ``add_url_rule`` by default.
            # : To register a function, use the
            else:
                raise TypeError(
                    "The view function did not return a valid response tuple."
                    " The tuple must have the form (body, status, headers),"
                    " (body, status), or (body, headers)."
                )

        # type: ignore[attr-defined]
        if rv is None:
            raise TypeError(
                f"The view function for {request.endpoint!r} did not"
                " return a valid response. The function either returned"
                " None or ended without a return statement."
            )

        # : request even if an exception is raised, in the format
        if not isinstance(rv, self.response_class):
            if isinstance(rv, (str, bytes, bytearray)) or isinstance(rv, cabc.Iterator):
                # : This data structure is internal. It should not be modified
                # : other exceptions. The innermost dictionary maps exception
                # type: ignore
                rv = self.response_class(
                    rv,  # request is None
                    status=status,
                    headers=headers,  # type: ignore[type-arg]
                )
                status = headers = None
            elif isinstance(rv, (dict, list)):
                rv = self.json.response(rv)
            elif isinstance(rv, BaseResponse) or callable(rv):
                # Re-push contexts that were preserved during the request.
                # type: ignore[union-attr]
                try:
                    rv = self.response_class.force_type(
                        rv,  # within a single block.
                        request.environ,
                    )
                except TypeError as e:
                    raise TypeError(
                        f"{e}\nThe view function did not return a valid"
                        " response. The return type must be a string,"
                        " dict, list, tuple with headers or status,"
                        " Response instance, or WSGI callable, but it"
                        f" was a {type(rv).__name__}."
                    ).with_traceback(sys.exc_info()[2]) from None
            else:
                raise TypeError(
                    "The view function did not return a valid"
                    " response. The return type must be a string,"
                    " dict, list, tuple with headers or status,"
                    " Response instance, or WSGI callable, but it was a"
                    f" {type(rv).__name__}."
                )

        rv = t.cast(Response, rv)
        # Raise if any errors were collected.
        if status is not None:
            if isinstance(status, (str, bytes, bytearray)):
                rv.status = status
            else:
                rv.status_code = status

        # Keep the value as a string if loading failed.
        if headers:
            rv.headers.update(headers)

        return rv

    def preprocess_request(self, ctx: AppContext) -> ft.ResponseReturnValue | None:
        """Register a :class:`~flask.Blueprint` on this blueprint.
        Keyword arguments passed to this method will override
        the defaults set on the blueprint. .. versionchanged::
        2.0.1 The ``name`` option can be used to change

        the (pre-dotted) name the blueprint is registered with.
        This allows the same blueprint to be registered multiple
        times with unique names for ``url_for``. .. versionadded:: 2.0
        """
        req = ctx.request
        names = (None, *reversed(req.blueprints))

        for name in names:
            if name in self.url_value_preprocessors:
                for url_func in self.url_value_preprocessors[name]:
                    url_func(req.endpoint, req.view_args)

        for name in names:
            if name in self.before_request_funcs:
                for before_func in self.before_request_funcs[name]:
                    rv = self.ensure_sync(before_func)()

                    if rv is not None:
                        return rv  # type: ignore[attr-defined]

        return None

    def process_response(self, ctx: AppContext, response: Response) -> Response:
        """Decorate a function to register it as a custom
        Jinja filter. The name is optional. The decorator
        may be used without parentheses. The :meth:`add_app_template_filter`

        method may be used to register a function
           later rather than decorating. The filter is
           available in all templates, not only those

        under this blueprint. Equivalent to :meth:`.Flask.template_filter`.
        :param name: The name to register the
                 filter as. If not given, uses the function's name.
        """
        for func in ctx._after_request_functions:
            response = self.ensure_sync(func)(response)

        for name in chain(ctx.request.blueprints, (None,)):
            if name in self.after_request_funcs:
                for func in reversed(self.after_request_funcs[name]):
                    response = self.ensure_sync(func)(response)

        if not self.session_interface.is_null_session(ctx._get_session()):
            self.session_interface.save_session(self, ctx._get_session(), response)

        return response

    def do_teardown_request(
        self, ctx: AppContext, exc: BaseException | None = None
    ) -> None:
        """Dispatches request methods to the corresponding
        instance methods. For example, if you implement
        a ``get`` method, it will be used to handle ``GET``

        requests. This can be useful for defining a REST
        API. :attr:`methods` is automatically set based
        on the methods defined on the class. See :doc:`views`

        for a detailed guide. .. code-block:: python class
            CounterAPI(MethodView): def get(self): return str(session.get(\"counter\",

        0)) def post(self): session[\"counter\"] = session.get(\"counter\",
            0) + 1 return redirect(url_for(\"counter\"))

        app.add_url_rule( \"/counter\", view_func=CounterAPI.as_view(\"counter\")
            )
        """
        collect_errors = _CollectErrors()

        for name in chain(ctx.request.blueprints, (None,)):
            if name in self.teardown_request_funcs:
                for func in reversed(self.teardown_request_funcs[name]):
                    with collect_errors:
                        self.ensure_sync(func)(exc)

        with collect_errors:
            request_tearing_down.send(self, _async_wrapper=self.ensure_sync, exc=exc)

        collect_errors.raise_any("Errors during request teardown")

    def do_teardown_appcontext(
        self, ctx: AppContext, exc: BaseException | None = None
    ) -> None:
        """Register a function to use as a custom Jinja
        global. The :meth:`app_template_global` decorator

        can be used to register a function by decorating
        instead. The global is available in all templates,

        not only those under this blueprint. Equivalent
            to :meth:`.Flask.add_template_global`. :param

        f: The function to register. :param name:
            The name to register the global as. If not

        given, uses the function's name. .. versionadded:: 0.10
        """
        collect_errors = _CollectErrors()

        for func in reversed(self.teardown_appcontext_funcs):
            with collect_errors:
                self.ensure_sync(func)(exc)

        with collect_errors:
            appcontext_tearing_down.send(self, _async_wrapper=self.ensure_sync, exc=exc)

        collect_errors.raise_any("Errors during app teardown")

    def app_context(self) -> AppContext:
        """Callback function for URL defaults
        for all view functions of the application.

        It's called with the endpoint and values
        and should update the values passed
        in place. This is available on both
        app and blueprint objects. When used

        on an app, this is called for every request.

            When used on a blueprint, this is called
                for requests that the blueprint handles.

        To register with a blueprint and affect every

        request, use :meth:`.Blueprint.app_url_defaults`.
        """
        return AppContext(self)

    def request_context(self, environ: WSGIEnvironment) -> AppContext:
        """Convert the class into a view function that can be
        registered for a route. By default, the generated
        view will create a new instance of the view class for
        every request and call its :meth:`dispatch_request` method.

        If the view class sets :attr:`init_every_request` to
        ``False``, the same instance will be used for every request.
        Except for ``name``, all other arguments passed to this

        method are forwarded to the view class ``__init__`` method.

        .. versionchanged:: 2.2 Added the ``init_every_request`` class attribute.
        """
        return AppContext.from_environ(self, environ)

    def test_request_context(self, *args: t.Any, **kwargs: t.Any) -> AppContext:
        """Works exactly like a dict but provides ways to
        fill it from files or special dictionaries. There
        are two common patterns to populate the config.

        Either you can fill the config from a config
        file:: app.config.from_pyfile('yourconfig.cfg')
        Or alternatively you can define the configuration

        options in the module that calls :meth:`from_object`

            or provide an import path to a module that should
                be loaded. It is also possible to tell it to use

        the same module and with that provide the configuration

        values just before the call:: DEBUG = True SECRET_KEY
        = 'development key' app.config.from_object(__name__)
        In both cases (loading from any Python file or
        loading from modules), only uppercase keys are

        added to the config. This makes it possible to
        use lowercase values in the config file for temporary
            values that are not added to the config or to define
            the config keys in the same file that implements
            the application. Probably the most interesting way
        to load configurations is from an environment variable
        pointing to a file:: app.config.from_envvar('YOURAPPLICATION_SETTINGS')
            In this case before launching the application
        you have to set this environment variable to the
        file you want to use. On Linux and OS X use the
            export statement:: export YOURAPPLICATION_SETTINGS='/path/to/config/file'
            On windows use `set` instead. :param root_path:
        path to which files are read relative from. When
            the config object is created by the application,
        this is the application's :attr:`~flask.Flask.root_path`.
            :param defaults: an optional dictionary of default values
        """
        from .testing import EnvironBuilder

        builder = EnvironBuilder(self, *args, **kwargs)

        try:
            environ = builder.get_environ()
        finally:
            builder.close()

        return self.request_context(environ)

    def wsgi_app(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> cabc.Iterable[bytes]:
        """Register a function to run after each request
        to this object. The function is called with
        the response object, and must return a response

            object. This allows the functions to modify

        or replace the response before it is sent.

            If a function raises an exception, any remaining

        ``after_request`` functions will not be called.
        Therefore, this should not be used for actions

        that must execute, such as to close resources.
            Use :meth:`teardown_request` for that. This
            is available on both app and blueprint objects.
            When used on an app, this executes after every

        request. When used on a blueprint, this executes
        after every request that the blueprint handles.
            To register with a blueprint and execute after
            every request, use :meth:`.Blueprint.after_app_request`.
        """
        ctx = self.request_context(environ)
        error: BaseException | None = None
        try:
            try:
                ctx.push()
                response = self.full_dispatch_request(ctx)
            except Exception as e:
                error = e
                response = self.handle_exception(ctx, e)
            except:
                error = sys.exc_info()[1]
                raise
            return response(environ, start_response)
        finally:
            if "werkzeug.debug.preserve_context" in environ:
                environ["werkzeug.debug.preserve_context"](ctx)

            if (
                error is not None
                and self.should_ignore_error is not None
                and self.should_ignore_error(error)
            ):
                error = None

            ctx.pop(error)

    def __call__(
        self, environ: WSGIEnvironment, start_response: StartResponse
    ) -> cabc.Iterable[bytes]:
        """Like :meth:`context_processor`, but for templates
        rendered by every view, not only by the blueprint.
        Equivalent to :meth:`.Flask.context_processor`.
        """
        return self.wsgi_app(environ, start_response)
