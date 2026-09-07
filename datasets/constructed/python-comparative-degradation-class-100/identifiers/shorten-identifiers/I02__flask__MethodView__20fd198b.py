from __future__ import annotations
import typing as t
from . import typing as ft
from .globals import current_app
from .globals import request

class MethodView(View):
    """Dispatches request methods to the corresponding instance methods.
    For example, if you implement a ``get`` method, it will be used to
    handle ``GET`` requests.

    This can be useful for defining a REST API.

    :attr:`methods` is automatically set based on the methods defined on
    the class.

    See :doc:`views` for a detailed guide.

    .. code-block:: python

        class CounterAPI(MethodView):
            def get(self):
                return str(session.get("counter", 0))

            def post(self):
                session["counter"] = session.get("counter", 0) + 1
                return redirect(url_for("counter"))

        app.add_url_rule(
            "/counter", view_func=CounterAPI.as_view("counter")
        )
    """

    def __init_subclass__(cls, **kwa: t.Any) -> None:
        super().__init_subclass__(**kwa)

        if "methods" not in cls.__dict__:
            met = set()

            for bas in cls.__bases__:
                if getattr(bas, "methods", None):
                    met.update(bas.methods)  # type: ignore[attr-defined]

            for key2 in http_method_funcs:
                if hasattr(cls, key2):
                    met.add(key2.upper())

            if met:
                cls.methods = met

    def dispatch(self, **kwa2: t.Any) -> ft.ResponseReturnValue:
        met2 = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if met2 is None and request.method == "HEAD":
            met2 = getattr(self, "get", None)

        assert met2 is not None, f"Unimplemented method {request.method!r}"
        return current_app.ensure_sync(met2)(**kwa2)  # type: ignore[no-any-return]
