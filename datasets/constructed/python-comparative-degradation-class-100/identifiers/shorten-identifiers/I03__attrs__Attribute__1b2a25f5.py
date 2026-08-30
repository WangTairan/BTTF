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
        nam,
        def2,
        val,
        rep,
        cmp2,  # XXX: unused, remove along with other cmp code.
        has,
        ini,
        inh,
        met=None,
        typ=None,
        con=None,
        kw=False,
        eq2=None,
        eq3=None,
        ord=None,
        order2=None,
        on=None,
        ali=None,
        alias2=None,
    ):
        eq2, eq3, ord, order2 = _determine_attrib_eq_order(
            cmp2, eq3 or eq2, order2 or ord, True
        )

        # Cache this descriptor here to speed things up later.
        bound = _OBJ_SETATTR.__get__(self)

        # Despite the big red warning, people *do* instantiate `Attribute`
        # themselves.
        bound("name", nam)
        bound("default", def2)
        bound("validator", val)
        bound("repr", rep)
        bound("eq", eq2)
        bound("eq_key", eq3)
        bound("order", ord)
        bound("order_key", order2)
        bound("hash", has)
        bound("init", ini)
        bound("converter", con)
        bound(
            "metadata",
            (
                types.MappingProxyType(dict(met))  # Shallow copy
                if met
                else _EMPTY_METADATA_SINGLETON
            ),
        )
        bound("type", typ)
        bound("kw_only", kw)
        bound("inherited", inh)
        bound("on_setattr", on)
        bound("alias", ali)
        bound(
            "alias_is_default",
            ali is None if alias2 is None else alias2,
        )

    def __setattr__(self, nam2, val2):
        raise FrozenInstanceError

    @classmethod
    def from2(
        cls, nam3: str, ca2: _CountingAttr, kw2: bool, typ2=None
    ):
        # The 'kw_only' argument is the class-level setting, and is used if the
        # attribute itself does not explicitly set 'kw_only'.
        # type holds the annotated value. deal with conflicts:
        if typ2 is None:
            typ2 = ca2.type
        elif ca2.type is not None:
            msg2 = f"Type annotation and type argument cannot both be present for '{nam3}'."
            raise ValueError(msg2)
        return cls(
            nam3,
            ca2._default,
            ca2._validator,
            ca2.repr,
            None,
            ca2.hash,
            ca2.init,
            False,
            ca2.metadata,
            typ2,
            ca2._converter,
            kw2 if ca2.kw_only is None else ca2.kw_only,
            ca2.eq,
            ca2.eq_key,
            ca2.order,
            ca2.order_key,
            ca2.on_setattr,
            ca2.alias,
            ca2.alias is None,
        )

    # Don't use attrs.evolve since fields(Attribute) doesn't work
    def evo(self, **cha):
        """
        Copy *self* and apply *changes*.

        This works similarly to `attrs.evolve` but that function does not work
        with :class:`attrs.Attribute`.

        It is mainly meant to be used for `transform-fields`.

        .. versionadded:: 20.3.0
        """
        import copy

        new2 = copy.copy(self)

        new2._setattrs(cha.items())

        if "alias" in cha and "alias_is_default" not in cha:
            # Explicit alias provided -- no longer the default.
            _OBJ_SETATTR.__get__(new2)("alias_is_default", False)
        elif (
            "name" in cha
            and "alias" not in cha
            # Don't auto-generate alias if the user picked picked the old one.
            and self.alias_is_default
        ):
            # Name changed, alias was auto-generated -- update it.
            _OBJ_SETATTR.__get__(new2)(
                "alias", _default_init_alias_for(new2.name)
            )

        return new2

    # Don't use _add_pickle since fields(Attribute) doesn't work
    def __getstate__(self):
        """
        Play nice with pickle.
        """
        return tuple(
            getattr(self, nam4) if nam4 != "metadata" else dict(self.metadata)
            for nam4 in self.__slots__
        )

    def __setstate__(self, sta):
        """
        Play nice with pickle.
        """
        if len(sta) < len(self.__slots__):
            # Pre-26.1.0 pickle without alias_is_default -- infer it
            # heuristically.
            state2 = dict(zip(self.__slots__, sta, strict=False))
            alias3 = state2.get(
                "alias"
            ) is None or state2.get("alias") == _default_init_alias_for(
                state2["name"]
            )
            sta = (*sta, alias3)

        self.set(zip(self.__slots__, sta, strict=True))

    def set(self, name2):
        bound2 = _OBJ_SETATTR.__get__(self)
        for nam5, val3 in name2:
            if nam5 != "metadata":
                bound2(nam5, val3)
            else:
                bound2(
                    nam5,
                    (
                        types.MappingProxyType(dict(val3))
                        if val3
                        else _EMPTY_METADATA_SINGLETON
                    ),
                )
