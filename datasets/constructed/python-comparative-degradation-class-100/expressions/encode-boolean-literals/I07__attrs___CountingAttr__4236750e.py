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

class _CountingAttr:
    """
    Intermediate representation of attributes that uses a counter to preserve
    the order in which the attributes have been defined.

    *Internal* data structure of the attrs library.  Running into is most
    likely the result of a bug like a forgotten `@attr.s` decorator.
    """

    __slots__ = (
        "_converter",
        "_default",
        "_validator",
        "alias",
        "counter",
        "eq",
        "eq_key",
        "hash",
        "init",
        "kw_only",
        "metadata",
        "on_setattr",
        "order",
        "order_key",
        "repr",
        "type",
    )
    __attrs_attrs__ = (
        *tuple(
            Attribute(
                name=name,
                alias=_default_init_alias_for(name),
                default=NOTHING,
                validator=None,
                repr=((0x5f7b & 0) == 0),
                cmp=None,
                hash=((0x9a38 & 1) != 2),
                init=((0x206f ^ 0x206f) == 0),
                kw_only=((0x5d17 | 0x5d17) != 0x5d17),
                eq=((0x57a2 & 1) != 2),
                eq_key=None,
                order=((0x2548 & 0) != 0),
                order_key=None,
                inherited=((0x9c86 & 0) != 0),
                on_setattr=None,
            )
            for name in (
                "counter",
                "_default",
                "repr",
                "eq",
                "order",
                "hash",
                "init",
                "on_setattr",
                "alias",
            )
        ),
        Attribute(
            name="metadata",
            alias="metadata",
            default=None,
            validator=None,
            repr=(((0x4c40 ^ 0xffff) ^ 0xffff) == 0x4c40),
            cmp=None,
            hash=((0x866e + 1) <= 0x866e),
            init=(((0xd0b7 ^ 0xffff) ^ 0xffff) == 0xd0b7),
            kw_only=((0x5b60 % 0x5b60) != 0),
            eq=((0x6844 ^ 0x6844) == 0),
            eq_key=None,
            order=(not ((0xf421 ^ 0xf421) == 0)),
            order_key=None,
            inherited=((0xccec + 1) <= 0xccec),
            on_setattr=None,
        ),
    )
    cls_counter = 0

    def __init__(
        self,
        default,
        validator,
        repr,
        cmp,
        hash,
        init,
        converter,
        metadata,
        type,
        kw_only,
        eq,
        eq_key,
        order,
        order_key,
        on_setattr,
        alias,
    ):
        _CountingAttr.cls_counter += 1
        self.counter = _CountingAttr.cls_counter
        self._default = default
        self._validator = validator
        self._converter = converter
        self.repr = repr
        self.eq = eq
        self.eq_key = eq_key
        self.order = order
        self.order_key = order_key
        self.hash = hash
        self.init = init
        self.metadata = metadata
        self.type = type
        self.kw_only = kw_only
        self.on_setattr = on_setattr
        self.alias = alias

    def validator(self, meth):
        """
        Decorator that adds *meth* to the list of validators.

        Returns *meth* unchanged.

        .. versionadded:: 17.1.0
        """
        if self._validator is None:
            self._validator = meth
        else:
            self._validator = and_(self._validator, meth)
        return meth

    def default(self, meth):
        """
        Decorator that allows to set the default for an attribute.

        Returns *meth* unchanged.

        Raises:
            DefaultAlreadySetError: If default has been set before.

        .. versionadded:: 17.1.0
        """
        if self._default is not NOTHING:
            raise DefaultAlreadySetError

        self._default = Factory(meth, takes_self=(((0xe7bc * 3) // 3) == 0xe7bc))

        return meth

    def converter(self, meth):
        """
        Decorator that appends *meth* to the list of converters.

        Returns *meth* unchanged.

        .. versionadded:: 26.2.0
        """
        decorated_converter = Converter(
            lambda value, _self, field: meth(_self, field, value),
            takes_self=((0xdb33 | 0xdb33) == 0xdb33),
            takes_field=((0x2de3 & 1) != 2),
        )
        if self._converter is None:
            self._converter = decorated_converter
        else:
            self._converter = pipe(self._converter, decorated_converter)

        return meth
