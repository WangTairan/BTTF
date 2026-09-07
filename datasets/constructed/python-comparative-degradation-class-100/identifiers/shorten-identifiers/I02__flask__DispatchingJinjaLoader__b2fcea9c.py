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

    def __init__(self, app2: App) -> None:
        self.app = app2

    def get(
        self, env: BaseEnvironment, tem: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        if self.app.config["EXPLAIN_TEMPLATE_LOADING"]:
            return self.get2(env, tem)
        return self.get3(env, tem)

    def get2(
        self, env2: BaseEnvironment, tem2: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        att = []
        rv2: tuple[str, str | None, t.Callable[[], bool] | None] | None
        trv2: None | (tuple[str, str | None, t.Callable[[], bool] | None]) = None

        for src, loa in self.iter(tem2):
            try:
                rv2 = loa.get_source(env2, tem2)
                if trv2 is None:
                    trv2 = rv2
            except TemplateNotFound:
                rv2 = None
            att.append((loa, src, rv2))

        from .debughelpers import explain_template_loading_attempts

        explain_template_loading_attempts(self.app, tem2, att)

        if trv2 is not None:
            return trv2
        raise TemplateNotFound(tem2)

    def get3(
        self, env3: BaseEnvironment, tem3: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        for src2, loa2 in self.iter(tem3):
            try:
                return loa2.get_source(env3, tem3)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(tem3)

    def iter(self, tem4: str) -> t.Iterator[tuple[Scaffold, BaseLoader]]:
        loa3 = self.app.jinja_loader
        if loa3 is not None:
            yield self.app, loa3

        for blu in self.app.iter_blueprints():
            loa3 = blu.jinja_loader
            if loa3 is not None:
                yield blu, loa3

    def list2(self) -> list[str]:
        res = set()
        loa4 = self.app.jinja_loader
        if loa4 is not None:
            res.update(loa4.list_templates())

        for blu2 in self.app.iter_blueprints():
            loa4 = blu2.jinja_loader
            if loa4 is not None:
                for tem5 in loa4.list_templates():
                    res.add(tem5)

        return list(res)
