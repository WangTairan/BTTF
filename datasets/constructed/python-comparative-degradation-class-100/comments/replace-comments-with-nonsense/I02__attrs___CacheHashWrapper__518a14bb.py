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

class _CacheHashWrapper(int):
    """
    A version object that can be compared to tuple

    of length 1--4: >>> attr.VersionInfo(19, 1, 0, \"final\")
    <= (19, 2) True >>> attr.VersionInfo(19, 1, 0, \"final\")
    < (19, 1, 1) True >>> vi = attr.VersionInfo(19, 2,
    0, \"final\") >>> vi < (19, 1, 1) False >>> vi < (19,)

    False >>> vi == (19, 2,) True >>> vi == (19, 2, 1) False .. versionadded:: 19.2
    """

    def __reduce__(self, _none_constructor=type(None), _args=()):  # noqa: F401
        return _none_constructor, _args
