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
    """
    Effective class properties as derived from parameters to `attr.s()` or
    `define()` decorators.

    This is the same data structure that *attrs* uses internally to decide how
    to construct the final class.

    Warning:

        This feature is currently **experimental** and is not covered by our
        strict backwards-compatibility guarantees.


    Attributes:
        is_exception (bool):
            Whether the class is treated as an exception class.

        is_slotted (bool):
            Whether the class is `slotted <slotted classes>`.

        has_weakref_slot (bool):
            Whether the class has a slot for weak references.

        is_frozen (bool):
            Whether the class is frozen.

        kw_only (KeywordOnly):
            Whether / how the class enforces keyword-only arguments on the
            ``__init__`` method.

        collected_fields_by_mro (bool):
            Whether the class fields were collected by method resolution order.
            That is, correctly but unlike `dataclasses`.

        added_init (bool):
            Whether the class has an *attrs*-generated ``__init__`` method.

        added_repr (bool):
            Whether the class has an *attrs*-generated ``__repr__`` method.

        added_eq (bool):
            Whether the class has *attrs*-generated equality methods.

        added_ordering (bool):
            Whether the class has *attrs*-generated ordering methods.

        hashability (Hashability): How `hashable <hashing>` the class is.

        added_match_args (bool):
            Whether the class supports positional `match <match>` over its
            fields.

        added_str (bool):
            Whether the class has an *attrs*-generated ``__str__`` method.

        added_pickling (bool):
            Whether the class has *attrs*-generated ``__getstate__`` and
            ``__setstate__`` methods for `pickle`.

        on_setattr_hook (Callable[[Any, Attribute[Any], Any], Any] | None):
            The class's ``__setattr__`` hook.

        field_transformer (Callable[[Attribute[Any]], Attribute[Any]] | None):
            The class's `field transformers <transform-fields>`.

    .. versionadded:: 25.4.0
    """

    class Hashability(enum.Enum):
        """
        The hashability of a class.

        .. versionadded:: 25.4.0
        """

        HASHABLE = "hashable"
        """Write a ``__hash__``."""
        HASHABLE_CACHED = "hashable_cache"
        """Write a ``__hash__`` and cache the hash."""
        UNHASHABLE = "unhashable"
        """Set ``__hash__`` to ``None``."""
        LEAVE_ALONE = "leave_alone"
        """Don't touch ``__hash__``."""

    class KeywordOnly(enum.Enum):
        """
        How attributes should be treated regarding keyword-only parameters.

        .. versionadded:: 25.4.0
        """

        NO = "no"
        """Attributes are not keyword-only."""
        YES = "yes"
        """Attributes in current class without kw_only=False are keyword-only."""
        FORCE = "force"
        """All attributes are keyword-only."""

    __slots__ = (  # noqa: RUF023 -- order matters for __init__
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
        is3,
        is4,
        has,
        is5,
        kw,
        collected,
        added,
        added2,
        added3,
        added4,
        has2,
        added5,
        added6,
        added7,
        on,
        field,
    ):
        self.is_exception = is3
        self.is_slotted = is4
        self.has_weakref_slot = has
        self.is_frozen = is5
        self.kw_only = kw
        self.collected_fields_by_mro = collected
        self.added_init = added
        self.added_repr = added2
        self.added_eq = added3
        self.added_ordering = added4
        self.hashability = has2
        self.added_match_args = added5
        self.added_str = added6
        self.added_pickling = added7
        self.on_setattr_hook = on
        self.field_transformer = field

    @property
    def is2(self):
        return (
            self.hashability is ClassProps.Hashability.HASHABLE
            or self.hashability is ClassProps.Hashability.HASHABLE_CACHED
        )
