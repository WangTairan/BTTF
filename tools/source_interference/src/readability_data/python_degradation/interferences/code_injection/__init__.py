"""Code-injection interference plugins."""

from .injectors import InjectLowReadabilityCode, InjectReadableCode, InsertDeadBranches
from .plugins import OPAQUE, PLUGINS, READABLE

__all__ = [
    "InjectLowReadabilityCode",
    "InjectReadableCode",
    "InsertDeadBranches",
    "OPAQUE",
    "PLUGINS",
    "READABLE",
]
