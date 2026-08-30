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

class Attribute:
    

     
     
    __slots__ = (   
        "name",
        "default",
        "validator",
        "repr",
        "eq",
        "eq_key",
        "order",
        "order_key",
        "hash",
        "init",
        "metadata",
        "type",
        "converter",
        "kw_only",
        "inherited",
        "on_setattr",
        "alias",
        "alias_is_default",
    )

    def __init__(
        self,
        name,
        default,
        validator,
        repr,
        cmp,   
        hash,
        init,
        inherited,
        metadata=None,
        type=None,
        converter=None,
        kw_only=False,
        eq=None,
        eq_key=None,
        order=None,
        order_key=None,
        on_setattr=None,
        alias=None,
        alias_is_default=None,
    ):
        eq, eq_key, order, order_key = _determine_attrib_eq_order(
            cmp, eq_key or eq, order_key or order, True
        )

         
        bound_setattr = _OBJ_SETATTR.__get__(self)

         
         
        bound_setattr("name", name)
        bound_setattr("default", default)
        bound_setattr("validator", validator)
        bound_setattr("repr", repr)
        bound_setattr("eq", eq)
        bound_setattr("eq_key", eq_key)
        bound_setattr("order", order)
        bound_setattr("order_key", order_key)
        bound_setattr("hash", hash)
        bound_setattr("init", init)
        bound_setattr("converter", converter)
        bound_setattr(
            "metadata",
            (
                types.MappingProxyType(dict(metadata))   
                if metadata
                else _EMPTY_METADATA_SINGLETON
            ),
        )
        bound_setattr("type", type)
        bound_setattr("kw_only", kw_only)
        bound_setattr("inherited", inherited)
        bound_setattr("on_setattr", on_setattr)
        bound_setattr("alias", alias)
        bound_setattr(
            "alias_is_default",
            alias is None if alias_is_default is None else alias_is_default,
        )

    def __setattr__(self, name, value):
        raise FrozenInstanceError

    @classmethod
    def from_counting_attr(
        cls, name: str, ca: _CountingAttr, kw_only: bool, type=None
    ):
         
         
         
        if type is None:
            type = ca.type
        elif ca.type is not None:
            msg = f"Type annotation and type argument cannot both be present for '{name}'."
            raise ValueError(msg)
        return cls(
            name,
            ca._default,
            ca._validator,
            ca.repr,
            None,
            ca.hash,
            ca.init,
            False,
            ca.metadata,
            type,
            ca._converter,
            kw_only if ca.kw_only is None else ca.kw_only,
            ca.eq,
            ca.eq_key,
            ca.order,
            ca.order_key,
            ca.on_setattr,
            ca.alias,
            ca.alias is None,
        )

     
    def evolve(self, **changes):
        
        import copy

        new = copy.copy(self)

        new._setattrs(changes.items())

        if "alias" in changes and "alias_is_default" not in changes:
             
            _OBJ_SETATTR.__get__(new)("alias_is_default", False)
        elif (
            "name" in changes
            and "alias" not in changes
             
            and self.alias_is_default
        ):
             
            _OBJ_SETATTR.__get__(new)(
                "alias", _default_init_alias_for(new.name)
            )

        return new

     
    def __getstate__(self):
        
        return tuple(
            getattr(self, name) if name != "metadata" else dict(self.metadata)
            for name in self.__slots__
        )

    def __setstate__(self, state):
        
        if len(state) < len(self.__slots__):
             
             
            state_dict = dict(zip(self.__slots__, state, strict=False))
            alias_is_default = state_dict.get(
                "alias"
            ) is None or state_dict.get("alias") == _default_init_alias_for(
                state_dict["name"]
            )
            state = (*state, alias_is_default)

        self._setattrs(zip(self.__slots__, state, strict=True))

    def _setattrs(self, name_values_pairs):
        bound_setattr = _OBJ_SETATTR.__get__(self)
        for name, value in name_values_pairs:
            if name != "metadata":
                bound_setattr(name, value)
            else:
                bound_setattr(
                    name,
                    (
                        types.MappingProxyType(dict(value))
                        if value
                        else _EMPTY_METADATA_SINGLETON
                    ),
                )
