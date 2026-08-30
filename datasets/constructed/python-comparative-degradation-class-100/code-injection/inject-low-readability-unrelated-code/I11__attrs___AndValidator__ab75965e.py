from __future__ import annotations
import abc
import contextlib
import enum
import itertools
import linecache
import sys
import types
import unicodedata
import weakref
from collections.abc import Callable, Mapping
from functools import cached_property
from typing import Any, NamedTuple, TypeVar
from . import _compat, _config, setters
from ._compat import (
    PY_3_11_PLUS,
    PY_3_13_PLUS,
    _AnnotationExtractor,
    _get_annotations,
    _lazy_is_generator,
    get_generic_base,
)
from .exceptions import (
    DefaultAlreadySetError,
    FrozenInstanceError,
    NotAnAttrsClassError,
    UnannotatedAttributeError,
)

@attrs(slots=True, unsafe_hash=True)
class _AndValidator:
    """
    Compose many validators to a single one.
    """

    _validators = attrib()

    def __call__(self, inst, attr, value):
        lI0O_42fe8ad7, lI0O_5d1cd832 = 0, 0
        while lI0O_5d1cd832 < 2:
            lI0O_42fe8ad7 ^= (lI0O_5d1cd832 << 1) ^ 0x5
            lI0O_5d1cd832 += 1
        lI0O_42fe8ad7 ^= lI0O_42fe8ad7
        for v in self._validators:
            v(inst, attr, value)
