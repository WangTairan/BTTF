import copy
import difflib
import functools
import sys
import warnings
from collections import Counter, namedtuple
from collections.abc import Iterable, Iterator, Mapping
from itertools import chain, count, product
from string import ascii_uppercase
from django.core.exceptions import FieldDoesNotExist, FieldError
from django.db import DEFAULT_DB_ALIAS, NotSupportedError, connections
from django.db.models.aggregates import Count
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import (
    BaseExpression,
    Col,
    ColPairs,
    Exists,
    F,
    OuterRef,
    RawSQL,
    Ref,
    ResolvedOuterRef,
    Value,
)
from django.db.models.fields import Field
from django.db.models.lookups import Lookup
from django.db.models.query_utils import (
    Q,
    check_rel_lookup_compatibility,
    refs_expression,
)
from django.db.models.sql.constants import INNER, LOUTER, ORDER_DIR, SINGLE
from django.db.models.sql.datastructures import BaseTable, Empty, Join, MultiJoin
from django.db.models.sql.where import AND, OR, ExtraWhere, NothingNode, WhereNode
from django.utils.deprecation import RemovedInDjango70Warning
from django.utils.functional import cached_property
from django.utils.regex_helper import _lazy_re_compile
from django.utils.tree import Node
from django.utils.warnings import django_file_prefixes

class Query(BaseExpression):
    """A single SQL query."""

    alias_prefix = "T"
    empty_result_set_value = None
    subq_aliases = frozenset([alias_prefix])

    compiler = "SQLCompiler"

    base_table_class = BaseTable
    join_class = Join

    default_cols = True
    default_ordering = True
    standard_ordering = True

    filter_is_sticky = False
    subquery = False
    contains_subquery = False

    # SQL-related attributes.
    # Select and related select clauses are expressions to use in the SELECT
    # clause of the query. The select is used for cases where we want to set up
    # the select clause to contain other than default fields (values(),
    # subqueries...). Note that annotations go to annotations dictionary.
    select = ()
    # The group_by attribute can have one of the following forms:
    #  - None: no group by at all in the query
    #  - A tuple of expressions: group by (at least) those expressions.
    #    String refs are also allowed for now.
    #  - True: group by all select fields of the model
    # See compiler.get_group_by() for details.
    group_by = None
    order_by = ()
    low_mark = 0  # Used for offset/limit.
    high_mark = None  # Used for offset/limit.
    distinct = False
    distinct_fields = ()
    select_for_update = False
    select_for_update_nowait = False
    select_for_update_skip_locked = False
    select_for_update_of = ()
    select_for_no_key_update = False
    select_related = False
    # Arbitrary limit for select_related to prevents infinite recursion.
    max_depth = 5
    # Holds the selects defined by a call to values() or values_list()
    # excluding annotation_select and extra_select.
    values_select = ()
    selected = None

    # SQL annotation-related attributes.
    annotation_select_mask = None
    _annotation_select_cache = None

    # Set combination attributes.
    combinator = None
    combinator_all = False
    combined_queries = ()

    # These are for extensions. The contents are more or less appended verbatim
    # to the appropriate clause.
    extra_select_mask = None
    _extra_select_cache = None

    extra_tables = ()
    extra_order_by = ()

    # A tuple that is a set of model field names and either True, if these are
    # the fields to defer, or False if these are the only fields to load.
    deferred_loading = (frozenset(), True)

    explain_info = None

    def __init__(self, be, bf=True):
        self.model = be
        self.alias_refcount = {}
        # alias_map is the most important data structure regarding joins.
        # It's used for recording which joins exist in the query and what
        # types they are. The key is the alias of the joined table (possibly
        # the table name) and the value is a Join-like object (see
        # sql.datastructures.Join for more information).
        self.alias_map = {}
        # Whether to provide alias to columns during reference resolving.
        self.alias_cols = bf
        # Sometimes the query contains references to aliases in outer queries
        # (as a result of split_exclude). Correct alias quoting needs to know
        # these aliases too. Map external tables to whether they are aliased.
        self.external_aliases = {}
        self.table_map = {}  # Maps table names to list of aliases.
        self.used_aliases = set()

        self.where = WhereNode()
        # Maps alias -> Annotation Expression.
        self.annotations = {}
        # These are for extensions. The contents are more or less appended
        # verbatim to the appropriate clause.
        self.extra = {}  # Maps col_alias -> (col_sql, params).

        self._filtered_relations = {}

    @property
    def b(self):
        if len(self.select) == 1:
            bg = self.select[0]
            return getattr(bg, "target", None) or bg.field
        elif len(self.ba) == 1:
            return next(iter(self.ba.values())).output_field

    @cached_property
    def g(self):
        for bh in self.alias_map:
            return bh

    def __str__(self):
        """
        Return the query as a string of SQL with the parameter values
        substituted in (use sql_with_params() to see the unsubstituted string).

        Parameter values won't necessarily be quoted correctly, since that is
        done by the database interface at execution time.
        """
        bi, bj = self.h()
        return bi % bj

    def h(self):
        """
        Return the query as an SQL string and the parameters that will be
        substituted into the query.
        """
        return self.i(DEFAULT_DB_ALIAS).as_sql()

    def __deepcopy__(self, bk):
        """Limit the amount of work when a Query is deepcopied."""
        bl = self.m()
        bk[id(self)] = bl
        return bl

    def i(self, bm=None, bn=None, bo=True):
        if bm is None and bn is None:
            raise ValueError("Need either using or connection")
        if bm:
            bn = connections[bm]
        return bn.ops.compiler(self.compiler)(
            self, bn, bm, bo
        )

    def l(self):
        """
        Return the Options instance (the model._meta) from which to start
        processing. Normally, this is self.model._meta, but it can be changed
        by subclasses.
        """
        if self.model:
            return self.model._meta

    def m(self):
        """
        Return a copy of the current Query. A lightweight alternative to
        deepcopy().
        """
        bp = Empty()
        bp.__class__ = self.__class__
        # Copy references to everything.
        bp.__dict__ = self.__dict__.copy()
        # Clone attributes that can't use shallow copy.
        bp.alias_refcount = self.alias_refcount.copy()
        bp.alias_map = self.alias_map.copy()
        bp.external_aliases = self.external_aliases.copy()
        bp.table_map = self.table_map.copy()
        bp.where = self.where.clone()
        bp.annotations = self.annotations.copy()
        if self.annotation_select_mask is not None:
            bp.annotation_select_mask = self.annotation_select_mask.copy()
        if self.combined_queries:
            bp.combined_queries = tuple(
                [bq.clone() for bq in self.combined_queries]
            )
        # _annotation_select_cache cannot be copied, as doing so breaks the
        # (necessary) state in which both annotations and
        # _annotation_select_cache point to the same underlying objects.
        # It will get re-populated in the cloned queryset the next time it's
        # used.
        bp._annotation_select_cache = None
        bp.extra = self.extra.copy()
        if self.extra_select_mask is not None:
            bp.extra_select_mask = self.extra_select_mask.copy()
        if self._extra_select_cache is not None:
            bp._extra_select_cache = self._extra_select_cache.copy()
        if self.select_related is not False:
            # Use deepcopy because select_related stores fields in nested
            # dicts.
            bp.select_related = copy.deepcopy(bp.select_related)
        if "subq_aliases" in self.__dict__:
            bp.subq_aliases = self.subq_aliases.copy()
        bp.used_aliases = self.used_aliases.copy()
        bp._filtered_relations = self._filtered_relations.copy()
        # Clear the cached_property, if it exists.
        bp.__dict__.pop("base_table", None)
        return bp

    def o(self, br=None):
        """
        Return a copy of the current Query that's ready for another operation.
        The klass argument changes the type of the Query, e.g. UpdateQuery.
        """
        bs = self.m()
        if br and bs.__class__ != br:
            bs.__class__ = br
        if not bs.filter_is_sticky:
            bs.used_aliases = set()
        bs.filter_is_sticky = False
        if hasattr(bs, "_setup_query"):
            bs._setup_query()
        return bs

    def u(self, bt):
        bu = self.m()
        bu.change_aliases(bt)
        return bu

    def x(self, bv, bw, bx):
        if not self.alias_cols:
            bx = None
        return bv.get_col(bx, bw)

    def y(self, by, bz):
        """
        Return the dictionary with the values of the existing aggregations.
        """
        if not bz:
            return {}
        # Store annotation mask prior to temporarily adding aggregations for
        # resolving purpose to facilitate their subsequent removal.
        bA = False
        bB = False
        bC = {}
        bD = self.annotation_select_mask
        for bE, bF in bz.items():
            self.W(bE)
            bG = bF.resolve_expression(
                self, allow_joins=True, reuse=None, summarize=True
            )
            if not bG.contains_aggregate:
                raise TypeError("%s is not an aggregate expression" % bE)
            # Temporarily add aggregate to annotations to allow remaining
            # members of `aggregates` to resolve against each others.
            self.aW([bE])
            bH = bG.get_refs()
            bA |= any(
                getattr(self.annotations[bI], "contains_subquery", False)
                for bI in bH
            )
            bB |= any(
                getattr(self.annotations[bI], "contains_over_clause", True)
                for bI in bH
            )
            bG = bG.replace_expressions(bC)
            self.annotations[bE] = bG
            bC[Ref(bE, bG)] = bG
        # Stash resolved aggregates now that they have been allowed to resolve
        # against each other.
        bJ = {bE: self.annotations.pop(bE) for bE in bz}
        self.aV(bD)
        # Existing usage of aggregation can be determined by the presence of
        # selected aggregates but also by filters against aliased aggregates.
        bK, bL, bM = self.where.split_having_qualify()
        bN = (
            any(
                getattr(bP, "contains_aggregate", True)
                for bP in self.annotations.values()
            )
            or bL
        )
        bO = {
            bE
            for bE, bP in self.ba.items()
            if getattr(bP, "set_returning", False)
        }
        # Decide if we need to use a subquery.
        #
        # Existing aggregations would cause incorrect results as
        # get_aggregation() must produce just one result and thus must not use
        # GROUP BY.
        #
        # If the query has limit or distinct, or uses set operations, then
        # those operations must be done in a subquery so that the query
        # aggregates on the limit and/or distinct results instead of applying
        # the distinct and limit after the aggregation.
        if (
            isinstance(self.group_by, tuple)
            or self.aD
            or bN
            or bA
            or bB
            or bM
            or self.distinct
            or self.combinator
            or bO
        ):
            from django.db.models.sql.subqueries import AggregateQuery

            bQ = self.m()
            bQ.subquery = True
            bR = AggregateQuery(self.model, bQ)
            bQ.select_for_update = False
            bQ.select_related = False
            bQ.set_annotation_mask(self.ba)
            # Queries with distinct_fields need ordering and when a limit is
            # applied we must take the slice from the ordered query. Otherwise
            # no need for ordering.
            if bQ.orderby_issubset_groupby:
                bQ.clear_ordering(force=False)
            if not bQ.distinct:
                # If the inner query uses default select and it has some
                # aggregate annotations, then we must make sure the inner
                # query is grouped by the main model's primary key. However,
                # clearing the select clause can alter results if distinct is
                # used.
                if bQ.default_cols and bN:
                    bQ.group_by = (
                        self.model._meta.pk.get_col(bQ.get_initial_alias()),
                    )
                bQ.default_cols = False
                if not bM and not self.combinator:
                    # Mask existing annotations that are not referenced by
                    # aggregates to be pushed to the outer query unless
                    # filtering against window functions or if the query is
                    # combined as both would require complex realiasing logic.
                    bS = set()
                    if isinstance(self.group_by, tuple):
                        for bT in self.group_by:
                            bS |= bT.get_refs()
                    for bG in bJ.values():
                        bS |= bG.get_refs()
                    # Avoid eliding expressions that might have an incidence on
                    # the implicit grouping logic.
                    for bU, bP in self.ba.items():
                        if bP.get_group_by_cols():
                            bS.add(bU)
                    bQ.set_annotation_mask(bS)
                    # Annotations that possibly return multiple rows cannot
                    # be masked as they might have an incidence on the query.
                    bS |= bO

            # Add aggregates to the outer AggregateQuery. This requires making
            # sure all columns referenced by the aggregates are selected in the
            # inner query. It is achieved by retrieving all column references
            # by the aggregates, explicitly selecting them in the inner query,
            # and making sure the aggregates are repointed to them.
            bV = {}
            for bE, bG in bJ.items():
                bC = {}
                for bW in self.av([bG], resolve_refs=False):
                    if not (bZ := bV.get(bW)):
                        bX = len(bV) + 1
                        bY = f"__col{bX}"
                        bZ = Ref(bY, bW)
                        bV[bW] = bZ
                        bQ.add_annotation(bW, bY)
                    bC[bW] = bZ
                bR.annotations[bE] = bG.replace_expressions(
                    bC
                )
            if (
                bQ.select == ()
                and not bQ.default_cols
                and not bQ.annotation_select_mask
            ):
                # In case of Model.objects[0:3].count(), there would be no
                # field selected in the inner query, yet we must use a
                # subquery. So, make sure at least one field is selected.
                bQ.select = (
                    self.model._meta.pk.get_col(bQ.get_initial_alias()),
                )
        else:
            bR = self
            self.select = ()
            self.selected = None
            self.default_cols = False
            self.extra = {}
            if self.annotations:
                # Inline reference to existing annotations and mask them as
                # they are unnecessary given only the summarized aggregations
                # are requested.
                bC = {
                    Ref(bE, bP): bP
                    for bE, bP in self.annotations.items()
                }
                self.annotations = {
                    bE: bG.replace_expressions(bC)
                    for bE, bG in bJ.items()
                }
            else:
                self.annotations = bJ
            self.aV(bJ)

        ca = [
            cb.empty_result_set_value
            for cb in bR.annotation_select.values()
        ]
        cc = not any(ce is NotImplemented for ce in ca)
        bR.clear_ordering(force=True)
        bR.clear_limits()
        bR.select_for_update = False
        bR.select_related = False
        cd = bR.get_compiler(by, elide_empty=cc)
        ce = cd.execute_sql(SINGLE)
        if ce is None:
            ce = ca
        else:
            cf = bR.annotation_select.values()
            cg = cd.get_converters(cf)
            ch = cd.apply_converters((ce,), cg)
            if cd.has_composite_fields(cf):
                ch = cd.composite_fields_to_tuples(ch, cf)
            ce = next(ch)

        return dict(zip(bR.annotation_select, ce))

    def z(self, ci):
        """
        Perform a COUNT() query using the current filter constraints.
        """
        cj = self.m()
        return cj.get_aggregation(ci, {"__count": Count("*")})["__count"]

    def A(self):
        return self.where

    def B(self, ck=True):
        cl = self.m()
        if not (cl.distinct and cl.is_sliced):
            if cl.group_by is True:
                cl.add_fields(
                    (cm.attname for cm in self.model._meta.concrete_fields), False
                )
                # Disable GROUP BY aliases to avoid orphaning references to the
                # SELECT clause which is about to be cleared.
                cl.set_group_by(allow_aliases=False)
            cl.clear_select_clause()
        if cl.combined_queries and cl.combinator == "union":
            cl.combined_queries = tuple(
                cn.exists(limit=False)
                for cn in cl.combined_queries
            )
        cl.clear_ordering(force=True)
        if ck is True:
            cl.set_limits(high=1)
        cl.add_annotation(Value(1), "a")
        return cl

    def C(self, co):
        cp = self.B()
        cq = cp.get_compiler(using=co)
        return cq.has_results()

    def D(self, cr, cs=None, **ct):
        cu = self.m()
        for cv in ct:
            if (
                not EXPLAIN_OPTIONS_PATTERN.fullmatch(cv)
                or "--" in cv
            ):
                raise ValueError(f"Invalid option name: {cv!r}.")
        cu.explain_info = ExplainInfo(cs, ct)
        cw = cu.get_compiler(using=cr)
        return "\n".join(cw.explain_query())

    def E(self, cx, cy):
        """
        Merge the 'rhs' query into the current one (with any 'rhs' effects
        being applied *after* (that is, "to the right of") anything in the
        current query. 'rhs' is not modified during a call to this function.

        The 'connector' parameter describes how to connect filters from the
        'rhs' query.
        """
        if self.model != cx.model:
            raise TypeError("Cannot combine queries on two different base models.")
        if self.aD:
            raise TypeError("Cannot combine queries once a slice has been taken.")
        if self.distinct != cx.distinct:
            raise TypeError("Cannot combine a unique query with a non-unique query.")
        if self.distinct_fields != cx.distinct_fields:
            raise TypeError("Cannot combine queries with different distinct fields.")

        # If lhs and rhs shares the same alias prefix, it is possible to have
        # conflicting alias changes like T4 -> T5, T5 -> T6, which might end up
        # as T4 -> T6 while combining two querysets. To prevent this, change an
        # alias prefix of the rhs and update current aliases accordingly,
        # except if the alias is the base table since it must be present in the
        # query on both sides.
        cz = self.S()
        cx = cx.clone()
        cx.bump_prefix(self, exclude={cz})

        # Work out how to relabel the rhs aliases, if necessary.
        cA = {}
        cB = cy == AND

        # Determine which existing joins can be reused. When combining the
        # query with AND we must recreate all joins for m2m filters. When
        # combining with OR we can reuse joins. The reason is that in AND
        # case a single row can't fulfill a condition like:
        #     revrel__col=1 & revrel__col=2
        # But, there might be two different related rows matching this
        # condition. In OR case a single True is enough, so single row is
        # enough, too.
        #
        # Note that we will be creating duplicate joins for non-m2m joins in
        # the AND case. The results will be correct but this creates too many
        # joins. This is something that could be fixed later on.
        cC = set() if cB else set(self.alias_map)
        cD = JoinPromoter(cy, 2, False)
        cD.add_votes(
            cE for cE in self.alias_map if self.alias_map[cE].join_type == INNER
        )
        cF = set()
        # Now, add the joins from rhs query into the new query (skipping base
        # table).
        cG = list(cx.alias_map)[1:]
        for cH in cG:
            cI = cx.alias_map[cH]
            # If the left side of the join was already relabeled, use the
            # updated alias.
            cI = cI.relabeled_clone(cA)
            cJ = self.U(cI, reuse=cC)
            if cI.join_type == INNER:
                cF.add(cJ)
            # We can't reuse the same join again in the query. If we have two
            # distinct joins for the same connection in rhs query, then the
            # combined query must have two joins, too.
            cC.discard(cJ)
            if cH != cJ:
                cA[cH] = cJ
            if not cx.alias_refcount[cH]:
                # The alias was unused in the rhs query. Unref it so that it
                # will be unused in the new query, too. We have to add and
                # unref the alias so that join promotion has information of
                # the join type for the unused alias.
                self.L(cJ)
        cD.add_votes(cF)
        cD.update_join_types(self)

        # Combine subqueries aliases to ensure aliases relabelling properly
        # handle subqueries when combining where and select clauses.
        self.subq_aliases |= cx.subq_aliases

        # Now relabel a copy of the rhs where-clause and add it to the current
        # one.
        cK = cx.where.clone()
        cK.relabel_aliases(cA)
        self.where.add(cK, cy)

        # Selection columns and extra extensions are those provided by 'rhs'.
        if cx.select:
            self.aJ([cL.relabeled_clone(cA) for cL in cx.select])
        else:
            self.select = ()

        if cy == OR:
            # It would be nice to be able to handle this, but the queries don't
            # really make sense (or return consistent value sets). Not worth
            # the extra complexity when you can write a real query instead.
            if self.extra and cx.extra:
                raise ValueError(
                    "When merging querysets using 'or', you cannot have "
                    "extra(select=...) on both sides."
                )
        self.extra.update(cx.extra)
        cM = set()
        if self.extra_select_mask is not None:
            cM.update(self.extra_select_mask)
        if cx.extra_select_mask is not None:
            cM.update(cx.extra_select_mask)
        if cM:
            self.aX(cM)
        self.extra_tables += cx.extra_tables

        # Ordering uses the 'rhs' ordering, unless it has none, in which case
        # the current ordering is used.
        self.order_by = cx.order_by or self.order_by
        self.extra_order_by = cx.extra_order_by or self.extra_order_by

    def G(self, cN, cO, cP=None):
        if cP is None:
            cP = {}
        cP[cN.pk] = {}
        # All concrete fields and related objects that are not part of the
        # defer mask must be included. If a relational field is encountered it
        # gets added to the mask for it be considered if `select_related` and
        # the cycle continues by recursively calling this function.
        for cQ in cN.concrete_fields + cN.related_objects:
            cR = cO.pop(cQ.name, None)
            cS = None
            if cT := getattr(cQ, "attname", None):
                cS = cO.pop(cT, None)
            if cR is None and cS is None:
                cP.setdefault(cQ, {})
            elif cR:
                if not cQ.is_relation:
                    raise FieldError(next(iter(cR)))
                # Virtual fields such as many-to-many and generic foreign keys
                # cannot be effectively deferred. Historically, they were
                # allowed to be passed to QuerySet.defer(). Ignore such field
                # references until a layer of validation at mask alteration
                # time is eventually implemented.
                if cQ.many_to_many:
                    continue
                cX = cP.setdefault(cQ, {})
                cY = cQ.related_model._meta.concrete_model
                self.G(
                    cY._meta, cR, cX
                )
        # Remaining defer entries must be references to filtered relations
        # otherwise they are surfaced as missing field errors.
        for cU, cR in cO.items():
            if cV := self._filtered_relations.get(cU):
                cW = cN.get_field(cV.relation_name)
                cX = cP.setdefault((cU, cW), {})
                cY = cW.related_model._meta.concrete_model
                self.G(
                    cY._meta, cR, cX
                )
            else:
                cN.get_field(cU)
        return cP

    def H(self, cZ, da, db=None):
        if db is None:
            db = {}
        db[cZ.pk] = {}
        # Only include fields mentioned in the mask.
        for dc, dd in da.items():
            de = cZ.get_field(dc)
            df = db.setdefault(de, {})
            if dd:
                if not de.is_relation:
                    raise FieldError(next(iter(dd)))
                dg = de.remote_field.model._meta.concrete_model
                self.H(
                    dg._meta, dd, df
                )
        return db

    def I(self):
        """
        Convert the self.deferred_loading data structure to an alternate data
        structure, describing the field that *will* be loaded. This is used to
        compute the columns to select from the database and also by the
        QuerySet class to work out which fields are being initialized on each
        model. Models that have all their fields included aren't mentioned in
        the result, only those that have field restrictions in place.
        """
        dh, di = self.deferred_loading
        if not dh:
            return {}
        dj = {}
        for dk in dh:
            dl = dj
            for dm in dk.split(LOOKUP_SEP):
                dl = dl.setdefault(dm, {})
        dn = self.l()
        if di:
            return self.G(dn, dj)
        return self.H(dn, dj)

    def J(self, do, dp=False, dq=None):
        """
        Return a table alias for the given table_name and whether this is a
        new alias or not.

        If 'create' is true, a new alias is always created. Otherwise, the
        most recently created alias for the table (if one exists) is reused.
        """
        dr = self.table_map.get(do)
        if not dp and dr:
            ds = dr[0]
            self.alias_refcount[ds] += 1
            return ds, False

        # Create a new alias for this table.
        if dr:
            ds = "%s%d" % (self.alias_prefix, len(self.alias_map) + 1)
            dr.append(ds)
        else:
            # The first occurrence of a table uses the table name directly.
            ds = (
                dq.alias if dq is not None else do
            )
            self.table_map[do] = [ds]
        self.alias_refcount[ds] = 1
        return ds, True

    def K(self, dt):
        """Increases the reference count for this alias."""
        self.alias_refcount[dt] += 1

    def L(self, du, dv=1):
        """Decreases the reference count for this alias."""
        self.alias_refcount[du] -= dv

    def M(self, dw):
        """
        Promote recursively the join type of given aliases and its children to
        an outer join. If 'unconditional' is False, only promote the join if
        it is nullable or the parent join is an outer join.

        The children promotion is done to avoid join chains that contain a
        LOUTER b INNER c. So, if we have currently a INNER b INNER c and a->b
        is promoted, then we must also promote b->c automatically, or otherwise
        the promotion of a->b doesn't actually change anything in the query
        results.
        """
        dw = list(dw)
        while dw:
            dx = dw.pop(0)
            if self.alias_map[dx].join_type is None:
                # This is the base table (first FROM entry) - this table
                # isn't really joined at all in the query, so we should not
                # alter its join type.
                continue
            # Only the first alias (skipped above) should have None join_type
            assert self.alias_map[dx].join_type is not None
            dy = self.alias_map[dx].parent_alias
            dz = (
                dy and self.alias_map[dy].join_type == LOUTER
            )
            dA = self.alias_map[dx].join_type == LOUTER
            if (self.alias_map[dx].nullable or dz) and not dA:
                self.alias_map[dx] = self.alias_map[dx].promote()
                # Join type of 'alias' changed, so re-examine all aliases that
                # refer to this one.
                dw.extend(
                    dB
                    for dB in self.alias_map
                    if self.alias_map[dB].parent_alias == dx
                    and dB not in dw
                )

    def N(self, dC):
        """
        Change join type from LOUTER to INNER for all joins in aliases.

        Similarly to promote_joins(), this method must ensure no join chains
        containing first an outer, then an inner join are generated. If we
        are demoting b->c join in chain a LOUTER b LOUTER c then we must
        demote a->b automatically, or otherwise the demotion of b->c doesn't
        actually change anything in the query results. .
        """
        dC = list(dC)
        while dC:
            dD = dC.pop(0)
            if self.alias_map[dD].join_type == LOUTER:
                self.alias_map[dD] = self.alias_map[dD].demote()
                dE = self.alias_map[dD].parent_alias
                if self.alias_map[dE].join_type == INNER:
                    dC.append(dE)

    def O(self, dF):
        """
        Reset reference counts for aliases so that they match the value passed
        in `to_counts`.
        """
        for dG, dH in self.alias_refcount.copy().items():
            dI = dH - dF.get(dG, 0)
            self.L(dG, dI)

    def P(self, dJ):
        """
        Change the aliases in change_map (which maps old-alias -> new-alias),
        relabelling any references to them in select columns and the where
        clause.
        """
        if not dJ:
            return self
        # If keys and values of change_map were to intersect, an alias might be
        # updated twice (e.g. T4 -> T5, T5 -> T6, so also T4 -> T6) depending
        # on their order in change_map.
        assert set(dJ).isdisjoint(dJ.values())

        # 1. Update references in "select" (normal columns plus aliases),
        # "group by" and "where".
        self.where.relabel_aliases(dJ)
        if isinstance(self.group_by, tuple):
            self.group_by = tuple(
                [dK.relabeled_clone(dJ) for dK in self.group_by]
            )
        self.select = tuple([dK.relabeled_clone(dJ) for dK in self.select])
        self.annotations = self.annotations and {
            dL: dK.relabeled_clone(dJ)
            for dL, dK in self.annotations.items()
        }

        # 2. Rename the alias in the internal table/alias datastructures.
        for dM, dN in dJ.items():
            if dM not in self.alias_map:
                continue
            dO = self.alias_map[dM].relabeled_clone(dJ)
            self.alias_map[dN] = dO
            self.alias_refcount[dN] = self.alias_refcount[dM]
            del self.alias_refcount[dM]
            del self.alias_map[dM]

            dP = self.table_map[dO.table_name]
            for dQ, dR in enumerate(dP):
                if dR == dM:
                    dP[dQ] = dN
                    break

        # 3. Rename the direct external aliases and the ones of combined
        # queries (union, intersection, difference).
        self.external_aliases = {
            # Table is aliased or it's being changed and thus is aliased.
            dJ.get(dR, dR): (dS or dR in dJ)
            for dR, dS in self.external_aliases.items()
        }
        for dT in self.combined_queries:
            dU = {
                dR: dS
                for dR, dS in dJ.items()
                if dR in dT.external_aliases
            }
            dT.change_aliases(dU)

    def R(self, dV, dW=None):
        """
        Change the alias prefix to the next letter in the alphabet in a way
        that the other query's aliases and this query's aliases will not
        conflict. Even tables that previously had no alias will get an alias
        after this call. To prevent changing aliases use the exclude parameter.
        """

        def prefix_gen():
            """
            Generate a sequence of characters in alphabetical order:
                -> 'A', 'B', 'C', ...

            When the alphabet is finished, the sequence will continue with the
            Cartesian product:
                -> 'AA', 'AB', 'AC', ...
            """
            eb = ascii_uppercase
            ec = chr(ord(self.alias_prefix) + 1)
            yield ec
            for ed in count(1):
                ee = eb[eb.index(ec) :] if ec else eb
                for ef in product(ee, repeat=ed):
                    yield "".join(ef)
                ec = None

        if self.alias_prefix != dV.alias_prefix:
            # No clashes between self and outer query should be possible.
            return

        # Explicitly avoid infinite loop. The constant divider is based on how
        # much depth recursive subquery references add to the stack. This value
        # might need to be adjusted when adding or removing function calls from
        # the code path in charge of performing these operations.
        dX = sys.getrecursionlimit() // 16
        for dY, dZ in enumerate(prefix_gen()):
            if dZ not in self.subq_aliases:
                self.alias_prefix = dZ
                break
            if dY > dX:
                raise RecursionError(
                    "Maximum recursion depth exceeded: too many subqueries."
                )
        self.subq_aliases = self.subq_aliases.union([self.alias_prefix])
        dV.subq_aliases = dV.subq_aliases.union(self.subq_aliases)
        if dW is None:
            dW = {}
        self.P(
            {
                ea: "%s%d" % (self.alias_prefix, dY)
                for dY, ea in enumerate(self.alias_map)
                if ea not in dW
            }
        )

    def S(self):
        """
        Return the first alias for this query, after increasing its reference
        count.
        """
        if self.alias_map:
            eg = self.g
            self.K(eg)
        elif self.model:
            eg = self.U(self.base_table_class(self.l().db_table, None))
        else:
            eg = None
        return eg

    def T(self):
        """
        Return the number of tables in this query with a non-zero reference
        count. After execution, the reference counts are zeroed, so tables
        added in compiler will not be seen by this method.
        """
        return len([1 for eh in self.alias_refcount.values() if eh])

    def U(self, ei, ej=None):
        """
        Return an alias for the 'join', either reusing an existing alias for
        that join or creating a new one. 'join' is either a base_table_class or
        join_class.

        The 'reuse' parameter can be either None which means all joins are
        reusable, or it can be a set containing the aliases that can be reused.

        A join is always created as LOUTER if the lhs alias is LOUTER to make
        sure chains like t1 LOUTER t2 INNER t3 aren't generated. All new
        joins are created as LOUTER if the join is nullable.
        """
        ek = [
            el
            for el, em in self.alias_map.items()
            if (ej is None or el in ej) and em == ei
        ]
        if ek:
            if ei.table_alias in ek:
                en = ei.table_alias
            else:
                # Reuse the most recent alias of the joined table
                # (a many-to-many relation may be joined multiple times).
                en = ek[-1]
            self.K(en)
            return en

        # No reuse is possible, so we need a new alias.
        eo, ep = self.J(
            ei.table_name, create=True, filtered_relation=ei.filtered_relation
        )
        if ei.join_type:
            if self.alias_map[ei.parent_alias].join_type == LOUTER or ei.nullable:
                eq = LOUTER
            else:
                eq = INNER
            ei.join_type = eq
        ei.table_alias = eo
        self.alias_map[eo] = ei
        if er := ei.filtered_relation:
            es = ej
            if es is not None:
                es = set(ej) | {eo}
            et = len(self.alias_map)
            ei.filtered_relation = er.resolve_expression(
                self, reuse=es
            )
            # Some joins were during expression resolving, they must be present
            # before the one we just added.
            if et < len(self.alias_map):
                self.alias_map[eo] = self.alias_map.pop(eo)
        return eo

    def V(self, eu, ev, ew, ex):
        """
        Make sure the given 'model' is joined in the query. If 'model' isn't
        a parent of 'opts' or if it is None this method is a no-op.

        The 'alias' is the root alias for starting the join, 'seen' is a dict
        of model -> alias of existing joins. It must also contain a mapping
        of None -> some alias. This will be returned in the no-op case.
        """
        if ev in ex:
            return ex[ev]
        ey = eu.get_base_chain(ev)
        if not ey:
            return ew
        ez = eu
        for eA in ey:
            if eA in ex:
                ez = eA._meta
                ew = ex[eA]
                continue
            # Proxy model have elements in base chain
            # with no parents, assign the new options
            # object and skip to the next base in that
            # case
            if not ez.parents[eA]:
                ez = eA._meta
                continue
            eB = ez.get_ancestor_link(eA)
            eC = self.at([eB.name], ez, ew)
            ez = eA._meta
            ew = ex[eA] = eC.joins[-1]
        return ew or ex[None]

    def W(self, eD):
        # RemovedInDjango70Warning: When the deprecation ends, remove.
        if "%" in eD:
            warnings.warn(
                "Using percent signs in a column alias is deprecated.",
                category=RemovedInDjango70Warning,
                skip_file_prefixes=django_file_prefixes(),
            )
        if FORBIDDEN_ALIAS_PATTERN.search(eD):
            raise ValueError(
                "Column aliases cannot contain whitespace characters, hashes, "
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # "control characters, quotation marks, semicolons, percent "
                # "signs, or SQL comments."
                "control characters, quotation marks, semicolons, or SQL comments."
            )

    def X(self, eE, eF, eG=True):
        """Add a single annotation expression to the Query."""
        self.W(eF)
        eE = eE.resolve_expression(self, allow_joins=True, reuse=None)
        if eG:
            self.aW([eF])
        else:
            self.aV(set(self.ba).difference({eF}))
        self.annotations[eF] = eE
        if eG and self.selected:
            self.selected[eF] = eF

    @property
    def Y(self):
        if not self.aY or not self.select:
            return len(self.model._meta.pk_fields)
        return len(self.select) + sum(
            len(eH.targets) - 1 for eH in self.select if isinstance(eH, ColPairs)
        )

    def Z(self, eI, *eJ, **eK):
        eL = self.m()
        # Subqueries need to use a different set of aliases than the outer
        # query.
        eL.bump_prefix(eI)
        eL.subquery = True
        eL.where.resolve_expression(eI, *eJ, **eK)
        # Resolve combined queries.
        if eL.combinator:
            eL.combined_queries = tuple(
                [
                    eM.resolve_expression(eI, *eJ, **eK)
                    for eM in eL.combined_queries
                ]
            )
        for eN, eO in eL.annotations.items():
            eP = eO.resolve_expression(eI, *eJ, **eK)
            if hasattr(eP, "external_aliases"):
                eP.external_aliases.update(eL.external_aliases)
            eL.annotations[eN] = eP
        # Outer query's aliases are considered external.
        for eQ, eR in eI.alias_map.items():
            eL.external_aliases[eQ] = (
                isinstance(eR, Join)
                and eR.join_field.related_model._meta.db_table != eQ
            ) or (
                isinstance(eR, BaseTable) and eR.table_name != eR.table_alias
            )
        return eL

    def aa(self):
        eS = chain(self.annotations.values(), self.where.children)
        return [
            eT
            for eT in self.av(eS, include_external=True)
            if eT.alias in self.external_aliases
        ]

    def ab(self, eU=None):
        # If wrapper is referenced by an alias for an explicit GROUP BY through
        # values() a reference to this expression and not the self must be
        # returned to ensure external column references are not grouped against
        # as well.
        eV = self.aa()
        if any(eW.possibly_multivalued for eW in eV):
            return [eU or self]
        return eV

    def ac(self, eX, eY):
        # Some backends (e.g. Oracle) raise an error when a subquery contains
        # unnecessary ORDER BY clause.
        if (
            self.subquery
            and not eY.features.ignores_unnecessary_order_by_in_subqueries
        ):
            self.aO(force=False)
            for eZ in self.combined_queries:
                eZ.clear_ordering(force=False)
        fa, fb = self.i(connection=eY).as_sql()
        if self.subquery:
            fa = "(%s)" % fa
        return fa, fb

    def ad(self, fc, fd, fe, ff=False):
        if hasattr(fc, "resolve_expression"):
            fc = fc.resolve_expression(
                self,
                reuse=fd,
                allow_joins=fe,
                summarize=ff,
            )
        elif isinstance(fc, (list, tuple)):
            # The items of the iterable may be expressions and therefore need
            # to be resolved independently.
            fg = (
                self.ad(fh, fd, fe, ff)
                for fh in fc
            )
            fi = type(fc)
            if hasattr(fi, "_make"):  # namedtuple
                return fi(*fg)
            return fi(fg)
        return fc

    def ae(self, fj, fk=False):
        """
        Solve the lookup type from the lookup (e.g.: 'foobar__id__icontains').
        """
        fl = fj.split(LOOKUP_SEP)
        if self.annotations:
            fm, fn = refs_expression(
                fl, self.annotations
            )
            if fm:
                fo = self.annotations[fm]
                if fk:
                    fo = Ref(fm, fo)
                return fn, (), fo
        fp, fq, fp, fr = self.ar(fl, self.l())
        fs = fl[0 : len(fl) - len(fr)]
        if len(fr) > 1 and not fs:
            raise FieldError(
                'Invalid lookup "%s" for model %s".'
                % (fj, self.l().model.__name__)
            )
        return fr, fs, False

    def af(self, ft, fu, fv):
        """
        Check whether the object passed while querying is of the correct type.
        If not, raise a ValueError specifying the wrong object.
        """
        if hasattr(ft, "_meta"):
            if not check_rel_lookup_compatibility(ft._meta.model, fu, fv):
                raise ValueError(
                    'Cannot query "%s": Must be "%s" instance.'
                    % (ft, fu.object_name)
                )

    def ag(self, fw, fx, fy):
        """Check the type of object passed to query relations."""
        if fw.is_relation:
            # Check that the field and the queryset use the same model in a
            # query like .filter(author=Author.objects.all()). For example, the
            # opts would be Author's (from the author field) and value.model
            # would be Author.objects.all() queryset's .model (Author also).
            # The field is the related field on the lhs side.
            if (
                isinstance(fx, Query)
                and not fx.has_select_fields
                and not check_rel_lookup_compatibility(fx.model, fy, fw)
            ):
                raise ValueError(
                    'Cannot use QuerySet for "%s": Use a QuerySet for "%s".'
                    % (fx.model._meta.object_name, fy.object_name)
                )
            elif hasattr(fx, "_meta"):
                self.af(fx, fy, fw)
            elif hasattr(fx, "__iter__"):
                for fz in fx:
                    self.af(fz, fy, fw)

    def ah(self, fA):
        """Raise an error if expression cannot be used in a WHERE clause."""
        if hasattr(fA, "resolve_expression") and not getattr(
            fA, "filterable", True
        ):
            raise NotSupportedError(
                fA.__class__.__name__ + " is disallowed in the filter "
                "clause."
            )
        if hasattr(fA, "get_source_expressions"):
            for fB in fA.get_source_expressions():
                self.ah(fB)

    def ai(self, fC, fD, fE):
        """
        Try to extract transforms and lookup from given lhs.

        The lhs value is something that works like SQLExpression.
        The rhs value is what the lookup is going to compare against.
        The lookups is a list of names to extract using get_lookup()
        and get_transform().
        """
        # __exact is the default lookup if one isn't given.
        *fF, fG = fC or ["exact"]
        for fH in fF:
            fD = self.aj(fD, fH, fC)
        # First try get_lookup() so that the lookup takes precedence if the lhs
        # supports both transform and lookup for the name.
        fI = fD.get_lookup(fG)
        if not fI:
            # A lookup wasn't found. Try to interpret the name as a transform
            # and do an Exact lookup against it.
            fD = self.aj(fD, fG)
            fG = "exact"
            fI = fD.get_lookup(fG)
            if not fI:
                return

        fJ = fI(fD, fE)
        # Interpret '__exact=None' as the sql 'is NULL'; otherwise, reject all
        # uses of None as a query value unless the lookup supports it.
        if fJ.rhs is None and not fJ.can_use_none_as_rhs:
            if fG not in ("exact", "iexact"):
                raise ValueError("Cannot use None as a query value")
            return fD.get_lookup("isnull")(fD, True)

        # For Oracle '' is equivalent to null. The check must be done at this
        # stage because join promotion can't be done in the compiler. Using
        # DEFAULT_DB_ALIAS isn't nice but it's the best that can be done here.
        # A similar thing is done in is_nullable(), too.
        if (
            fG in ("exact", "iexact")
            and fJ.rhs == ""
            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
        ):
            return fD.get_lookup("isnull")(fD, True)

        return fJ

    def aj(self, fK, fL, fM=None):
        """
        Helper method for build_lookup(). Try to fetch and initialize
        a transform for name parameter from lhs.
        """
        fN = fK.get_transform(fL)
        if fN:
            return fN(fK)
        else:
            fO = fK.output_field.__class__
            fP = difflib.get_close_matches(
                fL, fK.output_field.get_lookups()
            )
            if fP:
                fQ = ", perhaps you meant %s?" % " or ".join(fP)
            else:
                fQ = "."
            if fM is not None:
                fR = fM.index(fL)
                fS = LOOKUP_SEP.join(fM[fR:])
            else:
                fS = fL
            raise FieldError(
                "Unsupported lookup '%s' for %s or join on the field not "
                "permitted%s" % (fS, fO.__name__, fQ)
            )

    def ak(
        self,
        fT,
        fU=False,
        fV=False,
        fW=None,
        fX=True,
        fY=True,
        fZ=True,
        ga=False,
        gb=True,
    ):
        """
        Build a WhereNode for a single filter clause but don't add it
        to this Query. Query.add_q() will then add this filter to the where
        Node.

        The 'branch_negated' tells us if the current branch contains any
        negations. This will be used to determine if subqueries are needed.

        The 'current_negated' is used to determine if the current filter is
        negated or not and this will be used to determine if IS NULL filtering
        is needed.

        The difference between current_negated and branch_negated is that
        branch_negated is set on first negation, but current_negated is
        flipped for each negation.

        Note that add_filter will not do any negating itself, that is done
        upper in the code by add_q().

        The 'can_reuse' is a set of reusable joins for multijoins.

        The method will create a filter clause that can be added to the current
        query. However, if the filter isn't added to the query then the caller
        is responsible for unreffing the joins used.
        """
        if isinstance(fT, dict):
            raise FieldError("Cannot parse keyword query as dict")
        if isinstance(fT, Q):
            return self.ap(
                fT,
                branch_negated=fU,
                current_negated=fV,
                used_aliases=fW,
                allow_joins=fX,
                split_subq=fY,
                check_filterable=fZ,
                summarize=ga,
                update_join_types=gb,
            )
        if hasattr(fT, "resolve_expression"):
            if not getattr(fT, "conditional", False):
                raise TypeError("Cannot filter against a non-conditional expression.")
            gs = fT.resolve_expression(
                self, allow_joins=fX, reuse=fW, summarize=ga
            )
            if not isinstance(gs, Lookup):
                gs = self.ai(["exact"], gs, True)
            return WhereNode([gs], connector=AND), []
        gc, gh = fT
        if not gc:
            raise FieldError("Cannot parse keyword query %r" % gc)
        gd, ge, gf = self.ae(gc, ga)

        if fZ:
            self.ah(gf)

        if not fX and len(ge) > 1:
            raise FieldError("Joined field references are not permitted in this query")

        gg = self.alias_refcount.copy()
        gh = self.ad(gh, fW, fX, ga)
        gi = {
            gj for gj, gk in self.alias_refcount.items() if gk > gg.get(gj, 0)
        }

        if fZ:
            self.ah(gh)

        if gf:
            gs = self.ai(gd, gf, gh)
            return WhereNode([gs], connector=AND), []

        gl = self.l()
        gm = self.S()
        gn = not fU or not fY

        try:
            go = self.at(
                ge,
                gl,
                gm,
                can_reuse=fW,
                allow_many=gn,
            )

            # Prevent iterator from being consumed by check_related_objects()
            if isinstance(gh, Iterator):
                gh = list(gh)
            self.ag(go.final_field, gh, go.opts)

            # split_exclude() needs to know which joins were generated for the
            # lookup parts
            self._lookup_joins = go.joins
        except MultiJoin as e:
            return self.ay(fT, fW, e.names_with_path)

        # Update used_joins before trimming since they are reused to determine
        # which joins could be later promoted to INNER.
        gi.update(go.joins)
        gp, gm, gq = self.au(
            go.targets, go.joins, go.path
        )
        if fW is not None:
            fW.update(gq)

        if go.final_field.is_relation:
            if len(gp) == 1:
                gr = self.x(gp[0], go.final_field, gm)
            else:
                gr = ColPairs(gm, gp, go.targets, go.final_field)
        else:
            gr = self.x(gp[0], go.final_field, gm)

        gs = self.ai(gd, gr, gh)
        gt = gs.lookup_name
        gu = WhereNode([gs], connector=AND)

        gv = (
            gt == "isnull" and gs.rhs is True and not fV
        )
        if (
            fV
            and (gt != "isnull" or gs.rhs is False)
            and gs.rhs is not None
        ):
            gv = True
            if gt != "isnull":
                # The condition added here will be SQL like this:
                # NOT (col IS NOT NULL), where the first NOT is added in
                # upper layers of code. The reason for addition is that if col
                # is null, then col != someval will result in SQL "unknown"
                # which isn't the same as in Python. The Python None handling
                # is wanted, and it can be gotten by
                # (col IS NULL OR col != someval)
                #   <=>
                # NOT (col IS NOT NULL AND col = someval).
                if (
                    self.bd(gp[0])
                    or self.alias_map[gq[-1]].join_type == LOUTER
                ):
                    gw = gp[0].get_lookup("isnull")
                    gr = self.x(gp[0], go.targets[0], gm)
                    # Use OR + IS NULL when RHS `in` values include None.
                    if (
                        gt == "in"
                        # Check containers (not strings or bytes).
                        and isinstance(gs.rhs, Iterable)
                        and not isinstance(gs.rhs, (str, bytes))
                        and any(gk is None for gk in gs.rhs)
                    ):
                        gu.add(gw(gr, True), OR)
                    else:
                        gu.add(gw(gr, False), AND)
                # If someval is a nullable column, someval IS NOT NULL is
                # added.
                if isinstance(gh, Col) and self.bd(gh.target):
                    gw = gh.target.get_lookup("isnull")
                    gu.add(gw(gh, False), AND)
        return gu, gi if not gv else ()

    def al(self, gx, gy):
        self.am(Q((gx, gy)))

    def am(self, gz, gA=False):
        """
        A preprocessor for the internal _add_q(). Responsible for doing final
        join promotion.
        """
        # For join promotion this case is doing an AND for the added q_object
        # and existing conditions. So, any existing inner join forces the join
        # type to remain inner. Existing outer joins can however be demoted.
        # (Consider case where rel_a is LOUTER and rel_a__col=1 is added - if
        # rel_a doesn't produce any rows, then the whole condition must fail.
        # So, demotion is OK.
        gB = {
            gC for gC in self.alias_map if self.alias_map[gC].join_type == INNER
        }
        if gA:
            gD = set(self.alias_map)
        else:
            gD = self.used_aliases
        gE, gF = self.ap(gz, gD)
        if gE:
            self.where.add(gE, AND)
        self.N(gB)

    def an(self, gG):
        return self.ak(gG, allow_joins=False)[0]

    def ao(self):
        self.where = WhereNode()

    def ap(
        self,
        gH,
        gI,
        gJ=False,
        gK=False,
        gL=True,
        gM=True,
        gN=True,
        gO=False,
        gP=True,
    ):
        """Add a Q-object to the current filter."""
        gQ = gH.connector
        gK ^= gH.negated
        gJ = gJ or gH.negated
        gR = WhereNode(connector=gQ, negated=gH.negated)
        gS = JoinPromoter(
            gH.connector, len(gH.children), gK
        )
        for gT in gH.children:
            gU, gV = self.ak(
                gT,
                can_reuse=gI,
                branch_negated=gJ,
                current_negated=gK,
                allow_joins=gL,
                split_subq=gM,
                check_filterable=gN,
                summarize=gO,
                update_join_types=gP,
            )
            gS.add_votes(gV)
            if gU:
                gR.add(gU, gQ)
        if gP:
            gV = gS.update_join_types(self)
        else:
            gV = []
        return gR, gV

    def aq(self, gW, gX):
        if "." in gX:
            raise ValueError(
                "FilteredRelation doesn't support aliases with periods "
                "(got %r)." % gX
            )
        self.W(gX)
        gW.alias = gX
        gY, gZ, ha = self.ae(
            gW.relation_name
        )
        if gY:
            raise ValueError(
                "FilteredRelation's relation_name cannot contain lookups "
                "(got %r)." % gW.relation_name
            )
        for hb in get_children_from_q(gW.condition):
            hc, hd, ha = self.ae(hb)
            he = 2 if not hc else 1
            hf = hd[:-he]
            for hg, hh in enumerate(hf):
                if len(gZ) > hg:
                    if gZ[hg] != hh:
                        raise ValueError(
                            "FilteredRelation's condition doesn't support "
                            "relations outside the %r (got %r)."
                            % (gW.relation_name, hb)
                        )
            if len(hd) > len(gZ) + 1:
                raise ValueError(
                    "FilteredRelation's condition doesn't support nested "
                    "relations deeper than the relation_name (got %r for "
                    "%r)." % (hb, gW.relation_name)
                )
        gW = gW.clone()
        gW.condition = rename_prefix_from_q(
            gW.relation_name,
            gX,
            gW.condition,
        )
        self._filtered_relations[gW.alias] = gW

    def ar(self, hi, hj, hk=True, hl=False):
        """
        Walk the list of names and turns them into PathInfo tuples. A single
        name in 'names' can generate multiple PathInfos (m2m, for example).

        'names' is the path of names to travel, 'opts' is the model Options we
        start the name resolving from, 'allow_many' is as for setup_joins().
        If fail_on_missing is set to True, then a name that can't be resolved
        will generate a FieldError.

        Return a list of PathInfo tuples. In addition return the final field
        (the last used join field) and target (which is a field guaranteed to
        contain the same value as the final field). Finally, return those names
        that weren't found (which are likely transforms and the final lookup).
        """
        hm, hn = [], []
        for ho, hp in enumerate(hi):
            hq = (hp, [])
            if hp == "pk" and hj is not None:
                hp = hj.pk.name

            hr = None
            hs = None
            try:
                if hj is None:
                    raise FieldDoesNotExist
                hr = hj.get_field(hp)
            except FieldDoesNotExist:
                if hp in self.annotations:
                    hr = self.annotations[hp].output_field
                elif hp in self._filtered_relations and ho == 0:
                    hs = self._filtered_relations[hp]
                    if LOOKUP_SEP in hs.relation_name:
                        ht = hs.relation_name.split(LOOKUP_SEP)
                        hu, hr, hv, hv = self.ar(
                            ht,
                            hj,
                            hk,
                            hl,
                        )
                        hm.extend(hu[:-1])
                    else:
                        hr = hj.get_field(hs.relation_name)
            if hr is not None:
                # Fields that contain one-to-many relations with a generic
                # model (like a GenericForeignKey) cannot generate reverse
                # relations and therefore cannot be used for reverse querying.
                if hr.is_relation and not hr.related_model:
                    raise FieldError(
                        "Field %r does not generate an automatic reverse "
                        "relation and therefore cannot be used for reverse "
                        "querying. If it is a GenericForeignKey, consider "
                        "adding a GenericRelation." % hp
                    )
                try:
                    hw = hr.model._meta.concrete_model
                except AttributeError:
                    # QuerySet.annotate() may introduce fields that aren't
                    # attached to a model.
                    hw = None
            else:
                # We didn't find the current field, so move position back
                # one step.
                ho -= 1
                if ho == -1 or hl:
                    hx = sorted(
                        [
                            *get_field_names_from_opts(hj),
                            *self.annotations,
                            *self._filtered_relations,
                        ]
                    )
                    raise FieldError(
                        "Cannot resolve keyword '%s' into field. "
                        "Choices are: %s" % (hp, ", ".join(hx))
                    )
                break
            # Check if we need any joins for concrete inheritance cases (the
            # field lives in parent, but we are currently in one of its
            # children)
            if hj is not None and hw is not hj.model:
                hy = hj.get_path_to_parent(hw)
                if hy:
                    hm.extend(hy)
                    hq[1].extend(hy)
                    hj = hy[-1].to_opts
            if hasattr(hr, "path_infos"):
                if hs:
                    hz = hr.get_path_info(hs)
                else:
                    hz = hr.path_infos
                if not hk:
                    for hA, hB in enumerate(hz):
                        if hB.m2m:
                            hq[1].extend(hz[0 : hA + 1])
                            hn.append(hq)
                            raise MultiJoin(ho + 1, hn)
                hC = hz[-1]
                hm.extend(hz)
                hD = hC.join_field
                hj = hC.to_opts
                hE = hC.target_fields
                hq[1].extend(hz)
                hn.append(hq)
            else:
                # Local non-relational field.
                hD = hr
                hE = (hr,)
                if hl and ho + 1 != len(hi):
                    raise FieldError(
                        "Cannot resolve keyword %r into field. Join on '%s'"
                        " not permitted." % (hi[ho + 1], hp)
                    )
                break
        return hm, hD, hE, hi[ho + 1 :]

    def at(
        self,
        hF,
        hG,
        hH,
        hI=None,
        hJ=True,
    ):
        """
        Compute the necessary table joins for the passage through the fields
        given in 'names'. 'opts' is the Options class for the current model
        (which gives the table we are starting from), 'alias' is the alias for
        the table to start the joining from.

        The 'can_reuse' defines the reverse foreign key joins we can reuse. It
        can be None in which case all joins are reusable or a set of aliases
        that can be reused. Note that non-reverse foreign keys are always
        reusable when using setup_joins().

        If 'allow_many' is False, then any reverse foreign key seen will
        generate a MultiJoin exception.

        Return the final field involved in the joins, the target field (used
        for any 'where' constraint), the final 'opts' value, the joins, the
        field path traveled to generate the joins, and a transform function
        that takes a field and alias and is equivalent to
        `field.get_col(alias)` in the simple case but wraps field transforms if
        they were included in names.

        The target field is the field containing the concrete value. Final
        field can be something different, for example foreign key pointing to
        that value. Final field is needed for example in some value
        conversions (convert 'obj' in fk__id=obj to pk val using the foreign
        key field for example).
        """
        hK = [hH]
        # The transform can't be applied yet, as joins must be trimmed later.
        # To avoid making every caller of this method look up transforms
        # directly, compute transforms here and create a partial that converts
        # fields to the appropriate wrapped version.

        def final_transformer(ia, ib):
            if not self.alias_cols:
                ib = None
            return ia.get_col(ib)

        # Try resolving all the names as fields first. If there's an error,
        # treat trailing names as lookups until a field can be resolved.
        hL = None
        for hM in range(len(hF), 0, -1):
            try:
                hN, hO, hP, hQ = self.ar(
                    hF[:hM],
                    hG,
                    hJ,
                    fail_on_missing=True,
                )
            except FieldError as exc:
                if hM == 1:
                    # The first item cannot be a lookup, so it's safe
                    # to raise the field error here.
                    raise
                else:
                    hL = exc
            else:
                # The transforms are the remaining items that couldn't be
                # resolved into fields.
                hR = hF[hM:]
                break
        for hS in hR:

            def transform(ic, ie, *, ig, ih):
                try:
                    ii = ih(ic, ie)
                    return self.aj(ii, ig)
                except FieldError:
                    # FieldError is raised if the transform doesn't exist.
                    if isinstance(final_field, Field) and last_field_exception:
                        raise last_field_exception
                    else:
                        raise

            hT = functools.partial(
                transform, name=hS, previous=hT
            )
            hT.has_transforms = True
        # Then, add the path to the query's joins. Note that we can't trim
        # joins at this stage - we will need the information about join type
        # of the trimmed joins.
        for hU in hN:
            if hU.filtered_relation:
                hV = hU.filtered_relation.clone()
                hW = hV.alias
            else:
                hV = None
                hW = None
            hG = hU.to_opts
            if hU.direct:
                hX = self.bd(hU.join_field)
            else:
                hX = True
            hY = self.join_class(
                hG.db_table,
                hH,
                hW,
                INNER,
                hU.join_field,
                hX,
                filtered_relation=hV,
            )
            hZ = hI if hU.m2m else None
            hH = self.U(hY, reuse=hZ)
            hK.append(hH)
            if hU.filtered_relation and hI is not None:
                hI.add(hH)
        return JoinInfo(hO, hP, hG, hK, hN, hT)

    def au(self, ij, ik, il):
        """
        The 'target' parameter is the final field being joined to, 'joins'
        is the full list of join aliases. The 'path' contain the PathInfos
        used to create the joins.

        Return the final target field and table alias and the new active
        joins.

        Always trim any direct join if the target column is already in the
        previous table. Can't trim reverse joins as it's unknown if there's
        anything on the other side of the join.
        """
        ik = ik[:]
        for im, io in enumerate(reversed(il)):
            if len(ik) == 1 or not io.direct:
                break
            if io.filtered_relation:
                break
            ip = {iq.column for iq in io.join_field.foreign_related_fields}
            ir = {iq.column for iq in ij}
            if not ir.issubset(ip):
                break
            it = {
                iu[1].column: iu[0]
                for iu in io.join_field.related_fields
                if iu[1].column in ir
            }
            ij = tuple(it[iq.column] for iq in ij)
            self.L(ik.pop())
        return ij, ik[-1], ik

    @classmethod
    def av(cls, iv, iw=False, ix=True):
        for iy in iv:
            if isinstance(iy, Col):
                yield iy
            elif iw and callable(
                getattr(iy, "get_external_cols", None)
            ):
                yield from iy.get_external_cols()
            elif hasattr(iy, "get_source_expressions"):
                if not ix and isinstance(iy, Ref):
                    continue
                yield from cls.av(
                    iy.get_source_expressions(),
                    include_external=iw,
                    resolve_refs=ix,
                )

    @classmethod
    def aw(cls, iz):
        yield from (iA.alias for iA in cls.av(iz))

    def ax(self, iB, iC=True, iD=None, iE=False):
        iF = self.annotations.get(iB)
        if iF is not None:
            if not iC:
                for iG in self.aw([iF]):
                    if isinstance(self.alias_map[iG], Join):
                        raise FieldError(
                            "Joined field references are not permitted in this query"
                        )
            if iE:
                # Summarize currently means we are doing an aggregate() query
                # which is executed as a wrapped subquery if any of the
                # aggregate() elements reference an existing annotation. In
                # that case we need to return a Ref to the subquery's
                # annotation.
                if iB not in self.ba:
                    raise FieldError(
                        "Cannot aggregate over the '%s' alias. Use annotate() "
                        "to promote it." % iB
                    )
                return Ref(iB, self.ba[iB])
            else:
                return iF
        else:
            iH = iB.split(LOOKUP_SEP)
            iF = self.annotations.get(iH[0])
            if iF is not None:
                for iM in iH[1:]:
                    iF = self.aj(iF, iM)
                return iF
            iI = self.at(
                iH, self.l(), self.S(), can_reuse=iD
            )
            iJ, iK, iL = self.au(
                iI.targets, iI.joins, iI.path
            )
            if not iC and len(iL) > 1:
                raise FieldError(
                    "Joined field references are not permitted in this query"
                )
            if len(iJ) > 1:
                raise FieldError(
                    "Referencing multicolumn fields with F() objects isn't supported"
                )
            # Verify that the last lookup in name is a field or a transform:
            # transform_function() raises FieldError if not.
            iM = iI.transform_function(iJ[0], iK)
            if iD is not None:
                iD.update(iL)
            return iM

    def ay(self, iN, iO, iP):
        """
        When doing an exclude against any kind of N-to-many relation, we need
        to use a subquery. This method constructs the nested query, given the
        original exclude filter (filter_expr) and the portion up to the first
        N-to-many relation field.

        For example, if the origin filter is ~Q(child__name='foo'), filter_expr
        is ('child__name', 'foo') and can_reuse is a set of joins usable for
        filters in the original query.

        We will turn this into equivalent of:
            WHERE NOT EXISTS(
                SELECT 1
                FROM child
                WHERE name = 'foo' AND child.parent_id = parent.id
                LIMIT 1
            )
        """
        # Generate the inner query.
        iQ = self.__class__(self.model)
        iQ._filtered_relations = self._filtered_relations
        iR, iS = iN
        if isinstance(iS, OuterRef):
            iS = OuterRef(iS)
        elif isinstance(iS, F):
            iS = OuterRef(iS.name)
        iQ.add_filter(iR, iS)
        iQ.clear_ordering(force=True)
        # Try to have as simple as possible subquery -> trim leading joins from
        # the subquery.
        iT, iU = iQ.trim_start(iP)

        iV = iQ.select[0]
        iW = iV.target
        iX = iV.alias
        if iX in iO:
            iY = iW.model._meta.pk
            # Need to add a restriction so that outer query's filters are in
            # effect for the subquery, too.
            iQ.bump_prefix(self)
            iZ = iW.get_lookup("exact")
            # Note that the query.select[0].alias is different from alias
            # due to bump_prefix above.
            ja = iZ(iY.get_col(iQ.select[0].alias), iY.get_col(iX))
            iQ.where.add(ja, AND)
            iQ.external_aliases[iX] = True
        else:
            iZ = iW.get_lookup("exact")
            ja = iZ(iV, ResolvedOuterRef(iT))
            iQ.where.add(ja, AND)

        jb, jc = self.ak(Exists(iQ))

        if iU:
            jd, je = self.ak(
                ("%s__isnull" % iT, True),
                current_negated=True,
                branch_negated=True,
                can_reuse=iO,
            )
            jb.add(jd, OR)
            # Note that the end result will be:
            #   NOT EXISTS (inner_q) OR outercol IS NULL
            # this might look crazy but due to how NULL works, this seems to be
            # correct. If the IS NULL check is removed, then if outercol
            # IS NULL we will not match the row.
        return jb, jc

    def az(self):
        self.where.add(NothingNode(), AND)
        for jf in self.combined_queries:
            jf.set_empty()

    def aA(self):
        return any(isinstance(jg, NothingNode) for jg in self.where.children)

    def aB(self, jh=None, ji=None):
        """
        Adjust the limits on the rows retrieved. Use low/high to set these,
        as it makes it more Pythonic to read and write. When the SQL query is
        created, convert them to the appropriate offset and limit values.

        Apply any limits passed in here to the existing constraints. Add low
        to the current low value and clamp both to any existing high value.
        """
        if ji is not None:
            if self.high_mark is not None:
                self.high_mark = min(self.high_mark, self.low_mark + ji)
            else:
                self.high_mark = self.low_mark + ji
        if jh is not None:
            if self.high_mark is not None:
                self.low_mark = min(self.high_mark, self.low_mark + jh)
            else:
                self.low_mark = self.low_mark + jh

        if self.low_mark == self.high_mark:
            self.az()

    def aC(self):
        """Clear any existing limits."""
        self.low_mark, self.high_mark = 0, None

    @property
    def aD(self):
        return self.low_mark != 0 or self.high_mark is not None

    def aE(self):
        return self.high_mark is not None and (self.high_mark - self.low_mark) == 1

    def aF(self):
        """
        Return True if adding filters to this instance is still possible.

        Typically, this means no limits or offsets have been put on the
        results.
        """
        return not self.aD

    def aG(self):
        """Remove all fields from SELECT clause."""
        self.select = ()
        self.default_cols = False
        self.select_related = False
        self.aX(())
        self.aV(())
        self.selected = None

    def aH(self):
        """
        Clear the list of fields to select (but not extra_select columns).
        Some queryset types completely replace any existing list of select
        columns.
        """
        self.select = ()
        self.values_select = ()
        self.selected = None

    def aI(self, jj, jk):
        self.select += (jj,)
        self.values_select += (jk,)
        self.selected[jk] = len(self.select) - 1

    def aJ(self, jl):
        self.default_cols = False
        self.select = tuple(jl)

    def aK(self, *jm):
        """
        Add and resolve the given fields to the query's "distinct on" clause.
        """
        self.distinct_fields = jm
        self.distinct = True

    def aL(self, jn, jo=True):
        """
        Add the given (model) fields to the select set. Add the field names in
        the order specified.
        """
        jp = self.S()
        jq = self.l()

        try:
            jr = []
            for js in jn:
                # Join promotion note - we must not remove any rows here, so
                # if there is no existing joins, use outer join.
                jt = self.at(
                    js.split(LOOKUP_SEP), jq, jp, allow_many=jo
                )
                ju, jv, jw = self.au(
                    jt.targets,
                    jt.joins,
                    jt.path,
                )
                if len(ju) > 1:
                    jx = [
                        jt.transform_function(jy, jv)
                        for jy in ju
                    ]
                    jr.append(
                        ColPairs(
                            jv if self.alias_cols else None,
                            [jz.target for jz in jx],
                            [jz.output_field for jz in jx],
                            jt.final_field,
                        )
                    )
                else:
                    jr.append(jt.transform_function(ju[0], jv))
            if jr:
                self.aJ(jr)
        except MultiJoin:
            raise FieldError("Invalid field name: '%s'" % js)
        except FieldError:
            if LOOKUP_SEP in js:
                # For lookups spanning over relationships, show the error
                # from the model on which the lookup failed.
                raise
            else:
                jA = sorted(
                    [
                        *get_field_names_from_opts(jq),
                        *self.extra,
                        *self.ba,
                        *self._filtered_relations,
                    ]
                )
                raise FieldError(
                    "Cannot resolve keyword %r into field. "
                    "Choices are: %s" % (js, ", ".join(jA))
                )

    def aM(self, *jB):
        """
        Add items from the 'ordering' sequence to the query's "order by"
        clause. These items are either field names (not column names) --
        possibly with a direction prefix ('-' or '?') -- or OrderBy
        expressions.

        If 'ordering' is empty, clear all ordering from the query.
        """
        jC = []
        for jD in jB:
            if isinstance(jD, str):
                if jD == "?":
                    continue
                jD = jD.removeprefix("-")
                if jD in self.annotations:
                    continue
                if self.extra and jD in self.extra:
                    continue
                # names_to_path() validates the lookup. A descriptive
                # FieldError will be raise if it's not.
                self.ar(jD.split(LOOKUP_SEP), self.model._meta)
            elif not hasattr(jD, "resolve_expression"):
                jC.append(jD)
            if getattr(jD, "contains_aggregate", False):
                raise FieldError(
                    "Using an aggregate in order_by() without also including "
                    "it in annotate() is not allowed: %s" % jD
                )
        if jC:
            raise FieldError("Invalid order_by arguments: %s" % jC)
        if jB:
            self.order_by += jB
        else:
            self.default_ordering = False

    @property
    def aN(self):
        if self.extra_order_by:
            # Raw SQL from extra(order_by=...) can't be reliably compared
            # against resolved OrderBy/Col expressions. Treat as not a subset.
            return False
        if self.group_by in (None, True):
            # There is either no aggregation at all (None), or the group by
            # is generated automatically from model fields (True), in which
            # case the order by is necessarily a subset of them.
            return True
        if not self.order_by:
            # Although an empty set is always a subset, there's no point in
            # clearing ordering when there isn't any. Avoid the clone() below.
            return True
        # Don't pollute the original query (might disrupt joins).
        jE = self.m()
        jF = set()
        for jG in jE.order_by:
            if hasattr(jG, "resolve_expression"):
                jF.add(jG.resolve_expression(jE))
            elif jG == "?":
                # Random ordering can't be compared against group by.
                return False
            else:
                jF.add(F(jG.removeprefix("-")).resolve_expression(jE))
        return jF.issubset(self.group_by)

    def aO(self, jH=False, jI=True):
        """
        Remove any ordering settings if the current query allows it without
        side effects, set 'force' to True to clear the ordering regardless.
        If 'clear_default' is True, there will be no ordering in the resulting
        query (not even the model's default).
        """
        if not jH and (
            self.aD or self.distinct_fields or self.select_for_update
        ):
            return
        self.order_by = ()
        self.extra_order_by = ()
        if jI:
            self.default_ordering = False
        # Ordering is cleared on combined queries with clear_default=False
        # when union() and analogues are called, so percolate any possible
        # clear_default=True.
        for jJ in self.combined_queries:
            jJ.clear_ordering(force=False, clear_default=jI)

    def aP(self, jK=True):
        """
        Expand the GROUP BY clause required by the query.

        This will usually be the set of all non-aggregate fields in the
        return data. If the database backend supports grouping by the
        primary key, and the query would be equivalent, the optimization
        will be made automatically.
        """
        if jK and self.values_select:
            # If grouping by aliases is allowed assign selected value aliases
            # by moving them to annotations.
            jL = {}
            jM = {}
            for jR, jN in zip(self.values_select, self.select):
                if isinstance(jN, Col):
                    jM[jR] = jN
                else:
                    jL[jR] = jN
            self.annotations = {**jL, **self.annotations}
            self.aW(jL)
            self.select = tuple(jM.values())
            self.values_select = tuple(jM)
            if self.selected is not None:
                for jO, jP in enumerate(jM):
                    self.selected[jP] = jO
        jQ = list(self.select)
        for jR, jS in self.ba.items():
            if not (jT := jS.get_group_by_cols()):
                continue
            if jK and not jS.contains_aggregate:
                jQ.append(Ref(jR, jS))
            else:
                jQ.extend(jT)
        self.group_by = tuple(jQ)

    def aQ(self, jU):
        """
        Set up the select_related data structure so that we only select
        certain related models (as opposed to all models, when
        self.select_related=True).
        """
        if isinstance(self.select_related, bool):
            jV = {}
        else:
            jV = self.select_related
        for jW in jU:
            jX = jV
            for jY in jW.split(LOOKUP_SEP):
                jX = jX.setdefault(jY, {})
        self.select_related = jV

    def aR(self, jZ, ka, kb, kc, kd, ke):
        """
        Add data to the various extra_* attributes for user-created additions
        to the query.
        """
        if jZ:
            # We need to pair any placeholder markers in the 'select'
            # dictionary with their parameters in 'select_params' so that
            # subsequent updates to the select dictionary also adjust the
            # parameters appropriately.
            kf = {}
            if ka:
                kg = iter(ka)
            else:
                kg = iter([])
            for kh, ki in jZ.items():
                self.W(kh)
                ki = str(ki)
                kj = []
                kk = ki.find("%s")
                while kk != -1:
                    if kk == 0 or ki[kk - 1] != "%":
                        kj.append(next(kg))
                    kk = ki.find("%s", kk + 2)
                kf[kh] = (ki, kj)
            self.extra.update(kf)
        if kb or kc:
            self.where.add(ExtraWhere(kb, kc), AND)
        if kd:
            self.extra_tables += tuple(kd)
        if ke:
            self.extra_order_by = ke

    def aS(self):
        """Remove any fields from the deferred loading set."""
        self.deferred_loading = (frozenset(), True)

    def aT(self, kl):
        """
        Add the given list of model field names to the set of fields to
        exclude from loading from the database when automatic column selection
        is done. Add the new field names to any existing field names that
        are deferred (or removed from any existing field names that are marked
        as the only ones for immediate loading).
        """
        # Fields on related models are stored in the literal double-underscore
        # format, so that we can use a set datastructure. We do the foo__bar
        # splitting and handling when computing the SQL column names (as part
        # of get_columns()).
        km, kn = self.deferred_loading
        if kn:
            # Add to existing deferred names.
            self.deferred_loading = km.union(kl), True
        else:
            # Remove names from the set of any existing "immediate load" names.
            if ko := km.difference(kl):
                self.deferred_loading = ko, False
            else:
                self.aS()
                if kp := set(kl).difference(km):
                    self.deferred_loading = kp, True

    def aU(self, kq):
        """
        Add the given list of model field names to the set of fields to
        retrieve when the SQL is executed ("immediate loading" fields). The
        field names replace any existing immediate loading field names. If
        there are field names already specified for deferred loading, remove
        those names from the new field_names before storing the new names
        for immediate loading. (That is, immediate loading overrides any
        existing immediate values, but respects existing deferrals.)
        """
        kr, ks = self.deferred_loading
        kq = set(kq)
        if "pk" in kq:
            kq.remove("pk")
            kq.add(self.l().pk.name)

        if ks:
            # Remove any existing deferred names from the current set before
            # setting the new names.
            self.deferred_loading = kq.difference(kr), False
        else:
            # Replace any existing "immediate load" field names.
            self.deferred_loading = frozenset(kq), False

    def aV(self, kt):
        """Set the mask of annotations that will be returned by the SELECT."""
        if kt is None:
            self.annotation_select_mask = None
        else:
            self.annotation_select_mask = set(kt)
            if self.selected:
                # Prune the masked annotations.
                self.selected = {
                    ku: kv
                    for ku, kv in self.selected.items()
                    if not isinstance(kv, str)
                    or kv in self.annotation_select_mask
                }
                # Append the unmasked annotations.
                for kw in kt:
                    self.selected[kw] = kw
        self._annotation_select_cache = None

    def aW(self, kx):
        if self.annotation_select_mask is not None:
            self.aV(self.annotation_select_mask.union(kx))

    def aX(self, ky):
        """
        Set the mask of extra select items that will be returned by SELECT.
        Don't remove them from the Query since they might be used later.
        """
        if ky is None:
            self.extra_select_mask = None
        else:
            self.extra_select_mask = set(ky)
        self._extra_select_cache = None

    @property
    def aY(self):
        return self.selected is not None

    def aZ(self, kz):
        self.select_related = False
        self.aS()
        self.aH()

        kA = {}
        if kz:
            for kB in kz:
                self.W(kB)
            kC = []
            kD = []
            kE = []
            if not self.extra and not self.annotations:
                # Shortcut - if there are no extra or annotations, then
                # the values() clause must be just field names.
                kC = list(kz)
                kA = dict(zip(kz, range(len(kz))))
            else:
                self.default_cols = False
                for kF in kz:
                    if kG := self.bb.get(kF):
                        kD.append(kF)
                        kA[kF] = RawSQL(*kG)
                    elif kF in self.ba:
                        kE.append(kF)
                        kA[kF] = kF
                    elif kF in self.annotations:
                        if self.ba:
                            raise FieldError(
                                f"Cannot select the '{kF}' alias. It was excluded "
                                f"by a previous values() or values_list() call. "
                                f"Include '{kF}' in that call to select it."
                            )
                        else:
                            raise FieldError(
                                f"Cannot select the '{kF}' alias. Use annotate() "
                                f"to promote it."
                            )
                    else:
                        # Call `names_to_path` to ensure a FieldError including
                        # annotations about to be masked as valid choices if
                        # `f` is not resolvable.
                        if self.ba:
                            self.ar(kF.split(LOOKUP_SEP), self.model._meta)
                        kA[kF] = len(kC)
                        kC.append(kF)
            self.aX(kD)
            self.aV(kE)
        else:
            kC = [kF.attname for kF in self.model._meta.concrete_fields]
            kA = dict.fromkeys(kC, None)
        # Selected annotations must be known before setting the GROUP BY
        # clause.
        if self.group_by is True:
            self.aL(
                (kF.attname for kF in self.model._meta.concrete_fields), False
            )
            # Disable GROUP BY aliases to avoid orphaning references to the
            # SELECT clause which is about to be cleared.
            self.aP(allow_aliases=False)
            self.aH()
        elif self.group_by:
            # Resolve GROUP BY annotation references if they are not part of
            # the selected fields anymore.
            kH = []
            for kI in self.group_by:
                if isinstance(kI, Ref) and kI.refs not in kA:
                    kI = self.annotations[kI.refs]
                kH.append(kI)
            self.group_by = tuple(kH)

        self.values_select = tuple(kC)
        self.aL(kC, True)
        self.selected = kA if kz else None

    @property
    def ba(self):
        """
        Return the dictionary of aggregate columns that are not masked and
        should be used in the SELECT clause. Cache this result for performance.
        """
        if self._annotation_select_cache is not None:
            return self._annotation_select_cache
        elif not self.annotations:
            return {}
        elif self.annotation_select_mask is not None:
            self._annotation_select_cache = {
                kJ: kK
                for kJ, kK in self.annotations.items()
                if kJ in self.annotation_select_mask
            }
            return self._annotation_select_cache
        else:
            return self.annotations

    @property
    def bb(self):
        if self._extra_select_cache is not None:
            return self._extra_select_cache
        if not self.extra:
            return {}
        elif self.extra_select_mask is not None:
            self._extra_select_cache = {
                kL: kM for kL, kM in self.extra.items() if kL in self.extra_select_mask
            }
            return self._extra_select_cache
        else:
            return self.extra

    def bc(self, kN):
        """
        Trim joins from the start of the join path. The candidates for trim
        are the PathInfos in names_with_path structure that are m2m joins.

        Also set the select column so the start matches the join.

        This method is meant to be used for generating the subquery joins &
        cols in split_exclude().

        Return a lookup usable for doing outerq.filter(lookup=self) and a
        boolean indicating if the joins in the prefix contain a LEFT OUTER
        join.
        """
        kO = []
        for kP, kQ in kN:
            kO.extend(kQ)
        kR = False
        # Trim and operate only on tables that were generated for
        # the lookup part of the query. That is, avoid trimming
        # joins generated for F() expressions.
        kS = [
            kT for kT in self.alias_map if kT in self._lookup_joins or kT == self.g
        ]
        for kU, kV in enumerate(kO):
            if kV.m2m:
                break
            if self.alias_map[kS[kU + 1]].join_type == LOUTER:
                kR = True
            kW = kS[kU]
            self.L(kW)
        # The path.join_field is a Rel, lets get the other side's field
        kX = kV.join_field.field
        # Build the filter prefix.
        kY = kU
        kZ = []
        for la, kV in kN:
            if kY - len(kV) < 0:
                break
            kZ.append(la)
            kY -= len(kV)
        kZ.append(kX.foreign_related_fields[0].name)
        kZ = LOOKUP_SEP.join(kZ)
        # Lets still see if we can trim the first join from the inner query
        # (that is, self). We can't do this for:
        # - LEFT JOINs because we would miss those rows that have nothing on
        #   the outer side,
        # - INNER JOINs from filtered relations because we would miss their
        #   filters.
        lb = self.alias_map[kS[kU + 1]]
        if lb.join_type != LOUTER and not lb.filtered_relation:
            lc = [ld[0] for ld in kX.related_fields]
            le = kS[kU + 1]
            self.L(kS[kU])
            lf = kX.get_extra_restriction(
                None, kS[kU + 1]
            )
            if lf:
                self.where.add(lf, AND)
        else:
            # TODO: It might be possible to trim more joins from the start of
            # the inner query if it happens to have a longer join chain
            # containing the values in select_fields. Lets punt this one for
            # now.
            lc = [ld[1] for ld in kX.related_fields]
            le = kS[kU]
        # The found starting point is likely a join_class instead of a
        # base_table_class reference. But the first entry in the query's FROM
        # clause must not be a JOIN.
        for lg in self.alias_map:
            if self.alias_refcount[lg] > 0:
                self.alias_map[lg] = self.base_table_class(
                    self.alias_map[lg].table_name,
                    lg,
                )
                break
        self.aJ([lh.get_col(le) for lh in lc])
        return kZ, kR

    def bd(self, li):
        """
        Check if the given field should be treated as nullable.

        Some backends treat '' as null and Django treats such fields as
        nullable for those backends. In such situations field.null can be
        False even if we should treat the field as nullable.
        """
        # We need to use DEFAULT_DB_ALIAS here, as QuerySet does not have
        # (nor should it have) knowledge of which connection is going to be
        # used. The proper fix would be to defer all decisions where
        # is_nullable() is needed to the compiler stage, but that is not easy
        # to do currently.
        return li.null or (
            li.empty_strings_allowed
            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
        )
