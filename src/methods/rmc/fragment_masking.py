from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import hashlib
import random
import re

from .masking import apply_char_masks, merge_strict_char_spans
from .types import MaskConstraints, MaskSpan, MaskedSequence


JAVA_FRAGMENT_CONTROL_STRATEGY = "dorn_fragment_control_v2"
CONTROL_KEYWORDS = {"if", "for", "while", "do", "switch", "try", "catch", "synchronized"}
PYTHON_BLOCK_KEYWORDS = {"if", "elif", "else", "for", "while", "try", "except", "finally", "with"}
PYTHON_METHOD_KEYWORDS = {"def"}


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
        for candidate in _fragment_candidates(source, tokens)
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


def _fragment_candidates(source: str, tokens: tuple[FragmentToken, ...]) -> tuple[FragmentCandidate, ...]:
    candidates: dict[tuple[int, int, str, str], FragmentCandidate] = {}
    if "{" in source and "}" in source:
        for candidate in _brace_fragment_candidates(tokens):
            candidates.setdefault((candidate.start, candidate.end, candidate.node_type, candidate.role), candidate)
    for candidate in _python_indent_candidates(source):
        candidates.setdefault((candidate.start, candidate.end, candidate.node_type, candidate.role), candidate)
    return tuple(sorted(candidates.values(), key=lambda item: (item.start, item.end, item.node_type, item.role)))


def _brace_fragment_candidates(tokens: tuple[FragmentToken, ...]) -> tuple[FragmentCandidate, ...]:
    candidates: dict[tuple[int, int, str], FragmentCandidate] = {}
    index = 0
    while index < len(tokens):
        value = tokens[index].value
        if value in CONTROL_KEYWORDS:
            candidate_ranges = _control_body_candidates(tokens, index)
            for node_type, role, start, end in candidate_ranges:
                if end < start:
                    continue
                candidate = FragmentCandidate(
                    node_type=node_type,
                    start=tokens[start].start,
                    end=tokens[end].end,
                    token_count=end - start + 1,
                    role=role,
                )
                candidates.setdefault((candidate.start, candidate.end, candidate.node_type), candidate)
            index += 1
            continue

        method_body = _method_body_candidate(tokens, index)
        if method_body is not None:
            start, end = method_body
            candidate = FragmentCandidate(
                node_type="MethodBody",
                start=tokens[start].start,
                end=tokens[end].end,
                token_count=end - start + 1,
                role="method_body",
            )
            candidates.setdefault((candidate.start, candidate.end, candidate.node_type), candidate)
        index += 1
    return tuple(sorted(candidates.values(), key=lambda item: (item.start, item.end, item.node_type)))


def _control_body_candidates(
    tokens: tuple[FragmentToken, ...],
    index: int,
) -> tuple[tuple[str, str, int, int], ...]:
    keyword = tokens[index].value
    node_type = _node_type(keyword)
    if keyword == "if":
        return _if_body_candidates(tokens, index)
    if keyword == "try":
        return _try_body_candidates(tokens, index)
    if keyword == "do":
        start = _next_non_gap(tokens, index + 1)
        body = _statement_body_interval(tokens, start) if start is not None else None
        return ((node_type, "body", body[0], body[1]),) if body is not None else ()
    if keyword == "switch":
        return _switch_case_candidates(tokens, index)
    if keyword in {"for", "while", "catch", "synchronized"}:
        statement_start = _after_optional_parenthesized_header(tokens, index + 1)
        body = _statement_body_interval(tokens, statement_start) if statement_start is not None else None
        return ((node_type, "body", body[0], body[1]),) if body is not None else ()
    return ()


def _if_body_candidates(tokens: tuple[FragmentToken, ...], index: int) -> tuple[tuple[str, str, int, int], ...]:
    statement_start = _after_optional_parenthesized_header(tokens, index + 1)
    if statement_start is None:
        return ()
    then_body = _statement_body_interval(tokens, statement_start)
    if then_body is None:
        return ()
    result = [("IfBranch", "then_branch", then_body[0], then_body[1])]
    then_end = _statement_end(tokens, statement_start)
    next_index = _next_non_gap(tokens, then_end + 1) if then_end is not None else None
    if next_index is not None and tokens[next_index].value == "else":
        else_start = _next_non_gap(tokens, next_index + 1)
        if else_start is not None and tokens[else_start].value != "if":
            else_body = _statement_body_interval(tokens, else_start)
            if else_body is not None:
                result.append(("IfBranch", "else_branch", else_body[0], else_body[1]))
    return tuple(result)


def _switch_case_candidates(tokens: tuple[FragmentToken, ...], index: int) -> tuple[tuple[str, str, int, int], ...]:
    statement_start = _after_optional_parenthesized_header(tokens, index + 1)
    if statement_start is None or tokens[statement_start].value != "{":
        return ()
    close = _matching(tokens, statement_start, "{", "}")
    if close is None:
        return ()
    labels = [
        cursor
        for cursor in range(statement_start + 1, close)
        if tokens[cursor].value in {"case", "default"}
    ]
    result = []
    for offset, label in enumerate(labels):
        colon = next((cursor for cursor in range(label, close) if tokens[cursor].value == ":"), None)
        if colon is None:
            continue
        next_label = labels[offset + 1] if offset + 1 < len(labels) else close
        start = colon + 1
        end = next_label - 1
        if start <= end:
            result.append(("SwitchCase", "case_body", start, end))
    return tuple(result)


def _try_body_candidates(tokens: tuple[FragmentToken, ...], index: int) -> tuple[tuple[str, str, int, int], ...]:
    result = []
    try_body = _statement_body_interval(tokens, index + 1)
    if try_body is not None:
        result.append(("TryBody", "try_body", try_body[0], try_body[1]))
    try_end = _statement_end(tokens, index + 1)
    cursor = _next_non_gap(tokens, try_end + 1) if try_end is not None else None
    while cursor is not None and tokens[cursor].value in {"catch", "finally"}:
        if tokens[cursor].value == "catch":
            statement_start = _after_optional_parenthesized_header(tokens, cursor + 1)
            body = _statement_body_interval(tokens, statement_start) if statement_start is not None else None
            if body is not None:
                result.append(("CatchBody", "catch_body", body[0], body[1]))
            end = _statement_end(tokens, statement_start) if statement_start is not None else None
        else:
            body = _statement_body_interval(tokens, cursor + 1)
            if body is not None:
                result.append(("FinallyBody", "finally_body", body[0], body[1]))
            end = _statement_end(tokens, cursor + 1)
        cursor = _next_non_gap(tokens, end + 1) if end is not None else None
    return tuple(result)


def _method_body_candidate(tokens: tuple[FragmentToken, ...], index: int) -> tuple[int, int] | None:
    if tokens[index].value != "{":
        return None
    if index == 0 or tokens[index - 1].value != ")":
        return None
    header_start = _header_start_before_paren(tokens, index - 1)
    if header_start is None:
        return None
    header_values = {token.value for token in tokens[header_start:index]}
    if header_values & CONTROL_KEYWORDS:
        return None
    close = _matching(tokens, index, "{", "}")
    if close is None or index + 1 > close - 1:
        return None
    return index + 1, close - 1


def _header_start_before_paren(tokens: tuple[FragmentToken, ...], close_paren: int) -> int | None:
    open_paren = _matching_backward(tokens, close_paren, "(", ")")
    if open_paren is None:
        return None
    cursor = open_paren - 1
    while cursor >= 0 and tokens[cursor].value not in {";", "{", "}"}:
        cursor -= 1
    return cursor + 1


def _matching_backward(
    tokens: tuple[FragmentToken, ...],
    index: int,
    open_value: str,
    close_value: str,
) -> int | None:
    depth = 0
    for cursor in range(index, -1, -1):
        value = tokens[cursor].value
        if value == close_value:
            depth += 1
        elif value == open_value:
            depth -= 1
            if depth == 0:
                return cursor
    return None


def _python_indent_candidates(source: str) -> tuple[FragmentCandidate, ...]:
    lines = _source_lines(source)
    candidates: dict[tuple[int, int, str, str], FragmentCandidate] = {}
    for index, line in enumerate(lines):
        stripped = line["text"].strip()
        if not stripped or stripped.startswith("#") or not stripped.endswith(":"):
            continue
        keyword = _python_header_keyword(stripped)
        if keyword is None:
            continue
        body = _python_body_interval(lines, index)
        if body is None:
            continue
        start, end = body
        text = source[start:end]
        token_count = len(_tokens(text))
        if token_count == 0:
            continue
        node_type, role = _python_node_type(keyword)
        candidate = FragmentCandidate(
            node_type=node_type,
            start=start,
            end=end,
            token_count=token_count,
            role=role,
        )
        candidates.setdefault((candidate.start, candidate.end, candidate.node_type, candidate.role), candidate)
    return tuple(sorted(candidates.values(), key=lambda item: (item.start, item.end, item.node_type, item.role)))


def _source_lines(source: str) -> list[dict[str, int | str]]:
    lines = []
    offset = 0
    for raw in source.splitlines(keepends=True):
        text = raw[:-1] if raw.endswith("\n") else raw
        if text.endswith("\r"):
            text = text[:-1]
        lines.append(
            {
                "text": text,
                "start": offset,
                "end": offset + len(raw),
                "content_end": offset + len(text),
                "indent": _indent_width(text),
            }
        )
        offset += len(raw)
    if source and not source.endswith(("\n", "\r")) and not lines:
        lines.append({"text": source, "start": 0, "end": len(source), "content_end": len(source), "indent": _indent_width(source)})
    return lines


def _indent_width(text: str) -> int:
    width = 0
    for char in text:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4
        else:
            break
    return width


def _python_header_keyword(stripped: str) -> str | None:
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\b", stripped)
    if not match:
        return None
    keyword = match.group(1)
    if keyword in PYTHON_BLOCK_KEYWORDS or keyword in PYTHON_METHOD_KEYWORDS:
        return keyword
    return None


def _python_body_interval(lines: list[dict[str, int | str]], header_index: int) -> tuple[int, int] | None:
    header_indent = int(lines[header_index]["indent"])
    body_start_line: int | None = None
    last_body_line: int | None = None
    index = header_index + 1
    while index < len(lines):
        text = str(lines[index]["text"])
        stripped = text.strip()
        if not stripped:
            if body_start_line is not None:
                last_body_line = index
            index += 1
            continue
        indent = int(lines[index]["indent"])
        if indent <= header_indent:
            break
        if body_start_line is None:
            body_start_line = index
        last_body_line = index
        index += 1
    if body_start_line is None or last_body_line is None:
        return None
    return int(lines[body_start_line]["start"]), int(lines[last_body_line]["content_end"])


def _python_node_type(keyword: str) -> tuple[str, str]:
    return {
        "def": ("MethodBody", "method_body"),
        "if": ("IfBranch", "then_branch"),
        "elif": ("IfBranch", "elif_branch"),
        "else": ("IfBranch", "else_branch"),
        "for": ("ForStatement", "body"),
        "while": ("WhileStatement", "body"),
        "try": ("TryBody", "try_body"),
        "except": ("CatchBody", "catch_body"),
        "finally": ("FinallyBody", "finally_body"),
        "with": ("WithStatement", "body"),
    }[keyword]


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


def _statement_body_interval(tokens: tuple[FragmentToken, ...], index: int | None) -> tuple[int, int] | None:
    if index is None:
        return None
    index = _next_non_gap(tokens, index)
    if index is None or index >= len(tokens):
        return None
    if tokens[index].value == "{":
        close = _matching(tokens, index, "{", "}")
        if close is None or index + 1 > close - 1:
            return None
        return index + 1, close - 1
    end = _statement_end(tokens, index)
    return (index, end) if end is not None and index <= end else None


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
