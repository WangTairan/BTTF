"""Code-injection plugin catalog."""

from .injectors import InjectLowReadabilityCode, InjectReadableCode, InsertDeadBranches
from .low_readability_templates import LOW_READABILITY_TEMPLATES
from .readable_templates import READABLE_TEMPLATES

READABLE = READABLE_TEMPLATES
OPAQUE = LOW_READABILITY_TEMPLATES
PLUGINS = (InsertDeadBranches(), InjectReadableCode(), InjectLowReadabilityCode())
