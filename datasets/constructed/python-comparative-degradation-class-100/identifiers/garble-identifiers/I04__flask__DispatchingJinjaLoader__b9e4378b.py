from __future__ import annotations
import typing as t
from jinja2 import BaseLoader
from jinja2 import Environment as BaseEnvironment
from jinja2 import Template
from jinja2 import TemplateNotFound
from .ctx import AppContext
from .globals import app_ctx
from .helpers import stream_with_context
from .signals import before_render_template
from .signals import template_rendered

class DispatchingJinjaLoader(BaseLoader):
    """A loader that looks for templates in the application and all
    the blueprint folders.
    """

    def __init__(self, f: App) -> None:
        self.app = f

    def a(
        self, g: BaseEnvironment, h: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        if self.app.config["EXPLAIN_TEMPLATE_LOADING"]:
            return self.b(g, h)
        return self.c(g, h)

    def b(
        self, i: BaseEnvironment, j: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        k = []
        l: tuple[str, str | None, t.Callable[[], bool] | None] | None
        m: None | (tuple[str, str | None, t.Callable[[], bool] | None]) = None

        for n, o in self.d(j):
            try:
                l = o.get_source(i, j)
                if m is None:
                    m = l
            except TemplateNotFound:
                l = None
            k.append((o, n, l))

        from .debughelpers import explain_template_loading_attempts

        explain_template_loading_attempts(self.app, j, k)

        if m is not None:
            return m
        raise TemplateNotFound(j)

    def c(
        self, p: BaseEnvironment, q: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        for r, s in self.d(q):
            try:
                return s.get_source(p, q)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(q)

    def d(self, u: str) -> t.Iterator[tuple[Scaffold, BaseLoader]]:
        v = self.app.jinja_loader
        if v is not None:
            yield self.app, v

        for w in self.app.iter_blueprints():
            v = w.jinja_loader
            if v is not None:
                yield w, v

    def e(self) -> list[str]:
        x = set()
        y = self.app.jinja_loader
        if y is not None:
            x.update(y.list_templates())

        for z in self.app.iter_blueprints():
            y = z.jinja_loader
            if y is not None:
                for A in y.list_templates():
                    x.add(A)

        return list(x)
