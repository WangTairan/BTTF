from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import hashlib
import random
import re

from .masking import apply_char_masks, merge_strict_char_spans
from .types import MaskConstraints, MaskSpan, MaskedSequence


JAVA_FRAGMENT_CONTROL_STRATEGY = "java_fragment_control_v1"
CONTROL_KEYWORDS = {"if", "for", "while", "do", "switch", "try", "catch", "synchronized"}


@dataclass(frozen=True)
class FragmentToken:
    value: str
    start: int
    end: int


@dataclass(frozen=True)
class FragmentCandidate:
    node_type: str
    start: int
    end: int
    token_count: int
    role: str = "whole_control"


def java_fragment_control_masks(
    source: str,
    constraints: MaskConstraints,
    min_tokens: int,
    max_combination_size: int,
    max_samples_per_stratum: int | None,
    sampling_seed: int,
) -> tuple[MaskedSequence, ...]:
    constraints.validate()
    if min_tokens < 1:
        raise ValueError("min_tokens must be >= 1")
    if max_combination_size < 1:
        raise ValueError("max_combination_size must be >= 1")
    if max_samples_per_stratum is not None and max_samples_per_stratum < 1:
        raise ValueError("max_samples_per_stratum must be >= 1")

    tokens = _tokens(source)
    candidates = tuple(
        candidate
        for candidate in _control_candidates(tokens)
        if candidate.token_count >= min_tokens
    )
    masks = [_build_mask(source, (candidate,)) for candidate in candidates]
    for count in range(2, min(max_combination_size, len(candidates)) + 1):
        sampled, total = _sample_non_overlapping(
            candidates,
            count,
            max_samples_per_stratum,
            source,
            sampling_seed,
        )
        for selected in sampled:
            masks.append(
                _build_mask(
                    source,
                    selected,
                    stratum_total=total,
                    stratum_sampled=len(sampled),
                    sampling_seed=sampling_seed if max_samples_per_stratum is not None else None,
                )
            )
    return tuple(masks)


def _tokens(source: str) -> tuple[FragmentToken, ...]:
    tokens: list[FragmentToken] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            index = len(source) if end < 0 else end + 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if char in {"'", '"'}:
            index = _skip_quoted(source, index, char)
            continue
        if re.match(r"[A-Za-z_$]", char):
            end = index + 1
            while end < len(source) and re.match(r"[A-Za-z0-9_$]", source[end]):
                end += 1
            tokens.append(FragmentToken(source[index:end], index, end))
            index = end
            continue
        tokens.append(FragmentToken(char, index, index + 1))
        index += 1
    return tuple(tokens)


def _skip_quoted(source: str, index: int, quote: str) -> int:
    index += 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
            continue
        if source[index] == quote:
            return index + 1
        index += 1
    return index


def _control_candidates(tokens: tuple[FragmentToken, ...]) -> tuple[FragmentCandidate, ...]:
    candidates: dict[tuple[int, int, str], FragmentCandidate] = {}
    index = 0
    while index < len(tokens):
        value = tokens[index].value
        if value not in CONTROL_KEYWORDS:
            index += 1
            continue
        end = _control_end(tokens, index)
        if end is None or end <= index:
            index += 1
            continue
        node_type = _node_type(value)
        candidate = FragmentCandidate(
            node_type=node_type,
            start=tokens[index].start,
            end=tokens[end].end,
            token_count=end - index + 1,
            role="whole_control",
        )
        candidates.setdefault((candidate.start, candidate.end, candidate.node_type), candidate)
        index += 1
    return tuple(sorted(candidates.values(), key=lambda item: (item.start, item.end, item.node_type)))


def _control_end(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    keyword = tokens[index].value
    if keyword == "if":
        return _if_end(tokens, index)
    if keyword == "try":
        return _try_end(tokens, index)
    if keyword == "do":
        return _do_end(tokens, index)
    if keyword in {"for", "while", "switch", "catch", "synchronized"}:
        statement_start = _after_optional_parenthesized_header(tokens, index + 1)
        if statement_start is None:
            return None
        return _statement_end(tokens, statement_start)
    return None


def _if_end(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    statement_start = _after_optional_parenthesized_header(tokens, index + 1)
    if statement_start is None:
        return None
    end = _statement_end(tokens, statement_start)
    if end is None:
        return None
    next_index = _next_non_gap(tokens, end + 1)
    if next_index is not None and tokens[next_index].value == "else":
        else_start = _next_non_gap(tokens, next_index + 1)
        if else_start is None:
            return end
        if tokens[else_start].value == "if":
            nested = _if_end(tokens, else_start)
            return nested if nested is not None else end
        else_end = _statement_end(tokens, else_start)
        return else_end if else_end is not None else end
    return end


def _try_end(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    end = _statement_end(tokens, index + 1)
    if end is None:
        return None
    cursor = _next_non_gap(tokens, end + 1)
    while cursor is not None and tokens[cursor].value in {"catch", "finally"}:
        if tokens[cursor].value == "catch":
            block_start = _after_optional_parenthesized_header(tokens, cursor + 1)
            if block_start is None:
                break
        else:
            block_start = cursor + 1
        next_end = _statement_end(tokens, block_start)
        if next_end is None:
            break
        end = next_end
        cursor = _next_non_gap(tokens, end + 1)
    return end


def _do_end(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    body_end = _statement_end(tokens, index + 1)
    if body_end is None:
        return None
    cursor = _next_non_gap(tokens, body_end + 1)
    if cursor is None or tokens[cursor].value != "while":
        return body_end
    header_end = _after_optional_parenthesized_header(tokens, cursor + 1)
    if header_end is None:
        return body_end
    if header_end < len(tokens) and tokens[header_end].value == ";":
        return header_end
    return header_end - 1


def _after_optional_parenthesized_header(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    index = _next_non_gap(tokens, index)
    if index is None:
        return None
    if tokens[index].value != "(":
        return index
    close = _matching(tokens, index, "(", ")")
    if close is None:
        return None
    return _next_non_gap(tokens, close + 1)


def _statement_end(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    index = _next_non_gap(tokens, index)
    if index is None or index >= len(tokens):
        return None
    if tokens[index].value == "{":
        return _matching(tokens, index, "{", "}")
    depth_paren = 0
    depth_brace = 0
    cursor = index
    while cursor < len(tokens):
        value = tokens[cursor].value
        if value == "(":
            depth_paren += 1
        elif value == ")":
            depth_paren = max(0, depth_paren - 1)
        elif value == "{":
            depth_brace += 1
        elif value == "}":
            if depth_brace == 0:
                return cursor - 1 if cursor > index else cursor
            depth_brace -= 1
        elif value == ";" and depth_paren == 0 and depth_brace == 0:
            return cursor
        cursor += 1
    return len(tokens) - 1


def _matching(
    tokens: tuple[FragmentToken, ...],
    index: int,
    open_value: str,
    close_value: str,
) -> int | None:
    depth = 0
    for cursor in range(index, len(tokens)):
        value = tokens[cursor].value
        if value == open_value:
            depth += 1
        elif value == close_value:
            depth -= 1
            if depth == 0:
                return cursor
    return None


def _next_non_gap(tokens: tuple[FragmentToken, ...], index: int) -> int | None:
    return index if index < len(tokens) else None


def _node_type(keyword: str) -> str:
    return {
        "if": "IfStatement",
        "for": "ForStatement",
        "while": "WhileStatement",
        "do": "DoStatement",
        "switch": "SwitchStatement",
        "try": "TryStatement",
        "catch": "CatchClause",
        "synchronized": "SynchronizedStatement",
    }[keyword]


def _sample_non_overlapping(
    candidates: tuple[FragmentCandidate, ...],
    count: int,
    limit: int | None,
    source: str,
    sampling_seed: int,
) -> tuple[tuple[tuple[FragmentCandidate, ...], ...], int]:
    selected = tuple(
        combination
        for combination in combinations(candidates, count)
        if _non_overlapping(combination)
    )
    total = len(selected)
    if limit is None or total <= limit:
        return selected, total
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    rng = random.Random(f"{sampling_seed}:{digest}:fragment_control:{count}")
    indexes = sorted(rng.sample(range(total), limit))
    return tuple(selected[index] for index in indexes), total


def _non_overlapping(candidates: tuple[FragmentCandidate, ...]) -> bool:
    ordered = sorted(candidates, key=lambda item: item.start)
    return all(left.end <= right.start for left, right in zip(ordered, ordered[1:]))


def _build_mask(
    source: str,
    candidates: tuple[FragmentCandidate, ...],
    stratum_total: int | None = None,
    stratum_sampled: int | None = None,
    sampling_seed: int | None = None,
) -> MaskedSequence:
    ordered = tuple(sorted(candidates, key=lambda item: item.start))
    char_spans = merge_strict_char_spans(
        source,
        ((candidate.start, candidate.end) for candidate in ordered),
    )
    masked_text = apply_char_masks(source, char_spans)
    spans = tuple(
        _line_span(source, start, end)
        for start, end in char_spans
    )
    single = ordered[0] if len(ordered) == 1 else None
    return MaskedSequence(
        lines=tuple(masked_text.splitlines()),
        spans=spans,
        granularity=len(ordered),
        masked_segments=len(ordered),
        selected_segments=len(ordered),
        strategy=JAVA_FRAGMENT_CONTROL_STRATEGY,
        node_type=single.node_type if single is not None else None,
        char_start=single.start if single is not None else None,
        char_end=single.end if single is not None else None,
        token_count=sum(candidate.token_count for candidate in ordered),
        ast_role=single.role if single is not None else None,
        ast_granularity="control",
        node_types=tuple(candidate.node_type for candidate in ordered),
        ast_roles=tuple(candidate.role for candidate in ordered),
        char_spans=char_spans,
        stratum_total=stratum_total,
        stratum_sampled=stratum_sampled,
        sampling_seed=sampling_seed,
    )


def _line_span(source: str, start: int, end: int) -> MaskSpan:
    offsets = _line_offsets(source)
    start_line = _line_index(offsets, start)
    end_line = _line_index(offsets, max(start, end - 1)) + 1
    return MaskSpan(start_line, end_line)


def _line_offsets(source: str) -> tuple[int, ...]:
    offsets = [0]
    for match in re.finditer("\n", source):
        offsets.append(match.end())
    return tuple(offsets)


def _line_index(offsets: tuple[int, ...], position: int) -> int:
    low = 0
    high = len(offsets)
    while low + 1 < high:
        mid = (low + high) // 2
        if offsets[mid] <= position:
            low = mid
        else:
            high = mid
    return low
