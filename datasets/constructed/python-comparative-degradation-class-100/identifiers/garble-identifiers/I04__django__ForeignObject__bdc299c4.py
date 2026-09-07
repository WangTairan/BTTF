import functools
import inspect
from functools import partial
from django import forms
from django.apps import apps
from django.conf import SettingsReference, settings
from django.core import checks, exceptions
from django.db import connection, connections, router
from django.db.backends import utils
from django.db.models import NOT_PROVIDED, Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.deletion import (
    CASCADE,
    DB_CASCADE,
    DB_SET_DEFAULT,
    DB_SET_NULL,
    DO_NOTHING,
    SET_DEFAULT,
    SET_NULL,
    DatabaseOnDelete,
)
from django.db.models.query_utils import PathInfo
from django.db.models.utils import make_model_tuple
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from . import Field
from .mixins import FieldCacheMixin
from .related_descriptors import (
    ForeignKeyDeferredAttribute,
    ForwardManyToOneDescriptor,
    ForwardOneToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from .related_lookups import (
    RelatedExact,
    RelatedGreaterThan,
    RelatedGreaterThanOrEqual,
    RelatedIn,
    RelatedIsNull,
    RelatedLessThan,
    RelatedLessThanOrEqual,
)
from .reverse_related import ForeignObjectRel, ManyToManyRel, ManyToOneRel, OneToOneRel

class ForeignObject(RelatedField):
    """
    Abstraction of the ForeignKey relation to support multi-column relations.
    """

    # Field flags
    many_to_many = False
    many_to_one = True
    one_to_many = False
    one_to_one = False

    requires_unique_target = True
    related_accessor_class = ReverseManyToOneDescriptor
    forward_related_accessor_class = ForwardManyToOneDescriptor
    rel_class = ForeignObjectRel

    def __init__(
        self,
        B,
        C,
        D,
        E,
        F=None,
        G=None,
        H=None,
        I=None,
        J=False,
        K=True,
        **L,
    ):
        if F is None:
            F = self.rel_class(
                self,
                B,
                related_name=G,
                related_query_name=H,
                limit_choices_to=I,
                parent_link=J,
                on_delete=C,
            )

        super().__init__(
            rel=F,
            related_name=G,
            related_query_name=H,
            limit_choices_to=I,
            **L,
        )

        self.from_fields = D
        self.to_fields = E
        self.swappable = K

    def __copy__(self):
        M = super().__copy__()
        # Remove any cached PathInfo values.
        M.__dict__.pop("path_infos", None)
        M.__dict__.pop("reverse_path_infos", None)
        return M

    @property
    def a(self):
        if isinstance(self.remote_field.on_delete, DatabaseOnDelete):
            # Database-level on_delete options are part of the column
            # definition.
            return super().non_db_attrs
        return super().non_db_attrs + ("on_delete",)

    def b(self, **N):
        return [
            *super().check(**N),
            *self.c(),
            *self.d(),
            *self.e(),
        ]

    def c(self):
        # Skip nonexistent models.
        if isinstance(self.remote_field.model, str):
            return []

        O = []
        for P in self.to_fields:
            if P:
                try:
                    self.remote_field.model._meta.get_field(P)
                except exceptions.FieldDoesNotExist:
                    O.append(
                        checks.Error(
                            "The to_field '%s' doesn't exist on the related "
                            "model '%s'."
                            % (P, self.remote_field.model._meta.label),
                            obj=self,
                            id="fields.E312",
                        )
                    )
        return O

    def d(self):
        from django.db.models.fields.composite import CompositePrimaryKey

        # Skip nonexistent models.
        if isinstance(self.remote_field.model, str):
            return []

        Q = []
        for R in self.to_fields:
            try:
                S = (
                    self.remote_field.model._meta.pk
                    if R is None
                    else self.remote_field.model._meta.get_field(R)
                )
            except exceptions.FieldDoesNotExist:
                pass
            else:
                if isinstance(S, CompositePrimaryKey):
                    Q.append(
                        checks.Error(
                            "Field defines a relation involving model "
                            f"{self.remote_field.model._meta.object_name!r} which has "
                            "a CompositePrimaryKey and such relations are not "
                            "supported.",
                            obj=self,
                            id="fields.E347",
                        )
                    )
        return Q

    def e(self):
        T = isinstance(self.remote_field.model, str)
        if T or not self.requires_unique_target:
            return []

        try:
            self.l
        except exceptions.FieldDoesNotExist:
            return []

        if not self.l:
            return []

        U = any(
            V.unique for V in self.l
        )
        if not U:
            W = {X.name for X in self.l}
            Y = self.remote_field.model._meta
            U = (
                any(
                    frozenset(Z) <= W
                    for Z in Y.unique_together
                )
                or any(
                    frozenset(aa.fields) <= W
                    for aa in Y.total_unique_constraints
                )
                # If the model defines a composite primary key and the foreign
                # key refers to it, the target is unique.
                or (
                    frozenset(ab.name for ab in Y.pk_fields)
                    == W
                )
            )

        if not U:
            if len(self.l) > 1:
                ac = ", ".join(
                    f"'{V.name}'" for V in self.l
                )
                ad = self.remote_field.model.__name__
                return [
                    checks.Error(
                        f"No subset of the fields {ac} on model "
                        f"'{ad}' is unique.",
                        hint=(
                            "Mark a single field as unique=True or add a set of "
                            "fields to a unique constraint (via unique_together "
                            "or a UniqueConstraint (without condition) in the "
                            "model Meta.constraints)."
                        ),
                        obj=self,
                        id="fields.E310",
                    )
                ]
            else:
                ae = self.l[0].name
                ad = self.remote_field.model.__name__
                return [
                    checks.Error(
                        f"'{ad}.{ae}' must be unique because it is "
                        "referenced by a foreign key.",
                        hint=(
                            "Add unique=True to this field or add a "
                            "UniqueConstraint (without condition) in the model "
                            "Meta.constraints."
                        ),
                        obj=self,
                        id="fields.E311",
                    )
                ]
        return []

    def g(self):
        af, ag, ah, ai = super().deconstruct()
        ai["on_delete"] = self.remote_field.on_delete
        ai["from_fields"] = self.from_fields
        ai["to_fields"] = self.to_fields

        if self.remote_field.parent_link:
            ai["parent_link"] = self.remote_field.parent_link
        if isinstance(self.remote_field.model, str):
            if "." in self.remote_field.model:
                aj, ak = self.remote_field.model.split(".")
                ai["to"] = "%s.%s" % (aj, ak.lower())
            else:
                ai["to"] = self.remote_field.model.lower()
        else:
            ai["to"] = self.remote_field.model._meta.label_lower
        # If swappable is True, then see if we're actually pointing to the
        # target of a swap.
        al = self.swappable_setting
        if al is not None:
            # If it's already a settings reference, error
            if hasattr(ai["to"], "setting_name"):
                if ai["to"].setting_name != al:
                    raise ValueError(
                        "Cannot deconstruct a ForeignKey pointing to a model "
                        "that is swapped in place of more than one model (%s and %s)"
                        % (ai["to"].setting_name, al)
                    )
            # Set it
            ai["to"] = SettingsReference(
                ai["to"],
                al,
            )
        return af, ag, ah, ai

    def h(self):
        if not self.from_fields or len(self.from_fields) != len(self.to_fields):
            raise ValueError(
                "Foreign Object from and to fields must be the same non-zero length"
            )
        if isinstance(self.remote_field.model, str):
            raise ValueError(
                "Related model %r cannot be resolved" % self.remote_field.model
            )
        am = []
        for an, ao in zip(self.from_fields, self.to_fields):
            ap = (
                self
                if an == RECURSIVE_RELATIONSHIP_CONSTANT
                else self.opts.get_field(an)
            )
            aq = (
                self.remote_field.model._meta.pk
                if ao is None
                else self.remote_field.model._meta.get_field(ao)
            )
            am.append((ap, aq))
        return am

    @cached_property
    def i(self):
        return self.h()

    @cached_property
    def j(self):
        return [(at, ar) for ar, at in self.i]

    @cached_property
    def k(self):
        return tuple(au for au, av in self.i)

    @cached_property
    def l(self):
        return tuple(
            ax for aw, ax in self.i if ax
        )

    def m(self, ay):
        return self.o(ay, self.k)

    def n(self, az):
        return self.o(az, self.l)

    @staticmethod
    def o(aA, aB):
        aC = []
        aD = aA._meta
        for aE in aB:
            # Gotcha: in some cases (like fixture loading) a model can have
            # different values in parent_ptr_id and parent's id. So, use
            # instance.pk (that is, parent_ptr_id) when asked for instance.id.
            if aE.primary_key:
                aF = aD.get_ancestor_link(aE.model)
                if (
                    not aF
                    or aF.primary_key
                    or aF.model._meta.abstract
                ):
                    aC.append(aA.pk)
                    continue
            aC.append(getattr(aA, aE.attname))
        return tuple(aC)

    def p(self):
        aG, aH = super().get_attname_column()
        return aG, None

    def q(self, aI=False):
        return tuple(
            self.j if aI else self.i
        )

    def r(self):
        return self.q(reverse_join=True)

    def s(self, aJ):
        """
        Return an extra filter condition for related object fetching when
        user does 'instance.fieldname', that is the extra filter is used in
        the descriptor of the field.

        The filter should be either a dict usable in .filter(**kwargs) call or
        a Q-object. The condition will be ANDed together with the relation's
        joining columns.

        A parallel method is get_extra_restriction() which is used in
        JOIN and subquery conditions.
        """
        return {}

    def t(self, aK, aL):
        """
        Return a pair condition used for joining and subquery pushdown. The
        condition is something that responds to as_sql(compiler, connection)
        method.

        Note that currently referring both the 'alias' and 'related_alias'
        will not work in some conditions, like subquery pushdown.

        A parallel method is get_extra_descriptor_filter() which is used in
        instance.fieldname related object fetching.
        """
        return None

    def u(self, aM=None):
        """Get path from this field to the related model."""
        aN = self.remote_field.model._meta
        aO = self.model._meta
        return [
            PathInfo(
                from_opts=aO,
                to_opts=aN,
                target_fields=self.l,
                join_field=self,
                m2m=False,
                direct=True,
                filtered_relation=aM,
            )
        ]

    @cached_property
    def v(self):
        return self.u()

    def w(self, aP=None):
        """Get path from the related model to this field's model."""
        aQ = self.model._meta
        aR = self.remote_field.model._meta
        return [
            PathInfo(
                from_opts=aR,
                to_opts=aQ,
                target_fields=(aQ.pk,),
                join_field=self.remote_field,
                m2m=not self.unique,
                direct=False,
                filtered_relation=aP,
            )
        ]

    @cached_property
    def x(self):
        return self.w()

    @classmethod
    @functools.cache
    def y(cls):
        aS = inspect.getmro(cls)
        aS = aS[: aS.index(ForeignObject) + 1]
        aT = [aU.__dict__.get("class_lookups", {}) for aU in aS]
        return cls.merge_dicts(aT)

    def z(self, cls, aV, aW=False, **aX):
        super().contribute_to_class(cls, aV, private_only=aW, **aX)
        setattr(cls, self.name, self.forward_related_accessor_class(self))

    def A(self, cls, aY):
        # Internal FK's - i.e., those with a related name ending with '+' -
        # and swapped models don't get a related descriptor.
        if not self.remote_field.hidden and not aY.related_model._meta.swapped:
            setattr(
                cls._meta.concrete_model,
                aY.accessor_name,
                self.related_accessor_class(aY),
            )
            # While 'limit_choices_to' might be a callable, simply pass
            # it along for later - this is too early because it's still
            # model load time.
            if self.remote_field.limit_choices_to:
                cls._meta.related_fkey_lookups.append(
                    self.remote_field.limit_choices_to
                )
