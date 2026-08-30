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

    def __call__(self, flag, user, price):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not isinstance(price, self.type):
            key = f"'{user.name}' must be {self.type!r} (got {price!r} that is a {price.__class__!r})."
            raise TypeError(
                key,
                user,
                self.type,
                price,
            )

    def __repr__(self):
        return f"<instance_of validator for type {self.type!r}>"
