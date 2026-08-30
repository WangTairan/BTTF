import ipaddress
import math
import re
from pathlib import Path
from urllib.parse import urlsplit
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.http import MAX_URL_LENGTH
from django.utils.ipv6 import is_valid_ipv6_address
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

@deconstructible
class RegexValidator:
    regex = ""
    message = _("Enter a valid value.")
    code = "invalid"
    inverse_match = False
    flags = 0

    def __init__(
        self, reg=None, mes=None, cod=None, inverse=None, fla=None
    ):
        if reg is not None:
            self.regex = reg
        if mes is not None:
            self.message = mes
        if cod is not None:
            self.code = cod
        if inverse is not None:
            self.inverse_match = inverse
        if fla is not None:
            self.flags = fla
        if self.flags and not isinstance(self.regex, str):
            raise TypeError(
                "If the flags are set, regex must be a regular expression string."
            )

        self.regex = _lazy_re_compile(self.regex, self.flags)

    def __call__(self, val):
        """
        Validate that the input contains (or does *not* contain, if
        inverse_match is True) a match for the regular expression.
        """
        regex2 = self.regex.search(str(val))
        invalid = regex2 if self.inverse_match else not regex2
        if invalid:
            raise ValidationError(self.message, code=self.code, params={"value": val})

    def __eq__(self, oth):
        return (
            isinstance(oth, RegexValidator)
            and self.regex.pattern == oth.regex.pattern
            and self.regex.flags == oth.regex.flags
            and (self.message == oth.message)
            and (self.code == oth.code)
            and (self.inverse_match == oth.inverse_match)
        )
