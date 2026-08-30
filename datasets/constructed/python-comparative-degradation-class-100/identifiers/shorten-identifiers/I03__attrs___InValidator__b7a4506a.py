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

    def __call__(self, ins, att, val):
        try:
            in2 = val in self.options
        except TypeError:  # e.g. `1 in "abc"`
            in2 = False

        if not in2:
            msg2 = f"'{att.name}' must be in {self._original_options!r} (got {val!r})"
            raise ValueError(
                msg2,
                att,
                self._original_options,
                val,
            )

    def __repr__(self):
        return f"<in_ validator with options {self._original_options!r}>"
