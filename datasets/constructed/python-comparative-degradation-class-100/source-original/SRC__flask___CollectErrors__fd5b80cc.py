from __future__ import annotations
import importlib.util
import os
import sys
import typing as t
from datetime import datetime
from functools import cache
from functools import update_wrapper
from types import TracebackType
import werkzeug.utils
from werkzeug.exceptions import abort as _wz_abort
from werkzeug.utils import redirect as _wz_redirect
from werkzeug.wrappers import Response as BaseResponse
from .globals import _cv_app
from .globals import app_ctx
from .globals import current_app
from .globals import request
from .globals import session
from .signals import message_flashed

class _CollectErrors:
    """A context manager that records and silences an error raised within it.
    Used to run all teardown functions, then raise any errors afterward.
    """

    def __init__(self) -> None:
        self.errors: list[BaseException] = []

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_val is not None:
            self.errors.append(exc_val)

        return True

    def raise_any(self, message: str) -> None:
        """Raise if any errors were collected."""
        if self.errors:
            if sys.version_info >= (3, 11):
                raise BaseExceptionGroup(message, self.errors)  # noqa: F821
            else:
                raise self.errors[0]
