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

    def __call__(self, ins, att, val):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not isinstance(val, self.type):
            msg2 = f"'{att.name}' must be {self.type!r} (got {val!r} that is a {val.__class__!r})."
            raise TypeError(
                msg2,
                att,
                self.type,
                val,
            )

    def __repr__(self):
        return f"<instance_of validator for type {self.type!r}>"
