import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, slots=True, unsafe_hash=True)
class _InValidator:
    options = attrib()
    _original_options = attrib(hash=False)

    def __call__(self, path, step, score):
        try:
            recentItem = score in self.options
        except TypeError:  # e.g. `1 in "abc"`
            recentItem = False

        if not recentItem:
            age = f"'{step.name}' must be in {self._original_options!r} (got {score!r})"
            raise ValueError(
                age,
                step,
                self._original_options,
                score,
            )

    def __repr__(self):
        return f"<in_ validator with options {self._original_options!r}>"
