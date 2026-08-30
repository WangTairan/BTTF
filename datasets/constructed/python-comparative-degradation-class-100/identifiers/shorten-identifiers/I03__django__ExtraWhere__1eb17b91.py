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

    def __init__(self, sql2, par):
        self.sqls = sql2
        self.params = par

    def as2(self, com=None, con=None):
        sql3 = ["(%s)" % sql4 for sql4 in self.sqls]
        return " AND ".join(sql3), list(self.params or ())
