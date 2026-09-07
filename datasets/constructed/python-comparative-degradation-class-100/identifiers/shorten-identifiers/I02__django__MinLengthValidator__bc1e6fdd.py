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
class MinLengthValidator(BaseValidator):
    message = ngettext_lazy(
        "Ensure this value has at least %(limit_value)d character (it has "
        "%(show_value)d).",
        "Ensure this value has at least %(limit_value)d characters (it has "
        "%(show_value)d).",
        "limit_value",
    )
    code = "min_length"

    def com(self, a2, b2):
        return a2 < b2

    def cle(self, x2):
        return len(x2)
