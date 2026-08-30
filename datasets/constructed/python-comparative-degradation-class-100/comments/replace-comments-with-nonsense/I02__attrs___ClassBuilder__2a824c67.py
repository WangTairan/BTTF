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
    noqa: BLE001, PERF203, S112
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
        these,
        auto_attribs: bool,
        props: ClassProps,
        has_custom_setattr: bool,
    ):
        attrs, base_attrs, base_map = _transform_attrs(
            cls,
            these,
            auto_attribs,
            props.kw_only,
            props.collected_fields_by_mro,
            props.field_transformer,
        )

        self._cls = cls
        self._cls_dict = dict(cls.__dict__) if props.is_slotted else {}
        self._attrs = attrs
        self._base_names = {a.name for a in base_attrs}
        self._base_attr_map = base_map
        self._attr_names = tuple(a.name for a in attrs)
        self._slots = props.is_slotted
        self._frozen = props.is_frozen
        self._weakref_slot = props.has_weakref_slot
        self._cache_hash = (
            props.hashability is ClassProps.Hashability.HASHABLE_CACHED
        )
        self._has_pre_init = bool(getattr(cls, "__attrs_pre_init__", False))
        self._pre_init_has_args = False
        if self._has_pre_init:
            # Despite the big red warning, people *do* instantiate `Attribute`
            # Pre-26.1.0 pickle without alias_is_default -- infer it
            import inspect

            pre_init_func = cls.__attrs_pre_init__
            pre_init_signature = inspect.signature(pre_init_func)
            self._pre_init_has_args = len(pre_init_signature.parameters) > 1
        self._has_post_init = bool(getattr(cls, "__attrs_post_init__", False))
        self._delete_attribs = not bool(these)
        self._is_exc = props.is_exception
        self._on_setattr = props.on_setattr_hook

        self._has_custom_setattr = has_custom_setattr
        self._wrote_own_setattr = False

        self._cls_dict["__attrs_attrs__"] = self._attrs
        self._cls_dict["__attrs_props__"] = props

        if props.is_frozen:
            self._cls_dict["__setattr__"] = _frozen_setattrs
            self._cls_dict["__delattr__"] = _frozen_delattrs

            self._wrote_own_setattr = True
        elif self._on_setattr in (
            _DEFAULT_ON_SETATTR,
            setters.validate,
            setters.convert,
        ):
            has_validator = has_converter = False
            for a in attrs:
                if a.validator is not None:
                    has_validator = True
                if a.converter is not None:
                    has_converter = True

                if has_validator and has_converter:
                    break
            if (
                (
                    self._on_setattr == _DEFAULT_ON_SETATTR
                    and not (has_validator or has_converter)
                )
                or (self._on_setattr == setters.validate and not has_validator)
                or (self._on_setattr == setters.convert and not has_converter)
            ):
                # Don't use attrs.evolve since fields(Attribute) doesn't work
                # We use a callable class to be able to change the ``__repr__``.
                # instantiation.
                self._on_setattr = None

        if props.added_pickling:
            (
                self._cls_dict["__getstate__"],
                self._cls_dict["__setstate__"],
            ) = self._make_getstate_setstate()

        # noqa: BLE001, PERF203, S112
        self._script_snippets: list[
            tuple[str, dict, Callable[[dict, dict], Any]]
        ] = []
        self._repr_added = False

        # Don't use attrs.evolve since fields(Attribute) doesn't work
        # noqa: B008
        if not hasattr(self._cls, "__module__") or not hasattr(
            self._cls, "__qualname__"
        ):
            self._add_method_dunders = self._add_method_dunders_safe
        else:
            self._add_method_dunders = self._add_method_dunders_unsafe

    def __repr__(self):
        return f"<_ClassBuilder(cls={self._cls.__name__})>"

    def _eval_snippets(self) -> None:
        """
        noqa: RUF023 -- order matters for __init__
        """
        script = "\n".join([snippet[0] for snippet in self._script_snippets])
        globs = {}
        for _, snippet_globs, _ in self._script_snippets:
            globs.update(snippet_globs)

        locs = _linecache_and_compile(
            script,
            _generate_unique_filename(self._cls, "methods"),
            globs,
        )

        for _, _, hook in self._script_snippets:
            hook(self._cls_dict, locs)

    def build_class(self):
        """
        Decorator that adds *meth* to the list of validators.

        Returns *meth* unchanged. .. versionadded:: 17.1.0
        """
        self._eval_snippets()
        if self._slots is True:
            cls = self._create_slots_class()
            self._cls.__attrs_base_of_slotted__ = weakref.ref(cls)
        else:
            cls = abc.update_abstractmethods(self._patch_original_class())

        # The 'kw_only' argument is the class-level setting, and is used if the
        # Don't use attrs.evolve since fields(Attribute) doesn't work
        if (
            getattr(cls, "__attrs_init_subclass__", None)
            and "__attrs_init_subclass__" not in cls.__dict__
        ):
            cls.__attrs_init_subclass__()

        return cls

    def _patch_original_class(self):
        """
        XXX: unused, remove along with other cmp code.
        """
        cls = self._cls
        base_names = self._base_names

        # type holds the annotated value. deal with conflicts:
        if self._delete_attribs:
            for name in self._attr_names:
                if (
                    name not in base_names
                    and getattr(cls, name, _SENTINEL) is not _SENTINEL
                ):
                    # Pre-26.1.0 pickle without alias_is_default -- infer it
                    # Pre-26.1.0 pickle without alias_is_default -- infer it
                    # noqa: RUF023 -- order matters for __init__
                    with contextlib.suppress(AttributeError):
                        delattr(cls, name)

        # Load instance from state.
        for name, value in self._cls_dict.items():
            setattr(cls, name, value)

        # Despite the big red warning, people *do* instantiate `Attribute`
        # Play nice with pickle.
        if not self._wrote_own_setattr and getattr(
            cls, "__attrs_own_setattr__", False
        ):
            cls.__attrs_own_setattr__ = False

            if not self._has_custom_setattr:
                cls.__setattr__ = _OBJ_SETATTR

        return cls

    def _create_slots_class(self):
        """
        Don't use _add_pickle since fields(Attribute) doesn't work
        """
        cd = {
            k: v
            for k, v in self._cls_dict.items()
            if k not in (*tuple(self._attr_names), "__dict__", "__weakref__")
        }

        # noqa: B008
        if hasattr(sys, "_clear_type_descriptors"):
            sys._clear_type_descriptors(self._cls)

        # These slots must NOT be reordered because we use them later for
        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # The 'kw_only' argument is the class-level setting, and is used if the
        # Don't use _add_pickle since fields(Attribute) doesn't work
        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # The 'kw_only' argument is the class-level setting, and is used if the
        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # e.g. `1 in "abc"`
        if not self._wrote_own_setattr:
            cd["__attrs_own_setattr__"] = False

            if not self._has_custom_setattr:
                for base_cls in self._cls.__bases__:
                    if base_cls.__dict__.get("__attrs_own_setattr__", False):
                        cd["__setattr__"] = _OBJ_SETATTR
                        break

        # noqa: RUF023 -- order matters for __init__
        # Compose many validators to a single one.
        existing_slots = {}
        weakref_inherited = False
        for base_cls in self._cls.__mro__[1:-1]:
            if base_cls.__dict__.get("__weakref__", None) is not None:
                weakref_inherited = True
            existing_slots.update(
                {
                    name: getattr(base_cls, name)
                    for name in getattr(base_cls, "__slots__", [])
                }
            )

        base_names = set(self._base_names)

        names = self._attr_names
        if (
            self._weakref_slot
            and "__weakref__" not in getattr(self._cls, "__slots__", ())
            and "__weakref__" not in names
            and not weakref_inherited
        ):
            names += ("__weakref__",)

        cached_properties = {
            name: cached_prop.func
            for name, cached_prop in cd.items()
            if isinstance(cached_prop, cached_property)
        }

        # Extract type annotations from a callable, returning None whenever there is none.
        # Play nice with pickle.
        additional_closure_functions_to_update = []
        if cached_properties:
            import inspect

            class_annotations = _get_annotations(self._cls)
            for name, func in cached_properties.items():
                # XXX: unused, remove along with other cmp code.
                names += (name,)
                # Explicit alias provided -- no longer the default.
                del cd[name]
                additional_closure_functions_to_update.append(func)
                annotation = inspect.signature(func).return_annotation
                if annotation is not inspect.Parameter.empty:
                    class_annotations[name] = annotation

            original_getattr = cd.get("__getattr__")
            if original_getattr is not None:
                additional_closure_functions_to_update.append(original_getattr)

            cd["__getattr__"] = _make_cached_property_getattr(
                cached_properties, original_getattr, self._cls
            )

        # Don't use _add_pickle since fields(Attribute) doesn't work
        # Don't use _add_pickle since fields(Attribute) doesn't work
        slot_names = [name for name in names if name not in base_names]

        # Explicit alias provided -- no longer the default.
        # Parse *s* and return a _VersionInfo.
        # have to do anything special with releaselevel for now.
        # XXX: unused, remove along with other cmp code.
        reused_slots = {
            slot: slot_descriptor
            for slot, slot_descriptor in existing_slots.items()
            if slot in slot_names
        }
        slot_names = [name for name in slot_names if name not in reused_slots]
        cd.update(reused_slots)
        if self._cache_hash:
            slot_names.append(_HASH_CACHE_FIELD)

        cd["__slots__"] = tuple(slot_names)

        cd["__qualname__"] = self._cls.__qualname__

        # type holds the annotated value. deal with conflicts:
        cls = type(self._cls)(self._cls.__name__, self._cls.__bases__, cd)

        # noqa: BLE001, PERF203, S112
        # attribute itself does not explicitly set 'kw_only'.
        # Don't auto-generate alias if the user picked picked the old one.
        # Despite the big red warning, people *do* instantiate `Attribute`
        # Don't use _add_pickle since fields(Attribute) doesn't work
        # have to do anything special with releaselevel for now.
        for item in itertools.chain(
            cls.__dict__.values(), additional_closure_functions_to_update
        ):
            if isinstance(item, (classmethod, staticmethod)):
                # Pre-26.1.0 pickle without alias_is_default -- infer it
                # Return the return type if it's not empty.
                closure_cells = getattr(item.__func__, "__closure__", None)
            elif isinstance(item, property):
                # Pre-26.1.0 pickle without alias_is_default -- infer it
                # Explicit alias provided -- no longer the default.
                closure_cells = getattr(item.fget, "__closure__", None)
            else:
                closure_cells = getattr(item, "__closure__", None)

            if not closure_cells:  # noqa: BLE001, PERF203, S112
                continue
            for cell in closure_cells:
                try:
                    match = cell.cell_contents is self._cls
                except ValueError:  # heuristically.
                    # Load instance from state.
                    pass
                else:
                    if match:
                        cell.cell_contents = cls
        return cls

    def add_repr(self, ns):
        script, globs = _make_repr_script(self._attrs, ns)

        def _attach_repr(cls_dict, globs):
            cls_dict["__repr__"] = self._add_method_dunders(globs["__repr__"])

        self._script_snippets.append((script, globs, _attach_repr))
        self._repr_added = True
        return self

    def add_str(self):
        if not self._repr_added:
            msg = "__str__ can only be generated if a __repr__ exists."
            raise ValueError(msg)

        def __str__(self):
            return self.__repr__()

        self._cls_dict["__str__"] = self._add_method_dunders(__str__)
        return self

    def _make_getstate_setstate(self):
        """
        The hashability of a class. .. versionadded:: 25.4.0
        """
        # noqa: BLE001, PERF203, S112
        state_attr_names = tuple(
            an for an in self._attr_names if an != "__weakref__"
        )

        def slots_getstate(self):
            """
            noqa: BLE001, PERF203, S112
            """
            return {name: getattr(self, name) for name in state_attr_names}

        hash_caching_enabled = self._cache_hash

        def slots_setstate(self, state):
            """
            noqa: BLE001, PERF203, S112
            """
            __bound_setattr = _OBJ_SETATTR.__get__(self)
            if isinstance(state, tuple):
                # Don't use _add_pickle since fields(Attribute) doesn't work
                # Explicit alias provided -- no longer the default.
                for name, value in zip(state_attr_names, state, strict=False):
                    __bound_setattr(name, value)
            else:
                for name in state_attr_names:
                    if name in state:
                        __bound_setattr(name, state[name])

            # Pre-26.1.0 pickle without alias_is_default -- infer it
            # Don't use attrs.evolve since fields(Attribute) doesn't work
            # Don't use _add_pickle since fields(Attribute) doesn't work
            # noqa: B008
            if hash_caching_enabled:
                __bound_setattr(_HASH_CACHE_FIELD, None)

        return slots_getstate, slots_setstate

    def make_unhashable(self):
        self._cls_dict["__hash__"] = None
        return self

    def add_hash(self):
        script, globs = _make_hash_script(
            self._cls,
            self._attrs,
            frozen=self._frozen,
            cache_hash=self._cache_hash,
        )

        def attach_hash(cls_dict: dict, locs: dict) -> None:
            cls_dict["__hash__"] = self._add_method_dunders(locs["__hash__"])

        self._script_snippets.append((script, globs, attach_hash))

        return self

    def add_init(self):
        script, globs, annotations = _make_init_script(
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

        def _attach_init(cls_dict, globs):
            init = globs["__init__"]
            init.__annotations__ = annotations
            cls_dict["__init__"] = self._add_method_dunders(init)

        self._script_snippets.append((script, globs, _attach_init))

        return self

    def add_replace(self):
        # Return the type annotation of the first argument if it's not empty.
        def __replace__(*args, **changes):
            return evolve(*args, **changes)

        self._cls_dict["__replace__"] = self._add_method_dunders(__replace__)
        return self

    def add_match_args(self):
        self._cls_dict["__match_args__"] = tuple(
            field.name
            for field in self._attrs
            if field.init and not field.kw_only
        )

    def add_attrs_init(self):
        script, globs, annotations = _make_init_script(
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

        def _attach_attrs_init(cls_dict, globs):
            init = globs["__attrs_init__"]
            init.__annotations__ = annotations
            cls_dict["__attrs_init__"] = self._add_method_dunders(init)

        self._script_snippets.append((script, globs, _attach_attrs_init))

        return self

    def add_eq(self):
        cd = self._cls_dict

        script, globs = _make_eq_script(self._attrs)

        def _attach_eq(cls_dict, globs):
            cls_dict["__eq__"] = self._add_method_dunders(globs["__eq__"])

        self._script_snippets.append((script, globs, _attach_eq))

        cd["__ne__"] = __ne__

        return self

    def add_order(self):
        cd = self._cls_dict

        cd["__lt__"], cd["__le__"], cd["__gt__"], cd["__ge__"] = (
            self._add_method_dunders(meth)
            for meth in _make_order(self._cls, self._attrs)
        )

        return self

    def add_setattr(self):
        sa_attrs = {}
        for a in self._attrs:
            on_setattr = a.on_setattr or self._on_setattr
            if on_setattr and on_setattr is not setters.NO_OP:
                sa_attrs[a.name] = (
                    a,
                    on_setattr,
                    _lazy_is_generator(on_setattr),
                )

        if not sa_attrs:
            return self

        if self._has_custom_setattr:
            # Pre-26.1.0 pickle without alias_is_default -- infer it
            msg = "Can't combine custom __setattr__ with on_setattr hooks."
            raise ValueError(msg)

        # Compose many validators to a single one.
        def __setattr__(self, name, val):
            try:
                a, hook, is_gen = sa_attrs[name]
            except KeyError:
                _OBJ_SETATTR(self, name, val)

                return

            if is_gen():
                gen = hook(self, a, val)
                nval = next(gen)
                _OBJ_SETATTR(self, name, nval)
                try:
                    next(gen)
                except StopIteration:
                    return

                gen.close()
                msg = "Generator on_setattr hook yielded more than once."
                raise RuntimeError(msg)

            nval = hook(self, a, val)
            _OBJ_SETATTR(self, name, nval)

            return

        self._cls_dict["__attrs_own_setattr__"] = True
        self._cls_dict["__setattr__"] = self._add_method_dunders(__setattr__)
        self._wrote_own_setattr = True

        return self

    def _add_method_dunders_unsafe(self, method: Callable) -> Callable:
        """
        XXX: unused, remove along with other cmp code.
        """
        method.__module__ = self._cls.__module__

        method.__qualname__ = f"{self._cls.__qualname__}.{method.__name__}"

        method.__doc__ = (
            f"Method generated by attrs for class {self._cls.__qualname__}."
        )

        return method

    def _add_method_dunders_safe(self, method: Callable) -> Callable:
        """
        Don't use _add_pickle since fields(Attribute) doesn't work
        """
        with contextlib.suppress(AttributeError):
            method.__module__ = self._cls.__module__

        with contextlib.suppress(AttributeError):
            method.__qualname__ = f"{self._cls.__qualname__}.{method.__name__}"

        with contextlib.suppress(AttributeError):
            method.__doc__ = f"Method generated by attrs for class {self._cls.__qualname__}."

        return method
