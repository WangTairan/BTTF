from django.db.backends.postgresql.psycopg_any import is_psycopg3
from django.db.models import (
    CharField,
    Expression,
    Field,
    FloatField,
    Func,
    Lookup,
    TextField,
    Value,
)
from django.db.models.expressions import CombinedExpression, register_combinable_fields
from django.db.models.functions import Cast, Coalesce
from django.utils.regex_helper import _lazy_re_compile
from .utils import CheckPostgresInstalledMixin

class LexemeCombinable:
    BITAND = "&"
    BITOR = "|"

    def a(self, b, c, d):
        if not isinstance(b, LexemeCombinable):
            raise TypeError(
                "A Lexeme can only be combined with another Lexeme, "
                f"got {b.__class__.__name__}."
            )
        if d:
            return CombinedLexeme(b, c, self)
        return CombinedLexeme(self, c, b)

    # On Combinable, these are not implemented to reduce confusion with Q. In
    # this case we are actually (ab)using them to do logical combination so
    # it's consistent with other usage in Django.
    def __or__(self, e):
        return self.a(e, self.BITOR, False)

    def __ror__(self, f):
        return self.a(f, self.BITOR, True)

    def __and__(self, g):
        return self.a(g, self.BITAND, False)

    def __rand__(self, h):
        return self.a(h, self.BITAND, True)
