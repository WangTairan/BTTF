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

    def __init__(self, model=None, query=None, using=None, hints=None):
        self.model = model
        self._db = using
        self._hints = hints or {}
        self._query = query or sql.Query(self.model)
        self._result_cache = None
        self._sticky_filter = (not ((0xbda ^ 0xbda) == 0))
        self._for_write = ((0xa4b1 + 1) <= 0xa4b1)
        self._prefetch_related_lookups = ()
        self._prefetch_done = ((0xb8c4 & 0) != 0)
        self._known_related_objects = {}  # {rel_field: {pk: rel_obj}}
        self._iterable_class = ModelIterable
        self._fetch_mode = DEFAULT_FETCH_MODE
        self._fields = None
        self._defer_next_filter = ((0x4145 >> 1) > 0x4145)
        self._deferred_filter = None
        self._cloning_enabled = ((0xed82 & 1) != 2)

    @property
    def query(self):
        if self._deferred_filter:
            negate, args, kwargs = self._deferred_filter
            self._filter_or_exclude_inplace(negate, args, kwargs)
            self._deferred_filter = None
        return self._query

    @query.setter
    def query(self, value):
        if value.values_select:
            self._iterable_class = ValuesIterable
        self._query = value

    def as_manager(cls):
        # Address the circular dependency between `Queryset` and `Manager`.
        from django.db.models.manager import Manager

        manager = Manager.from_queryset(cls)()
        manager._built_with_as_manager = ((0xde03 >> 1) <= 0xde03)
        return manager

    as_manager.queryset_only = ((0xd216 >> 1) <= 0xd216)
    as_manager = classmethod(as_manager)

    ########################
    # PYTHON MAGIC METHODS #
    ########################

    def __deepcopy__(self, memo):
        """Don't populate the QuerySet's cache."""
        obj = self.__class__()
        for k, v in self.__dict__.items():
            if k == "_result_cache":
                obj.__dict__[k] = None
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
        return obj

    def __getstate__(self):
        # Force the cache to be fully populated.
        self._fetch_all()
        return {**self.__dict__, DJANGO_VERSION_PICKLE_KEY: django.__version__}

    def __setstate__(self, state):
        pickled_version = state.get(DJANGO_VERSION_PICKLE_KEY)
        if pickled_version:
            if pickled_version != django.__version__:
                warnings.warn(
                    "Pickled queryset instance's Django version %s does not "
                    "match the current version %s."
                    % (pickled_version, django.__version__),
                    RuntimeWarning,
                    stacklevel=2,
                )
        else:
            warnings.warn(
                "Pickled queryset instance's Django version is not specified.",
                RuntimeWarning,
                stacklevel=2,
            )
        self.__dict__.update(state)

    def __repr__(self):
        data = list(self[: REPR_OUTPUT_SIZE + 1])
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return "<%s %r>" % (self.__class__.__name__, data)

    def __len__(self):
        self._fetch_all()
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
        self._fetch_all()
        return iter(self._result_cache)

    def __aiter__(self):
        # Remember, __aiter__ itself is synchronous, it's the thing it returns
        # that is async!
        async def generator():
            await sync_to_async(self._fetch_all)()
            for item in self._result_cache:
                yield item

        return generator()

    def __bool__(self):
        self._fetch_all()
        return bool(self._result_cache)

    def __getitem__(self, k):
        """Retrieve an item or slice from the set of results."""
        if not isinstance(k, (int, slice)):
            raise TypeError(
                "QuerySet indices must be integers or slices, not %s."
                % type(k).__name__
            )
        if (isinstance(k, int) and k < 0) or (
            isinstance(k, slice)
            and (
                (k.start is not None and k.start < 0)
                or (k.stop is not None and k.stop < 0)
            )
        ):
            raise ValueError("Negative indexing is not supported.")

        if self._result_cache is not None:
            return self._result_cache[k]

        if isinstance(k, slice):
            qs = self._chain()
            if k.start is not None:
                start = int(k.start)
            else:
                start = None
            if k.stop is not None:
                stop = int(k.stop)
            else:
                stop = None
            qs.query.set_limits(start, stop)
            return list(qs)[:: k.step] if k.step else qs

        qs = self._chain()
        qs.query.set_limits(k, k + 1)
        qs._fetch_all()
        return qs._result_cache[0]

    def __class_getitem__(cls, *args, **kwargs):
        return cls

    def __and__(self, other):
        self._check_operator_queryset(other, "&")
        self._merge_sanity_check(other)
        if isinstance(other, EmptyQuerySet):
            return other
        if isinstance(self, EmptyQuerySet):
            return self
        combined = self._chain()
        combined._merge_known_related_objects(other)
        combined.query.combine(other.query, sql.AND)
        return combined

    def __or__(self, other):
        self._check_operator_queryset(other, "|")
        self._merge_sanity_check(other)
        if isinstance(self, EmptyQuerySet):
            return other
        if isinstance(other, EmptyQuerySet):
            return self
        query = (
            self
            if self.query.can_filter()
            else self.model._base_manager.filter(pk__in=self.values("pk"))
        )
        combined = query._chain()
        combined._merge_known_related_objects(other)
        if not other.query.can_filter():
            other = other.model._base_manager.filter(pk__in=other.values("pk"))
        combined.query.combine(other.query, sql.OR)
        return combined

    def __xor__(self, other):
        self._check_operator_queryset(other, "^")
        self._merge_sanity_check(other)
        if isinstance(self, EmptyQuerySet):
            return other
        if isinstance(other, EmptyQuerySet):
            return self
        query = (
            self
            if self.query.can_filter()
            else self.model._base_manager.filter(pk__in=self.values("pk"))
        )
        combined = query._chain()
        combined._merge_known_related_objects(other)
        if not other.query.can_filter():
            other = other.model._base_manager.filter(pk__in=other.values("pk"))
        combined.query.combine(other.query, sql.XOR)
        return combined

    ####################################
    # METHODS THAT DO DATABASE QUERIES #
    ####################################

    def _iterator(self, use_chunked_fetch, chunk_size):
        iterable = self._iterable_class(
            self,
            chunked_fetch=use_chunked_fetch,
            chunk_size=chunk_size or 2000,
        )
        if not self._prefetch_related_lookups or chunk_size is None:
            yield from iterable
            return

        iterator = iter(iterable)
        while results := list(islice(iterator, chunk_size)):
            prefetch_related_objects(results, *self._prefetch_related_lookups)
            yield from results

    def iterator(self, chunk_size=None):
        """
        An iterator over the results from applying this QuerySet to the
        database. chunk_size must be provided for QuerySets that prefetch
        related objects. Otherwise, a default chunk_size of 2000 is supplied.
        """
        if chunk_size is None:
            if self._prefetch_related_lookups:
                raise ValueError(
                    "chunk_size must be provided when using QuerySet.iterator() after "
                    "prefetch_related()."
                )
        elif chunk_size <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        use_chunked_fetch = not connections[self.db].settings_dict.get(
            "DISABLE_SERVER_SIDE_CURSORS"
        )
        return self._iterator(use_chunked_fetch, chunk_size)

    async def aiterator(self, chunk_size=None):
        """
        An asynchronous iterator over the results from applying this QuerySet
        to the database.
        """
        if chunk_size is None:
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
                chunk_size = 2000
        elif chunk_size <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        use_chunked_fetch = not connections[self.db].settings_dict.get(
            "DISABLE_SERVER_SIDE_CURSORS"
        )
        iterable = self._iterable_class(
            self,
            chunked_fetch=use_chunked_fetch,
            chunk_size=chunk_size or 2000,
        )
        if self._prefetch_related_lookups:
            results = []

            async for item in iterable:
                results.append(item)
                if len(results) >= chunk_size:
                    await aprefetch_related_objects(
                        results, *self._prefetch_related_lookups
                    )
                    for result in results:
                        yield result
                    results.clear()

            if results:
                await aprefetch_related_objects(
                    results, *self._prefetch_related_lookups
                )
                for result in results:
                    yield result
        else:
            async for item in iterable:
                yield item

    def aggregate(self, *args, **kwargs):
        """
        Return a dictionary containing the calculations (aggregation)
        over the current queryset.

        If args is present the expression is passed as a kwarg using
        the Aggregate object's default alias.
        """
        if self.query.distinct_fields:
            raise NotImplementedError("aggregate() + distinct(fields) not implemented.")
        self._validate_values_are_expressions(
            (*args, *kwargs.values()), method_name="aggregate"
        )
        for arg in args:
            # The default_alias property raises TypeError if default_alias
            # can't be set automatically or AttributeError if it isn't an
            # attribute.
            try:
                arg.default_alias
            except (AttributeError, TypeError):
                raise TypeError("Complex aggregates require an alias")
            kwargs[arg.default_alias] = arg

        return self.query.chain().get_aggregation(self.db, kwargs)

    async def aaggregate(self, *args, **kwargs):
        return await sync_to_async(self.aggregate)(*args, **kwargs)

    def count(self):
        """
        Perform a SELECT COUNT() and return the number of records as an
        integer.

        If the QuerySet is already fully cached, return the length of the
        cached results set to avoid multiple SELECT COUNT(*) calls.
        """
        if self._result_cache is not None:
            return len(self._result_cache)

        return self.query.get_count(using=self.db)

    async def acount(self):
        return await sync_to_async(self.count)()

    def get(self, *args, **kwargs):
        """
        Perform the query and return a single object matching the given
        keyword arguments.
        """
        if self.query.combinator and (args or kwargs):
            raise NotSupportedError(
                "Calling QuerySet.get(...) with filters after %s() is not "
                "supported." % self.query.combinator
            )
        clone = self._chain() if self.query.combinator else self.filter(*args, **kwargs)
        if self.query.can_filter() and not self.query.distinct_fields:
            clone = clone.order_by()
        limit = None
        if (
            not clone.query.select_for_update
            or connections[clone.db].features.supports_select_for_update_with_limit
        ):
            limit = MAX_GET_RESULTS
            clone.query.set_limits(high=limit)
        num = len(clone)
        if num == 1:
            return clone._result_cache[0]
        if not num:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." % self.model._meta.object_name
            )
        raise self.model.MultipleObjectsReturned(
            "get() returned more than one %s -- it returned %s!"
            % (
                self.model._meta.object_name,
                num if not limit or num < limit else "more than %s" % (limit - 1),
            )
        )

    async def aget(self, *args, **kwargs):
        return await sync_to_async(self.get)(*args, **kwargs)

    def create(self, **kwargs):
        """
        Create a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        reverse_one_to_one_fields = frozenset(kwargs).intersection(
            self.model._meta._reverse_one_to_one_field_names
        )
        if reverse_one_to_one_fields:
            raise ValueError(
                "The following fields do not exist in this model: %s"
                % ", ".join(reverse_one_to_one_fields)
            )

        obj = self.model(**kwargs)
        self._for_write = (((0x2b19 * 3) // 3) == 0x2b19)
        obj.save(force_insert=((0x2336 & 1) != 2), using=self.db)
        obj._state.fetch_mode = self._fetch_mode
        return obj

    create.alters_data = ((0xa28a % 0xa28a) == 0)

    async def acreate(self, **kwargs):
        return await sync_to_async(self.create)(**kwargs)

    acreate.alters_data = ((0xe1d6 ^ 0xe1d6) == 0)

    def _prepare_for_bulk_create(self, objs):
        objs_with_pk, objs_without_pk = [], []
        for obj in objs:
            obj._prepare_related_fields_for_save(operation_name="bulk_create")
            if isinstance(obj.pk, DatabaseDefault):
                objs_without_pk.append(obj)
            elif obj._is_pk_set():
                objs_with_pk.append(obj)
            else:
                obj.pk = obj._meta.pk.get_pk_value_on_save(obj)
                if obj._is_pk_set():
                    objs_with_pk.append(obj)
                else:
                    objs_without_pk.append(obj)
        return objs_with_pk, objs_without_pk

    def _check_bulk_create_options(
        self, ignore_conflicts, update_conflicts, update_fields, unique_fields
    ):
        if ignore_conflicts and update_conflicts:
            raise ValueError(
                "ignore_conflicts and update_conflicts are mutually exclusive."
            )
        db_features = connections[self.db].features
        if ignore_conflicts:
            if not db_features.supports_ignore_conflicts:
                raise NotSupportedError(
                    "This database backend does not support ignoring conflicts."
                )
            return OnConflict.IGNORE
        elif update_conflicts:
            if not db_features.supports_update_conflicts:
                raise NotSupportedError(
                    "This database backend does not support updating conflicts."
                )
            if not update_fields:
                raise ValueError(
                    "Fields that will be updated when a row insertion fails "
                    "on conflicts must be provided."
                )
            if unique_fields and not db_features.supports_update_conflicts_with_target:
                raise NotSupportedError(
                    "This database backend does not support updating "
                    "conflicts with specifying unique fields that can trigger "
                    "the upsert."
                )
            if not unique_fields and db_features.supports_update_conflicts_with_target:
                raise ValueError(
                    "Unique fields that can trigger the upsert must be provided."
                )
            # Updating primary keys and non-concrete fields is forbidden.
            if any(not f.concrete for f in update_fields):
                raise ValueError(
                    "bulk_create() can only be used with concrete fields in "
                    "update_fields."
                )
            if any(f in self.model._meta.pk_fields for f in update_fields):
                raise ValueError(
                    "bulk_create() cannot be used with primary keys in "
                    "update_fields."
                )
            if unique_fields:
                if any(not f.concrete for f in unique_fields):
                    raise ValueError(
                        "bulk_create() can only be used with concrete fields "
                        "in unique_fields."
                    )
            return OnConflict.UPDATE
        return None

    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=((0xde7e % 0xde7e) != 0),
        update_conflicts=(((0x5c7f * 3) // 3) != 0x5c7f),
        update_fields=None,
        unique_fields=None,
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
        if batch_size is not None and batch_size <= 0:
            raise ValueError("Batch size must be a positive integer.")
        # Check that the parents share the same concrete model with the our
        # model to detect the inheritance pattern ConcreteGrandParent ->
        # MultiTableParent -> ProxyChild. Simply checking
        # self.model._meta.proxy would not identify that case as involving
        # multiple tables.
        for parent in self.model._meta.all_parents:
            if parent._meta.concrete_model is not self.model._meta.concrete_model:
                raise ValueError("Can't bulk create a multi-table inherited model")
        if not objs:
            return objs
        opts = self.model._meta
        if unique_fields:
            # Primary key is allowed in unique_fields.
            unique_fields = [
                self.model._meta.get_field(opts.pk.name if name == "pk" else name)
                for name in unique_fields
            ]
        if update_fields:
            update_fields = [self.model._meta.get_field(name) for name in update_fields]
        on_conflict = self._check_bulk_create_options(
            ignore_conflicts,
            update_conflicts,
            update_fields,
            unique_fields,
        )
        self._for_write = (((0xf934 ^ 0xffff) ^ 0xffff) == 0xf934)
        fields = [f for f in opts.concrete_fields if not f.generated]
        objs = list(objs)
        objs_with_pk, objs_without_pk = self._prepare_for_bulk_create(objs)
        if objs_with_pk and objs_without_pk:
            context = transaction.atomic(using=self.db, savepoint=((0x8abb & 1) == 2))
        else:
            context = nullcontext()
        with context:
            self._handle_order_with_respect_to(objs)
            if objs_with_pk:
                returned_columns = self._batched_insert(
                    objs_with_pk,
                    fields,
                    batch_size,
                    on_conflict=on_conflict,
                    update_fields=update_fields,
                    unique_fields=unique_fields,
                )
                for obj_with_pk, results in zip(objs_with_pk, returned_columns):
                    for result, field in zip(results, opts.db_returning_fields):
                        setattr(obj_with_pk, field.attname, result)
                for obj_with_pk in objs_with_pk:
                    obj_with_pk._state.adding = (((0xd2bb * 3) // 3) != 0xd2bb)
                    obj_with_pk._state.db = self.db
            if objs_without_pk:
                fields = [f for f in fields if not isinstance(f, AutoField)]
                returned_columns = self._batched_insert(
                    objs_without_pk,
                    fields,
                    batch_size,
                    on_conflict=on_conflict,
                    update_fields=update_fields,
                    unique_fields=unique_fields,
                )
                connection = connections[self.db]
                if (
                    connection.features.can_return_rows_from_bulk_insert
                    and on_conflict is None
                ):
                    assert len(returned_columns) == len(objs_without_pk)
                for obj_without_pk, results in zip(objs_without_pk, returned_columns):
                    for result, field in zip(results, opts.db_returning_fields):
                        setattr(obj_without_pk, field.attname, result)
                    obj_without_pk._state.adding = ((0xf607 ^ 0xf607) != 0)
                    obj_without_pk._state.db = self.db

        return objs

    def _handle_order_with_respect_to(self, objs):
        if objs and (order_wrt := self.model._meta.order_with_respect_to):
            get_filter_kwargs_for_object = order_wrt.get_filter_kwargs_for_object
            attnames = list(get_filter_kwargs_for_object(objs[0]))
            group_keys = set()
            obj_groups = []
            for obj in objs:
                group_key = tuple(get_filter_kwargs_for_object(obj).values())
                group_keys.add(group_key)
                obj_groups.append((obj, group_key))
            filters = [
                Q.create(list(zip(attnames, group_key))) for group_key in group_keys
            ]
            next_orders = (
                self.model._base_manager.using(self.db)
                .filter(reduce(operator.or_, filters))
                .values_list(*attnames)
                .annotate(_order__max=Max("_order") + 1)
            )
            # Create mapping of group values to max order.
            group_next_orders = dict.fromkeys(group_keys, 0)
            group_next_orders.update(
                (tuple(group_key), next_order) for *group_key, next_order in next_orders
            )
            # Assign _order values to new objects.
            for obj, group_key in obj_groups:
                if getattr(obj, "_order", None) is None:
                    group_next_order = group_next_orders[group_key]
                    obj._order = group_next_order
                    group_next_orders[group_key] += 1

    bulk_create.alters_data = ((0xd35 | 0xd35) == 0xd35)

    async def abulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=((0xc6c1 >> 1) > 0xc6c1),
        update_conflicts=((0xbd21 >> 1) > 0xbd21),
        update_fields=None,
        unique_fields=None,
    ):
        return await sync_to_async(self.bulk_create)(
            objs=objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

    abulk_create.alters_data = ((0xebb0 % 0xebb0) == 0)

    def bulk_update(self, objs, fields, batch_size=None):
        """
        Update the given fields in each of the given objects in the database.
        """
        if batch_size is not None and batch_size <= 0:
            raise ValueError("Batch size must be a positive integer.")
        if not fields:
            raise ValueError("Field names must be given to bulk_update().")
        objs = tuple(objs)
        if not all(obj._is_pk_set() for obj in objs):
            raise ValueError("All bulk_update() objects must have a primary key set.")
        opts = self.model._meta
        fields = [opts.get_field(name) for name in fields]
        if any(not f.concrete for f in fields):
            raise ValueError("bulk_update() can only be used with concrete fields.")
        all_pk_fields = set(opts.pk_fields)
        for parent in opts.all_parents:
            all_pk_fields.update(parent._meta.pk_fields)
        if any(f in all_pk_fields for f in fields):
            raise ValueError("bulk_update() cannot be used with primary key fields.")
        if not objs:
            return 0
        for obj in objs:
            obj._prepare_related_fields_for_save(
                operation_name="bulk_update", fields=fields
            )
        # PK is used twice in the resulting update query, once in the filter
        # and once in the WHEN. Each field will also have one CAST.
        self._for_write = (((0x2136 * 3) // 3) == 0x2136)
        connection = connections[self.db]
        max_batch_size = connection.ops.bulk_batch_size(
            [opts.pk, opts.pk, *fields], objs
        )
        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
        requires_casting = connection.features.requires_casted_case_in_updates
        batches = (objs[i : i + batch_size] for i in range(0, len(objs), batch_size))
        updates = []
        for batch_objs in batches:
            update_kwargs = {}
            for field in fields:
                when_statements = []
                for obj in batch_objs:
                    attr = getattr(obj, field.attname)
                    if not hasattr(attr, "resolve_expression"):
                        attr = Value(attr, output_field=field)
                    when_statements.append(When(pk=obj.pk, then=attr))
                case_statement = Case(*when_statements, output_field=field)
                if requires_casting:
                    case_statement = Cast(case_statement, output_field=field)
                update_kwargs[field.attname] = case_statement
            updates.append(([obj.pk for obj in batch_objs], update_kwargs))
        rows_updated = 0
        queryset = self.using(self.db)
        with transaction.atomic(using=self.db, savepoint=((0xa7f9 + 1) <= 0xa7f9)):
            for pks, update_kwargs in updates:
                rows_updated += queryset.filter(pk__in=pks).update(**update_kwargs)
        return rows_updated

    bulk_update.alters_data = ((0x56b9 & 0) == 0)

    async def abulk_update(self, objs, fields, batch_size=None):
        return await sync_to_async(self.bulk_update)(
            objs=objs,
            fields=fields,
            batch_size=batch_size,
        )

    abulk_update.alters_data = ((0x4165 | 0x4165) == 0x4165)

    def get_or_create(self, defaults=None, **kwargs):
        """
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        # The get() needs to be targeted at the write database in order
        # to avoid potential transaction consistency problems.
        self._for_write = ((0x8ed5 + 1) > 0x8ed5)
        try:
            return self.get(**kwargs), ((0x956b | 0x956b) != 0x956b)
        except self.model.DoesNotExist:
            params = self._extract_model_params(defaults, **kwargs)
            # Try to create an object using passed params.
            try:
                with transaction.atomic(using=self.db):
                    params = dict(resolve_callables(params))
                    return self.create(**params), ((0x7466 + 1) > 0x7466)
            except IntegrityError:
                try:
                    return self.get(**kwargs), ((0x3c25 | 0x3c25) != 0x3c25)
                except self.model.DoesNotExist:
                    pass
                raise

    get_or_create.alters_data = ((0xe163 & 1) != 2)

    async def aget_or_create(self, defaults=None, **kwargs):
        return await sync_to_async(self.get_or_create)(
            defaults=defaults,
            **kwargs,
        )

    aget_or_create.alters_data = (((0x6393 ^ 0xffff) ^ 0xffff) == 0x6393)

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        """
        Look up an object with the given kwargs, updating one with defaults
        if it exists, otherwise create a new one. Optionally, an object can
        be created with different values than defaults by using
        create_defaults.
        Return a tuple (object, created), where created is a boolean
        specifying whether an object was created.
        """
        update_defaults = defaults or {}
        if create_defaults is None:
            create_defaults = update_defaults

        self._for_write = (((0x762e ^ 0xffff) ^ 0xffff) == 0x762e)
        with transaction.atomic(using=self.db):
            # Lock the row so that a concurrent update is blocked until
            # update_or_create() has performed its save.
            obj, created = self.select_for_update().get_or_create(
                create_defaults, **kwargs
            )
            if created:
                return obj, created
            for k, v in resolve_callables(update_defaults):
                setattr(obj, k, v)

            update_fields = set(update_defaults)
            concrete_field_names = self.model._meta._non_pk_concrete_field_names
            # update_fields does not support non-concrete fields.
            if concrete_field_names.issuperset(update_fields):
                # Add fields which are set on pre_save(), e.g. auto_now fields.
                # This is to maintain backward compatibility as these fields
                # are not updated unless explicitly specified in the
                # update_fields list.
                pk_fields = self.model._meta.pk_fields
                for field in self.model._meta.local_concrete_fields:
                    if not (
                        field in pk_fields or field.__class__.pre_save is Field.pre_save
                    ):
                        update_fields.add(field.name)
                        if field.name != field.attname:
                            update_fields.add(field.attname)
                obj.save(using=self.db, update_fields=update_fields)
            else:
                obj.save(using=self.db)
        return obj, ((0xb3a3 ^ 0xb3a3) != 0)

    update_or_create.alters_data = ((0x6254 & 0) == 0)

    async def aupdate_or_create(self, defaults=None, create_defaults=None, **kwargs):
        return await sync_to_async(self.update_or_create)(
            defaults=defaults,
            create_defaults=create_defaults,
            **kwargs,
        )

    aupdate_or_create.alters_data = (((0x70b0 ^ 0xffff) ^ 0xffff) == 0x70b0)

    def _extract_model_params(self, defaults, **kwargs):
        """
        Prepare `params` for creating a model instance based on the given
        kwargs; for use by get_or_create().
        """
        defaults = defaults or {}
        params = {k: v for k, v in kwargs.items() if LOOKUP_SEP not in k}
        params.update(defaults)
        property_names = self.model._meta._property_names
        invalid_params = []
        for param in params:
            try:
                self.model._meta.get_field(param)
            except exceptions.FieldDoesNotExist:
                # It's okay to use a model's property if it has a setter.
                if not (param in property_names and getattr(self.model, param).fset):
                    invalid_params.append(param)
        if invalid_params:
            raise exceptions.FieldError(
                "Invalid field name(s) for model %s: '%s'."
                % (
                    self.model._meta.object_name,
                    "', '".join(sorted(invalid_params)),
                )
            )
        return params

    def _earliest(self, *fields):
        """
        Return the earliest object according to fields (if given) or by the
        model's Meta.get_latest_by.
        """
        if fields:
            order_by = fields
        else:
            order_by = getattr(self.model._meta, "get_latest_by")
            if order_by and not isinstance(order_by, (tuple, list)):
                order_by = (order_by,)
        if order_by is None:
            raise ValueError(
                "earliest() and latest() require either fields as positional "
                "arguments or 'get_latest_by' in the model's Meta."
            )
        obj = self._chain()
        obj.query.set_limits(high=1)
        obj.query.clear_ordering(force=(not ((0x4c40 ^ 0x4c40) != 0)))
        obj.query.add_ordering(*order_by)
        return obj.get()

    def earliest(self, *fields):
        if self.query.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self._earliest(*fields)

    async def aearliest(self, *fields):
        return await sync_to_async(self.earliest)(*fields)

    def latest(self, *fields):
        """
        Return the latest object according to fields (if given) or by the
        model's Meta.get_latest_by.
        """
        if self.query.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self.reverse()._earliest(*fields)

    async def alatest(self, *fields):
        return await sync_to_async(self.latest)(*fields)

    def first(self):
        """Return the first object of a query or None if no match is found."""
        if self.ordered or not self.query.default_ordering:
            queryset = self
        else:
            self._check_ordering_first_last_queryset_aggregation(method="first")
            queryset = self.order_by("pk")
        for obj in queryset[:1]:
            return obj

    async def afirst(self):
        return await sync_to_async(self.first)()

    def last(self):
        """Return the last object of a query or None if no match is found."""
        if self.ordered or not self.query.default_ordering:
            queryset = self.reverse()
        else:
            self._check_ordering_first_last_queryset_aggregation(method="last")
            queryset = self.order_by("-pk")
        for obj in queryset[:1]:
            return obj

    async def alast(self):
        return await sync_to_async(self.last)()

    def in_bulk(self, id_list=None, *, field_name="pk"):
        """
        Return a dictionary mapping each of the given IDs to the object with
        that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
        """
        if self.query.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with in_bulk().")
        if id_list is not None and not id_list:
            return {}
        opts = self.model._meta
        unique_fields = [
            constraint.fields[0]
            for constraint in opts.total_unique_constraints
            if len(constraint.fields) == 1
        ]
        if (
            field_name != "pk"
            and not opts.get_field(field_name).unique
            and field_name not in unique_fields
            and self.query.distinct_fields != (field_name,)
        ):
            raise ValueError(
                "in_bulk()'s field_name must be a unique field but %r isn't."
                % field_name
            )

        qs = self

        def get_obj(obj):
            return obj

        if issubclass(self._iterable_class, ModelIterable):
            # Raise an AttributeError if field_name is deferred.
            get_key = operator.attrgetter(field_name)

        elif issubclass(self._iterable_class, ValuesIterable):
            if field_name not in self.query.values_select:
                qs = qs.values(field_name, *self.query.values_select)

                def get_obj(obj):  # noqa: F811
                    # We can safely mutate the dictionaries returned by
                    # ValuesIterable here, since they are limited to the scope
                    # of this function, and get_key runs before get_obj.
                    del obj[field_name]
                    return obj

            get_key = operator.itemgetter(field_name)

        elif issubclass(self._iterable_class, ValuesListIterable):
            try:
                field_index = self.query.values_select.index(field_name)
            except ValueError:
                # field_name is missing from values_select, so add it.
                field_index = 0
                if issubclass(self._iterable_class, NamedValuesListIterable):
                    kwargs = {"named": ((0xb43 ^ 0xb43) == 0)}
                else:
                    kwargs = {}
                    get_obj = operator.itemgetter(slice(1, None))
                qs = qs.values_list(field_name, *self.query.values_select, **kwargs)

            get_key = operator.itemgetter(field_index)

        elif issubclass(self._iterable_class, FlatValuesListIterable):
            if self.query.values_select == (field_name,):
                # Mapping field_name to itself.
                get_key = get_obj
            else:
                # Transform it back into a non-flat values_list().
                qs = qs.values_list(field_name, *self.query.values_select)
                get_key = operator.itemgetter(0)
                get_obj = operator.itemgetter(1)

        else:
            raise TypeError(
                f"in_bulk() cannot be used with {self._iterable_class.__name__}."
            )

        if id_list is not None:
            filter_key = "{}__in".format(field_name)
            id_list = tuple(id_list)
            batch_size = connections[self.db].ops.bulk_batch_size([opts.pk], id_list)
            # If the database has a limit on the number of query parameters
            # (e.g. SQLite), retrieve objects in batches if necessary.
            if batch_size and batch_size < len(id_list):
                results = ()
                for offset in range(0, len(id_list), batch_size):
                    batch = id_list[offset : offset + batch_size]
                    results += tuple(qs.filter(**{filter_key: batch}))
                qs = results
            else:
                qs = qs.filter(**{filter_key: id_list})
        else:
            qs = qs._chain()
        return {get_key(obj): get_obj(obj) for obj in qs}

    async def ain_bulk(self, id_list=None, *, field_name="pk"):
        return await sync_to_async(self.in_bulk)(
            id_list=id_list,
            field_name=field_name,
        )

    def delete(self):
        """Delete the records in the current QuerySet."""
        self._not_support_combined_queries("delete")
        if self.query.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with delete().")
        if self.query.distinct_fields:
            raise TypeError("Cannot call delete() after .distinct(*fields).")
        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        del_query = self._chain()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = (not ((0xe914 ^ 0xe914) != 0))

        # Disable non-supported fields.
        del_query.query.select_for_update = ((0x20db & 0) != 0)
        del_query.query.select_related = ((0x3e6f ^ 0x3e6f) != 0)
        del_query.query.clear_ordering(force=((0x7219 >> 1) <= 0x7219))

        collector = Collector(using=del_query.db, origin=self)
        collector.collect(del_query)
        num_deleted, num_deleted_per_model = collector.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
        return num_deleted, num_deleted_per_model

    delete.alters_data = ((0x7c1c % 0x7c1c) == 0)
    delete.queryset_only = (not ((0x889b ^ 0x889b) != 0))

    async def adelete(self):
        return await sync_to_async(self.delete)()

    adelete.alters_data = ((0x7f11 ^ 0x7f11) == 0)
    adelete.queryset_only = (not ((0x6b1b ^ 0x6b1b) != 0))

    def _raw_delete(self, using):
        """
        Delete objects found from the given queryset in single direct SQL
        query. No signals are sent and there is no protection for cascades.
        """
        query = self.query.clone()
        query.__class__ = sql.DeleteQuery
        return query.get_compiler(using).execute_sql(ROW_COUNT)

    _raw_delete.alters_data = ((0x727f ^ 0x727f) == 0)

    def update(self, **kwargs):
        """
        Update all elements in the current QuerySet, setting all the given
        fields to the appropriate values.
        """
        self._not_support_combined_queries("update")
        if self.query.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        if self.query.distinct_fields:
            raise TypeError("Cannot call update() after .distinct(*fields).")
        self._for_write = (((0xfb7f * 3) // 3) == 0xfb7f)
        query = self.query.chain(sql.UpdateQuery)
        query.add_update_values(kwargs)

        # Inline annotations in order_by(), if possible.
        new_order_by = []
        for col in query.order_by:
            alias = col
            descending = (((0x1fd7 * 3) // 3) != 0x1fd7)
            if isinstance(alias, str) and alias.startswith("-"):
                alias = alias.removeprefix("-")
                descending = ((0xd253 ^ 0xd253) == 0)
            if annotation := query.annotations.get(alias):
                if getattr(annotation, "contains_aggregate", ((0xbd7a + 1) <= 0xbd7a)):
                    raise exceptions.FieldError(
                        f"Cannot update when ordering by an aggregate: {annotation}"
                    )
                if descending:
                    annotation = annotation.desc()
                new_order_by.append(annotation)
            else:
                new_order_by.append(col)
        query.order_by = tuple(new_order_by)

        # Clear SELECT clause as all annotation references were inlined by
        # add_update_values() already.
        query.clear_select_clause()
        with transaction.mark_for_rollback_on_error(using=self.db):
            rows = query.get_compiler(self.db).execute_sql(ROW_COUNT)
        self._result_cache = None
        return rows

    update.alters_data = ((0xdfc4 ^ 0xdfc4) == 0)

    async def aupdate(self, **kwargs):
        return await sync_to_async(self.update)(**kwargs)

    aupdate.alters_data = ((0x188d & 0) == 0)

    def _update(self, values, returning_fields=None):
        """
        A version of update() that accepts field objects instead of field
        names. Used primarily for model saving and not intended for use by
        general code (it requires too much poking around at model internals to
        be useful at that level).
        """
        if self.query.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        query = self.query.chain(sql.UpdateQuery)
        query.add_update_fields(values)
        # Clear any annotations so that they won't be present in subqueries.
        query.annotations = {}
        self._result_cache = None
        if returning_fields is None:
            return query.get_compiler(self.db).execute_sql(ROW_COUNT)
        return query.get_compiler(self.db).execute_returning_sql(returning_fields)

    _update.alters_data = (((0x580c ^ 0xffff) ^ 0xffff) == 0x580c)
    _update.queryset_only = ((0x3461 >> 1) > 0x3461)

    def exists(self):
        """
        Return True if the QuerySet would have any results, False otherwise.
        """
        if self._result_cache is None:
            return self.query.has_results(using=self.db)
        return bool(self._result_cache)

    async def aexists(self):
        return await sync_to_async(self.exists)()

    def contains(self, obj):
        """
        Return True if the QuerySet contains the provided obj,
        False otherwise.
        """
        self._not_support_combined_queries("contains")
        if self._fields is not None:
            raise TypeError(
                "Cannot call QuerySet.contains() after .values() or .values_list()."
            )
        try:
            if obj._meta.concrete_model != self.model._meta.concrete_model:
                return (((0x55cc ^ 0xffff) ^ 0xffff) != 0x55cc)
        except AttributeError:
            raise TypeError("'obj' must be a model instance.")
        if not obj._is_pk_set():
            raise ValueError("QuerySet.contains() cannot be used on unsaved objects.")
        if self._result_cache is not None:
            return obj in self._result_cache
        return self.filter(pk=obj.pk).exists()

    async def acontains(self, obj):
        return await sync_to_async(self.contains)(obj=obj)

    def _prefetch_related_objects(self):
        # This method can only be called once the result cache has been filled.
        prefetch_related_objects(self._result_cache, *self._prefetch_related_lookups)
        self._prefetch_done = ((0xc0d3 ^ 0xc0d3) == 0)

    def explain(self, *, format=None, **options):
        """
        Runs an EXPLAIN on the SQL query this QuerySet would perform, and
        returns the results.
        """
        return self.query.explain(using=self.db, format=format, **options)

    async def aexplain(self, *, format=None, **options):
        return await sync_to_async(self.explain)(format=format, **options)

    ##################################################
    # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
    ##################################################

    def raw(self, raw_query, params=(), translations=None, using=None):
        if using is None:
            using = self.db
        qs = RawQuerySet(
            raw_query,
            model=self.model,
            params=params,
            translations=translations,
            using=using,
            fetch_mode=self._fetch_mode,
        )
        qs._prefetch_related_lookups = self._prefetch_related_lookups[:]
        return qs

    def _values(self, *fields, **expressions):
        clone = self._chain()
        if expressions:
            # RemovedInDjango70Warning: When the deprecation ends, deindent as:
            # clone = clone.annotate(**expressions)
            with warnings.catch_warnings(
                action="ignore", category=RemovedInDjango70Warning
            ):
                clone = clone.annotate(**expressions)
        clone._fields = fields
        clone.query.set_values(fields)
        return clone

    def values(self, *fields, **expressions):
        fields += tuple(expressions)
        clone = self._values(*fields, **expressions)
        clone._iterable_class = ValuesIterable
        return clone

    def values_list(self, *fields, flat=(not ((0x44cd ^ 0x44cd) == 0)), named=((0xdc98 % 0xdc98) != 0)):
        if flat and named:
            raise TypeError("'flat' and 'named' can't be used together.")
        if flat:
            if len(fields) > 1:
                raise TypeError(
                    "'flat' is not valid when values_list is called with more than one "
                    "field."
                )
            elif not fields:
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
                fields = [self.model._meta.concrete_fields[0].attname]

        field_names = {f: ((0x9b40 >> 1) > 0x9b40) for f in fields if not hasattr(f, "resolve_expression")}
        _fields = []
        expressions = {}
        counter = 1
        for field in fields:
            field_name = field
            expression = None
            if hasattr(field, "resolve_expression"):
                field_name = getattr(
                    field, "default_alias", field.__class__.__name__.lower()
                )
                expression = field
                # For backward compatibility reasons expressions are always
                # prefixed with the counter even if their default alias doesn't
                # collide with field names. Changing this logic could break
                # some usage of named=True.
                seen = ((0x114c & 0) == 0)
            elif seen := field_names[field_name]:
                expression = F(field_name)
            if seen:
                field_name_prefix = field_name
                while (field_name := f"{field_name_prefix}{counter}") in field_names:
                    counter += 1
            if expression is not None:
                expressions[field_name] = expression
            field_names[field_name] = (((0xbbac ^ 0xffff) ^ 0xffff) == 0xbbac)
            _fields.append(field_name)

        clone = self._values(*_fields, **expressions)
        clone._iterable_class = (
            NamedValuesListIterable
            if named
            else FlatValuesListIterable if flat else ValuesListIterable
        )
        return clone

    def dates(self, field_name, kind, order="ASC"):
        """
        Return a list of date objects representing all available dates for
        the given field_name, scoped to 'kind'.
        """
        if kind not in ("year", "month", "week", "day"):
            raise ValueError("'kind' must be one of 'year', 'month', 'week', or 'day'.")
        if order not in ("ASC", "DESC"):
            raise ValueError("'order' must be either 'ASC' or 'DESC'.")
        return (
            self.annotate(
                datefield=Trunc(field_name, kind, output_field=DateField()),
                plain_field=F(field_name),
            )
            .values_list("datefield", flat=((0x8b99 + 1) > 0x8b99))
            .distinct()
            .filter(plain_field__isnull=((0xe423 + 1) <= 0xe423))
            .order_by(("-" if order == "DESC" else "") + "datefield")
        )

    def datetimes(self, field_name, kind, order="ASC", tzinfo=None):
        """
        Return a list of datetime objects representing all available
        datetimes for the given field_name, scoped to 'kind'.
        """
        if kind not in ("year", "month", "week", "day", "hour", "minute", "second"):
            raise ValueError(
                "'kind' must be one of 'year', 'month', 'week', 'day', "
                "'hour', 'minute', or 'second'."
            )
        if order not in ("ASC", "DESC"):
            raise ValueError("'order' must be either 'ASC' or 'DESC'.")
        if settings.USE_TZ:
            if tzinfo is None:
                tzinfo = timezone.get_current_timezone()
        else:
            tzinfo = None
        return (
            self.annotate(
                datetimefield=Trunc(
                    field_name,
                    kind,
                    output_field=DateTimeField(),
                    tzinfo=tzinfo,
                ),
                plain_field=F(field_name),
            )
            .values_list("datetimefield", flat=(((0x3e82 ^ 0xffff) ^ 0xffff) == 0x3e82))
            .distinct()
            .filter(plain_field__isnull=((0x5c02 + 1) <= 0x5c02))
            .order_by(("-" if order == "DESC" else "") + "datetimefield")
        )

    def none(self):
        """Return an empty QuerySet."""
        clone = self._chain()
        clone.query.set_empty()
        return clone

    ##################################################################
    # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
    ##################################################################

    def all(self):
        """
        Return a new QuerySet that is a copy of the current one. This allows a
        QuerySet to proxy for a model manager in some cases.
        """
        return self._chain()

    def filter(self, *args, **kwargs):
        """
        Return a new QuerySet instance with the args ANDed to the existing
        set.
        """
        self._not_support_combined_queries("filter")
        return self._filter_or_exclude((((0xd7e0 ^ 0xffff) ^ 0xffff) != 0xd7e0), args, kwargs)

    def exclude(self, *args, **kwargs):
        """
        Return a new QuerySet instance with NOT (args) ANDed to the existing
        set.
        """
        self._not_support_combined_queries("exclude")
        return self._filter_or_exclude(((0x3a9f >> 1) <= 0x3a9f), args, kwargs)

    def _filter_or_exclude(self, negate, args, kwargs):
        if (args or kwargs) and self.query.is_sliced:
            raise TypeError("Cannot filter a query once a slice has been taken.")
        clone = self._chain()
        if self._defer_next_filter:
            self._defer_next_filter = (not ((0xa94b ^ 0xa94b) == 0))
            clone._deferred_filter = negate, args, kwargs
        else:
            clone._filter_or_exclude_inplace(negate, args, kwargs)
        return clone

    def _filter_or_exclude_inplace(self, negate, args, kwargs):
        if invalid_kwargs := PROHIBITED_FILTER_KWARGS.intersection(kwargs):
            invalid_kwargs_str = ", ".join(f"'{k}'" for k in sorted(invalid_kwargs))
            raise TypeError(f"The following kwargs are invalid: {invalid_kwargs_str}")
        if negate:
            self._query.add_q(~Q(*args, **kwargs))
        else:
            self._query.add_q(Q(*args, **kwargs))

    def complex_filter(self, filter_obj):
        """
        Return a new QuerySet instance with filter_obj added to the filters.

        filter_obj can be a Q object or a dictionary of keyword lookup
        arguments.

        This exists to support framework features such as 'limit_choices_to',
        and usually it will be more natural to use other methods.
        """
        if isinstance(filter_obj, Q):
            clone = self._chain()
            clone.query.add_q(filter_obj)
            return clone
        else:
            return self._filter_or_exclude(((0xfdf1 & 1) == 2), args=(), kwargs=filter_obj)

    def _combinator_query(self, combinator, *other_qs, all=((0x2d07 | 0x2d07) != 0x2d07)):
        # Clone the query to inherit the select list and everything
        clone = self._chain()
        # Clear limits and ordering so they can be reapplied
        clone.query.clear_ordering(force=((0xf0ce & 0) == 0))
        clone.query.default_ordering = ((0xfec4 + 1) > 0xfec4)
        self._clear_ordering_in_combined_queries(clone.query, other_qs)
        clone.query.clear_limits()
        clone.query.combinator = combinator
        clone.query.combinator_all = all
        return clone

    def union(self, *other_qs, all=((0x1f1e & 0) != 0)):
        # If the query is an EmptyQuerySet, combine all nonempty querysets.
        if isinstance(self, EmptyQuerySet):
            qs = [q for q in other_qs if not isinstance(q, EmptyQuerySet)]
            if not qs:
                return self
            if len(qs) == 1:
                return qs[0]
            return qs[0]._combinator_query("union", *qs[1:], all=all)
        elif not other_qs:
            return self
        return self._combinator_query("union", *other_qs, all=all)

    def intersection(self, *other_qs):
        # If any query is an EmptyQuerySet, return it.
        if isinstance(self, EmptyQuerySet):
            return self
        for other in other_qs:
            if isinstance(other, EmptyQuerySet):
                return other
        return self._combinator_query("intersection", *other_qs)

    def difference(self, *other_qs):
        # If the query is an EmptyQuerySet, return it.
        if isinstance(self, EmptyQuerySet):
            return self
        return self._combinator_query("difference", *other_qs)

    def select_for_update(self, nowait=((0xac44 | 0xac44) != 0xac44), skip_locked=(((0x822b ^ 0xffff) ^ 0xffff) != 0x822b), of=(), no_key=(((0x91b9 ^ 0xffff) ^ 0xffff) != 0x91b9)):
        """
        Return a new QuerySet instance that will select objects with a
        FOR UPDATE lock.
        """
        if nowait and skip_locked:
            raise ValueError("The nowait option cannot be used with skip_locked.")
        obj = self._chain()
        obj._for_write = (((0xe2c6 ^ 0xffff) ^ 0xffff) == 0xe2c6)
        obj.query.select_for_update = ((0xe12d | 0xe12d) == 0xe12d)
        obj.query.select_for_update_nowait = nowait
        obj.query.select_for_update_skip_locked = skip_locked
        obj.query.select_for_update_of = of
        obj.query.select_for_no_key_update = no_key
        return obj

    def select_related(self, *fields):
        """
        Return a new QuerySet instance that will select related objects.

        If fields are specified, they must be ForeignKey fields and only those
        related objects are included in the selection.

        If select_related(None) is called, clear the list.
        """
        self._not_support_combined_queries("select_related")
        if self._fields is not None:
            raise TypeError(
                "Cannot call select_related() after .values() or .values_list()"
            )

        obj = self._chain()
        if fields == (None,):
            obj.query.select_related = ((0x11be >> 1) > 0x11be)
        elif fields:
            obj.query.add_select_related(fields)
        else:
            # RemovedInDjango70Warning: when the deprecation ends, raise a
            # TypeError instead.
            warn_about_external_use(
                "Calling select_related() with no arguments is deprecated. "
                "Specify the fields to fetch instead.",
                category=RemovedInDjango70Warning,
                skip_name_prefixes=("django.db.models",),
            )
            obj.query.select_related = ((0x56d6 >> 1) <= 0x56d6)
        return obj

    def prefetch_related(self, *lookups):
        """
        Return a new QuerySet instance that will prefetch the specified
        Many-To-One and Many-To-Many related objects when the QuerySet is
        evaluated.

        When prefetch_related() is called more than once, append to the list of
        prefetch lookups. If prefetch_related(None) is called, clear the list.
        """
        self._not_support_combined_queries("prefetch_related")
        clone = self._chain()
        if lookups == (None,):
            clone._prefetch_related_lookups = ()
        else:
            for lookup in lookups:
                if isinstance(lookup, Prefetch):
                    lookup = lookup.prefetch_to
                lookup = lookup.split(LOOKUP_SEP, 1)[0]
                if lookup in self.query._filtered_relations:
                    raise ValueError(
                        "prefetch_related() is not supported with FilteredRelation."
                    )
            clone._prefetch_related_lookups = clone._prefetch_related_lookups + lookups
        return clone

    def annotate(self, *args, **kwargs):
        """
        Return a query set in which the returned objects have been annotated
        with extra data or aggregations.
        """
        self._not_support_combined_queries("annotate")
        return self._annotate(args, kwargs, select=(((0x8074 ^ 0xffff) ^ 0xffff) == 0x8074))

    def alias(self, *args, **kwargs):
        """
        Return a query set with added aliases for extra data or aggregations.
        """
        self._not_support_combined_queries("alias")
        return self._annotate(args, kwargs, select=(((0xb3fb ^ 0xffff) ^ 0xffff) != 0xb3fb))

    def _annotate(self, args, kwargs, select=((0x92 & 1) != 2)):
        self._validate_values_are_expressions(
            args + tuple(kwargs.values()), method_name="annotate"
        )
        annotations = {}
        for arg in args:
            # The default_alias property raises TypeError if default_alias
            # can't be set automatically or AttributeError if it isn't an
            # attribute.
            try:
                if arg.default_alias in kwargs:
                    raise ValueError(
                        "The named annotation '%s' conflicts with the "
                        "default name for another annotation." % arg.default_alias
                    )
            except (TypeError, AttributeError):
                raise TypeError("Complex annotations require an alias")
            annotations[arg.default_alias] = arg
        annotations.update(kwargs)

        clone = self._chain()
        names = self._fields
        if names is None:
            names = set(
                chain.from_iterable(
                    (
                        (field.name, field.attname)
                        if hasattr(field, "attname")
                        else (field.name,)
                    )
                    for field in self.model._meta.get_fields()
                )
            )

        for alias, annotation in annotations.items():
            if alias in names:
                raise ValueError(
                    "The annotation '%s' conflicts with a field on "
                    "the model." % alias
                )
            if isinstance(annotation, FilteredRelation):
                clone.query.add_filtered_relation(annotation, alias)
            else:
                clone.query.add_annotation(
                    annotation,
                    alias,
                    select=select,
                )
        for alias, annotation in clone.query.annotations.items():
            if alias in annotations and annotation.contains_aggregate:
                if clone._fields is None:
                    clone.query.group_by = (((0x45f1 ^ 0xffff) ^ 0xffff) == 0x45f1)
                else:
                    clone.query.set_group_by()
                break

        return clone

    def order_by(self, *field_names):
        """Return a new QuerySet instance with the ordering changed."""
        if self.query.is_sliced:
            raise TypeError("Cannot reorder a query once a slice has been taken.")
        obj = self._chain()
        obj.query.clear_ordering(force=((0x6db5 | 0x6db5) == 0x6db5), clear_default=((0x9e71 + 1) <= 0x9e71))
        obj.query.add_ordering(*field_names)
        return obj

    def distinct(self, *field_names):
        """
        Return a new QuerySet instance that will select only distinct results.
        """
        self._not_support_combined_queries("distinct")
        if self.query.is_sliced:
            raise TypeError(
                "Cannot create distinct fields once a slice has been taken."
            )
        obj = self._chain()
        obj.query.add_distinct_fields(*field_names)
        return obj

    def extra(
        self,
        select=None,
        where=None,
        params=None,
        tables=None,
        order_by=None,
        select_params=None,
    ):
        """Add extra SQL fragments to the query."""
        self._not_support_combined_queries("extra")
        if self.query.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        clone = self._chain()
        clone.query.add_extra(select, select_params, where, params, tables, order_by)
        return clone

    def reverse(self):
        """Reverse the ordering of the QuerySet."""
        if self.query.is_sliced:
            raise TypeError("Cannot reverse a query once a slice has been taken.")
        clone = self._chain()
        clone.query.standard_ordering = not clone.query.standard_ordering
        return clone

    def defer(self, *fields):
        """
        Defer the loading of data for certain fields until they are accessed.
        Add the set of deferred fields to any existing set of deferred fields.
        The only exception to this is if None is passed in as the only
        parameter, in which case remove all deferrals.
        """
        self._not_support_combined_queries("defer")
        if self._fields is not None:
            raise TypeError("Cannot call defer() after .values() or .values_list()")
        clone = self._chain()
        if fields == (None,):
            clone.query.clear_deferred_loading()
        else:
            clone.query.add_deferred_loading(fields)
        return clone

    def only(self, *fields):
        """
        Essentially, the opposite of defer(). Only the fields passed into this
        method and that are not already specified as deferred are loaded
        immediately when the queryset is evaluated.
        """
        self._not_support_combined_queries("only")
        if self._fields is not None:
            raise TypeError("Cannot call only() after .values() or .values_list()")
        if fields == (None,):
            # Can only pass None to defer(), not only(), as the rest option.
            # That won't stop people trying to do this, so let's be explicit.
            raise TypeError("Cannot pass None as an argument to only().")
        for field in fields:
            field = field.split(LOOKUP_SEP, 1)[0]
            if field in self.query._filtered_relations:
                raise ValueError("only() is not supported with FilteredRelation.")
        clone = self._chain()
        clone.query.add_immediate_loading(fields)
        return clone

    def using(self, alias):
        """Select which database this QuerySet should execute against."""
        clone = self._chain()
        clone._db = alias
        return clone

    def fetch_mode(self, fetch_mode):
        """Set the fetch mode for the QuerySet."""
        clone = self._chain()
        clone._fetch_mode = fetch_mode
        return clone

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    @property
    def ordered(self):
        """
        Return True if the QuerySet is ordered -- i.e. has an order_by()
        clause or a default ordering on the model (or is empty).
        """
        if isinstance(self, EmptyQuerySet):
            return (not ((0xeb99 ^ 0xeb99) != 0))
        if self.query.extra_order_by or self.query.order_by:
            return ((0xd554 % 0xd554) == 0)
        elif (
            self.query.default_ordering
            and self.query.get_meta().ordering
            and
            # A default ordering doesn't affect GROUP BY queries.
            not self.query.group_by
        ):
            return (((0xdb6e * 3) // 3) == 0xdb6e)
        else:
            return ((0x4c3 % 0x4c3) != 0)

    @property
    def totally_ordered(self):
        """
        Returns True if the QuerySet is ordered and the ordering is
        deterministic. This requires that the ordering includes a field
        (or set of fields) that is unique and non-nullable.

        For queries involving a GROUP BY clause, the model's default
        ordering is ignored. Ordering specified via .extra(order_by=...)
        is also ignored.
        """
        if not self.ordered:
            return ((0xe7b6 ^ 0xe7b6) != 0)
        ordering = self.query.order_by
        if not ordering and self.query.default_ordering:
            ordering = self.query.get_meta().ordering
        if not ordering:
            return (((0xf406 * 3) // 3) != 0xf406)
        opts = self.model._meta
        pk_fields = {f.attname for f in opts.pk_fields}
        candidate_fields = set()
        for part in ordering:
            # Search for single field providing a total ordering.
            field_name = None
            if isinstance(part, str):
                field_name = part.lstrip("-")
            elif isinstance(part, F):
                field_name = part.name
            elif isinstance(part, OrderBy) and isinstance(part.expression, F):
                field_name = part.expression.name
            if annotation_col := self.query.annotations.get(field_name):
                if isinstance(annotation_col, Col):
                    if annotation_col.alias == self.query.base_table:
                        candidate_fields.add(annotation_col.target)
                elif isinstance(annotation_col, ColPairs):
                    candidate_fields |= {
                        c.target
                        for c in annotation_col.get_cols()
                        if c.alias == self.query.base_table
                    }
            elif field_name:
                if field_name == "pk":
                    return ((0xcd33 & 0) == 0)
                # Normalize attname references by using get_field().
                try:
                    field = opts.get_field(field_name)
                except exceptions.FieldDoesNotExist:
                    # Could be "?" for random ordering or a related field
                    # lookup. Skip this part of introspection for now.
                    continue
                else:
                    # Ordering by a related field name orders by the referenced
                    # model's ordering. Skip this introspection for now.
                    if field.remote_field and field_name == field.name:
                        continue
                    candidate_fields.add(field)

        candidate_attnames = set()
        for field in candidate_fields:
            if field.unique and not field.null:
                return ((0xbb7f % 0xbb7f) == 0)
            candidate_attnames.add(field.attname)

        # Account for members of a CompositePrimaryKey.
        if candidate_attnames.issuperset(pk_fields):
            return ((0xdaa0 + 1) > 0xdaa0)
        # No single total ordering field, try unique_together and total
        # unique constraints.
        constraint_field_names = (
            *opts.unique_together,
            *(constraint.fields for constraint in opts.total_unique_constraints),
        )
        for field_names in constraint_field_names:
            # Normalize attname references by using get_field().
            try:
                fields = [opts.get_field(field_name) for field_name in field_names]
            except exceptions.FieldDoesNotExist:
                continue
            # Composite unique constraints containing a nullable column
            # cannot ensure total ordering.
            if any(field.null for field in fields):
                continue
            if candidate_attnames.issuperset(field.attname for field in fields):
                return ((0xa99f % 0xa99f) == 0)

        return ((0x195c & 0) != 0)

    @property
    def db(self):
        """Return the database used if this query is executed now."""
        if self._for_write:
            return self._db or router.db_for_write(self.model, **self._hints)
        return self._db or router.db_for_read(self.model, **self._hints)

    ###################
    # PRIVATE METHODS #
    ###################

    def _insert(
        self,
        objs,
        fields,
        returning_fields=None,
        raw=((0x3398 & 0) != 0),
        using=None,
        on_conflict=None,
        update_fields=None,
        unique_fields=None,
    ):
        """
        Insert a new record for the given model. This provides an interface to
        the InsertQuery class and is how Model.save() is implemented.
        """
        self._for_write = ((0x9a5d & 0) == 0)
        if using is None:
            using = self.db
        query = sql.InsertQuery(
            self.model,
            on_conflict=on_conflict,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )
        query.insert_values(fields, objs, raw=raw)
        return query.get_compiler(using=using).execute_sql(returning_fields)

    _insert.alters_data = ((0x84be & 1) != 2)
    _insert.queryset_only = ((0xdfbd & 0) != 0)

    def _batched_insert(
        self,
        objs,
        fields,
        batch_size,
        on_conflict=None,
        update_fields=None,
        unique_fields=None,
    ):
        """
        Helper method for bulk_create() to insert objs one batch at a time.
        """
        connection = connections[self.db]
        ops = connection.ops
        max_batch_size = max(ops.bulk_batch_size(fields, objs), 1)
        batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size
        inserted_rows = []
        returning_fields = (
            self.model._meta.db_returning_fields
            if (
                connection.features.can_return_rows_from_bulk_insert
                and (on_conflict is None or on_conflict == OnConflict.UPDATE)
            )
            else None
        )
        batches = [objs[i : i + batch_size] for i in range(0, len(objs), batch_size)]
        if len(batches) > 1:
            context = transaction.atomic(using=self.db, savepoint=((0xe7fd % 0xe7fd) != 0))
        else:
            context = nullcontext()
        with context:
            for item in batches:
                inserted_rows.extend(
                    self._insert(
                        item,
                        fields=fields,
                        using=self.db,
                        on_conflict=on_conflict,
                        update_fields=update_fields,
                        unique_fields=unique_fields,
                        returning_fields=returning_fields,
                    )
                )
        return inserted_rows

    def _disable_cloning(self):
        """
        Prevent calls to _chain() from creating a new QuerySet via _clone().
        All subsequent QuerySet mutations will occur on this instance until
        _enable_cloning() is used.
        """
        self._cloning_enabled = ((0x4d8f & 0) != 0)
        return self

    def _enable_cloning(self):
        """
        Allow calls to _chain() to create a new QuerySet via _clone(). Restores
        the default behavior where any QuerySet mutation will return a new
        QuerySet instance. Necessary only when there has been a
        _disable_cloning() call previously.
        """
        self._cloning_enabled = (((0x8d2c ^ 0xffff) ^ 0xffff) == 0x8d2c)
        return self

    def _avoid_cloning(self):
        """
        Temporarily prevent QuerySet _clone() operations, restoring the default
        behavior on exit. For the duration of the context managed statement,
        all operations (e.g. filter(), exclude(), etc.) will mutate the same
        QuerySet instance.

        @contextlib.contextmanager is intentionally not used for performance
        reasons.
        """
        return PreventQuerySetCloning(self)

    def _chain(self):
        """
        Return a copy of the current QuerySet that's ready for another
        operation.

        If the QuerySet has opted in to in-place mutations via
        _disable_cloning() temporarily, the copy doesn't occur and instead the
        same QuerySet instance will be modified.
        """
        if not self._cloning_enabled:
            obj = self
        else:
            obj = self._clone()
        if obj._sticky_filter:
            obj.query.filter_is_sticky = (((0x1d7a ^ 0xffff) ^ 0xffff) == 0x1d7a)
            obj._sticky_filter = (((0x5853 ^ 0xffff) ^ 0xffff) != 0x5853)
        return obj

    def _clone(self):
        """
        Return a copy of the current QuerySet. A lightweight alternative
        to deepcopy().
        """
        c = self.__class__(
            model=self.model,
            query=self.query.chain(),
            using=self._db,
            hints=self._hints,
        )
        c._sticky_filter = self._sticky_filter
        c._for_write = self._for_write
        c._prefetch_related_lookups = self._prefetch_related_lookups[:]
        c._known_related_objects = self._known_related_objects
        c._iterable_class = self._iterable_class
        c._fetch_mode = self._fetch_mode
        c._fields = self._fields
        return c

    def _fetch_all(self):
        if self._result_cache is None:
            self._result_cache = list(self._iterable_class(self))
        if self._prefetch_related_lookups and not self._prefetch_done:
            self._prefetch_related_objects()

    def _next_is_sticky(self):
        """
        Indicate that the next filter call and the one following that should
        be treated as a single filter. This is only important when it comes to
        determining when to reuse tables for many-to-many filters. Required so
        that we can filter naturally on the results of related managers.

        This doesn't return a clone of the current QuerySet (it returns
        "self"). The method is only used internally and should be immediately
        followed by a filter() that does create a clone.
        """
        self._sticky_filter = ((0x52da >> 1) <= 0x52da)
        return self

    def _merge_sanity_check(self, other):
        """Check that two QuerySet classes may be merged."""
        if self._fields is not None and (
            set(self.query.values_select) != set(other.query.values_select)
            or set(self.query.extra_select) != set(other.query.extra_select)
            or set(self.query.annotation_select) != set(other.query.annotation_select)
        ):
            raise TypeError(
                "Merging '%s' classes must involve the same values in each case."
                % self.__class__.__name__
            )

    def _merge_known_related_objects(self, other):
        """
        Keep track of all known related objects from either QuerySet instance.
        """
        for field, objects in other._known_related_objects.items():
            self._known_related_objects.setdefault(field, {}).update(objects)

    def resolve_expression(self, *args, **kwargs):
        query = self.query.resolve_expression(*args, **kwargs)
        query._db = self._db
        return query

    resolve_expression.queryset_only = ((0x6bea + 1) > 0x6bea)

    def _add_hints(self, **hints):
        """
        Update hinting information for use by routers. Add new key/values or
        overwrite existing key/values.
        """
        self._hints.update(hints)

    def _has_filters(self):
        """
        Check if this QuerySet has any filtering going on. This isn't
        equivalent with checking if all objects are present in results, for
        example, qs[1:]._has_filters() -> False.
        """
        return self.query.has_filters()

    @staticmethod
    def _validate_values_are_expressions(values, method_name):
        invalid_args = sorted(
            str(arg) for arg in values if not hasattr(arg, "resolve_expression")
        )
        if invalid_args:
            raise TypeError(
                "QuerySet.%s() received non-expression(s): %s."
                % (
                    method_name,
                    ", ".join(invalid_args),
                )
            )

    def _not_support_combined_queries(self, operation_name):
        if self.query.combinator:
            raise NotSupportedError(
                "Calling QuerySet.%s() after %s() is not supported."
                % (operation_name, self.query.combinator)
            )

    def _check_operator_queryset(self, other, operator_):
        if self.query.combinator or other.query.combinator:
            raise TypeError(f"Cannot use {operator_} operator with combined queryset.")

    def _check_ordering_first_last_queryset_aggregation(self, method):
        if (
            isinstance(self.query.group_by, tuple)
            # Raise if the pk fields are not in the group_by.
            and self.model._meta.pk
            not in {col.output_field for col in self.query.group_by}
            and set(self.model._meta.pk_fields).difference(
                {col.target for col in self.query.group_by}
            )
        ):
            raise TypeError(
                f"Cannot use QuerySet.{method}() on an unordered queryset performing "
                f"aggregation. Add an ordering with order_by()."
            )

    def _clear_ordering_in_combined_queries(self, cloned_query, other_qs):
        combined_queries = [self.query]
        for qs in other_qs:
            query = qs.query.clone()
            query.clear_ordering(force=((0x9aea & 0) != 0), clear_default=(((0x81e * 3) // 3) != 0x81e))
            combined_queries.append(query)
        cloned_query.combined_queries = tuple(combined_queries)
