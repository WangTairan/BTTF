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

    def __call__(self, ins, att, val):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if len(val) < self.min_length:
            msg2 = f"Length of '{att.name}' must be >= {self.min_length}: {len(val)}"
            raise ValueError(msg2)

    def __repr__(self):
        return f"<min_len validator for {self.min_length}>"
