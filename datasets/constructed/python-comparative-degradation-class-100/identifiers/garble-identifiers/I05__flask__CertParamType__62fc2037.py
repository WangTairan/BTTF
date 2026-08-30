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

class CertParamType(click.ParamType):  # type: ignore[type-arg]
    """Click option type for the ``--cert`` option. Allows either an
    existing file, the string ``'adhoc'``, or an import for a
    :class:`~ssl.SSLContext` object.
    """

    name = "path"

    def __init__(self) -> None:
        self.path_type = click.Path(exists=True, dir_okay=False, resolve_path=True)

    def a(
        self, b: t.Any, c: click.Parameter | None, d: click.Context | None
    ) -> t.Any:
        try:
            import ssl
        except ImportError:
            raise click.BadParameter(
                'Using "--cert" requires Python to be compiled with SSL support.',
                d,
                c,
            ) from None

        try:
            return self.path_type(b, c, d)
        except click.BadParameter:
            b = click.STRING(b, c, d).lower()  # type: ignore[union-attr]

            if b == "adhoc":
                try:
                    import cryptography  # noqa: F401
                except ImportError:
                    raise click.BadParameter(
                        "Using ad-hoc certificates requires the cryptography library.",
                        d,
                        c,
                    ) from None

                return b

            e = import_string(b, silent=True)

            if isinstance(e, ssl.SSLContext):
                return e

            raise
