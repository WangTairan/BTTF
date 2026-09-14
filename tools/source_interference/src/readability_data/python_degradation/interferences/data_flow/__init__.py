"""Local data-flow degradation plugins."""

from .plugins import PLUGINS, InlineIntermediateVariables, IntroduceNumericIntermediates

__all__ = [
    "InlineIntermediateVariables",
    "IntroduceNumericIntermediates",
    "PLUGINS",
]
