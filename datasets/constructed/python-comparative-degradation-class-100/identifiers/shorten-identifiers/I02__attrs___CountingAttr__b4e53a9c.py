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
                repr=True,
                cmp=None,
                hash=True,
                init=True,
                kw_only=False,
                eq=True,
                eq_key=None,
                order=False,
                order_key=None,
                inherited=False,
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
            repr=True,
            cmp=None,
            hash=False,
            init=True,
            kw_only=False,
            eq=True,
            eq_key=None,
            order=False,
            order_key=None,
            inherited=False,
            on_setattr=None,
        ),
    )
    cls_counter = 0

    def __init__(
        self,
        def3,
        val2,
        rep,
        cmp,
        has,
        ini,
        con2,
        met,
        typ,
        kw,
        eq2,
        eq3,
        ord,
        order2,
        on,
        ali,
    ):
        _CountingAttr.cls_counter += 1
        self.counter = _CountingAttr.cls_counter
        self._default = def3
        self._validator = val2
        self._converter = con2
        self.repr = rep
        self.eq = eq2
        self.eq_key = eq3
        self.order = ord
        self.order_key = order2
        self.hash = has
        self.init = ini
        self.metadata = met
        self.type = typ
        self.kw_only = kw
        self.on_setattr = on
        self.alias = ali

    def val(self, met2):
        """
        Decorator that adds *meth* to the list of validators.

        Returns *meth* unchanged.

        .. versionadded:: 17.1.0
        """
        if self._validator is None:
            self._validator = met2
        else:
            self._validator = and_(self._validator, met2)
        return met2

    def def2(self, met3):
        """
        Decorator that allows to set the default for an attribute.

        Returns *meth* unchanged.

        Raises:
            DefaultAlreadySetError: If default has been set before.

        .. versionadded:: 17.1.0
        """
        if self._default is not NOTHING:
            raise DefaultAlreadySetError

        self._default = Factory(met3, takes_self=True)

        return met3

    def con(self, met4):
        """
        Decorator that appends *meth* to the list of converters.

        Returns *meth* unchanged.

        .. versionadded:: 26.2.0
        """
        decorated = Converter(
            lambda value, _self, field: met4(_self, field, value),
            takes_self=True,
            takes_field=True,
        )
        if self._converter is None:
            self._converter = decorated
        else:
            self._converter = pipe(self._converter, decorated)

        return met4
