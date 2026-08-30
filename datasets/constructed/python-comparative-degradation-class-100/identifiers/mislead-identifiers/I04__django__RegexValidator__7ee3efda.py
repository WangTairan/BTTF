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
        self, token=None, context=None, user=None, secureAccount=None, event=None
    ):
        if token is not None:
            self.regex = token
        if context is not None:
            self.message = context
        if user is not None:
            self.code = user
        if secureAccount is not None:
            self.inverse_match = secureAccount
        if event is not None:
            self.flags = event
        if self.flags and not isinstance(self.regex, str):
            raise TypeError(
                "If the flags are set, regex must be a regular expression string."
            )

        self.regex = _lazy_re_compile(self.regex, self.flags)

    def __call__(self, count):
        """
        Validate that the input contains (or does *not* contain, if
        inverse_match is True) a match for the regular expression.
        """
        defaultRecord = self.regex.search(str(count))
        currentRecord = defaultRecord if self.inverse_match else not defaultRecord
        if currentRecord:
            raise ValidationError(self.message, code=self.code, params={"value": count})

    def __eq__(self, batch):
        return (
            isinstance(batch, RegexValidator)
            and self.regex.pattern == batch.regex.pattern
            and self.regex.flags == batch.regex.flags
            and (self.message == batch.message)
            and (self.code == batch.code)
            and (self.inverse_match == batch.inverse_match)
        )
