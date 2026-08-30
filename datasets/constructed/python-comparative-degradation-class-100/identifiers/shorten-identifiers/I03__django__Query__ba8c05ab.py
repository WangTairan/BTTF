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

    def __init__(self, mod, alias2=True):
        self.model = mod
        self.alias_refcount = {}
        # alias_map is the most important data structure regarding joins.
        # It's used for recording which joins exist in the query and what
        # types they are. The key is the alias of the joined table (possibly
        # the table name) and the value is a Join-like object (see
        # sql.datastructures.Join for more information).
        self.alias_map = {}
        # Whether to provide alias to columns during reference resolving.
        self.alias_cols = alias2
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
    def output(self):
        if len(self.select) == 1:
            sel = self.select[0]
            return getattr(sel, "target", None) or sel.field
        elif len(self.annotation2) == 1:
            return next(iter(self.annotation2.values())).output_field

    @cached_property
    def base(self):
        for ali in self.alias_map:
            return ali

    def __str__(self):
        """
        Return the query as a string of SQL with the parameter values
        substituted in (use sql_with_params() to see the unsubstituted string).

        Parameter values won't necessarily be quoted correctly, since that is
        done by the database interface at execution time.
        """
        sql3, par = self.sql2()
        return sql3 % par

    def sql2(self):
        """
        Return the query as an SQL string and the parameters that will be
        substituted into the query.
        """
        return self.get2(DEFAULT_DB_ALIAS).as_sql()

    def __deepcopy__(self, mem):
        """Limit the amount of work when a Query is deepcopied."""
        res = self.clo()
        mem[id(self)] = res
        return res

    def get2(self, usi=None, con=None, elide=True):
        if usi is None and con is None:
            raise ValueError("Need either using or connection")
        if usi:
            con = connections[usi]
        return con.ops.compiler(self.compiler)(
            self, con, usi, elide
        )

    def get3(self):
        """
        Return the Options instance (the model._meta) from which to start
        processing. Normally, this is self.model._meta, but it can be changed
        by subclasses.
        """
        if self.model:
            return self.model._meta

    def clo(self):
        """
        Return a copy of the current Query. A lightweight alternative to
        deepcopy().
        """
        obj2 = Empty()
        obj2.__class__ = self.__class__
        # Copy references to everything.
        obj2.__dict__ = self.__dict__.copy()
        # Clone attributes that can't use shallow copy.
        obj2.alias_refcount = self.alias_refcount.copy()
        obj2.alias_map = self.alias_map.copy()
        obj2.external_aliases = self.external_aliases.copy()
        obj2.table_map = self.table_map.copy()
        obj2.where = self.where.clone()
        obj2.annotations = self.annotations.copy()
        if self.annotation_select_mask is not None:
            obj2.annotation_select_mask = self.annotation_select_mask.copy()
        if self.combined_queries:
            obj2.combined_queries = tuple(
                [que.clone() for que in self.combined_queries]
            )
        # _annotation_select_cache cannot be copied, as doing so breaks the
        # (necessary) state in which both annotations and
        # _annotation_select_cache point to the same underlying objects.
        # It will get re-populated in the cloned queryset the next time it's
        # used.
        obj2._annotation_select_cache = None
        obj2.extra = self.extra.copy()
        if self.extra_select_mask is not None:
            obj2.extra_select_mask = self.extra_select_mask.copy()
        if self._extra_select_cache is not None:
            obj2._extra_select_cache = self._extra_select_cache.copy()
        if self.select_related is not False:
            # Use deepcopy because select_related stores fields in nested
            # dicts.
            obj2.select_related = copy.deepcopy(obj2.select_related)
        if "subq_aliases" in self.__dict__:
            obj2.subq_aliases = self.subq_aliases.copy()
        obj2.used_aliases = self.used_aliases.copy()
        obj2._filtered_relations = self._filtered_relations.copy()
        # Clear the cached_property, if it exists.
        obj2.__dict__.pop("base_table", None)
        return obj2

    def cha(self, kla=None):
        """
        Return a copy of the current Query that's ready for another operation.
        The klass argument changes the type of the Query, e.g. UpdateQuery.
        """
        obj3 = self.clo()
        if kla and obj3.__class__ != kla:
            obj3.__class__ = kla
        if not obj3.filter_is_sticky:
            obj3.used_aliases = set()
        obj3.filter_is_sticky = False
        if hasattr(obj3, "_setup_query"):
            obj3._setup_query()
        return obj3

    def relabeled(self, change2):
        clo2 = self.clo()
        clo2.change_aliases(change2)
        return clo2

    def get4(self, tar, fie, ali2):
        if not self.alias_cols:
            ali2 = None
        return tar.get_col(ali2, fie)

    def get5(self, usi2, aggregate2):
        """
        Return the dictionary with the values of the existing aggregations.
        """
        if not aggregate2:
            return {}
        # Store annotation mask prior to temporarily adding aggregations for
        # resolving purpose to facilitate their subsequent removal.
        refs2 = False
        refs3 = False
        rep = {}
        annotation3 = self.annotation_select_mask
        for ali3, aggregate3 in aggregate2.items():
            self.check(ali3)
            agg = aggregate3.resolve_expression(
                self, allow_joins=True, reuse=None, summarize=True
            )
            if not agg.contains_aggregate:
                raise TypeError("%s is not an aggregate expression" % ali3)
            # Temporarily add aggregate to annotations to allow remaining
            # members of `aggregates` to resolve against each others.
            self.append2([ali3])
            aggregate4 = agg.get_refs()
            refs2 |= any(
                getattr(self.annotations[ref3], "contains_subquery", False)
                for ref3 in aggregate4
            )
            refs3 |= any(
                getattr(self.annotations[ref3], "contains_over_clause", True)
                for ref3 in aggregate4
            )
            agg = agg.replace_expressions(rep)
            self.annotations[ali3] = agg
            rep[Ref(ali3, agg)] = agg
        # Stash resolved aggregates now that they have been allowed to resolve
        # against each other.
        agg2 = {ali3: self.annotations.pop(ali3) for ali3 in aggregate2}
        self.set6(annotation3)
        # Existing usage of aggregation can be determined by the presence of
        # selected aggregates but also by filters against aliased aggregates.
        _2, hav, qua = self.where.split_having_qualify()
        has5 = (
            any(
                getattr(ann, "contains_aggregate", True)
                for ann in self.annotations.values()
            )
            or hav
        )
        set9 = {
            ali3
            for ali3, ann in self.annotation2.items()
            if getattr(ann, "set_returning", False)
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
            or self.is3
            or has5
            or refs2
            or refs3
            or qua
            or self.distinct
            or self.combinator
            or set9
        ):
            from django.db.models.sql.subqueries import AggregateQuery

            inner = self.clo()
            inner.subquery = True
            outer = AggregateQuery(self.model, inner)
            inner.select_for_update = False
            inner.select_related = False
            inner.set_annotation_mask(self.annotation2)
            # Queries with distinct_fields need ordering and when a limit is
            # applied we must take the slice from the ordered query. Otherwise
            # no need for ordering.
            if inner.orderby_issubset_groupby:
                inner.clear_ordering(force=False)
            if not inner.distinct:
                # If the inner query uses default select and it has some
                # aggregate annotations, then we must make sure the inner
                # query is grouped by the main model's primary key. However,
                # clearing the select clause can alter results if distinct is
                # used.
                if inner.default_cols and has5:
                    inner.group_by = (
                        self.model._meta.pk.get_col(inner.get_initial_alias()),
                    )
                inner.default_cols = False
                if not qua and not self.combinator:
                    # Mask existing annotations that are not referenced by
                    # aggregates to be pushed to the outer query unless
                    # filtering against window functions or if the query is
                    # combined as both would require complex realiasing logic.
                    annotation4 = set()
                    if isinstance(self.group_by, tuple):
                        for exp2 in self.group_by:
                            annotation4 |= exp2.get_refs()
                    for agg in agg2.values():
                        annotation4 |= agg.get_refs()
                    # Avoid eliding expressions that might have an incidence on
                    # the implicit grouping logic.
                    for annotation5, ann in self.annotation2.items():
                        if ann.get_group_by_cols():
                            annotation4.add(annotation5)
                    inner.set_annotation_mask(annotation4)
                    # Annotations that possibly return multiple rows cannot
                    # be masked as they might have an incidence on the query.
                    annotation4 |= set9

            # Add aggregates to the outer AggregateQuery. This requires making
            # sure all columns referenced by the aggregates are selected in the
            # inner query. It is achieved by retrieving all column references
            # by the aggregates, explicitly selecting them in the inner query,
            # and making sure the aggregates are repointed to them.
            col2 = {}
            for ali3, agg in agg2.items():
                rep = {}
                for col3 in self.gen([agg], resolve_refs=False):
                    if not (col5 := col2.get(col3)):
                        ind = len(col2) + 1
                        col4 = f"__col{ind}"
                        col5 = Ref(col4, col3)
                        col2[col3] = col5
                        inner.add_annotation(col3, col4)
                    rep[col3] = col5
                outer.annotations[ali3] = agg.replace_expressions(
                    rep
                )
            if (
                inner.select == ()
                and not inner.default_cols
                and not inner.annotation_select_mask
            ):
                # In case of Model.objects[0:3].count(), there would be no
                # field selected in the inner query, yet we must use a
                # subquery. So, make sure at least one field is selected.
                inner.select = (
                    self.model._meta.pk.get_col(inner.get_initial_alias()),
                )
        else:
            outer = self
            self.select = ()
            self.selected = None
            self.default_cols = False
            self.extra = {}
            if self.annotations:
                # Inline reference to existing annotations and mask them as
                # they are unnecessary given only the summarized aggregations
                # are requested.
                rep = {
                    Ref(ali3, ann): ann
                    for ali3, ann in self.annotations.items()
                }
                self.annotations = {
                    ali3: agg.replace_expressions(rep)
                    for ali3, agg in agg2.items()
                }
            else:
                self.annotations = agg2
            self.set6(agg2)

        empty = [
            exp3.empty_result_set_value
            for exp3 in outer.annotation_select.values()
        ]
        elide2 = not any(res2 is NotImplemented for res2 in empty)
        outer.clear_ordering(force=True)
        outer.clear_limits()
        outer.select_for_update = False
        outer.select_related = False
        com2 = outer.get_compiler(usi2, elide_empty=elide2)
        res2 = com2.execute_sql(SINGLE)
        if res2 is None:
            res2 = empty
        else:
            col6 = outer.annotation_select.values()
            con2 = com2.get_converters(col6)
            row = com2.apply_converters((res2,), con2)
            if com2.has_composite_fields(col6):
                row = com2.composite_fields_to_tuples(row, col6)
            res2 = next(row)

        return dict(zip(outer.annotation_select, res2))

    def get6(self, usi3):
        """
        Perform a COUNT() query using the current filter constraints.
        """
        obj4 = self.clo()
        return obj4.get_aggregation(usi3, {"__count": Count("*")})["__count"]

    def has(self):
        return self.where

    def exi(self, lim=True):
        q2 = self.clo()
        if not (q2.distinct and q2.is_sliced):
            if q2.group_by is True:
                q2.add_fields(
                    (f2.attname for f2 in self.model._meta.concrete_fields), False
                )
                # Disable GROUP BY aliases to avoid orphaning references to the
                # SELECT clause which is about to be cleared.
                q2.set_group_by(allow_aliases=False)
            q2.clear_select_clause()
        if q2.combined_queries and q2.combinator == "union":
            q2.combined_queries = tuple(
                combined.exists(limit=False)
                for combined in q2.combined_queries
            )
        q2.clear_ordering(force=True)
        if lim is True:
            q2.set_limits(high=1)
        q2.add_annotation(Value(1), "a")
        return q2

    def has2(self, usi4):
        q3 = self.exi()
        com3 = q3.get_compiler(using=usi4)
        return com3.has_results()

    def exp(self, usi5, for2=None, **opt):
        q4 = self.clo()
        for option in opt:
            if (
                not EXPLAIN_OPTIONS_PATTERN.fullmatch(option)
                or "--" in option
            ):
                raise ValueError(f"Invalid option name: {option!r}.")
        q4.explain_info = ExplainInfo(for2, opt)
        com4 = q4.get_compiler(using=usi5)
        return "\n".join(com4.explain_query())

    def com(self, rhs2, con3):
        """
        Merge the 'rhs' query into the current one (with any 'rhs' effects
        being applied *after* (that is, "to the right of") anything in the
        current query. 'rhs' is not modified during a call to this function.

        The 'connector' parameter describes how to connect filters from the
        'rhs' query.
        """
        if self.model != rhs2.model:
            raise TypeError("Cannot combine queries on two different base models.")
        if self.is3:
            raise TypeError("Cannot combine queries once a slice has been taken.")
        if self.distinct != rhs2.distinct:
            raise TypeError("Cannot combine a unique query with a non-unique query.")
        if self.distinct_fields != rhs2.distinct_fields:
            raise TypeError("Cannot combine queries with different distinct fields.")

        # If lhs and rhs shares the same alias prefix, it is possible to have
        # conflicting alias changes like T4 -> T5, T5 -> T6, which might end up
        # as T4 -> T6 while combining two querysets. To prevent this, change an
        # alias prefix of the rhs and update current aliases accordingly,
        # except if the alias is the base table since it must be present in the
        # query on both sides.
        initial = self.get10()
        rhs2 = rhs2.clone()
        rhs2.bump_prefix(self, exclude={initial})

        # Work out how to relabel the rhs aliases, if necessary.
        change3 = {}
        con4 = con3 == AND

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
        reu = set() if con4 else set(self.alias_map)
        joi2 = JoinPromoter(con3, 2, False)
        joi2.add_votes(
            j2 for j2 in self.alias_map if self.alias_map[j2].join_type == INNER
        )
        rhs3 = set()
        # Now, add the joins from rhs query into the new query (skipping base
        # table).
        rhs4 = list(rhs2.alias_map)[1:]
        for ali4 in rhs4:
            joi3 = rhs2.alias_map[ali4]
            # If the left side of the join was already relabeled, use the
            # updated alias.
            joi3 = joi3.relabeled_clone(change3)
            new = self.joi(joi3, reuse=reu)
            if joi3.join_type == INNER:
                rhs3.add(new)
            # We can't reuse the same join again in the query. If we have two
            # distinct joins for the same connection in rhs query, then the
            # combined query must have two joins, too.
            reu.discard(new)
            if ali4 != new:
                change3[ali4] = new
            if not rhs2.alias_refcount[ali4]:
                # The alias was unused in the rhs query. Unref it so that it
                # will be unused in the new query, too. We have to add and
                # unref the alias so that join promotion has information of
                # the join type for the unused alias.
                self.unref(new)
        joi2.add_votes(rhs3)
        joi2.update_join_types(self)

        # Combine subqueries aliases to ensure aliases relabelling properly
        # handle subqueries when combining where and select clauses.
        self.subq_aliases |= rhs2.subq_aliases

        # Now relabel a copy of the rhs where-clause and add it to the current
        # one.
        w2 = rhs2.where.clone()
        w2.relabel_aliases(change3)
        self.where.add(w2, con3)

        # Selection columns and extra extensions are those provided by 'rhs'.
        if rhs2.select:
            self.set4([col7.relabeled_clone(change3) for col7 in rhs2.select])
        else:
            self.select = ()

        if con3 == OR:
            # It would be nice to be able to handle this, but the queries don't
            # really make sense (or return consistent value sets). Not worth
            # the extra complexity when you can write a real query instead.
            if self.extra and rhs2.extra:
                raise ValueError(
                    "When merging querysets using 'or', you cannot have "
                    "extra(select=...) on both sides."
                )
        self.extra.update(rhs2.extra)
        extra3 = set()
        if self.extra_select_mask is not None:
            extra3.update(self.extra_select_mask)
        if rhs2.extra_select_mask is not None:
            extra3.update(rhs2.extra_select_mask)
        if extra3:
            self.set7(extra3)
        self.extra_tables += rhs2.extra_tables

        # Ordering uses the 'rhs' ordering, unless it has none, in which case
        # the current ordering is used.
        self.order_by = rhs2.order_by or self.order_by
        self.extra_order_by = rhs2.extra_order_by or self.extra_order_by

    def get7(self, opt2, mas, select2=None):
        if select2 is None:
            select2 = {}
        select2[opt2.pk] = {}
        # All concrete fields and related objects that are not part of the
        # defer mask must be included. If a relational field is encountered it
        # gets added to the mask for it be considered if `select_related` and
        # the cycle continues by recursively calling this function.
        for fie2 in opt2.concrete_fields + opt2.related_objects:
            field2 = mas.pop(fie2.name, None)
            field3 = None
            if field4 := getattr(fie2, "attname", None):
                field3 = mas.pop(field4, None)
            if field2 is None and field3 is None:
                select2.setdefault(fie2, {})
            elif field2:
                if not fie2.is_relation:
                    raise FieldError(next(iter(field2)))
                # Virtual fields such as many-to-many and generic foreign keys
                # cannot be effectively deferred. Historically, they were
                # allowed to be passed to QuerySet.defer(). Ignore such field
                # references until a layer of validation at mask alteration
                # time is eventually implemented.
                if fie2.many_to_many:
                    continue
                field6 = select2.setdefault(fie2, {})
                related = fie2.related_model._meta.concrete_model
                self.get7(
                    related._meta, field2, field6
                )
        # Remaining defer entries must be references to filtered relations
        # otherwise they are surfaced as missing field errors.
        for field5, field2 in mas.items():
            if filtered := self._filtered_relations.get(field5):
                rel = opt2.get_field(filtered.relation_name)
                field6 = select2.setdefault((field5, rel), {})
                related = rel.related_model._meta.concrete_model
                self.get7(
                    related._meta, field2, field6
                )
            else:
                opt2.get_field(field5)
        return select2

    def get8(self, opt3, mas2, select3=None):
        if select3 is None:
            select3 = {}
        select3[opt3.pk] = {}
        # Only include fields mentioned in the mask.
        for field7, field8 in mas2.items():
            fie3 = opt3.get_field(field7)
            field9 = select3.setdefault(fie3, {})
            if field8:
                if not fie3.is_relation:
                    raise FieldError(next(iter(field8)))
                related2 = fie3.remote_field.model._meta.concrete_model
                self.get8(
                    related2._meta, field8, field9
                )
        return select3

    def get9(self):
        """
        Convert the self.deferred_loading data structure to an alternate data
        structure, describing the field that *will* be loaded. This is used to
        compute the columns to select from the database and also by the
        QuerySet class to work out which fields are being initialized on each
        model. Models that have all their fields included aren't mentioned in
        the result, only those that have field restrictions in place.
        """
        field10, def2 = self.deferred_loading
        if not field10:
            return {}
        mas3 = {}
        for field11 in field10:
            part2 = mas3
            for par2 in field11.split(LOOKUP_SEP):
                part2 = part2.setdefault(par2, {})
        opt4 = self.get3()
        if def2:
            return self.get7(opt4, mas3)
        return self.get8(opt4, mas3)

    def table2(self, table3, cre=False, filtered2=None):
        """
        Return a table alias for the given table_name and whether this is a
        new alias or not.

        If 'create' is true, a new alias is always created. Otherwise, the
        most recently created alias for the table (if one exists) is reused.
        """
        alias3 = self.table_map.get(table3)
        if not cre and alias3:
            ali5 = alias3[0]
            self.alias_refcount[ali5] += 1
            return ali5, False

        # Create a new alias for this table.
        if alias3:
            ali5 = "%s%d" % (self.alias_prefix, len(self.alias_map) + 1)
            alias3.append(ali5)
        else:
            # The first occurrence of a table uses the table name directly.
            ali5 = (
                filtered2.alias if filtered2 is not None else table3
            )
            self.table_map[table3] = [ali5]
        self.alias_refcount[ali5] = 1
        return ali5, True

    def ref2(self, ali6):
        """Increases the reference count for this alias."""
        self.alias_refcount[ali6] += 1

    def unref(self, ali7, amo=1):
        """Decreases the reference count for this alias."""
        self.alias_refcount[ali7] -= amo

    def promote2(self, ali8):
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
        ali8 = list(ali8)
        while ali8:
            ali9 = ali8.pop(0)
            if self.alias_map[ali9].join_type is None:
                # This is the base table (first FROM entry) - this table
                # isn't really joined at all in the query, so we should not
                # alter its join type.
                continue
            # Only the first alias (skipped above) should have None join_type
            assert self.alias_map[ali9].join_type is not None
            parent = self.alias_map[ali9].parent_alias
            parent2 = (
                parent and self.alias_map[parent].join_type == LOUTER
            )
            already = self.alias_map[ali9].join_type == LOUTER
            if (self.alias_map[ali9].nullable or parent2) and not already:
                self.alias_map[ali9] = self.alias_map[ali9].promote()
                # Join type of 'alias' changed, so re-examine all aliases that
                # refer to this one.
                ali8.extend(
                    joi4
                    for joi4 in self.alias_map
                    if self.alias_map[joi4].parent_alias == ali9
                    and joi4 not in ali8
                )

    def demote2(self, ali10):
        """
        Change join type from LOUTER to INNER for all joins in aliases.

        Similarly to promote_joins(), this method must ensure no join chains
        containing first an outer, then an inner join are generated. If we
        are demoting b->c join in chain a LOUTER b LOUTER c then we must
        demote a->b automatically, or otherwise the demotion of b->c doesn't
        actually change anything in the query results. .
        """
        ali10 = list(ali10)
        while ali10:
            ali11 = ali10.pop(0)
            if self.alias_map[ali11].join_type == LOUTER:
                self.alias_map[ali11] = self.alias_map[ali11].demote()
                parent3 = self.alias_map[ali11].parent_alias
                if self.alias_map[parent3].join_type == INNER:
                    ali10.append(parent3)

    def reset(self, to):
        """
        Reset reference counts for aliases so that they match the value passed
        in `to_counts`.
        """
        for ali12, cur in self.alias_refcount.copy().items():
            unref2 = cur - to.get(ali12, 0)
            self.unref(ali12, unref2)

    def change(self, change4):
        """
        Change the aliases in change_map (which maps old-alias -> new-alias),
        relabelling any references to them in select columns and the where
        clause.
        """
        if not change4:
            return self
        # If keys and values of change_map were to intersect, an alias might be
        # updated twice (e.g. T4 -> T5, T5 -> T6, so also T4 -> T6) depending
        # on their order in change_map.
        assert set(change4).isdisjoint(change4.values())

        # 1. Update references in "select" (normal columns plus aliases),
        # "group by" and "where".
        self.where.relabel_aliases(change4)
        if isinstance(self.group_by, tuple):
            self.group_by = tuple(
                [col8.relabeled_clone(change4) for col8 in self.group_by]
            )
        self.select = tuple([col8.relabeled_clone(change4) for col8 in self.select])
        self.annotations = self.annotations and {
            key2: col8.relabeled_clone(change4)
            for key2, col8 in self.annotations.items()
        }

        # 2. Rename the alias in the internal table/alias datastructures.
        for old, new2 in change4.items():
            if old not in self.alias_map:
                continue
            alias4 = self.alias_map[old].relabeled_clone(change4)
            self.alias_map[new2] = alias4
            self.alias_refcount[new2] = self.alias_refcount[old]
            del self.alias_refcount[old]
            del self.alias_map[old]

            table4 = self.table_map[alias4.table_name]
            for pos2, ali13 in enumerate(table4):
                if ali13 == old:
                    table4[pos2] = new2
                    break

        # 3. Rename the direct external aliases and the ones of combined
        # queries (union, intersection, difference).
        self.external_aliases = {
            # Table is aliased or it's being changed and thus is aliased.
            change4.get(ali13, ali13): (ali14 or ali13 in change4)
            for ali13, ali14 in self.external_aliases.items()
        }
        for combined2 in self.combined_queries:
            external = {
                ali13: ali14
                for ali13, ali14 in change4.items()
                if ali13 in combined2.external_aliases
            }
            combined2.change_aliases(external)

    def bump(self, other, exc2=None):
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
            alp = ascii_uppercase
            pre2 = chr(ord(self.alias_prefix) + 1)
            yield pre2
            for n2 in count(1):
                seq2 = alp[alp.index(pre2) :] if pre2 else alp
                for s2 in product(seq2, repeat=n2):
                    yield "".join(s2)
                pre2 = None

        if self.alias_prefix != other.alias_prefix:
            # No clashes between self and outer query should be possible.
            return

        # Explicitly avoid infinite loop. The constant divider is based on how
        # much depth recursive subquery references add to the stack. This value
        # might need to be adjusted when adding or removing function calls from
        # the code path in charge of performing these operations.
        local = sys.getrecursionlimit() // 16
        for pos3, pre in enumerate(prefix_gen()):
            if pre not in self.subq_aliases:
                self.alias_prefix = pre
                break
            if pos3 > local:
                raise RecursionError(
                    "Maximum recursion depth exceeded: too many subqueries."
                )
        self.subq_aliases = self.subq_aliases.union([self.alias_prefix])
        other.subq_aliases = other.subq_aliases.union(self.subq_aliases)
        if exc2 is None:
            exc2 = {}
        self.change(
            {
                ali15: "%s%d" % (self.alias_prefix, pos3)
                for pos3, ali15 in enumerate(self.alias_map)
                if ali15 not in exc2
            }
        )

    def get10(self):
        """
        Return the first alias for this query, after increasing its reference
        count.
        """
        if self.alias_map:
            ali16 = self.base
            self.ref2(ali16)
        elif self.model:
            ali16 = self.joi(self.base_table_class(self.get3().db_table, None))
        else:
            ali16 = None
        return ali16

    def count2(self):
        """
        Return the number of tables in this query with a non-zero reference
        count. After execution, the reference counts are zeroed, so tables
        added in compiler will not be seen by this method.
        """
        return len([1 for cou in self.alias_refcount.values() if cou])

    def joi(self, joi5, reu2=None):
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
        reuse2 = [
            a2
            for a2, j3 in self.alias_map.items()
            if (reu2 is None or a2 in reu2) and j3 == joi5
        ]
        if reuse2:
            if joi5.table_alias in reuse2:
                reuse3 = joi5.table_alias
            else:
                # Reuse the most recent alias of the joined table
                # (a many-to-many relation may be joined multiple times).
                reuse3 = reuse2[-1]
            self.ref2(reuse3)
            return reuse3

        # No reuse is possible, so we need a new alias.
        ali17, _3 = self.table2(
            joi5.table_name, create=True, filtered_relation=joi5.filtered_relation
        )
        if joi5.join_type:
            if self.alias_map[joi5.parent_alias].join_type == LOUTER or joi5.nullable:
                join3 = LOUTER
            else:
                join3 = INNER
            joi5.join_type = join3
        joi5.table_alias = ali17
        self.alias_map[ali17] = joi5
        if filtered3 := joi5.filtered_relation:
            resolve4 = reu2
            if resolve4 is not None:
                resolve4 = set(reu2) | {ali17}
            joins2 = len(self.alias_map)
            joi5.filtered_relation = filtered3.resolve_expression(
                self, reuse=resolve4
            )
            # Some joins were during expression resolving, they must be present
            # before the one we just added.
            if joins2 < len(self.alias_map):
                self.alias_map[ali17] = self.alias_map.pop(ali17)
        return ali17

    def join2(self, opt5, mod2, ali18, see):
        """
        Make sure the given 'model' is joined in the query. If 'model' isn't
        a parent of 'opts' or if it is None this method is a no-op.

        The 'alias' is the root alias for starting the join, 'seen' is a dict
        of model -> alias of existing joins. It must also contain a mapping
        of None -> some alias. This will be returned in the no-op case.
        """
        if mod2 in see:
            return see[mod2]
        cha2 = opt5.get_base_chain(mod2)
        if not cha2:
            return ali18
        curr = opt5
        for int in cha2:
            if int in see:
                curr = int._meta
                ali18 = see[int]
                continue
            # Proxy model have elements in base chain
            # with no parents, assign the new options
            # object and skip to the next base in that
            # case
            if not curr.parents[int]:
                curr = int._meta
                continue
            link = curr.get_ancestor_link(int)
            join4 = self.setup([link.name], curr, ali18)
            curr = int._meta
            ali18 = see[int] = join4.joins[-1]
        return ali18 or see[None]

    def check(self, ali19):
        # RemovedInDjango70Warning: When the deprecation ends, remove.
        if "%" in ali19:
            warnings.warn(
                "Using percent signs in a column alias is deprecated.",
                category=RemovedInDjango70Warning,
                skip_file_prefixes=django_file_prefixes(),
            )
        if FORBIDDEN_ALIAS_PATTERN.search(ali19):
            raise ValueError(
                "Column aliases cannot contain whitespace characters, hashes, "
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # "control characters, quotation marks, semicolons, percent "
                # "signs, or SQL comments."
                "control characters, quotation marks, semicolons, or SQL comments."
            )

    def add2(self, ann2, ali20, sel2=True):
        """Add a single annotation expression to the Query."""
        self.check(ali20)
        ann2 = ann2.resolve_expression(self, allow_joins=True, reuse=None)
        if sel2:
            self.append2([ali20])
        else:
            self.set6(set(self.annotation2).difference({ali20}))
        self.annotations[ali20] = ann2
        if sel2 and self.selected:
            self.selected[ali20] = ali20

    @property
    def subquery2(self):
        if not self.has4 or not self.select:
            return len(self.model._meta.pk_fields)
        return len(self.select) + sum(
            len(exp4.targets) - 1 for exp4 in self.select if isinstance(exp4, ColPairs)
        )

    def resolve(self, que2, *arg2, **kwa):
        clo3 = self.clo()
        # Subqueries need to use a different set of aliases than the outer
        # query.
        clo3.bump_prefix(que2)
        clo3.subquery = True
        clo3.where.resolve_expression(que2, *arg2, **kwa)
        # Resolve combined queries.
        if clo3.combinator:
            clo3.combined_queries = tuple(
                [
                    combined3.resolve_expression(que2, *arg2, **kwa)
                    for combined3 in clo3.combined_queries
                ]
            )
        for key3, val in clo3.annotations.items():
            res3 = val.resolve_expression(que2, *arg2, **kwa)
            if hasattr(res3, "external_aliases"):
                res3.external_aliases.update(clo3.external_aliases)
            clo3.annotations[key3] = res3
        # Outer query's aliases are considered external.
        for ali21, tab in que2.alias_map.items():
            clo3.external_aliases[ali21] = (
                isinstance(tab, Join)
                and tab.join_field.related_model._meta.db_table != ali21
            ) or (
                isinstance(tab, BaseTable) and tab.table_name != tab.table_alias
            )
        return clo3

    def get11(self):
        exp5 = chain(self.annotations.values(), self.where.children)
        return [
            col9
            for col9 in self.gen(exp5, include_external=True)
            if col9.alias in self.external_aliases
        ]

    def get12(self, wra=None):
        # If wrapper is referenced by an alias for an explicit GROUP BY through
        # values() a reference to this expression and not the self must be
        # returned to ensure external column references are not grouped against
        # as well.
        external2 = self.get11()
        if any(col10.possibly_multivalued for col10 in external2):
            return [wra or self]
        return external2

    def as2(self, com5, con5):
        # Some backends (e.g. Oracle) raise an error when a subquery contains
        # unnecessary ORDER BY clause.
        if (
            self.subquery
            and not con5.features.ignores_unnecessary_order_by_in_subqueries
        ):
            self.clear5(force=False)
            for que3 in self.combined_queries:
                que3.clear_ordering(force=False)
        sql4, par3 = self.get2(connection=con5).as_sql()
        if self.subquery:
            sql4 = "(%s)" % sql4
        return sql4, par3

    def resolve2(self, val2, can2, allow, sum2=False):
        if hasattr(val2, "resolve_expression"):
            val2 = val2.resolve_expression(
                self,
                reuse=can2,
                allow_joins=allow,
                summarize=sum2,
            )
        elif isinstance(val2, (list, tuple)):
            # The items of the iterable may be expressions and therefore need
            # to be resolved independently.
            val3 = (
                self.resolve2(sub, can2, allow, sum2)
                for sub in val2
            )
            typ = type(val2)
            if hasattr(typ, "_make"):  # namedtuple
                return typ(*val3)
            return typ(val3)
        return val2

    def solve(self, loo, sum3=False):
        """
        Solve the lookup type from the lookup (e.g.: 'foobar__id__icontains').
        """
        lookup2 = loo.split(LOOKUP_SEP)
        if self.annotations:
            ann3, expression2 = refs_expression(
                lookup2, self.annotations
            )
            if ann3:
                exp6 = self.annotations[ann3]
                if sum3:
                    exp6 = Ref(ann3, exp6)
                return expression2, (), exp6
        _4, fie4, _4, lookup3 = self.names2(lookup2, self.get3())
        field12 = lookup2[0 : len(lookup2) - len(lookup3)]
        if len(lookup3) > 1 and not field12:
            raise FieldError(
                'Invalid lookup "%s" for model %s".'
                % (loo, self.get3().model.__name__)
            )
        return lookup3, field12, False

    def check2(self, val4, opt6, fie5):
        """
        Check whether the object passed while querying is of the correct type.
        If not, raise a ValueError specifying the wrong object.
        """
        if hasattr(val4, "_meta"):
            if not check_rel_lookup_compatibility(val4._meta.model, opt6, fie5):
                raise ValueError(
                    'Cannot query "%s": Must be "%s" instance.'
                    % (val4, opt6.object_name)
                )

    def check3(self, fie6, val5, opt7):
        """Check the type of object passed to query relations."""
        if fie6.is_relation:
            # Check that the field and the queryset use the same model in a
            # query like .filter(author=Author.objects.all()). For example, the
            # opts would be Author's (from the author field) and value.model
            # would be Author.objects.all() queryset's .model (Author also).
            # The field is the related field on the lhs side.
            if (
                isinstance(val5, Query)
                and not val5.has_select_fields
                and not check_rel_lookup_compatibility(val5.model, opt7, fie6)
            ):
                raise ValueError(
                    'Cannot use QuerySet for "%s": Use a QuerySet for "%s".'
                    % (val5.model._meta.object_name, opt7.object_name)
                )
            elif hasattr(val5, "_meta"):
                self.check2(val5, opt7, fie6)
            elif hasattr(val5, "__iter__"):
                for v2 in val5:
                    self.check2(v2, opt7, fie6)

    def check4(self, exp7):
        """Raise an error if expression cannot be used in a WHERE clause."""
        if hasattr(exp7, "resolve_expression") and not getattr(
            exp7, "filterable", True
        ):
            raise NotSupportedError(
                exp7.__class__.__name__ + " is disallowed in the filter "
                "clause."
            )
        if hasattr(exp7, "get_source_expressions"):
            for exp8 in exp7.get_source_expressions():
                self.check4(exp8)

    def build(self, loo2, lhs2, rhs5):
        """
        Try to extract transforms and lookup from given lhs.

        The lhs value is something that works like SQLExpression.
        The rhs value is what the lookup is going to compare against.
        The lookups is a list of names to extract using get_lookup()
        and get_transform().
        """
        # __exact is the default lookup if one isn't given.
        *tra, lookup4 = loo2 or ["exact"]
        for nam in tra:
            lhs2 = self.try2(lhs2, nam, loo2)
        # First try get_lookup() so that the lookup takes precedence if the lhs
        # supports both transform and lookup for the name.
        lookup5 = lhs2.get_lookup(lookup4)
        if not lookup5:
            # A lookup wasn't found. Try to interpret the name as a transform
            # and do an Exact lookup against it.
            lhs2 = self.try2(lhs2, lookup4)
            lookup4 = "exact"
            lookup5 = lhs2.get_lookup(lookup4)
            if not lookup5:
                return

        loo3 = lookup5(lhs2, rhs5)
        # Interpret '__exact=None' as the sql 'is NULL'; otherwise, reject all
        # uses of None as a query value unless the lookup supports it.
        if loo3.rhs is None and not loo3.can_use_none_as_rhs:
            if lookup4 not in ("exact", "iexact"):
                raise ValueError("Cannot use None as a query value")
            return lhs2.get_lookup("isnull")(lhs2, True)

        # For Oracle '' is equivalent to null. The check must be done at this
        # stage because join promotion can't be done in the compiler. Using
        # DEFAULT_DB_ALIAS isn't nice but it's the best that can be done here.
        # A similar thing is done in is_nullable(), too.
        if (
            lookup4 in ("exact", "iexact")
            and loo3.rhs == ""
            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
        ):
            return lhs2.get_lookup("isnull")(lhs2, True)

        return loo3

    def try2(self, lhs3, nam2, loo4=None):
        """
        Helper method for build_lookup(). Try to fetch and initialize
        a transform for name parameter from lhs.
        """
        transform2 = lhs3.get_transform(nam2)
        if transform2:
            return transform2(lhs3)
        else:
            output2 = lhs3.output_field.__class__
            suggested = difflib.get_close_matches(
                nam2, lhs3.output_field.get_lookups()
            )
            if suggested:
                sug = ", perhaps you meant %s?" % " or ".join(suggested)
            else:
                sug = "."
            if loo4 is not None:
                name2 = loo4.index(nam2)
                unsupported = LOOKUP_SEP.join(loo4[name2:])
            else:
                unsupported = nam2
            raise FieldError(
                "Unsupported lookup '%s' for %s or join on the field not "
                "permitted%s" % (unsupported, output2.__name__, sug)
            )

    def build2(
        self,
        filter,
        branch=False,
        current=False,
        can3=None,
        allow2=True,
        split3=True,
        check5=True,
        sum4=False,
        update2=True,
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
        if isinstance(filter, dict):
            raise FieldError("Cannot parse keyword query as dict")
        if isinstance(filter, Q):
            return self.add5(
                filter,
                branch_negated=branch,
                current_negated=current,
                used_aliases=can3,
                allow_joins=allow2,
                split_subq=split3,
                check_filterable=check5,
                summarize=sum4,
                update_join_types=update2,
            )
        if hasattr(filter, "resolve_expression"):
            if not getattr(filter, "conditional", False):
                raise TypeError("Cannot filter against a non-conditional expression.")
            con6 = filter.resolve_expression(
                self, allow_joins=allow2, reuse=can3, summarize=sum4
            )
            if not isinstance(con6, Lookup):
                con6 = self.build(["exact"], con6, True)
            return WhereNode([con6], connector=AND), []
        arg3, val6 = filter
        if not arg3:
            raise FieldError("Cannot parse keyword query %r" % arg3)
        loo5, par4, reffed = self.solve(arg3, sum4)

        if check5:
            self.check4(reffed)

        if not allow2 and len(par4) > 1:
            raise FieldError("Joined field references are not permitted in this query")

        pre3 = self.alias_refcount.copy()
        val6 = self.resolve2(val6, can3, allow2, sum4)
        used = {
            k2 for k2, v3 in self.alias_refcount.items() if v3 > pre3.get(k2, 0)
        }

        if check5:
            self.check4(val6)

        if reffed:
            con6 = self.build(loo5, reffed, val6)
            return WhereNode([con6], connector=AND), []

        opt8 = self.get3()
        ali22 = self.get10()
        allow3 = not branch or not split3

        try:
            join5 = self.setup(
                par4,
                opt8,
                ali22,
                can_reuse=can3,
                allow_many=allow3,
            )

            # Prevent iterator from being consumed by check_related_objects()
            if isinstance(val6, Iterator):
                val6 = list(val6)
            self.check3(join5.final_field, val6, join5.opts)

            # split_exclude() needs to know which joins were generated for the
            # lookup parts
            self._lookup_joins = join5.joins
        except MultiJoin as e:
            return self.split2(filter, can3, e.names_with_path)

        # Update used_joins before trimming since they are reused to determine
        # which joins could be later promoted to INNER.
        used.update(join5.joins)
        tar2, ali22, join6 = self.trim(
            join5.targets, join5.joins, join5.path
        )
        if can3 is not None:
            can3.update(join6)

        if join5.final_field.is_relation:
            if len(tar2) == 1:
                col11 = self.get4(tar2[0], join5.final_field, ali22)
            else:
                col11 = ColPairs(ali22, tar2, join5.targets, join5.final_field)
        else:
            col11 = self.get4(tar2[0], join5.final_field, ali22)

        con6 = self.build(loo5, col11, val6)
        lookup6 = con6.lookup_name
        cla = WhereNode([con6], connector=AND)

        require = (
            lookup6 == "isnull" and con6.rhs is True and not current
        )
        if (
            current
            and (lookup6 != "isnull" or con6.rhs is False)
            and con6.rhs is not None
        ):
            require = True
            if lookup6 != "isnull":
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
                    self.is4(tar2[0])
                    or self.alias_map[join6[-1]].join_type == LOUTER
                ):
                    lookup7 = tar2[0].get_lookup("isnull")
                    col11 = self.get4(tar2[0], join5.targets[0], ali22)
                    # Use OR + IS NULL when RHS `in` values include None.
                    if (
                        lookup6 == "in"
                        # Check containers (not strings or bytes).
                        and isinstance(con6.rhs, Iterable)
                        and not isinstance(con6.rhs, (str, bytes))
                        and any(v3 is None for v3 in con6.rhs)
                    ):
                        cla.add(lookup7(col11, True), OR)
                    else:
                        cla.add(lookup7(col11, False), AND)
                # If someval is a nullable column, someval IS NOT NULL is
                # added.
                if isinstance(val6, Col) and self.is4(val6.target):
                    lookup7 = val6.target.get_lookup("isnull")
                    cla.add(lookup7(val6, False), AND)
        return cla, used if not require else ()

    def add3(self, filter2, filter3):
        self.add4(Q((filter2, filter3)))

    def add4(self, q5, reuse4=False):
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
        existing2 = {
            a3 for a3 in self.alias_map if self.alias_map[a3].join_type == INNER
        }
        if reuse4:
            can4 = set(self.alias_map)
        else:
            can4 = self.used_aliases
        cla2, _5 = self.add5(q5, can4)
        if cla2:
            self.where.add(cla2, AND)
        self.demote2(existing2)

    def build3(self, filter4):
        return self.build2(filter4, allow_joins=False)[0]

    def clear(self):
        self.where = WhereNode()

    def add5(
        self,
        q6,
        used2,
        branch2=False,
        current2=False,
        allow4=True,
        split4=True,
        check6=True,
        sum5=False,
        update3=True,
    ):
        """Add a Q-object to the current filter."""
        con7 = q6.connector
        current2 ^= q6.negated
        branch2 = branch2 or q6.negated
        target2 = WhereNode(connector=con7, negated=q6.negated)
        joi6 = JoinPromoter(
            q6.connector, len(q6.children), current2
        )
        for chi in q6.children:
            child2, needed = self.build2(
                chi,
                can_reuse=used2,
                branch_negated=branch2,
                current_negated=current2,
                allow_joins=allow4,
                split_subq=split4,
                check_filterable=check6,
                summarize=sum5,
                update_join_types=update3,
            )
            joi6.add_votes(needed)
            if child2:
                target2.add(child2, con7)
        if update3:
            needed = joi6.update_join_types(self)
        else:
            needed = []
        return target2, needed

    def add6(self, filtered4, ali23):
        if "." in ali23:
            raise ValueError(
                "FilteredRelation doesn't support aliases with periods "
                "(got %r)." % ali23
            )
        self.check(ali23)
        filtered4.alias = ali23
        relation2, relation3, _6 = self.solve(
            filtered4.relation_name
        )
        if relation2:
            raise ValueError(
                "FilteredRelation's relation_name cannot contain lookups "
                "(got %r)." % filtered4.relation_name
            )
        for loo6 in get_children_from_q(filtered4.condition):
            lookup8, lookup9, _6 = self.solve(loo6)
            shi = 2 if not lookup8 else 1
            lookup10 = lookup9[:-shi]
            for idx2, lookup11 in enumerate(lookup10):
                if len(relation3) > idx2:
                    if relation3[idx2] != lookup11:
                        raise ValueError(
                            "FilteredRelation's condition doesn't support "
                            "relations outside the %r (got %r)."
                            % (filtered4.relation_name, loo6)
                        )
            if len(lookup9) > len(relation3) + 1:
                raise ValueError(
                    "FilteredRelation's condition doesn't support nested "
                    "relations deeper than the relation_name (got %r for "
                    "%r)." % (loo6, filtered4.relation_name)
                )
        filtered4 = filtered4.clone()
        filtered4.condition = rename_prefix_from_q(
            filtered4.relation_name,
            ali23,
            filtered4.condition,
        )
        self._filtered_relations[filtered4.alias] = filtered4

    def names2(self, nam3, opt9, allow5=True, fail=False):
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
        pat, names3 = [], []
        for pos4, nam4 in enumerate(nam3):
            cur2 = (nam4, [])
            if nam4 == "pk" and opt9 is not None:
                nam4 = opt9.pk.name

            fie7 = None
            filtered5 = None
            try:
                if opt9 is None:
                    raise FieldDoesNotExist
                fie7 = opt9.get_field(nam4)
            except FieldDoesNotExist:
                if nam4 in self.annotations:
                    fie7 = self.annotations[nam4].output_field
                elif nam4 in self._filtered_relations and pos4 == 0:
                    filtered5 = self._filtered_relations[nam4]
                    if LOOKUP_SEP in filtered5.relation_name:
                        par5 = filtered5.relation_name.split(LOOKUP_SEP)
                        filtered6, fie7, _7, _7 = self.names2(
                            par5,
                            opt9,
                            allow5,
                            fail,
                        )
                        pat.extend(filtered6[:-1])
                    else:
                        fie7 = opt9.get_field(filtered5.relation_name)
            if fie7 is not None:
                # Fields that contain one-to-many relations with a generic
                # model (like a GenericForeignKey) cannot generate reverse
                # relations and therefore cannot be used for reverse querying.
                if fie7.is_relation and not fie7.related_model:
                    raise FieldError(
                        "Field %r does not generate an automatic reverse "
                        "relation and therefore cannot be used for reverse "
                        "querying. If it is a GenericForeignKey, consider "
                        "adding a GenericRelation." % nam4
                    )
                try:
                    mod3 = fie7.model._meta.concrete_model
                except AttributeError:
                    # QuerySet.annotate() may introduce fields that aren't
                    # attached to a model.
                    mod3 = None
            else:
                # We didn't find the current field, so move position back
                # one step.
                pos4 -= 1
                if pos4 == -1 or fail:
                    ava = sorted(
                        [
                            *get_field_names_from_opts(opt9),
                            *self.annotations,
                            *self._filtered_relations,
                        ]
                    )
                    raise FieldError(
                        "Cannot resolve keyword '%s' into field. "
                        "Choices are: %s" % (nam4, ", ".join(ava))
                    )
                break
            # Check if we need any joins for concrete inheritance cases (the
            # field lives in parent, but we are currently in one of its
            # children)
            if opt9 is not None and mod3 is not opt9.model:
                path2 = opt9.get_path_to_parent(mod3)
                if path2:
                    pat.extend(path2)
                    cur2[1].extend(path2)
                    opt9 = path2[-1].to_opts
            if hasattr(fie7, "path_infos"):
                if filtered5:
                    pat2 = fie7.get_path_info(filtered5)
                else:
                    pat2 = fie7.path_infos
                if not allow5:
                    for inner2, p2 in enumerate(pat2):
                        if p2.m2m:
                            cur2[1].extend(pat2[0 : inner2 + 1])
                            names3.append(cur2)
                            raise MultiJoin(pos4 + 1, names3)
                las = pat2[-1]
                pat.extend(pat2)
                final = las.join_field
                opt9 = las.to_opts
                tar3 = las.target_fields
                cur2[1].extend(pat2)
                names3.append(cur2)
            else:
                # Local non-relational field.
                final = fie7
                tar3 = (fie7,)
                if fail and pos4 + 1 != len(nam3):
                    raise FieldError(
                        "Cannot resolve keyword %r into field. Join on '%s'"
                        " not permitted." % (nam3[pos4 + 1], nam4)
                    )
                break
        return pat, final, tar3, nam3[pos4 + 1 :]

    def setup(
        self,
        nam5,
        opt10,
        ali24,
        can5=None,
        allow6=True,
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
        joi7 = [ali24]
        # The transform can't be applied yet, as joins must be trimmed later.
        # To avoid making every caller of this method look up transforms
        # directly, compute transforms here and create a partial that converts
        # fields to the appropriate wrapped version.

        def final_transformer(fie8, ali25):
            if not self.alias_cols:
                ali25 = None
            return fie8.get_col(ali25)

        # Try resolving all the names as fields first. If there's an error,
        # treat trailing names as lookups until a field can be resolved.
        last2 = None
        for piv in range(len(nam5), 0, -1):
            try:
                pat3, final2, tar4, res4 = self.names2(
                    nam5[:piv],
                    opt10,
                    allow6,
                    fail_on_missing=True,
                )
            except FieldError as exc:
                if piv == 1:
                    # The first item cannot be a lookup, so it's safe
                    # to raise the field error here.
                    raise
                else:
                    last2 = exc
            else:
                # The transforms are the remaining items that couldn't be
                # resolved into fields.
                tra2 = nam5[piv:]
                break
        for nam6 in tra2:

            def transform(fie9, ali26, *, nam7, pre4):
                try:
                    wra2 = pre4(fie9, ali26)
                    return self.try2(wra2, nam7)
                except FieldError:
                    # FieldError is raised if the transform doesn't exist.
                    if isinstance(final_field, Field) and last_field_exception:
                        raise last_field_exception
                    else:
                        raise

            final3 = functools.partial(
                transform, name=nam6, previous=final3
            )
            final3.has_transforms = True
        # Then, add the path to the query's joins. Note that we can't trim
        # joins at this stage - we will need the information about join type
        # of the trimmed joins.
        for joi8 in pat3:
            if joi8.filtered_relation:
                filtered7 = joi8.filtered_relation.clone()
                table5 = filtered7.alias
            else:
                filtered7 = None
                table5 = None
            opt10 = joi8.to_opts
            if joi8.direct:
                nul = self.is4(joi8.join_field)
            else:
                nul = True
            con8 = self.join_class(
                opt10.db_table,
                ali24,
                table5,
                INNER,
                joi8.join_field,
                nul,
                filtered_relation=filtered7,
            )
            reu3 = can5 if joi8.m2m else None
            ali24 = self.joi(con8, reuse=reu3)
            joi7.append(ali24)
            if joi8.filtered_relation and can5 is not None:
                can5.add(ali24)
        return JoinInfo(final2, tar4, opt10, joi7, pat3, final3)

    def trim(self, tar5, joi9, pat4):
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
        joi9 = joi9[:]
        for pos5, inf in enumerate(reversed(pat4)):
            if len(joi9) == 1 or not inf.direct:
                break
            if inf.filtered_relation:
                break
            join7 = {t2.column for t2 in inf.join_field.foreign_related_fields}
            cur3 = {t2.column for t2 in tar5}
            if not cur3.issubset(join7):
                break
            targets2 = {
                r2[1].column: r2[0]
                for r2 in inf.join_field.related_fields
                if r2[1].column in cur3
            }
            tar5 = tuple(targets2[t2.column] for t2 in tar5)
            self.unref(joi9.pop())
        return tar5, joi9[-1], joi9

    @classmethod
    def gen(cls, exp9, include=False, resolve5=True):
        for exp10 in exp9:
            if isinstance(exp10, Col):
                yield exp10
            elif include and callable(
                getattr(exp10, "get_external_cols", None)
            ):
                yield from exp10.get_external_cols()
            elif hasattr(exp10, "get_source_expressions"):
                if not resolve5 and isinstance(exp10, Ref):
                    continue
                yield from cls.gen(
                    exp10.get_source_expressions(),
                    include_external=include,
                    resolve_refs=resolve5,
                )

    @classmethod
    def gen2(cls, exp11):
        yield from (exp12.alias for exp12 in cls.gen(exp11))

    def resolve3(self, nam8, allow7=True, reu4=None, sum6=False):
        ann4 = self.annotations.get(nam8)
        if ann4 is not None:
            if not allow7:
                for ali27 in self.gen2([ann4]):
                    if isinstance(self.alias_map[ali27], Join):
                        raise FieldError(
                            "Joined field references are not permitted in this query"
                        )
            if sum6:
                # Summarize currently means we are doing an aggregate() query
                # which is executed as a wrapped subquery if any of the
                # aggregate() elements reference an existing annotation. In
                # that case we need to return a Ref to the subquery's
                # annotation.
                if nam8 not in self.annotation2:
                    raise FieldError(
                        "Cannot aggregate over the '%s' alias. Use annotate() "
                        "to promote it." % nam8
                    )
                return Ref(nam8, self.annotation2[nam8])
            else:
                return ann4
        else:
            field13 = nam8.split(LOOKUP_SEP)
            ann4 = self.annotations.get(field13[0])
            if ann4 is not None:
                for tra3 in field13[1:]:
                    ann4 = self.try2(ann4, tra3)
                return ann4
            join8 = self.setup(
                field13, self.get3(), self.get10(), can_reuse=reu4
            )
            tar6, final4, join9 = self.trim(
                join8.targets, join8.joins, join8.path
            )
            if not allow7 and len(join9) > 1:
                raise FieldError(
                    "Joined field references are not permitted in this query"
                )
            if len(tar6) > 1:
                raise FieldError(
                    "Referencing multicolumn fields with F() objects isn't supported"
                )
            # Verify that the last lookup in name is a field or a transform:
            # transform_function() raises FieldError if not.
            tra3 = join8.transform_function(tar6[0], final4)
            if reu4 is not None:
                reu4.update(join9)
            return tra3

    def split2(self, filter5, can6, names4):
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
        que4 = self.__class__(self.model)
        que4._filtered_relations = self._filtered_relations
        filter6, filter7 = filter5
        if isinstance(filter7, OuterRef):
            filter7 = OuterRef(filter7)
        elif isinstance(filter7, F):
            filter7 = OuterRef(filter7.name)
        que4.add_filter(filter6, filter7)
        que4.clear_ordering(force=True)
        # Try to have as simple as possible subquery -> trim leading joins from
        # the subquery.
        trimmed, contains = que4.trim_start(names4)

        col12 = que4.select[0]
        select4 = col12.target
        ali28 = col12.alias
        if ali28 in can6:
            pk2 = select4.model._meta.pk
            # Need to add a restriction so that outer query's filters are in
            # effect for the subquery, too.
            que4.bump_prefix(self)
            lookup12 = select4.get_lookup("exact")
            # Note that the query.select[0].alias is different from alias
            # due to bump_prefix above.
            loo7 = lookup12(pk2.get_col(que4.select[0].alias), pk2.get_col(ali28))
            que4.where.add(loo7, AND)
            que4.external_aliases[ali28] = True
        else:
            lookup12 = select4.get_lookup("exact")
            loo7 = lookup12(col12, ResolvedOuterRef(trimmed))
            que4.where.add(loo7, AND)

        con9, needed2 = self.build2(Exists(que4))

        if contains:
            or2, _8 = self.build2(
                ("%s__isnull" % trimmed, True),
                current_negated=True,
                branch_negated=True,
                can_reuse=can6,
            )
            con9.add(or2, OR)
            # Note that the end result will be:
            #   NOT EXISTS (inner_q) OR outercol IS NULL
            # this might look crazy but due to how NULL works, this seems to be
            # correct. If the IS NULL check is removed, then if outercol
            # IS NULL we will not match the row.
        return con9, needed2

    def set2(self):
        self.where.add(NothingNode(), AND)
        for que5 in self.combined_queries:
            que5.set_empty()

    def is2(self):
        return any(isinstance(c2, NothingNode) for c2 in self.where.children)

    def set3(self, low2=None, hig=None):
        """
        Adjust the limits on the rows retrieved. Use low/high to set these,
        as it makes it more Pythonic to read and write. When the SQL query is
        created, convert them to the appropriate offset and limit values.

        Apply any limits passed in here to the existing constraints. Add low
        to the current low value and clamp both to any existing high value.
        """
        if hig is not None:
            if self.high_mark is not None:
                self.high_mark = min(self.high_mark, self.low_mark + hig)
            else:
                self.high_mark = self.low_mark + hig
        if low2 is not None:
            if self.high_mark is not None:
                self.low_mark = min(self.high_mark, self.low_mark + low2)
            else:
                self.low_mark = self.low_mark + low2

        if self.low_mark == self.high_mark:
            self.set2()

    def clear2(self):
        """Clear any existing limits."""
        self.low_mark, self.high_mark = 0, None

    @property
    def is3(self):
        return self.low_mark != 0 or self.high_mark is not None

    def has3(self):
        return self.high_mark is not None and (self.high_mark - self.low_mark) == 1

    def can(self):
        """
        Return True if adding filters to this instance is still possible.

        Typically, this means no limits or offsets have been put on the
        results.
        """
        return not self.is3

    def clear3(self):
        """Remove all fields from SELECT clause."""
        self.select = ()
        self.default_cols = False
        self.select_related = False
        self.set7(())
        self.set6(())
        self.selected = None

    def clear4(self):
        """
        Clear the list of fields to select (but not extra_select columns).
        Some queryset types completely replace any existing list of select
        columns.
        """
        self.select = ()
        self.values_select = ()
        self.selected = None

    def add7(self, col13, nam9):
        self.select += (col13,)
        self.values_select += (nam9,)
        self.selected[nam9] = len(self.select) - 1

    def set4(self, col14):
        self.default_cols = False
        self.select = tuple(col14)

    def add8(self, *field14):
        """
        Add and resolve the given fields to the query's "distinct on" clause.
        """
        self.distinct_fields = field14
        self.distinct = True

    def add9(self, field15, allow8=True):
        """
        Add the given (model) fields to the select set. Add the field names in
        the order specified.
        """
        ali29 = self.get10()
        opt11 = self.get3()

        try:
            col15 = []
            for nam10 in field15:
                # Join promotion note - we must not remove any rows here, so
                # if there is no existing joins, use outer join.
                join10 = self.setup(
                    nam10.split(LOOKUP_SEP), opt11, ali29, allow_many=allow8
                )
                tar7, final5, joi10 = self.trim(
                    join10.targets,
                    join10.joins,
                    join10.path,
                )
                if len(tar7) > 1:
                    transformed = [
                        join10.transform_function(tar8, final5)
                        for tar8 in tar7
                    ]
                    col15.append(
                        ColPairs(
                            final5 if self.alias_cols else None,
                            [col16.target for col16 in transformed],
                            [col16.output_field for col16 in transformed],
                            join10.final_field,
                        )
                    )
                else:
                    col15.append(join10.transform_function(tar7[0], final5))
            if col15:
                self.set4(col15)
        except MultiJoin:
            raise FieldError("Invalid field name: '%s'" % nam10)
        except FieldError:
            if LOOKUP_SEP in nam10:
                # For lookups spanning over relationships, show the error
                # from the model on which the lookup failed.
                raise
            else:
                nam11 = sorted(
                    [
                        *get_field_names_from_opts(opt11),
                        *self.extra,
                        *self.annotation2,
                        *self._filtered_relations,
                    ]
                )
                raise FieldError(
                    "Cannot resolve keyword %r into field. "
                    "Choices are: %s" % (nam10, ", ".join(nam11))
                )

    def add10(self, *ord2):
        """
        Add items from the 'ordering' sequence to the query's "order by"
        clause. These items are either field names (not column names) --
        possibly with a direction prefix ('-' or '?') -- or OrderBy
        expressions.

        If 'ordering' is empty, clear all ordering from the query.
        """
        err = []
        for ite in ord2:
            if isinstance(ite, str):
                if ite == "?":
                    continue
                ite = ite.removeprefix("-")
                if ite in self.annotations:
                    continue
                if self.extra and ite in self.extra:
                    continue
                # names_to_path() validates the lookup. A descriptive
                # FieldError will be raise if it's not.
                self.names2(ite.split(LOOKUP_SEP), self.model._meta)
            elif not hasattr(ite, "resolve_expression"):
                err.append(ite)
            if getattr(ite, "contains_aggregate", False):
                raise FieldError(
                    "Using an aggregate in order_by() without also including "
                    "it in annotate() is not allowed: %s" % ite
                )
        if err:
            raise FieldError("Invalid order_by arguments: %s" % err)
        if ord2:
            self.order_by += ord2
        else:
            self.default_ordering = False

    @property
    def orderby(self):
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
        q7 = self.clo()
        order = set()
        for order2 in q7.order_by:
            if hasattr(order2, "resolve_expression"):
                order.add(order2.resolve_expression(q7))
            elif order2 == "?":
                # Random ordering can't be compared against group by.
                return False
            else:
                order.add(F(order2.removeprefix("-")).resolve_expression(q7))
        return order.issubset(self.group_by)

    def clear5(self, for3=False, clear7=True):
        """
        Remove any ordering settings if the current query allows it without
        side effects, set 'force' to True to clear the ordering regardless.
        If 'clear_default' is True, there will be no ordering in the resulting
        query (not even the model's default).
        """
        if not for3 and (
            self.is3 or self.distinct_fields or self.select_for_update
        ):
            return
        self.order_by = ()
        self.extra_order_by = ()
        if clear7:
            self.default_ordering = False
        # Ordering is cleared on combined queries with clear_default=False
        # when union() and analogues are called, so percolate any possible
        # clear_default=True.
        for que6 in self.combined_queries:
            que6.clear_ordering(force=False, clear_default=clear7)

    def set5(self, allow9=True):
        """
        Expand the GROUP BY clause required by the query.

        This will usually be the set of all non-aggregate fields in the
        return data. If the database backend supports grouping by the
        primary key, and the query would be equivalent, the optimization
        will be made automatically.
        """
        if allow9 and self.values_select:
            # If grouping by aliases is allowed assign selected value aliases
            # by moving them to annotations.
            group = {}
            values2 = {}
            for ali30, exp13 in zip(self.values_select, self.select):
                if isinstance(exp13, Col):
                    values2[ali30] = exp13
                else:
                    group[ali30] = exp13
            self.annotations = {**group, **self.annotations}
            self.append2(group)
            self.select = tuple(values2.values())
            self.values_select = tuple(values2)
            if self.selected is not None:
                for ind2, value2 in enumerate(values2):
                    self.selected[value2] = ind2
        group2 = list(self.select)
        for ali30, ann5 in self.annotation2.items():
            if not (group3 := ann5.get_group_by_cols()):
                continue
            if allow9 and not ann5.contains_aggregate:
                group2.append(Ref(ali30, ann5))
            else:
                group2.extend(group3)
        self.group_by = tuple(group2)

    def add11(self, fie10):
        """
        Set up the select_related data structure so that we only select
        certain related models (as opposed to all models, when
        self.select_related=True).
        """
        if isinstance(self.select_related, bool):
            field16 = {}
        else:
            field16 = self.select_related
        for fie11 in fie10:
            d2 = field16
            for par6 in fie11.split(LOOKUP_SEP):
                d2 = d2.setdefault(par6, {})
        self.select_related = field16

    def add12(self, sel3, select5, whe, par7, tab2, order3):
        """
        Add data to the various extra_* attributes for user-created additions
        to the query.
        """
        if sel3:
            # We need to pair any placeholder markers in the 'select'
            # dictionary with their parameters in 'select_params' so that
            # subsequent updates to the select dictionary also adjust the
            # parameters appropriately.
            select6 = {}
            if select5:
                param = iter(select5)
            else:
                param = iter([])
            for nam12, ent in sel3.items():
                self.check(nam12)
                ent = str(ent)
                entry2 = []
                pos6 = ent.find("%s")
                while pos6 != -1:
                    if pos6 == 0 or ent[pos6 - 1] != "%":
                        entry2.append(next(param))
                    pos6 = ent.find("%s", pos6 + 2)
                select6[nam12] = (ent, entry2)
            self.extra.update(select6)
        if whe or par7:
            self.where.add(ExtraWhere(whe, par7), AND)
        if tab2:
            self.extra_tables += tuple(tab2)
        if order3:
            self.extra_order_by = order3

    def clear6(self):
        """Remove any fields from the deferred loading set."""
        self.deferred_loading = (frozenset(), True)

    def add13(self, field17):
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
        exi2, def3 = self.deferred_loading
        if def3:
            # Add to existing deferred names.
            self.deferred_loading = exi2.union(field17), True
        else:
            # Remove names from the set of any existing "immediate load" names.
            if new3 := exi2.difference(field17):
                self.deferred_loading = new3, False
            else:
                self.clear6()
                if new4 := set(field17).difference(exi2):
                    self.deferred_loading = new4, True

    def add14(self, field18):
        """
        Add the given list of model field names to the set of fields to
        retrieve when the SQL is executed ("immediate loading" fields). The
        field names replace any existing immediate loading field names. If
        there are field names already specified for deferred loading, remove
        those names from the new field_names before storing the new names
        for immediate loading. (That is, immediate loading overrides any
        existing immediate values, but respects existing deferrals.)
        """
        exi3, def4 = self.deferred_loading
        field18 = set(field18)
        if "pk" in field18:
            field18.remove("pk")
            field18.add(self.get3().pk.name)

        if def4:
            # Remove any existing deferred names from the current set before
            # setting the new names.
            self.deferred_loading = field18.difference(exi3), False
        else:
            # Replace any existing "immediate load" field names.
            self.deferred_loading = frozenset(field18), False

    def set6(self, nam13):
        """Set the mask of annotations that will be returned by the SELECT."""
        if nam13 is None:
            self.annotation_select_mask = None
        else:
            self.annotation_select_mask = set(nam13)
            if self.selected:
                # Prune the masked annotations.
                self.selected = {
                    key4: val7
                    for key4, val7 in self.selected.items()
                    if not isinstance(val7, str)
                    or val7 in self.annotation_select_mask
                }
                # Append the unmasked annotations.
                for nam14 in nam13:
                    self.selected[nam14] = nam14
        self._annotation_select_cache = None

    def append2(self, nam15):
        if self.annotation_select_mask is not None:
            self.set6(self.annotation_select_mask.union(nam15))

    def set7(self, nam16):
        """
        Set the mask of extra select items that will be returned by SELECT.
        Don't remove them from the Query since they might be used later.
        """
        if nam16 is None:
            self.extra_select_mask = None
        else:
            self.extra_select_mask = set(nam16)
        self._extra_select_cache = None

    @property
    def has4(self):
        return self.selected is not None

    def set8(self, fie12):
        self.select_related = False
        self.clear6()
        self.clear4()

        sel4 = {}
        if fie12:
            for fie13 in fie12:
                self.check(fie13)
            field19 = []
            extra4 = []
            annotation6 = []
            if not self.extra and not self.annotations:
                # Shortcut - if there are no extra or annotations, then
                # the values() clause must be just field names.
                field19 = list(fie12)
                sel4 = dict(zip(fie12, range(len(fie12))))
            else:
                self.default_cols = False
                for f3 in fie12:
                    if ext := self.extra2.get(f3):
                        extra4.append(f3)
                        sel4[f3] = RawSQL(*ext)
                    elif f3 in self.annotation2:
                        annotation6.append(f3)
                        sel4[f3] = f3
                    elif f3 in self.annotations:
                        if self.annotation2:
                            raise FieldError(
                                f"Cannot select the '{f3}' alias. It was excluded "
                                f"by a previous values() or values_list() call. "
                                f"Include '{f3}' in that call to select it."
                            )
                        else:
                            raise FieldError(
                                f"Cannot select the '{f3}' alias. Use annotate() "
                                f"to promote it."
                            )
                    else:
                        # Call `names_to_path` to ensure a FieldError including
                        # annotations about to be masked as valid choices if
                        # `f` is not resolvable.
                        if self.annotation2:
                            self.names2(f3.split(LOOKUP_SEP), self.model._meta)
                        sel4[f3] = len(field19)
                        field19.append(f3)
            self.set7(extra4)
            self.set6(annotation6)
        else:
            field19 = [f3.attname for f3 in self.model._meta.concrete_fields]
            sel4 = dict.fromkeys(field19, None)
        # Selected annotations must be known before setting the GROUP BY
        # clause.
        if self.group_by is True:
            self.add9(
                (f3.attname for f3 in self.model._meta.concrete_fields), False
            )
            # Disable GROUP BY aliases to avoid orphaning references to the
            # SELECT clause which is about to be cleared.
            self.set5(allow_aliases=False)
            self.clear4()
        elif self.group_by:
            # Resolve GROUP BY annotation references if they are not part of
            # the selected fields anymore.
            group4 = []
            for exp14 in self.group_by:
                if isinstance(exp14, Ref) and exp14.refs not in sel4:
                    exp14 = self.annotations[exp14.refs]
                group4.append(exp14)
            self.group_by = tuple(group4)

        self.values_select = tuple(field19)
        self.add9(field19, True)
        self.selected = sel4 if fie12 else None

    @property
    def annotation2(self):
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
                k3: v4
                for k3, v4 in self.annotations.items()
                if k3 in self.annotation_select_mask
            }
            return self._annotation_select_cache
        else:
            return self.annotations

    @property
    def extra2(self):
        if self._extra_select_cache is not None:
            return self._extra_select_cache
        if not self.extra:
            return {}
        elif self.extra_select_mask is not None:
            self._extra_select_cache = {
                k4: v5 for k4, v5 in self.extra.items() if k4 in self.extra_select_mask
            }
            return self._extra_select_cache
        else:
            return self.extra

    def trim2(self, names5):
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
        all = []
        for _9, pat5 in names5:
            all.extend(pat5)
        contains2 = False
        # Trim and operate only on tables that were generated for
        # the lookup part of the query. That is, avoid trimming
        # joins generated for F() expressions.
        lookup13 = [
            t3 for t3 in self.alias_map if t3 in self._lookup_joins or t3 == self.base
        ]
        for trimmed2, pat6 in enumerate(all):
            if pat6.m2m:
                break
            if self.alias_map[lookup13[trimmed2 + 1]].join_type == LOUTER:
                contains2 = True
            ali31 = lookup13[trimmed2]
            self.unref(ali31)
        # The path.join_field is a Rel, lets get the other side's field
        join11 = pat6.join_field.field
        # Build the filter prefix.
        paths2 = trimmed2
        trimmed3 = []
        for nam17, pat6 in names5:
            if paths2 - len(pat6) < 0:
                break
            trimmed3.append(nam17)
            paths2 -= len(pat6)
        trimmed3.append(join11.foreign_related_fields[0].name)
        trimmed3 = LOOKUP_SEP.join(trimmed3)
        # Lets still see if we can trim the first join from the inner query
        # (that is, self). We can't do this for:
        # - LEFT JOINs because we would miss those rows that have nothing on
        #   the outer side,
        # - INNER JOINs from filtered relations because we would miss their
        #   filters.
        first = self.alias_map[lookup13[trimmed2 + 1]]
        if first.join_type != LOUTER and not first.filtered_relation:
            select7 = [r3[0] for r3 in join11.related_fields]
            select8 = lookup13[trimmed2 + 1]
            self.unref(lookup13[trimmed2])
            extra5 = join11.get_extra_restriction(
                None, lookup13[trimmed2 + 1]
            )
            if extra5:
                self.where.add(extra5, AND)
        else:
            # TODO: It might be possible to trim more joins from the start of
            # the inner query if it happens to have a longer join chain
            # containing the values in select_fields. Lets punt this one for
            # now.
            select7 = [r3[1] for r3 in join11.related_fields]
            select8 = lookup13[trimmed2]
        # The found starting point is likely a join_class instead of a
        # base_table_class reference. But the first entry in the query's FROM
        # clause must not be a JOIN.
        for tab3 in self.alias_map:
            if self.alias_refcount[tab3] > 0:
                self.alias_map[tab3] = self.base_table_class(
                    self.alias_map[tab3].table_name,
                    tab3,
                )
                break
        self.set4([f4.get_col(select8) for f4 in select7])
        return trimmed3, contains2

    def is4(self, fie14):
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
        return fie14.null or (
            fie14.empty_strings_allowed
            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
        )
