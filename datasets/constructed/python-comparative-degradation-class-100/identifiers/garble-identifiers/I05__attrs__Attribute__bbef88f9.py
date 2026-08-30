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
        d,
        e,
        f,
        g,
        h,  # XXX: unused, remove along with other cmp code.
        i,
        j,
        k,
        l=None,
        m=None,
        n=None,
        o=False,
        p=None,
        q=None,
        r=None,
        s=None,
        t=None,
        u=None,
        v=None,
    ):
        p, q, r, s = _determine_attrib_eq_order(
            h, q or p, s or r, True
        )

        # Cache this descriptor here to speed things up later.
        w = _OBJ_SETATTR.__get__(self)

        # Despite the big red warning, people *do* instantiate `Attribute`
        # themselves.
        w("name", d)
        w("default", e)
        w("validator", f)
        w("repr", g)
        w("eq", p)
        w("eq_key", q)
        w("order", r)
        w("order_key", s)
        w("hash", i)
        w("init", j)
        w("converter", n)
        w(
            "metadata",
            (
                types.MappingProxyType(dict(l))  # Shallow copy
                if l
                else _EMPTY_METADATA_SINGLETON
            ),
        )
        w("type", m)
        w("kw_only", o)
        w("inherited", k)
        w("on_setattr", t)
        w("alias", u)
        w(
            "alias_is_default",
            u is None if v is None else v,
        )

    def __setattr__(self, x, y):
        raise FrozenInstanceError

    @classmethod
    def a(
        cls, z: str, A: _CountingAttr, B: bool, C=None
    ):
        # The 'kw_only' argument is the class-level setting, and is used if the
        # attribute itself does not explicitly set 'kw_only'.
        # type holds the annotated value. deal with conflicts:
        if C is None:
            C = A.type
        elif A.type is not None:
            D = f"Type annotation and type argument cannot both be present for '{z}'."
            raise ValueError(D)
        return cls(
            z,
            A._default,
            A._validator,
            A.repr,
            None,
            A.hash,
            A.init,
            False,
            A.metadata,
            C,
            A._converter,
            B if A.kw_only is None else A.kw_only,
            A.eq,
            A.eq_key,
            A.order,
            A.order_key,
            A.on_setattr,
            A.alias,
            A.alias is None,
        )

    # Don't use attrs.evolve since fields(Attribute) doesn't work
    def b(self, **E):
        """
        Copy *self* and apply *changes*.

        This works similarly to `attrs.evolve` but that function does not work
        with :class:`attrs.Attribute`.

        It is mainly meant to be used for `transform-fields`.

        .. versionadded:: 20.3.0
        """
        import copy

        F = copy.copy(self)

        F._setattrs(E.items())

        if "alias" in E and "alias_is_default" not in E:
            # Explicit alias provided -- no longer the default.
            _OBJ_SETATTR.__get__(F)("alias_is_default", False)
        elif (
            "name" in E
            and "alias" not in E
            # Don't auto-generate alias if the user picked picked the old one.
            and self.alias_is_default
        ):
            # Name changed, alias was auto-generated -- update it.
            _OBJ_SETATTR.__get__(F)(
                "alias", _default_init_alias_for(F.name)
            )

        return F

    # Don't use _add_pickle since fields(Attribute) doesn't work
    def __getstate__(self):
        """
        Play nice with pickle.
        """
        return tuple(
            getattr(self, G) if G != "metadata" else dict(self.metadata)
            for G in self.__slots__
        )

    def __setstate__(self, H):
        """
        Play nice with pickle.
        """
        if len(H) < len(self.__slots__):
            # Pre-26.1.0 pickle without alias_is_default -- infer it
            # heuristically.
            I = dict(zip(self.__slots__, H, strict=False))
            J = I.get(
                "alias"
            ) is None or I.get("alias") == _default_init_alias_for(
                I["name"]
            )
            H = (*H, J)

        self.c(zip(self.__slots__, H, strict=True))

    def c(self, K):
        L = _OBJ_SETATTR.__get__(self)
        for M, N in K:
            if M != "metadata":
                L(M, N)
            else:
                L(
                    M,
                    (
                        types.MappingProxyType(dict(N))
                        if N
                        else _EMPTY_METADATA_SINGLETON
                    ),
                )
