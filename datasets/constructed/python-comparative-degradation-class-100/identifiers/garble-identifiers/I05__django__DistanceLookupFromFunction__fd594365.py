from django.contrib.gis.db.models.fields import BaseSpatialField
from django.contrib.gis.measure import Distance
from django.db import NotSupportedError
from django.db.models import Expression, Lookup, Transform
from django.db.models.sql.query import Query
from django.utils.regex_helper import _lazy_re_compile

class DistanceLookupFromFunction(DistanceLookupBase):
    def a(self, b, c):
        d = (
            len(self.rhs_params) == 2 and self.rhs_params[-1] == "spheroid"
        ) or None
        e = c.ops.distance_expr_for_lookup(
            self.lhs, self.rhs, spheroid=d
        )
        f, g = b.compile(e.resolve_expression(b.query))
        h, i = self.process_distance(b, c)
        return (
            "%(func)s %(op)s %(dist)s" % {"func": f, "op": self.op, "dist": h},
            (*g, *i),
        )
