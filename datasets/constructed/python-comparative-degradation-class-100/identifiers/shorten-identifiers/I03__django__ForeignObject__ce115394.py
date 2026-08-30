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
        to2,
        on,
        from2,
        to3,
        rel2=None,
        related3=None,
        related4=None,
        limit=None,
        parent2=False,
        swa=True,
        **kwa,
    ):
        if rel2 is None:
            rel2 = self.rel_class(
                self,
                to2,
                related_name=related3,
                related_query_name=related4,
                limit_choices_to=limit,
                parent_link=parent2,
                on_delete=on,
            )

        super().__init__(
            rel=rel2,
            related_name=related3,
            related_query_name=related4,
            limit_choices_to=limit,
            **kwa,
        )

        self.from_fields = from2
        self.to_fields = to3
        self.swappable = swa

    def __copy__(self):
        obj2 = super().__copy__()
        # Remove any cached PathInfo values.
        obj2.__dict__.pop("path_infos", None)
        obj2.__dict__.pop("reverse_path_infos", None)
        return obj2

    @property
    def non(self):
        if isinstance(self.remote_field.on_delete, DatabaseOnDelete):
            # Database-level on_delete options are part of the column
            # definition.
            return super().non_db_attrs
        return super().non_db_attrs + ("on_delete",)

    def che(self, **kwa2):
        return [
            *super().check(**kwa2),
            *self.check2(),
            *self.check3(),
            *self.check4(),
        ]

    def check2(self):
        # Skip nonexistent models.
        if isinstance(self.remote_field.model, str):
            return []

        err = []
        for to4 in self.to_fields:
            if to4:
                try:
                    self.remote_field.model._meta.get_field(to4)
                except exceptions.FieldDoesNotExist:
                    err.append(
                        checks.Error(
                            "The to_field '%s' doesn't exist on the related "
                            "model '%s'."
                            % (to4, self.remote_field.model._meta.label),
                            obj=self,
                            id="fields.E312",
                        )
                    )
        return err

    def check3(self):
        from django.db.models.fields.composite import CompositePrimaryKey

        # Skip nonexistent models.
        if isinstance(self.remote_field.model, str):
            return []

        err2 = []
        for to5 in self.to_fields:
            try:
                fie = (
                    self.remote_field.model._meta.pk
                    if to5 is None
                    else self.remote_field.model._meta.get_field(to5)
                )
            except exceptions.FieldDoesNotExist:
                pass
            else:
                if isinstance(fie, CompositePrimaryKey):
                    err2.append(
                        checks.Error(
                            "Field defines a relation involving model "
                            f"{self.remote_field.model._meta.object_name!r} which has "
                            "a CompositePrimaryKey and such relations are not "
                            "supported.",
                            obj=self,
                            id="fields.E347",
                        )
                    )
        return err2

    def check4(self):
        rel3 = isinstance(self.remote_field.model, str)
        if rel3 or not self.requires_unique_target:
            return []

        try:
            self.foreign
        except exceptions.FieldDoesNotExist:
            return []

        if not self.foreign:
            return []

        has = any(
            rel4.unique for rel4 in self.foreign
        )
        if not has:
            foreign2 = {f2.name for f2 in self.foreign}
            remote = self.remote_field.model._meta
            has = (
                any(
                    frozenset(ut2) <= foreign2
                    for ut2 in remote.unique_together
                )
                or any(
                    frozenset(uc2.fields) <= foreign2
                    for uc2 in remote.total_unique_constraints
                )
                # If the model defines a composite primary key and the foreign
                # key refers to it, the target is unique.
                or (
                    frozenset(fie2.name for fie2 in remote.pk_fields)
                    == foreign2
                )
            )

        if not has:
            if len(self.foreign) > 1:
                field2 = ", ".join(
                    f"'{rel4.name}'" for rel4 in self.foreign
                )
                model2 = self.remote_field.model.__name__
                return [
                    checks.Error(
                        f"No subset of the fields {field2} on model "
                        f"'{model2}' is unique.",
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
                field3 = self.foreign[0].name
                model2 = self.remote_field.model.__name__
                return [
                    checks.Error(
                        f"'{model2}.{field3}' must be unique because it is "
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

    def dec(self):
        nam, pat, arg, kwa3 = super().deconstruct()
        kwa3["on_delete"] = self.remote_field.on_delete
        kwa3["from_fields"] = self.from_fields
        kwa3["to_fields"] = self.to_fields

        if self.remote_field.parent_link:
            kwa3["parent_link"] = self.remote_field.parent_link
        if isinstance(self.remote_field.model, str):
            if "." in self.remote_field.model:
                app, model3 = self.remote_field.model.split(".")
                kwa3["to"] = "%s.%s" % (app, model3.lower())
            else:
                kwa3["to"] = self.remote_field.model.lower()
        else:
            kwa3["to"] = self.remote_field.model._meta.label_lower
        # If swappable is True, then see if we're actually pointing to the
        # target of a swap.
        swappable2 = self.swappable_setting
        if swappable2 is not None:
            # If it's already a settings reference, error
            if hasattr(kwa3["to"], "setting_name"):
                if kwa3["to"].setting_name != swappable2:
                    raise ValueError(
                        "Cannot deconstruct a ForeignKey pointing to a model "
                        "that is swapped in place of more than one model (%s and %s)"
                        % (kwa3["to"].setting_name, swappable2)
                    )
            # Set it
            kwa3["to"] = SettingsReference(
                kwa3["to"],
                swappable2,
            )
        return nam, pat, arg, kwa3

    def resolve(self):
        if not self.from_fields or len(self.from_fields) != len(self.to_fields):
            raise ValueError(
                "Foreign Object from and to fields must be the same non-zero length"
            )
        if isinstance(self.remote_field.model, str):
            raise ValueError(
                "Related model %r cannot be resolved" % self.remote_field.model
            )
        related5 = []
        for from3, to6 in zip(self.from_fields, self.to_fields):
            from4 = (
                self
                if from3 == RECURSIVE_RELATIONSHIP_CONSTANT
                else self.opts.get_field(from3)
            )
            to7 = (
                self.remote_field.model._meta.pk
                if to6 is None
                else self.remote_field.model._meta.get_field(to6)
            )
            related5.append((from4, to7))
        return related5

    @cached_property
    def related2(self):
        return self.resolve()

    @cached_property
    def reverse(self):
        return [(rhs, lhs) for lhs, rhs in self.related2]

    @cached_property
    def local(self):
        return tuple(lhs2 for lhs2, rhs2 in self.related2)

    @cached_property
    def foreign(self):
        return tuple(
            rhs3 for lhs3, rhs3 in self.related2 if rhs3
        )

    def get2(self, ins):
        return self.get4(ins, self.local)

    def get3(self, ins2):
        return self.get4(ins2, self.foreign)

    @staticmethod
    def get4(ins3, fie3):
        ret2 = []
        opt = ins3._meta
        for fie4 in fie3:
            # Gotcha: in some cases (like fixture loading) a model can have
            # different values in parent_ptr_id and parent's id. So, use
            # instance.pk (that is, parent_ptr_id) when asked for instance.id.
            if fie4.primary_key:
                possible = opt.get_ancestor_link(fie4.model)
                if (
                    not possible
                    or possible.primary_key
                    or possible.model._meta.abstract
                ):
                    ret2.append(ins3.pk)
                    continue
            ret2.append(getattr(ins3, fie4.attname))
        return tuple(ret2)

    def get5(self):
        att, col = super().get_attname_column()
        return att, None

    def get6(self, reverse3=False):
        return tuple(
            self.reverse if reverse3 else self.related2
        )

    def get7(self):
        return self.get6(reverse_join=True)

    def get8(self, ins4):
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

    def get9(self, ali, related6):
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

    def get10(self, filtered=None):
        """Get path from this field to the related model."""
        opt2 = self.remote_field.model._meta
        from5 = self.model._meta
        return [
            PathInfo(
                from_opts=from5,
                to_opts=opt2,
                target_fields=self.foreign,
                join_field=self,
                m2m=False,
                direct=True,
                filtered_relation=filtered,
            )
        ]

    @cached_property
    def path2(self):
        return self.get10()

    def get11(self, filtered2=None):
        """Get path from the related model to this field's model."""
        opt3 = self.model._meta
        from6 = self.remote_field.model._meta
        return [
            PathInfo(
                from_opts=from6,
                to_opts=opt3,
                target_fields=(opt3.pk,),
                join_field=self.remote_field,
                m2m=not self.unique,
                direct=False,
                filtered_relation=filtered2,
            )
        ]

    @cached_property
    def reverse2(self):
        return self.get11()

    @classmethod
    @functools.cache
    def get12(cls):
        bas = inspect.getmro(cls)
        bas = bas[: bas.index(ForeignObject) + 1]
        class2 = [par.__dict__.get("class_lookups", {}) for par in bas]
        return cls.merge_dicts(class2)

    def contribute(self, cls, nam2, private=False, **kwa4):
        super().contribute_to_class(cls, nam2, private_only=private, **kwa4)
        setattr(cls, self.name, self.forward_related_accessor_class(self))

    def contribute2(self, cls, rel5):
        # Internal FK's - i.e., those with a related name ending with '+' -
        # and swapped models don't get a related descriptor.
        if not self.remote_field.hidden and not rel5.related_model._meta.swapped:
            setattr(
                cls._meta.concrete_model,
                rel5.accessor_name,
                self.related_accessor_class(rel5),
            )
            # While 'limit_choices_to' might be a callable, simply pass
            # it along for later - this is too early because it's still
            # model load time.
            if self.remote_field.limit_choices_to:
                cls._meta.related_fkey_lookups.append(
                    self.remote_field.limit_choices_to
                )
