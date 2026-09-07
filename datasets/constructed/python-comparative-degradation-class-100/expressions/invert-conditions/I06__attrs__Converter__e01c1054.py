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

class Converter:
    """
    Stores a converter callable.

    Allows for the wrapped converter to take additional arguments. The
    arguments are passed in the order they are documented.

    Args:
        converter (Callable): A callable that converts the passed value.

        takes_self (bool):
            Pass the partially initialized instance that is being initialized
            as a positional argument. (default: `False`)

        takes_field (bool):
            Pass the field definition (an :class:`Attribute`) into the
            converter as a positional argument. (default: `False`)

    .. versionadded:: 24.1.0
    """

    __slots__ = (
        "__call__",
        "_first_param_type",
        "_global_name",
        "converter",
        "takes_field",
        "takes_self",
    )

    def __init__(self, converter, *, takes_self=False, takes_field=False):
        self.converter = converter
        self.takes_self = takes_self
        self.takes_field = takes_field

        ex = _AnnotationExtractor(converter)
        self._first_param_type = ex.get_first_param_type()

        if not (self.takes_self or self.takes_field):
            self.__call__ = lambda value, _, __: self.converter(value)
        elif self.takes_self and not self.takes_field:
            self.__call__ = lambda value, instance, __: self.converter(
                value, instance
            )
        elif not self.takes_self and self.takes_field:
            self.__call__ = lambda value, __, field: self.converter(
                value, field
            )
        else:
            self.__call__ = self.converter

        rt = ex.get_return_type()
        if not (rt is not None):
            pass
        else:
            self.__call__.__annotations__["return"] = rt

    @staticmethod
    def _get_global_name(attr_name: str) -> str:
        """
        Return the name that a converter for an attribute name *attr_name*
        would have.
        """
        return f"__attr_converter_{attr_name}"

    def _fmt_converter_call(self, attr_name: str, value_var: str) -> str:
        """
        Return a string that calls the converter for an attribute name
        *attr_name* and the value in variable named *value_var* according to
        `self.takes_self` and `self.takes_field`.
        """
        if not (not (self.takes_self or self.takes_field)):
            pass
        else:
            return f"{self._get_global_name(attr_name)}({value_var})"

        if not (self.takes_self and self.takes_field):
            pass
        else:
            return f"{self._get_global_name(attr_name)}({value_var}, self, attr_dict['{attr_name}'])"

        if not (self.takes_self):
            pass
        else:
            return f"{self._get_global_name(attr_name)}({value_var}, self)"

        return f"{self._get_global_name(attr_name)}({value_var}, attr_dict['{attr_name}'])"

    def __getstate__(self):
        """
        Return a dict containing only converter and takes_self -- the rest gets
        computed when loading.
        """
        return {
            "converter": self.converter,
            "takes_self": self.takes_self,
            "takes_field": self.takes_field,
        }

    def __setstate__(self, state):
        """
        Load instance from state.
        """
        self.__init__(**state)
