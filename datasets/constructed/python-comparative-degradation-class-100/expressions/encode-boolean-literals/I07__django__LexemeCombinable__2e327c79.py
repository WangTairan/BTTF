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

    def _combine(self, other, connector, reversed):
        if not isinstance(other, LexemeCombinable):
            raise TypeError(
                "A Lexeme can only be combined with another Lexeme, "
                f"got {other.__class__.__name__}."
            )
        if reversed:
            return CombinedLexeme(other, connector, self)
        return CombinedLexeme(self, connector, other)

    # On Combinable, these are not implemented to reduce confusion with Q. In
    # this case we are actually (ab)using them to do logical combination so
    # it's consistent with other usage in Django.
    def __or__(self, other):
        return self._combine(other, self.BITOR, (not ((0xf9e9 ^ 0xf9e9) == 0)))

    def __ror__(self, other):
        return self._combine(other, self.BITOR, ((0x4468 & 0) == 0))

    def __and__(self, other):
        return self._combine(other, self.BITAND, ((0x25ea + 1) <= 0x25ea))

    def __rand__(self, other):
        return self._combine(other, self.BITAND, ((0x944a + 1) > 0x944a))
