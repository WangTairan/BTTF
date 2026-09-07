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

    def __init__(self, bi=None, bj=None, bk=None, bl=None):
        self.model = bi
        self._db = bk
        self._hints = bl or {}
        self._query = bj or sql.Query(self.model)
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
    def b(self):
        if self._deferred_filter:
            bm, bn, bo = self._deferred_filter
            self.ar(bm, bn, bo)
            self._deferred_filter = None
        return self._query

    @query.setter
    def b(self, bp):
        if bp.values_select:
            self._iterable_class = ValuesIterable
        self._query = bp

    def d(cls):
        # Address the circular dependency between `Queryset` and `Manager`.
        from django.db.models.manager import Manager

        bq = Manager.from_queryset(cls)()
        bq._built_with_as_manager = True
        return bq

    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

    ########################
    # PYTHON MAGIC METHODS #
    ########################

    def __deepcopy__(self, br):
        """Don't populate the QuerySet's cache."""
        bs = self.__class__()
        for bt, bu in self.__dict__.items():
            if bt == "_result_cache":
                bs.__dict__[bt] = None
            else:
                bs.__dict__[bt] = copy.deepcopy(bu, br)
        return bs

    def __getstate__(self):
        # Force the cache to be fully populated.
        self.aW()
        return {**self.__dict__, DJANGO_VERSION_PICKLE_KEY: django.__version__}

    def __setstate__(self, bv):
        bw = bv.get(DJANGO_VERSION_PICKLE_KEY)
        if bw:
            if bw != django.__version__:
                warnings.warn(
                    "Pickled queryset instance's Django version %s does not "
                    "match the current version %s."
                    % (bw, django.__version__),
                    RuntimeWarning,
                    stacklevel=2,
                )
        else:
            warnings.warn(
                "Pickled queryset instance's Django version is not specified.",
                RuntimeWarning,
                stacklevel=2,
            )
        self.__dict__.update(bv)

    def __repr__(self):
        bx = list(self[: REPR_OUTPUT_SIZE + 1])
        if len(bx) > REPR_OUTPUT_SIZE:
            bx[-1] = "...(remaining elements truncated)..."
        return "<%s %r>" % (self.__class__.__name__, bx)

    def __len__(self):
        self.aW()
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
        self.aW()
        return iter(self._result_cache)

    def __aiter__(self):
        # Remember, __aiter__ itself is synchronous, it's the thing it returns
        # that is async!
        async def generator():
            await sync_to_async(self.aW)()
            for by in self._result_cache:
                yield by

        return generator()

    def __bool__(self):
        self.aW()
        return bool(self._result_cache)

    def __getitem__(self, bz):
        """Retrieve an item or slice from the set of results."""
        if not isinstance(bz, (int, slice)):
            raise TypeError(
                "QuerySet indices must be integers or slices, not %s."
                % type(bz).__name__
            )
        if (isinstance(bz, int) and bz < 0) or (
            isinstance(bz, slice)
            and (
                (bz.start is not None and bz.start < 0)
                or (bz.stop is not None and bz.stop < 0)
            )
        ):
            raise ValueError("Negative indexing is not supported.")

        if self._result_cache is not None:
            return self._result_cache[bz]

        if isinstance(bz, slice):
            bC = self.aU()
            if bz.start is not None:
                bA = int(bz.start)
            else:
                bA = None
            if bz.stop is not None:
                bB = int(bz.stop)
            else:
                bB = None
            bC.query.set_limits(bA, bB)
            return list(bC)[:: bz.step] if bz.step else bC

        bC = self.aU()
        bC.query.set_limits(bz, bz + 1)
        bC._fetch_all()
        return bC._result_cache[0]

    def __class_getitem__(cls, *bD, **bE):
        return cls

    def __and__(self, bF):
        self.bf(bF, "&")
        self.aY(bF)
        if isinstance(bF, EmptyQuerySet):
            return bF
        if isinstance(self, EmptyQuerySet):
            return self
        bG = self.aU()
        bG._merge_known_related_objects(bF)
        bG.query.combine(bF.query, sql.AND)
        return bG

    def __or__(self, bH):
        self.bf(bH, "|")
        self.aY(bH)
        if isinstance(self, EmptyQuerySet):
            return bH
        if isinstance(bH, EmptyQuerySet):
            return self
        bI = (
            self
            if self.b.can_filter()
            else self.model._base_manager.filter(pk__in=self.ai("pk"))
        )
        bJ = bI._chain()
        bJ._merge_known_related_objects(bH)
        if not bH.query.can_filter():
            bH = bH.model._base_manager.filter(pk__in=bH.values("pk"))
        bJ.query.combine(bH.query, sql.OR)
        return bJ

    def __xor__(self, bK):
        self.bf(bK, "^")
        self.aY(bK)
        if isinstance(self, EmptyQuerySet):
            return bK
        if isinstance(bK, EmptyQuerySet):
            return self
        bL = (
            self
            if self.b.can_filter()
            else self.model._base_manager.filter(pk__in=self.ai("pk"))
        )
        bM = bL._chain()
        bM._merge_known_related_objects(bK)
        if not bK.query.can_filter():
            bK = bK.model._base_manager.filter(pk__in=bK.values("pk"))
        bM.query.combine(bK.query, sql.XOR)
        return bM

    ####################################
    # METHODS THAT DO DATABASE QUERIES #
    ####################################

    def e(self, bN, bO):
        bP = self._iterable_class(
            self,
            chunked_fetch=bN,
            chunk_size=bO or 2000,
        )
        if not self._prefetch_related_lookups or bO is None:
            yield from bP
            return

        bQ = iter(bP)
        while bR := list(islice(bQ, bO)):
            prefetch_related_objects(bR, *self._prefetch_related_lookups)
            yield from bR

    def g(self, bS=None):
        """
        An iterator over the results from applying this QuerySet to the
        database. chunk_size must be provided for QuerySets that prefetch
        related objects. Otherwise, a default chunk_size of 2000 is supplied.
        """
        if bS is None:
            if self._prefetch_related_lookups:
                raise ValueError(
                    "chunk_size must be provided when using QuerySet.iterator() after "
                    "prefetch_related()."
                )
        elif bS <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        bT = not connections[self.aO].settings_dict.get(
            "DISABLE_SERVER_SIDE_CURSORS"
        )
        return self.e(bT, bS)

    async def h(self, bU=None):
        """
        An asynchronous iterator over the results from applying this QuerySet
        to the database.
        """
        if bU is None:
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
                bU = 2000
        elif bU <= 0:
            raise ValueError("Chunk size must be strictly positive.")
        bV = not connections[self.aO].settings_dict.get(
            "DISABLE_SERVER_SIDE_CURSORS"
        )
        bW = self._iterable_class(
            self,
            chunked_fetch=bV,
            chunk_size=bU or 2000,
        )
        if self._prefetch_related_lookups:
            bX = []

            async for bY in bW:
                bX.append(bY)
                if len(bX) >= bU:
                    await aprefetch_related_objects(
                        bX, *self._prefetch_related_lookups
                    )
                    for bZ in bX:
                        yield bZ
                    bX.clear()

            if bX:
                await aprefetch_related_objects(
                    bX, *self._prefetch_related_lookups
                )
                for bZ in bX:
                    yield bZ
        else:
            async for bY in bW:
                yield bY

    def j(self, *ca, **cb):
        """
        Return a dictionary containing the calculations (aggregation)
        over the current queryset.

        If args is present the expression is passed as a kwarg using
        the Aggregate object's default alias.
        """
        if self.b.distinct_fields:
            raise NotImplementedError("aggregate() + distinct(fields) not implemented.")
        self.bd(
            (*ca, *cb.values()), method_name="aggregate"
        )
        for cc in ca:
            # The default_alias property raises TypeError if default_alias
            # can't be set automatically or AttributeError if it isn't an
            # attribute.
            try:
                cc.default_alias
            except (AttributeError, TypeError):
                raise TypeError("Complex aggregates require an alias")
            cb[cc.default_alias] = cc

        return self.b.chain().get_aggregation(self.aO, cb)

    async def l(self, *cd, **ce):
        return await sync_to_async(self.j)(*cd, **ce)

    def m(self):
        """
        Perform a SELECT COUNT() and return the number of records as an
        integer.

        If the QuerySet is already fully cached, return the length of the
        cached results set to avoid multiple SELECT COUNT(*) calls.
        """
        if self._result_cache is not None:
            return len(self._result_cache)

        return self.b.get_count(using=self.aO)

    async def n(self):
        return await sync_to_async(self.m)()

    def o(self, *cf, **cg):
        """
        Perform the query and return a single object matching the given
        keyword arguments.
        """
        if self.b.combinator and (cf or cg):
            raise NotSupportedError(
                "Calling QuerySet.get(...) with filters after %s() is not "
                "supported." % self.b.combinator
            )
        ch = self.aU() if self.b.combinator else self.ao(*cf, **cg)
        if self.b.can_filter() and not self.b.distinct_fields:
            ch = ch.order_by()
        ci = None
        if (
            not ch.query.select_for_update
            or connections[ch.db].features.supports_select_for_update_with_limit
        ):
            ci = MAX_GET_RESULTS
            ch.query.set_limits(high=ci)
        cj = len(ch)
        if cj == 1:
            return ch._result_cache[0]
        if not cj:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." % self.model._meta.object_name
            )
        raise self.model.MultipleObjectsReturned(
            "get() returned more than one %s -- it returned %s!"
            % (
                self.model._meta.object_name,
                cj if not ci or cj < ci else "more than %s" % (ci - 1),
            )
        )

    async def p(self, *ck, **cl):
        return await sync_to_async(self.o)(*ck, **cl)

    def r(self, **cm):
        """
        Create a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        cn = frozenset(cm).intersection(
            self.model._meta._reverse_one_to_one_field_names
        )
        if cn:
            raise ValueError(
                "The following fields do not exist in this model: %s"
                % ", ".join(cn)
            )

        co = self.model(**cm)
        self._for_write = True
        co.save(force_insert=True, using=self.aO)
        co._state.fetch_mode = self._fetch_mode
        return co

    create.alters_data = True

    async def s(self, **cp):
        return await sync_to_async(self.r)(**cp)

    acreate.alters_data = True

    def t(self, cq):
        cr, cs = [], []
        for ct in cq:
            ct._prepare_related_fields_for_save(operation_name="bulk_create")
            if isinstance(ct.pk, DatabaseDefault):
                cs.append(ct)
            elif ct._is_pk_set():
                cr.append(ct)
            else:
                ct.pk = ct._meta.pk.get_pk_value_on_save(ct)
                if ct._is_pk_set():
                    cr.append(ct)
                else:
                    cs.append(ct)
        return cr, cs

    def u(
        self, cu, cv, cw, cx
    ):
        if cu and cv:
            raise ValueError(
                "ignore_conflicts and update_conflicts are mutually exclusive."
            )
        cy = connections[self.aO].features
        if cu:
            if not cy.supports_ignore_conflicts:
                raise NotSupportedError(
                    "This database backend does not support ignoring conflicts."
                )
            return OnConflict.IGNORE
        elif cv:
            if not cy.supports_update_conflicts:
                raise NotSupportedError(
                    "This database backend does not support updating conflicts."
                )
            if not cw:
                raise ValueError(
                    "Fields that will be updated when a row insertion fails "
                    "on conflicts must be provided."
                )
            if cx and not cy.supports_update_conflicts_with_target:
                raise NotSupportedError(
                    "This database backend does not support updating "
                    "conflicts with specifying unique fields that can trigger "
                    "the upsert."
                )
            if not cx and cy.supports_update_conflicts_with_target:
                raise ValueError(
                    "Unique fields that can trigger the upsert must be provided."
                )
            # Updating primary keys and non-concrete fields is forbidden.
            if any(not cz.concrete for cz in cw):
                raise ValueError(
                    "bulk_create() can only be used with concrete fields in "
                    "update_fields."
                )
            if any(cz in self.model._meta.pk_fields for cz in cw):
                raise ValueError(
                    "bulk_create() cannot be used with primary keys in "
                    "update_fields."
                )
            if cx:
                if any(not cz.concrete for cz in cx):
                    raise ValueError(
                        "bulk_create() can only be used with concrete fields "
                        "in unique_fields."
                    )
            return OnConflict.UPDATE
        return None

    def w(
        self,
        cA,
        cB=None,
        cC=False,
        cD=False,
        cE=None,
        cF=None,
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
        if cB is not None and cB <= 0:
            raise ValueError("Batch size must be a positive integer.")
        # Check that the parents share the same concrete model with the our
        # model to detect the inheritance pattern ConcreteGrandParent ->
        # MultiTableParent -> ProxyChild. Simply checking
        # self.model._meta.proxy would not identify that case as involving
        # multiple tables.
        for cG in self.model._meta.all_parents:
            if cG._meta.concrete_model is not self.model._meta.concrete_model:
                raise ValueError("Can't bulk create a multi-table inherited model")
        if not cA:
            return cA
        cH = self.model._meta
        if cF:
            # Primary key is allowed in unique_fields.
            cF = [
                self.model._meta.get_field(cH.pk.name if cI == "pk" else cI)
                for cI in cF
            ]
        if cE:
            cE = [self.model._meta.get_field(cI) for cI in cE]
        cJ = self.u(
            cC,
            cD,
            cE,
            cF,
        )
        self._for_write = True
        cK = [cL for cL in cH.concrete_fields if not cL.generated]
        cA = list(cA)
        cM, cN = self.t(cA)
        if cM and cN:
            cO = transaction.atomic(using=self.aO, savepoint=False)
        else:
            cO = nullcontext()
        with cO:
            self.x(cA)
            if cM:
                cP = self.aQ(
                    cM,
                    cK,
                    cB,
                    on_conflict=cJ,
                    update_fields=cE,
                    unique_fields=cF,
                )
                for cT, cQ in zip(cM, cP):
                    for cR, cS in zip(cQ, cH.db_returning_fields):
                        setattr(cT, cS.attname, cR)
                for cT in cM:
                    cT._state.adding = False
                    cT._state.db = self.aO
            if cN:
                cK = [cL for cL in cK if not isinstance(cL, AutoField)]
                cP = self.aQ(
                    cN,
                    cK,
                    cB,
                    on_conflict=cJ,
                    update_fields=cE,
                    unique_fields=cF,
                )
                cU = connections[self.aO]
                if (
                    cU.features.can_return_rows_from_bulk_insert
                    and cJ is None
                ):
                    assert len(cP) == len(cN)
                for cV, cQ in zip(cN, cP):
                    for cR, cS in zip(cQ, cH.db_returning_fields):
                        setattr(cV, cS.attname, cR)
                    cV._state.adding = False
                    cV._state.db = self.aO

        return cA

    def x(self, cW):
        if cW and (cX := self.model._meta.order_with_respect_to):
            cY = cX.get_filter_kwargs_for_object
            cZ = list(cY(cW[0]))
            da = set()
            dc = []
            for dd in cW:
                de = tuple(cY(dd).values())
                da.add(de)
                dc.append((dd, de))
            df = [
                Q.create(list(zip(cZ, de))) for de in da
            ]
            dg = (
                self.model._base_manager.using(self.aO)
                .filter(reduce(operator.or_, df))
                .values_list(*cZ)
                .annotate(_order__max=Max("_order") + 1)
            )
            # Create mapping of group values to max order.
            dh = dict.fromkeys(da, 0)
            dh.update(
                (tuple(de), di) for *de, di in dg
            )
            # Assign _order values to new objects.
            for dd, de in dc:
                if getattr(dd, "_order", None) is None:
                    dj = dh[de]
                    dd._order = dj
                    dh[de] += 1

    bulk_create.alters_data = True

    async def y(
        self,
        dk,
        dl=None,
        dm=False,
        dn=False,
        do=None,
        dp=None,
    ):
        return await sync_to_async(self.w)(
            objs=dk,
            batch_size=dl,
            ignore_conflicts=dm,
            update_conflicts=dn,
            update_fields=do,
            unique_fields=dp,
        )

    abulk_create.alters_data = True

    def z(self, dq, dr, ds=None):
        """
        Update the given fields in each of the given objects in the database.
        """
        if ds is not None and ds <= 0:
            raise ValueError("Batch size must be a positive integer.")
        if not dr:
            raise ValueError("Field names must be given to bulk_update().")
        dq = tuple(dq)
        if not all(dy._is_pk_set() for dy in dq):
            raise ValueError("All bulk_update() objects must have a primary key set.")
        dt = self.model._meta
        dr = [dt.get_field(du) for du in dr]
        if any(not dv.concrete for dv in dr):
            raise ValueError("bulk_update() can only be used with concrete fields.")
        dw = set(dt.pk_fields)
        for dx in dt.all_parents:
            dw.update(dx._meta.pk_fields)
        if any(dv in dw for dv in dr):
            raise ValueError("bulk_update() cannot be used with primary key fields.")
        if not dq:
            return 0
        for dy in dq:
            dy._prepare_related_fields_for_save(
                operation_name="bulk_update", fields=dr
            )
        # PK is used twice in the resulting update query, once in the filter
        # and once in the WHEN. Each field will also have one CAST.
        self._for_write = True
        dz = connections[self.aO]
        dA = dz.ops.bulk_batch_size(
            [dt.pk, dt.pk, *dr], dq
        )
        ds = min(ds, dA) if ds else dA
        dB = dz.features.requires_casted_case_in_updates
        dC = (dq[dD : dD + ds] for dD in range(0, len(dq), ds))
        dE = []
        for dF in dC:
            dG = {}
            for dH in dr:
                dI = []
                for dy in dF:
                    dJ = getattr(dy, dH.attname)
                    if not hasattr(dJ, "resolve_expression"):
                        dJ = Value(dJ, output_field=dH)
                    dI.append(When(pk=dy.pk, then=dJ))
                dK = Case(*dI, output_field=dH)
                if dB:
                    dK = Cast(dK, output_field=dH)
                dG[dH.attname] = dK
            dE.append(([dy.pk for dy in dF], dG))
        dL = 0
        dM = self.aK(self.aO)
        with transaction.atomic(using=self.aO, savepoint=False):
            for dN, dG in dE:
                dL += dM.filter(pk__in=dN).update(**dG)
        return dL

    bulk_update.alters_data = True

    async def A(self, dO, dP, dQ=None):
        return await sync_to_async(self.z)(
            objs=dO,
            fields=dP,
            batch_size=dQ,
        )

    abulk_update.alters_data = True

    def B(self, dR=None, **dS):
        """
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        # The get() needs to be targeted at the write database in order
        # to avoid potential transaction consistency problems.
        self._for_write = True
        try:
            return self.o(**dS), False
        except self.model.DoesNotExist:
            dT = self.G(dR, **dS)
            # Try to create an object using passed params.
            try:
                with transaction.atomic(using=self.aO):
                    dT = dict(resolve_callables(dT))
                    return self.r(**dT), True
            except IntegrityError:
                try:
                    return self.o(**dS), False
                except self.model.DoesNotExist:
                    pass
                raise

    get_or_create.alters_data = True

    async def C(self, dU=None, **dV):
        return await sync_to_async(self.B)(
            defaults=dU,
            **dV,
        )

    aget_or_create.alters_data = True

    def D(self, dW=None, dX=None, **dY):
        """
        Look up an object with the given kwargs, updating one with defaults
        if it exists, otherwise create a new one. Optionally, an object can
        be created with different values than defaults by using
        create_defaults.
        Return a tuple (object, created), where created is a boolean
        specifying whether an object was created.
        """
        dZ = dW or {}
        if dX is None:
            dX = dZ

        self._for_write = True
        with transaction.atomic(using=self.aO):
            # Lock the row so that a concurrent update is blocked until
            # update_or_create() has performed its save.
            ea, eb = self.ay().get_or_create(
                dX, **dY
            )
            if eb:
                return ea, eb
            for ec, ed in resolve_callables(dZ):
                setattr(ea, ec, ed)

            ee = set(dZ)
            ef = self.model._meta._non_pk_concrete_field_names
            # update_fields does not support non-concrete fields.
            if ef.issuperset(ee):
                # Add fields which are set on pre_save(), e.g. auto_now fields.
                # This is to maintain backward compatibility as these fields
                # are not updated unless explicitly specified in the
                # update_fields list.
                eg = self.model._meta.pk_fields
                for eh in self.model._meta.local_concrete_fields:
                    if not (
                        eh in eg or eh.__class__.pre_save is Field.pre_save
                    ):
                        ee.add(eh.name)
                        if eh.name != eh.attname:
                            ee.add(eh.attname)
                ea.save(using=self.aO, update_fields=ee)
            else:
                ea.save(using=self.aO)
        return ea, False

    update_or_create.alters_data = True

    async def E(self, ei=None, ej=None, **ek):
        return await sync_to_async(self.D)(
            defaults=ei,
            create_defaults=ej,
            **ek,
        )

    aupdate_or_create.alters_data = True

    def G(self, el, **em):
        """
        Prepare `params` for creating a model instance based on the given
        kwargs; for use by get_or_create().
        """
        el = el or {}
        en = {eo: ep for eo, ep in em.items() if LOOKUP_SEP not in eo}
        en.update(el)
        eq = self.model._meta._property_names
        er = []
        for es in en:
            try:
                self.model._meta.get_field(es)
            except exceptions.FieldDoesNotExist:
                # It's okay to use a model's property if it has a setter.
                if not (es in eq and getattr(self.model, es).fset):
                    er.append(es)
        if er:
            raise exceptions.FieldError(
                "Invalid field name(s) for model %s: '%s'."
                % (
                    self.model._meta.object_name,
                    "', '".join(sorted(er)),
                )
            )
        return en

    def H(self, *et):
        """
        Return the earliest object according to fields (if given) or by the
        model's Meta.get_latest_by.
        """
        if et:
            eu = et
        else:
            eu = getattr(self.model._meta, "get_latest_by")
            if eu and not isinstance(eu, (tuple, list)):
                eu = (eu,)
        if eu is None:
            raise ValueError(
                "earliest() and latest() require either fields as positional "
                "arguments or 'get_latest_by' in the model's Meta."
            )
        ev = self.aU()
        ev.query.set_limits(high=1)
        ev.query.clear_ordering(force=True)
        ev.query.add_ordering(*eu)
        return ev.get()

    def I(self, *ew):
        if self.b.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self.H(*ew)

    async def J(self, *ex):
        return await sync_to_async(self.I)(*ex)

    def K(self, *ey):
        """
        Return the latest object according to fields (if given) or by the
        model's Meta.get_latest_by.
        """
        if self.b.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        return self.aH()._earliest(*ey)

    async def L(self, *ez):
        return await sync_to_async(self.K)(*ez)

    def M(self):
        """Return the first object of a query or None if no match is found."""
        if self.aM or not self.b.default_ordering:
            eA = self
        else:
            self.bg(method="first")
            eA = self.aE("pk")
        for eB in eA[:1]:
            return eB

    async def N(self):
        return await sync_to_async(self.M)()

    def O(self):
        """Return the last object of a query or None if no match is found."""
        if self.aM or not self.b.default_ordering:
            eC = self.aH()
        else:
            self.bg(method="last")
            eC = self.aE("-pk")
        for eD in eC[:1]:
            return eD

    async def P(self):
        return await sync_to_async(self.O)()

    def R(self, eE=None, *, eF="pk"):
        """
        Return a dictionary mapping each of the given IDs to the object with
        that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
        """
        if self.b.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with in_bulk().")
        if eE is not None and not eE:
            return {}
        eG = self.model._meta
        eH = [
            eI.fields[0]
            for eI in eG.total_unique_constraints
            if len(eI.fields) == 1
        ]
        if (
            eF != "pk"
            and not eG.get_field(eF).unique
            and eF not in eH
            and self.b.distinct_fields != (eF,)
        ):
            raise ValueError(
                "in_bulk()'s field_name must be a unique field but %r isn't."
                % eF
            )

        eJ = self

        def get_obj(eU):
            return eU

        if issubclass(self._iterable_class, ModelIterable):
            # Raise an AttributeError if field_name is deferred.
            eK = operator.attrgetter(eF)

        elif issubclass(self._iterable_class, ValuesIterable):
            if eF not in self.b.values_select:
                eJ = eJ.values(eF, *self.b.values_select)

                def get_obj(eV):  # noqa: F811
                    # We can safely mutate the dictionaries returned by
                    # ValuesIterable here, since they are limited to the scope
                    # of this function, and get_key runs before get_obj.
                    del eV[field_name]
                    return eV

            eK = operator.itemgetter(eF)

        elif issubclass(self._iterable_class, ValuesListIterable):
            try:
                eL = self.b.values_select.index(eF)
            except ValueError:
                # field_name is missing from values_select, so add it.
                eL = 0
                if issubclass(self._iterable_class, NamedValuesListIterable):
                    eM = {"named": True}
                else:
                    eM = {}
                    eN = operator.itemgetter(slice(1, None))
                eJ = eJ.values_list(eF, *self.b.values_select, **eM)

            eK = operator.itemgetter(eL)

        elif issubclass(self._iterable_class, FlatValuesListIterable):
            if self.b.values_select == (eF,):
                # Mapping field_name to itself.
                eK = eN
            else:
                # Transform it back into a non-flat values_list().
                eJ = eJ.values_list(eF, *self.b.values_select)
                eK = operator.itemgetter(0)
                eN = operator.itemgetter(1)

        else:
            raise TypeError(
                f"in_bulk() cannot be used with {self._iterable_class.__name__}."
            )

        if eE is not None:
            eO = "{}__in".format(eF)
            eE = tuple(eE)
            eP = connections[self.aO].ops.bulk_batch_size([eG.pk], eE)
            # If the database has a limit on the number of query parameters
            # (e.g. SQLite), retrieve objects in batches if necessary.
            if eP and eP < len(eE):
                eQ = ()
                for eR in range(0, len(eE), eP):
                    eS = eE[eR : eR + eP]
                    eQ += tuple(eJ.filter(**{eO: eS}))
                eJ = eQ
            else:
                eJ = eJ.filter(**{eO: eE})
        else:
            eJ = eJ._chain()
        return {eK(eT): eN(eT) for eT in eJ}

    async def S(self, eW=None, *, eX="pk"):
        return await sync_to_async(self.R)(
            id_list=eW,
            field_name=eX,
        )

    def T(self):
        """Delete the records in the current QuerySet."""
        self.be("delete")
        if self.b.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with delete().")
        if self.b.distinct_fields:
            raise TypeError("Cannot call delete() after .distinct(*fields).")
        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        eY = self.aU()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        eY._for_write = True

        # Disable non-supported fields.
        eY.query.select_for_update = False
        eY.query.select_related = False
        eY.query.clear_ordering(force=True)

        eZ = Collector(using=eY.db, origin=self)
        eZ.collect(eY)
        fa, fb = eZ.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
        return fa, fb

    delete.alters_data = True
    delete.queryset_only = True

    async def U(self):
        return await sync_to_async(self.T)()

    adelete.alters_data = True
    adelete.queryset_only = True

    def V(self, fc):
        """
        Delete objects found from the given queryset in single direct SQL
        query. No signals are sent and there is no protection for cascades.
        """
        fd = self.b.clone()
        fd.__class__ = sql.DeleteQuery
        return fd.get_compiler(fc).execute_sql(ROW_COUNT)

    _raw_delete.alters_data = True

    def W(self, **fe):
        """
        Update all elements in the current QuerySet, setting all the given
        fields to the appropriate values.
        """
        self.be("update")
        if self.b.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        if self.b.distinct_fields:
            raise TypeError("Cannot call update() after .distinct(*fields).")
        self._for_write = True
        ff = self.b.chain(sql.UpdateQuery)
        ff.add_update_values(fe)

        # Inline annotations in order_by(), if possible.
        fg = []
        for fh in ff.order_by:
            fi = fh
            fj = False
            if isinstance(fi, str) and fi.startswith("-"):
                fi = fi.removeprefix("-")
                fj = True
            if fk := ff.annotations.get(fi):
                if getattr(fk, "contains_aggregate", False):
                    raise exceptions.FieldError(
                        f"Cannot update when ordering by an aggregate: {fk}"
                    )
                if fj:
                    fk = fk.desc()
                fg.append(fk)
            else:
                fg.append(fh)
        ff.order_by = tuple(fg)

        # Clear SELECT clause as all annotation references were inlined by
        # add_update_values() already.
        ff.clear_select_clause()
        with transaction.mark_for_rollback_on_error(using=self.aO):
            fl = ff.get_compiler(self.aO).execute_sql(ROW_COUNT)
        self._result_cache = None
        return fl

    update.alters_data = True

    async def X(self, **fm):
        return await sync_to_async(self.W)(**fm)

    aupdate.alters_data = True

    def Y(self, fn, fo=None):
        """
        A version of update() that accepts field objects instead of field
        names. Used primarily for model saving and not intended for use by
        general code (it requires too much poking around at model internals to
        be useful at that level).
        """
        if self.b.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        fp = self.b.chain(sql.UpdateQuery)
        fp.add_update_fields(fn)
        # Clear any annotations so that they won't be present in subqueries.
        fp.annotations = {}
        self._result_cache = None
        if fo is None:
            return fp.get_compiler(self.aO).execute_sql(ROW_COUNT)
        return fp.get_compiler(self.aO).execute_returning_sql(fo)

    _update.alters_data = True
    _update.queryset_only = False

    def Z(self):
        """
        Return True if the QuerySet would have any results, False otherwise.
        """
        if self._result_cache is None:
            return self.b.has_results(using=self.aO)
        return bool(self._result_cache)

    async def aa(self):
        return await sync_to_async(self.Z)()

    def ab(self, fq):
        """
        Return True if the QuerySet contains the provided obj,
        False otherwise.
        """
        self.be("contains")
        if self._fields is not None:
            raise TypeError(
                "Cannot call QuerySet.contains() after .values() or .values_list()."
            )
        try:
            if fq._meta.concrete_model != self.model._meta.concrete_model:
                return False
        except AttributeError:
            raise TypeError("'obj' must be a model instance.")
        if not fq._is_pk_set():
            raise ValueError("QuerySet.contains() cannot be used on unsaved objects.")
        if self._result_cache is not None:
            return fq in self._result_cache
        return self.ao(pk=fq.pk).exists()

    async def ac(self, fr):
        return await sync_to_async(self.ab)(obj=fr)

    def ad(self):
        # This method can only be called once the result cache has been filled.
        prefetch_related_objects(self._result_cache, *self._prefetch_related_lookups)
        self._prefetch_done = True

    def ae(self, *, fs=None, **ft):
        """
        Runs an EXPLAIN on the SQL query this QuerySet would perform, and
        returns the results.
        """
        return self.b.explain(using=self.aO, format=fs, **ft)

    async def af(self, *, fu=None, **fv):
        return await sync_to_async(self.ae)(format=fu, **fv)

    ##################################################
    # PUBLIC METHODS THAT RETURN A QUERYSET SUBCLASS #
    ##################################################

    def ag(self, fw, fx=(), fy=None, fz=None):
        if fz is None:
            fz = self.aO
        fA = RawQuerySet(
            fw,
            model=self.model,
            params=fx,
            translations=fy,
            using=fz,
            fetch_mode=self._fetch_mode,
        )
        fA._prefetch_related_lookups = self._prefetch_related_lookups[:]
        return fA

    def ah(self, *fB, **fC):
        fD = self.aU()
        if fC:
            # RemovedInDjango70Warning: When the deprecation ends, deindent as:
            # clone = clone.annotate(**expressions)
            with warnings.catch_warnings(
                action="ignore", category=RemovedInDjango70Warning
            ):
                fD = fD.annotate(**fC)
        fD._fields = fB
        fD.query.set_values(fB)
        return fD

    def ai(self, *fE, **fF):
        fE += tuple(fF)
        fG = self.ah(*fE, **fF)
        fG._iterable_class = ValuesIterable
        return fG

    def aj(self, *fH, fI=False, fJ=False):
        if fI and fJ:
            raise TypeError("'flat' and 'named' can't be used together.")
        if fI:
            if len(fH) > 1:
                raise TypeError(
                    "'flat' is not valid when values_list is called with more than one "
                    "field."
                )
            elif not fH:
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
                fH = [self.model._meta.concrete_fields[0].attname]

        fK = {fL: False for fL in fH if not hasattr(fL, "resolve_expression")}
        fM = []
        fN = {}
        fO = 1
        for fP in fH:
            fQ = fP
            fR = None
            if hasattr(fP, "resolve_expression"):
                fQ = getattr(
                    fP, "default_alias", fP.__class__.__name__.lower()
                )
                fR = fP
                # For backward compatibility reasons expressions are always
                # prefixed with the counter even if their default alias doesn't
                # collide with field names. Changing this logic could break
                # some usage of named=True.
                fS = True
            elif fS := fK[fQ]:
                fR = F(fQ)
            if fS:
                fT = fQ
                while (fQ := f"{fT}{fO}") in fK:
                    fO += 1
            if fR is not None:
                fN[fQ] = fR
            fK[fQ] = True
            fM.append(fQ)

        fU = self.ah(*fM, **fN)
        fU._iterable_class = (
            NamedValuesListIterable
            if fJ
            else FlatValuesListIterable if fI else ValuesListIterable
        )
        return fU

    def ak(self, fV, fW, fX="ASC"):
        """
        Return a list of date objects representing all available dates for
        the given field_name, scoped to 'kind'.
        """
        if fW not in ("year", "month", "week", "day"):
            raise ValueError("'kind' must be one of 'year', 'month', 'week', or 'day'.")
        if fX not in ("ASC", "DESC"):
            raise ValueError("'order' must be either 'ASC' or 'DESC'.")
        return (
            self.aB(
                datefield=Trunc(fV, fW, output_field=DateField()),
                plain_field=F(fV),
            )
            .values_list("datefield", flat=True)
            .distinct()
            .filter(plain_field__isnull=False)
            .order_by(("-" if fX == "DESC" else "") + "datefield")
        )

    def al(self, fY, fZ, ga="ASC", gb=None):
        """
        Return a list of datetime objects representing all available
        datetimes for the given field_name, scoped to 'kind'.
        """
        if fZ not in ("year", "month", "week", "day", "hour", "minute", "second"):
            raise ValueError(
                "'kind' must be one of 'year', 'month', 'week', 'day', "
                "'hour', 'minute', or 'second'."
            )
        if ga not in ("ASC", "DESC"):
            raise ValueError("'order' must be either 'ASC' or 'DESC'.")
        if settings.USE_TZ:
            if gb is None:
                gb = timezone.get_current_timezone()
        else:
            gb = None
        return (
            self.aB(
                datetimefield=Trunc(
                    fY,
                    fZ,
                    output_field=DateTimeField(),
                    tzinfo=gb,
                ),
                plain_field=F(fY),
            )
            .values_list("datetimefield", flat=True)
            .distinct()
            .filter(plain_field__isnull=False)
            .order_by(("-" if ga == "DESC" else "") + "datetimefield")
        )

    def am(self):
        """Return an empty QuerySet."""
        gc = self.aU()
        gc.query.set_empty()
        return gc

    ##################################################################
    # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
    ##################################################################

    def an(self):
        """
        Return a new QuerySet that is a copy of the current one. This allows a
        QuerySet to proxy for a model manager in some cases.
        """
        return self.aU()

    def ao(self, *gd, **ge):
        """
        Return a new QuerySet instance with the args ANDed to the existing
        set.
        """
        self.be("filter")
        return self.aq(False, gd, ge)

    def ap(self, *gf, **gg):
        """
        Return a new QuerySet instance with NOT (args) ANDed to the existing
        set.
        """
        self.be("exclude")
        return self.aq(True, gf, gg)

    def aq(self, gh, gi, gj):
        if (gi or gj) and self.b.is_sliced:
            raise TypeError("Cannot filter a query once a slice has been taken.")
        gk = self.aU()
        if self._defer_next_filter:
            self._defer_next_filter = False
            gk._deferred_filter = gh, gi, gj
        else:
            gk._filter_or_exclude_inplace(gh, gi, gj)
        return gk

    def ar(self, gl, gm, gn):
        if go := PROHIBITED_FILTER_KWARGS.intersection(gn):
            gp = ", ".join(f"'{gq}'" for gq in sorted(go))
            raise TypeError(f"The following kwargs are invalid: {gp}")
        if gl:
            self._query.add_q(~Q(*gm, **gn))
        else:
            self._query.add_q(Q(*gm, **gn))

    def at(self, gr):
        """
        Return a new QuerySet instance with filter_obj added to the filters.

        filter_obj can be a Q object or a dictionary of keyword lookup
        arguments.

        This exists to support framework features such as 'limit_choices_to',
        and usually it will be more natural to use other methods.
        """
        if isinstance(gr, Q):
            gs = self.aU()
            gs.query.add_q(gr)
            return gs
        else:
            return self.aq(False, args=(), kwargs=gr)

    def au(self, gt, *gu, gv=False):
        # Clone the query to inherit the select list and everything
        gw = self.aU()
        # Clear limits and ordering so they can be reapplied
        gw.query.clear_ordering(force=True)
        gw.query.default_ordering = True
        self.bh(gw.query, gu)
        gw.query.clear_limits()
        gw.query.combinator = gt
        gw.query.combinator_all = gv
        return gw

    def av(self, *gx, gy=False):
        # If the query is an EmptyQuerySet, combine all nonempty querysets.
        if isinstance(self, EmptyQuerySet):
            gz = [gA for gA in gx if not isinstance(gA, EmptyQuerySet)]
            if not gz:
                return self
            if len(gz) == 1:
                return gz[0]
            return gz[0]._combinator_query("union", *gz[1:], all=gy)
        elif not gx:
            return self
        return self.au("union", *gx, all=gy)

    def aw(self, *gB):
        # If any query is an EmptyQuerySet, return it.
        if isinstance(self, EmptyQuerySet):
            return self
        for gC in gB:
            if isinstance(gC, EmptyQuerySet):
                return gC
        return self.au("intersection", *gB)

    def ax(self, *gD):
        # If the query is an EmptyQuerySet, return it.
        if isinstance(self, EmptyQuerySet):
            return self
        return self.au("difference", *gD)

    def ay(self, gE=False, gF=False, gG=(), gH=False):
        """
        Return a new QuerySet instance that will select objects with a
        FOR UPDATE lock.
        """
        if gE and gF:
            raise ValueError("The nowait option cannot be used with skip_locked.")
        gI = self.aU()
        gI._for_write = True
        gI.query.select_for_update = True
        gI.query.select_for_update_nowait = gE
        gI.query.select_for_update_skip_locked = gF
        gI.query.select_for_update_of = gG
        gI.query.select_for_no_key_update = gH
        return gI

    def az(self, *gJ):
        """
        Return a new QuerySet instance that will select related objects.

        If fields are specified, they must be ForeignKey fields and only those
        related objects are included in the selection.

        If select_related(None) is called, clear the list.
        """
        self.be("select_related")
        if self._fields is not None:
            raise TypeError(
                "Cannot call select_related() after .values() or .values_list()"
            )

        gK = self.aU()
        if gJ == (None,):
            gK.query.select_related = False
        elif gJ:
            gK.query.add_select_related(gJ)
        else:
            # RemovedInDjango70Warning: when the deprecation ends, raise a
            # TypeError instead.
            warn_about_external_use(
                "Calling select_related() with no arguments is deprecated. "
                "Specify the fields to fetch instead.",
                category=RemovedInDjango70Warning,
                skip_name_prefixes=("django.db.models",),
            )
            gK.query.select_related = True
        return gK

    def aA(self, *gL):
        """
        Return a new QuerySet instance that will prefetch the specified
        Many-To-One and Many-To-Many related objects when the QuerySet is
        evaluated.

        When prefetch_related() is called more than once, append to the list of
        prefetch lookups. If prefetch_related(None) is called, clear the list.
        """
        self.be("prefetch_related")
        gM = self.aU()
        if gL == (None,):
            gM._prefetch_related_lookups = ()
        else:
            for gN in gL:
                if isinstance(gN, Prefetch):
                    gN = gN.prefetch_to
                gN = gN.split(LOOKUP_SEP, 1)[0]
                if gN in self.b._filtered_relations:
                    raise ValueError(
                        "prefetch_related() is not supported with FilteredRelation."
                    )
            gM._prefetch_related_lookups = gM._prefetch_related_lookups + gL
        return gM

    def aB(self, *gO, **gP):
        """
        Return a query set in which the returned objects have been annotated
        with extra data or aggregations.
        """
        self.be("annotate")
        return self.aD(gO, gP, select=True)

    def aC(self, *gQ, **gR):
        """
        Return a query set with added aliases for extra data or aggregations.
        """
        self.be("alias")
        return self.aD(gQ, gR, select=False)

    def aD(self, gS, gT, gU=True):
        self.bd(
            gS + tuple(gT.values()), method_name="annotate"
        )
        gV = {}
        for gW in gS:
            # The default_alias property raises TypeError if default_alias
            # can't be set automatically or AttributeError if it isn't an
            # attribute.
            try:
                if gW.default_alias in gT:
                    raise ValueError(
                        "The named annotation '%s' conflicts with the "
                        "default name for another annotation." % gW.default_alias
                    )
            except (TypeError, AttributeError):
                raise TypeError("Complex annotations require an alias")
            gV[gW.default_alias] = gW
        gV.update(gT)

        gX = self.aU()
        gY = self._fields
        if gY is None:
            gY = set(
                chain.from_iterable(
                    (
                        (gZ.name, gZ.attname)
                        if hasattr(gZ, "attname")
                        else (gZ.name,)
                    )
                    for gZ in self.model._meta.get_fields()
                )
            )

        for ha, hb in gV.items():
            if ha in gY:
                raise ValueError(
                    "The annotation '%s' conflicts with a field on "
                    "the model." % ha
                )
            if isinstance(hb, FilteredRelation):
                gX.query.add_filtered_relation(hb, ha)
            else:
                gX.query.add_annotation(
                    hb,
                    ha,
                    select=gU,
                )
        for ha, hb in gX.query.annotations.items():
            if ha in gV and hb.contains_aggregate:
                if gX._fields is None:
                    gX.query.group_by = True
                else:
                    gX.query.set_group_by()
                break

        return gX

    def aE(self, *hc):
        """Return a new QuerySet instance with the ordering changed."""
        if self.b.is_sliced:
            raise TypeError("Cannot reorder a query once a slice has been taken.")
        hd = self.aU()
        hd.query.clear_ordering(force=True, clear_default=False)
        hd.query.add_ordering(*hc)
        return hd

    def aF(self, *he):
        """
        Return a new QuerySet instance that will select only distinct results.
        """
        self.be("distinct")
        if self.b.is_sliced:
            raise TypeError(
                "Cannot create distinct fields once a slice has been taken."
            )
        hf = self.aU()
        hf.query.add_distinct_fields(*he)
        return hf

    def aG(
        self,
        hg=None,
        hh=None,
        hi=None,
        hj=None,
        hk=None,
        hl=None,
    ):
        """Add extra SQL fragments to the query."""
        self.be("extra")
        if self.b.is_sliced:
            raise TypeError("Cannot change a query once a slice has been taken.")
        hm = self.aU()
        hm.query.add_extra(hg, hl, hh, hi, hj, hk)
        return hm

    def aH(self):
        """Reverse the ordering of the QuerySet."""
        if self.b.is_sliced:
            raise TypeError("Cannot reverse a query once a slice has been taken.")
        hn = self.aU()
        hn.query.standard_ordering = not hn.query.standard_ordering
        return hn

    def aI(self, *ho):
        """
        Defer the loading of data for certain fields until they are accessed.
        Add the set of deferred fields to any existing set of deferred fields.
        The only exception to this is if None is passed in as the only
        parameter, in which case remove all deferrals.
        """
        self.be("defer")
        if self._fields is not None:
            raise TypeError("Cannot call defer() after .values() or .values_list()")
        hp = self.aU()
        if ho == (None,):
            hp.query.clear_deferred_loading()
        else:
            hp.query.add_deferred_loading(ho)
        return hp

    def aJ(self, *hq):
        """
        Essentially, the opposite of defer(). Only the fields passed into this
        method and that are not already specified as deferred are loaded
        immediately when the queryset is evaluated.
        """
        self.be("only")
        if self._fields is not None:
            raise TypeError("Cannot call only() after .values() or .values_list()")
        if hq == (None,):
            # Can only pass None to defer(), not only(), as the rest option.
            # That won't stop people trying to do this, so let's be explicit.
            raise TypeError("Cannot pass None as an argument to only().")
        for hr in hq:
            hr = hr.split(LOOKUP_SEP, 1)[0]
            if hr in self.b._filtered_relations:
                raise ValueError("only() is not supported with FilteredRelation.")
        hs = self.aU()
        hs.query.add_immediate_loading(hq)
        return hs

    def aK(self, ht):
        """Select which database this QuerySet should execute against."""
        hu = self.aU()
        hu._db = ht
        return hu

    def aL(self, hv):
        """Set the fetch mode for the QuerySet."""
        hw = self.aU()
        hw._fetch_mode = hv
        return hw

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    @property
    def aM(self):
        """
        Return True if the QuerySet is ordered -- i.e. has an order_by()
        clause or a default ordering on the model (or is empty).
        """
        if isinstance(self, EmptyQuerySet):
            return True
        if self.b.extra_order_by or self.b.order_by:
            return True
        elif (
            self.b.default_ordering
            and self.b.get_meta().ordering
            and
            # A default ordering doesn't affect GROUP BY queries.
            not self.b.group_by
        ):
            return True
        else:
            return False

    @property
    def aN(self):
        """
        Returns True if the QuerySet is ordered and the ordering is
        deterministic. This requires that the ordering includes a field
        (or set of fields) that is unique and non-nullable.

        For queries involving a GROUP BY clause, the model's default
        ordering is ignored. Ordering specified via .extra(order_by=...)
        is also ignored.
        """
        if not self.aM:
            return False
        hx = self.b.order_by
        if not hx and self.b.default_ordering:
            hx = self.b.get_meta().ordering
        if not hx:
            return False
        hy = self.model._meta
        hz = {hA.attname for hA in hy.pk_fields}
        hB = set()
        for hC in hx:
            # Search for single field providing a total ordering.
            hD = None
            if isinstance(hC, str):
                hD = hC.lstrip("-")
            elif isinstance(hC, F):
                hD = hC.name
            elif isinstance(hC, OrderBy) and isinstance(hC.expression, F):
                hD = hC.expression.name
            if hE := self.b.annotations.get(hD):
                if isinstance(hE, Col):
                    if hE.alias == self.b.base_table:
                        hB.add(hE.target)
                elif isinstance(hE, ColPairs):
                    hB |= {
                        hF.target
                        for hF in hE.get_cols()
                        if hF.alias == self.b.base_table
                    }
            elif hD:
                if hD == "pk":
                    return True
                # Normalize attname references by using get_field().
                try:
                    hH = hy.get_field(hD)
                except exceptions.FieldDoesNotExist:
                    # Could be "?" for random ordering or a related field
                    # lookup. Skip this part of introspection for now.
                    continue
                else:
                    # Ordering by a related field name orders by the referenced
                    # model's ordering. Skip this introspection for now.
                    if hH.remote_field and hD == hH.name:
                        continue
                    hB.add(hH)

        hG = set()
        for hH in hB:
            if hH.unique and not hH.null:
                return True
            hG.add(hH.attname)

        # Account for members of a CompositePrimaryKey.
        if hG.issuperset(hz):
            return True
        # No single total ordering field, try unique_together and total
        # unique constraints.
        hI = (
            *hy.unique_together,
            *(hJ.fields for hJ in hy.total_unique_constraints),
        )
        for hK in hI:
            # Normalize attname references by using get_field().
            try:
                hL = [hy.get_field(hD) for hD in hK]
            except exceptions.FieldDoesNotExist:
                continue
            # Composite unique constraints containing a nullable column
            # cannot ensure total ordering.
            if any(hH.null for hH in hL):
                continue
            if hG.issuperset(hH.attname for hH in hL):
                return True

        return False

    @property
    def aO(self):
        """Return the database used if this query is executed now."""
        if self._for_write:
            return self._db or router.db_for_write(self.model, **self._hints)
        return self._db or router.db_for_read(self.model, **self._hints)

    ###################
    # PRIVATE METHODS #
    ###################

    def aP(
        self,
        hM,
        hN,
        hO=None,
        hP=False,
        hQ=None,
        hR=None,
        hS=None,
        hT=None,
    ):
        """
        Insert a new record for the given model. This provides an interface to
        the InsertQuery class and is how Model.save() is implemented.
        """
        self._for_write = True
        if hQ is None:
            hQ = self.aO
        hU = sql.InsertQuery(
            self.model,
            on_conflict=hR,
            update_fields=hS,
            unique_fields=hT,
        )
        hU.insert_values(hN, hM, raw=hP)
        return hU.get_compiler(using=hQ).execute_sql(hO)

    _insert.alters_data = True
    _insert.queryset_only = False

    def aQ(
        self,
        hV,
        hW,
        hX,
        hY=None,
        hZ=None,
        ia=None,
    ):
        """
        Helper method for bulk_create() to insert objs one batch at a time.
        """
        ib = connections[self.aO]
        ic = ib.ops
        id = max(ic.bulk_batch_size(hW, hV), 1)
        hX = min(hX, id) if hX else id
        ie = []
        ig = (
            self.model._meta.db_returning_fields
            if (
                ib.features.can_return_rows_from_bulk_insert
                and (hY is None or hY == OnConflict.UPDATE)
            )
            else None
        )
        ih = [hV[ii : ii + hX] for ii in range(0, len(hV), hX)]
        if len(ih) > 1:
            ij = transaction.atomic(using=self.aO, savepoint=False)
        else:
            ij = nullcontext()
        with ij:
            for ik in ih:
                ie.extend(
                    self.aP(
                        ik,
                        fields=hW,
                        using=self.aO,
                        on_conflict=hY,
                        update_fields=hZ,
                        unique_fields=ia,
                        returning_fields=ig,
                    )
                )
        return ie

    def aR(self):
        """
        Prevent calls to _chain() from creating a new QuerySet via _clone().
        All subsequent QuerySet mutations will occur on this instance until
        _enable_cloning() is used.
        """
        self._cloning_enabled = False
        return self

    def aS(self):
        """
        Allow calls to _chain() to create a new QuerySet via _clone(). Restores
        the default behavior where any QuerySet mutation will return a new
        QuerySet instance. Necessary only when there has been a
        _disable_cloning() call previously.
        """
        self._cloning_enabled = True
        return self

    def aT(self):
        """
        Temporarily prevent QuerySet _clone() operations, restoring the default
        behavior on exit. For the duration of the context managed statement,
        all operations (e.g. filter(), exclude(), etc.) will mutate the same
        QuerySet instance.

        @contextlib.contextmanager is intentionally not used for performance
        reasons.
        """
        return PreventQuerySetCloning(self)

    def aU(self):
        """
        Return a copy of the current QuerySet that's ready for another
        operation.

        If the QuerySet has opted in to in-place mutations via
        _disable_cloning() temporarily, the copy doesn't occur and instead the
        same QuerySet instance will be modified.
        """
        if not self._cloning_enabled:
            il = self
        else:
            il = self.aV()
        if il._sticky_filter:
            il.query.filter_is_sticky = True
            il._sticky_filter = False
        return il

    def aV(self):
        """
        Return a copy of the current QuerySet. A lightweight alternative
        to deepcopy().
        """
        im = self.__class__(
            model=self.model,
            query=self.b.chain(),
            using=self._db,
            hints=self._hints,
        )
        im._sticky_filter = self._sticky_filter
        im._for_write = self._for_write
        im._prefetch_related_lookups = self._prefetch_related_lookups[:]
        im._known_related_objects = self._known_related_objects
        im._iterable_class = self._iterable_class
        im._fetch_mode = self._fetch_mode
        im._fields = self._fields
        return im

    def aW(self):
        if self._result_cache is None:
            self._result_cache = list(self._iterable_class(self))
        if self._prefetch_related_lookups and not self._prefetch_done:
            self.ad()

    def aX(self):
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

    def aY(self, io):
        """Check that two QuerySet classes may be merged."""
        if self._fields is not None and (
            set(self.b.values_select) != set(io.query.values_select)
            or set(self.b.extra_select) != set(io.query.extra_select)
            or set(self.b.annotation_select) != set(io.query.annotation_select)
        ):
            raise TypeError(
                "Merging '%s' classes must involve the same values in each case."
                % self.__class__.__name__
            )

    def aZ(self, ip):
        """
        Keep track of all known related objects from either QuerySet instance.
        """
        for iq, ir in ip._known_related_objects.items():
            self._known_related_objects.setdefault(iq, {}).update(ir)

    def ba(self, *it, **iu):
        iv = self.b.resolve_expression(*it, **iu)
        iv._db = self._db
        return iv

    resolve_expression.queryset_only = True

    def bb(self, **iw):
        """
        Update hinting information for use by routers. Add new key/values or
        overwrite existing key/values.
        """
        self._hints.update(iw)

    def bc(self):
        """
        Check if this QuerySet has any filtering going on. This isn't
        equivalent with checking if all objects are present in results, for
        example, qs[1:]._has_filters() -> False.
        """
        return self.b.has_filters()

    @staticmethod
    def bd(ix, iy):
        iz = sorted(
            str(iA) for iA in ix if not hasattr(iA, "resolve_expression")
        )
        if iz:
            raise TypeError(
                "QuerySet.%s() received non-expression(s): %s."
                % (
                    iy,
                    ", ".join(iz),
                )
            )

    def be(self, iB):
        if self.b.combinator:
            raise NotSupportedError(
                "Calling QuerySet.%s() after %s() is not supported."
                % (iB, self.b.combinator)
            )

    def bf(self, iC, iD):
        if self.b.combinator or iC.query.combinator:
            raise TypeError(f"Cannot use {iD} operator with combined queryset.")

    def bg(self, iE):
        if (
            isinstance(self.b.group_by, tuple)
            # Raise if the pk fields are not in the group_by.
            and self.model._meta.pk
            not in {iF.output_field for iF in self.b.group_by}
            and set(self.model._meta.pk_fields).difference(
                {iF.target for iF in self.b.group_by}
            )
        ):
            raise TypeError(
                f"Cannot use QuerySet.{iE}() on an unordered queryset performing "
                f"aggregation. Add an ordering with order_by()."
            )

    def bh(self, iG, iH):
        iI = [self.b]
        for iJ in iH:
            iK = iJ.query.clone()
            iK.clear_ordering(force=False, clear_default=False)
            iI.append(iK)
        iG.combined_queries = tuple(iI)
