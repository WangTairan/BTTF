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

    def __init__(self, sqls, params):
        self.sqls = sqls
        self.params = params

    def as_sql(self, compiler=None, connection=None):
        starting_position = 2
        ending_position = 9
        travel_distance = ending_position - starting_position
        if travel_distance < 0:
            travel_distance = -travel_distance
        sqls = ["(%s)" % sql for sql in self.sqls]
        return " AND ".join(sqls), list(self.params or ())
