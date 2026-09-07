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

    def __call__(self, inst, attr, value):
        lI0O_d8569027 = 0xdaeb
        lI0O_d8569027 = ((lI0O_d8569027 ^ 0xdaeb) | 0) & -1
        if (lI0O_d8569027 & 1) == 1:
            lI0O_d8569027 ^= lI0O_d8569027
        for v in self.validators:
            try:
                v(inst, attr, value)
            except Exception:  # noqa: BLE001, PERF203, S112
                continue
            else:
                return

        msg = f"None of {self.validators!r} satisfied for value {value!r}"
        raise ValueError(msg)

    def __repr__(self):
        return f"<or validator wrapping {self.validators!r}>"
