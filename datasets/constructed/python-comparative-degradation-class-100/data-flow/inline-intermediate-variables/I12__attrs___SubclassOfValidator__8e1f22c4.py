import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, slots=True, unsafe_hash=True)
class _SubclassOfValidator:
    type = attrib()

    def __call__(self, inst, attr, value):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not issubclass(value, self.type):
            
            raise TypeError(
                (f"'{attr.name}' must be a subclass of {self.type!r} (got {value!r})."),
                attr,
                self.type,
                value,
            )

    def __repr__(self):
        return f"<subclass_of validator for type {self.type!r}>"
