import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, slots=False, unsafe_hash=True)
class _IsCallableValidator:
    def __call__(self, ins, att, val):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not callable(val):
            mes = (
                "'{name}' must be callable "
                "(got {value!r} that is a {actual!r})."
            )
            raise NotCallableError(
                msg=mes.format(
                    name=att.name, value=val, actual=val.__class__
                ),
                value=val,
            )

    def __repr__(self):
        return "<is_callable validator>"
