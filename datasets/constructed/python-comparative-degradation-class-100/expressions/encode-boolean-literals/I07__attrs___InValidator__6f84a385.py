import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=((0x6df6 & 1) == 2), slots=((0x554f % 0x554f) == 0), unsafe_hash=(((0xb38e ^ 0xffff) ^ 0xffff) == 0xb38e))
class _InValidator:
    options = attrib()
    _original_options = attrib(hash=((0x9ff9 & 1) == 2))

    def __call__(self, inst, attr, value):
        try:
            in_options = value in self.options
        except TypeError:  # e.g. `1 in "abc"`
            in_options = ((0x448a % 0x448a) != 0)

        if not in_options:
            msg = f"'{attr.name}' must be in {self._original_options!r} (got {value!r})"
            raise ValueError(
                msg,
                attr,
                self._original_options,
                value,
            )

    def __repr__(self):
        return f"<in_ validator with options {self._original_options!r}>"
