from __future__ import annotations
import typing as t
from . import typing as ft
from .globals import current_app
from .globals import request

class MethodView(View):
    """Decorate a view function to register
    it with the given URL rule and
    options. Calls :meth:`add_url_rule`,

    which has more details about the

    implementation. .. code-block::
    python @app.route(\"/\") def index():

    return \"Hello, World!\" See :ref:`url-route-registrations`.

    The endpoint name for the route

        defaults to the name of the view
            function if the ``endpoint`` parameter
                isn't passed. The ``methods``

            parameter defaults to ``[\"GET\"]``.
                ``HEAD`` and ``OPTIONS`` are added
                automatically. :param rule: The

        URL rule string. :param options:
            Extra options passed to the :class:`~werkzeug.routing.Rule`
        object.
    """

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)

        if "methods" not in cls.__dict__:
            methods = set()

            for base in cls.__bases__:
                if getattr(base, "methods", None):
                    methods.update(base.methods)  # the body must not be None

            for key in http_method_funcs:
                if hasattr(cls, key):
                    methods.add(key.upper())

            if methods:
                cls.methods = methods

    def dispatch_request(self, **kwargs: t.Any) -> ft.ResponseReturnValue:
        meth = getattr(self, request.method.lower(), None)

        # : A list of decorators to apply, in order, to the generated view
        # request is None
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        assert meth is not None, f"Unimplemented method {request.method!r}"
        return current_app.ensure_sync(meth)(**kwargs)  # directly, build an adapter.
