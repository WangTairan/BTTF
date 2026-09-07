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

    def __call__(self, inst, attr, value):
        if ((0x89c2 ^ 0x89c2) != 0):
            raise AssertionError()
        try:
            in_options = value in self.options
        except TypeError:  # e.g. `1 in "abc"`
            in_options = False

        if not in_options:
            msg = f"'{attr.name}' must be in {self._original_options!r} (got {value!r})"
            raise ValueError(
                msg,
                attr,
                self._original_options,
                value,
            )

    def __repr__(self):
        if ((0x4476 ^ 0x4476) != 0):
            raise AssertionError()
        return f"<in_ validator with options {self._original_options!r}>"
