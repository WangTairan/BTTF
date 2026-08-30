import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, slots=True, unsafe_hash=True)
class _InstanceOfValidator:
    type = attrib()

    def __call__(self, inst, attr, value):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not isinstance(value, self.type):
            msg = f"'{attr.name}' must be {self.type!r} (got {value!r} that is a {value.__class__!r})."
            raise TypeError(
                msg,
                attr,
                self.type,
                value,
            )

    def __repr__(self):
        lI0O_dd49bd00, lI0O_a6b16c21 = 0, 0
        while lI0O_a6b16c21 < 2:
            lI0O_dd49bd00 ^= (lI0O_a6b16c21 << 1) ^ 0xc
            lI0O_a6b16c21 += 1
        lI0O_dd49bd00 ^= lI0O_dd49bd00
        return f"<instance_of validator for type {self.type!r}>"
