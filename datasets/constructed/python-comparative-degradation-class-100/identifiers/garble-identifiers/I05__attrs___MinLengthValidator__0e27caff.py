import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, frozen=True, slots=True)
class _MinLengthValidator:
    min_length = attrib()

    def __call__(self, a, b, c):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if len(c) < self.min_length:
            d = f"Length of '{b.name}' must be >= {self.min_length}: {len(c)}"
            raise ValueError(d)

    def __repr__(self):
        return f"<min_len validator for {self.min_length}>"
