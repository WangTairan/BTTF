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

class _ClassBuilder:
    """
    Iteratively build *one* class.
    """

    __slots__ = (
        "_add_method_dunders",
        "_attr_names",
        "_attrs",
        "_base_attr_map",
        "_base_names",
        "_cache_hash",
        "_cls",
        "_cls_dict",
        "_delete_attribs",
        "_frozen",
        "_has_custom_setattr",
        "_has_post_init",
        "_has_pre_init",
        "_is_exc",
        "_on_setattr",
        "_pre_init_has_args",
        "_repr_added",
        "_script_snippets",
        "_slots",
        "_weakref_slot",
        "_wrote_own_setattr",
    )

    def __init__(
        self,
        cls: type,
        u,
        w: bool,
        x: ClassProps,
        y: bool,
    ):
        z, A, B = _transform_attrs(
            cls,
            u,
            w,
            x.kw_only,
            x.collected_fields_by_mro,
            x.field_transformer,
        )

        self._cls = cls
        self._cls_dict = dict(cls.__dict__) if x.is_slotted else {}
        self._attrs = z
        self._base_names = {C.name for C in A}
        self._base_attr_map = B
        self._attr_names = tuple(C.name for C in z)
        self._slots = x.is_slotted
        self._frozen = x.is_frozen
        self._weakref_slot = x.has_weakref_slot
        self._cache_hash = (
            x.hashability is ClassProps.Hashability.HASHABLE_CACHED
        )
        self._has_pre_init = bool(getattr(cls, "__attrs_pre_init__", False))
        self._pre_init_has_args = False
        if self._has_pre_init:
            # Check if the pre init method has more arguments than just `self`
            # We want to pass arguments if pre init expects arguments
            import inspect

            D = cls.__attrs_pre_init__
            E = inspect.signature(D)
            self._pre_init_has_args = len(E.parameters) > 1
        self._has_post_init = bool(getattr(cls, "__attrs_post_init__", False))
        self._delete_attribs = not bool(u)
        self._is_exc = x.is_exception
        self._on_setattr = x.on_setattr_hook

        self._has_custom_setattr = y
        self._wrote_own_setattr = False

        self._cls_dict["__attrs_attrs__"] = self._attrs
        self._cls_dict["__attrs_props__"] = x

        if x.is_frozen:
            self._cls_dict["__setattr__"] = _frozen_setattrs
            self._cls_dict["__delattr__"] = _frozen_delattrs

            self._wrote_own_setattr = True
        elif self._on_setattr in (
            _DEFAULT_ON_SETATTR,
            setters.validate,
            setters.convert,
        ):
            F = G = False
            for C in z:
                if C.validator is not None:
                    F = True
                if C.converter is not None:
                    G = True

                if F and G:
                    break
            if (
                (
                    self._on_setattr == _DEFAULT_ON_SETATTR
                    and not (F or G)
                )
                or (self._on_setattr == setters.validate and not F)
                or (self._on_setattr == setters.convert and not G)
            ):
                # If class-level on_setattr is set to convert + validate, but
                # there's no field to convert or validate, pretend like there's
                # no on_setattr.
                self._on_setattr = None

        if x.added_pickling:
            (
                self._cls_dict["__getstate__"],
                self._cls_dict["__setstate__"],
            ) = self.h()

        # tuples of script, globs, hook
        self._script_snippets: list[
            tuple[str, dict, Callable[[dict, dict], Any]]
        ] = []
        self._repr_added = False

        # We want to only do this check once; in 99.9% of cases these
        # exist.
        if not hasattr(self._cls, "__module__") or not hasattr(
            self._cls, "__qualname__"
        ):
            self._add_method_dunders = self.t
        else:
            self._add_method_dunders = self.s

    def __repr__(self):
        return f"<_ClassBuilder(cls={self._cls.__name__})>"

    def b(self) -> None:
        """
        Evaluate any registered snippets in one go.
        """
        H = "\n".join([I[0] for I in self._script_snippets])
        J = {}
        for K, L, K in self._script_snippets:
            J.update(L)

        M = _linecache_and_compile(
            H,
            _generate_unique_filename(self._cls, "methods"),
            J,
        )

        for K, K, N in self._script_snippets:
            N(self._cls_dict, M)

    def c(self):
        """
        Finalize class based on the accumulated configuration.

        Builder cannot be used after calling this method.
        """
        self.b()
        if self._slots is True:
            O = self.e()
            self._cls.__attrs_base_of_slotted__ = weakref.ref(O)
        else:
            O = abc.update_abstractmethods(self.d())

        # The method gets only called if it's not inherited from a base class.
        # _has_own_attribute does NOT work properly for classmethods.
        if (
            getattr(O, "__attrs_init_subclass__", None)
            and "__attrs_init_subclass__" not in O.__dict__
        ):
            O.__attrs_init_subclass__()

        return O

    def d(self):
        """
        Apply accumulated methods and return the class.
        """
        P = self._cls
        Q = self._base_names

        # Clean class of attribute definitions (`attr.ib()`s).
        if self._delete_attribs:
            for R in self._attr_names:
                if (
                    R not in Q
                    and getattr(P, R, _SENTINEL) is not _SENTINEL
                ):
                    # An AttributeError can happen if a base class defines a
                    # class variable and we want to set an attribute with the
                    # same name by using only a type annotation.
                    with contextlib.suppress(AttributeError):
                        delattr(P, R)

        # Attach our dunder methods.
        for R, S in self._cls_dict.items():
            setattr(P, R, S)

        # If we've inherited an attrs __setattr__ and don't write our own,
        # reset it to object's.
        if not self._wrote_own_setattr and getattr(
            P, "__attrs_own_setattr__", False
        ):
            P.__attrs_own_setattr__ = False

            if not self._has_custom_setattr:
                P.__setattr__ = _OBJ_SETATTR

        return P

    def e(self):
        """
        Build and return a new class with a `__slots__` attribute.
        """
        T = {
            U: V
            for U, V in self._cls_dict.items()
            if U not in (*tuple(self._attr_names), "__dict__", "__weakref__")
        }

        # 3.14.0rc2+
        if hasattr(sys, "_clear_type_descriptors"):
            sys._clear_type_descriptors(self._cls)

        # If our class doesn't have its own implementation of __setattr__
        # (either from the user or by us), check the bases, if one of them has
        # an attrs-made __setattr__, that needs to be reset. We don't walk the
        # MRO because we only care about our immediate base classes.
        # XXX: This can be confused by subclassing a slotted attrs class with
        # XXX: a non-attrs class and subclass the resulting class with an attrs
        # XXX: class.  See `test_slotted_confused` for details.  For now that's
        # XXX: OK with us.
        if not self._wrote_own_setattr:
            T["__attrs_own_setattr__"] = False

            if not self._has_custom_setattr:
                for Y in self._cls.__bases__:
                    if Y.__dict__.get("__attrs_own_setattr__", False):
                        T["__setattr__"] = _OBJ_SETATTR
                        break

        # Traverse the MRO to collect existing slots
        # and check for an existing __weakref__.
        W = {}
        X = False
        for Y in self._cls.__mro__[1:-1]:
            if Y.__dict__.get("__weakref__", None) is not None:
                X = True
            W.update(
                {
                    af: getattr(Y, af)
                    for af in getattr(Y, "__slots__", [])
                }
            )

        Z = set(self._base_names)

        aa = self._attr_names
        if (
            self._weakref_slot
            and "__weakref__" not in getattr(self._cls, "__slots__", ())
            and "__weakref__" not in aa
            and not X
        ):
            aa += ("__weakref__",)

        ab = {
            af: ac.func
            for af, ac in T.items()
            if isinstance(ac, cached_property)
        }

        # Collect methods with a `__class__` reference that are shadowed in the new class.
        # To know to update them.
        ad = []
        if ab:
            import inspect

            ae = _get_annotations(self._cls)
            for af, ag in ab.items():
                # Add cached properties to names for slotting.
                aa += (af,)
                # Clear out function from class to avoid clashing.
                del T[af]
                ad.append(ag)
                ah = inspect.signature(ag).return_annotation
                if ah is not inspect.Parameter.empty:
                    ae[af] = ah

            ai = T.get("__getattr__")
            if ai is not None:
                ad.append(ai)

            T["__getattr__"] = _make_cached_property_getattr(
                ab, ai, self._cls
            )

        # We only add the names of attributes that aren't inherited.
        # Setting __slots__ to inherited attributes wastes memory.
        aj = [af for af in aa if af not in Z]

        # There are slots for attributes from current class
        # that are defined in parent classes.
        # As their descriptors may be overridden by a child class,
        # we collect them here and update the class dict
        ak = {
            al: am
            for al, am in W.items()
            if al in aj
        }
        aj = [af for af in aj if af not in ak]
        T.update(ak)
        if self._cache_hash:
            aj.append(_HASH_CACHE_FIELD)

        T["__slots__"] = tuple(aj)

        T["__qualname__"] = self._cls.__qualname__

        # Create new class based on old class and our methods.
        ao = type(self._cls)(self._cls.__name__, self._cls.__bases__, T)

        # The following is a fix for
        # <https://github.com/python-attrs/attrs/issues/102>.
        # If a method mentions `__class__` or uses the no-arg super(), the
        # compiler will bake a reference to the class in the method itself
        # as `method.__closure__`.  Since we replace the class with a
        # clone, we rewrite these references so it keeps working.
        for ap in itertools.chain(
            ao.__dict__.values(), ad
        ):
            if isinstance(ap, (classmethod, staticmethod)):
                # Class- and staticmethods hide their functions inside.
                # These might need to be rewritten as well.
                aq = getattr(ap.__func__, "__closure__", None)
            elif isinstance(ap, property):
                # Workaround for property `super()` shortcut (PY3-only).
                # There is no universal way for other descriptors.
                aq = getattr(ap.fget, "__closure__", None)
            else:
                aq = getattr(ap, "__closure__", None)

            if not aq:  # Catch None or the empty list.
                continue
            for ar in aq:
                try:
                    at = ar.cell_contents is self._cls
                except ValueError:  # noqa: PERF203
                    # ValueError: Cell is empty
                    pass
                else:
                    if at:
                        ar.cell_contents = ao
        return ao

    def f(self, au):
        av, aw = _make_repr_script(self._attrs, au)

        def _attach_repr(ax, ay):
            ax["__repr__"] = self._add_method_dunders(ay["__repr__"])

        self._script_snippets.append((av, aw, _attach_repr))
        self._repr_added = True
        return self

    def g(self):
        if not self._repr_added:
            az = "__str__ can only be generated if a __repr__ exists."
            raise ValueError(az)

        def __str__(self):
            return self.__repr__()

        self._cls_dict["__str__"] = self._add_method_dunders(__str__)
        return self

    def h(self):
        """
        Create custom __setstate__ and __getstate__ methods.
        """
        # __weakref__ is not writable.
        aA = tuple(
            aB for aB in self._attr_names if aB != "__weakref__"
        )

        def slots_getstate(self):
            """
            Automatically created by attrs.
            """
            return {aD: getattr(self, aD) for aD in state_attr_names}

        aC = self._cache_hash

        def slots_setstate(self, aE):
            """
            Automatically created by attrs.
            """
            aF = _OBJ_SETATTR.__get__(self)
            if isinstance(aE, tuple):
                # Backward compatibility with attrs instances pickled with
                # attrs versions before v22.2.0 which stored tuples.
                for aH, aG in zip(state_attr_names, aE, strict=False):
                    aF(aH, aG)
            else:
                for aH in state_attr_names:
                    if aH in aE:
                        aF(aH, aE[aH])

            # The hash code cache is not included when the object is
            # serialized, but it still needs to be initialized to None to
            # indicate that the first call to __hash__ should be a cache
            # miss.
            if hash_caching_enabled:
                aF(_HASH_CACHE_FIELD, None)

        return slots_getstate, slots_setstate

    def i(self):
        self._cls_dict["__hash__"] = None
        return self

    def j(self):
        aI, aJ = _make_hash_script(
            self._cls,
            self._attrs,
            frozen=self._frozen,
            cache_hash=self._cache_hash,
        )

        def attach_hash(aK: dict, aL: dict) -> None:
            aK["__hash__"] = self._add_method_dunders(aL["__hash__"])

        self._script_snippets.append((aI, aJ, attach_hash))

        return self

    def l(self):
        aM, aN, aO = _make_init_script(
            self._cls,
            self._attrs,
            self._has_pre_init,
            self._pre_init_has_args,
            self._has_post_init,
            self._frozen,
            self._slots,
            self._cache_hash,
            self._base_attr_map,
            self._is_exc,
            self._on_setattr,
            attrs_init=False,
        )

        def _attach_init(aP, aQ):
            aR = aQ["__init__"]
            aR.__annotations__ = annotations
            aP["__init__"] = self._add_method_dunders(aR)

        self._script_snippets.append((aM, aN, _attach_init))

        return self

    def m(self):
        # We create a local `evolve` proxy because it gets modified in place.
        def __replace__(*aS, **aT):
            return evolve(*aS, **aT)

        self._cls_dict["__replace__"] = self._add_method_dunders(__replace__)
        return self

    def n(self):
        self._cls_dict["__match_args__"] = tuple(
            aU.name
            for aU in self._attrs
            if aU.init and not aU.kw_only
        )

    def o(self):
        aV, aW, aX = _make_init_script(
            self._cls,
            self._attrs,
            self._has_pre_init,
            self._pre_init_has_args,
            self._has_post_init,
            self._frozen,
            self._slots,
            self._cache_hash,
            self._base_attr_map,
            self._is_exc,
            self._on_setattr,
            attrs_init=True,
        )

        def _attach_attrs_init(aY, aZ):
            ba = aZ["__attrs_init__"]
            ba.__annotations__ = annotations
            aY["__attrs_init__"] = self._add_method_dunders(ba)

        self._script_snippets.append((aV, aW, _attach_attrs_init))

        return self

    def p(self):
        bb = self._cls_dict

        bc, bd = _make_eq_script(self._attrs)

        def _attach_eq(be, bf):
            be["__eq__"] = self._add_method_dunders(bf["__eq__"])

        self._script_snippets.append((bc, bd, _attach_eq))

        bb["__ne__"] = __ne__

        return self

    def q(self):
        bg = self._cls_dict

        bg["__lt__"], bg["__le__"], bg["__gt__"], bg["__ge__"] = (
            self._add_method_dunders(bh)
            for bh in _make_order(self._cls, self._attrs)
        )

        return self

    def r(self):
        bi = {}
        for bj in self._attrs:
            bk = bj.on_setattr or self._on_setattr
            if bk and bk is not setters.NO_OP:
                bi[bj.name] = (
                    bj,
                    bk,
                    _lazy_is_generator(bk),
                )

        if not bi:
            return self

        if self._has_custom_setattr:
            # We need to write a __setattr__ but there already is one!
            bl = "Can't combine custom __setattr__ with on_setattr hooks."
            raise ValueError(bl)

        # docstring comes from _add_method_dunders
        def __setattr__(self, bm, bn):
            try:
                bo, bp, bq = sa_attrs[bm]
            except KeyError:
                _OBJ_SETATTR(self, bm, bn)

                return

            if bq():
                br = bp(self, bo, bn)
                bt = next(br)
                _OBJ_SETATTR(self, bm, bt)
                try:
                    next(br)
                except StopIteration:
                    return

                br.close()
                bs = "Generator on_setattr hook yielded more than once."
                raise RuntimeError(bs)

            bt = bp(self, bo, bn)
            _OBJ_SETATTR(self, bm, bt)

            return

        self._cls_dict["__attrs_own_setattr__"] = True
        self._cls_dict["__setattr__"] = self._add_method_dunders(__setattr__)
        self._wrote_own_setattr = True

        return self

    def s(self, bu: Callable) -> Callable:
        """
        Add __module__ and __qualname__ to a *method*.
        """
        bu.__module__ = self._cls.__module__

        bu.__qualname__ = f"{self._cls.__qualname__}.{bu.__name__}"

        bu.__doc__ = (
            f"Method generated by attrs for class {self._cls.__qualname__}."
        )

        return bu

    def t(self, bv: Callable) -> Callable:
        """
        Add __module__ and __qualname__ to a *method* if possible.
        """
        with contextlib.suppress(AttributeError):
            bv.__module__ = self._cls.__module__

        with contextlib.suppress(AttributeError):
            bv.__qualname__ = f"{self._cls.__qualname__}.{bv.__name__}"

        with contextlib.suppress(AttributeError):
            bv.__doc__ = f"Method generated by attrs for class {self._cls.__qualname__}."

        return bv
