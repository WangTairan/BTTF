from __future__ import annotations

import ast
import keyword
from dataclasses import dataclass

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
    offsets,
    span,
)

_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
_SIMPLE_CONSUMERS = (ast.Assert, ast.Expr, ast.Raise, ast.Return)
_REPEATED_SCOPES = (
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


@dataclass(frozen=True)
class _Candidate:
    declaration: ast.stmt
    initializer: ast.expr
    reference: ast.Name
    start: int


@dataclass(frozen=True)
class _NumericCandidate:
    literal: ast.Constant
    statement: ast.stmt
    value: int
    start: int


class IntroduceNumericIntermediates(Interference):
    """Split eligible integer literals through two short-named local variables."""

    category = "data-flow"
    slug = "introduce-numeric-intermediates"
    description = "Split eligible integer literals into pairs of short-named intermediate variables"

    def apply(self, source: str, context: Context) -> Result:
        del context
        tree = ast.parse(source)
        starts = offsets(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
            argument.arg
            for node in ast.walk(tree)
            if isinstance(node, _FUNCTIONS)
            for argument in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
                *([node.args.vararg] if node.args.vararg else []),
                *([node.args.kwarg] if node.args.kwarg else []),
            )
        }
        candidates: list[_NumericCandidate] = []
        for node in ast.walk(tree):
            if (
                not isinstance(node, ast.Constant)
                or not isinstance(node.value, int)
                or isinstance(node.value, bool)
                or _inside_pattern(node, parents)
            ):
                continue
            start, end = span(node, starts)
            raw = source.encode()[start:end].decode("utf-8")
            if not raw.replace("_", "").isdigit():
                continue
            statement = _containing_suite_statement(node, parents)
            if statement is None or _nearest_function(statement, parents) is None:
                continue
            statement = _outermost_elif_statement(source, statement, parents)
            candidates.append(_NumericCandidate(node, statement, node.value, start))

        grouped: dict[ast.stmt, list[_NumericCandidate]] = {}
        for candidate in candidates:
            grouped.setdefault(candidate.statement, []).append(candidate)
        edits: list[tuple[int, int, str]] = []
        names = _short_name_source(used)
        for statement in sorted(grouped, key=lambda item: span(item, starts)[0]):
            declarations: list[str] = []
            for candidate in sorted(grouped[statement], key=lambda item: item.start):
                first_name = next(names)
                second_name = next(names)
                first_value, second_value = _split_numeric_value(candidate.value)
                declarations.extend(
                    (f"{first_name} = {first_value}", f"{second_name} = {second_value}")
                )
                literal_start, literal_end = span(candidate.literal, starts)
                edits.append(
                    (literal_start, literal_end, f"({first_name} + {second_name})")
                )
            statement_start = span(statement, starts)[0]
            edits.append(
                (
                    statement_start,
                    statement_start,
                    _render_numeric_declarations(source, statement, declarations),
                )
            )
        return Result(
            apply_edits(source, edits),
            {
                "integer_literals_split": len(candidates),
                "intermediate_variables_introduced": 2 * len(candidates),
                "statements_augmented": len(grouped),
            },
        )


class InlineIntermediateVariables(Interference):
    """Inline every conservatively identified single-use local variable."""

    category = "data-flow"
    slug = "inline-intermediate-variables"
    description = "Inline all eligible single-use intermediate local variables"

    def apply(self, source: str, context: Context) -> Result:
        tree = ast.parse(source)
        starts = offsets(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        candidates = _candidates(source, tree, starts, parents)
        edits: list[tuple[int, int, str]] = []
        for candidate in candidates:
            declaration_start, declaration_end = span(candidate.declaration, starts)
            initializer_start, initializer_end = span(candidate.initializer, starts)
            reference_start, reference_end = span(candidate.reference, starts)
            initializer = source.encode()[initializer_start:initializer_end].decode()
            edits.append((reference_start, reference_end, f"({initializer})"))
            edits.append((declaration_start, declaration_end, ""))
        return Result(
            apply_edits(source, edits),
            {
                "intermediate_variables_available": len(candidates),
                "intermediate_variables_inlined": len(candidates),
                "identifier_references_replaced": len(candidates),
                "target_fraction_percent": 100,
            },
        )


def _candidates(
    source: str,
    tree: ast.AST,
    starts: list[int],
    parents: dict[ast.AST, ast.AST],
) -> list[_Candidate]:
    result: list[_Candidate] = []
    for declaration in ast.walk(tree):
        target: ast.Name | None = None
        initializer: ast.expr | None = None
        if (
            isinstance(declaration, ast.Assign)
            and len(declaration.targets) == 1
            and isinstance(declaration.targets[0], ast.Name)
        ):
            target, initializer = declaration.targets[0], declaration.value
        elif (
            isinstance(declaration, ast.AnnAssign)
            and isinstance(declaration.target, ast.Name)
            and declaration.value is not None
        ):
            target, initializer = declaration.target, declaration.value
        if target is None or initializer is None:
            continue
        function = _nearest_function(declaration, parents)
        if function is None:
            continue
        if not _occupies_clean_lines(source, declaration):
            continue
        parameters = {
            argument.arg
            for argument in [
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
                *([function.args.vararg] if function.args.vararg else []),
                *([function.args.kwarg] if function.args.kwarg else []),
            ]
        }
        if target.id in parameters:
            continue
        stores = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, (ast.Store, ast.Del))
            and node.id == target.id
            and _nearest_function(node, parents) is function
        ]
        loads = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id == target.id
            and _nearest_function(node, parents) is function
            and not _inside_repeated_scope(node, function, parents)
        ]
        if len(stores) != 1 or len(loads) != 1:
            continue
        reference = loads[0]
        consumer = _consumer_in_same_suite(declaration, reference, parents)
        if consumer is None or not isinstance(consumer, _SIMPLE_CONSUMERS):
            continue
        if not _contains(consumer, reference) or _inside_f_string(reference, parents):
            continue
        declaration_start = span(declaration, starts)[0]
        result.append(
            _Candidate(declaration, initializer, reference, declaration_start)
        )
    return result


def _nearest_function(node: ast.AST, parents: dict[ast.AST, ast.AST]):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, _FUNCTIONS):
            return current
        if isinstance(current, (ast.Lambda, ast.ClassDef)):
            return None
    return None


def _consumer_in_same_suite(
    statement: ast.stmt,
    reference: ast.Name,
    parents: dict[ast.AST, ast.AST],
) -> ast.stmt | None:
    parent = parents.get(statement)
    if parent is None:
        return None
    for _, value in ast.iter_fields(parent):
        if not isinstance(value, list) or statement not in value:
            continue
        index = value.index(statement)
        current: ast.AST = reference
        while current in parents and parents[current] is not parent:
            current = parents[current]
        if current not in value:
            return None
        consumer_index = value.index(current)
        if consumer_index > index and isinstance(current, ast.stmt):
            return current
        return None
    return None


def _contains(owner: ast.AST, child: ast.AST) -> bool:
    return any(node is child for node in ast.walk(owner))


def _inside_repeated_scope(
    node: ast.AST,
    function: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    current = node
    while current in parents and current is not function:
        current = parents[current]
        if isinstance(current, _REPEATED_SCOPES):
            return True
    return False


def _inside_f_string(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.JoinedStr):
            return True
        if isinstance(current, ast.stmt):
            return False
    return False


def _occupies_clean_lines(source: str, statement: ast.stmt) -> bool:
    lines = source.splitlines()
    first = lines[statement.lineno - 1]
    last = lines[statement.end_lineno - 1]
    return (
        not first[: statement.col_offset].strip()
        and not last[statement.end_col_offset :].strip()
    )


def _inside_pattern(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    pattern_types = tuple(
        item
        for name in ("MatchValue", "MatchSingleton")
        if (item := getattr(ast, name, None)) is not None
    )
    current = node
    while current in parents:
        current = parents[current]
        if pattern_types and isinstance(current, pattern_types):
            return True
    return False


def _split_numeric_value(value: int) -> tuple[int, int]:
    if value < 2:
        return value + 1, -1
    first = value // 2
    return first, value - first


def _containing_suite_statement(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> ast.stmt | None:
    current = node
    while current in parents:
        current = parents[current]
        if not isinstance(current, ast.stmt):
            continue
        parent = parents.get(current)
        if parent is None:
            return None
        if any(
            isinstance(value, list) and current in value
            for _, value in ast.iter_fields(parent)
        ):
            return current
    return None


def _short_name_source(used: set[str]):
    index = 0
    while True:
        number = index
        characters = []
        while True:
            characters.append(chr(ord("a") + number % 26))
            number = number // 26 - 1
            if number < 0:
                break
        candidate = "".join(reversed(characters))
        index += 1
        if candidate in used or keyword.iskeyword(candidate):
            continue
        used.add(candidate)
        yield candidate


def _outermost_elif_statement(
    source: str, statement: ast.stmt, parents: dict[ast.AST, ast.AST]
) -> ast.stmt:
    lines = source.splitlines()
    current = statement
    while isinstance(current, ast.If):
        tail = lines[current.lineno - 1][current.col_offset :]
        parent = parents.get(current)
        if not tail.startswith("elif ") or not isinstance(parent, ast.If):
            break
        current = parent
    return current


def _render_numeric_declarations(
    source: str, statement: ast.stmt, declarations: list[str]
) -> str:
    lines = source.splitlines(keepends=True)
    prefix = lines[statement.lineno - 1][: statement.col_offset]
    if prefix.strip():
        return "; ".join(declarations) + "; "
    separator = "\n" + prefix
    return separator.join(declarations) + separator


PLUGINS = (IntroduceNumericIntermediates(), InlineIntermediateVariables())
