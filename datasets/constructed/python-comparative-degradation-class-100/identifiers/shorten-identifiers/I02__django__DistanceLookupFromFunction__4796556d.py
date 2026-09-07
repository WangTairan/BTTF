from django.contrib.gis.db.models.fields import BaseSpatialField
from django.contrib.gis.measure import Distance
from django.db import NotSupportedError
from django.db.models import Expression, Lookup, Transform
from django.db.models.sql.query import Query
from django.utils.regex_helper import _lazy_re_compile

class DistanceLookupFromFunction(DistanceLookupBase):
    def as2(self, com, con):
        sph = (
            len(self.rhs_params) == 2 and self.rhs_params[-1] == "spheroid"
        ) or None
        distance = con.ops.distance_expr_for_lookup(
            self.lhs, self.rhs, spheroid=sph
        )
        sql2, par = com.compile(distance.resolve_expression(com.query))
        dist, dist2 = self.process_distance(com, con)
        return (
            "%(func)s %(op)s %(dist)s" % {"func": sql2, "op": self.op, "dist": dist},
            (*par, *dist2),
        )
