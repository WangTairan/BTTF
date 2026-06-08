from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class DatasetItem:
    task_id: str
    content: str
    readability_score: float | None = None
    readability_prompt: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

