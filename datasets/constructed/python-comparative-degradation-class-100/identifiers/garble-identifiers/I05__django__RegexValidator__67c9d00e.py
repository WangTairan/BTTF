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
        self, a=None, b=None, c=None, d=None, e=None
    ):
        if a is not None:
            self.regex = a
        if b is not None:
            self.message = b
        if c is not None:
            self.code = c
        if d is not None:
            self.inverse_match = d
        if e is not None:
            self.flags = e
        if self.flags and not isinstance(self.regex, str):
            raise TypeError(
                "If the flags are set, regex must be a regular expression string."
            )

        self.regex = _lazy_re_compile(self.regex, self.flags)

    def __call__(self, f):
        """
        Validate that the input contains (or does *not* contain, if
        inverse_match is True) a match for the regular expression.
        """
        g = self.regex.search(str(f))
        h = g if self.inverse_match else not g
        if h:
            raise ValidationError(self.message, code=self.code, params={"value": f})

    def __eq__(self, i):
        return (
            isinstance(i, RegexValidator)
            and self.regex.pattern == i.regex.pattern
            and self.regex.flags == i.regex.flags
            and (self.message == i.message)
            and (self.code == i.code)
            and (self.inverse_match == i.inverse_match)
        )
