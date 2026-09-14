from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

from readability_data.java_degradation.interferences.core.base import (
    Interference,
    InterferenceContext,
    TransformResult,
)
from readability_data.java_degradation.interferences.core.java import (
    ancestor,
    apply_edits,
    tree,
    walk,
)

_CALLABLES = {
    "compact_constructor_declaration",
    "constructor_declaration",
    "method_declaration",
}
_SIMPLE_CONSUMERS = {
    "assert_statement",
    "expression_statement",
    "return_statement",
    "throw_statement",
    "yield_statement",
}
_DECLARATION_PARENTS = {
    "annotation_type_declaration",
    "catch_formal_parameter",
    "class_declaration",
    "compact_constructor_declaration",
    "constructor_declaration",
    "element_value_pair",
    "enum_declaration",
    "formal_parameter",
    "interface_declaration",
    "method_declaration",
    "record_declaration",
    "spread_parameter",
    "variable_declarator",
}


@dataclass(frozen=True)
class _Candidate:
    declaration: Node
    initializer: Node
    reference: Node
    name: str


class InlineIntermediateVariables(Interference):
    """Inline every conservatively identified single-use local variable."""

    category = "data-flow"
    slug = "inline-intermediate-variables"
    description = "Inline all eligible single-use intermediate local variables"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        candidates = _candidates(source)
        edits: list[tuple[int, int, bytes]] = []
        for candidate in candidates:
            expression = source[
                candidate.initializer.start_byte : candidate.initializer.end_byte
            ]
            edits.append(
                (
                    candidate.reference.start_byte,
                    candidate.reference.end_byte,
                    b"(" + expression + b")",
                )
            )
            edits.append(
                (candidate.declaration.start_byte, candidate.declaration.end_byte, b"")
            )
        return TransformResult(
            apply_edits(source, edits),
            {
                "intermediate_variables_available": len(candidates),
                "intermediate_variables_inlined": len(candidates),
                "identifier_references_replaced": len(candidates),
                "target_fraction_percent": 100,
            },
        )


def _candidates(source: bytes) -> list[_Candidate]:
    root = tree(source).root_node
    result: list[_Candidate] = []
    for declaration in walk(root):
        if declaration.type != "local_variable_declaration":
            continue
        block = declaration.parent
        if block is None or block.type != "block":
            continue
        declarators = [
            child
            for child in declaration.named_children
            if child.type == "variable_declarator"
        ]
        if len(declarators) != 1:
            continue
        declarator = declarators[0]
        name_node = declarator.child_by_field_name("name")
        initializer = declarator.child_by_field_name("value")
        if (
            name_node is None
            or name_node.type != "identifier"
            or initializer is None
            or initializer.type == "array_initializer"
        ):
            continue
        callable_node = ancestor(declaration, _CALLABLES)
        if callable_node is None:
            continue
        name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
        references = [
            node
            for node in walk(callable_node)
            if node.type == "identifier"
            and source[node.start_byte : node.end_byte].decode("utf-8") == name
            and _is_variable_reference(node)
        ]
        if len(references) != 1:
            continue
        reference = references[0]
        consumer = _direct_child(reference, block)
        if (
            consumer is None
            or consumer.start_byte <= declaration.end_byte
            or consumer.type not in _SIMPLE_CONSUMERS
        ):
            continue
        if not (
            consumer.start_byte
            <= reference.start_byte
            < reference.end_byte
            <= consumer.end_byte
        ):
            continue
        if _is_write(reference):
            continue
        result.append(_Candidate(declaration, initializer, reference, name))
    return result


def _direct_child(node: Node, parent: Node) -> Node | None:
    current = node
    while current.parent is not None and current.parent != parent:
        current = current.parent
    return current if current.parent == parent else None


def _is_variable_reference(node: Node) -> bool:
    parent = node.parent
    if parent is None:
        return False
    if parent.type == "scoped_identifier":
        return False
    if parent.type == "field_access" and parent.child_by_field_name("field") == node:
        return False
    if (
        parent.type
        in {
            "method_invocation",
            "method_reference",
            "super_method_invocation",
        }
        and parent.child_by_field_name("name") == node
    ):
        return False
    if (
        parent.type in _DECLARATION_PARENTS
        and parent.child_by_field_name("name") == node
    ):
        return False
    return True


def _is_write(node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type == "update_expression":
            return True
        if current.type == "assignment_expression":
            left = current.child_by_field_name("left")
            return bool(
                left
                and left.start_byte <= node.start_byte
                and node.end_byte <= left.end_byte
            )
        if current.type.endswith("_statement") or current.type == "block":
            return False
        current = current.parent
    return False
