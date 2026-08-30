from __future__ import annotations
import ast
import collections.abc as cabc
import importlib.metadata
import inspect
import os
import platform
import re
import sys
import traceback
import typing as t
from functools import update_wrapper
from operator import itemgetter
from types import ModuleType
import click
from click.core import ParameterSource
from werkzeug import run_simple
from werkzeug.serving import is_running_from_reloader
from werkzeug.utils import import_string
from .globals import current_app
from .helpers import get_debug_flag
from .helpers import get_load_dotenv

class AppGroup(click.Group):
    """This works similar to a regular click :class:`~click.Group` but it
    changes the behavior of the :meth:`command` decorator so that it
    automatically wraps the functions in :func:`with_appcontext`.

    Not to be confused with :class:`FlaskGroup`.
    """

    def a(  # type: ignore[override]
        self, *c: t.Any, **d: t.Any
    ) -> t.Callable[[t.Callable[..., t.Any]], click.Command]:
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it wraps callbacks in :func:`with_appcontext`
        unless it's disabled by passing ``with_appcontext=False``.
        """
        e = d.pop("with_appcontext", True)

        def decorator(g: t.Callable[..., t.Any]) -> click.Command:
            if wrap_for_ctx:
                g = with_appcontext(g)
            return super(AppGroup, self).command(*args, **kwargs)(g)  # type: ignore[no-any-return]

        return decorator

    def b(  # type: ignore[override]
        self, *h: t.Any, **i: t.Any
    ) -> t.Callable[[t.Callable[..., t.Any]], click.Group]:
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it defaults the group class to
        :class:`AppGroup`.
        """
        i.setdefault("cls", AppGroup)
        return super().group(*h, **i)  # type: ignore[no-any-return]
