"""Expression plugin catalog."""

from .conditions import InvertConditions
from .literals import EncodeIntegerLiterals

PLUGINS = (EncodeIntegerLiterals(), InvertConditions())
