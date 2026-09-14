"""Ordered Java interference catalog."""

from readability_data.java_degradation.interferences.code_injection import (
    InjectLowReadabilityCode,
    InjectReadableCode,
    InsertDeadBranches,
)
from readability_data.java_degradation.interferences.comments import (
    RemoveComments,
)
from readability_data.java_degradation.interferences.control_flow import LowerForToWhile
from readability_data.java_degradation.interferences.data_flow import (
    InlineIntermediateVariables,
    IntroduceNumericIntermediates,
)
from readability_data.java_degradation.interferences.expressions import (
    EncodeIntegerLiterals,
    InvertConditions,
)
from readability_data.java_degradation.interferences.identifiers import (
    RenameIdentifiers,
)
from readability_data.java_degradation.interferences.layout import (
    PartiallyCompactLayout,
)
from readability_data.shared.alignment import INTERFERENCE_SPECS

INTERFERENCE_CATALOG = (
    RemoveComments(),
    RenameIdentifiers("short"),
    RenameIdentifiers("misleading"),
    RenameIdentifiers("garbled"),
    EncodeIntegerLiterals(),
    InvertConditions(),
    InsertDeadBranches(),
    InjectReadableCode(),
    InjectLowReadabilityCode(),
    PartiallyCompactLayout(),
    IntroduceNumericIntermediates(),
    InlineIntermediateVariables(),
    LowerForToWhile(),
)

if tuple((item.category, item.slug) for item in INTERFERENCE_CATALOG) != tuple(
    (item.category, item.slug) for item in INTERFERENCE_SPECS
):
    raise RuntimeError("Java interference catalog violates the alignment contract")


def interference_registry():
    registry = {
        interference.slug: interference for interference in INTERFERENCE_CATALOG
    }
    if len(registry) != len(INTERFERENCE_CATALOG):
        raise ValueError("interference slugs must be unique")
    return registry
