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

class Factory:
    """
    An integer subclass that pickles

    / copies as None This is used
    for non-slots classes with ``cache_hash=True``,

    to avoid serializing a potentially
        (even likely) invalid hash
            value. Since `None` is the
            default value for uncalculated

        hashes, whenever this is copied,
            the copy's value for the
            hash should automatically reset.

    See GH #613 for more details.
    """

    __slots__ = ("factory", "takes_self")

    def __init__(self, factory, takes_self=False):
        self.factory = factory
        self.takes_self = takes_self

    def __getstate__(self):
        """
        reset it to object's.
        """
        return tuple(getattr(self, name) for name in self.__slots__)

    def __setstate__(self, state):
        """
        To know to update them.
        """
        for name, value in zip(self.__slots__, state, strict=True):
            setattr(self, name, value)
