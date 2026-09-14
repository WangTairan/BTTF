from __future__ import annotations

import textwrap
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

_LOOPS = {
    "do_statement",
    "enhanced_for_statement",
    "for_statement",
    "while_statement",
}


@dataclass(frozen=True)
class _ForParts:
    node: Node
    initializers: tuple[Node, ...]
    condition: Node | None
    updates: tuple[Node, ...]
    body: Node


@dataclass(frozen=True)
class _EnhancedForParts:
    node: Node
    declaration: str
    element_type: str
    value: str
    body: Node
    source_kind: str


_ITERABLE_METHODS = {
    "entrySet",
    "getAll",
    "keySet",
    "names",
    "socketWithFastOpen",
    "values",
}

_ARRAY_METHODS = {"getInterfaces", "getKeyParameters"}


class LowerForToWhile(Interference):
    """Lower eligible classic and enhanced Java for loops to while loops."""

    category = "control-flow"
    slug = "lower-for-to-while"
    description = "Lower every eligible classic and enhanced for loop to a while loop"

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        del context  # Selection and fresh-name allocation are source-deterministic.
        original_root = tree(source).root_node
        original_nodes = [
            node for node in walk(original_root) if node.type == "for_statement"
        ]
        reasons = [_reason(source, node) for node in original_nodes]
        eligible = sum(reason is None for reason in reasons)
        enhanced_nodes = [
            node
            for node in walk(original_root)
            if node.type == "enhanced_for_statement"
        ]
        enhanced_reasons = [_enhanced_reason(source, node) for node in enhanced_nodes]
        enhanced_eligible = sum(reason is None for reason in enhanced_reasons)
        current = source
        classic_lowered = 0
        while True:
            candidates = [
                parts
                for node in walk(tree(current).root_node)
                if node.type == "for_statement"
                and _reason(current, node) is None
                and (parts := _parts(node)) is not None
            ]
            if not candidates:
                break
            innermost = [
                candidate
                for candidate in candidates
                if not any(
                    candidate.node.start_byte < other.node.start_byte
                    and other.node.end_byte < candidate.node.end_byte
                    for other in candidates
                )
            ]
            edits = [
                (
                    candidate.node.start_byte,
                    candidate.node.end_byte,
                    _render(current, candidate),
                )
                for candidate in innermost
            ]
            current = apply_edits(current, edits)
            classic_lowered += len(edits)
        used_names = {
            current[node.start_byte : node.end_byte].decode("utf-8")
            for node in walk(tree(current).root_node)
            if node.type == "identifier"
        }
        enhanced_lowered = 0
        arrays_lowered = 0
        iterables_lowered = 0
        while True:
            current_root = tree(current).root_node
            candidates = [
                parts
                for node in walk(current_root)
                if node.type == "enhanced_for_statement"
                and _enhanced_reason(current, node) is None
                and (parts := _enhanced_parts(current, node)) is not None
            ]
            if not candidates:
                break
            innermost = [
                candidate
                for candidate in candidates
                if not any(
                    candidate.node.start_byte < other.node.start_byte
                    and other.node.end_byte < candidate.node.end_byte
                    for other in candidates
                )
            ]
            edits = []
            for candidate in sorted(innermost, key=lambda item: item.node.start_byte):
                if candidate.source_kind == "array":
                    source_name = _fresh_name(used_names, "loopArray")
                    used_names.add(source_name)
                    position_name = _fresh_name(used_names, "loopIndex")
                    used_names.add(position_name)
                    helper_names = (source_name, position_name)
                    arrays_lowered += 1
                else:
                    iterator_name = _fresh_name(used_names, "loopIterator")
                    used_names.add(iterator_name)
                    helper_names = (iterator_name,)
                    iterables_lowered += 1
                edits.append(
                    (
                        candidate.node.start_byte,
                        candidate.node.end_byte,
                        _render_enhanced(current, candidate, helper_names),
                    )
                )
            current = apply_edits(current, edits)
            enhanced_lowered += len(edits)
        return TransformResult(
            current,
            {
                "classic_for_loops_found": len(original_nodes),
                "classic_for_loops_eligible": eligible,
                "classic_for_loops_lowered_to_while": classic_lowered,
                "enhanced_for_loops_found": len(enhanced_nodes),
                "enhanced_for_loops_eligible": enhanced_eligible,
                "enhanced_for_loops_lowered_to_while": enhanced_lowered,
                "enhanced_array_loops_lowered": arrays_lowered,
                "enhanced_iterable_loops_lowered": iterables_lowered,
                "for_loops_lowered_to_while": classic_lowered + enhanced_lowered,
                "for_loops_skipped_for_continue": reasons.count("continue"),
                "for_loops_skipped_for_label": reasons.count("label"),
                "for_loops_skipped_for_header_comment": reasons.count("header-comment"),
                "enhanced_for_loops_skipped_for_label": enhanced_reasons.count("label"),
                "enhanced_for_loops_skipped_for_header_comment": (
                    enhanced_reasons.count("header-comment")
                ),
                "enhanced_for_loops_skipped_unknown_source_type": (
                    enhanced_reasons.count("unknown-source-type")
                ),
                "enhanced_for_loops_untouched": (
                    len(enhanced_nodes) - enhanced_lowered
                ),
            },
        )


def _reason(source: bytes, node: Node) -> str | None:
    parts = _parts(node)
    if parts is None:
        return "unsupported"
    if node.parent is not None and node.parent.type == "labeled_statement":
        return "label"
    header = source[node.start_byte : parts.body.start_byte]
    if b"//" in header or b"/*" in header:
        return "header-comment"
    if parts.updates and _has_targeted_continue(parts.body, node):
        return "continue"
    return None


def _parts(node: Node) -> _ForParts | None:
    body = node.child_by_field_name("body")
    if body is None:
        return None
    initializer = node.child_by_field_name("init")
    condition = node.child_by_field_name("condition")
    direct_semicolons = [child for child in node.children if child.type == ";"]
    if not direct_semicolons:
        return None
    if initializer is None:
        initializers: tuple[Node, ...] = ()
    elif initializer.type == "local_variable_declaration":
        initializers = (initializer,)
    else:
        first_semicolon = direct_semicolons[0]
        initializers = tuple(
            child
            for child in node.named_children
            if initializer.start_byte <= child.start_byte
            and child.end_byte <= first_semicolon.start_byte
        )
    update_start = direct_semicolons[-1].end_byte
    updates = tuple(
        child
        for child in node.named_children
        if update_start <= child.start_byte and child.end_byte <= body.start_byte
    )
    return _ForParts(node, initializers, condition, updates, body)


def _enhanced_reason(source: bytes, node: Node) -> str | None:
    body = node.child_by_field_name("body")
    element_type = node.child_by_field_name("type")
    value = node.child_by_field_name("value")
    name = node.child_by_field_name("name")
    if body is None or element_type is None or value is None or name is None:
        return "unknown-source-type"
    if source[element_type.start_byte : element_type.end_byte].strip() == b"var":
        return "unknown-source-type"
    if node.parent is not None and node.parent.type == "labeled_statement":
        return "label"
    header = source[node.start_byte : body.start_byte]
    if b"//" in header or b"/*" in header:
        return "header-comment"
    kind = _enhanced_source_kind(source, node, value, element_type)
    return None if kind is not None else "unknown-source-type"


def _enhanced_parts(source: bytes, node: Node) -> _EnhancedForParts | None:
    body = node.child_by_field_name("body")
    element_type = node.child_by_field_name("type")
    value = node.child_by_field_name("value")
    name = node.child_by_field_name("name")
    if body is None or element_type is None or value is None or name is None:
        return None
    source_kind = _enhanced_source_kind(source, node, value, element_type)
    if source_kind is None:
        return None
    first_declaration_part = next(
        (child for child in node.named_children if child.end_byte <= name.end_byte),
        element_type,
    )
    declaration = source[first_declaration_part.start_byte : name.end_byte].decode(
        "utf-8"
    )
    return _EnhancedForParts(
        node=node,
        declaration=declaration.strip(),
        element_type=source[element_type.start_byte : element_type.end_byte].decode(
            "utf-8"
        ),
        value=source[value.start_byte : value.end_byte].decode("utf-8").strip(),
        body=body,
        source_kind=source_kind,
    )


def _enhanced_source_kind(
    source: bytes,
    loop: Node,
    value: Node,
    element_type: Node,
) -> str | None:
    value_text = source[value.start_byte : value.end_byte].decode("utf-8").strip()
    if value.type in {"array_creation_expression", "array_initializer"}:
        return "array"
    if value.type == "identifier":
        return (
            "array"
            if _binding_is_array(source, loop, value_text) is True
            else "iterable"
        )
    if value.type == "this":
        return "iterable"
    if value.type == "field_access":
        field_name = next(
            (
                source[child.start_byte : child.end_byte].decode("utf-8")
                for child in reversed(value.named_children)
                if child.type == "identifier"
            ),
            "",
        )
        return (
            "array"
            if _binding_is_array(source, loop, field_name) is True
            else "iterable"
        )
    if value.type != "method_invocation":
        return None
    method_node = value.child_by_field_name("name")
    if method_node is None:
        return None
    method_name = source[method_node.start_byte : method_node.end_byte].decode("utf-8")
    local_kind = _local_method_source_kind(source, loop, value, method_name)
    if local_kind is not None:
        return local_kind
    if method_name in _ARRAY_METHODS:
        return "array"
    if method_name == "values":
        receiver = value.child_by_field_name("object")
        if receiver is None and _inside_enum(loop):
            return "array"
        element_text = source[element_type.start_byte : element_type.end_byte].decode(
            "utf-8"
        )
        qualifier = value_text[: -len(".values()")]
        if qualifier and qualifier.rsplit(".", 1)[-1] == element_text:
            return "array"
    return "iterable" if method_name in _ITERABLE_METHODS else None


def _local_method_source_kind(
    source: bytes, loop: Node, invocation: Node, method_name: str
) -> str | None:
    receiver = invocation.child_by_field_name("object")
    if receiver is not None:
        receiver_text = source[receiver.start_byte : receiver.end_byte].decode("utf-8")
        if receiver_text != "this":
            return None
    type_node = _ancestor(
        loop,
        {
            "annotation_type_declaration",
            "class_declaration",
            "enum_declaration",
            "interface_declaration",
            "record_declaration",
        },
    )
    body = type_node.child_by_field_name("body") if type_node is not None else None
    if body is None:
        return None
    kinds = set()
    for declaration in body.named_children:
        if declaration.type != "method_declaration":
            continue
        name = declaration.child_by_field_name("name")
        return_type = declaration.child_by_field_name("type")
        if name is None or return_type is None:
            continue
        declared_name = source[name.start_byte : name.end_byte].decode("utf-8")
        if declared_name == method_name:
            kinds.add("array" if return_type.type == "array_type" else "iterable")
    return kinds.pop() if len(kinds) == 1 else None


def _inside_enum(node: Node) -> bool:
    current = node.parent
    while current is not None:
        if current.type == "enum_declaration":
            return True
        current = current.parent
    return False


def _binding_is_array(source: bytes, loop: Node, name: str) -> bool | None:
    callable_node = _ancestor(
        loop,
        {
            "compact_constructor_declaration",
            "constructor_declaration",
            "method_declaration",
        },
    )
    if callable_node is not None:
        declarations = [
            node
            for node in walk(callable_node)
            if node.start_byte < loop.start_byte
            and node.type
            in {
                "formal_parameter",
                "local_variable_declaration",
                "resource",
                "spread_parameter",
            }
            and name in _declared_names(source, node)
        ]
        if declarations:
            nearest = max(declarations, key=lambda node: node.start_byte)
            return _declaration_is_array(nearest)
    type_node = _ancestor(
        loop,
        {
            "annotation_type_declaration",
            "class_declaration",
            "enum_declaration",
            "interface_declaration",
            "record_declaration",
        },
    )
    body = type_node.child_by_field_name("body") if type_node is not None else None
    if body is not None:
        for declaration in body.named_children:
            if declaration.type == "field_declaration" and name in _declared_names(
                source, declaration
            ):
                return _declaration_is_array(declaration)
    return None


def _declared_names(source: bytes, declaration: Node) -> set[str]:
    result = set()
    direct_name = declaration.child_by_field_name("name")
    if direct_name is not None:
        result.add(
            source[direct_name.start_byte : direct_name.end_byte].decode("utf-8")
        )
    for child in declaration.named_children:
        if child.type != "variable_declarator":
            continue
        name = child.child_by_field_name("name")
        if name is not None:
            result.add(source[name.start_byte : name.end_byte].decode("utf-8"))
    return result


def _declaration_is_array(declaration: Node) -> bool:
    if declaration.type == "spread_parameter":
        return True
    declared_type = declaration.child_by_field_name("type")
    if declared_type is not None and declared_type.type == "array_type":
        return True
    for declarator in declaration.named_children:
        if declarator.type != "variable_declarator":
            continue
        if any(child.type == "dimensions" for child in declarator.named_children):
            return True
    return False


def _ancestor(node: Node, types: set[str]) -> Node | None:
    current = node.parent
    while current is not None:
        if current.type in types:
            return current
        current = current.parent
    return None


def _has_targeted_continue(body: Node, loop: Node) -> bool:
    for node in walk(body):
        if node.type != "continue_statement":
            continue
        if node.named_children:
            return True
        current = node.parent
        while current is not None and current.type not in _LOOPS:
            current = current.parent
        if current == loop:
            return True
    return False


def _render(source: bytes, parts: _ForParts) -> bytes:
    base_indent = _line_indent(source, parts.node.start_byte)
    inner_indent = base_indent + "  "
    body_indent = base_indent + "    "
    initializers = [_statement_text(source, node) for node in parts.initializers]
    updates = [_statement_text(source, node) for node in parts.updates]
    condition = (
        source[parts.condition.start_byte : parts.condition.end_byte]
        .decode("utf-8")
        .strip()
        if parts.condition is not None
        else "true"
    )
    lines = ["{"]
    lines.extend(f"{inner_indent}{statement}" for statement in initializers)
    lines.append(f"{inner_indent}while ({condition}) {{")
    body = _body_text(source, parts.body)
    if body:
        lines.extend(
            f"{body_indent}{line}" if line else "" for line in body.splitlines()
        )
    lines.extend(f"{body_indent}{statement}" for statement in updates)
    lines.append(f"{inner_indent}}}")
    lines.append(f"{base_indent}}}")
    return "\n".join(lines).encode("utf-8")


def _render_enhanced(
    source: bytes,
    parts: _EnhancedForParts,
    helper_names: tuple[str, ...],
) -> bytes:
    base_indent = _line_indent(source, parts.node.start_byte)
    inner_indent = base_indent + "  "
    body_indent = base_indent + "    "
    lines = ["{"]
    if parts.source_kind == "array":
        array_name, index_name = helper_names
        lines.extend(
            (
                f"{inner_indent}{parts.element_type}[] {array_name} = {parts.value};",
                f"{inner_indent}int {index_name} = 0;",
                f"{inner_indent}while ({index_name} < {array_name}.length) {{",
                (f"{body_indent}{parts.declaration} = {array_name}[{index_name}++];"),
            )
        )
    else:
        (iterator_name,) = helper_names
        lines.extend(
            (
                (
                    f"{inner_indent}java.util.Iterator<?> {iterator_name} = "
                    f"({parts.value}).iterator();"
                ),
                f"{inner_indent}while ({iterator_name}.hasNext()) {{",
                (
                    f"{body_indent}{parts.declaration} = "
                    f"{_iterator_value(parts.element_type, iterator_name)};"
                ),
            )
        )
    body = _body_text(source, parts.body)
    if body:
        lines.extend(
            f"{body_indent}{line}" if line else "" for line in body.splitlines()
        )
    lines.append(f"{inner_indent}}}")
    lines.append(f"{base_indent}}}")
    return "\n".join(lines).encode("utf-8")


def _iterator_value(element_type: str, iterator_name: str) -> str:
    numeric_accessors = {
        "byte": "byteValue",
        "double": "doubleValue",
        "float": "floatValue",
        "int": "intValue",
        "long": "longValue",
        "short": "shortValue",
    }
    if element_type in numeric_accessors:
        accessor = numeric_accessors[element_type]
        return f"((java.lang.Number) {iterator_name}.next()).{accessor}()"
    if element_type == "boolean":
        return f"((java.lang.Boolean) {iterator_name}.next()).booleanValue()"
    if element_type == "char":
        return f"((java.lang.Character) {iterator_name}.next()).charValue()"
    return f"({element_type}) {iterator_name}.next()"


def _fresh_name(used: set[str], base: str) -> str:
    index = 0
    while True:
        suffix = "" if index == 0 else _letters(index - 1)
        candidate = base + suffix
        if candidate not in used:
            return candidate
        index += 1


def _letters(index: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = []
    while True:
        result.append(alphabet[index % len(alphabet)])
        index = index // len(alphabet) - 1
        if index < 0:
            return "".join(reversed(result))


def _statement_text(source: bytes, node: Node) -> str:
    text = source[node.start_byte : node.end_byte].decode("utf-8").strip()
    return text if text.endswith(";") else f"{text};"


def _body_text(source: bytes, body: Node) -> str:
    if body.type == "block":
        raw = source[body.start_byte + 1 : body.end_byte - 1]
    else:
        raw = source[body.start_byte : body.end_byte]
    return textwrap.dedent(raw.decode("utf-8")).strip()


def _line_indent(source: bytes, offset: int) -> str:
    line_start = source.rfind(b"\n", 0, offset) + 1
    prefix = source[line_start:offset]
    return prefix.decode("utf-8") if not prefix.strip() else ""
