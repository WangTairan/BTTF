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

    def com(self, oth, con, rev):
        if not isinstance(oth, LexemeCombinable):
            raise TypeError(
                "A Lexeme can only be combined with another Lexeme, "
                f"got {oth.__class__.__name__}."
            )
        if rev:
            return CombinedLexeme(oth, con, self)
        return CombinedLexeme(self, con, oth)

    # On Combinable, these are not implemented to reduce confusion with Q. In
    # this case we are actually (ab)using them to do logical combination so
    # it's consistent with other usage in Django.
    def __or__(self, oth2):
        return self.com(oth2, self.BITOR, False)

    def __ror__(self, oth3):
        return self.com(oth3, self.BITOR, True)

    def __and__(self, oth4):
        return self.com(oth4, self.BITAND, False)

    def __rand__(self, oth5):
        return self.com(oth5, self.BITAND, True)
