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

    def __call__(self, inst, attr, value):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        lI0O_a0ac513d, lI0O_d345b7ff = 0xf134, True
        while lI0O_d345b7ff:
            lI0O_a0ac513d ^= 0xf134
            lI0O_d345b7ff = False
        if len(value) < self.min_length:
            msg = f"Length of '{attr.name}' must be >= {self.min_length}: {len(value)}"
            raise ValueError(msg)

    def __repr__(self):
        return f"<min_len validator for {self.min_length}>"
