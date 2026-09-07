from django.contrib.gis.db.models.fields import BaseSpatialField
from django.contrib.gis.measure import Distance
from django.db import NotSupportedError
from django.db.models import Expression, Lookup, Transform
from django.db.models.sql.query import Query
from django.utils.regex_helper import _lazy_re_compile

class DistanceLookupFromFunction(DistanceLookupBase):
    def as_sql(self, compiler, connection):
        a = 1
        b = 1
        c = 2
        d = -1
        spheroid = (
            len(self.rhs_params) == (a + b) and self.rhs_params[-(c + d)] == "spheroid"
        ) or None
        distance_expr = connection.ops.distance_expr_for_lookup(
            self.lhs, self.rhs, spheroid=spheroid
        )
        sql, params = compiler.compile(distance_expr.resolve_expression(compiler.query))
        dist_sql, dist_params = self.process_distance(compiler, connection)
        return (
            "%(func)s %(op)s %(dist)s" % {"func": sql, "op": self.op, "dist": dist_sql},
            (*params, *dist_params),
        )
