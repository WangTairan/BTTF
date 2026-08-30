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
        the,
        auto: bool,
        pro: ClassProps,
        has: bool,
    ):
        att, base, base2 = _transform_attrs(
            cls,
            the,
            auto,
            pro.kw_only,
            pro.collected_fields_by_mro,
            pro.field_transformer,
        )

        self._cls = cls
        self._cls_dict = dict(cls.__dict__) if pro.is_slotted else {}
        self._attrs = att
        self._base_names = {a2.name for a2 in base}
        self._base_attr_map = base2
        self._attr_names = tuple(a2.name for a2 in att)
        self._slots = pro.is_slotted
        self._frozen = pro.is_frozen
        self._weakref_slot = pro.has_weakref_slot
        self._cache_hash = (
            pro.hashability is ClassProps.Hashability.HASHABLE_CACHED
        )
        self._has_pre_init = bool(getattr(cls, "__attrs_pre_init__", False))
        self._pre_init_has_args = False
        if self._has_pre_init:
            # Check if the pre init method has more arguments than just `self`
            # We want to pass arguments if pre init expects arguments
            import inspect

            pre = cls.__attrs_pre_init__
            pre2 = inspect.signature(pre)
            self._pre_init_has_args = len(pre2.parameters) > 1
        self._has_post_init = bool(getattr(cls, "__attrs_post_init__", False))
        self._delete_attribs = not bool(the)
        self._is_exc = pro.is_exception
        self._on_setattr = pro.on_setattr_hook

        self._has_custom_setattr = has
        self._wrote_own_setattr = False

        self._cls_dict["__attrs_attrs__"] = self._attrs
        self._cls_dict["__attrs_props__"] = pro

        if pro.is_frozen:
            self._cls_dict["__setattr__"] = _frozen_setattrs
            self._cls_dict["__delattr__"] = _frozen_delattrs

            self._wrote_own_setattr = True
        elif self._on_setattr in (
            _DEFAULT_ON_SETATTR,
            setters.validate,
            setters.convert,
        ):
            has2 = has3 = False
            for a2 in att:
                if a2.validator is not None:
                    has2 = True
                if a2.converter is not None:
                    has3 = True

                if has2 and has3:
                    break
            if (
                (
                    self._on_setattr == _DEFAULT_ON_SETATTR
                    and not (has2 or has3)
                )
                or (self._on_setattr == setters.validate and not has2)
                or (self._on_setattr == setters.convert and not has3)
            ):
                # If class-level on_setattr is set to convert + validate, but
                # there's no field to convert or validate, pretend like there's
                # no on_setattr.
                self._on_setattr = None

        if pro.added_pickling:
            (
                self._cls_dict["__getstate__"],
                self._cls_dict["__setstate__"],
            ) = self.make()

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
            self._add_method_dunders = self.add12
        else:
            self._add_method_dunders = self.add11

    def __repr__(self):
        return f"<_ClassBuilder(cls={self._cls.__name__})>"

    def eval(self) -> None:
        """
        Evaluate any registered snippets in one go.
        """
        scr = "\n".join([sni[0] for sni in self._script_snippets])
        glo = {}
        for _2, snippet2, _2 in self._script_snippets:
            glo.update(snippet2)

        loc = _linecache_and_compile(
            scr,
            _generate_unique_filename(self._cls, "methods"),
            glo,
        )

        for _2, _2, hoo in self._script_snippets:
            hoo(self._cls_dict, loc)

    def build(self):
        """
        Finalize class based on the accumulated configuration.

        Builder cannot be used after calling this method.
        """
        self.eval()
        if self._slots is True:
            cls2 = self.create()
            self._cls.__attrs_base_of_slotted__ = weakref.ref(cls2)
        else:
            cls2 = abc.update_abstractmethods(self.patch())

        # The method gets only called if it's not inherited from a base class.
        # _has_own_attribute does NOT work properly for classmethods.
        if (
            getattr(cls2, "__attrs_init_subclass__", None)
            and "__attrs_init_subclass__" not in cls2.__dict__
        ):
            cls2.__attrs_init_subclass__()

        return cls2

    def patch(self):
        """
        Apply accumulated methods and return the class.
        """
        cls3 = self._cls
        base3 = self._base_names

        # Clean class of attribute definitions (`attr.ib()`s).
        if self._delete_attribs:
            for nam in self._attr_names:
                if (
                    nam not in base3
                    and getattr(cls3, nam, _SENTINEL) is not _SENTINEL
                ):
                    # An AttributeError can happen if a base class defines a
                    # class variable and we want to set an attribute with the
                    # same name by using only a type annotation.
                    with contextlib.suppress(AttributeError):
                        delattr(cls3, nam)

        # Attach our dunder methods.
        for nam, val2 in self._cls_dict.items():
            setattr(cls3, nam, val2)

        # If we've inherited an attrs __setattr__ and don't write our own,
        # reset it to object's.
        if not self._wrote_own_setattr and getattr(
            cls3, "__attrs_own_setattr__", False
        ):
            cls3.__attrs_own_setattr__ = False

            if not self._has_custom_setattr:
                cls3.__setattr__ = _OBJ_SETATTR

        return cls3

    def create(self):
        """
        Build and return a new class with a `__slots__` attribute.
        """
        cd2 = {
            k2: v2
            for k2, v2 in self._cls_dict.items()
            if k2 not in (*tuple(self._attr_names), "__dict__", "__weakref__")
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
            cd2["__attrs_own_setattr__"] = False

            if not self._has_custom_setattr:
                for base4 in self._cls.__bases__:
                    if base4.__dict__.get("__attrs_own_setattr__", False):
                        cd2["__setattr__"] = _OBJ_SETATTR
                        break

        # Traverse the MRO to collect existing slots
        # and check for an existing __weakref__.
        existing = {}
        weakref2 = False
        for base4 in self._cls.__mro__[1:-1]:
            if base4.__dict__.get("__weakref__", None) is not None:
                weakref2 = True
            existing.update(
                {
                    nam3: getattr(base4, nam3)
                    for nam3 in getattr(base4, "__slots__", [])
                }
            )

        base5 = set(self._base_names)

        nam2 = self._attr_names
        if (
            self._weakref_slot
            and "__weakref__" not in getattr(self._cls, "__slots__", ())
            and "__weakref__" not in nam2
            and not weakref2
        ):
            nam2 += ("__weakref__",)

        cached = {
            nam3: cached2.func
            for nam3, cached2 in cd2.items()
            if isinstance(cached2, cached_property)
        }

        # Collect methods with a `__class__` reference that are shadowed in the new class.
        # To know to update them.
        additional = []
        if cached:
            import inspect

            class2 = _get_annotations(self._cls)
            for nam3, fun in cached.items():
                # Add cached properties to names for slotting.
                nam2 += (nam3,)
                # Clear out function from class to avoid clashing.
                del cd2[nam3]
                additional.append(fun)
                ann = inspect.signature(fun).return_annotation
                if ann is not inspect.Parameter.empty:
                    class2[nam3] = ann

            original = cd2.get("__getattr__")
            if original is not None:
                additional.append(original)

            cd2["__getattr__"] = _make_cached_property_getattr(
                cached, original, self._cls
            )

        # We only add the names of attributes that aren't inherited.
        # Setting __slots__ to inherited attributes wastes memory.
        slot2 = [nam3 for nam3 in nam2 if nam3 not in base5]

        # There are slots for attributes from current class
        # that are defined in parent classes.
        # As their descriptors may be overridden by a child class,
        # we collect them here and update the class dict
        reused = {
            slo: slot3
            for slo, slot3 in existing.items()
            if slo in slot2
        }
        slot2 = [nam3 for nam3 in slot2 if nam3 not in reused]
        cd2.update(reused)
        if self._cache_hash:
            slot2.append(_HASH_CACHE_FIELD)

        cd2["__slots__"] = tuple(slot2)

        cd2["__qualname__"] = self._cls.__qualname__

        # Create new class based on old class and our methods.
        cls4 = type(self._cls)(self._cls.__name__, self._cls.__bases__, cd2)

        # The following is a fix for
        # <https://github.com/python-attrs/attrs/issues/102>.
        # If a method mentions `__class__` or uses the no-arg super(), the
        # compiler will bake a reference to the class in the method itself
        # as `method.__closure__`.  Since we replace the class with a
        # clone, we rewrite these references so it keeps working.
        for ite in itertools.chain(
            cls4.__dict__.values(), additional
        ):
            if isinstance(ite, (classmethod, staticmethod)):
                # Class- and staticmethods hide their functions inside.
                # These might need to be rewritten as well.
                closure = getattr(ite.__func__, "__closure__", None)
            elif isinstance(ite, property):
                # Workaround for property `super()` shortcut (PY3-only).
                # There is no universal way for other descriptors.
                closure = getattr(ite.fget, "__closure__", None)
            else:
                closure = getattr(ite, "__closure__", None)

            if not closure:  # Catch None or the empty list.
                continue
            for cel in closure:
                try:
                    mat = cel.cell_contents is self._cls
                except ValueError:  # noqa: PERF203
                    # ValueError: Cell is empty
                    pass
                else:
                    if mat:
                        cel.cell_contents = cls4
        return cls4

    def add(self, ns2):
        scr2, glo2 = _make_repr_script(self._attrs, ns2)

        def _attach_repr(cls5, glo3):
            cls5["__repr__"] = self._add_method_dunders(glo3["__repr__"])

        self._script_snippets.append((scr2, glo2, _attach_repr))
        self._repr_added = True
        return self

    def add2(self):
        if not self._repr_added:
            msg2 = "__str__ can only be generated if a __repr__ exists."
            raise ValueError(msg2)

        def __str__(self):
            return self.__repr__()

        self._cls_dict["__str__"] = self._add_method_dunders(__str__)
        return self

    def make(self):
        """
        Create custom __setstate__ and __getstate__ methods.
        """
        # __weakref__ is not writable.
        state2 = tuple(
            an2 for an2 in self._attr_names if an2 != "__weakref__"
        )

        def slots_getstate(self):
            """
            Automatically created by attrs.
            """
            return {nam4: getattr(self, nam4) for nam4 in state_attr_names}

        hash = self._cache_hash

        def slots_setstate(self, sta):
            """
            Automatically created by attrs.
            """
            bound = _OBJ_SETATTR.__get__(self)
            if isinstance(sta, tuple):
                # Backward compatibility with attrs instances pickled with
                # attrs versions before v22.2.0 which stored tuples.
                for nam5, val3 in zip(state_attr_names, sta, strict=False):
                    bound(nam5, val3)
            else:
                for nam5 in state_attr_names:
                    if nam5 in sta:
                        bound(nam5, sta[nam5])

            # The hash code cache is not included when the object is
            # serialized, but it still needs to be initialized to None to
            # indicate that the first call to __hash__ should be a cache
            # miss.
            if hash_caching_enabled:
                bound(_HASH_CACHE_FIELD, None)

        return slots_getstate, slots_setstate

    def make2(self):
        self._cls_dict["__hash__"] = None
        return self

    def add3(self):
        scr3, glo4 = _make_hash_script(
            self._cls,
            self._attrs,
            frozen=self._frozen,
            cache_hash=self._cache_hash,
        )

        def attach_hash(cls6: dict, loc2: dict) -> None:
            cls6["__hash__"] = self._add_method_dunders(loc2["__hash__"])

        self._script_snippets.append((scr3, glo4, attach_hash))

        return self

    def add4(self):
        scr4, glo5, ann2 = _make_init_script(
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

        def _attach_init(cls7, glo6):
            ini = glo6["__init__"]
            ini.__annotations__ = annotations
            cls7["__init__"] = self._add_method_dunders(ini)

        self._script_snippets.append((scr4, glo5, _attach_init))

        return self

    def add5(self):
        # We create a local `evolve` proxy because it gets modified in place.
        def __replace__(*arg, **cha):
            return evolve(*arg, **cha)

        self._cls_dict["__replace__"] = self._add_method_dunders(__replace__)
        return self

    def add6(self):
        self._cls_dict["__match_args__"] = tuple(
            fie.name
            for fie in self._attrs
            if fie.init and not fie.kw_only
        )

    def add7(self):
        scr5, glo7, ann3 = _make_init_script(
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

        def _attach_attrs_init(cls8, glo8):
            ini2 = glo8["__attrs_init__"]
            ini2.__annotations__ = annotations
            cls8["__attrs_init__"] = self._add_method_dunders(ini2)

        self._script_snippets.append((scr5, glo7, _attach_attrs_init))

        return self

    def add8(self):
        cd3 = self._cls_dict

        scr6, glo9 = _make_eq_script(self._attrs)

        def _attach_eq(cls9, glo10):
            cls9["__eq__"] = self._add_method_dunders(glo10["__eq__"])

        self._script_snippets.append((scr6, glo9, _attach_eq))

        cd3["__ne__"] = __ne__

        return self

    def add9(self):
        cd4 = self._cls_dict

        cd4["__lt__"], cd4["__le__"], cd4["__gt__"], cd4["__ge__"] = (
            self._add_method_dunders(met)
            for met in _make_order(self._cls, self._attrs)
        )

        return self

    def add10(self):
        sa = {}
        for a3 in self._attrs:
            on = a3.on_setattr or self._on_setattr
            if on and on is not setters.NO_OP:
                sa[a3.name] = (
                    a3,
                    on,
                    _lazy_is_generator(on),
                )

        if not sa:
            return self

        if self._has_custom_setattr:
            # We need to write a __setattr__ but there already is one!
            msg3 = "Can't combine custom __setattr__ with on_setattr hooks."
            raise ValueError(msg3)

        # docstring comes from _add_method_dunders
        def __setattr__(self, nam6, val4):
            try:
                a4, hoo2, is2 = sa_attrs[nam6]
            except KeyError:
                _OBJ_SETATTR(self, nam6, val4)

                return

            if is2():
                gen2 = hoo2(self, a4, val4)
                nva = next(gen2)
                _OBJ_SETATTR(self, nam6, nva)
                try:
                    next(gen2)
                except StopIteration:
                    return

                gen2.close()
                msg4 = "Generator on_setattr hook yielded more than once."
                raise RuntimeError(msg4)

            nva = hoo2(self, a4, val4)
            _OBJ_SETATTR(self, nam6, nva)

            return

        self._cls_dict["__attrs_own_setattr__"] = True
        self._cls_dict["__setattr__"] = self._add_method_dunders(__setattr__)
        self._wrote_own_setattr = True

        return self

    def add11(self, met2: Callable) -> Callable:
        """
        Add __module__ and __qualname__ to a *method*.
        """
        met2.__module__ = self._cls.__module__

        met2.__qualname__ = f"{self._cls.__qualname__}.{met2.__name__}"

        met2.__doc__ = (
            f"Method generated by attrs for class {self._cls.__qualname__}."
        )

        return met2

    def add12(self, met3: Callable) -> Callable:
        """
        Add __module__ and __qualname__ to a *method* if possible.
        """
        with contextlib.suppress(AttributeError):
            met3.__module__ = self._cls.__module__

        with contextlib.suppress(AttributeError):
            met3.__qualname__ = f"{self._cls.__qualname__}.{met3.__name__}"

        with contextlib.suppress(AttributeError):
            met3.__doc__ = f"Method generated by attrs for class {self._cls.__qualname__}."

        return met3
