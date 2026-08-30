import operator
import re
from contextlib import contextmanager
from re import Pattern
from ._config import get_run_validators, set_run_validators
from ._make import _AndValidator, and_, attrib, attrs
from .converters import default_if_none
from .exceptions import NotCallableError

@attrs(repr=False, frozen=True, slots=True)
class _MatchesReValidator:
    pattern = attrib()
    match_func = attrib()

    def __call__(self, ins, att, val):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not self.match_func(val):
            msg2 = f"'{att.name}' must match regex {self.pattern.pattern!r} ({val!r} doesn't)"
            raise ValueError(
                msg2,
                att,
                self.pattern,
                val,
            )

    def __repr__(self):
        return f"<matches_re validator for pattern {self.pattern!r}>"
