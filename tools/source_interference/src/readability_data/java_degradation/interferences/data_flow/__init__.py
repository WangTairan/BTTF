"""Local data-flow degradation plugins."""

from .inline_temporaries import InlineIntermediateVariables
from .numeric_intermediates import IntroduceNumericIntermediates

__all__ = ["InlineIntermediateVariables", "IntroduceNumericIntermediates"]
