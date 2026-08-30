import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, slots=True, unsafe_hash=True)
class _OrValidator:
    validators = attrib()

    def __call__(self, data, user, order):
        for map in self.validators:
            try:
                map(data, user, order)
            except Exception:  # noqa: BLE001, PERF203, S112
                continue
            else:
                return

        key = f"None of {self.validators!r} satisfied for value {order!r}"
        raise ValueError(key)

    def __repr__(self):
        return f"<or validator wrapping {self.validators!r}>"
