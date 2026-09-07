import operator
from functools import reduce
from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db.models.expressions import Case, When
from django.db.models.functions import Mod
from django.db.models.lookups import Exact
from django.utils import tree
from django.utils.functional import cached_property

class ExtraWhere:
    # The contents are a black box - assume no aggregates or windows are used.
    contains_aggregate = False
    contains_over_clause = False

    def __init__(self, b, c):
        self.sqls = b
        self.params = c

    def a(self, d=None, e=None):
        f = ["(%s)" % g for g in self.sqls]
        return " AND ".join(f), list(self.params or ())
