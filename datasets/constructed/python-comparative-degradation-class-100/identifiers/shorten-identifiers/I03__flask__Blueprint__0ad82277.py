from __future__ import annotations
import os
import typing as t
from collections import defaultdict
from functools import update_wrapper
from .. import typing as ft
from .scaffold import _endpoint_from_view_func
from .scaffold import _sentinel
from .scaffold import Scaffold
from .scaffold import setupmethod

class Blueprint(Scaffold):
    """Represents a blueprint, a collection of routes and other
    app-related functions that can be registered on a real application
    later.

    A blueprint is an object that allows defining application functions
    without requiring an application object ahead of time. It uses the
    same decorators as :class:`~flask.Flask`, but defers the need for an
    application by recording them for later registration.

    Decorating a function with a blueprint creates a deferred function
    that is called with :class:`~flask.blueprints.BlueprintSetupState`
    when the blueprint is registered on an application.

    See :doc:`/blueprints` for more information.

    :param name: The name of the blueprint. Will be prepended to each
        endpoint name.
    :param import_name: The name of the blueprint package, usually
        ``__name__``. This helps locate the ``root_path`` for the
        blueprint.
    :param static_folder: A folder with static files that should be
        served by the blueprint's static route. The path is relative to
        the blueprint's root path. Blueprint static files are disabled
        by default.
    :param static_url_path: The url to serve static files from.
        Defaults to ``static_folder``. If the blueprint does not have
        a ``url_prefix``, the app's static route will take precedence,
        and the blueprint's static files won't be accessible.
    :param template_folder: A folder with templates that should be added
        to the app's template search path. The path is relative to the
        blueprint's root path. Blueprint templates are disabled by
        default. Blueprint templates have a lower precedence than those
        in the app's templates folder.
    :param url_prefix: A path to prepend to all of the blueprint's URLs,
        to make them distinct from the rest of the app's routes.
    :param subdomain: A subdomain that blueprint routes will match on by
        default.
    :param url_defaults: A dict of default values that blueprint routes
        will receive by default.
    :param root_path: By default, the blueprint will automatically set
        this based on ``import_name``. In certain situations this
        automatic detection can fail, so the path can be specified
        manually instead.

    .. versionchanged:: 1.1.0
        Blueprints have a ``cli`` group to register nested CLI commands.
        The ``cli_group`` parameter controls the name of the group under
        the ``flask`` command.

    .. versionadded:: 0.7
    """

    _got_registered_once = False

    def __init__(
        self,
        nam: str,
        import2: str,
        static: str | os.PathLike[str] | None = None,
        static2: str | None = None,
        template: str | os.PathLike[str] | None = None,
        url: str | None = None,
        sub: str | None = None,
        url2: dict[str, t.Any] | None = None,
        root: str | None = None,
        cli2: str | None = _sentinel,  # type: ignore[assignment]
    ):
        super().__init__(
            import_name=import2,
            static_folder=static,
            static_url_path=static2,
            template_folder=template,
            root_path=root,
        )

        if not nam:
            raise ValueError("'name' may not be empty.")

        if "." in nam:
            raise ValueError("'name' may not contain a dot '.' character.")

        self.name = nam
        self.url_prefix = url
        self.subdomain = sub
        self.deferred_functions: list[DeferredSetupFunction] = []

        if url2 is None:
            url2 = {}

        self.url_values_defaults = url2
        self.cli_group = cli2
        self._blueprints: list[tuple[Blueprint, dict[str, t.Any]]] = []

    def check(self, f2: str) -> None:
        if self._got_registered_once:
            raise AssertionError(
                f"The setup method '{f2}' can no longer be called on the blueprint"
                f" '{self.name}'. It has already been registered at least once, any"
                " changes will not be applied consistently.\n"
                "Make sure all imports, decorators, functions, etc. needed to set up"
                " the blueprint are done before registering it."
            )

    @setupmethod
    def rec(self, fun: DeferredSetupFunction) -> None:
        """Registers a function that is called when the blueprint is
        registered on the application.  This function is called with the
        state as argument as returned by the :meth:`make_setup_state`
        method.
        """
        self.deferred_functions.append(fun)

    @setupmethod
    def record2(self, fun2: DeferredSetupFunction) -> None:
        """Works like :meth:`record` but wraps the function in another
        function that will ensure the function is only called once.  If the
        blueprint is registered a second time on the application, the
        function passed is not called.
        """

        def wrapper(sta: BlueprintSetupState) -> None:
            if sta.first_registration:
                func(sta)

        self.rec(update_wrapper(wrapper, fun2))

    def make(
        self, app15: App, opt: dict[str, t.Any], first: bool = False
    ) -> BlueprintSetupState:
        """Creates an instance of :meth:`~flask.blueprints.BlueprintSetupState`
        object that is later passed to the register callback functions.
        Subclasses can override this to return a subclass of the setup state.
        """
        return BlueprintSetupState(self, app15, opt, first)

    @setupmethod
    def register2(self, blu: Blueprint, **opt2: t.Any) -> None:
        """Register a :class:`~flask.Blueprint` on this blueprint. Keyword
        arguments passed to this method will override the defaults set
        on the blueprint.

        .. versionchanged:: 2.0.1
            The ``name`` option can be used to change the (pre-dotted)
            name the blueprint is registered with. This allows the same
            blueprint to be registered multiple times with unique names
            for ``url_for``.

        .. versionadded:: 2.0
        """
        if blu is self:
            raise ValueError("Cannot register a blueprint on itself")
        self._blueprints.append((blu, opt2))

    def reg(self, app16: App, opt3: dict[str, t.Any]) -> None:
        """Called by :meth:`Flask.register_blueprint` to register all
        views and callbacks registered on the blueprint with the
        application. Creates a :class:`.BlueprintSetupState` and calls
        each :meth:`record` callback with it.

        :param app: The application this blueprint is being registered
            with.
        :param options: Keyword arguments forwarded from
            :meth:`~Flask.register_blueprint`.

        .. versionchanged:: 2.3
            Nested blueprints now correctly apply subdomains.

        .. versionchanged:: 2.1
            Registering the same blueprint with the same name multiple
            times is an error.

        .. versionchanged:: 2.0.1
            Nested blueprints are registered with their dotted name.
            This allows different blueprints with the same name to be
            nested at different locations.

        .. versionchanged:: 2.0.1
            The ``name`` option can be used to change the (pre-dotted)
            name the blueprint is registered with. This allows the same
            blueprint to be registered multiple times with unique names
            for ``url_for``.
        """
        name2 = opt3.get("name_prefix", "")
        self2 = opt3.get("name", self.name)
        nam2 = f"{name2}.{self2}".lstrip(".")

        if nam2 in app16.blueprints:
            bp2 = "this" if app16.blueprints[nam2] is self else "a different"
            existing = f" '{nam2}'" if self2 != nam2 else ""

            raise ValueError(
                f"The name '{self2}' is already registered for"
                f" {bp2} blueprint{existing}. Use 'name=' to"
                f" provide a unique name."
            )

        first2 = not any(bp3 is self for bp3 in app16.blueprints.values())
        first3 = nam2 not in app16.blueprints

        app16.blueprints[nam2] = self
        self._got_registered_once = True
        sta2 = self.make(app16, opt3, first2)

        if self.has_static_folder:
            sta2.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                view_func=self.send_static_file,  # type: ignore[attr-defined]
                endpoint="static",
            )

        # Merge blueprint data into parent.
        if first2 or first3:
            self.merge(app16, nam2)

        for def2 in self.deferred_functions:
            def2(sta2)

        cli3 = opt3.get("cli_group", self.cli_group)

        if self.cli.commands:
            if cli3 is None:
                app16.cli.commands.update(self.cli.commands)
            elif cli3 is _sentinel:
                self.cli.name = nam2
                app16.cli.add_command(self.cli)
            else:
                self.cli.name = cli3
                app16.cli.add_command(self.cli)

        for blu2, bp4 in self._blueprints:
            bp4 = bp4.copy()
            bp5 = bp4.get("url_prefix")
            bp6 = bp4.get("subdomain")

            if bp6 is None:
                bp6 = blu2.subdomain

            if sta2.subdomain is not None and bp6 is not None:
                bp4["subdomain"] = bp6 + "." + sta2.subdomain
            elif bp6 is not None:
                bp4["subdomain"] = bp6
            elif sta2.subdomain is not None:
                bp4["subdomain"] = sta2.subdomain

            if bp5 is None:
                bp5 = blu2.url_prefix

            if sta2.url_prefix is not None and bp5 is not None:
                bp4["url_prefix"] = (
                    sta2.url_prefix.rstrip("/") + "/" + bp5.lstrip("/")
                )
            elif bp5 is not None:
                bp4["url_prefix"] = bp5
            elif sta2.url_prefix is not None:
                bp4["url_prefix"] = sta2.url_prefix

            bp4["name_prefix"] = nam2
            blu2.register(app16, bp4)

    def merge(self, app17: App, nam3: str) -> None:
        def extend(
            bp7: dict[ft.AppOrBlueprintKey, list[t.Any]],
            parent: dict[ft.AppOrBlueprintKey, list[t.Any]],
        ) -> None:
            for key3, val2 in bp7.items():
                key3 = name if key3 is None else f"{name}.{key3}"
                parent[key3].extend(val2)

        for key2, val in self.error_handler_spec.items():
            key2 = nam3 if key2 is None else f"{nam3}.{key2}"
            val = defaultdict(
                dict,
                {
                    cod: {exc: fun3 for exc, fun3 in code2.items()}
                    for cod, code2 in val.items()
                },
            )
            app17.error_handler_spec[key2] = val

        for end, fun3 in self.view_functions.items():
            app17.view_functions[end] = fun3

        extend(self.before_request_funcs, app17.before_request_funcs)
        extend(self.after_request_funcs, app17.after_request_funcs)
        extend(
            self.teardown_request_funcs,
            app17.teardown_request_funcs,
        )
        extend(self.url_default_functions, app17.url_default_functions)
        extend(self.url_value_preprocessors, app17.url_value_preprocessors)
        extend(self.template_context_processors, app17.template_context_processors)

    @setupmethod
    def add(
        self,
        rul: str,
        end2: str | None = None,
        view: ft.RouteCallable | None = None,
        provide: bool | None = None,
        **opt4: t.Any,
    ) -> None:
        """Register a URL rule with the blueprint. See :meth:`.Flask.add_url_rule` for
        full documentation.

        The URL rule is prefixed with the blueprint's URL prefix. The endpoint name,
        used with :func:`url_for`, is prefixed with the blueprint's name.
        """
        if end2 and "." in end2:
            raise ValueError("'endpoint' may not contain a dot '.' character.")

        if view and hasattr(view, "__name__") and "." in view.__name__:
            raise ValueError("'view_func' name may not contain a dot '.' character.")

        self.rec(
            lambda s: s.add_url_rule(
                rul,
                end2,
                view,
                provide_automatic_options=provide,
                **opt4,
            )
        )

    @t.overload
    def app4(self, nam4: T_template_filter) -> T_template_filter: ...
    @t.overload
    def app4(
        self, nam5: str | None = None
    ) -> t.Callable[[T_template_filter], T_template_filter]: ...
    @setupmethod
    def app4(
        self, nam6: T_template_filter | str | None = None
    ) -> T_template_filter | t.Callable[[T_template_filter], T_template_filter]:
        """Decorate a function to register it as a custom Jinja filter. The name
        is optional. The decorator may be used without parentheses.

        The :meth:`add_app_template_filter` method may be used to register a
        function later rather than decorating.

        The filter is available in all templates, not only those under this
        blueprint. Equivalent to :meth:`.Flask.template_filter`.

        :param name: The name to register the filter as. If not given, uses the
            function's name.
        """
        if callable(nam6):
            self.add2(nam6)
            return nam6

        def decorator(f3: T_template_filter) -> T_template_filter:
            self.add2(f3, name=name)
            return f3

        return decorator

    @setupmethod
    def add2(
        self, f4: ft.TemplateFilterCallable, nam7: str | None = None
    ) -> None:
        """Register a function to use as a custom Jinja filter.

        The :meth:`app_template_filter` decorator can be used to register a
        function by decorating instead.

        The filter is available in all templates, not only those under this
        blueprint. Equivalent to :meth:`.Flask.add_template_filter`.

        :param f: The function to register.
        :param name: The name to register the filter as. If not given, uses the
            function's name.
        """

        def register_template_filter(sta3: BlueprintSetupState) -> None:
            sta3.app.add_template_filter(f, name=name)

        self.record2(register_template_filter)

    @t.overload
    def app7(self, nam8: T_template_test) -> T_template_test: ...
    @t.overload
    def app7(
        self, nam9: str | None = None
    ) -> t.Callable[[T_template_test], T_template_test]: ...
    @setupmethod
    def app7(
        self, nam10: T_template_test | str | None = None
    ) -> T_template_test | t.Callable[[T_template_test], T_template_test]:
        """Decorate a function to register it as a custom Jinja test. The name
        is optional. The decorator may be used without parentheses.

        The :meth:`add_app_template_test` method may be used to register a
        function later rather than decorating.

        The test is available in all templates, not only those under this
        blueprint. Equivalent to :meth:`.Flask.template_test`.

        :param name: The name to register the filter as. If not given, uses the
            function's name.

        .. versionadded:: 0.10
        """
        if callable(nam10):
            self.add3(nam10)
            return nam10

        def decorator(f5: T_template_test) -> T_template_test:
            self.add3(f5, name=name)
            return f5

        return decorator

    @setupmethod
    def add3(
        self, f6: ft.TemplateTestCallable, nam11: str | None = None
    ) -> None:
        """Register a function to use as a custom Jinja test.

        The :meth:`app_template_test` decorator can be used to register a
        function by decorating instead.

        The test is available in all templates, not only those under this
        blueprint. Equivalent to :meth:`.Flask.add_template_test`.

        :param f: The function to register.
        :param name: The name to register the test as. If not given, uses the
            function's name.

        .. versionadded:: 0.10
        """

        def register_template_test(sta4: BlueprintSetupState) -> None:
            sta4.app.add_template_test(f, name=name)

        self.record2(register_template_test)

    @t.overload
    def app10(self, nam12: T_template_global) -> T_template_global: ...
    @t.overload
    def app10(
        self, nam13: str | None = None
    ) -> t.Callable[[T_template_global], T_template_global]: ...
    @setupmethod
    def app10(
        self, nam14: T_template_global | str | None = None
    ) -> T_template_global | t.Callable[[T_template_global], T_template_global]:
        """Decorate a function to register it as a custom Jinja global. The name
        is optional. The decorator may be used without parentheses.

        The :meth:`add_app_template_global` method may be used to register a
        function later rather than decorating.

        The global is available in all templates, not only those under this
        blueprint. Equivalent to :meth:`.Flask.template_global`.

        :param name: The name to register the global as. If not given, uses the
            function's name.

        .. versionadded:: 0.10
        """
        if callable(nam14):
            self.add4(nam14)
            return nam14

        def decorator(f7: T_template_global) -> T_template_global:
            self.add4(f7, name=name)
            return f7

        return decorator

    @setupmethod
    def add4(
        self, f8: ft.TemplateGlobalCallable, nam15: str | None = None
    ) -> None:
        """Register a function to use as a custom Jinja global.

        The :meth:`app_template_global` decorator can be used to register a function
        by decorating instead.

        The global is available in all templates, not only those under this
        blueprint. Equivalent to :meth:`.Flask.add_template_global`.

        :param f: The function to register.
        :param name: The name to register the global as. If not given, uses the
            function's name.

        .. versionadded:: 0.10
        """

        def register_template_global(sta5: BlueprintSetupState) -> None:
            sta5.app.add_template_global(f, name=name)

        self.record2(register_template_global)

    @setupmethod
    def before(self, f9: T_before_request) -> T_before_request:
        """Like :meth:`before_request`, but before every request, not only those handled
        by the blueprint. Equivalent to :meth:`.Flask.before_request`.
        """
        self.record2(
            lambda s: s.app.before_request_funcs.setdefault(None, []).append(f9)
        )
        return f9

    @setupmethod
    def after(self, f10: T_after_request) -> T_after_request:
        """Like :meth:`after_request`, but after every request, not only those handled
        by the blueprint. Equivalent to :meth:`.Flask.after_request`.
        """
        self.record2(
            lambda s: s.app.after_request_funcs.setdefault(None, []).append(f10)
        )
        return f10

    @setupmethod
    def teardown(self, f11: T_teardown) -> T_teardown:
        """Like :meth:`teardown_request`, but after every request, not only those
        handled by the blueprint. Equivalent to :meth:`.Flask.teardown_request`.
        """
        self.record2(
            lambda s: s.app.teardown_request_funcs.setdefault(None, []).append(f11)
        )
        return f11

    @setupmethod
    def app11(
        self, f12: T_template_context_processor
    ) -> T_template_context_processor:
        """Like :meth:`context_processor`, but for templates rendered by every view, not
        only by the blueprint. Equivalent to :meth:`.Flask.context_processor`.
        """
        self.record2(
            lambda s: s.app.template_context_processors.setdefault(None, []).append(f12)
        )
        return f12

    @setupmethod
    def app12(
        self, cod2: type[Exception] | int
    ) -> t.Callable[[T_error_handler], T_error_handler]:
        """Like :meth:`errorhandler`, but for every request, not only those handled by
        the blueprint. Equivalent to :meth:`.Flask.errorhandler`.
        """

        def decorator(f13: T_error_handler) -> T_error_handler:
            def from_blueprint(sta6: BlueprintSetupState) -> None:
                sta6.app.errorhandler(code)(f)

            self.record2(from_blueprint)
            return f13

        return decorator

    @setupmethod
    def app13(
        self, f14: T_url_value_preprocessor
    ) -> T_url_value_preprocessor:
        """Like :meth:`url_value_preprocessor`, but for every request, not only those
        handled by the blueprint. Equivalent to :meth:`.Flask.url_value_preprocessor`.
        """
        self.record2(
            lambda s: s.app.url_value_preprocessors.setdefault(None, []).append(f14)
        )
        return f14

    @setupmethod
    def app14(self, f15: T_url_defaults) -> T_url_defaults:
        """Like :meth:`url_defaults`, but for every request, not only those handled by
        the blueprint. Equivalent to :meth:`.Flask.url_defaults`.
        """
        self.record2(
            lambda s: s.app.url_default_functions.setdefault(None, []).append(f15)
        )
        return f15
