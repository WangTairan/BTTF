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

     
     
     
     
     
    select = ()
     
     
     
     
     
     
    group_by = None
    order_by = ()
    low_mark = 0   
    high_mark = None   
    distinct = False
    distinct_fields = ()
    select_for_update = False
    select_for_update_nowait = False
    select_for_update_skip_locked = False
    select_for_update_of = ()
    select_for_no_key_update = False
    select_related = False
     
    max_depth = 5
     
     
    values_select = ()
    selected = None

     
    annotation_select_mask = None
    _annotation_select_cache = None

     
    combinator = None
    combinator_all = False
    combined_queries = ()

     
     
    extra_select_mask = None
    _extra_select_cache = None

    extra_tables = ()
    extra_order_by = ()

     
     
    deferred_loading = (frozenset(), True)

    explain_info = None

    def __init__(self, model, alias_cols=True):
        self.model = model
        self.alias_refcount = {}
         
         
         
         
         
        self.alias_map = {}
         
        self.alias_cols = alias_cols
         
         
         
        self.external_aliases = {}
        self.table_map = {}   
        self.used_aliases = set()

        self.where = WhereNode()
         
        self.annotations = {}
         
         
        self.extra = {}   

        self._filtered_relations = {}

    @property
    def output_field(self):
        if len(self.select) == 1:
            select = self.select[0]
            return getattr(select, "target", None) or select.field
        elif len(self.annotation_select) == 1:
            return next(iter(self.annotation_select.values())).output_field

    @cached_property
    def base_table(self):
        for alias in self.alias_map:
            return alias

    def __str__(self):
        
        sql, params = self.sql_with_params()
        return sql % params

    def sql_with_params(self):
        
        return self.get_compiler(DEFAULT_DB_ALIAS).as_sql()

    def __deepcopy__(self, memo):
        
        result = self.clone()
        memo[id(self)] = result
        return result

    def get_compiler(self, using=None, connection=None, elide_empty=True):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return connection.ops.compiler(self.compiler)(
            self, connection, using, elide_empty
        )

    def get_meta(self):
        
        if self.model:
            return self.model._meta

    def clone(self):
        
        obj = Empty()
        obj.__class__ = self.__class__
         
        obj.__dict__ = self.__dict__.copy()
         
        obj.alias_refcount = self.alias_refcount.copy()
        obj.alias_map = self.alias_map.copy()
        obj.external_aliases = self.external_aliases.copy()
        obj.table_map = self.table_map.copy()
        obj.where = self.where.clone()
        obj.annotations = self.annotations.copy()
        if self.annotation_select_mask is not None:
            obj.annotation_select_mask = self.annotation_select_mask.copy()
        if self.combined_queries:
            obj.combined_queries = tuple(
                [query.clone() for query in self.combined_queries]
            )
         
         
         
         
         
        obj._annotation_select_cache = None
        obj.extra = self.extra.copy()
        if self.extra_select_mask is not None:
            obj.extra_select_mask = self.extra_select_mask.copy()
        if self._extra_select_cache is not None:
            obj._extra_select_cache = self._extra_select_cache.copy()
        if self.select_related is not False:
             
             
            obj.select_related = copy.deepcopy(obj.select_related)
        if "subq_aliases" in self.__dict__:
            obj.subq_aliases = self.subq_aliases.copy()
        obj.used_aliases = self.used_aliases.copy()
        obj._filtered_relations = self._filtered_relations.copy()
         
        obj.__dict__.pop("base_table", None)
        return obj

    def chain(self, klass=None):
        
        obj = self.clone()
        if klass and obj.__class__ != klass:
            obj.__class__ = klass
        if not obj.filter_is_sticky:
            obj.used_aliases = set()
        obj.filter_is_sticky = False
        if hasattr(obj, "_setup_query"):
            obj._setup_query()
        return obj

    def relabeled_clone(self, change_map):
        clone = self.clone()
        clone.change_aliases(change_map)
        return clone

    def _get_col(self, target, field, alias):
        if not self.alias_cols:
            alias = None
        return target.get_col(alias, field)

    def get_aggregation(self, using, aggregate_exprs):
        
        if not aggregate_exprs:
            return {}
         
         
        refs_subquery = False
        refs_window = False
        replacements = {}
        annotation_select_mask = self.annotation_select_mask
        for alias, aggregate_expr in aggregate_exprs.items():
            self.check_alias(alias)
            aggregate = aggregate_expr.resolve_expression(
                self, allow_joins=True, reuse=None, summarize=True
            )
            if not aggregate.contains_aggregate:
                raise TypeError("%s is not an aggregate expression" % alias)
             
             
            self.append_annotation_mask([alias])
            aggregate_refs = aggregate.get_refs()
            refs_subquery |= any(
                getattr(self.annotations[ref], "contains_subquery", False)
                for ref in aggregate_refs
            )
            refs_window |= any(
                getattr(self.annotations[ref], "contains_over_clause", True)
                for ref in aggregate_refs
            )
            aggregate = aggregate.replace_expressions(replacements)
            self.annotations[alias] = aggregate
            replacements[Ref(alias, aggregate)] = aggregate
         
         
        aggregates = {alias: self.annotations.pop(alias) for alias in aggregate_exprs}
        self.set_annotation_mask(annotation_select_mask)
         
         
        _, having, qualify = self.where.split_having_qualify()
        has_existing_aggregation = (
            any(
                getattr(annotation, "contains_aggregate", True)
                for annotation in self.annotations.values()
            )
            or having
        )
        set_returning_annotations = {
            alias
            for alias, annotation in self.annotation_select.items()
            if getattr(annotation, "set_returning", False)
        }
         
         
         
         
         
         
         
         
         
         
        if (
            isinstance(self.group_by, tuple)
            or self.is_sliced
            or has_existing_aggregation
            or refs_subquery
            or refs_window
            or qualify
            or self.distinct
            or self.combinator
            or set_returning_annotations
        ):
            from django.db.models.sql.subqueries import AggregateQuery

            inner_query = self.clone()
            inner_query.subquery = True
            outer_query = AggregateQuery(self.model, inner_query)
            inner_query.select_for_update = False
            inner_query.select_related = False
            inner_query.set_annotation_mask(self.annotation_select)
             
             
             
            if inner_query.orderby_issubset_groupby:
                inner_query.clear_ordering(force=False)
            if not inner_query.distinct:
                 
                 
                 
                 
                 
                if inner_query.default_cols and has_existing_aggregation:
                    inner_query.group_by = (
                        self.model._meta.pk.get_col(inner_query.get_initial_alias()),
                    )
                inner_query.default_cols = False
                if not qualify and not self.combinator:
                     
                     
                     
                     
                    annotation_mask = set()
                    if isinstance(self.group_by, tuple):
                        for expr in self.group_by:
                            annotation_mask |= expr.get_refs()
                    for aggregate in aggregates.values():
                        annotation_mask |= aggregate.get_refs()
                     
                     
                    for annotation_alias, annotation in self.annotation_select.items():
                        if annotation.get_group_by_cols():
                            annotation_mask.add(annotation_alias)
                    inner_query.set_annotation_mask(annotation_mask)
                     
                     
                    annotation_mask |= set_returning_annotations

             
             
             
             
             
            col_refs = {}
            for alias, aggregate in aggregates.items():
                replacements = {}
                for col in self._gen_cols([aggregate], resolve_refs=False):
                    if not (col_ref := col_refs.get(col)):
                        index = len(col_refs) + 1
                        col_alias = f"__col{index}"
                        col_ref = Ref(col_alias, col)
                        col_refs[col] = col_ref
                        inner_query.add_annotation(col, col_alias)
                    replacements[col] = col_ref
                outer_query.annotations[alias] = aggregate.replace_expressions(
                    replacements
                )
            if (
                inner_query.select == ()
                and not inner_query.default_cols
                and not inner_query.annotation_select_mask
            ):
                 
                 
                 
                inner_query.select = (
                    self.model._meta.pk.get_col(inner_query.get_initial_alias()),
                )
        else:
            outer_query = self
            self.select = ()
            self.selected = None
            self.default_cols = False
            self.extra = {}
            if self.annotations:
                 
                 
                 
                replacements = {
                    Ref(alias, annotation): annotation
                    for alias, annotation in self.annotations.items()
                }
                self.annotations = {
                    alias: aggregate.replace_expressions(replacements)
                    for alias, aggregate in aggregates.items()
                }
            else:
                self.annotations = aggregates
            self.set_annotation_mask(aggregates)

        empty_set_result = [
            expression.empty_result_set_value
            for expression in outer_query.annotation_select.values()
        ]
        elide_empty = not any(result is NotImplemented for result in empty_set_result)
        outer_query.clear_ordering(force=True)
        outer_query.clear_limits()
        outer_query.select_for_update = False
        outer_query.select_related = False
        compiler = outer_query.get_compiler(using, elide_empty=elide_empty)
        result = compiler.execute_sql(SINGLE)
        if result is None:
            result = empty_set_result
        else:
            cols = outer_query.annotation_select.values()
            converters = compiler.get_converters(cols)
            rows = compiler.apply_converters((result,), converters)
            if compiler.has_composite_fields(cols):
                rows = compiler.composite_fields_to_tuples(rows, cols)
            result = next(rows)

        return dict(zip(outer_query.annotation_select, result))

    def get_count(self, using):
        
        obj = self.clone()
        return obj.get_aggregation(using, {"__count": Count("*")})["__count"]

    def has_filters(self):
        return self.where

    def exists(self, limit=True):
        q = self.clone()
        if not (q.distinct and q.is_sliced):
            if q.group_by is True:
                q.add_fields(
                    (f.attname for f in self.model._meta.concrete_fields), False
                )
                 
                 
                q.set_group_by(allow_aliases=False)
            q.clear_select_clause()
        if q.combined_queries and q.combinator == "union":
            q.combined_queries = tuple(
                combined_query.exists(limit=False)
                for combined_query in q.combined_queries
            )
        q.clear_ordering(force=True)
        if limit is True:
            q.set_limits(high=1)
        q.add_annotation(Value(1), "a")
        return q

    def has_results(self, using):
        q = self.exists()
        compiler = q.get_compiler(using=using)
        return compiler.has_results()

    def explain(self, using, format=None, **options):
        q = self.clone()
        for option_name in options:
            if (
                not EXPLAIN_OPTIONS_PATTERN.fullmatch(option_name)
                or "--" in option_name
            ):
                raise ValueError(f"Invalid option name: {option_name!r}.")
        q.explain_info = ExplainInfo(format, options)
        compiler = q.get_compiler(using=using)
        return "\n".join(compiler.explain_query())

    def combine(self, rhs, connector):
        
        if self.model != rhs.model:
            raise TypeError("Cannot combine queries on two different base models.")
        if self.is_sliced:
            raise TypeError("Cannot combine queries once a slice has been taken.")
        if self.distinct != rhs.distinct:
            raise TypeError("Cannot combine a unique query with a non-unique query.")
        if self.distinct_fields != rhs.distinct_fields:
            raise TypeError("Cannot combine queries with different distinct fields.")

         
         
         
         
         
         
        initial_alias = self.get_initial_alias()
        rhs = rhs.clone()
        rhs.bump_prefix(self, exclude={initial_alias})

         
        change_map = {}
        conjunction = connector == AND

         
         
         
         
         
         
         
         
         
         
         
         
        reuse = set() if conjunction else set(self.alias_map)
        joinpromoter = JoinPromoter(connector, 2, False)
        joinpromoter.add_votes(
            j for j in self.alias_map if self.alias_map[j].join_type == INNER
        )
        rhs_votes = set()
         
         
        rhs_tables = list(rhs.alias_map)[1:]
        for alias in rhs_tables:
            join = rhs.alias_map[alias]
             
             
            join = join.relabeled_clone(change_map)
            new_alias = self.join(join, reuse=reuse)
            if join.join_type == INNER:
                rhs_votes.add(new_alias)
             
             
             
            reuse.discard(new_alias)
            if alias != new_alias:
                change_map[alias] = new_alias
            if not rhs.alias_refcount[alias]:
                 
                 
                 
                 
                self.unref_alias(new_alias)
        joinpromoter.add_votes(rhs_votes)
        joinpromoter.update_join_types(self)

         
         
        self.subq_aliases |= rhs.subq_aliases

         
         
        w = rhs.where.clone()
        w.relabel_aliases(change_map)
        self.where.add(w, connector)

         
        if rhs.select:
            self.set_select([col.relabeled_clone(change_map) for col in rhs.select])
        else:
            self.select = ()

        if connector == OR:
             
             
             
            if self.extra and rhs.extra:
                raise ValueError(
                    "When merging querysets using 'or', you cannot have "
                    "extra(select=...) on both sides."
                )
        self.extra.update(rhs.extra)
        extra_select_mask = set()
        if self.extra_select_mask is not None:
            extra_select_mask.update(self.extra_select_mask)
        if rhs.extra_select_mask is not None:
            extra_select_mask.update(rhs.extra_select_mask)
        if extra_select_mask:
            self.set_extra_mask(extra_select_mask)
        self.extra_tables += rhs.extra_tables

         
         
        self.order_by = rhs.order_by or self.order_by
        self.extra_order_by = rhs.extra_order_by or self.extra_order_by

    def _get_defer_select_mask(self, opts, mask, select_mask=None):
        if select_mask is None:
            select_mask = {}
        select_mask[opts.pk] = {}
         
         
         
         
        for field in opts.concrete_fields + opts.related_objects:
            field_mask = mask.pop(field.name, None)
            field_att_mask = None
            if field_attname := getattr(field, "attname", None):
                field_att_mask = mask.pop(field_attname, None)
            if field_mask is None and field_att_mask is None:
                select_mask.setdefault(field, {})
            elif field_mask:
                if not field.is_relation:
                    raise FieldError(next(iter(field_mask)))
                 
                 
                 
                 
                 
                if field.many_to_many:
                    continue
                field_select_mask = select_mask.setdefault(field, {})
                related_model = field.related_model._meta.concrete_model
                self._get_defer_select_mask(
                    related_model._meta, field_mask, field_select_mask
                )
         
         
        for field_name, field_mask in mask.items():
            if filtered_relation := self._filtered_relations.get(field_name):
                relation = opts.get_field(filtered_relation.relation_name)
                field_select_mask = select_mask.setdefault((field_name, relation), {})
                related_model = relation.related_model._meta.concrete_model
                self._get_defer_select_mask(
                    related_model._meta, field_mask, field_select_mask
                )
            else:
                opts.get_field(field_name)
        return select_mask

    def _get_only_select_mask(self, opts, mask, select_mask=None):
        if select_mask is None:
            select_mask = {}
        select_mask[opts.pk] = {}
         
        for field_name, field_mask in mask.items():
            field = opts.get_field(field_name)
            field_select_mask = select_mask.setdefault(field, {})
            if field_mask:
                if not field.is_relation:
                    raise FieldError(next(iter(field_mask)))
                related_model = field.remote_field.model._meta.concrete_model
                self._get_only_select_mask(
                    related_model._meta, field_mask, field_select_mask
                )
        return select_mask

    def get_select_mask(self):
        
        field_names, defer = self.deferred_loading
        if not field_names:
            return {}
        mask = {}
        for field_name in field_names:
            part_mask = mask
            for part in field_name.split(LOOKUP_SEP):
                part_mask = part_mask.setdefault(part, {})
        opts = self.get_meta()
        if defer:
            return self._get_defer_select_mask(opts, mask)
        return self._get_only_select_mask(opts, mask)

    def table_alias(self, table_name, create=False, filtered_relation=None):
        
        alias_list = self.table_map.get(table_name)
        if not create and alias_list:
            alias = alias_list[0]
            self.alias_refcount[alias] += 1
            return alias, False

         
        if alias_list:
            alias = "%s%d" % (self.alias_prefix, len(self.alias_map) + 1)
            alias_list.append(alias)
        else:
             
            alias = (
                filtered_relation.alias if filtered_relation is not None else table_name
            )
            self.table_map[table_name] = [alias]
        self.alias_refcount[alias] = 1
        return alias, True

    def ref_alias(self, alias):
        
        self.alias_refcount[alias] += 1

    def unref_alias(self, alias, amount=1):
        
        self.alias_refcount[alias] -= amount

    def promote_joins(self, aliases):
        
        aliases = list(aliases)
        while aliases:
            alias = aliases.pop(0)
            if self.alias_map[alias].join_type is None:
                 
                 
                 
                continue
             
            assert self.alias_map[alias].join_type is not None
            parent_alias = self.alias_map[alias].parent_alias
            parent_louter = (
                parent_alias and self.alias_map[parent_alias].join_type == LOUTER
            )
            already_louter = self.alias_map[alias].join_type == LOUTER
            if (self.alias_map[alias].nullable or parent_louter) and not already_louter:
                self.alias_map[alias] = self.alias_map[alias].promote()
                 
                 
                aliases.extend(
                    join
                    for join in self.alias_map
                    if self.alias_map[join].parent_alias == alias
                    and join not in aliases
                )

    def demote_joins(self, aliases):
        
        aliases = list(aliases)
        while aliases:
            alias = aliases.pop(0)
            if self.alias_map[alias].join_type == LOUTER:
                self.alias_map[alias] = self.alias_map[alias].demote()
                parent_alias = self.alias_map[alias].parent_alias
                if self.alias_map[parent_alias].join_type == INNER:
                    aliases.append(parent_alias)

    def reset_refcounts(self, to_counts):
        
        for alias, cur_refcount in self.alias_refcount.copy().items():
            unref_amount = cur_refcount - to_counts.get(alias, 0)
            self.unref_alias(alias, unref_amount)

    def change_aliases(self, change_map):
        
        if not change_map:
            return self
         
         
         
        assert set(change_map).isdisjoint(change_map.values())

         
         
        self.where.relabel_aliases(change_map)
        if isinstance(self.group_by, tuple):
            self.group_by = tuple(
                [col.relabeled_clone(change_map) for col in self.group_by]
            )
        self.select = tuple([col.relabeled_clone(change_map) for col in self.select])
        self.annotations = self.annotations and {
            key: col.relabeled_clone(change_map)
            for key, col in self.annotations.items()
        }

         
        for old_alias, new_alias in change_map.items():
            if old_alias not in self.alias_map:
                continue
            alias_data = self.alias_map[old_alias].relabeled_clone(change_map)
            self.alias_map[new_alias] = alias_data
            self.alias_refcount[new_alias] = self.alias_refcount[old_alias]
            del self.alias_refcount[old_alias]
            del self.alias_map[old_alias]

            table_aliases = self.table_map[alias_data.table_name]
            for pos, alias in enumerate(table_aliases):
                if alias == old_alias:
                    table_aliases[pos] = new_alias
                    break

         
         
        self.external_aliases = {
             
            change_map.get(alias, alias): (aliased or alias in change_map)
            for alias, aliased in self.external_aliases.items()
        }
        for combined_query in self.combined_queries:
            external_change_map = {
                alias: aliased
                for alias, aliased in change_map.items()
                if alias in combined_query.external_aliases
            }
            combined_query.change_aliases(external_change_map)

    def bump_prefix(self, other_query, exclude=None):
        

        def prefix_gen():
            
            alphabet = ascii_uppercase
            prefix = chr(ord(self.alias_prefix) + 1)
            yield prefix
            for n in count(1):
                seq = alphabet[alphabet.index(prefix) :] if prefix else alphabet
                for s in product(seq, repeat=n):
                    yield "".join(s)
                prefix = None

        if self.alias_prefix != other_query.alias_prefix:
             
            return

         
         
         
         
        local_recursion_limit = sys.getrecursionlimit() // 16
        for pos, prefix in enumerate(prefix_gen()):
            if prefix not in self.subq_aliases:
                self.alias_prefix = prefix
                break
            if pos > local_recursion_limit:
                raise RecursionError(
                    "Maximum recursion depth exceeded: too many subqueries."
                )
        self.subq_aliases = self.subq_aliases.union([self.alias_prefix])
        other_query.subq_aliases = other_query.subq_aliases.union(self.subq_aliases)
        if exclude is None:
            exclude = {}
        self.change_aliases(
            {
                alias: "%s%d" % (self.alias_prefix, pos)
                for pos, alias in enumerate(self.alias_map)
                if alias not in exclude
            }
        )

    def get_initial_alias(self):
        
        if self.alias_map:
            alias = self.base_table
            self.ref_alias(alias)
        elif self.model:
            alias = self.join(self.base_table_class(self.get_meta().db_table, None))
        else:
            alias = None
        return alias

    def count_active_tables(self):
        
        return len([1 for count in self.alias_refcount.values() if count])

    def join(self, join, reuse=None):
        
        reuse_aliases = [
            a
            for a, j in self.alias_map.items()
            if (reuse is None or a in reuse) and j == join
        ]
        if reuse_aliases:
            if join.table_alias in reuse_aliases:
                reuse_alias = join.table_alias
            else:
                 
                 
                reuse_alias = reuse_aliases[-1]
            self.ref_alias(reuse_alias)
            return reuse_alias

         
        alias, _ = self.table_alias(
            join.table_name, create=True, filtered_relation=join.filtered_relation
        )
        if join.join_type:
            if self.alias_map[join.parent_alias].join_type == LOUTER or join.nullable:
                join_type = LOUTER
            else:
                join_type = INNER
            join.join_type = join_type
        join.table_alias = alias
        self.alias_map[alias] = join
        if filtered_relation := join.filtered_relation:
            resolve_reuse = reuse
            if resolve_reuse is not None:
                resolve_reuse = set(reuse) | {alias}
            joins_len = len(self.alias_map)
            join.filtered_relation = filtered_relation.resolve_expression(
                self, reuse=resolve_reuse
            )
             
             
            if joins_len < len(self.alias_map):
                self.alias_map[alias] = self.alias_map.pop(alias)
        return alias

    def join_parent_model(self, opts, model, alias, seen):
        
        if model in seen:
            return seen[model]
        chain = opts.get_base_chain(model)
        if not chain:
            return alias
        curr_opts = opts
        for int_model in chain:
            if int_model in seen:
                curr_opts = int_model._meta
                alias = seen[int_model]
                continue
             
             
             
             
            if not curr_opts.parents[int_model]:
                curr_opts = int_model._meta
                continue
            link_field = curr_opts.get_ancestor_link(int_model)
            join_info = self.setup_joins([link_field.name], curr_opts, alias)
            curr_opts = int_model._meta
            alias = seen[int_model] = join_info.joins[-1]
        return alias or seen[None]

    def check_alias(self, alias):
         
        if "%" in alias:
            warnings.warn(
                "Using percent signs in a column alias is deprecated.",
                category=RemovedInDjango70Warning,
                skip_file_prefixes=django_file_prefixes(),
            )
        if FORBIDDEN_ALIAS_PATTERN.search(alias):
            raise ValueError(
                "Column aliases cannot contain whitespace characters, hashes, "
                 
                 
                 
                 
                "control characters, quotation marks, semicolons, or SQL comments."
            )

    def add_annotation(self, annotation, alias, select=True):
        
        self.check_alias(alias)
        annotation = annotation.resolve_expression(self, allow_joins=True, reuse=None)
        if select:
            self.append_annotation_mask([alias])
        else:
            self.set_annotation_mask(set(self.annotation_select).difference({alias}))
        self.annotations[alias] = annotation
        if select and self.selected:
            self.selected[alias] = alias

    @property
    def _subquery_fields_len(self):
        if not self.has_select_fields or not self.select:
            return len(self.model._meta.pk_fields)
        return len(self.select) + sum(
            len(expr.targets) - 1 for expr in self.select if isinstance(expr, ColPairs)
        )

    def resolve_expression(self, query, *args, **kwargs):
        clone = self.clone()
         
         
        clone.bump_prefix(query)
        clone.subquery = True
        clone.where.resolve_expression(query, *args, **kwargs)
         
        if clone.combinator:
            clone.combined_queries = tuple(
                [
                    combined_query.resolve_expression(query, *args, **kwargs)
                    for combined_query in clone.combined_queries
                ]
            )
        for key, value in clone.annotations.items():
            resolved = value.resolve_expression(query, *args, **kwargs)
            if hasattr(resolved, "external_aliases"):
                resolved.external_aliases.update(clone.external_aliases)
            clone.annotations[key] = resolved
         
        for alias, table in query.alias_map.items():
            clone.external_aliases[alias] = (
                isinstance(table, Join)
                and table.join_field.related_model._meta.db_table != alias
            ) or (
                isinstance(table, BaseTable) and table.table_name != table.table_alias
            )
        return clone

    def get_external_cols(self):
        exprs = chain(self.annotations.values(), self.where.children)
        return [
            col
            for col in self._gen_cols(exprs, include_external=True)
            if col.alias in self.external_aliases
        ]

    def get_group_by_cols(self, wrapper=None):
         
         
         
         
        external_cols = self.get_external_cols()
        if any(col.possibly_multivalued for col in external_cols):
            return [wrapper or self]
        return external_cols

    def as_sql(self, compiler, connection):
         
         
        if (
            self.subquery
            and not connection.features.ignores_unnecessary_order_by_in_subqueries
        ):
            self.clear_ordering(force=False)
            for query in self.combined_queries:
                query.clear_ordering(force=False)
        sql, params = self.get_compiler(connection=connection).as_sql()
        if self.subquery:
            sql = "(%s)" % sql
        return sql, params

    def resolve_lookup_value(self, value, can_reuse, allow_joins, summarize=False):
        if hasattr(value, "resolve_expression"):
            value = value.resolve_expression(
                self,
                reuse=can_reuse,
                allow_joins=allow_joins,
                summarize=summarize,
            )
        elif isinstance(value, (list, tuple)):
             
             
            values = (
                self.resolve_lookup_value(sub_value, can_reuse, allow_joins, summarize)
                for sub_value in value
            )
            type_ = type(value)
            if hasattr(type_, "_make"):   
                return type_(*values)
            return type_(values)
        return value

    def solve_lookup_type(self, lookup, summarize=False):
        
        lookup_splitted = lookup.split(LOOKUP_SEP)
        if self.annotations:
            annotation, expression_lookups = refs_expression(
                lookup_splitted, self.annotations
            )
            if annotation:
                expression = self.annotations[annotation]
                if summarize:
                    expression = Ref(annotation, expression)
                return expression_lookups, (), expression
        _, field, _, lookup_parts = self.names_to_path(lookup_splitted, self.get_meta())
        field_parts = lookup_splitted[0 : len(lookup_splitted) - len(lookup_parts)]
        if len(lookup_parts) > 1 and not field_parts:
            raise FieldError(
                'Invalid lookup "%s" for model %s".'
                % (lookup, self.get_meta().model.__name__)
            )
        return lookup_parts, field_parts, False

    def check_query_object_type(self, value, opts, field):
        
        if hasattr(value, "_meta"):
            if not check_rel_lookup_compatibility(value._meta.model, opts, field):
                raise ValueError(
                    'Cannot query "%s": Must be "%s" instance.'
                    % (value, opts.object_name)
                )

    def check_related_objects(self, field, value, opts):
        
        if field.is_relation:
             
             
             
             
             
            if (
                isinstance(value, Query)
                and not value.has_select_fields
                and not check_rel_lookup_compatibility(value.model, opts, field)
            ):
                raise ValueError(
                    'Cannot use QuerySet for "%s": Use a QuerySet for "%s".'
                    % (value.model._meta.object_name, opts.object_name)
                )
            elif hasattr(value, "_meta"):
                self.check_query_object_type(value, opts, field)
            elif hasattr(value, "__iter__"):
                for v in value:
                    self.check_query_object_type(v, opts, field)

    def check_filterable(self, expression):
        
        if hasattr(expression, "resolve_expression") and not getattr(
            expression, "filterable", True
        ):
            raise NotSupportedError(
                expression.__class__.__name__ + " is disallowed in the filter "
                "clause."
            )
        if hasattr(expression, "get_source_expressions"):
            for expr in expression.get_source_expressions():
                self.check_filterable(expr)

    def build_lookup(self, lookups, lhs, rhs):
        
         
        *transforms, lookup_name = lookups or ["exact"]
        for name in transforms:
            lhs = self.try_transform(lhs, name, lookups)
         
         
        lookup_class = lhs.get_lookup(lookup_name)
        if not lookup_class:
             
             
            lhs = self.try_transform(lhs, lookup_name)
            lookup_name = "exact"
            lookup_class = lhs.get_lookup(lookup_name)
            if not lookup_class:
                return

        lookup = lookup_class(lhs, rhs)
         
         
        if lookup.rhs is None and not lookup.can_use_none_as_rhs:
            if lookup_name not in ("exact", "iexact"):
                raise ValueError("Cannot use None as a query value")
            return lhs.get_lookup("isnull")(lhs, True)

         
         
         
         
        if (
            lookup_name in ("exact", "iexact")
            and lookup.rhs == ""
            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
        ):
            return lhs.get_lookup("isnull")(lhs, True)

        return lookup

    def try_transform(self, lhs, name, lookups=None):
        
        transform_class = lhs.get_transform(name)
        if transform_class:
            return transform_class(lhs)
        else:
            output_field = lhs.output_field.__class__
            suggested_lookups = difflib.get_close_matches(
                name, lhs.output_field.get_lookups()
            )
            if suggested_lookups:
                suggestion = ", perhaps you meant %s?" % " or ".join(suggested_lookups)
            else:
                suggestion = "."
            if lookups is not None:
                name_index = lookups.index(name)
                unsupported_lookup = LOOKUP_SEP.join(lookups[name_index:])
            else:
                unsupported_lookup = name
            raise FieldError(
                "Unsupported lookup '%s' for %s or join on the field not "
                "permitted%s" % (unsupported_lookup, output_field.__name__, suggestion)
            )

    def build_filter(
        self,
        filter_expr,
        branch_negated=False,
        current_negated=False,
        can_reuse=None,
        allow_joins=True,
        split_subq=True,
        check_filterable=True,
        summarize=False,
        update_join_types=True,
    ):
        
        if isinstance(filter_expr, dict):
            raise FieldError("Cannot parse keyword query as dict")
        if isinstance(filter_expr, Q):
            return self._add_q(
                filter_expr,
                branch_negated=branch_negated,
                current_negated=current_negated,
                used_aliases=can_reuse,
                allow_joins=allow_joins,
                split_subq=split_subq,
                check_filterable=check_filterable,
                summarize=summarize,
                update_join_types=update_join_types,
            )
        if hasattr(filter_expr, "resolve_expression"):
            if not getattr(filter_expr, "conditional", False):
                raise TypeError("Cannot filter against a non-conditional expression.")
            condition = filter_expr.resolve_expression(
                self, allow_joins=allow_joins, reuse=can_reuse, summarize=summarize
            )
            if not isinstance(condition, Lookup):
                condition = self.build_lookup(["exact"], condition, True)
            return WhereNode([condition], connector=AND), []
        arg, value = filter_expr
        if not arg:
            raise FieldError("Cannot parse keyword query %r" % arg)
        lookups, parts, reffed_expression = self.solve_lookup_type(arg, summarize)

        if check_filterable:
            self.check_filterable(reffed_expression)

        if not allow_joins and len(parts) > 1:
            raise FieldError("Joined field references are not permitted in this query")

        pre_joins = self.alias_refcount.copy()
        value = self.resolve_lookup_value(value, can_reuse, allow_joins, summarize)
        used_joins = {
            k for k, v in self.alias_refcount.items() if v > pre_joins.get(k, 0)
        }

        if check_filterable:
            self.check_filterable(value)

        if reffed_expression:
            condition = self.build_lookup(lookups, reffed_expression, value)
            return WhereNode([condition], connector=AND), []

        opts = self.get_meta()
        alias = self.get_initial_alias()
        allow_many = not branch_negated or not split_subq

        try:
            join_info = self.setup_joins(
                parts,
                opts,
                alias,
                can_reuse=can_reuse,
                allow_many=allow_many,
            )

             
            if isinstance(value, Iterator):
                value = list(value)
            self.check_related_objects(join_info.final_field, value, join_info.opts)

             
             
            self._lookup_joins = join_info.joins
        except MultiJoin as e:
            return self.split_exclude(filter_expr, can_reuse, e.names_with_path)

         
         
        used_joins.update(join_info.joins)
        targets, alias, join_list = self.trim_joins(
            join_info.targets, join_info.joins, join_info.path
        )
        if can_reuse is not None:
            can_reuse.update(join_list)

        if join_info.final_field.is_relation:
            if len(targets) == 1:
                col = self._get_col(targets[0], join_info.final_field, alias)
            else:
                col = ColPairs(alias, targets, join_info.targets, join_info.final_field)
        else:
            col = self._get_col(targets[0], join_info.final_field, alias)

        condition = self.build_lookup(lookups, col, value)
        lookup_type = condition.lookup_name
        clause = WhereNode([condition], connector=AND)

        require_outer = (
            lookup_type == "isnull" and condition.rhs is True and not current_negated
        )
        if (
            current_negated
            and (lookup_type != "isnull" or condition.rhs is False)
            and condition.rhs is not None
        ):
            require_outer = True
            if lookup_type != "isnull":
                 
                 
                 
                 
                 
                 
                 
                 
                 
                if (
                    self.is_nullable(targets[0])
                    or self.alias_map[join_list[-1]].join_type == LOUTER
                ):
                    lookup_class = targets[0].get_lookup("isnull")
                    col = self._get_col(targets[0], join_info.targets[0], alias)
                     
                    if (
                        lookup_type == "in"
                         
                        and isinstance(condition.rhs, Iterable)
                        and not isinstance(condition.rhs, (str, bytes))
                        and any(v is None for v in condition.rhs)
                    ):
                        clause.add(lookup_class(col, True), OR)
                    else:
                        clause.add(lookup_class(col, False), AND)
                 
                 
                if isinstance(value, Col) and self.is_nullable(value.target):
                    lookup_class = value.target.get_lookup("isnull")
                    clause.add(lookup_class(value, False), AND)
        return clause, used_joins if not require_outer else ()

    def add_filter(self, filter_lhs, filter_rhs):
        self.add_q(Q((filter_lhs, filter_rhs)))

    def add_q(self, q_object, reuse_all=False):
        
         
         
         
         
         
         
        existing_inner = {
            a for a in self.alias_map if self.alias_map[a].join_type == INNER
        }
        if reuse_all:
            can_reuse = set(self.alias_map)
        else:
            can_reuse = self.used_aliases
        clause, _ = self._add_q(q_object, can_reuse)
        if clause:
            self.where.add(clause, AND)
        self.demote_joins(existing_inner)

    def build_where(self, filter_expr):
        return self.build_filter(filter_expr, allow_joins=False)[0]

    def clear_where(self):
        self.where = WhereNode()

    def _add_q(
        self,
        q_object,
        used_aliases,
        branch_negated=False,
        current_negated=False,
        allow_joins=True,
        split_subq=True,
        check_filterable=True,
        summarize=False,
        update_join_types=True,
    ):
        
        connector = q_object.connector
        current_negated ^= q_object.negated
        branch_negated = branch_negated or q_object.negated
        target_clause = WhereNode(connector=connector, negated=q_object.negated)
        joinpromoter = JoinPromoter(
            q_object.connector, len(q_object.children), current_negated
        )
        for child in q_object.children:
            child_clause, needed_inner = self.build_filter(
                child,
                can_reuse=used_aliases,
                branch_negated=branch_negated,
                current_negated=current_negated,
                allow_joins=allow_joins,
                split_subq=split_subq,
                check_filterable=check_filterable,
                summarize=summarize,
                update_join_types=update_join_types,
            )
            joinpromoter.add_votes(needed_inner)
            if child_clause:
                target_clause.add(child_clause, connector)
        if update_join_types:
            needed_inner = joinpromoter.update_join_types(self)
        else:
            needed_inner = []
        return target_clause, needed_inner

    def add_filtered_relation(self, filtered_relation, alias):
        if "." in alias:
            raise ValueError(
                "FilteredRelation doesn't support aliases with periods "
                "(got %r)." % alias
            )
        self.check_alias(alias)
        filtered_relation.alias = alias
        relation_lookup_parts, relation_field_parts, _ = self.solve_lookup_type(
            filtered_relation.relation_name
        )
        if relation_lookup_parts:
            raise ValueError(
                "FilteredRelation's relation_name cannot contain lookups "
                "(got %r)." % filtered_relation.relation_name
            )
        for lookup in get_children_from_q(filtered_relation.condition):
            lookup_parts, lookup_field_parts, _ = self.solve_lookup_type(lookup)
            shift = 2 if not lookup_parts else 1
            lookup_field_path = lookup_field_parts[:-shift]
            for idx, lookup_field_part in enumerate(lookup_field_path):
                if len(relation_field_parts) > idx:
                    if relation_field_parts[idx] != lookup_field_part:
                        raise ValueError(
                            "FilteredRelation's condition doesn't support "
                            "relations outside the %r (got %r)."
                            % (filtered_relation.relation_name, lookup)
                        )
            if len(lookup_field_parts) > len(relation_field_parts) + 1:
                raise ValueError(
                    "FilteredRelation's condition doesn't support nested "
                    "relations deeper than the relation_name (got %r for "
                    "%r)." % (lookup, filtered_relation.relation_name)
                )
        filtered_relation = filtered_relation.clone()
        filtered_relation.condition = rename_prefix_from_q(
            filtered_relation.relation_name,
            alias,
            filtered_relation.condition,
        )
        self._filtered_relations[filtered_relation.alias] = filtered_relation

    def names_to_path(self, names, opts, allow_many=True, fail_on_missing=False):
        
        path, names_with_path = [], []
        for pos, name in enumerate(names):
            cur_names_with_path = (name, [])
            if name == "pk" and opts is not None:
                name = opts.pk.name

            field = None
            filtered_relation = None
            try:
                if opts is None:
                    raise FieldDoesNotExist
                field = opts.get_field(name)
            except FieldDoesNotExist:
                if name in self.annotations:
                    field = self.annotations[name].output_field
                elif name in self._filtered_relations and pos == 0:
                    filtered_relation = self._filtered_relations[name]
                    if LOOKUP_SEP in filtered_relation.relation_name:
                        parts = filtered_relation.relation_name.split(LOOKUP_SEP)
                        filtered_relation_path, field, _, _ = self.names_to_path(
                            parts,
                            opts,
                            allow_many,
                            fail_on_missing,
                        )
                        path.extend(filtered_relation_path[:-1])
                    else:
                        field = opts.get_field(filtered_relation.relation_name)
            if field is not None:
                 
                 
                 
                if field.is_relation and not field.related_model:
                    raise FieldError(
                        "Field %r does not generate an automatic reverse "
                        "relation and therefore cannot be used for reverse "
                        "querying. If it is a GenericForeignKey, consider "
                        "adding a GenericRelation." % name
                    )
                try:
                    model = field.model._meta.concrete_model
                except AttributeError:
                     
                     
                    model = None
            else:
                 
                 
                pos -= 1
                if pos == -1 or fail_on_missing:
                    available = sorted(
                        [
                            *get_field_names_from_opts(opts),
                            *self.annotations,
                            *self._filtered_relations,
                        ]
                    )
                    raise FieldError(
                        "Cannot resolve keyword '%s' into field. "
                        "Choices are: %s" % (name, ", ".join(available))
                    )
                break
             
             
             
            if opts is not None and model is not opts.model:
                path_to_parent = opts.get_path_to_parent(model)
                if path_to_parent:
                    path.extend(path_to_parent)
                    cur_names_with_path[1].extend(path_to_parent)
                    opts = path_to_parent[-1].to_opts
            if hasattr(field, "path_infos"):
                if filtered_relation:
                    pathinfos = field.get_path_info(filtered_relation)
                else:
                    pathinfos = field.path_infos
                if not allow_many:
                    for inner_pos, p in enumerate(pathinfos):
                        if p.m2m:
                            cur_names_with_path[1].extend(pathinfos[0 : inner_pos + 1])
                            names_with_path.append(cur_names_with_path)
                            raise MultiJoin(pos + 1, names_with_path)
                last = pathinfos[-1]
                path.extend(pathinfos)
                final_field = last.join_field
                opts = last.to_opts
                targets = last.target_fields
                cur_names_with_path[1].extend(pathinfos)
                names_with_path.append(cur_names_with_path)
            else:
                 
                final_field = field
                targets = (field,)
                if fail_on_missing and pos + 1 != len(names):
                    raise FieldError(
                        "Cannot resolve keyword %r into field. Join on '%s'"
                        " not permitted." % (names[pos + 1], name)
                    )
                break
        return path, final_field, targets, names[pos + 1 :]

    def setup_joins(
        self,
        names,
        opts,
        alias,
        can_reuse=None,
        allow_many=True,
    ):
        
        joins = [alias]
         
         
         
         

        def final_transformer(field, alias):
            if not self.alias_cols:
                alias = None
            return field.get_col(alias)

         
         
        last_field_exception = None
        for pivot in range(len(names), 0, -1):
            try:
                path, final_field, targets, rest = self.names_to_path(
                    names[:pivot],
                    opts,
                    allow_many,
                    fail_on_missing=True,
                )
            except FieldError as exc:
                if pivot == 1:
                     
                     
                    raise
                else:
                    last_field_exception = exc
            else:
                 
                 
                transforms = names[pivot:]
                break
        for name in transforms:

            def transform(field, alias, *, name, previous):
                try:
                    wrapped = previous(field, alias)
                    return self.try_transform(wrapped, name)
                except FieldError:
                     
                    if isinstance(final_field, Field) and last_field_exception:
                        raise last_field_exception
                    else:
                        raise

            final_transformer = functools.partial(
                transform, name=name, previous=final_transformer
            )
            final_transformer.has_transforms = True
         
         
         
        for join in path:
            if join.filtered_relation:
                filtered_relation = join.filtered_relation.clone()
                table_alias = filtered_relation.alias
            else:
                filtered_relation = None
                table_alias = None
            opts = join.to_opts
            if join.direct:
                nullable = self.is_nullable(join.join_field)
            else:
                nullable = True
            connection = self.join_class(
                opts.db_table,
                alias,
                table_alias,
                INNER,
                join.join_field,
                nullable,
                filtered_relation=filtered_relation,
            )
            reuse = can_reuse if join.m2m else None
            alias = self.join(connection, reuse=reuse)
            joins.append(alias)
            if join.filtered_relation and can_reuse is not None:
                can_reuse.add(alias)
        return JoinInfo(final_field, targets, opts, joins, path, final_transformer)

    def trim_joins(self, targets, joins, path):
        
        joins = joins[:]
        for pos, info in enumerate(reversed(path)):
            if len(joins) == 1 or not info.direct:
                break
            if info.filtered_relation:
                break
            join_targets = {t.column for t in info.join_field.foreign_related_fields}
            cur_targets = {t.column for t in targets}
            if not cur_targets.issubset(join_targets):
                break
            targets_dict = {
                r[1].column: r[0]
                for r in info.join_field.related_fields
                if r[1].column in cur_targets
            }
            targets = tuple(targets_dict[t.column] for t in targets)
            self.unref_alias(joins.pop())
        return targets, joins[-1], joins

    @classmethod
    def _gen_cols(cls, exprs, include_external=False, resolve_refs=True):
        for expr in exprs:
            if isinstance(expr, Col):
                yield expr
            elif include_external and callable(
                getattr(expr, "get_external_cols", None)
            ):
                yield from expr.get_external_cols()
            elif hasattr(expr, "get_source_expressions"):
                if not resolve_refs and isinstance(expr, Ref):
                    continue
                yield from cls._gen_cols(
                    expr.get_source_expressions(),
                    include_external=include_external,
                    resolve_refs=resolve_refs,
                )

    @classmethod
    def _gen_col_aliases(cls, exprs):
        yield from (expr.alias for expr in cls._gen_cols(exprs))

    def resolve_ref(self, name, allow_joins=True, reuse=None, summarize=False):
        annotation = self.annotations.get(name)
        if annotation is not None:
            if not allow_joins:
                for alias in self._gen_col_aliases([annotation]):
                    if isinstance(self.alias_map[alias], Join):
                        raise FieldError(
                            "Joined field references are not permitted in this query"
                        )
            if summarize:
                 
                 
                 
                 
                 
                if name not in self.annotation_select:
                    raise FieldError(
                        "Cannot aggregate over the '%s' alias. Use annotate() "
                        "to promote it." % name
                    )
                return Ref(name, self.annotation_select[name])
            else:
                return annotation
        else:
            field_list = name.split(LOOKUP_SEP)
            annotation = self.annotations.get(field_list[0])
            if annotation is not None:
                for transform in field_list[1:]:
                    annotation = self.try_transform(annotation, transform)
                return annotation
            join_info = self.setup_joins(
                field_list, self.get_meta(), self.get_initial_alias(), can_reuse=reuse
            )
            targets, final_alias, join_list = self.trim_joins(
                join_info.targets, join_info.joins, join_info.path
            )
            if not allow_joins and len(join_list) > 1:
                raise FieldError(
                    "Joined field references are not permitted in this query"
                )
            if len(targets) > 1:
                raise FieldError(
                    "Referencing multicolumn fields with F() objects isn't supported"
                )
             
             
            transform = join_info.transform_function(targets[0], final_alias)
            if reuse is not None:
                reuse.update(join_list)
            return transform

    def split_exclude(self, filter_expr, can_reuse, names_with_path):
        
         
        query = self.__class__(self.model)
        query._filtered_relations = self._filtered_relations
        filter_lhs, filter_rhs = filter_expr
        if isinstance(filter_rhs, OuterRef):
            filter_rhs = OuterRef(filter_rhs)
        elif isinstance(filter_rhs, F):
            filter_rhs = OuterRef(filter_rhs.name)
        query.add_filter(filter_lhs, filter_rhs)
        query.clear_ordering(force=True)
         
         
        trimmed_prefix, contains_louter = query.trim_start(names_with_path)

        col = query.select[0]
        select_field = col.target
        alias = col.alias
        if alias in can_reuse:
            pk = select_field.model._meta.pk
             
             
            query.bump_prefix(self)
            lookup_class = select_field.get_lookup("exact")
             
             
            lookup = lookup_class(pk.get_col(query.select[0].alias), pk.get_col(alias))
            query.where.add(lookup, AND)
            query.external_aliases[alias] = True
        else:
            lookup_class = select_field.get_lookup("exact")
            lookup = lookup_class(col, ResolvedOuterRef(trimmed_prefix))
            query.where.add(lookup, AND)

        condition, needed_inner = self.build_filter(Exists(query))

        if contains_louter:
            or_null_condition, _ = self.build_filter(
                ("%s__isnull" % trimmed_prefix, True),
                current_negated=True,
                branch_negated=True,
                can_reuse=can_reuse,
            )
            condition.add(or_null_condition, OR)
             
             
             
             
             
        return condition, needed_inner

    def set_empty(self):
        self.where.add(NothingNode(), AND)
        for query in self.combined_queries:
            query.set_empty()

    def is_empty(self):
        return any(isinstance(c, NothingNode) for c in self.where.children)

    def set_limits(self, low=None, high=None):
        
        if high is not None:
            if self.high_mark is not None:
                self.high_mark = min(self.high_mark, self.low_mark + high)
            else:
                self.high_mark = self.low_mark + high
        if low is not None:
            if self.high_mark is not None:
                self.low_mark = min(self.high_mark, self.low_mark + low)
            else:
                self.low_mark = self.low_mark + low

        if self.low_mark == self.high_mark:
            self.set_empty()

    def clear_limits(self):
        
        self.low_mark, self.high_mark = 0, None

    @property
    def is_sliced(self):
        return self.low_mark != 0 or self.high_mark is not None

    def has_limit_one(self):
        return self.high_mark is not None and (self.high_mark - self.low_mark) == 1

    def can_filter(self):
        
        return not self.is_sliced

    def clear_select_clause(self):
        
        self.select = ()
        self.default_cols = False
        self.select_related = False
        self.set_extra_mask(())
        self.set_annotation_mask(())
        self.selected = None

    def clear_select_fields(self):
        
        self.select = ()
        self.values_select = ()
        self.selected = None

    def add_select_col(self, col, name):
        self.select += (col,)
        self.values_select += (name,)
        self.selected[name] = len(self.select) - 1

    def set_select(self, cols):
        self.default_cols = False
        self.select = tuple(cols)

    def add_distinct_fields(self, *field_names):
        
        self.distinct_fields = field_names
        self.distinct = True

    def add_fields(self, field_names, allow_m2m=True):
        
        alias = self.get_initial_alias()
        opts = self.get_meta()

        try:
            cols = []
            for name in field_names:
                 
                 
                join_info = self.setup_joins(
                    name.split(LOOKUP_SEP), opts, alias, allow_many=allow_m2m
                )
                targets, final_alias, joins = self.trim_joins(
                    join_info.targets,
                    join_info.joins,
                    join_info.path,
                )
                if len(targets) > 1:
                    transformed_targets = [
                        join_info.transform_function(target, final_alias)
                        for target in targets
                    ]
                    cols.append(
                        ColPairs(
                            final_alias if self.alias_cols else None,
                            [col.target for col in transformed_targets],
                            [col.output_field for col in transformed_targets],
                            join_info.final_field,
                        )
                    )
                else:
                    cols.append(join_info.transform_function(targets[0], final_alias))
            if cols:
                self.set_select(cols)
        except MultiJoin:
            raise FieldError("Invalid field name: '%s'" % name)
        except FieldError:
            if LOOKUP_SEP in name:
                 
                 
                raise
            else:
                names = sorted(
                    [
                        *get_field_names_from_opts(opts),
                        *self.extra,
                        *self.annotation_select,
                        *self._filtered_relations,
                    ]
                )
                raise FieldError(
                    "Cannot resolve keyword %r into field. "
                    "Choices are: %s" % (name, ", ".join(names))
                )

    def add_ordering(self, *ordering):
        
        errors = []
        for item in ordering:
            if isinstance(item, str):
                if item == "?":
                    continue
                item = item.removeprefix("-")
                if item in self.annotations:
                    continue
                if self.extra and item in self.extra:
                    continue
                 
                 
                self.names_to_path(item.split(LOOKUP_SEP), self.model._meta)
            elif not hasattr(item, "resolve_expression"):
                errors.append(item)
            if getattr(item, "contains_aggregate", False):
                raise FieldError(
                    "Using an aggregate in order_by() without also including "
                    "it in annotate() is not allowed: %s" % item
                )
        if errors:
            raise FieldError("Invalid order_by arguments: %s" % errors)
        if ordering:
            self.order_by += ordering
        else:
            self.default_ordering = False

    @property
    def orderby_issubset_groupby(self):
        if self.extra_order_by:
             
             
            return False
        if self.group_by in (None, True):
             
             
             
            return True
        if not self.order_by:
             
             
            return True
         
        q = self.clone()
        order_by_set = set()
        for order_by in q.order_by:
            if hasattr(order_by, "resolve_expression"):
                order_by_set.add(order_by.resolve_expression(q))
            elif order_by == "?":
                 
                return False
            else:
                order_by_set.add(F(order_by.removeprefix("-")).resolve_expression(q))
        return order_by_set.issubset(self.group_by)

    def clear_ordering(self, force=False, clear_default=True):
        
        if not force and (
            self.is_sliced or self.distinct_fields or self.select_for_update
        ):
            return
        self.order_by = ()
        self.extra_order_by = ()
        if clear_default:
            self.default_ordering = False
         
         
         
        for query in self.combined_queries:
            query.clear_ordering(force=False, clear_default=clear_default)

    def set_group_by(self, allow_aliases=True):
        
        if allow_aliases and self.values_select:
             
             
            group_by_annotations = {}
            values_select = {}
            for alias, expr in zip(self.values_select, self.select):
                if isinstance(expr, Col):
                    values_select[alias] = expr
                else:
                    group_by_annotations[alias] = expr
            self.annotations = {**group_by_annotations, **self.annotations}
            self.append_annotation_mask(group_by_annotations)
            self.select = tuple(values_select.values())
            self.values_select = tuple(values_select)
            if self.selected is not None:
                for index, value_select in enumerate(values_select):
                    self.selected[value_select] = index
        group_by = list(self.select)
        for alias, annotation in self.annotation_select.items():
            if not (group_by_cols := annotation.get_group_by_cols()):
                continue
            if allow_aliases and not annotation.contains_aggregate:
                group_by.append(Ref(alias, annotation))
            else:
                group_by.extend(group_by_cols)
        self.group_by = tuple(group_by)

    def add_select_related(self, fields):
        
        if isinstance(self.select_related, bool):
            field_dict = {}
        else:
            field_dict = self.select_related
        for field in fields:
            d = field_dict
            for part in field.split(LOOKUP_SEP):
                d = d.setdefault(part, {})
        self.select_related = field_dict

    def add_extra(self, select, select_params, where, params, tables, order_by):
        
        if select:
             
             
             
             
            select_pairs = {}
            if select_params:
                param_iter = iter(select_params)
            else:
                param_iter = iter([])
            for name, entry in select.items():
                self.check_alias(name)
                entry = str(entry)
                entry_params = []
                pos = entry.find("%s")
                while pos != -1:
                    if pos == 0 or entry[pos - 1] != "%":
                        entry_params.append(next(param_iter))
                    pos = entry.find("%s", pos + 2)
                select_pairs[name] = (entry, entry_params)
            self.extra.update(select_pairs)
        if where or params:
            self.where.add(ExtraWhere(where, params), AND)
        if tables:
            self.extra_tables += tuple(tables)
        if order_by:
            self.extra_order_by = order_by

    def clear_deferred_loading(self):
        
        self.deferred_loading = (frozenset(), True)

    def add_deferred_loading(self, field_names):
        
         
         
         
         
        existing, defer = self.deferred_loading
        if defer:
             
            self.deferred_loading = existing.union(field_names), True
        else:
             
            if new_existing := existing.difference(field_names):
                self.deferred_loading = new_existing, False
            else:
                self.clear_deferred_loading()
                if new_only := set(field_names).difference(existing):
                    self.deferred_loading = new_only, True

    def add_immediate_loading(self, field_names):
        
        existing, defer = self.deferred_loading
        field_names = set(field_names)
        if "pk" in field_names:
            field_names.remove("pk")
            field_names.add(self.get_meta().pk.name)

        if defer:
             
             
            self.deferred_loading = field_names.difference(existing), False
        else:
             
            self.deferred_loading = frozenset(field_names), False

    def set_annotation_mask(self, names):
        
        if names is None:
            self.annotation_select_mask = None
        else:
            self.annotation_select_mask = set(names)
            if self.selected:
                 
                self.selected = {
                    key: value
                    for key, value in self.selected.items()
                    if not isinstance(value, str)
                    or value in self.annotation_select_mask
                }
                 
                for name in names:
                    self.selected[name] = name
        self._annotation_select_cache = None

    def append_annotation_mask(self, names):
        if self.annotation_select_mask is not None:
            self.set_annotation_mask(self.annotation_select_mask.union(names))

    def set_extra_mask(self, names):
        
        if names is None:
            self.extra_select_mask = None
        else:
            self.extra_select_mask = set(names)
        self._extra_select_cache = None

    @property
    def has_select_fields(self):
        return self.selected is not None

    def set_values(self, fields):
        self.select_related = False
        self.clear_deferred_loading()
        self.clear_select_fields()

        selected = {}
        if fields:
            for field in fields:
                self.check_alias(field)
            field_names = []
            extra_names = []
            annotation_names = []
            if not self.extra and not self.annotations:
                 
                 
                field_names = list(fields)
                selected = dict(zip(fields, range(len(fields))))
            else:
                self.default_cols = False
                for f in fields:
                    if extra := self.extra_select.get(f):
                        extra_names.append(f)
                        selected[f] = RawSQL(*extra)
                    elif f in self.annotation_select:
                        annotation_names.append(f)
                        selected[f] = f
                    elif f in self.annotations:
                        if self.annotation_select:
                            raise FieldError(
                                f"Cannot select the '{f}' alias. It was excluded "
                                f"by a previous values() or values_list() call. "
                                f"Include '{f}' in that call to select it."
                            )
                        else:
                            raise FieldError(
                                f"Cannot select the '{f}' alias. Use annotate() "
                                f"to promote it."
                            )
                    else:
                         
                         
                         
                        if self.annotation_select:
                            self.names_to_path(f.split(LOOKUP_SEP), self.model._meta)
                        selected[f] = len(field_names)
                        field_names.append(f)
            self.set_extra_mask(extra_names)
            self.set_annotation_mask(annotation_names)
        else:
            field_names = [f.attname for f in self.model._meta.concrete_fields]
            selected = dict.fromkeys(field_names, None)
         
         
        if self.group_by is True:
            self.add_fields(
                (f.attname for f in self.model._meta.concrete_fields), False
            )
             
             
            self.set_group_by(allow_aliases=False)
            self.clear_select_fields()
        elif self.group_by:
             
             
            group_by = []
            for expr in self.group_by:
                if isinstance(expr, Ref) and expr.refs not in selected:
                    expr = self.annotations[expr.refs]
                group_by.append(expr)
            self.group_by = tuple(group_by)

        self.values_select = tuple(field_names)
        self.add_fields(field_names, True)
        self.selected = selected if fields else None

    @property
    def annotation_select(self):
        
        if self._annotation_select_cache is not None:
            return self._annotation_select_cache
        elif not self.annotations:
            return {}
        elif self.annotation_select_mask is not None:
            self._annotation_select_cache = {
                k: v
                for k, v in self.annotations.items()
                if k in self.annotation_select_mask
            }
            return self._annotation_select_cache
        else:
            return self.annotations

    @property
    def extra_select(self):
        if self._extra_select_cache is not None:
            return self._extra_select_cache
        if not self.extra:
            return {}
        elif self.extra_select_mask is not None:
            self._extra_select_cache = {
                k: v for k, v in self.extra.items() if k in self.extra_select_mask
            }
            return self._extra_select_cache
        else:
            return self.extra

    def trim_start(self, names_with_path):
        
        all_paths = []
        for _, paths in names_with_path:
            all_paths.extend(paths)
        contains_louter = False
         
         
         
        lookup_tables = [
            t for t in self.alias_map if t in self._lookup_joins or t == self.base_table
        ]
        for trimmed_paths, path in enumerate(all_paths):
            if path.m2m:
                break
            if self.alias_map[lookup_tables[trimmed_paths + 1]].join_type == LOUTER:
                contains_louter = True
            alias = lookup_tables[trimmed_paths]
            self.unref_alias(alias)
         
        join_field = path.join_field.field
         
        paths_in_prefix = trimmed_paths
        trimmed_prefix = []
        for name, path in names_with_path:
            if paths_in_prefix - len(path) < 0:
                break
            trimmed_prefix.append(name)
            paths_in_prefix -= len(path)
        trimmed_prefix.append(join_field.foreign_related_fields[0].name)
        trimmed_prefix = LOOKUP_SEP.join(trimmed_prefix)
         
         
         
         
         
         
        first_join = self.alias_map[lookup_tables[trimmed_paths + 1]]
        if first_join.join_type != LOUTER and not first_join.filtered_relation:
            select_fields = [r[0] for r in join_field.related_fields]
            select_alias = lookup_tables[trimmed_paths + 1]
            self.unref_alias(lookup_tables[trimmed_paths])
            extra_restriction = join_field.get_extra_restriction(
                None, lookup_tables[trimmed_paths + 1]
            )
            if extra_restriction:
                self.where.add(extra_restriction, AND)
        else:
             
             
             
             
            select_fields = [r[1] for r in join_field.related_fields]
            select_alias = lookup_tables[trimmed_paths]
         
         
         
        for table in self.alias_map:
            if self.alias_refcount[table] > 0:
                self.alias_map[table] = self.base_table_class(
                    self.alias_map[table].table_name,
                    table,
                )
                break
        self.set_select([f.get_col(select_alias) for f in select_fields])
        return trimmed_prefix, contains_louter

    def is_nullable(self, field):
        
         
         
         
         
         
        return field.null or (
            field.empty_strings_allowed
            and connections[DEFAULT_DB_ALIAS].features.interprets_empty_strings_as_nulls
        )
