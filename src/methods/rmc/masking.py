from itertools import combinations
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from .types import MaskConstraints, MaskSpan, MaskedSequence


MASK_TOKEN = "<mask>"


def coerce_lines(sequence: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(sequence, str):
        return tuple(sequence.splitlines())
    return tuple(sequence)


def partition_indices(length: int, parts: int) -> Tuple[MaskSpan, ...]:
    return tuple(
        MaskSpan(
            start=(index * length) // parts,
            end=((index + 1) * length) // parts,
        )
        for index in range(parts)
    )


def merge_adjacent_spans(spans: Iterable[MaskSpan]) -> Tuple[MaskSpan, ...]:
    ordered = sorted(spans, key=lambda span: span.start)
    if not ordered:
        return ()

    merged: List[MaskSpan] = []
    current = ordered[0]
    for span in ordered[1:]:
        if span.start <= current.end:
            current = MaskSpan(current.start, max(current.end, span.end))
            continue
        merged.append(current)
        current = span

    merged.append(current)
    return tuple(merged)


def merge_strict_char_spans(
    source: str,
    spans: Iterable[tuple[int, int]],
) -> Tuple[tuple[int, int], ...]:
    ordered = sorted(spans, key=lambda span: span[0])
    if not ordered:
        return ()

    merged: List[tuple[int, int]] = []
    current_start, current_end = ordered[0]
    for start, end in ordered[1:]:
        gap = source[current_end:start]
        if start <= current_end or gap.strip() == "":
            current_end = max(current_end, end)
            continue
        merged.append((current_start, current_end))
        current_start, current_end = start, end

    merged.append((current_start, current_end))
    return tuple(merged)


def apply_char_masks(source: str, spans: Sequence[tuple[int, int]]) -> str:
    parts: List[str] = []
    cursor = 0
    for start, end in spans:
        parts.append(source[cursor:start])
        parts.append(MASK_TOKEN)
        cursor = end
    parts.append(source[cursor:])
    return "".join(parts)


def apply_masks(lines: Sequence[str], spans: Sequence[MaskSpan]) -> Tuple[str, ...]:
    masked: List[str] = []
    cursor = 0

    for span in spans:
        masked.extend(lines[cursor:span.start])
        masked.append(MASK_TOKEN)
        cursor = span.end

    masked.extend(lines[cursor:])
    return tuple(masked)


def is_reasonable_combination(
    lines: Sequence[str],
    spans: Sequence[MaskSpan],
    constraints: MaskConstraints,
) -> bool:
    """Reserved for pruning combinations that are not meaningful to recover."""
    return True


def delta_mask(
    sequence: Union[str, Sequence[str]],
    constraints: MaskConstraints,
    granularity: Optional[int] = None,
    masked_segments: int = 1,
) -> Tuple[MaskedSequence, ...]:
    constraints.validate()
    lines = coerce_lines(sequence)

    if granularity is None:
        granularity = max(
            constraints.nmin,
            (len(lines) + constraints.lmax - 1) // constraints.lmax,
        )

    if len(lines) / granularity < constraints.lmin:
        return ()
    if granularity > constraints.nmax:
        return ()

    partitions = partition_indices(len(lines), granularity)
    local: List[MaskedSequence] = []

    for selected in combinations(partitions, masked_segments):
        spans = merge_adjacent_spans(selected)

        if len(spans) > constraints.nmax:
            continue
        if any(span.length < constraints.lmin for span in spans):
            continue
        if any(span.length > constraints.lmax for span in spans):
            continue
        if not is_reasonable_combination(lines, spans, constraints):
            continue

        local.append(
            MaskedSequence(
                lines=apply_masks(lines, spans),
                spans=spans,
                granularity=granularity,
                masked_segments=len(spans),
                selected_segments=masked_segments,
            )
        )

    if masked_segments < granularity - 1:
        local.extend(
            delta_mask(
                lines,
                constraints,
                granularity=granularity,
                masked_segments=masked_segments + 1,
            )
        )
    else:
        local.extend(
            delta_mask(
                lines,
                constraints,
                granularity=2 * granularity,
                masked_segments=1,
            )
        )

    return tuple(local)
