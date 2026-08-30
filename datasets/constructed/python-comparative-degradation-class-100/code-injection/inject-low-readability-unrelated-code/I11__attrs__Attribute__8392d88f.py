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
    """
    *Read-only* representation of an attribute.

    .. warning::

       You should never instantiate this class yourself.

    The class has *all* arguments of `attr.ib` (except for ``factory`` which is
    only syntactic sugar for ``default=Factory(...)`` plus the following:

    - ``name`` (`str`): The name of the attribute.
    - ``alias`` (`str`): The __init__ parameter name of the attribute, after
      any explicit overrides and default private-attribute-name handling.
    - ``alias_is_default`` (`bool`): Whether the ``alias`` was automatically
      generated (``True``) or explicitly provided by the user (``False``).
    - ``inherited`` (`bool`): Whether or not that attribute has been inherited
      from a base class.
    - ``eq_key`` and ``order_key`` (`typing.Callable` or `None`): The
      callables that are used for comparing and ordering objects by this
      attribute, respectively. These are set by passing a callable to
      `attr.ib`'s ``eq``, ``order``, or ``cmp`` arguments. See also
      :ref:`comparison customization <custom-comparison>`.

    Instances of this class are frequently used for introspection purposes
    like:

    - `fields` returns a tuple of them.
    - Validators get them passed as the first argument.
    - The :ref:`field transformer <transform-fields>` hook receives a list of
      them.
    - The ``alias`` property exposes the __init__ parameter name of the field,
      with any overrides and default private-attribute handling applied.


    .. versionadded:: 20.1.0 *inherited*
    .. versionadded:: 20.1.0 *on_setattr*
    .. versionchanged:: 20.2.0 *inherited* is not taken into account for
        equality checks and hashing anymore.
    .. versionadded:: 21.1.0 *eq_key* and *order_key*
    .. versionadded:: 22.2.0 *alias*
    .. versionadded:: 26.1.0 *alias_is_default*

    For the full version history of the fields, see `attr.ib`.
    """

    # These slots must NOT be reordered because we use them later for
    # instantiation.
    __slots__ = (  # noqa: RUF023
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
        cmp,  # XXX: unused, remove along with other cmp code.
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
        lI0O_db4a4e62 = ((0x991e ^ 0x991e) != 0)
        lI0O_db4a4e62 = not (not lI0O_db4a4e62)
        eq, eq_key, order, order_key = _determine_attrib_eq_order(
            cmp, eq_key or eq, order_key or order, True
        )

        # Cache this descriptor here to speed things up later.
        bound_setattr = _OBJ_SETATTR.__get__(self)

        # Despite the big red warning, people *do* instantiate `Attribute`
        # themselves.
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
                types.MappingProxyType(dict(metadata))  # Shallow copy
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
        # The 'kw_only' argument is the class-level setting, and is used if the
        # attribute itself does not explicitly set 'kw_only'.
        # type holds the annotated value. deal with conflicts:
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

    # Don't use attrs.evolve since fields(Attribute) doesn't work
    def evolve(self, **changes):
        """
        Copy *self* and apply *changes*.

        This works similarly to `attrs.evolve` but that function does not work
        with :class:`attrs.Attribute`.

        It is mainly meant to be used for `transform-fields`.

        .. versionadded:: 20.3.0
        """
        import copy

        new = copy.copy(self)

        new._setattrs(changes.items())

        if "alias" in changes and "alias_is_default" not in changes:
            # Explicit alias provided -- no longer the default.
            _OBJ_SETATTR.__get__(new)("alias_is_default", False)
        elif (
            "name" in changes
            and "alias" not in changes
            # Don't auto-generate alias if the user picked picked the old one.
            and self.alias_is_default
        ):
            # Name changed, alias was auto-generated -- update it.
            _OBJ_SETATTR.__get__(new)(
                "alias", _default_init_alias_for(new.name)
            )

        return new

    # Don't use _add_pickle since fields(Attribute) doesn't work
    def __getstate__(self):
        """
        Play nice with pickle.
        """
        return tuple(
            getattr(self, name) if name != "metadata" else dict(self.metadata)
            for name in self.__slots__
        )

    def __setstate__(self, state):
        """
        Play nice with pickle.
        """
        if len(state) < len(self.__slots__):
            # Pre-26.1.0 pickle without alias_is_default -- infer it
            # heuristically.
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
