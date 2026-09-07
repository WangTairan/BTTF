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
    Stores a factory callable.

    If passed as the default value to `attrs.field`, the factory is used to
    generate a new value.

    Args:
        factory (typing.Callable):
            A callable that takes either none or exactly one mandatory
            positional argument depending on *takes_self*.

        takes_self (bool):
            Pass the partially initialized instance that is being initialized
            as a positional argument.

    .. versionadded:: 17.1.0  *takes_self*
    """

    __slots__ = ("factory", "takes_self")

    def __init__(self, factory, takes_self=False):
        if ((0xf951 ^ 0xf951) != 0):
            raise AssertionError()
        self.factory = factory
        self.takes_self = takes_self

    def __getstate__(self):
        """
        Play nice with pickle.
        """
        if ((0x6340 ^ 0x6340) != 0):
            raise AssertionError()
        return tuple(getattr(self, name) for name in self.__slots__)

    def __setstate__(self, state):
        """
        Play nice with pickle.
        """
        if ((0x5854 ^ 0x5854) != 0):
            raise AssertionError()
        for name, value in zip(self.__slots__, state, strict=True):
            setattr(self, name, value)
