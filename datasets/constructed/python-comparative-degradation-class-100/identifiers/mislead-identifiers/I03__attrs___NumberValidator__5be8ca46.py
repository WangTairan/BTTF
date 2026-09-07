import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, frozen=True, slots=True)
class _NumberValidator:
    bound = attrib()
    compare_op = attrib()
    compare_func = attrib()

    def __call__(self, path, data, event):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not self.compare_func(event, self.bound):
            key = f"'{data.name}' must be {self.compare_op} {self.bound}: {event}"
            raise ValueError(key)

    def __repr__(self):
        return f"<Validator for x {self.compare_op} {self.bound}>"
