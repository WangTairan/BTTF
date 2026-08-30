import email.message
import email.policy
import mimetypes
import warnings
from collections import namedtuple
from datetime import datetime, timezone
from email import charset as Charset
from email import generator
from email.errors import HeaderParseError
from email.header import Header
from email.headerregistry import Address, AddressHeader, parser
from email.mime.base import MIMEBase
from email.mime.message import MIMEMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, getaddresses, make_msgid
from io import BytesIO, StringIO
from pathlib import Path
from django.conf import settings
from django.core.mail.utils import DNS_NAME
from django.utils.deprecation import (
    RemovedInDjango70Warning,
    deprecate_posargs,
    warn_about_external_use,
)
from django.utils.encoding import force_bytes, force_str, punycode
from django.utils.timezone import get_current_timezone
from .deprecation import (
    CONNECTION_ARG_WARNING,
    FAIL_SILENTLY_ARG_WARNING,
    report_using_incompatibility,
)

class SafeMIMEMultipart(MIMEMixin, MIMEMultipart):
    def __init__(
        self, a="mixed", b=None, c=None, d=None, **e
    ):
        self.encoding = d
        MIMEMultipart.__init__(self, a, b, c, **e)

    def __setitem__(self, f, g):
        f, g = forbid_multi_line_headers(f, g, self.encoding)
        MIMEMultipart.__setitem__(self, f, g)
