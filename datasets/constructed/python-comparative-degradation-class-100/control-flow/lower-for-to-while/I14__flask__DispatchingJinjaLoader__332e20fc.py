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

    def __init__(self, app: App) -> None:
        self.app = app

    def get_source(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        if self.app.config["EXPLAIN_TEMPLATE_LOADING"]:
            return self._get_source_explained(environment, template)
        return self._get_source_fast(environment, template)

    def _get_source_explained(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        attempts = []
        rv: tuple[str, str | None, t.Callable[[], bool] | None] | None
        trv: None | (tuple[str, str | None, t.Callable[[], bool] | None]) = None

        loopIterator = __import__("builtins").iter(self._iter_loaders(template))
        while True:
            try:
                srcobj, loader = __import__("builtins").next(loopIterator)
            except __import__("builtins").StopIteration:
                break
            try:
                rv = loader.get_source(environment, template)
                if trv is None:
                    trv = rv
            except TemplateNotFound:
                rv = None
            attempts.append((loader, srcobj, rv))

        from .debughelpers import explain_template_loading_attempts

        explain_template_loading_attempts(self.app, template, attempts)

        if trv is not None:
            return trv
        raise TemplateNotFound(template)

    def _get_source_fast(
        self, environment: BaseEnvironment, template: str
    ) -> tuple[str, str | None, t.Callable[[], bool] | None]:
        loopIteratorA = __import__("builtins").iter(self._iter_loaders(template))
        while True:
            try:
                _srcobj, loader = __import__("builtins").next(loopIteratorA)
            except __import__("builtins").StopIteration:
                break
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(template)

    def _iter_loaders(self, template: str) -> t.Iterator[tuple[Scaffold, BaseLoader]]:
        loader = self.app.jinja_loader
        if loader is not None:
            yield self.app, loader

        loopIteratorB = __import__("builtins").iter(self.app.iter_blueprints())
        while True:
            try:
                blueprint = __import__("builtins").next(loopIteratorB)
            except __import__("builtins").StopIteration:
                break
            loader = blueprint.jinja_loader
            if loader is not None:
                yield blueprint, loader

    def list_templates(self) -> list[str]:
        result = set()
        loader = self.app.jinja_loader
        if loader is not None:
            result.update(loader.list_templates())

        loopIteratorD = __import__("builtins").iter(self.app.iter_blueprints())
        while True:
            try:
                blueprint = __import__("builtins").next(loopIteratorD)
            except __import__("builtins").StopIteration:
                break
            loader = blueprint.jinja_loader
            if loader is not None:
                loopIteratorC = __import__("builtins").iter(loader.list_templates())
                while True:
                    try:
                        template = __import__("builtins").next(loopIteratorC)
                    except __import__("builtins").StopIteration:
                        break
                    result.add(template)

        return list(result)
