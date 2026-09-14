from __future__ import annotations

from readability_data.shared.alignment import INTERFERENCE_SPECS

from .interferences.code_injection import PLUGINS as CODE_INJECTION
from .interferences.comments import PLUGINS as COMMENTS
from .interferences.control_flow import PLUGINS as CONTROL_FLOW
from .interferences.data_flow import PLUGINS as DATA_FLOW
from .interferences.expressions import PLUGINS as EXPRESSIONS
from .interferences.identifiers import PLUGINS as IDENTIFIERS
from .interferences.layout import PLUGINS as LAYOUT

ORDERED = (
    *COMMENTS,
    *IDENTIFIERS,
    *EXPRESSIONS,
    *CODE_INJECTION,
    *LAYOUT,
    *DATA_FLOW,
    *CONTROL_FLOW,
)
INTERFERENCES = {plugin.slug: plugin for plugin in ORDERED}

if tuple((item.category, item.slug) for item in ORDERED) != tuple(
    (item.category, item.slug) for item in INTERFERENCE_SPECS
):
    raise RuntimeError("Python interference catalog violates the alignment contract")
