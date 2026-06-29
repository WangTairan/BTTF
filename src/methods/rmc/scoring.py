from __future__ import annotations

import re
from typing import Any


METHOD_BODY_CAPACITY = 2.0
METHOD_BODY_ERROR_PENALTY = 1.0
EXCEPTION_CONTROL_CAPACITY = 0.5
EXCEPTION_ERROR_PENALTY = 0.5
DEFAULT_CONTROL_CAPACITY = 1.0
DEFAULT_ERROR_PENALTY = 1.0
MASK_PROPORTION_WEIGHT = "4r(1-r)"
MIN_CONTROL_DENSITY_LOC = 30
MIN_CONTROL_DENSITY = 0.15
SPARSE_CONTROL_PENALTY = 0.10
AGGREGATION_LABEL = "capacity-normalized recovery error with sparse-control penalty"

TOKEN_PATTERN = re.compile(r"\w+|[^\s\w]", re.UNICODE)

METHOD_BODY_NODE_TYPES = {
    "MethodDeclaration",
    "ConstructorDeclaration",
    "MethodBody",
}
EXCEPTION_NODE_TYPES = {
    "TryBody",
    "CatchBody",
    "CatchClause",
    "FinallyBody",
    "WithStatement",
}


def score_task_result(task_data: dict[str, Any] | None) -> float | None:
    if not task_data:
        return None

    masks = {mask.get("index"): mask for mask in task_data.get("masks", [])}
    source_token_count = count_source_tokens(task_data)
    total_capacity = 0.0
    total_error = 0.0
    for recovery in task_data.get("recoveries", []):
        mask = masks.get(recovery.get("index"), {})
        selected_segments = mask.get("selected_segments") or recovery.get(
            "selected_segments"
        )
        score = _as_float(recovery.get("score", recovery.get("similarity")))
        if selected_segments != 1 or score is None:
            continue
        capacity, penalty = mask_capacity_and_penalty(
            recovery, mask, source_token_count
        )
        total_capacity += capacity
        total_error += penalty * (1 - score)

    if total_capacity == 0:
        return None

    score = 1 - total_error / total_capacity
    source_line_count = len(task_data.get("source_lines", []))
    control_count = sum(
        1
        for mask in masks.values()
        if mask.get("selected_segments") == 1 and not is_method_body(mask)
    )
    if (
        source_line_count >= MIN_CONTROL_DENSITY_LOC
        and control_count / source_line_count < MIN_CONTROL_DENSITY
    ):
        score = max(0.0, score - SPARSE_CONTROL_PENALTY)
    return score


def mask_capacity_and_penalty(
    recovery: dict[str, Any],
    mask: dict[str, Any],
    source_token_count: int,
) -> tuple[float, float]:
    token_count = _as_float(recovery.get("token_count", mask.get("token_count")))
    combined = {**mask, **recovery}
    if is_method_body(combined):
        capacity = METHOD_BODY_CAPACITY
        penalty = METHOD_BODY_ERROR_PENALTY
    elif str(combined.get("node_type") or "") in EXCEPTION_NODE_TYPES:
        capacity = EXCEPTION_CONTROL_CAPACITY
        penalty = EXCEPTION_ERROR_PENALTY
    else:
        capacity = DEFAULT_CONTROL_CAPACITY
        penalty = DEFAULT_ERROR_PENALTY
    ratio = min(1.0, max(0.0, (token_count or 0.0) / max(1, source_token_count)))
    contribution = 4 * ratio * (1 - ratio)
    capacity *= contribution
    penalty *= contribution
    return capacity, penalty


def is_method_body(mask: dict[str, Any]) -> bool:
    return str(mask.get("ast_role") or "") == "method_body" or str(
        mask.get("node_type") or ""
    ) in METHOD_BODY_NODE_TYPES


def count_source_tokens(task_data: dict[str, Any]) -> int:
    lines = task_data.get("source_lines") or []
    if not isinstance(lines, list):
        return 0
    return len(TOKEN_PATTERN.findall("\n".join(str(line) for line in lines)))


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
