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
    def __call__(self, a, b, c):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not callable(c):
            d = (
                "'{name}' must be callable "
                "(got {value!r} that is a {actual!r})."
            )
            raise NotCallableError(
                msg=d.format(
                    name=b.name, value=c, actual=c.__class__
                ),
                value=c,
            )

    def __repr__(self):
        return "<is_callable validator>"
