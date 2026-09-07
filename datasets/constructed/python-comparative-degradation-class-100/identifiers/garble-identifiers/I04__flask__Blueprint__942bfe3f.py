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
        E: str,
        F: str,
        G: str | os.PathLike[str] | None = None,
        H: str | None = None,
        I: str | os.PathLike[str] | None = None,
        J: str | None = None,
        K: str | None = None,
        L: dict[str, t.Any] | None = None,
        M: str | None = None,
        N: str | None = _sentinel,  # type: ignore[assignment]
    ):
        super().__init__(
            import_name=F,
            static_folder=G,
            static_url_path=H,
            template_folder=I,
            root_path=M,
        )

        if not E:
            raise ValueError("'name' may not be empty.")

        if "." in E:
            raise ValueError("'name' may not contain a dot '.' character.")

        self.name = E
        self.url_prefix = J
        self.subdomain = K
        self.deferred_functions: list[DeferredSetupFunction] = []

        if L is None:
            L = {}

        self.url_values_defaults = L
        self.cli_group = N
        self._blueprints: list[tuple[Blueprint, dict[str, t.Any]]] = []

    def a(self, O: str) -> None:
        if self._got_registered_once:
            raise AssertionError(
                f"The setup method '{O}' can no longer be called on the blueprint"
                f" '{self.name}'. It has already been registered at least once, any"
                " changes will not be applied consistently.\n"
                "Make sure all imports, decorators, functions, etc. needed to set up"
                " the blueprint are done before registering it."
            )

    @setupmethod
    def b(self, P: DeferredSetupFunction) -> None:
        """Registers a function that is called when the blueprint is
        registered on the application.  This function is called with the
        state as argument as returned by the :meth:`make_setup_state`
        method.
        """
        self.deferred_functions.append(P)

    @setupmethod
    def c(self, Q: DeferredSetupFunction) -> None:
        """Works like :meth:`record` but wraps the function in another
        function that will ensure the function is only called once.  If the
        blueprint is registered a second time on the application, the
        function passed is not called.
        """

        def wrapper(R: BlueprintSetupState) -> None:
            if R.first_registration:
                func(R)

        self.b(update_wrapper(wrapper, Q))

    def d(
        self, S: App, T: dict[str, t.Any], U: bool = False
    ) -> BlueprintSetupState:
        """Creates an instance of :meth:`~flask.blueprints.BlueprintSetupState`
        object that is later passed to the register callback functions.
        Subclasses can override this to return a subclass of the setup state.
        """
        return BlueprintSetupState(self, S, T, U)

    @setupmethod
    def e(self, V: Blueprint, **W: t.Any) -> None:
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
        if V is self:
            raise ValueError("Cannot register a blueprint on itself")
        self._blueprints.append((V, W))

    def g(self, X: App, Y: dict[str, t.Any]) -> None:
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
        Z = Y.get("name_prefix", "")
        aa = Y.get("name", self.name)
        ab = f"{Z}.{aa}".lstrip(".")

        if ab in X.blueprints:
            ac = "this" if X.blueprints[ab] is self else "a different"
            ad = f" '{ab}'" if aa != ab else ""

            raise ValueError(
                f"The name '{aa}' is already registered for"
                f" {ac} blueprint{ad}. Use 'name=' to"
                f" provide a unique name."
            )

        ae = not any(af is self for af in X.blueprints.values())
        ag = ab not in X.blueprints

        X.blueprints[ab] = self
        self._got_registered_once = True
        ah = self.d(X, Y, ae)

        if self.has_static_folder:
            ah.add_url_rule(
                f"{self.static_url_path}/<path:filename>",
                view_func=self.send_static_file,  # type: ignore[attr-defined]
                endpoint="static",
            )

        # Merge blueprint data into parent.
        if ae or ag:
            self.h(X, ab)

        for ai in self.deferred_functions:
            ai(ah)

        aj = Y.get("cli_group", self.cli_group)

        if self.cli.commands:
            if aj is None:
                X.cli.commands.update(self.cli.commands)
            elif aj is _sentinel:
                self.cli.name = ab
                X.cli.add_command(self.cli)
            else:
                self.cli.name = aj
                X.cli.add_command(self.cli)

        for ak, al in self._blueprints:
            al = al.copy()
            am = al.get("url_prefix")
            an = al.get("subdomain")

            if an is None:
                an = ak.subdomain

            if ah.subdomain is not None and an is not None:
                al["subdomain"] = an + "." + ah.subdomain
            elif an is not None:
                al["subdomain"] = an
            elif ah.subdomain is not None:
                al["subdomain"] = ah.subdomain

            if am is None:
                am = ak.url_prefix

            if ah.url_prefix is not None and am is not None:
                al["url_prefix"] = (
                    ah.url_prefix.rstrip("/") + "/" + am.lstrip("/")
                )
            elif am is not None:
                al["url_prefix"] = am
            elif ah.url_prefix is not None:
                al["url_prefix"] = ah.url_prefix

            al["name_prefix"] = ab
            ak.register(X, al)

    def h(self, ao: App, ap: str) -> None:
        def extend(
            ay: dict[ft.AppOrBlueprintKey, list[t.Any]],
            az: dict[ft.AppOrBlueprintKey, list[t.Any]],
        ) -> None:
            for aA, aB in ay.items():
                aA = name if aA is None else f"{name}.{aA}"
                az[aA].extend(aB)

        for aq, ar in self.error_handler_spec.items():
            aq = ap if aq is None else f"{ap}.{aq}"
            ar = defaultdict(
                dict,
                {
                    au: {at: ax for at, ax in av.items()}
                    for au, av in ar.items()
                },
            )
            ao.error_handler_spec[aq] = ar

        for aw, ax in self.view_functions.items():
            ao.view_functions[aw] = ax

        extend(self.before_request_funcs, ao.before_request_funcs)
        extend(self.after_request_funcs, ao.after_request_funcs)
        extend(
            self.teardown_request_funcs,
            ao.teardown_request_funcs,
        )
        extend(self.url_default_functions, ao.url_default_functions)
        extend(self.url_value_preprocessors, ao.url_value_preprocessors)
        extend(self.template_context_processors, ao.template_context_processors)

    @setupmethod
    def i(
        self,
        aC: str,
        aD: str | None = None,
        aE: ft.RouteCallable | None = None,
        aF: bool | None = None,
        **aG: t.Any,
    ) -> None:
        """Register a URL rule with the blueprint. See :meth:`.Flask.add_url_rule` for
        full documentation.

        The URL rule is prefixed with the blueprint's URL prefix. The endpoint name,
        used with :func:`url_for`, is prefixed with the blueprint's name.
        """
        if aD and "." in aD:
            raise ValueError("'endpoint' may not contain a dot '.' character.")

        if aE and hasattr(aE, "__name__") and "." in aE.__name__:
            raise ValueError("'view_func' name may not contain a dot '.' character.")

        self.b(
            lambda s: s.add_url_rule(
                aC,
                aD,
                aE,
                provide_automatic_options=aF,
                **aG,
            )
        )

    @t.overload
    def l(self, aH: T_template_filter) -> T_template_filter: ...
    @t.overload
    def l(
        self, aI: str | None = None
    ) -> t.Callable[[T_template_filter], T_template_filter]: ...
    @setupmethod
    def l(
        self, aJ: T_template_filter | str | None = None
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
        if callable(aJ):
            self.m(aJ)
            return aJ

        def decorator(aK: T_template_filter) -> T_template_filter:
            self.m(aK, name=name)
            return aK

        return decorator

    @setupmethod
    def m(
        self, aL: ft.TemplateFilterCallable, aM: str | None = None
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

        def register_template_filter(aN: BlueprintSetupState) -> None:
            aN.app.add_template_filter(f, name=name)

        self.c(register_template_filter)

    @t.overload
    def p(self, aO: T_template_test) -> T_template_test: ...
    @t.overload
    def p(
        self, aP: str | None = None
    ) -> t.Callable[[T_template_test], T_template_test]: ...
    @setupmethod
    def p(
        self, aQ: T_template_test | str | None = None
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
        if callable(aQ):
            self.q(aQ)
            return aQ

        def decorator(aR: T_template_test) -> T_template_test:
            self.q(aR, name=name)
            return aR

        return decorator

    @setupmethod
    def q(
        self, aS: ft.TemplateTestCallable, aT: str | None = None
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

        def register_template_test(aU: BlueprintSetupState) -> None:
            aU.app.add_template_test(f, name=name)

        self.c(register_template_test)

    @t.overload
    def v(self, aV: T_template_global) -> T_template_global: ...
    @t.overload
    def v(
        self, aW: str | None = None
    ) -> t.Callable[[T_template_global], T_template_global]: ...
    @setupmethod
    def v(
        self, aX: T_template_global | str | None = None
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
        if callable(aX):
            self.w(aX)
            return aX

        def decorator(aY: T_template_global) -> T_template_global:
            self.w(aY, name=name)
            return aY

        return decorator

    @setupmethod
    def w(
        self, aZ: ft.TemplateGlobalCallable, ba: str | None = None
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

        def register_template_global(bb: BlueprintSetupState) -> None:
            bb.app.add_template_global(f, name=name)

        self.c(register_template_global)

    @setupmethod
    def x(self, bc: T_before_request) -> T_before_request:
        """Like :meth:`before_request`, but before every request, not only those handled
        by the blueprint. Equivalent to :meth:`.Flask.before_request`.
        """
        self.c(
            lambda s: s.app.before_request_funcs.setdefault(None, []).append(bc)
        )
        return bc

    @setupmethod
    def y(self, bd: T_after_request) -> T_after_request:
        """Like :meth:`after_request`, but after every request, not only those handled
        by the blueprint. Equivalent to :meth:`.Flask.after_request`.
        """
        self.c(
            lambda s: s.app.after_request_funcs.setdefault(None, []).append(bd)
        )
        return bd

    @setupmethod
    def z(self, be: T_teardown) -> T_teardown:
        """Like :meth:`teardown_request`, but after every request, not only those
        handled by the blueprint. Equivalent to :meth:`.Flask.teardown_request`.
        """
        self.c(
            lambda s: s.app.teardown_request_funcs.setdefault(None, []).append(be)
        )
        return be

    @setupmethod
    def A(
        self, bf: T_template_context_processor
    ) -> T_template_context_processor:
        """Like :meth:`context_processor`, but for templates rendered by every view, not
        only by the blueprint. Equivalent to :meth:`.Flask.context_processor`.
        """
        self.c(
            lambda s: s.app.template_context_processors.setdefault(None, []).append(bf)
        )
        return bf

    @setupmethod
    def B(
        self, bg: type[Exception] | int
    ) -> t.Callable[[T_error_handler], T_error_handler]:
        """Like :meth:`errorhandler`, but for every request, not only those handled by
        the blueprint. Equivalent to :meth:`.Flask.errorhandler`.
        """

        def decorator(bh: T_error_handler) -> T_error_handler:
            def from_blueprint(bi: BlueprintSetupState) -> None:
                bi.app.errorhandler(code)(f)

            self.c(from_blueprint)
            return bh

        return decorator

    @setupmethod
    def C(
        self, bj: T_url_value_preprocessor
    ) -> T_url_value_preprocessor:
        """Like :meth:`url_value_preprocessor`, but for every request, not only those
        handled by the blueprint. Equivalent to :meth:`.Flask.url_value_preprocessor`.
        """
        self.c(
            lambda s: s.app.url_value_preprocessors.setdefault(None, []).append(bj)
        )
        return bj

    @setupmethod
    def D(self, bk: T_url_defaults) -> T_url_defaults:
        """Like :meth:`url_defaults`, but for every request, not only those handled by
        the blueprint. Equivalent to :meth:`.Flask.url_defaults`.
        """
        self.c(
            lambda s: s.app.url_default_functions.setdefault(None, []).append(bk)
        )
        return bk
