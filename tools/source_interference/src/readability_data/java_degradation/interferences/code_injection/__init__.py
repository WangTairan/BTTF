"""Behaviorally isolated source-code injection interferences."""

from readability_data.java_degradation.interferences.code_injection.dead_branch import (
    InsertDeadBranches,
)
from readability_data.java_degradation.interferences.code_injection.low_readability import (
    InjectLowReadabilityCode,
)
from readability_data.java_degradation.interferences.code_injection.readable import (
    InjectReadableCode,
)

__all__ = ["InjectLowReadabilityCode", "InjectReadableCode", "InsertDeadBranches"]
