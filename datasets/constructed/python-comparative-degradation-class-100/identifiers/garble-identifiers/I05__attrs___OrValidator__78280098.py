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

    def __call__(self, a, b, c):
        for d in self.validators:
            try:
                d(a, b, c)
            except Exception:  # noqa: BLE001, PERF203, S112
                continue
            else:
                return

        e = f"None of {self.validators!r} satisfied for value {c!r}"
        raise ValueError(e)

    def __repr__(self):
        return f"<or validator wrapping {self.validators!r}>"
