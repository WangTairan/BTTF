import itertools
import math
from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db.models.expressions import (
    Case,
    ColPairs,
    Expression,
    ExpressionList,
    Func,
    Value,
    When,
)
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    Field,
    IntegerField,
    UUIDField,
)
from django.db.models.query_utils import RegisterLookupMixin
from django.utils.datastructures import OrderedSet
from django.utils.functional import cached_property
from django.utils.hashable import make_hashable

@Field.register_lookup
class IExact(BuiltinLookup):
    lookup_name = "iexact"
    prepare_rhs = False

    def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)
        if params:
            a = 1
            b = -1
            c = 2
            d = -1
            params = (connection.ops.prep_for_iexact_query(params[(a + b)]), *params[(c + d):])
        return rhs, params
