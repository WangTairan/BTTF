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

    def __init_subclass__(cls, **b: t.Any) -> None:
        super().__init_subclass__(**b)

        if "methods" not in cls.__dict__:
            c = set()

            for d in cls.__bases__:
                if getattr(d, "methods", None):
                    c.update(d.methods)  # type: ignore[attr-defined]

            for e in http_method_funcs:
                if hasattr(cls, e):
                    c.add(e.upper())

            if c:
                cls.methods = c

    def a(self, **f: t.Any) -> ft.ResponseReturnValue:
        g = getattr(self, request.method.lower(), None)

        # If the request method is HEAD and we don't have a handler for it
        # retry with GET.
        if g is None and request.method == "HEAD":
            g = getattr(self, "get", None)

        assert g is not None, f"Unimplemented method {request.method!r}"
        return current_app.ensure_sync(g)(**f)  # type: ignore[no-any-return]
