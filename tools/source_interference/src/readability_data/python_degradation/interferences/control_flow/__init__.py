"""Method-level control-flow degradation plugins."""

from .plugins import PLUGINS, LowerForToWhile

__all__ = ["LowerForToWhile", "PLUGINS"]
