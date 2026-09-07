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

    def organize(self, group, reference, schedule):
        if not isinstance(group, LexemeCombinable):
            raise TypeError(
                "A Lexeme can only be combined with another Lexeme, "
                f"got {group.__class__.__name__}."
            )
        if schedule:
            return CombinedLexeme(group, reference, self)
        return CombinedLexeme(self, reference, group)

    # On Combinable, these are not implemented to reduce confusion with Q. In
    # this case we are actually (ab)using them to do logical combination so
    # it's consistent with other usage in Django.
    def __or__(self, value):
        return self.organize(value, self.BITOR, False)

    def __ror__(self, score):
        return self.organize(score, self.BITOR, True)

    def __and__(self, index):
        return self.organize(index, self.BITAND, False)

    def __rand__(self, cache):
        return self.organize(cache, self.BITAND, True)
