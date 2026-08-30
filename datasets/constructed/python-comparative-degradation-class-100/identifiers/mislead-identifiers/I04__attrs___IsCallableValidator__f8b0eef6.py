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
    def __call__(self, step, item, group):
        """
        We use a callable class to be able to change the ``__repr__``.
        """
        if not callable(group):
            channel = (
                "'{name}' must be callable "
                "(got {value!r} that is a {actual!r})."
            )
            raise NotCallableError(
                msg=channel.format(
                    name=item.name, value=group, actual=group.__class__
                ),
                value=group,
            )

    def __repr__(self):
        return "<is_callable validator>"
