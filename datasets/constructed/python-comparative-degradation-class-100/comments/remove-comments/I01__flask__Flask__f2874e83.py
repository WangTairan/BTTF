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

     
     
    request_class: type[Request] = Request

     
     
    response_class: type[Response] = Response

     
     
     
     
    session_interface: SessionInterface = SecureCookieSessionInterface()

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        import warnings

         
         
         
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
                 
                continue

             
            iter_params = iter(inspect.signature(method).parameters.values())
            next(iter_params)
            param = next(iter_params, None)

             
            if param is None or not (
                 
                (param.annotation is inspect.Parameter.empty and param.name == "ctx")
                or (
                     
                    isinstance(param.annotation, str)
                    and param.annotation.rpartition(".")[2] == "AppContext"
                )
                or (
                     
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

         
         
         
         
        self.cli = cli.AppGroup()

         
         
        self.cli.name = self.name

         
         
         
         
         
        if self.has_static_folder:
            assert bool(static_host) == host_matching, (
                "Invalid static_host/host_matching combination"
            )
             
             
            self_ref = weakref.ref(self)
            self.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                endpoint="static",
                host=static_host,
                view_func=lambda **kw: self_ref().send_static_file(**kw),   
            )

    def get_send_file_max_age(self, filename: str | None) -> int | None:
        
        value = self.config["SEND_FILE_MAX_AGE_DEFAULT"]

        if value is None:
            return None

        if isinstance(value, timedelta):
            return int(value.total_seconds())

        return value   

    def send_static_file(self, filename: str) -> Response:
        
        if not self.has_static_folder:
            raise RuntimeError("'static_folder' must be set to serve static_files.")

         
         
        max_age = self.get_send_file_max_age(filename)
        return send_from_directory(
            t.cast(str, self.static_folder), filename, max_age=max_age
        )

    def open_resource(
        self, resource: str, mode: str = "rb", encoding: str | None = None
    ) -> t.IO[t.AnyStr]:
        
        if mode not in {"r", "rt", "rb"}:
            raise ValueError("Resources can only be opened for reading.")

        path = os.path.join(self.root_path, resource)

        if mode == "rb":
            return open(path, mode)   

        return open(path, mode, encoding=encoding)

    def open_instance_resource(
        self, resource: str, mode: str = "rb", encoding: str | None = "utf-8"
    ) -> t.IO[t.AnyStr]:
        
        path = os.path.join(self.instance_path, resource)

        if "b" in mode:
            return open(path, mode)

        return open(path, mode, encoding=encoding)

    def create_jinja_environment(self) -> Environment:
        
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
             
             
             
            request=request,
            session=session,
            g=g,
        )
        rv.policies["json.dumps_function"] = self.json.dumps
        return rv

    def create_url_adapter(self, request: Request | None) -> MapAdapter | None:
        
        if request is not None:
            if (trusted_hosts := self.config["TRUSTED_HOSTS"]) is not None:
                request.trusted_hosts = trusted_hosts

             
            request.host = get_host(request.environ, request.trusted_hosts)   
            subdomain = None
            server_name = self.config["SERVER_NAME"]

            if self.url_map.host_matching:
                 
                 
                server_name = None
            elif not self.subdomain_matching:
                 
                 
                 
                subdomain = self.url_map.default_subdomain or ""

            return self.url_map.bind_to_environ(
                request.environ, server_name=server_name, subdomain=subdomain
            )

         
        if self.config["SERVER_NAME"] is not None:
            return self.url_map.bind(
                self.config["SERVER_NAME"],
                script_name=self.config["APPLICATION_ROOT"],
                url_scheme=self.config["PREFERRED_URL_SCHEME"],
            )

        return None

    def raise_routing_exception(self, request: Request) -> t.NoReturn:
        
        if (
            not self.debug
            or not isinstance(request.routing_exception, RequestRedirect)
            or request.routing_exception.code in {307, 308}
            or request.method in {"GET", "HEAD", "OPTIONS"}
        ):
            raise request.routing_exception   

        from .debughelpers import FormDataRoutingRedirect

        raise FormDataRoutingRedirect(request)

    def update_template_context(
        self, ctx: AppContext, context: dict[str, t.Any]
    ) -> None:
        
        names: t.Iterable[str | None] = (None,)

         
        if ctx.has_request:
            names = chain(names, reversed(ctx.request.blueprints))

         
         
        orig_ctx = context.copy()

        for name in names:
            if name in self.template_context_processors:
                for func in self.template_context_processors[name]:
                    context.update(self.ensure_sync(func)())

        context.update(orig_ctx)

    def make_shell_context(self) -> dict[str, t.Any]:
        
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

             
            if "FLASK_DEBUG" in os.environ:
                self.debug = get_debug_flag()

         
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
             
             
             
            self._got_first_request = False

    def test_client(self, use_cookies: bool = True, **kwargs: t.Any) -> FlaskClient:
        
        cls = self.test_client_class
        if cls is None:
            from .testing import FlaskClient as cls
        return cls(   
            self, self.response_class, use_cookies=use_cookies, **kwargs
        )

    def test_cli_runner(self, **kwargs: t.Any) -> FlaskCliRunner:
        
        cls = self.test_cli_runner_class

        if cls is None:
            from .testing import FlaskCliRunner as cls

        return cls(self, **kwargs)   

    def handle_http_exception(
        self, ctx: AppContext, e: HTTPException
    ) -> HTTPException | ft.ResponseReturnValue:
        
         
         
        if e.code is None:
            return e

         
         
         
        if isinstance(e, RoutingException):
            return e

        handler = self._find_error_handler(e, ctx.request.blueprints)
        if handler is None:
            return e
        return self.ensure_sync(handler)(e)   

    def handle_user_exception(
        self, ctx: AppContext, e: Exception
    ) -> HTTPException | ft.ResponseReturnValue:
        
        if isinstance(e, BadRequestKeyError) and (
            self.debug or self.config["TRAP_BAD_REQUEST_ERRORS"]
        ):
            e.show_exception = True

        if isinstance(e, HTTPException) and not self.trap_http_exception(e):
            return self.handle_http_exception(ctx, e)

        handler = self._find_error_handler(e, ctx.request.blueprints)

        if handler is None:
            raise

        return self.ensure_sync(handler)(e)   

    def handle_exception(self, ctx: AppContext, e: Exception) -> Response:
        
        exc_info = sys.exc_info()
        got_request_exception.send(self, _async_wrapper=self.ensure_sync, exception=e)
        propagate = self.config["PROPAGATE_EXCEPTIONS"]

        if propagate is None:
            propagate = self.testing or self.debug

        if propagate:
             
             
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
        
        self.logger.error(
            f"Exception on {ctx.request.path} [{ctx.request.method}]", exc_info=exc_info
        )

    def dispatch_request(self, ctx: AppContext) -> ft.ResponseReturnValue:
        
        req = ctx.request

        if req.routing_exception is not None:
            self.raise_routing_exception(req)
        rule: Rule = req.url_rule   
         
         
        if (
            getattr(rule, "provide_automatic_options", False)
            and req.method == "OPTIONS"
        ):
            return self.make_default_options_response(ctx)
         
        view_args: dict[str, t.Any] = req.view_args   
        return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)   

    def full_dispatch_request(self, ctx: AppContext) -> Response:
        
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
        
        methods = ctx.url_adapter.allowed_methods()   
        rv = self.response_class()
        rv.allow.update(methods)
        return rv

    def ensure_sync(self, func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        
        if iscoroutinefunction(func):
            return self.async_to_sync(func)

        return func

    def async_to_sync(
        self, func: t.Callable[..., t.Coroutine[t.Any, t.Any, t.Any]]
    ) -> t.Callable[..., t.Any]:
        
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
        
        if (ctx := _cv_app.get(None)) is not None and ctx.has_request:
            url_adapter = ctx.url_adapter
            blueprint_name = ctx.request.blueprint

             
             
            if endpoint[:1] == ".":
                if blueprint_name is not None:
                    endpoint = f"{blueprint_name}{endpoint}"
                else:
                    endpoint = endpoint[1:]

             
             
            if _external is None:
                _external = _scheme is not None
        else:
             
             
             
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

             
             
            if _external is None:
                _external = True

         
         
        if _scheme is not None and not _external:
            raise ValueError("When specifying '_scheme', '_external' must be True.")

        self.inject_url_defaults(endpoint, values)

        try:
            rv = url_adapter.build(   
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
        

        status: int | None = None
        headers: HeadersValue | None = None

         
        if isinstance(rv, tuple):
            len_rv = len(rv)

             
            if len_rv == 3:
                rv, status, headers = rv   
             
            elif len_rv == 2:
                if isinstance(rv[1], (Headers, dict, tuple, list)):
                    rv, headers = rv   
                else:
                    rv, status = rv   
             
            else:
                raise TypeError(
                    "The view function did not return a valid response tuple."
                    " The tuple must have the form (body, status, headers),"
                    " (body, status), or (body, headers)."
                )

         
        if rv is None:
            raise TypeError(
                f"The view function for {request.endpoint!r} did not"
                " return a valid response. The function either returned"
                " None or ended without a return statement."
            )

         
        if not isinstance(rv, self.response_class):
            if isinstance(rv, (str, bytes, bytearray)) or isinstance(rv, cabc.Iterator):
                 
                 
                 
                rv = self.response_class(
                    rv,   
                    status=status,
                    headers=headers,   
                )
                status = headers = None
            elif isinstance(rv, (dict, list)):
                rv = self.json.response(rv)
            elif isinstance(rv, BaseResponse) or callable(rv):
                 
                 
                try:
                    rv = self.response_class.force_type(
                        rv,   
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
         
        if status is not None:
            if isinstance(status, (str, bytes, bytearray)):
                rv.status = status
            else:
                rv.status_code = status

         
        if headers:
            rv.headers.update(headers)

        return rv

    def preprocess_request(self, ctx: AppContext) -> ft.ResponseReturnValue | None:
        
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
                        return rv   

        return None

    def process_response(self, ctx: AppContext, response: Response) -> Response:
        
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
        
        collect_errors = _CollectErrors()

        for func in reversed(self.teardown_appcontext_funcs):
            with collect_errors:
                self.ensure_sync(func)(exc)

        with collect_errors:
            appcontext_tearing_down.send(self, _async_wrapper=self.ensure_sync, exc=exc)

        collect_errors.raise_any("Errors during app teardown")

    def app_context(self) -> AppContext:
        
        return AppContext(self)

    def request_context(self, environ: WSGIEnvironment) -> AppContext:
        
        return AppContext.from_environ(self, environ)

    def test_request_context(self, *args: t.Any, **kwargs: t.Any) -> AppContext:
        
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
        
        return self.wsgi_app(environ, start_response)
