"""Method-level control-flow degradation plugins."""

from .loops import LowerForToWhile

__all__ = ["LowerForToWhile"]
