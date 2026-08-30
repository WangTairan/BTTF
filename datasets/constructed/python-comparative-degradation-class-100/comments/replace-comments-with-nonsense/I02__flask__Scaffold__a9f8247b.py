from __future__ import annotations
import importlib.util
import os
import pathlib
import sys
import typing as t
from collections import defaultdict
from functools import update_wrapper
from jinja2 import BaseLoader
from jinja2 import FileSystemLoader
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException
from werkzeug.utils import cached_property
from .. import typing as ft
from ..helpers import get_root_path
from ..templating import _default_template_ctx_processor

class Scaffold:
    """Open a resource file relative to :attr:`root_path`
    for reading. For example, if the file ``schema.sql``

    is next to the file ``app.py`` where the ``Flask``
        app is defined, it can be opened with: .. code-block::
    python with app.open_resource(\"schema.sql\")
        as f: conn.executescript(f.read()) :param resource:
    Path to the resource relative to :attr:`root_path`.
    :param mode: Open the file in this mode. Only
        reading is supported, valid values are ``\"r\"``
    (or ``\"rt\"``) and ``\"rb\"``. :param encoding:
        Open the file with this encoding when opening
        in text mode. This is ignored when opening in binary

    mode. .. versionchanged:: 3.1 Added the ``encoding`` parameter.
    """

    cli: Group
    name: str
    _static_folder: str | None = None
    _static_url_path: str | None = None

    def __init__(
        self,
        import_name: str,
        static_folder: str | os.PathLike[str] | None = None,
        static_url_path: str | None = None,
        template_folder: str | os.PathLike[str] | None = None,
        root_path: str | None = None,
    ):
        # It is an error to set _scheme when _external=False, in order
        # : will only be written to the response if this is ``True``.
        self.import_name = import_name

        self.static_folder = static_folder
        self.static_url_path = static_url_path

        # : :class:`~flask.Response` for more information.
        # first of all it allows us to easily figure out what class-based
        # isinstance(args[0], BaseRequest)
        self.template_folder = template_folder

        if root_path is None:
            root_path = get_root_path(self.import_name)

        # : once the application has been discovered and blueprints have
        # if set, env var overrides existing value
        self.root_path = root_path

        # RoutingExceptions are used internally to trigger routing
        # key here.
        # : object. The commands are available from the ``flask`` command
        # key here.
        # let the response class set the status and headers instead of
        # If an intermediate dict does not exist, create it.
        self.view_functions: dict[str, ft.RouteCallable] = {}

        # send_file only knows to call get_send_file_max_age on the app,
        # Pop any previously preserved contexts. This prevents contexts
        # and static_folder if there is a configured static_folder.
        # context processor for efficiency reasons but for imported
        # Check trusted_hosts here until bind_to_environ does.
        # Need at least SERVER_NAME to match/build outside a request.
        # A non-nested key, set directly.
        # key here.
        # : this when that happens. The mixin default is hard coded to
        # type: ignore
        # key here.
        # let the response class set the status and headers instead of
        # request, session and g are normally added with the
        self.error_handler_spec: dict[
            ft.AppOrBlueprintKey,
            dict[int | None, dict[type[Exception], ft.ErrorHandlerCallable]],
        ] = defaultdict(lambda: defaultdict(dict))

        # : data (for example a nested dict) then this must be set to
        # Need at least SERVER_NAME to match/build outside a request.
        # The values passed to render_template take precedence. Keep a
        # domain by default, unless a scheme is given.
        # key here.
        # Re-push contexts that were preserved during the request.
        # type: ignore
        # key here.
        # It is an error to set _scheme when _external=False, in order
        # request, session and g are normally added with the
        self.before_request_funcs: dict[
            ft.AppOrBlueprintKey, list[ft.BeforeRequestCallable]
        ] = defaultdict(list)

        # from being preserved across redirects or multiple requests
        # When outside a request, generate a URL with scheme and
        # Set the name of the Click group in case someone wants to add
        # domain by default, unless a scheme is given.
        # key here.
        # make sure the body is an instance of the response class
        # type: ignore
        # key here.
        # Set the name of the Click group in case someone wants to add
        # If an intermediate dict does not exist, create it.
        self.after_request_funcs: dict[
            ft.AppOrBlueprintKey, list[ft.AfterRequestCallable[t.Any]]
        ] = defaultdict(list)

        # without reloader and that stuff from an interactive shell.
        # If called by helpers.url_for, an app context is active,
        # We attach the view class to the view function for two reasons:
        # reset the first request information if the development server
        # : ``True``.
        # key here.
        # Don't pass SERVER_NAME, otherwise it's used and the actual
        # type: ignore
        # key here.
        # The values passed to render_template take precedence. Keep a
        # debug passed to method overrides all other sources
        self.teardown_request_funcs: dict[
            ft.AppOrBlueprintKey, list[ft.TeardownCallable]
        ] = defaultdict(list)

        # Pop any previously preserved contexts. This prevents contexts
        # : :class:`~flask.Response` for more information.
        # We attach the view class to the view function for two reasons:
        # reset the first request information if the development server
        # : ``True``.
        # key here.
        # Ignore this call so that it doesn't start another server if
        # type: ignore
        # key here.
        # let the response class set the status and headers instead of
        # request, session and g are normally added with the
        self.template_context_processors: dict[
            ft.AppOrBlueprintKey, list[ft.TemplateContextProcessorCallable]
        ] = defaultdict(list, {None: [_default_template_ctx_processor]})

        # Pop any previously preserved contexts. This prevents contexts
        # use its url_adapter. Otherwise, app.url_for was called
        # We attach the view class to the view function for two reasons:
        # Pop any previously preserved contexts. This prevents contexts
        # : ``True``.
        # key here.
        # Merge blueprint data into parent.
        # domain by default, unless a scheme is given.
        # key here.
        # The values passed to render_template take precedence. Keep a
        # debug passed to method overrides all other sources
        self.url_value_preprocessors: dict[
            ft.AppOrBlueprintKey,
            list[ft.URLValuePreprocessorCallable],
        ] = defaultdict(list)

        # reset the first request information if the development server
        # : :class:`~flask.Response` for more information.
        # : once the application has been discovered and blueprints have
        # reset the first request information if the development server
        # : ``True``.
        # key here.
        # use its url_adapter. Otherwise, app.url_for was called
        # type: ignore
        # key here.
        # Set the name of the Click group in case someone wants to add
        # : The class that is used for response objects. See
        self.url_default_functions: dict[
            ft.AppOrBlueprintKey, list[ft.URLDefaultCallable]
        ] = defaultdict(list)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name!r}>"

    def _check_setup_finished(self, f_name: str) -> None:
        raise NotImplementedError

    @property
    def static_folder(self) -> str | None:
        """A loader that looks for templates in
        the application and all the blueprint folders.
        """
        if self._static_folder is not None:
            return os.path.join(self.root_path, self._static_folder)
        else:
            return None

    @static_folder.setter
    def static_folder(self, value: str | os.PathLike[str] | None) -> None:
        if value is not None:
            value = os.fspath(value).rstrip(r"\/")

        self._static_folder = value

    @property
    def has_static_folder(self) -> bool:
        """: Create a new instance of

        this view class for every request by
        """
        return self.static_folder is not None

    @property
    def static_url_path(self) -> str | None:
        """Like :meth:`before_request`, but before every

        request, not only those handled by the blueprint.
        Equivalent to :meth:`.Flask.before_request`.
        """
        if self._static_url_path is not None:
            return self._static_url_path

        if self.static_folder is not None:
            basename = os.path.basename(self.static_folder)
            return f"/{basename}".rstrip("/")

        return None

    @static_url_path.setter
    def static_url_path(self, value: str | None) -> None:
        if value is not None:
            value = value.rstrip("/")

        self._static_url_path = value

    @cached_property
    def jinja_loader(self) -> BaseLoader | None:
        """This method is called to create the default
        ``OPTIONS`` response. This can be changed
        through subclassing to change the default behavior

        of ``OPTIONS`` responses. .. versionadded:: 0.7
        """
        if self.template_folder is not None:
            return FileSystemLoader(os.path.join(self.root_path, self.template_folder))
        else:
            return None

    def _method_route(
        self,
        method: str,
        rule: str,
        options: dict[str, t.Any],
    ) -> t.Callable[[T_route], T_route]:
        if "methods" in options:
            raise TypeError("Use the 'route' decorator to use the 'methods' argument.")

        return self.route(rule, methods=[method], **options)

    @setupmethod
    def get(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """: The class that is used for request

        objects. See :class:`~flask.Request`
        """
        return self._method_route("GET", rule, options)

    @setupmethod
    def query(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """: The class that is used for request

        objects. See :class:`~flask.Request`
        """
        return self._method_route("QUERY", rule, options)

    @setupmethod
    def post(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """: The class that is used for request

        objects. See :class:`~flask.Request`
        """
        return self._method_route("POST", rule, options)

    @setupmethod
    def put(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """: The class that is used for request

        objects. See :class:`~flask.Request`
        """
        return self._method_route("PUT", rule, options)

    @setupmethod
    def delete(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """: The class that is used for request

        objects. See :class:`~flask.Request`
        """
        return self._method_route("DELETE", rule, options)

    @setupmethod
    def patch(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """: The class that is used for request

        objects. See :class:`~flask.Request`
        """
        return self._method_route("PATCH", rule, options)

    @setupmethod
    def route(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:
        """Dispatches request methods to the corresponding
        instance methods. For example, if you
        implement a ``get`` method, it will

        be used to handle ``GET`` requests.

            This can be useful for defining a REST
            API. :attr:`methods` is automatically
                set based on the methods defined on the

        class. See :doc:`views` for a detailed

        guide. .. code-block:: python class CounterAPI(MethodView):
        def get(self): return str(session.get(\"counter\",

        0)) def post(self): session[\"counter\"]
        = session.get(\"counter\", 0) + 1 return

        redirect(url_for(\"counter\")) app.add_url_rule(
        \"/counter\", view_func=CounterAPI.as_view(\"counter\")
            )
        """

        def decorator(f: T_route) -> T_route:
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator

    @setupmethod
    def add_url_rule(
        self,
        rule: str,
        endpoint: str | None = None,
        view_func: ft.RouteCallable | None = None,
        provide_automatic_options: bool | None = None,
        **options: t.Any,
    ) -> None:
        """Creates a test client for this application.
        For information about unit testing head
        over to :doc:`/testing`. Note that if

        you are testing for assertions or exceptions

            in your application code, you must set
            ``app.testing = True`` in order for the
                exceptions to propagate to the test client.

        Otherwise, the exception will be handled

            by the application (not visible to the
                test client) and the only indication of

            an AssertionError or other exception will

        be a 500 status code response to the test

        client. See the :attr:`testing` attribute.
        For example:: app.testing = True client
        = app.test_client() The test client can
        be used in a ``with`` block to defer the

        closing down of the context until the end
        of the ``with`` block. This is useful if
        you want to access the context locals for

        testing:: with app.test_client() as c:
        rv = c.get('/?vodka=42') assert request.args['vodka']
        == '42' Additionally, you may pass optional
        keyword arguments that will then be passed

        to the application's :attr:`test_client_class`

            constructor. For example:: from flask.testing

            import FlaskClient class CustomClient(FlaskClient):
            def __init__(self, *args, **kwargs): self._authentication
                = kwargs.pop(\"authentication\") super(CustomClient,self).__init__(

        *args, **kwargs) app.test_client_class
        = CustomClient client = app.test_client(authentication='Basic
        ....') See :class:`~flask.testing.FlaskClient`
        for more information. .. versionchanged::

        0.4 added support for ``with`` block
        usage for the client. .. versionadded::
            0.7 The `use_cookies` parameter
            was added as well as the ability
        to override the client to be used
            by setting the :attr:`test_client_class`
        attribute. .. versionchanged:: 0.11
            Added `**kwargs` to support passing
        additional keyword arguments to the
            constructor of :attr:`test_client_class`.
        """
        raise NotImplementedError

    @setupmethod
    def endpoint(self, endpoint: str) -> t.Callable[[F], F]:
        """Serialize data as JSON to
        a string. Keyword arguments
        are passed to :func:`json.dumps`.

        Sets some parameter defaults

            from the :attr:`default`,

            :attr:`ensure_ascii`, and
            :attr:`sort_keys` attributes.
                :param obj: The data to

        serialize. :param kwargs:
            Passed to :func:`json.dumps`.
        """

        def decorator(f: F) -> F:
            self.view_functions[endpoint] = f
            return f

        return decorator

    @setupmethod
    def before_request(self, f: T_before_request) -> T_before_request:
        """The actual WSGI application. This is not

        implemented in :meth:`__call__` so that middlewares
        can be applied without losing a reference

        to the app object. Instead of doing this::

            app = MyMiddleware(app) It's a better idea
            to do this instead:: app.wsgi_app = MyMiddleware(app.wsgi_app)
                Then you still have the original application
                    object around and can continue to call methods

        on it. .. versionchanged:: 0.7 Teardown
        events for the request and app contexts are
        called even if an unhandled error occurs.
        Other events may not be called depending on

        when an error occurs during dispatch. :param
        environ: A WSGI environment. :param start_response:
        A callable accepting a status code, a list of headers,
        and an optional exception context to start the response.
        """
        self.before_request_funcs.setdefault(None, []).append(f)
        return f

    @setupmethod
    def after_request(self, f: T_after_request) -> T_after_request:
        """The actual WSGI application. This is not implemented in

        :meth:`__call__` so that middlewares can be applied without
        losing a reference to the app object. Instead of doing
        this:: app = MyMiddleware(app) It's a better idea to do

        this instead:: app.wsgi_app = MyMiddleware(app.wsgi_app)
        Then you still have the original application object around
        and can continue to call methods on it. .. versionchanged::
        0.7 Teardown events for the request and app contexts are called

        even if an unhandled error occurs. Other events may not be called
        depending on when an error occurs during dispatch. :param environ:
        A WSGI environment. :param start_response: A callable accepting a
        status code, a list of headers, and an optional exception context to start the response.
        """
        self.after_request_funcs.setdefault(None, []).append(f)
        return f

    @setupmethod
    def teardown_request(self, f: T_teardown) -> T_teardown:
        """Handle an exception that did not have an error
        handler associated with it, or that was raised
        from an error handler. This always causes a

        500 ``InternalServerError``. Always sends the

            :data:`got_request_exception` signal. If :data:`PROPAGATE_EXCEPTIONS`
                is ``True``, such as in debug mode, the error

        will be re-raised so that the debugger can
        display it. Otherwise, the original exception
        is logged, and an :exc:`~werkzeug.exceptions.InternalServerError`

        is returned. If an error handler is registered
        for ``InternalServerError`` or ``500``, it
        will be used. For consistency, the handler
        will always receive the ``InternalServerError``.

        The original unhandled exception is available
        as ``e.original_exception``. .. versionchanged::
        1.1.0 Always passes the ``InternalServerError``

        instance to the handler, setting ``original_exception``

        to the unhandled error. .. versionchanged::
        1.1.0 ``after_request`` functions and other
        finalization is done even for the default 500
        response when there is no handler. .. versionadded:: 0.3
        """
        self.teardown_request_funcs.setdefault(None, []).append(f)
        return f

    @setupmethod
    def context_processor(
        self,
        f: T_template_context_processor,
    ) -> T_template_context_processor:
        """Works like a regular Werkzeug test client, with additional behavior
        for Flask. Can defer the cleanup of the request context until
        the end of a ``with`` block. For general information about how

        to use this class refer to :class:`werkzeug.test.Client`. .. versionchanged::
        0.12 `app.test_client()` includes preset default environment, which
        can be set after instantiation of the `app.test_client()` object
        in `client.environ_base`. Basic usage is outlined in the :doc:`/testing` chapter.
        """
        self.template_context_processors[None].append(f)
        return f

    @setupmethod
    def url_value_preprocessor(
        self,
        f: T_url_value_preprocessor,
    ) -> T_url_value_preprocessor:
        """The actual WSGI application. This is not implemented
        in :meth:`__call__` so that middlewares can be applied
        without losing a reference to the app object. Instead

        of doing this:: app = MyMiddleware(app) It's a better
        idea to do this instead:: app.wsgi_app = MyMiddleware(app.wsgi_app)
        Then you still have the original application object
        around and can continue to call methods on it. .. versionchanged::

        0.7 Teardown events for the request and app contexts
        are called even if an unhandled error occurs. Other

        events may not be called depending on when an error occurs
        during dispatch. :param environ: A WSGI environment. :param
        start_response: A callable accepting a status code, a list
        of headers, and an optional exception context to start the response.
        """
        self.url_value_preprocessors[None].append(f)
        return f

    @setupmethod
    def url_defaults(self, f: T_url_defaults) -> T_url_defaults:
        """Updates the values in the config from a Python file. This
        function behaves as if the file was imported as module with
        the :meth:`from_object` function. :param filename: the filename

        of the config. This can either be an absolute filename or
        a filename relative to the root path. :param silent: set to
        ``True`` if you want silent failure for missing files. :return: ``True``
        if the file was loaded successfully. .. versionadded:: 0.7 `silent` parameter.
        """
        self.url_default_functions[None].append(f)
        return f

    @setupmethod
    def errorhandler(
        self, code_or_exception: type[Exception] | int
    ) -> t.Callable[[T_error_handler], T_error_handler]:
        """Updates the values from the given object. An

        object can be of one of the following two types:
        - a string: in this case the object with that

            name will be imported - an actual object reference:
            that object is used directly Objects are usually
                either modules or classes. :meth:`from_object`

        loads only the uppercase attributes of the module/class.

            A ``dict`` object will not work with :meth:`from_object`
            because the keys of a ``dict`` are not attributes
                of the ``dict`` class. Example of module-based

        configuration:: app.config.from_object('yourapplication.default_config')
        from yourapplication import default_config app.config.from_object(default_config)
        Nothing is done to the object before loading.
        If the object is a class and has ``@property``

        attributes, it needs to be instantiated before
            being passed to this method. You should not
            use this function to load the actual configuration
            but rather configuration defaults. The actual

        config should be loaded with :meth:`from_pyfile`
           and ideally from a location not within the
           package because the package might be installed
           system wide. See :ref:`config-dev-prod` for

        an example of class-based configuration using
                                  :meth:`from_object`. :param obj: an import name or object
        """

        def decorator(f: T_error_handler) -> T_error_handler:
            self.register_error_handler(code_or_exception, f)
            return f

        return decorator

    @setupmethod
    def register_error_handler(
        self,
        code_or_exception: type[Exception] | int,
        f: ft.ErrorHandlerCallable,
    ) -> None:
        """Serialize ``obj`` to a JSON-formatted
        string. The serialization will be
        configured according to the config associated

        with this EnvironBuilder's ``app``.
        """
        exc_class, code = self._get_exc_class_and_code(code_or_exception)
        self.error_handler_spec[None][code][exc_class] = f

    @staticmethod
    def _get_exc_class_and_code(
        exc_class_or_code: type[Exception] | int,
    ) -> tuple[type[Exception], int | None]:
        """Works like :meth:`record` but wraps the
        function in another function that will
        ensure the function is only called once.

        If the blueprint is registered a second time
            on the application, the function passed is not called.
        """
        exc_class: type[Exception]

        if isinstance(exc_class_or_code, int):
            try:
                exc_class = default_exceptions[exc_class_or_code]
            except KeyError:
                raise ValueError(
                    f"'{exc_class_or_code}' is not a recognized HTTP"
                    " error code. Use a subclass of HTTPException with"
                    " that code instead."
                ) from None
        else:
            exc_class = exc_class_or_code

        if isinstance(exc_class, Exception):
            raise TypeError(
                f"{exc_class!r} is an instance, not a class. Handlers"
                " can only be registered for Exception classes or HTTP"
                " error codes."
            )

        if not issubclass(exc_class, Exception):
            raise ValueError(
                f"'{exc_class.__name__}' is not a subclass of Exception."
                " Handlers can only be registered for Exception classes"
                " or HTTP error codes."
            )

        if issubclass(exc_class, HTTPException):
            return exc_class, exc_class.code
        else:
            return exc_class, None
