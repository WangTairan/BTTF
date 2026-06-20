from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import random

from .masking import apply_char_masks, merge_strict_char_spans
from .config import (
    DEFAULT_AST_MAX_COMBINATION_SIZE,
    DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
    DEFAULT_AST_MIN_TOKENS,
    DEFAULT_AST_SAMPLING_SEED,
)
from .types import MaskConstraints, MaskSpan, MaskedSequence

try:
    import javalang
except ImportError:  # pragma: no cover
    javalang = None


JAVA_AST_STRATEGY = "java_ast_stratified_v8"
AST_GRANULARITIES = ("control", "statement")
BLOCK_NODE_TYPES = {"MethodDeclaration", "ConstructorDeclaration"}
STATEMENT_NODE_TYPES = {
    "FieldDeclaration",
    "LocalVariableDeclaration",
    "ReturnStatement",
    "ThrowStatement",
    "StatementExpression",
}
LOOP_NODE_TYPES = {"ForStatement", "WhileStatement", "DoStatement"}
CONTROL_BLOCK_NODE_TYPES = {"SwitchStatement", "TryStatement"}
DECLARATION_NODE_TYPES = {
    "MethodDeclaration",
    "ConstructorDeclaration",
    "FieldDeclaration",
    "LocalVariableDeclaration",
}
DECLARATION_MODIFIERS = {
    "public",
    "protected",
    "private",
    "abstract",
    "static",
    "final",
    "transient",
    "volatile",
    "synchronized",
    "native",
    "strictfp",
    "default",
}


@dataclass(frozen=True)
class TokenPosition:
    value: str
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class AstCandidate:
    node_type: str
    start: int
    end: int
    token_count: int
    ast_role: str = "whole"


def java_ast_masks(
    source: str,
    constraints: MaskConstraints,
    min_tokens: int = DEFAULT_AST_MIN_TOKENS,
    max_combination_size: int = DEFAULT_AST_MAX_COMBINATION_SIZE,
    max_samples_per_stratum: int | None = DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
    sampling_seed: int = DEFAULT_AST_SAMPLING_SEED,
    ast_granularity: str | None = None,
) -> tuple[MaskedSequence, ...]:
    """Produce masks for one AST granularity, or all granularities when omitted."""
    constraints.validate()
    if min_tokens < 1:
        raise ValueError("min_tokens must be >= 1")
    if max_combination_size < 1:
        raise ValueError("max_combination_size must be >= 1")
    if max_samples_per_stratum is not None and max_samples_per_stratum < 1:
        raise ValueError("max_samples_per_stratum must be >= 1")
    if ast_granularity is not None and ast_granularity not in AST_GRANULARITIES:
        raise ValueError(f"ast_granularity must be one of {AST_GRANULARITIES}")
    tree, parsed_source, prefix_length = _parse_java(source)
    tokens = _tokens(parsed_source)
    candidates = _candidates(tree, tokens, prefix_length, len(source))
    eligible = tuple(
        candidate
        for candidate in candidates
        if candidate.token_count >= min_tokens
        and (ast_granularity is None or _ast_granularity(candidate) == ast_granularity)
    )
    masks = [
        _build_mask(source, (candidate,), _ast_granularity(candidate))
        for candidate in eligible
    ]
    by_granularity: dict[str, list[AstCandidate]] = {}
    for candidate in eligible:
        by_granularity.setdefault(_ast_granularity(candidate), []).append(candidate)
    for granularity, same_level in by_granularity.items():
        for count in range(2, min(max_combination_size, len(same_level)) + 1):
            sampled, total = _sample_non_overlapping(
                same_level,
                count,
                max_samples_per_stratum,
                source,
                granularity,
                sampling_seed,
            )
            for selected in sampled:
                masks.append(
                    _build_mask(
                        source,
                        selected,
                        granularity,
                        stratum_total=total,
                        stratum_sampled=len(sampled),
                        sampling_seed=sampling_seed,
                    )
                )
    return tuple(masks)


def _ast_granularity(candidate: AstCandidate) -> str:
    if candidate.ast_role == "method_body":
        return "control"
    if candidate.node_type in LOOP_NODE_TYPES | {"IfBranch", "SwitchCase", "TryBody", "CatchBody", "FinallyBody"}:
        return "control"
    return "statement"


def _sample_non_overlapping(
    candidates: list[AstCandidate],
    count: int,
    limit: int | None,
    source: str,
    granularity: str,
    sampling_seed: int,
) -> tuple[tuple[tuple[AstCandidate, ...], ...], int]:
    ordered = tuple(sorted(candidates, key=lambda item: (item.start, item.end, item.node_type)))
    starts = [candidate.start for candidate in ordered]
    next_indexes = [
        bisect_left(starts, candidate.end, lo=index + 1)
        for index, candidate in enumerate(ordered)
    ]

    @lru_cache(maxsize=None)
    def subset_count(index: int, remaining: int) -> int:
        if remaining == 0:
            return 1
        if index >= len(ordered) or len(ordered) - index < remaining:
            return 0
        return subset_count(index + 1, remaining) + subset_count(next_indexes[index], remaining - 1)

    total = subset_count(0, count)
    if total == 0:
        return (), 0
    if limit is None or limit >= total:
        ranks = range(total)
    else:
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        rng = random.Random(f"{sampling_seed}:{digest}:{granularity}:{count}")
        ranks = sorted(rng.sample(range(total), limit))

    def unrank(rank: int) -> tuple[AstCandidate, ...]:
        selected = []
        index = 0
        remaining = count
        while remaining:
            include = subset_count(next_indexes[index], remaining - 1)
            if rank < include:
                selected.append(ordered[index])
                index = next_indexes[index]
                remaining -= 1
            else:
                rank -= include
                index += 1
        return tuple(selected)

    return tuple(unrank(rank) for rank in ranks), total


def _build_mask(
    source: str,
    candidates: tuple[AstCandidate, ...],
    granularity: str,
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
        strategy=JAVA_AST_STRATEGY,
        node_type=single.node_type if single is not None else None,
        char_start=single.start if single is not None else None,
        char_end=single.end if single is not None else None,
        token_count=sum(candidate.token_count for candidate in ordered),
        ast_role=single.ast_role if single is not None else None,
        ast_granularity=granularity,
        node_types=tuple(candidate.node_type for candidate in ordered),
        ast_roles=tuple(candidate.ast_role for candidate in ordered),
        char_spans=char_spans,
        stratum_total=stratum_total,
        stratum_sampled=stratum_sampled,
        sampling_seed=sampling_seed,
    )


def _parse_java(source: str):
    if javalang is None:
        raise RuntimeError("Missing dependency: javalang. Install requirements.txt.")
    try:
        return javalang.parse.parse(source), source, 0
    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as initial_error:
        prefix = "class Snippet {\n"
        wrapped = prefix + source + "\n}\n"
        try:
            return javalang.parse.parse(wrapped), wrapped, len(prefix)
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError):
            raise initial_error


def _tokens(source: str) -> list[TokenPosition]:
    line_offsets = _line_offsets(source)
    result = []
    for token in javalang.tokenizer.tokenize(source):
        start = line_offsets[token.position.line - 1] + token.position.column - 1
        result.append(
            TokenPosition(
                value=token.value,
                start=start,
                end=start + len(token.value),
                line=token.position.line,
                column=token.position.column,
            )
        )
    return result


def _candidates(tree, tokens: list[TokenPosition], prefix_length: int, source_length: int) -> tuple[AstCandidate, ...]:
    unique: dict[tuple[int, int, str], AstCandidate] = {}
    for _, node in tree:
        node_type = node.__class__.__name__
        if node_type == "IfStatement":
            _add_if_candidates(unique, node, tokens, prefix_length, source_length)
            continue
        if node_type in LOOP_NODE_TYPES:
            interval = _control_body_interval(node, tokens)
            if interval is not None:
                _add_candidate(
                    unique,
                    node_type=node_type,
                    role="body",
                    start_index=interval[0],
                    end_index=interval[1],
                    tokens=tokens,
                    prefix_length=prefix_length,
                    source_length=source_length,
                )
            continue
        if node_type == "SwitchStatement":
            _add_switch_case_candidates(unique, node, tokens, prefix_length, source_length)
            continue
        if node_type == "TryStatement":
            _add_try_body_candidates(unique, node, tokens, prefix_length, source_length)
            continue
        if node_type in BLOCK_NODE_TYPES:
            interval = _method_body_interval(node, tokens)
            if interval is not None:
                _add_candidate(
                    unique,
                    node_type=node_type,
                    role="method_body",
                    start_index=interval[0],
                    end_index=interval[1],
                    tokens=tokens,
                    prefix_length=prefix_length,
                    source_length=source_length,
                )
            continue
        if node_type not in STATEMENT_NODE_TYPES:
            continue
        token_index = _token_index_at_node(tokens, node)
        if token_index is None:
            continue
        start_index = (
            _declaration_start(tokens, token_index)
            if node_type in DECLARATION_NODE_TYPES
            else token_index
        )
        end_index = _statement_end_index(tokens, token_index)
        if end_index is None:
            continue
        _add_candidate(
            unique,
            node_type=node_type,
            role="whole",
            start_index=start_index,
            end_index=end_index,
            tokens=tokens,
            prefix_length=prefix_length,
            source_length=source_length,
        )
    return tuple(sorted(unique.values(), key=lambda item: (item.start, item.end, item.node_type, item.ast_role)))


def _add_if_candidates(
    unique: dict[tuple[int, int, str], AstCandidate],
    node,
    tokens: list[TokenPosition],
    prefix_length: int,
    source_length: int,
) -> None:
    token_index = _token_index_at_node(tokens, node)
    if token_index is None:
        return
    for role, statement in (("then_branch", node.then_statement), ("else_branch", node.else_statement)):
        if statement is None:
            continue
        interval = _statement_body_interval(statement, tokens)
        if interval is not None:
            _add_candidate(
                unique,
                node_type="IfBranch",
                role=role,
                start_index=interval[0],
                end_index=interval[1],
                tokens=tokens,
                prefix_length=prefix_length,
                source_length=source_length,
            )


def _add_switch_case_candidates(
    unique: dict[tuple[int, int, str], AstCandidate],
    node,
    tokens: list[TokenPosition],
    prefix_length: int,
    source_length: int,
) -> None:
    token_index = _token_index_at_node(tokens, node)
    if token_index is None:
        return
    open_index = next((i for i in range(token_index, len(tokens)) if tokens[i].value == "{"), None)
    close_index = _block_end_index(tokens, token_index)
    if open_index is None or close_index is None:
        return
    label_indexes = [
        index
        for index in range(open_index + 1, close_index)
        if tokens[index].value in {"case", "default"}
    ]
    for offset, label_index in enumerate(label_indexes):
        colon_index = next(
            (i for i in range(label_index, close_index) if tokens[i].value == ":"),
            None,
        )
        if colon_index is None:
            continue
        next_label = label_indexes[offset + 1] if offset + 1 < len(label_indexes) else close_index
        start_index = colon_index + 1
        end_index = next_label - 1
        if start_index <= end_index:
            _add_candidate(
                unique,
                node_type="SwitchCase",
                role="case_body",
                start_index=start_index,
                end_index=end_index,
                tokens=tokens,
                prefix_length=prefix_length,
                source_length=source_length,
            )


def _add_try_body_candidates(
    unique: dict[tuple[int, int, str], AstCandidate],
    node,
    tokens: list[TokenPosition],
    prefix_length: int,
    source_length: int,
) -> None:
    token_index = _token_index_at_node(tokens, node)
    if token_index is None:
        return
    try_body = _block_body_interval(tokens, token_index)
    if try_body is not None:
        _add_candidate(
            unique,
            node_type="TryBody",
            role="try_body",
            start_index=try_body[0],
            end_index=try_body[1],
            tokens=tokens,
            prefix_length=prefix_length,
            source_length=source_length,
        )
    try_end = _block_end_index(tokens, token_index)
    cursor = try_end + 1 if try_end is not None else token_index + 1
    while cursor < len(tokens):
        value = tokens[cursor].value
        if value == "catch":
            body = _block_body_interval(tokens, cursor)
            if body is not None:
                _add_candidate(
                    unique,
                    node_type="CatchBody",
                    role="catch_body",
                    start_index=body[0],
                    end_index=body[1],
                    tokens=tokens,
                    prefix_length=prefix_length,
                    source_length=source_length,
                )
                end_index = _block_end_index(tokens, cursor)
                cursor = end_index + 1 if end_index is not None else cursor + 1
                continue
        if value == "finally":
            body = _block_body_interval(tokens, cursor)
            if body is not None:
                _add_candidate(
                    unique,
                    node_type="FinallyBody",
                    role="finally_body",
                    start_index=body[0],
                    end_index=body[1],
                    tokens=tokens,
                    prefix_length=prefix_length,
                    source_length=source_length,
                )
            return
        return


def _add_candidate(
    unique: dict[tuple[int, int, str], AstCandidate],
    node_type: str,
    role: str,
    start_index: int,
    end_index: int,
    tokens: list[TokenPosition],
    prefix_length: int,
    source_length: int,
) -> None:
    start = tokens[start_index].start - prefix_length
    end = tokens[end_index].end - prefix_length
    if start < 0 or end > source_length or start >= end:
        return
    unique.setdefault(
        (start, end, role),
        AstCandidate(
            node_type=node_type,
            start=start,
            end=end,
            token_count=end_index - start_index + 1,
            ast_role=role,
        ),
    )


def _token_index_at_node(tokens: list[TokenPosition], node) -> int | None:
    position = getattr(node, "position", None)
    if position is None:
        return None
    for index, token in enumerate(tokens):
        if token.line == position.line and token.column >= position.column:
            return index
    return None


def _declaration_start(tokens: list[TokenPosition], index: int) -> int:
    line = tokens[index].line
    while (
        index > 0
        and tokens[index - 1].line == line
        and tokens[index - 1].value in DECLARATION_MODIFIERS
    ):
        index -= 1
    return index


def _block_end_index(tokens: list[TokenPosition], index: int) -> int | None:
    brace_index = next((i for i in range(index, len(tokens)) if tokens[i].value == "{"), None)
    if brace_index is None:
        return None
    depth = 0
    for end_index, token in enumerate(tokens[brace_index:], start=brace_index):
        if token.value == "{":
            depth += 1
        elif token.value == "}":
            depth -= 1
            if depth == 0:
                return end_index
    return None


def _block_body_interval(tokens: list[TokenPosition], index: int) -> tuple[int, int] | None:
    brace_index = next((i for i in range(index, len(tokens)) if tokens[i].value == "{"), None)
    if brace_index is None:
        return None
    end_index = _block_end_index(tokens, index)
    if end_index is None or brace_index + 1 > end_index - 1:
        return None
    return brace_index + 1, end_index - 1


def _statement_body_interval(node, tokens: list[TokenPosition]) -> tuple[int, int] | None:
    token_index = _token_index_at_node(tokens, node)
    if token_index is None:
        return None
    if tokens[token_index].value == "{":
        return _block_body_interval(tokens, token_index)
    return _node_interval(node, tokens)


def _control_body_interval(node, tokens: list[TokenPosition]) -> tuple[int, int] | None:
    node_type = node.__class__.__name__
    if node_type in {"ForStatement", "WhileStatement"}:
        return _statement_body_interval(node.body, tokens)
    if node_type == "DoStatement":
        return _statement_body_interval(node.body, tokens)
    return _statement_body_interval(node, tokens)


def _method_body_interval(node, tokens: list[TokenPosition]) -> tuple[int, int] | None:
    token_index = _token_index_at_node(tokens, node)
    if token_index is None:
        return None
    open_index = next((index for index in range(token_index, len(tokens)) if tokens[index].value == "{"), None)
    if open_index is None:
        return None
    close_index = _block_end_index(tokens, open_index)
    if close_index is None or open_index + 1 > close_index - 1:
        return None
    return open_index + 1, close_index - 1


def _parenthesized_interval(tokens: list[TokenPosition], index: int) -> tuple[int, int] | None:
    open_index = next((i for i in range(index, len(tokens)) if tokens[i].value == "("), None)
    if open_index is None:
        return None
    depth = 0
    for close_index, token in enumerate(tokens[open_index:], start=open_index):
        if token.value == "(":
            depth += 1
        elif token.value == ")":
            depth -= 1
            if depth == 0:
                return open_index, close_index
    return None


def _node_interval(node, tokens: list[TokenPosition]) -> tuple[int, int] | None:
    token_index = _token_index_at_node(tokens, node)
    if token_index is None:
        return None
    node_type = node.__class__.__name__
    if node_type == "BlockStatement":
        end_index = _block_end_index(tokens, token_index)
    elif node_type == "IfStatement":
        last = node.else_statement or node.then_statement
        nested = _node_interval(last, tokens)
        end_index = nested[1] if nested is not None else None
    elif node_type in {"ForStatement", "WhileStatement"}:
        nested = _node_interval(node.body, tokens)
        end_index = nested[1] if nested is not None else None
    elif node_type == "DoStatement":
        end_index = _statement_end_index(tokens, token_index)
    elif node_type == "SwitchStatement":
        end_index = _block_end_index(tokens, token_index)
    elif node_type == "TryStatement":
        end_index = _try_end_index(tokens, token_index)
    else:
        end_index = _statement_end_index(tokens, token_index)
    return (token_index, end_index) if end_index is not None else None


def _try_end_index(tokens: list[TokenPosition], index: int) -> int | None:
    """Return the end of a complete try/catch/finally control region."""
    end_index = _block_end_index(tokens, index)
    if end_index is None:
        return None
    cursor = end_index + 1
    while cursor < len(tokens) and tokens[cursor].value == "catch":
        end_index = _block_end_index(tokens, cursor)
        if end_index is None:
            return None
        cursor = end_index + 1
    if cursor < len(tokens) and tokens[cursor].value == "finally":
        return _block_end_index(tokens, cursor)
    return end_index


def _statement_end_index(tokens: list[TokenPosition], index: int) -> int | None:
    depth = {"(": 0, "[": 0, "{": 0}
    closes = {")": "(", "]": "[", "}": "{"}
    for end_index, token in enumerate(tokens[index:], start=index):
        if token.value in depth:
            depth[token.value] += 1
        elif token.value in closes:
            key = closes[token.value]
            depth[key] = max(0, depth[key] - 1)
        elif token.value == ";" and not any(depth.values()):
            return end_index
    return None


def _line_span(source: str, start: int, end: int) -> MaskSpan:
    first = source.count("\n", 0, start)
    last = source.count("\n", 0, max(start, end - 1)) + 1
    return MaskSpan(first, last)


def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for index, char in enumerate(source):
        if char == "\n":
            offsets.append(index + 1)
    return offsets
