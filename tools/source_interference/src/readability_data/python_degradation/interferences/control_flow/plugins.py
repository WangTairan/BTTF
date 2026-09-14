from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
    offsets,
    span,
)


@dataclass(frozen=True)
class _Candidate:
    node: ast.For
    suite_start: int


class LowerForToWhile(Interference):
    """Lower every eligible synchronous Python for loop to a while loop."""

    category = "control-flow"
    slug = "lower-for-to-while"
    description = "Lower every eligible synchronous for loop to a while loop"

    def apply(self, source: str, context: Context) -> Result:
        del context  # Selection is exhaustive; source order determines helper names.
        initial_tree = ast.parse(source)
        initial_starts = offsets(source)
        original = [
            node for node in ast.walk(initial_tree) if isinstance(node, ast.For)
        ]
        initial_suite_starts, initial_comments = _syntax_metadata(
            source, initial_starts, original
        )
        reasons = [
            _reason(node, initial_starts, initial_suite_starts, initial_comments)
            for node in original
        ]
        async_count = sum(
            isinstance(node, ast.AsyncFor) for node in ast.walk(initial_tree)
        )
        used_names = {
            node.id for node in ast.walk(initial_tree) if isinstance(node, ast.Name)
        }
        current = source
        lowered = 0
        helper_index = 0
        while True:
            current_tree = ast.parse(current)
            starts = offsets(current)
            current_loops = [
                node for node in ast.walk(current_tree) if isinstance(node, ast.For)
            ]
            suite_starts, comments = _syntax_metadata(current, starts, current_loops)
            candidates = [
                candidate
                for node in current_loops
                if _reason(node, starts, suite_starts, comments) is None
                and (candidate := _candidate(node, starts, suite_starts)) is not None
            ]
            if not candidates:
                break
            innermost = [
                candidate
                for candidate in candidates
                if not any(
                    candidate.node is not other.node
                    and _contains(candidate.node, other.node)
                    for other in candidates
                )
            ]
            edits = []
            for candidate in sorted(
                innermost, key=lambda item: (item.node.lineno, item.node.col_offset)
            ):
                iterator_name, helper_index = _next_iterator_name(
                    used_names, helper_index
                )
                used_names.add(iterator_name)
                start, end = span(candidate.node, starts)
                edits.append(
                    (
                        start,
                        end,
                        _render(current, candidate, starts, iterator_name),
                    )
                )
            current = apply_edits(current, edits)
            lowered += len(edits)
        return Result(
            current,
            {
                "synchronous_for_loops_found": len(original),
                "synchronous_for_loops_eligible": sum(
                    reason is None for reason in reasons
                ),
                "for_loops_lowered_to_while": lowered,
                "for_loops_skipped_for_else": reasons.count("else"),
                "for_loops_skipped_for_comment": reasons.count("comment"),
                "for_loops_skipped_for_single_line_suite": reasons.count("single-line"),
                "async_for_loops_untouched": async_count,
                "iterator_helpers_generated": lowered,
            },
        )


def _reason(
    node: ast.For,
    starts: list[int],
    suite_starts: dict[int, int],
    comments: list[tuple[int, int]],
) -> str | None:
    if node.orelse:
        return "else"
    if not node.body or node.body[0].lineno == node.lineno:
        return "single-line"
    start, end = span(node, starts)
    if any(start <= comment_start < end for comment_start, _ in comments):
        return "comment"
    return None if start in suite_starts else "unsupported"


def _candidate(
    node: ast.For, starts: list[int], suite_starts: dict[int, int]
) -> _Candidate | None:
    suite_start = suite_starts.get(span(node, starts)[0])
    return _Candidate(node, suite_start) if suite_start is not None else None


def _syntax_metadata(
    source: str, starts: list[int], loops: list[ast.For]
) -> tuple[dict[int, int], list[tuple[int, int]]]:
    lines = source.splitlines(keepends=True)
    positioned = [
        (
            token,
            _token_offset(lines, starts, token.start),
            _token_offset(lines, starts, token.end),
        )
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
    ]
    comments = [
        (token_start, token_end)
        for token, token_start, token_end in positioned
        if token.type == tokenize.COMMENT
    ]
    targets = {span(node, starts)[0] for node in loops}
    suites: dict[int, int] = {}
    for index, (token, token_start, _) in enumerate(positioned):
        if (
            token.type != tokenize.NAME
            or token.string != "for"
            or token_start not in targets
        ):
            continue
        depth = 0
        colon_found = False
        for later, _, later_end in positioned[index + 1 :]:
            if later.type == tokenize.OP:
                if later.string in "([{":
                    depth += 1
                elif later.string in ")]}" and depth:
                    depth -= 1
                elif later.string == ":" and depth == 0:
                    colon_found = True
            if colon_found and later.type == tokenize.NEWLINE:
                suites[token_start] = later_end
                break
    return suites, comments


def _token_offset(
    lines: list[str], starts: list[int], position: tuple[int, int]
) -> int:
    line_number, column = position
    if line_number > len(lines):
        return starts[-1]
    line = lines[line_number - 1]
    return starts[line_number - 1] + len(line[:column].encode("utf-8"))


def _render(
    source: str,
    candidate: _Candidate,
    starts: list[int],
    iterator_name: str,
) -> str:
    node = candidate.node
    start, end = span(node, starts)
    target_start, target_end = span(node.target, starts)
    iterable_start, iterable_end = span(node.iter, starts)
    data = source.encode("utf-8")
    target = data[target_start:target_end].decode("utf-8")
    iterable = data[iterable_start:iterable_end].decode("utf-8")
    body = data[candidate.suite_start : end].decode("utf-8").rstrip()
    base_indent = _line_indent(source, start)
    body_indent = _line_indent(source, span(node.body[0], starts)[0])
    unit = (
        body_indent[len(base_indent) :]
        if body_indent.startswith(base_indent)
        else "    "
    )
    level_one = base_indent + unit
    level_two = level_one + unit
    return (
        f'{iterator_name} = __import__("builtins").iter({iterable})\n'
        f"{base_indent}while True:\n"
        f"{level_one}try:\n"
        f'{level_two}{target} = __import__("builtins").next({iterator_name})\n'
        f'{level_one}except __import__("builtins").StopIteration:\n'
        f"{level_two}break\n"
        f"{body}"
    )


def _line_indent(source: str, offset: int) -> str:
    data = source.encode("utf-8")
    line_start = data.rfind(b"\n", 0, offset) + 1
    prefix = data[line_start:offset].decode("utf-8")
    return prefix if not prefix.strip() else ""


def _contains(owner: ast.AST, child: ast.AST) -> bool:
    return any(node is child for node in ast.walk(owner))


def _next_iterator_name(used: set[str], index: int) -> tuple[str, int]:
    while True:
        suffix = "" if index == 0 else _letters(index - 1)
        candidate = f"loopIterator{suffix}"
        index += 1
        if candidate not in used:
            return candidate, index


def _letters(index: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = []
    while True:
        result.append(alphabet[index % len(alphabet)])
        index = index // len(alphabet) - 1
        if index < 0:
            return "".join(reversed(result))


PLUGINS = (LowerForToWhile(),)
