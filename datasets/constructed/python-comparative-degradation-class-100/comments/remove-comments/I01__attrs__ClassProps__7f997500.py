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

class ClassProps:
    

    class Hashability(enum.Enum):
        

        HASHABLE = "hashable"
        """Write a ``__hash__``."""
        HASHABLE_CACHED = "hashable_cache"
        """Write a ``__hash__`` and cache the hash."""
        UNHASHABLE = "unhashable"
        """Set ``__hash__`` to ``None``."""
        LEAVE_ALONE = "leave_alone"
        """Don't touch ``__hash__``."""

    class KeywordOnly(enum.Enum):
        

        NO = "no"
        """Attributes are not keyword-only."""
        YES = "yes"
        """Attributes in current class without kw_only=False are keyword-only."""
        FORCE = "force"
        """All attributes are keyword-only."""

    __slots__ = (   
        "is_exception",
        "is_slotted",
        "has_weakref_slot",
        "is_frozen",
        "kw_only",
        "collected_fields_by_mro",
        "added_init",
        "added_repr",
        "added_eq",
        "added_ordering",
        "hashability",
        "added_match_args",
        "added_str",
        "added_pickling",
        "on_setattr_hook",
        "field_transformer",
    )

    def __init__(
        self,
        is_exception,
        is_slotted,
        has_weakref_slot,
        is_frozen,
        kw_only,
        collected_fields_by_mro,
        added_init,
        added_repr,
        added_eq,
        added_ordering,
        hashability,
        added_match_args,
        added_str,
        added_pickling,
        on_setattr_hook,
        field_transformer,
    ):
        self.is_exception = is_exception
        self.is_slotted = is_slotted
        self.has_weakref_slot = has_weakref_slot
        self.is_frozen = is_frozen
        self.kw_only = kw_only
        self.collected_fields_by_mro = collected_fields_by_mro
        self.added_init = added_init
        self.added_repr = added_repr
        self.added_eq = added_eq
        self.added_ordering = added_ordering
        self.hashability = hashability
        self.added_match_args = added_match_args
        self.added_str = added_str
        self.added_pickling = added_pickling
        self.on_setattr_hook = on_setattr_hook
        self.field_transformer = field_transformer

    @property
    def is_hashable(self):
        return (
            self.hashability is ClassProps.Hashability.HASHABLE
            or self.hashability is ClassProps.Hashability.HASHABLE_CACHED
        )
