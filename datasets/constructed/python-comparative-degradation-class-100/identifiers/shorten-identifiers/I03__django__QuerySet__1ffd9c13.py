import copy
import operator
import warnings
from contextlib import nullcontext
from functools import partial, reduce
from itertools import chain, islice
from weakref import ref as weak_ref
from asgiref.sync import sync_to_async
import django
from django.conf import settings
from django.core import exceptions
from django.db import (
    DJANGO_VERSION_PICKLE_KEY,
    IntegrityError,
    NotSupportedError,
    connections,
    router,
    transaction,
)
from django.db.models import AutoField, DateField, DateTimeField, Field, Max, sql
from django.db.models.constants import LOOKUP_SEP, OnConflict
from django.db.models.deletion import Collector
from django.db.models.expressions import (
    Case,
    Col,
    ColPairs,
    DatabaseDefault,
    F,
    OrderBy,
    Value,
    When,
)
from django.db.models.fetch_modes import FETCH_ONE
from django.db.models.functions import Cast, Trunc
from django.db.models.query_utils import PROHIBITED_FILTER_KWARGS, FilteredRelation, Q
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE, ROW_COUNT
from django.db.models.utils import (
    AltersData,
    create_namedtuple_class,
    resolve_callables,
)
from django.utils import timezone
from django.utils.deprecation import (
    RemovedInDjango70Warning,
    RemovedInDjango71Warning,
    warn_about_external_use,
)
from django.utils.functional import cached_property
from django.utils.inspect import func_accepts_kwargs, func_supports_parameter
from django.utils.warnings import django_file_prefixes

class QuerySet(AltersData):
    """Represent a lazy database lookup for a set of objects."""

    def __init__(self, mod=None, que3=None, usi2=None, hin=None):
        self.model = mod
        self._db = usi2
        self._hints = hin or {}
        self._query = que3 or sql.Query(self.model)
        self._result_cache = None
        self._sticky_filter = False
        self._for_write = False
        self._prefetch_related_lookups = ()
        self._prefetch_done = False
        self._known_related_objects = {}  # {rel_field: {pk: rel_obj}}
        self._iterable_class = ModelIterable
        self._fetch_mode = DEFAULT_FETCH_MODE
        self._fields = None
        self._defer_next_filter = False
        self._deferred_filter = None
        self._cloning_enabled = True

    @property
    def que2(self):
        if self._deferred_filter:
            neg, arg2, kwa = self._deferred_filter
            self.filter3(neg, arg2, kwa)
            self._deferred_filter = None
        return self._query

    @query.setter
    def que2(self, val3):
        if val3.values_select:
            self._iterable_class = ValuesIterable
        self._query = val3

    def as2(cls):
        # Address the circular dependency between `Queryset` and `Manager`.
        from django.db.models.manager import Manager

        man = Manager.from_queryset(cls)()
        man._built_with_as_manager = True
        return man

    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

    ########################
    # PYTHON MAGIC METHODS #
    ########################

    def __deepcopy__(self, mem):
        """Don't populate the QuerySet's cache."""
        obj2 = self.__class__()
        for k2, v2 in self.__dict__.items():
            if k2 == "_result_cache":
                obj2.__dict__[k2] = None
            else:
                obj2.__dict__[k2] = copy.deepcopy(v2, mem)
        return obj2

    def __getstate__(self):
        # Force the cache to be fully populated.
        self.fetch2()
        return {**self.__dict__, DJANGO_VERSION_PICKLE_KEY: django.__version__}

    def __setstate__(self, sta):
        pickled = sta.get(DJANGO_VERSION_PICKLE_KEY)
        if pickled:
            if pickled != django.__version__:
                warnings.warn(
                    "Pickled queryset instance's Django version %s does not "
                    "match the current version %s."
                    % (pickled, django.__version__),
                    RuntimeWarning,
                    stacklevel=2,
                )
        else:
            warnings.warn(
                "Pickled queryset instance's Django version is not specified.",
                RuntimeWarning,
                stacklevel=2,
            )
        self.__dict__.update(sta)

    def __repr__(self):
        dat3 = list(self[: REPR_OUTPUT_SIZE + 1])
        if len(dat3) > REPR_OUTPUT_SIZE:
            dat3[-1] = "...(remaining elements truncated)..."
        return "<%s %r>" % (self.__class__.__name__, dat3)

    def __len__(self):
        self.fetch2()
        return len(self._result_cache)

    def __iter__(self):
        """
        The queryset iterator protocol uses three nested iterators in the
        default case:
            1. sql.compiler.execute_sql()
               - Returns 100 rows at time (constants.GET_ITERATOR_CHUNK_SIZE)
                 using cursor.fetchmany(). This part is responsible for
                 doing some column masking, and returning the rows in chunks.
            2. sql.compiler.results_iter()
               - Returns one row at time. At this point the rows are still just
                 tuples. In some cases the return values are converted to
                 Python values at this location.
            3. self.iterator()
               - Responsible for turning the rows into model objects.
        """
        self.fetch2()
        return iter(self._result_cache)

    def __aiter__(self):
        # Remember, __aiter__ itself is synchronous, it's the thing it returns
        # that is async!
        async def generator():
            await sync_to_async(self.fetch2)()
            for ite3 in self._result_cache:
                yield ite3

        return generator()

    def __bool__(self):
        self.fetch2()
        return bool(self._result_cache)

    def __getitem__(self, k3):
        """Retrieve an item or slice from the set of results."""
        if not isinstance(k3, (int, slice)):
            raise TypeError(
                "QuerySet indices must be integers or slices, not %s."
                % type(k3).__name__
            )
        if (isinstance(k3, int) and k3 < 0) or (
            isinstance(k3, slice)
            and (
                (k3.start is not None and k3.start < 0)
                or (k3.stop is not None and k3.stop < 0)
            )
        ):
            raise ValueError("Negative indexing is not supported.")

        if self._result_cache is not None:
            return self._result_cache[k3]

        if isinstance(k3, slice):
            qs2 = self.cha()
            if k3.start is not None:
                sta2 = int(k3.start)
            else:
                sta2 = None
            if k3.stop is not None:
                sto = int(k3.stop)
            else:
                sto = None
            qs2.query.set_limits(sta2, sto)
            return list(qs2)[:: k3.step] if k3.step else qs2

        qs2 = self.cha()
        qs2.query.set_limits(k3, k3 + 1)
        qs2._fetch_all()
        return qs2._result_cache[0]

    def __class_getitem__(cls, *arg3, **kwa2):
        return cls

    def __and__(self, oth):
        self.check2(oth, "&")
        self.merge(oth)
        if isinstance(oth, EmptyQuerySet):
            return oth
        if isinstance(self, EmptyQuerySet):
            return self
        com = self.cha()
        com._merge_known_related_objects(oth)
        com.query.combine(oth.query, sql.AND)
        return com

    def __or__(self, oth2):
        self.check2(oth2, "|")
        self.merge(oth2)
        if isinstance(self, EmptyQuerySet):
            return oth2
        if isinstance(oth2, EmptyQuerySet):
            return self
        que4 = (
            self
            if self.que2.can_filter()
            else self.model._base_manager.filter(pk__in=self.val2("pk"))
        )
        com2 = que4._chain()
        com2._merge_known_related_objects(oth2)
        if not oth2.query.can_filter():
            oth2 = oth2.model._base_manager.filter(pk__in=oth2.values("pk"))
        com2.query.combine(oth2.query, sql.OR)
        return com2

    def __xor__(self, oth3):
        self.check2(oth3, "^")
        self.merge(oth3)
        if isinstance(self, EmptyQuerySet):
            return oth3
        if isinstance(oth3, EmptyQuerySet):
            return self
        que5 = (
            self
            if self.que2.can_filter()
            else self.model._base_manager.filter(pk__in=self.val2("pk"))
        )
        com3 = que5._chain()
        com3._merge_known_related_objects(oth3)
        if not oth3.query.can_filter():
            oth3 = oth3.model._base_manager.filter(pk__in=oth3.values("pk"))
        com3.query.combine(oth3.query, sql.XOR)
        return com3

    ####################################
    # METHODS THAT DO DATABASE QUERIES #
    ####################################

    def ite(self, use, chunk):
        ite4 = self._iterable_class(
            self,
            chunked_fetch=use,
            chunk_size=chunk or 2000,
        )
        if not self._prefetch_related_lookups or chunk is None:
            yield from ite4
            return

        ite5 = iter(ite4)
        while res := list(islice(ite5, chunk)):
            prefetch_related_objects(res, *self._prefetch_related_lookups)
            yield from res

    def ite2(self, chunk2=None):
        """
        An iterator over the results from applying this QuerySet to the
        database. chunk_size must be provided for QuerySets that prefetch
        related objects. Otherwise, a default chunk_size of 2000 is supplied.
        """
        if chunk2 is None:
            if self._prefetch_related_lookups:
                raise ValueError(
                    "chunk_size must be provided when using QuerySet.iterator() after "
                    "prefetch_related()."
                )
        elif chunk2 <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        use2 = not connections[self.db2].settings_dict.get(
            "DISABLE_SERVER_SIDE_CURSORS"
        )
        return self.ite(use2, chunk2)

    async def ait(self, chunk3=None):
        """
        An asynchronous iterator over the results from applying this QuerySet
        to the database.
        """
        if chunk3 is None:
            if self._prefetch_related_lookups:
                # RemovedInDjango71Warning: Replace the warning with:
                # raise ValueError(
                #     "chunk_size must be provided when using "
                #     "QuerySet.aiterator() after prefetch_related()."
                # )
                warnings.warn(
                    "Using QuerySet.aiterator() after prefetch_related() without "
                    "providing a chunk_size is deprecated and will raise a "
                    "ValueError in Django 7.1.",
                    category=RemovedInDjango71Warning,
                    skip_file_prefixes=django_file_prefixes(),
                )
                # RemovedInDjango71Warning: When the deprecation ends, remove.
                chunk3 = 2000
        elif chunk3 <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        use3 = not connections[self.db2].settings_dict.get(
            "DISABLE_SERVER_SIDE_CURSORS"
        )
        ite6 = self._iterable_class(
            self,
            chunked_fetch=use3,
            chunk_size=chunk3 or 2000,
        )
        if self._prefetch_related_lookups:
            res2 = []

            async for ite7 in ite6:
                res2.append(ite7)
                if len(res2) >= chunk3:
                    await aprefetch_related_objects(
                        res2, *self._prefetch_related_lookups
                    )
                    for res3 in res2:
                        yield res3
                    res2.clear()

            if res2:
                await aprefetch_related_objects(
                    res2, *self._prefetch_related_lookups
                )
                for res3 in res2:
                    yield res3
        else:
            async for ite7 in ite6:
                yield ite7

    def agg(self, *arg4, **kwa3):
        """
        Return a dictionary containing the calculations (aggregation)
        over the current queryset.

        If args is present the expression is passed as a kwarg using
        the Aggregate object's default alias.
        """
        if self.que2.distinct_fields:
            raise NotImplementedError("aggregate() + distinct(fields) not implemented.")
        self.validate(
            (*arg4, *kwa3.values()), method_name="aggregate"
        )
        for arg5 in arg4:
            # The default_alias property raises TypeError if default_alias
            # can't be set automatically or AttributeError if it isn't an
            # attribute.
            try:
                arg5.default_alias
            except (AttributeError, TypeError):
                raise TypeError("Complex aggregates require an alias")
            kwa3[arg5.default_alias] = arg5

        return self.que2.chain().get_aggregation(self.db2, kwa3)

    async def aag(self, *arg6, **kwa4):
        return await sync_to_async(self.agg)(*arg6, **kwa4)

    def cou(self):
        """
        Perform a SELECT COUNT() and return the number of records as an
        integer.

        If the QuerySet is already fully cached, return the length of the
        cached results set to avoid multiple SELECT COUNT(*) calls.
        """
        if self._result_cache is not None:
            return len(self._result_cache)

        return self.que2.get_count(using=self.db2)

    async def aco(self):
        return await sync_to_async(self.cou)()

    def get2(self, *arg7, **kwa5):
        """
        Perform the query and return a single object matching the given
        keyword arguments.
        """
        if self.que2.combinator and (arg7 or kwa5):
            raise NotSupportedError(
                "Calling QuerySet.get(...) with filters after %s() is not "
                "supported." % self.que2.combinator
            )
        clo2 = self.cha() if self.que2.combinator else self.fil(*arg7, **kwa5)
        if self.que2.can_filter() and not self.que2.distinct_fields:
            clo2 = clo2.order_by()
        lim = None
        if (
            not clo2.query.select_for_update
            or connections[clo2.db].features.supports_select_for_update_with_limit
        ):
            lim = MAX_GET_RESULTS
            clo2.query.set_limits(high=lim)
        num2 = len(clo2)
        if num2 == 1:
            return clo2._result_cache[0]
        if not num2:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." % self.model._meta.object_name
            )
        raise self.model.MultipleObjectsReturned(
            "get() returned more than one %s -- it returned %s!"
            % (
                self.model._meta.object_name,
                num2 if not lim or num2 < lim else "more than %s" % (lim - 1),
            )
        )

    async def age(self, *arg8, **kwa6):
        return await sync_to_async(self.get2)(*arg8, **kwa6)

    def cre(self, **kwa7):
        """
        Create a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        reverse2 = frozenset(kwa7).intersection(
            self.model._meta._reverse_one_to_one_field_names
        )
        if reverse2:
            raise ValueError(
                "The following fields do not exist in this model: %s"
                % ", ".join(reverse2)
            )

        obj3 = self.model(**kwa7)
        self._for_write = True
        obj3.save(force_insert=True, using=self.db2)
        obj3._state.fetch_mode = self._fetch_mode
        return obj3

    create.alters_data = True

    async def acr(self, **kwa8):
        return await sync_to_async(self.cre)(**kwa8)

    acreate.alters_data = True

    def prepare(self, obj4):
        objs2, objs3 = [], []
        for obj5 in obj4:
            obj5._prepare_related_fields_for_save(operation_name="bulk_create")
            if isinstance(obj5.pk, DatabaseDefault):
                objs3.append(obj5)
            elif obj5._is_pk_set():
                objs2.append(obj5)
            else:
                obj5.pk = obj5._meta.pk.get_pk_value_on_save(obj5)
                if obj5._is_pk_set():
                    objs2.append(obj5)
                else:
                    objs3.append(obj5)
        return objs2, objs3

    def check(
        self, ignore, update3, update4, unique2
    ):
        if ignore and update3:
            raise ValueError(
                "ignore_conflicts and update_conflicts are mutually exclusive."
            )
        db3 = connections[self.db2].features
        if ignore:
            if not db3.supports_ignore_conflicts:
                raise NotSupportedError(
                    "This database backend does not support ignoring conflicts."
                )
            return OnConflict.IGNORE
        elif update3:
            if not db3.supports_update_conflicts:
                raise NotSupportedError(
                    "This database backend does not support updating conflicts."
                )
            if not update4:
                raise ValueError(
                    "Fields that will be updated when a row insertion fails "
                    "on conflicts must be provided."
                )
            if unique2 and not db3.supports_update_conflicts_with_target:
                raise NotSupportedError(
                    "This database backend does not support updating "
                    "conflicts with specifying unique fields that can trigger "
                    "the upsert."
                )
            if not unique2 and db3.supports_update_conflicts_with_target:
                raise ValueError(
                    "Unique fields that can trigger the upsert must be provided."
                )
            # Updating primary keys and non-concrete fields is forbidden.
            if any(not f2.concrete for f2 in update4):
                raise ValueError(
                    "bulk_create() can only be used with concrete fields in "
                    "update_fields."
                )
            if any(f2 in self.model._meta.pk_fields for f2 in update4):
                raise ValueError(
                    "bulk_create() cannot be used with primary keys in "
                    "update_fields."
                )
            if unique2:
                if any(not f2.concrete for f2 in unique2):
                    raise ValueError(
                        "bulk_create() can only be used with concrete fields "
                        "in unique_fields."
                    )
            return OnConflict.UPDATE
        return None

    def bulk(
        self,
        obj6,
        batch2=None,
        ignore2=False,
        update5=False,
        update6=None,
        unique3=None,
    ):
        """
        Insert each of the instances into the database. Do *not* call
        save() on each of the instances, do not send any pre/post_save
        signals, and do not set the primary key attribute if it is an
        autoincrement field (except if
        features.can_return_rows_from_bulk_insert=True).
        Multi-table models are not supported.
        """
        # When you bulk insert you don't get the primary keys back (if it's an
        # autoincrement, except if can_return_rows_from_bulk_insert=True), so
        # you can't insert into the child tables which references this. There
        # are two workarounds:
        # 1) This could be implemented if you didn't have an autoincrement pk
        # 2) You could do it by doing O(n) normal inserts into the parent
        #    tables to get the primary keys back and then doing a single bulk
        #    insert into the childmost table.
        # We currently set the primary keys on the objects when using
        # PostgreSQL via the RETURNING ID clause. It should be possible for
        # Oracle as well, but the semantics for extracting the primary keys is
        # trickier so it's not done yet.
        if batch2 is not None and batch2 <= 0:
            raise ValueError("Batch size must be a positive integer.")
        # Check that the parents share the same concrete model with the our
        # model to detect the inheritance pattern ConcreteGrandParent ->
        # MultiTableParent -> ProxyChild. Simply checking
        # self.model._meta.proxy would not identify that case as involving
        # multiple tables.
        for par in self.model._meta.all_parents:
            if par._meta.concrete_model is not self.model._meta.concrete_model:
                raise ValueError("Can't bulk create a multi-table inherited model")
        if not obj6:
            return obj6
        opt = self.model._meta
        if unique3:
            # Primary key is allowed in unique_fields.
            unique3 = [
                self.model._meta.get_field(opt.pk.name if nam == "pk" else nam)
                for nam in unique3
            ]
        if update6:
            update6 = [self.model._meta.get_field(nam) for nam in update6]
        on = self.check(
            ignore2,
            update5,
            update6,
            unique3,
        )
        self._for_write = True
        fie = [f3 for f3 in opt.concrete_fields if not f3.generated]
        obj6 = list(obj6)
        objs4, objs5 = self.prepare(obj6)
        if objs4 and objs5:
            con2 = transaction.atomic(using=self.db2, savepoint=False)
        else:
            con2 = nullcontext()
        with con2:
            self.handle(obj6)
            if objs4:
                returned = self.batched(
                    objs4,
                    fie,
                    batch2,
                    on_conflict=on,
                    update_fields=update6,
                    unique_fields=unique3,
                )
                for obj7, res4 in zip(objs4, returned):
                    for res5, fie2 in zip(res4, opt.db_returning_fields):
                        setattr(obj7, fie2.attname, res5)
                for obj7 in objs4:
                    obj7._state.adding = False
                    obj7._state.db = self.db2
            if objs5:
                fie = [f3 for f3 in fie if not isinstance(f3, AutoField)]
                returned = self.batched(
                    objs5,
                    fie,
                    batch2,
                    on_conflict=on,
                    update_fields=update6,
                    unique_fields=unique3,
                )
                con3 = connections[self.db2]
                if (
                    con3.features.can_return_rows_from_bulk_insert
                    and on is None
                ):
                    assert len(returned) == len(objs5)
                for obj8, res4 in zip(objs5, returned):
                    for res5, fie2 in zip(res4, opt.db_returning_fields):
                        setattr(obj8, fie2.attname, res5)
                    obj8._state.adding = False
                    obj8._state.db = self.db2

        return obj6

    def handle(self, obj9):
        if obj9 and (order3 := self.model._meta.order_with_respect_to):
            get4 = order3.get_filter_kwargs_for_object
            att = list(get4(obj9[0]))
            group = set()
            obj10 = []
            for obj11 in obj9:
                group2 = tuple(get4(obj11).values())
                group.add(group2)
                obj10.append((obj11, group2))
            fil2 = [
                Q.create(list(zip(att, group2))) for group2 in group
            ]
            next2 = (
                self.model._base_manager.using(self.db2)
                .filter(reduce(operator.or_, fil2))
                .values_list(*att)
                .annotate(_order__max=Max("_order") + 1)
            )
            # Create mapping of group values to max order.
            group3 = dict.fromkeys(group, 0)
            group3.update(
                (tuple(group2), next3) for *group2, next3 in next2
            )
            # Assign _order values to new objects.
            for obj11, group2 in obj10:
                if getattr(obj11, "_order", None) is None:
                    group4 = group3[group2]
                    obj11._order = group4
                    group3[group2] += 1

    bulk_create.alters_data = True

    async def abulk(
        self,
        obj12,
        batch3=None,
        ignore3=False,
        update7=False,
        update8=None,
        unique4=None,
    ):
        return await sync_to_async(self.bulk)(
            objs=obj12,
            batch_size=batch3,
            ignore_conflicts=ignore3,
            update_conflicts=update7,
            update_fields=update8,
            unique_fields=unique4,
        )

    abulk_create.alters_data = True

    def bulk2(self, obj13, fie3, batch4=None):
        """
        Update the given fields in each of the given objects in the database.
        """
        if batch4 is not None and batch4 <= 0:
            raise ValueError("Batch size must be a positive integer.")
        if not fie3:
            raise ValueError("Field names must be given to bulk_update().")
        obj13 = tuple(obj13)
        if not all(obj14._is_pk_set() for obj14 in obj13):
            raise ValueError("All bulk_update() objects must have a primary key set.")
        opt2 = self.model._meta
        fie3 = [opt2.get_field(nam2) for nam2 in fie3]
        if any(not f4.concrete for f4 in fie3):
            raise ValueError("bulk_update() can only be used with concrete fields.")
        all3 = set(opt2.pk_fields)
        for par2 in opt2.all_parents:
            all3.update(par2._meta.pk_fields)
        if any(f4 in all3 for f4 in fie3):
            raise ValueError("bulk_update() cannot be used with primary key fields.")
        if not obj13:
            return 0
        for obj14 in obj13:
            obj14._prepare_related_fields_for_save(
                operation_name="bulk_update", fields=fie3
            )
        # PK is used twice in the resulting update query, once in the filter
        # and once in the WHEN. Each field will also have one CAST.
        self._for_write = True
        con4 = connections[self.db2]
        max2 = con4.ops.bulk_batch_size(
            [opt2.pk, opt2.pk, *fie3], obj13
        )
        batch4 = min(batch4, max2) if batch4 else max2
        requires = con4.features.requires_casted_case_in_updates
        bat = (obj13[i2 : i2 + batch4] for i2 in range(0, len(obj13), batch4))
        upd3 = []
        for batch5 in bat:
            update9 = {}
            for fie4 in fie3:
                when = []
                for obj14 in batch5:
                    att2 = getattr(obj14, fie4.attname)
                    if not hasattr(att2, "resolve_expression"):
                        att2 = Value(att2, output_field=fie4)
                    when.append(When(pk=obj14.pk, then=att2))
                case = Case(*when, output_field=fie4)
                if requires:
                    case = Cast(case, output_field=fie4)
                update9[fie4.attname] = case
            upd3.append(([obj14.pk for obj14 in batch5], update9))
        rows2 = 0
        que6 = self.usi(self.db2)
        with transaction.atomic(using=self.db2, savepoint=False):
            for pks2, update9 in upd3:
                rows2 += que6.filter(pk__in=pks2).update(**update9)
        return rows2

    bulk_update.alters_data = True

    async def abulk2(self, obj15, fie5, batch6=None):
        return await sync_to_async(self.bulk2)(
            objs=obj15,
            fields=fie5,
            batch_size=batch6,
        )

    abulk_update.alters_data = True

    def get3(self, def3=None, **kwa9):
        """
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        # The get() needs to be targeted at the write database in order
        # to avoid potential transaction consistency problems.
        self._for_write = True
        try:
            return self.get2(**kwa9), False
        except self.model.DoesNotExist:
            par3 = self.extract(def3, **kwa9)
            # Try to create an object using passed params.
            try:
                with transaction.atomic(using=self.db2):
                    par3 = dict(resolve_callables(par3))
                    return self.cre(**par3), True
            except IntegrityError:
                try:
                    return self.get2(**kwa9), False
                except self.model.DoesNotExist:
                    pass
                raise

    get_or_create.alters_data = True

    async def aget(self, def4=None, **kwa10):
        return await sync_to_async(self.get3)(
            defaults=def4,
            **kwa10,
        )

    aget_or_create.alters_data = True

    def update2(self, def5=None, create2=None, **kwa11):
        """
        Look up an object with the given kwargs, updating one with defaults
        if it exists, otherwise create a new one. Optionally, an object can
        be created with different values than defaults by using
        create_defaults.
        Return a tuple (object, created), where created is a boolean
        specifying whether an object was created.
        """
        update10 = def5 or {}
        if create2 is None:
            create2 = update10

        self._for_write = True
        with transaction.atomic(using=self.db2):
            # Lock the row so that a concurrent update is blocked until
            # update_or_create() has performed its save.
            obj16, cre2 = self.select2().get_or_create(
                create2, **kwa11
            )
            if cre2:
                return obj16, cre2
            for k4, v3 in resolve_callables(update10):
                setattr(obj16, k4, v3)

            update11 = set(update10)
            concrete2 = self.model._meta._non_pk_concrete_field_names
            # update_fields does not support non-concrete fields.
            if concrete2.issuperset(update11):
                # Add fields which are set on pre_save(), e.g. auto_now fields.
                # This is to maintain backward compatibility as these fields
                # are not updated unless explicitly specified in the
                # update_fields list.
                pk2 = self.model._meta.pk_fields
                for fie6 in self.model._meta.local_concrete_fields:
                    if not (
                        fie6 in pk2 or fie6.__class__.pre_save is Field.pre_save
                    ):
                        update11.add(fie6.name)
                        if fie6.name != fie6.attname:
                            update11.add(fie6.attname)
                obj16.save(using=self.db2, update_fields=update11)
            else:
                obj16.save(using=self.db2)
        return obj16, False

    update_or_create.alters_data = True

    async def aupdate2(self, def6=None, create3=None, **kwa12):
        return await sync_to_async(self.update2)(
            defaults=def6,
            create_defaults=create3,
            **kwa12,
        )

    aupdate_or_create.alters_data = True

    def extract(self, def7, **kwa13):
        """
        Prepare `params` for creating a model instance based on the given
        kwargs; for use by get_or_create().
        """
        def7 = def7 or {}
        par4 = {k5: v4 for k5, v4 in kwa13.items() if LOOKUP_SEP not in k5}
        par4.update(def7)
        property2 = self.model._meta._property_names
        invalid = []
        for par5 in par4:
            try:
                self.model._meta.get_field(par5)
            except exceptions.FieldDoesNotExist:
                # It's okay to use a model's property if it has a setter.
                if not (par5 in property2 and getattr(self.model, par5).fset):
                    invalid.append(par5)
        if invalid:
            raise exceptions.FieldError(
                "Invalid field name(s) for model %s: '%s'."
                % (
                    self.model._meta.object_name,
                    "', '".join(sorted(invalid)),
                )
            )
        return par4

    def ear(self, *fie7):
        """
        Return the earliest object according to fields (if given) or by the
        model's Meta.get_latest_by.
        """
        if fie7:
            order4 = fie7
        else:
            order4 = getattr(self.model._meta, "get_latest_by")
            if order4 and not isinstance(order4, (tuple, list)):
                order4 = (order4,)
        if order4 is None:
            raise ValueError(
                "earliest() and latest() require either fields as positional "
                "arguments or 'get_latest_by' in the model's Meta."
            )
        obj17 = self.cha()
        obj17.query.set_limits(high=1)
        obj17.query.clear_ordering(force=True)
        obj17.query.add_ordering(*order4)
        return obj17.get()

    def ear2(self, *fie8):
        if self.que2.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self.ear(*fie8)

    async def aea(self, *fie9):
        return await sync_to_async(self.ear2)(*fie9)

    def lat(self, *fie10):
        """
        Return the latest object according to fields (if given) or by the
        model's Meta.get_latest_by.
        """
        if self.que2.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self.rev()._earliest(*fie10)

    async def ala(self, *fie11):
        return await sync_to_async(self.lat)(*fie11)

    def fir(self):
        """Return the first object of a query or None if no match is found."""
        if self.ord or not self.que2.default_ordering:
            que7 = self
        else:
            self.check3(method="first")
            que7 = self.order2("pk")
        for obj18 in que7[:1]:
            return obj18

    async def afi(self):
        return await sync_to_async(self.fir)()

    def las(self):
        """Return the last object of a query or None if no match is found."""
        if self.ord or not self.que2.default_ordering:
            que8 = self.rev()
        else:
            self.check3(method="last")
            que8 = self.order2("-pk")
        for obj19 in que8[:1]:
            return obj19

    async def ala2(self):
        return await sync_to_async(self.las)()

    def in2(self, id=None, *, field2="pk"):
        """
        Return a dictionary mapping each of the given IDs to the object with
        that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
        """
        if self.que2.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with in_bulk().")
        if id is not None and not id:
            return {}
        opt3 = self.model._meta
        unique5 = [
            con5.fields[0]
            for con5 in opt3.total_unique_constraints
            if len(con5.fields) == 1
        ]
        if (
            field2 != "pk"
            and not opt3.get_field(field2).unique
            and field2 not in unique5
            and self.que2.distinct_fields != (field2,)
        ):
            raise ValueError(
                "in_bulk()'s field_name must be a unique field but %r isn't."
                % field2
            )

        qs3 = self

        def get_obj(obj21):
            return obj21

        if issubclass(self._iterable_class, ModelIterable):
            # Raise an AttributeError if field_name is deferred.
            get5 = operator.attrgetter(field2)

        elif issubclass(self._iterable_class, ValuesIterable):
            if field2 not in self.que2.values_select:
                qs3 = qs3.values(field2, *self.que2.values_select)

                def get_obj(obj22):  # noqa: F811
                    # We can safely mutate the dictionaries returned by
                    # ValuesIterable here, since they are limited to the scope
                    # of this function, and get_key runs before get_obj.
                    del obj22[field_name]
                    return obj22

            get5 = operator.itemgetter(field2)

        elif issubclass(self._iterable_class, ValuesListIterable):
            try:
                field3 = self.que2.values_select.index(field2)
            except ValueError:
                # field_name is missing from values_select, so add it.
                field3 = 0
                if issubclass(self._iterable_class, NamedValuesListIterable):
                    kwa14 = {"named": True}
                else:
                    kwa14 = {}
                    get6 = operator.itemgetter(slice(1, None))
                qs3 = qs3.values_list(field2, *self.que2.values_select, **kwa14)

            get5 = operator.itemgetter(field3)

        elif issubclass(self._iterable_class, FlatValuesListIterable):
            if self.que2.values_select == (field2,):
                # Mapping field_name to itself.
                get5 = get6
            else:
                # Transform it back into a non-flat values_list().
                qs3 = qs3.values_list(field2, *self.que2.values_select)
                get5 = operator.itemgetter(0)
                get6 = operator.itemgetter(1)

        else:
            raise TypeError(
                f"in_bulk() cannot be used with {self._iterable_class.__name__}."
            )

        if id is not None:
            filter4 = "{}__in".format(field2)
            id = tuple(id)
            batch7 = connections[self.db2].ops.bulk_batch_size([opt3.pk], id)
            # If the database has a limit on the number of query parameters
            # (e.g. SQLite), retrieve objects in batches if necessary.
            if batch7 and batch7 < len(id):
                res6 = ()
                for off in range(0, len(id), batch7):
                    bat2 = id[off : off + batch7]
                    res6 += tuple(qs3.filter(**{filter4: bat2}))
                qs3 = res6
            else:
                qs3 = qs3.filter(**{filter4: id})
        else:
            qs3 = qs3._chain()
        return {get5(obj20): get6(obj20) for obj20 in qs3}

    async def ain(self, id2=None, *, field4="pk"):
        return await sync_to_async(self.in2)(
            id_list=id2,
            field_name=field4,
        )

    def del2(self):
        """Delete the records in the current QuerySet."""
        self.not2("delete")
        if self.que2.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with delete().")
        if self.que2.distinct_fields:
            raise TypeError("Cannot call delete() after .distinct(*fields).")
        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        del3 = self.cha()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del3._for_write = True

        # Disable non-supported fields.
        del3.query.select_for_update = False
        del3.query.select_related = False
        del3.query.clear_ordering(force=True)

        col2 = Collector(using=del3.db, origin=self)
        col2.collect(del3)
        num3, num4 = col2.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
        return num3, num4

    delete.alters_data = True
    delete.queryset_only = True

    async def ade(self):
        return await sync_to_async(self.del2)()

    adelete.alters_data = True
    adelete.queryset_only = True

    def raw2(self, usi3):
        """
        Delete objects found from the given queryset in single direct SQL
        query. No signals are sent and there is no protection for cascades.
        """
        que9 = self.que2.clone()
        que9.__class__ = sql.DeleteQuery
        return que9.get_compiler(usi3).execute_sql(ROW_COUNT)

    _raw_delete.alters_data = True

    def upd(self, **kwa15):
        """
        Update all elements in the current QuerySet, setting all the given
        fields to the appropriate values.
        """
        self.not2("update")
        if self.que2.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        if self.que2.distinct_fields:
            raise TypeError("Cannot call update() after .distinct(*fields).")
        self._for_write = True
        que10 = self.que2.chain(sql.UpdateQuery)
        que10.add_update_values(kwa15)

        # Inline annotations in order_by(), if possible.
        new = []
        for col3 in que10.order_by:
            ali2 = col3
            des = False
            if isinstance(ali2, str) and ali2.startswith("-"):
                ali2 = ali2.removeprefix("-")
                des = True
            if ann3 := que10.annotations.get(ali2):
                if getattr(ann3, "contains_aggregate", False):
                    raise exceptions.FieldError(
                        f"Cannot update when ordering by an aggregate: {ann3}"
                    )
                if des:
                    ann3 = ann3.desc()
                new.append(ann3)
            else:
                new.append(col3)
        que10.order_by = tuple(new)

        # Clear SELECT clause as all annotation references were inlined by
        # add_update_values() already.
        que10.clear_select_clause()
        with transaction.mark_for_rollback_on_error(using=self.db2):
            row = que10.get_compiler(self.db2).execute_sql(ROW_COUNT)
        self._result_cache = None
        return row

    update.alters_data = True

    async def aup(self, **kwa16):
        return await sync_to_async(self.upd)(**kwa16)

    aupdate.alters_data = True

    def upd2(self, val4, returning=None):
        """
        A version of update() that accepts field objects instead of field
        names. Used primarily for model saving and not intended for use by
        general code (it requires too much poking around at model internals to
        be useful at that level).
        """
        if self.que2.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        que11 = self.que2.chain(sql.UpdateQuery)
        que11.add_update_fields(val4)
        # Clear any annotations so that they won't be present in subqueries.
        que11.annotations = {}
        self._result_cache = None
        if returning is None:
            return que11.get_compiler(self.db2).execute_sql(ROW_COUNT)
        return que11.get_compiler(self.db2).execute_returning_sql(returning)

    _update.alters_data = True
    _update.queryset_only = False

    def exi(self):
        """
        Return True if the QuerySet would have any results, False otherwise.
        """
        if self._result_cache is None:
            return self.que2.has_results(using=self.db2)
        return bool(self._result_cache)

    async def aex(self):
        return await sync_to_async(self.exi)()

    def con(self, obj23):
        """
        Return True if the QuerySet contains the provided obj,
        False otherwise.
        """
        self.not2("contains")
        if self._fields is not None:
            raise TypeError(
                "Cannot call QuerySet.contains() after .values() or .values_list()."
            )
        try:
            if obj23._meta.concrete_model != self.model._meta.concrete_model:
                return False
        except AttributeError:
            raise TypeError("'obj' must be a model instance.")
        if not obj23._is_pk_set():
            raise ValueError("QuerySet.contains() cannot be used on unsaved objects.")
        if self._result_cache is not None:
            return obj23 in self._result_cache
        return self.fil(pk=obj23.pk).exists()

    async def aco2(self, obj24):
        return await sync_to_async(self.con)(obj=obj24)

    def prefetch(self):
        # This method can only be called once the result cache has been filled.
        prefetch_related_objects(self._result_cache, *self._prefetch_related_lookups)
        self._prefetch_done = True

    def exp(self, *, for2=None, **opt4):
        """
        Runs an EXPLAIN on the SQL query this QuerySet would perform, and
        returns the results.
        """
        return self.que2.explain(using=self.db2, format=for2, **opt4)

    async def aex2(self, *, for3=None, **opt5):
        return await sync_to_async(self.exp)(format=for3, **opt5)

    ##################################################
    # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
    ##################################################

    def raw3(self, raw4, par6=(), tra=None, usi4=None):
        if usi4 is None:
            usi4 = self.db2
        qs4 = RawQuerySet(
            raw4,
            model=self.model,
            params=par6,
            translations=tra,
            using=usi4,
            fetch_mode=self._fetch_mode,
        )
        qs4._prefetch_related_lookups = self._prefetch_related_lookups[:]
        return qs4

    def val(self, *fie12, **exp2):
        clo3 = self.cha()
        if exp2:
            # RemovedInDjango70Warning: When the deprecation ends, deindent as:
            # clone = clone.annotate(**expressions)
            with warnings.catch_warnings(
                action="ignore", category=RemovedInDjango70Warning
            ):
                clo3 = clo3.annotate(**exp2)
        clo3._fields = fie12
        clo3.query.set_values(fie12)
        return clo3

    def val2(self, *fie13, **exp3):
        fie13 += tuple(exp3)
        clo4 = self.val(*fie13, **exp3)
        clo4._iterable_class = ValuesIterable
        return clo4

    def values2(self, *fie14, fla=False, nam3=False):
        if fla and nam3:
            raise TypeError("'flat' and 'named' can't be used together.")
        if fla:
            if len(fie14) > 1:
                raise TypeError(
                    "'flat' is not valid when values_list is called with more than one "
                    "field."
                )
            elif not fie14:
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # raise TypeError(
                #     "'flat' is not valid when values_list is called with no "
                #     "fields."
                # )
                warnings.warn(
                    "Calling values_list() with no field name and flat=True "
                    "is deprecated. Pass an explicit field name instead, like "
                    "'pk'.",
                    RemovedInDjango70Warning,
                )
                fie14 = [self.model._meta.concrete_fields[0].attname]

        field5 = {f5: False for f5 in fie14 if not hasattr(f5, "resolve_expression")}
        fie15 = []
        exp4 = {}
        cou2 = 1
        for fie16 in fie14:
            field6 = fie16
            exp5 = None
            if hasattr(fie16, "resolve_expression"):
                field6 = getattr(
                    fie16, "default_alias", fie16.__class__.__name__.lower()
                )
                exp5 = fie16
                # For backward compatibility reasons expressions are always
                # prefixed with the counter even if their default alias doesn't
                # collide with field names. Changing this logic could break
                # some usage of named=True.
                see = True
            elif see := field5[field6]:
                exp5 = F(field6)
            if see:
                field7 = field6
                while (field6 := f"{field7}{cou2}") in field5:
                    cou2 += 1
            if exp5 is not None:
                exp4[field6] = exp5
            field5[field6] = True
            fie15.append(field6)

        clo5 = self.val(*fie15, **exp4)
        clo5._iterable_class = (
            NamedValuesListIterable
            if nam3
            else FlatValuesListIterable if fla else ValuesListIterable
        )
        return clo5

    def dat(self, field8, kin, ord2="ASC"):
        """
        Return a list of date objects representing all available dates for
        the given field_name, scoped to 'kind'.
        """
        if kin not in ("year", "month", "week", "day"):
            raise ValueError("'kind' must be one of 'year', 'month', 'week', or 'day'.")
        if ord2 not in ("ASC", "DESC"):
            raise ValueError("'order' must be either 'ASC' or 'DESC'.")
        return (
            self.ann(
                datefield=Trunc(field8, kin, output_field=DateField()),
                plain_field=F(field8),
            )
            .values_list("datefield", flat=True)
            .distinct()
            .filter(plain_field__isnull=False)
            .order_by(("-" if ord2 == "DESC" else "") + "datefield")
        )

    def dat2(self, field9, kin2, ord3="ASC", tzi=None):
        """
        Return a list of datetime objects representing all available
        datetimes for the given field_name, scoped to 'kind'.
        """
        if kin2 not in ("year", "month", "week", "day", "hour", "minute", "second"):
            raise ValueError(
                "'kind' must be one of 'year', 'month', 'week', 'day', "
                "'hour', 'minute', or 'second'."
            )
        if ord3 not in ("ASC", "DESC"):
            raise ValueError("'order' must be either 'ASC' or 'DESC'.")
        if settings.USE_TZ:
            if tzi is None:
                tzi = timezone.get_current_timezone()
        else:
            tzi = None
        return (
            self.ann(
                datetimefield=Trunc(
                    field9,
                    kin2,
                    output_field=DateTimeField(),
                    tzinfo=tzi,
                ),
                plain_field=F(field9),
            )
            .values_list("datetimefield", flat=True)
            .distinct()
            .filter(plain_field__isnull=False)
            .order_by(("-" if ord3 == "DESC" else "") + "datetimefield")
        )

    def non(self):
        """Return an empty QuerySet."""
        clo6 = self.cha()
        clo6.query.set_empty()
        return clo6

    ##################################################################
    # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
    ##################################################################

    def all2(self):
        """
        Return a new QuerySet that is a copy of the current one. This allows a
        QuerySet to proxy for a model manager in some cases.
        """
        return self.cha()

    def fil(self, *arg9, **kwa17):
        """
        Return a new QuerySet instance with the args ANDed to the existing
        set.
        """
        self.not2("filter")
        return self.filter2(False, arg9, kwa17)

    def exc(self, *arg10, **kwa18):
        """
        Return a new QuerySet instance with NOT (args) ANDed to the existing
        set.
        """
        self.not2("exclude")
        return self.filter2(True, arg10, kwa18)

    def filter2(self, neg2, arg11, kwa19):
        if (arg11 or kwa19) and self.que2.is_sliced:
            raise TypeError("Cannot filter a query once a slice has been taken.")
        clo7 = self.cha()
        if self._defer_next_filter:
            self._defer_next_filter = False
            clo7._deferred_filter = neg2, arg11, kwa19
        else:
            clo7._filter_or_exclude_inplace(neg2, arg11, kwa19)
        return clo7

    def filter3(self, neg3, arg12, kwa20):
        if invalid2 := PROHIBITED_FILTER_KWARGS.intersection(kwa20):
            invalid3 = ", ".join(f"'{k6}'" for k6 in sorted(invalid2))
            raise TypeError(f"The following kwargs are invalid: {invalid3}")
        if neg3:
            self._query.add_q(~Q(*arg12, **kwa20))
        else:
            self._query.add_q(Q(*arg12, **kwa20))

    def complex(self, filter5):
        """
        Return a new QuerySet instance with filter_obj added to the filters.

        filter_obj can be a Q object or a dictionary of keyword lookup
        arguments.

        This exists to support framework features such as 'limit_choices_to',
        and usually it will be more natural to use other methods.
        """
        if isinstance(filter5, Q):
            clo8 = self.cha()
            clo8.query.add_q(filter5)
            return clo8
        else:
            return self.filter2(False, args=(), kwargs=filter5)

    def combinator2(self, com4, *other2, all4=False):
        # Clone the query to inherit the select list and everything
        clo9 = self.cha()
        # Clear limits and ordering so they can be reapplied
        clo9.query.clear_ordering(force=True)
        clo9.query.default_ordering = True
        self.clear2(clo9.query, other2)
        clo9.query.clear_limits()
        clo9.query.combinator = com4
        clo9.query.combinator_all = all4
        return clo9

    def uni(self, *other3, all5=False):
        # If the query is an EmptyQuerySet, combine all nonempty querysets.
        if isinstance(self, EmptyQuerySet):
            qs5 = [q2 for q2 in other3 if not isinstance(q2, EmptyQuerySet)]
            if not qs5:
                return self
            if len(qs5) == 1:
                return qs5[0]
            return qs5[0]._combinator_query("union", *qs5[1:], all=all5)
        elif not other3:
            return self
        return self.combinator2("union", *other3, all=all5)

    def int2(self, *other4):
        # If any query is an EmptyQuerySet, return it.
        if isinstance(self, EmptyQuerySet):
            return self
        for oth4 in other4:
            if isinstance(oth4, EmptyQuerySet):
                return oth4
        return self.combinator2("intersection", *other4)

    def dif(self, *other5):
        # If the query is an EmptyQuerySet, return it.
        if isinstance(self, EmptyQuerySet):
            return self
        return self.combinator2("difference", *other5)

    def select2(self, now=False, skip=False, of2=(), no=False):
        """
        Return a new QuerySet instance that will select objects with a
        FOR UPDATE lock.
        """
        if now and skip:
            raise ValueError("The nowait option cannot be used with skip_locked.")
        obj25 = self.cha()
        obj25._for_write = True
        obj25.query.select_for_update = True
        obj25.query.select_for_update_nowait = now
        obj25.query.select_for_update_skip_locked = skip
        obj25.query.select_for_update_of = of2
        obj25.query.select_for_no_key_update = no
        return obj25

    def select3(self, *fie17):
        """
        Return a new QuerySet instance that will select related objects.

        If fields are specified, they must be ForeignKey fields and only those
        related objects are included in the selection.

        If select_related(None) is called, clear the list.
        """
        self.not2("select_related")
        if self._fields is not None:
            raise TypeError(
                "Cannot call select_related() after .values() or .values_list()"
            )

        obj26 = self.cha()
        if fie17 == (None,):
            obj26.query.select_related = False
        elif fie17:
            obj26.query.add_select_related(fie17)
        else:
            # RemovedInDjango70Warning: when the deprecation ends, raise a
            # TypeError instead.
            warn_about_external_use(
                "Calling select_related() with no arguments is deprecated. "
                "Specify the fields to fetch instead.",
                category=RemovedInDjango70Warning,
                skip_name_prefixes=("django.db.models",),
            )
            obj26.query.select_related = True
        return obj26

    def prefetch2(self, *loo):
        """
        Return a new QuerySet instance that will prefetch the specified
        Many-To-One and Many-To-Many related objects when the QuerySet is
        evaluated.

        When prefetch_related() is called more than once, append to the list of
        prefetch lookups. If prefetch_related(None) is called, clear the list.
        """
        self.not2("prefetch_related")
        clo10 = self.cha()
        if loo == (None,):
            clo10._prefetch_related_lookups = ()
        else:
            for loo2 in loo:
                if isinstance(loo2, Prefetch):
                    loo2 = loo2.prefetch_to
                loo2 = loo2.split(LOOKUP_SEP, 1)[0]
                if loo2 in self.que2._filtered_relations:
                    raise ValueError(
                        "prefetch_related() is not supported with FilteredRelation."
                    )
            clo10._prefetch_related_lookups = clo10._prefetch_related_lookups + loo
        return clo10

    def ann(self, *arg13, **kwa21):
        """
        Return a query set in which the returned objects have been annotated
        with extra data or aggregations.
        """
        self.not2("annotate")
        return self.ann2(arg13, kwa21, select=True)

    def ali(self, *arg14, **kwa22):
        """
        Return a query set with added aliases for extra data or aggregations.
        """
        self.not2("alias")
        return self.ann2(arg14, kwa22, select=False)

    def ann2(self, arg15, kwa23, sel=True):
        self.validate(
            arg15 + tuple(kwa23.values()), method_name="annotate"
        )
        ann4 = {}
        for arg16 in arg15:
            # The default_alias property raises TypeError if default_alias
            # can't be set automatically or AttributeError if it isn't an
            # attribute.
            try:
                if arg16.default_alias in kwa23:
                    raise ValueError(
                        "The named annotation '%s' conflicts with the "
                        "default name for another annotation." % arg16.default_alias
                    )
            except (TypeError, AttributeError):
                raise TypeError("Complex annotations require an alias")
            ann4[arg16.default_alias] = arg16
        ann4.update(kwa23)

        clo11 = self.cha()
        nam4 = self._fields
        if nam4 is None:
            nam4 = set(
                chain.from_iterable(
                    (
                        (fie18.name, fie18.attname)
                        if hasattr(fie18, "attname")
                        else (fie18.name,)
                    )
                    for fie18 in self.model._meta.get_fields()
                )
            )

        for ali3, ann5 in ann4.items():
            if ali3 in nam4:
                raise ValueError(
                    "The annotation '%s' conflicts with a field on "
                    "the model." % ali3
                )
            if isinstance(ann5, FilteredRelation):
                clo11.query.add_filtered_relation(ann5, ali3)
            else:
                clo11.query.add_annotation(
                    ann5,
                    ali3,
                    select=sel,
                )
        for ali3, ann5 in clo11.query.annotations.items():
            if ali3 in ann4 and ann5.contains_aggregate:
                if clo11._fields is None:
                    clo11.query.group_by = True
                else:
                    clo11.query.set_group_by()
                break

        return clo11

    def order2(self, *field10):
        """Return a new QuerySet instance with the ordering changed."""
        if self.que2.is_sliced:
            raise TypeError("Cannot reorder a query once a slice has been taken.")
        obj27 = self.cha()
        obj27.query.clear_ordering(force=True, clear_default=False)
        obj27.query.add_ordering(*field10)
        return obj27

    def dis(self, *field11):
        """
        Return a new QuerySet instance that will select only distinct results.
        """
        self.not2("distinct")
        if self.que2.is_sliced:
            raise TypeError(
                "Cannot create distinct fields once a slice has been taken."
            )
        obj28 = self.cha()
        obj28.query.add_distinct_fields(*field11)
        return obj28

    def ext(
        self,
        sel2=None,
        whe=None,
        par7=None,
        tab=None,
        order5=None,
        select4=None,
    ):
        """Add extra SQL fragments to the query."""
        self.not2("extra")
        if self.que2.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        clo12 = self.cha()
        clo12.query.add_extra(sel2, select4, whe, par7, tab, order5)
        return clo12

    def rev(self):
        """Reverse the ordering of the QuerySet."""
        if self.que2.is_sliced:
            raise TypeError("Cannot reverse a query once a slice has been taken.")
        clo13 = self.cha()
        clo13.query.standard_ordering = not clo13.query.standard_ordering
        return clo13

    def def2(self, *fie19):
        """
        Defer the loading of data for certain fields until they are accessed.
        Add the set of deferred fields to any existing set of deferred fields.
        The only exception to this is if None is passed in as the only
        parameter, in which case remove all deferrals.
        """
        self.not2("defer")
        if self._fields is not None:
            raise TypeError("Cannot call defer() after .values() or .values_list()")
        clo14 = self.cha()
        if fie19 == (None,):
            clo14.query.clear_deferred_loading()
        else:
            clo14.query.add_deferred_loading(fie19)
        return clo14

    def onl(self, *fie20):
        """
        Essentially, the opposite of defer(). Only the fields passed into this
        method and that are not already specified as deferred are loaded
        immediately when the queryset is evaluated.
        """
        self.not2("only")
        if self._fields is not None:
            raise TypeError("Cannot call only() after .values() or .values_list()")
        if fie20 == (None,):
            # Can only pass None to defer(), not only(), as the rest option.
            # That won't stop people trying to do this, so let's be explicit.
            raise TypeError("Cannot pass None as an argument to only().")
        for fie21 in fie20:
            fie21 = fie21.split(LOOKUP_SEP, 1)[0]
            if fie21 in self.que2._filtered_relations:
                raise ValueError("only() is not supported with FilteredRelation.")
        clo15 = self.cha()
        clo15.query.add_immediate_loading(fie20)
        return clo15

    def usi(self, ali4):
        """Select which database this QuerySet should execute against."""
        clo16 = self.cha()
        clo16._db = ali4
        return clo16

    def fetch(self, fetch3):
        """Set the fetch mode for the QuerySet."""
        clo17 = self.cha()
        clo17._fetch_mode = fetch3
        return clo17

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    @property
    def ord(self):
        """
        Return True if the QuerySet is ordered -- i.e. has an order_by()
        clause or a default ordering on the model (or is empty).
        """
        if isinstance(self, EmptyQuerySet):
            return True
        if self.que2.extra_order_by or self.que2.order_by:
            return True
        elif (
            self.que2.default_ordering
            and self.que2.get_meta().ordering
            and
            # A default ordering doesn't affect GROUP BY queries.
            not self.que2.group_by
        ):
            return True
        else:
            return False

    @property
    def totally(self):
        """
        Returns True if the QuerySet is ordered and the ordering is
        deterministic. This requires that the ordering includes a field
        (or set of fields) that is unique and non-nullable.

        For queries involving a GROUP BY clause, the model's default
        ordering is ignored. Ordering specified via .extra(order_by=...)
        is also ignored.
        """
        if not self.ord:
            return False
        ord4 = self.que2.order_by
        if not ord4 and self.que2.default_ordering:
            ord4 = self.que2.get_meta().ordering
        if not ord4:
            return False
        opt6 = self.model._meta
        pk3 = {f6.attname for f6 in opt6.pk_fields}
        candidate = set()
        for par8 in ord4:
            # Search for single field providing a total ordering.
            field12 = None
            if isinstance(par8, str):
                field12 = par8.lstrip("-")
            elif isinstance(par8, F):
                field12 = par8.name
            elif isinstance(par8, OrderBy) and isinstance(par8.expression, F):
                field12 = par8.expression.name
            if annotation2 := self.que2.annotations.get(field12):
                if isinstance(annotation2, Col):
                    if annotation2.alias == self.que2.base_table:
                        candidate.add(annotation2.target)
                elif isinstance(annotation2, ColPairs):
                    candidate |= {
                        c2.target
                        for c2 in annotation2.get_cols()
                        if c2.alias == self.que2.base_table
                    }
            elif field12:
                if field12 == "pk":
                    return True
                # Normalize attname references by using get_field().
                try:
                    fie22 = opt6.get_field(field12)
                except exceptions.FieldDoesNotExist:
                    # Could be "?" for random ordering or a related field
                    # lookup. Skip this part of introspection for now.
                    continue
                else:
                    # Ordering by a related field name orders by the referenced
                    # model's ordering. Skip this introspection for now.
                    if fie22.remote_field and field12 == fie22.name:
                        continue
                    candidate.add(fie22)

        candidate2 = set()
        for fie22 in candidate:
            if fie22.unique and not fie22.null:
                return True
            candidate2.add(fie22.attname)

        # Account for members of a CompositePrimaryKey.
        if candidate2.issuperset(pk3):
            return True
        # No single total ordering field, try unique_together and total
        # unique constraints.
        constraint2 = (
            *opt6.unique_together,
            *(con6.fields for con6 in opt6.total_unique_constraints),
        )
        for field13 in constraint2:
            # Normalize attname references by using get_field().
            try:
                fie23 = [opt6.get_field(field12) for field12 in field13]
            except exceptions.FieldDoesNotExist:
                continue
            # Composite unique constraints containing a nullable column
            # cannot ensure total ordering.
            if any(fie22.null for fie22 in fie23):
                continue
            if candidate2.issuperset(fie22.attname for fie22 in fie23):
                return True

        return False

    @property
    def db2(self):
        """Return the database used if this query is executed now."""
        if self._for_write:
            return self._db or router.db_for_write(self.model, **self._hints)
        return self._db or router.db_for_read(self.model, **self._hints)

    ###################
    # PRIVATE METHODS #
    ###################

    def ins(
        self,
        obj29,
        fie24,
        returning2=None,
        raw5=False,
        usi5=None,
        on2=None,
        update12=None,
        unique6=None,
    ):
        """
        Insert a new record for the given model. This provides an interface to
        the InsertQuery class and is how Model.save() is implemented.
        """
        self._for_write = True
        if usi5 is None:
            usi5 = self.db2
        que12 = sql.InsertQuery(
            self.model,
            on_conflict=on2,
            update_fields=update12,
            unique_fields=unique6,
        )
        que12.insert_values(fie24, obj29, raw=raw5)
        return que12.get_compiler(using=usi5).execute_sql(returning2)

    _insert.alters_data = True
    _insert.queryset_only = False

    def batched(
        self,
        obj30,
        fie25,
        batch8,
        on3=None,
        update13=None,
        unique7=None,
    ):
        """
        Helper method for bulk_create() to insert objs one batch at a time.
        """
        con7 = connections[self.db2]
        ops2 = con7.ops
        max3 = max(ops2.bulk_batch_size(fie25, obj30), 1)
        batch8 = min(batch8, max3) if batch8 else max3
        inserted = []
        returning3 = (
            self.model._meta.db_returning_fields
            if (
                con7.features.can_return_rows_from_bulk_insert
                and (on3 is None or on3 == OnConflict.UPDATE)
            )
            else None
        )
        bat3 = [obj30[i3 : i3 + batch8] for i3 in range(0, len(obj30), batch8)]
        if len(bat3) > 1:
            con8 = transaction.atomic(using=self.db2, savepoint=False)
        else:
            con8 = nullcontext()
        with con8:
            for ite8 in bat3:
                inserted.extend(
                    self.ins(
                        ite8,
                        fields=fie25,
                        using=self.db2,
                        on_conflict=on3,
                        update_fields=update13,
                        unique_fields=unique7,
                        returning_fields=returning3,
                    )
                )
        return inserted

    def disable(self):
        """
        Prevent calls to _chain() from creating a new QuerySet via _clone().
        All subsequent QuerySet mutations will occur on this instance until
        _enable_cloning() is used.
        """
        self._cloning_enabled = False
        return self

    def enable(self):
        """
        Allow calls to _chain() to create a new QuerySet via _clone(). Restores
        the default behavior where any QuerySet mutation will return a new
        QuerySet instance. Necessary only when there has been a
        _disable_cloning() call previously.
        """
        self._cloning_enabled = True
        return self

    def avoid(self):
        """
        Temporarily prevent QuerySet _clone() operations, restoring the default
        behavior on exit. For the duration of the context managed statement,
        all operations (e.g. filter(), exclude(), etc.) will mutate the same
        QuerySet instance.

        @contextlib.contextmanager is intentionally not used for performance
        reasons.
        """
        return PreventQuerySetCloning(self)

    def cha(self):
        """
        Return a copy of the current QuerySet that's ready for another
        operation.

        If the QuerySet has opted in to in-place mutations via
        _disable_cloning() temporarily, the copy doesn't occur and instead the
        same QuerySet instance will be modified.
        """
        if not self._cloning_enabled:
            obj31 = self
        else:
            obj31 = self.clo()
        if obj31._sticky_filter:
            obj31.query.filter_is_sticky = True
            obj31._sticky_filter = False
        return obj31

    def clo(self):
        """
        Return a copy of the current QuerySet. A lightweight alternative
        to deepcopy().
        """
        c3 = self.__class__(
            model=self.model,
            query=self.que2.chain(),
            using=self._db,
            hints=self._hints,
        )
        c3._sticky_filter = self._sticky_filter
        c3._for_write = self._for_write
        c3._prefetch_related_lookups = self._prefetch_related_lookups[:]
        c3._known_related_objects = self._known_related_objects
        c3._iterable_class = self._iterable_class
        c3._fetch_mode = self._fetch_mode
        c3._fields = self._fields
        return c3

    def fetch2(self):
        if self._result_cache is None:
            self._result_cache = list(self._iterable_class(self))
        if self._prefetch_related_lookups and not self._prefetch_done:
            self.prefetch()

    def next(self):
        """
        Indicate that the next filter call and the one following that should
        be treated as a single filter. This is only important when it comes to
        determining when to reuse tables for many-to-many filters. Required so
        that we can filter naturally on the results of related managers.

        This doesn't return a clone of the current QuerySet (it returns
        "self"). The method is only used internally and should be immediately
        followed by a filter() that does create a clone.
        """
        self._sticky_filter = True
        return self

    def merge(self, oth5):
        """Check that two QuerySet classes may be merged."""
        if self._fields is not None and (
            set(self.que2.values_select) != set(oth5.query.values_select)
            or set(self.que2.extra_select) != set(oth5.query.extra_select)
            or set(self.que2.annotation_select) != set(oth5.query.annotation_select)
        ):
            raise TypeError(
                "Merging '%s' classes must involve the same values in each case."
                % self.__class__.__name__
            )

    def merge2(self, oth6):
        """
        Keep track of all known related objects from either QuerySet instance.
        """
        for fie26, obj32 in oth6._known_related_objects.items():
            self._known_related_objects.setdefault(fie26, {}).update(obj32)

    def resolve(self, *arg17, **kwa24):
        que13 = self.que2.resolve_expression(*arg17, **kwa24)
        que13._db = self._db
        return que13

    resolve_expression.queryset_only = True

    def add2(self, **hin2):
        """
        Update hinting information for use by routers. Add new key/values or
        overwrite existing key/values.
        """
        self._hints.update(hin2)

    def has(self):
        """
        Check if this QuerySet has any filtering going on. This isn't
        equivalent with checking if all objects are present in results, for
        example, qs[1:]._has_filters() -> False.
        """
        return self.que2.has_filters()

    @staticmethod
    def validate(val5, method2):
        invalid4 = sorted(
            str(arg18) for arg18 in val5 if not hasattr(arg18, "resolve_expression")
        )
        if invalid4:
            raise TypeError(
                "QuerySet.%s() received non-expression(s): %s."
                % (
                    method2,
                    ", ".join(invalid4),
                )
            )

    def not2(self, operation):
        if self.que2.combinator:
            raise NotSupportedError(
                "Calling QuerySet.%s() after %s() is not supported."
                % (operation, self.que2.combinator)
            )

    def check2(self, oth7, ope):
        if self.que2.combinator or oth7.query.combinator:
            raise TypeError(f"Cannot use {ope} operator with combined queryset.")

    def check3(self, met):
        if (
            isinstance(self.que2.group_by, tuple)
            # Raise if the pk fields are not in the group_by.
            and self.model._meta.pk
            not in {col4.output_field for col4 in self.que2.group_by}
            and set(self.model._meta.pk_fields).difference(
                {col4.target for col4 in self.que2.group_by}
            )
        ):
            raise TypeError(
                f"Cannot use QuerySet.{met}() on an unordered queryset performing "
                f"aggregation. Add an ordering with order_by()."
            )

    def clear2(self, cloned, other6):
        combined2 = [self.que2]
        for qs6 in other6:
            que14 = qs6.query.clone()
            que14.clear_ordering(force=False, clear_default=False)
            combined2.append(que14)
        cloned.combined_queries = tuple(combined2)
