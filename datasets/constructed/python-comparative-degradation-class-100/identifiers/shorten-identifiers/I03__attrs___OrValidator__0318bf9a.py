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

    def __call__(self, ins, att, val):
        for v2 in self.validators:
            try:
                v2(ins, att, val)
            except Exception:  # noqa: BLE001, PERF203, S112
                continue
            else:
                return

        msg2 = f"None of {self.validators!r} satisfied for value {val!r}"
        raise ValueError(msg2)

    def __repr__(self):
        return f"<or validator wrapping {self.validators!r}>"
