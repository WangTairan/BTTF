from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from tree_sitter import Node

from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    apply_edits,
    tree,
    walk,
)

_CALLABLES = {
    "compact_constructor_declaration",
    "constructor_declaration",
    "method_declaration",
}
_BLOCKS = {"block", "constructor_body"}
_JAVA_KEYWORDS = {
    "abstract",
    "assert",
    "boolean",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "class",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extends",
    "final",
    "finally",
    "float",
    "for",
    "goto",
    "if",
    "implements",
    "import",
    "instanceof",
    "int",
    "interface",
    "long",
    "native",
    "new",
    "package",
    "private",
    "protected",
    "public",
    "record",
    "return",
    "short",
    "static",
    "strictfp",
    "super",
    "switch",
    "synchronized",
    "this",
    "throw",
    "throws",
    "transient",
    "try",
    "var",
    "void",
    "volatile",
    "while",
    "yield",
    "true",
    "false",
    "null",
}


@dataclass(frozen=True)
class _Candidate:
    literal: Node
    statement: Node
    value: int
    long_suffix: bool


class IntroduceNumericIntermediates(Interference):
    """Split eligible integer literals through two short-named local constants."""

    category = "data-flow"
    slug = "introduce-numeric-intermediates"
    description = "Split eligible integer literals into pairs of short-named intermediate variables"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        del context  # This exhaustive transformation does not require random choices.
        root = tree(source).root_node
        used = {
            source[node.start_byte : node.end_byte].decode("utf-8")
            for node in walk(root)
            if node.type == "identifier"
        }
        candidates: list[_Candidate] = []
        for node in walk(root):
            if node.type != "decimal_integer_literal":
                continue
            raw = source[node.start_byte : node.end_byte].decode("utf-8")
            match = re.fullmatch(r"([0-9][0-9_]*)([lL]?)", raw)
            if not match:
                continue
            value = int(match.group(1).replace("_", ""))
            statement = _containing_statement(node)
            if statement is None or statement.type == "explicit_constructor_invocation":
                continue
            candidates.append(_Candidate(node, statement, value, bool(match.group(2))))

        grouped: dict[tuple[int, int], list[_Candidate]] = defaultdict(list)
        for candidate in candidates:
            grouped[
                (candidate.statement.start_byte, candidate.statement.end_byte)
            ].append(candidate)

        edits: list[tuple[int, int, bytes]] = []
        next_name = _short_name_source(used)
        for statement_key in sorted(grouped):
            statement_candidates = sorted(
                grouped[statement_key], key=lambda item: item.literal.start_byte
            )
            declarations: list[str] = []
            for candidate in statement_candidates:
                first_name = next(next_name)
                second_name = next(next_name)
                first_value, second_value = _split_value(candidate.value)
                suffix = "L" if candidate.long_suffix else ""
                type_name = "long" if candidate.long_suffix else "int"
                declarations.extend(
                    (
                        f"final {type_name} {first_name} = {first_value}{suffix};",
                        f"final {type_name} {second_name} = {second_value}{suffix};",
                    )
                )
                edits.append(
                    (
                        candidate.literal.start_byte,
                        candidate.literal.end_byte,
                        f"({first_name} + {second_name})".encode(),
                    )
                )
            statement = statement_candidates[0].statement
            edits.append(
                (
                    statement.start_byte,
                    statement.start_byte,
                    _render_declarations(source, statement.start_byte, declarations),
                )
            )

        return TransformResult(
            apply_edits(source, edits),
            {
                "integer_literals_split": len(candidates),
                "intermediate_variables_introduced": 2 * len(candidates),
                "statements_augmented": len(grouped),
            },
        )


def _containing_statement(node: Node) -> Node | None:
    current = node
    while current.parent is not None:
        parent = current.parent
        if parent.type in _CALLABLES:
            return None
        if parent.type in _BLOCKS:
            return current
        current = parent
    return None


def _split_value(value: int) -> tuple[int, int]:
    if value < 2:
        return value + 1, -1
    first = value // 2
    return first, value - first


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
        if candidate in used or candidate in _JAVA_KEYWORDS:
            continue
        used.add(candidate)
        yield candidate


def _render_declarations(
    source: bytes, statement_start: int, declarations: list[str]
) -> bytes:
    line_start = source.rfind(b"\n", 0, statement_start) + 1
    prefix = source[line_start:statement_start]
    encoded = [declaration.encode() for declaration in declarations]
    if prefix.strip():
        return b" ".join(encoded) + b" "
    separator = b"\n" + prefix
    return separator.join(encoded) + separator
