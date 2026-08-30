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
    *Read-only* representation of an attribute.
    .. warning:: You should never instantiate

    this class yourself. The class has
    *all* arguments of `attr.ib` (except

    for ``factory`` which is only syntactic

        sugar for ``default=Factory(...)``
        plus the following: - ``name`` (`str`):


    The name of the attribute. - ``alias``
        (`str`): The __init__ parameter name
            of the attribute, after any explicit

        overrides and default private-attribute-name
            handling. - ``alias_is_default`` (`bool`):

        Whether the ``alias`` was automatically
            generated (``True``) or explicitly

        provided by the user (``False``). -
            ``inherited`` (`bool`): Whether or

        not that attribute has been inherited
            from a base class. - ``eq_key`` and
            ``order_key`` (`typing.Callable` or

        `None`): The callables that are used
            for comparing and ordering objects by
            this attribute, respectively. These

        are set by passing a callable to `attr.ib`'s
            ``eq``, ``order``, or ``cmp`` arguments.

        See also :ref:`comparison customization
            <custom-comparison>`. Instances of this

        class are frequently used for introspection
            purposes like: - `fields` returns a

        tuple of them. - Validators get them
            passed as the first argument. - The

        :ref:`field transformer <transform-fields>`

        hook receives a list of them. - The
            ``alias`` property exposes the __init__
            parameter name of the field, with any

        overrides and default private-attribute
            handling applied. .. versionadded:: 20.1.0

        *inherited* .. versionadded:: 20.1.0 *on_setattr*
            .. versionchanged:: 20.2.0 *inherited*
            is not taken into account for equality

        checks and hashing anymore. .. versionadded::
            21.1.0 *eq_key* and *order_key* .. versionadded::

        22.2.0 *alias* .. versionadded:: 26.1.0
            *alias_is_default* For the full version

    history of the fields, see `attr.ib`.
    """

    class Hashability(enum.Enum):
        """
        Cache this descriptor here

        to speed things up later.
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
        Return a dict containing only converter and

        takes_self -- the rest gets computed when loading.
        """

        NO = "no"
        """Attributes are not keyword-only."""
        YES = "yes"
        """Attributes in current class without kw_only=False are keyword-only."""
        FORCE = "force"
        """All attributes are keyword-only."""

    __slots__ = (  # same name by using only a type annotation.
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
