from __future__ import annotations

import re
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
from readability_data.shared.meaningful_names import (
    LOCAL_MEANINGFUL_NAMES,
    METHOD_MEANINGFUL_NAMES,
    choose_misleading_name,
)

_CALLABLE_NODES = {
    "compact_constructor_declaration",
    "constructor_declaration",
    "method_declaration",
}
_PARAMETER_NODES = {
    "catch_formal_parameter",
    "formal_parameter",
    "spread_parameter",
}
_REFERENCE_NAME_PARENTS = {
    "annotation_type_declaration",
    "break_statement",
    "class_declaration",
    "constructor_declaration",
    "continue_statement",
    "element_value_pair",
    "enum_declaration",
    "field_access",
    "interface_declaration",
    "labeled_statement",
    "method_declaration",
    "method_invocation",
    "method_reference",
    "record_declaration",
    "super_method_invocation",
}
_TYPE_DECLARATIONS = {
    "annotation_type_declaration",
    "class_declaration",
    "enum_declaration",
    "interface_declaration",
    "record_declaration",
}
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
    "void",
    "volatile",
    "while",
    "yield",
    "true",
    "false",
    "null",
}


@dataclass(frozen=True)
class _Binding:
    original: str
    replacement: str
    declaration_start: int
    declaration_end: int
    scope_start: int
    scope_end: int


@dataclass(frozen=True)
class _MethodBinding:
    original: str
    replacement: str
    declaration_start: int
    scope_start: int
    scope_end: int
    type_name: str


class RenameIdentifiers(Interference):
    category = "identifiers"

    def __init__(self, mode: str) -> None:
        if mode not in {"short", "misleading", "garbled"}:
            raise ValueError(f"unknown identifier naming mode: {mode}")
        self.mode = mode
        self.slug = {
            "short": "shorten-identifiers",
            "misleading": "mislead-identifiers",
            "garbled": "garble-identifiers",
        }[mode]
        self.description = {
            "short": "Shorten method, parameter, and local names without collisions",
            "misleading": (
                "Replace method, parameter, and local names with length-matched, "
                "meaningful but unrelated names"
            ),
            "garbled": (
                "Replace method, parameter, and local names with deterministic "
                "ProGuard-style short identifiers"
            ),
        }[mode]

    def apply(self, source: bytes, context: InterferenceContext) -> TransformResult:
        locals_result = _rename_locals(source, context, self.mode)
        methods_result = _rename_methods(locals_result.content, context, self.mode)
        return TransformResult(
            methods_result.content,
            {**locals_result.stats, **methods_result.stats},
        )


def _rename_locals(
    source: bytes, context: InterferenceContext, mode: str
) -> TransformResult:
    root = tree(source).root_node
    existing = {
        source[node.start_byte : node.end_byte].decode("utf-8")
        for node in walk(root)
        if node.type == "identifier"
    }
    bindings: list[_Binding] = []
    used = set(existing)
    misleading_metrics = {
        "collision_candidates_skipped": 0,
        "alphabetic_fallbacks_used": 0,
    }
    declaration_nodes: set[tuple[int, int]] = set()
    for node in walk(root):
        name_node: Node | None = None
        scope: Node | None = None
        scope_start: int | None = None
        if node.type in _PARAMETER_NODES:
            name_node = node.child_by_field_name("name")
            scope = _parameter_scope(node)
            scope_start = scope.start_byte if scope else None
        elif node.type == "variable_declarator" and _nearest_callable(node) is not None:
            name_node = node.child_by_field_name("name")
            scope = _local_scope(node)
            scope_start = name_node.end_byte if name_node else None
        elif node.type == "enhanced_for_statement":
            name_node = node.child_by_field_name("name")
            scope = node.child_by_field_name("body")
            scope_start = scope.start_byte if scope else None
        elif node.type == "inferred_parameters":
            scope = ancestor(node, {"lambda_expression"})
            if scope is None:
                continue
            for identifier in [
                child for child in node.named_children if child.type == "identifier"
            ]:
                bindings.append(
                    _make_binding(
                        source,
                        identifier,
                        scope,
                        scope.start_byte,
                        context,
                        used,
                        mode,
                        misleading_metrics,
                    )
                )
                declaration_nodes.add((identifier.start_byte, identifier.end_byte))
            continue
        if name_node is None or scope is None or scope_start is None:
            continue
        if name_node.type != "identifier":
            continue
        bindings.append(
            _make_binding(
                source,
                name_node,
                scope,
                scope_start,
                context,
                used,
                mode,
                misleading_metrics,
            )
        )
        declaration_nodes.add((name_node.start_byte, name_node.end_byte))

    edits: dict[tuple[int, int], bytes] = {}
    for binding in bindings:
        edits[(binding.declaration_start, binding.declaration_end)] = (
            binding.replacement.encode()
        )
    references_renamed = 0
    for node in walk(root):
        if node.type != "identifier":
            continue
        key = (node.start_byte, node.end_byte)
        if key in declaration_nodes or not _is_reference_identifier(node):
            continue
        name = source[node.start_byte : node.end_byte].decode("utf-8")
        eligible = [
            binding
            for binding in bindings
            if binding.original == name
            and binding.scope_start <= node.start_byte < binding.scope_end
        ]
        if not eligible:
            continue
        binding = min(
            eligible,
            key=lambda item: (item.scope_end - item.scope_start, -item.scope_start),
        )
        edits[key] = binding.replacement.encode()
        references_renamed += 1
    stats: dict[str, int] = {
        "identifiers_declared": len(bindings),
        "identifier_references_renamed": references_renamed,
    }
    if mode == "short":
        stats["local_name_collisions_avoided"] = sum(
            binding.replacement != _short_name(binding.original) for binding in bindings
        )
    elif mode == "misleading":
        stats.update(
            {
                "local_candidate_pool_size": len(LOCAL_MEANINGFUL_NAMES),
                "local_random_pool_selections": len(bindings)
                - misleading_metrics["alphabetic_fallbacks_used"],
                "local_collision_candidates_skipped": misleading_metrics[
                    "collision_candidates_skipped"
                ],
                "local_alphabetic_fallbacks_used": misleading_metrics[
                    "alphabetic_fallbacks_used"
                ],
                "local_exact_length_matches": sum(
                    len(binding.replacement) == len(binding.original)
                    for binding in bindings
                ),
                "local_total_length_difference": sum(
                    abs(len(binding.replacement) - len(binding.original))
                    for binding in bindings
                ),
            }
        )
    else:
        stats["local_name_collisions_avoided"] = 0
    return TransformResult(
        apply_edits(
            source,
            [(start, end, value) for (start, end), value in edits.items()],
        ),
        stats,
    )


def _rename_methods(
    source: bytes, context: InterferenceContext, mode: str
) -> TransformResult:
    root = tree(source).root_node
    groups: dict[tuple[int, int, str], list[Node]] = {}
    type_names: dict[tuple[int, int], str] = {}
    method_names_by_type: dict[tuple[int, int], set[str]] = {}
    for node in walk(root):
        if node.type != "method_declaration":
            continue
        name_node = node.child_by_field_name("name")
        type_node = ancestor(node, _TYPE_DECLARATIONS)
        if name_node is None or type_node is None:
            continue
        type_key = (type_node.start_byte, type_node.end_byte)
        original = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
        groups.setdefault((*type_key, original), []).append(name_node)
        method_names_by_type.setdefault(type_key, set()).add(original)
        type_name_node = type_node.child_by_field_name("name")
        type_names[type_key] = (
            source[type_name_node.start_byte : type_name_node.end_byte].decode("utf-8")
            if type_name_node is not None
            else ""
        )

    used_by_type = {
        type_key: set(names) for type_key, names in method_names_by_type.items()
    }
    bindings: list[_MethodBinding] = []
    edits: dict[tuple[int, int], bytes] = {}
    declarations_renamed = 0
    misleading_metrics = {
        "collision_candidates_skipped": 0,
        "alphabetic_fallbacks_used": 0,
    }
    for (scope_start, scope_end, original), name_nodes in sorted(
        groups.items(), key=lambda item: item[1][0].start_byte
    ):
        if original in context.protected_names:
            continue
        type_key = (scope_start, scope_end)
        used = used_by_type[type_key]
        used.discard(original)
        first = name_nodes[0]
        replacement = _replacement_name(
            original,
            context,
            first.start_byte,
            used,
            mode,
            identity_suffix=f":method:{scope_start}",
            misleading_metrics=misleading_metrics,
        )
        bindings.append(
            _MethodBinding(
                original,
                replacement,
                first.start_byte,
                scope_start,
                scope_end,
                type_names[type_key],
            )
        )
        for name_node in name_nodes:
            edits[(name_node.start_byte, name_node.end_byte)] = replacement.encode()
            if replacement != original:
                declarations_renamed += 1

    calls_renamed = 0
    for node in walk(root):
        if node.type not in {"method_invocation", "method_reference"}:
            continue
        name_node = node.child_by_field_name("name")
        type_node = ancestor(node, _TYPE_DECLARATIONS)
        if name_node is None or type_node is None:
            continue
        name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
        binding = next(
            (
                item
                for item in bindings
                if item.original == name
                and item.scope_start == type_node.start_byte
                and item.scope_end == type_node.end_byte
            ),
            None,
        )
        if binding is None:
            continue
        object_node = node.child_by_field_name("object")
        if object_node is not None:
            qualifier = source[object_node.start_byte : object_node.end_byte].decode(
                "utf-8"
            )
            if qualifier not in {"this", binding.type_name}:
                continue
        edits[(name_node.start_byte, name_node.end_byte)] = binding.replacement.encode()
        if binding.replacement != name:
            calls_renamed += 1
    stats: dict[str, int] = {
        "method_declarations_renamed": declarations_renamed,
        "method_calls_renamed": calls_renamed,
        "method_name_groups": len(bindings),
    }
    if mode == "short":
        stats["method_name_collisions_avoided"] = sum(
            binding.replacement != _short_name(binding.original) for binding in bindings
        )
    elif mode == "misleading":
        stats.update(
            {
                "method_candidate_pool_size": len(METHOD_MEANINGFUL_NAMES),
                "method_random_pool_selections": len(bindings)
                - misleading_metrics["alphabetic_fallbacks_used"],
                "method_collision_candidates_skipped": misleading_metrics[
                    "collision_candidates_skipped"
                ],
                "method_alphabetic_fallbacks_used": misleading_metrics[
                    "alphabetic_fallbacks_used"
                ],
                "method_exact_length_matches": sum(
                    len(binding.replacement) == len(binding.original)
                    for binding in bindings
                ),
                "method_total_length_difference": sum(
                    abs(len(binding.replacement) - len(binding.original))
                    for binding in bindings
                ),
            }
        )
    else:
        stats["method_name_collisions_avoided"] = 0
    return TransformResult(
        apply_edits(
            source,
            [(start, end, value) for (start, end), value in edits.items()],
        ),
        stats,
    )


def _make_binding(
    source: bytes,
    name_node: Node,
    scope: Node,
    scope_start: int,
    context: InterferenceContext,
    used: set[str],
    mode: str,
    misleading_metrics: dict[str, int],
) -> _Binding:
    original = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
    used.discard(original)
    replacement = _replacement_name(
        original,
        context,
        name_node.start_byte,
        used,
        mode,
        misleading_metrics=misleading_metrics,
    )
    return _Binding(
        original,
        replacement,
        name_node.start_byte,
        name_node.end_byte,
        scope_start,
        scope.end_byte,
    )


def _replacement_name(
    original: str,
    context: InterferenceContext,
    offset: int,
    used: set[str],
    mode: str,
    identity_suffix: str = "",
    misleading_metrics: dict[str, int] | None = None,
) -> str:
    if mode == "short":
        base = _short_name(original)
        nonce = 1
        replacement = base
        while replacement in used or replacement in _JAVA_KEYWORDS:
            nonce += 1
            replacement = f"{base}{nonce}"
    elif mode == "misleading":
        choice = choose_misleading_name(
            original,
            context,
            offset,
            method=identity_suffix.startswith(":method:"),
            identity_suffix=identity_suffix,
            used=used,
            forbidden=_JAVA_KEYWORDS,
        )
        replacement = choice.name
        if misleading_metrics is not None:
            misleading_metrics["collision_candidates_skipped"] += (
                choice.collision_candidates_skipped
            )
            misleading_metrics["alphabetic_fallbacks_used"] += int(
                choice.used_alphabetic_fallback
            )
    else:
        index = 0
        while True:
            replacement = _proguard_style_name(index)
            if replacement not in used and replacement not in _JAVA_KEYWORDS:
                break
            index += 1
    used.add(replacement)
    return replacement


def _short_name(original: str) -> str:
    pieces = [piece for piece in re.split(r"_+", original) if piece]
    token_source = pieces[0] if pieces else original
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+", token_source)
    if len(pieces) > 1 or len(words) > 1:
        base = words[0] if words else token_source
    else:
        base = token_source[:3]
    base = base[:1].lower() + base[1:]
    base = re.sub(r"[^A-Za-z0-9_$]", "", base)
    if not base or not re.match(r"[A-Za-z_$]", base):
        base = "var"
    return base


def _proguard_style_name(index: int) -> str:
    """Return the shortest mixed-case identifier at a zero-based index.

    This independently implements the documented ProGuard-style sequence
    ``a..z, A..Z, aa, ab, ...``. Java keywords are filtered by the caller.
    """
    if index < 0:
        raise ValueError("identifier index must be non-negative")
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = len(alphabet)
    characters: list[str] = []
    while True:
        characters.append(alphabet[index % base])
        index = index // base - 1
        if index < 0:
            return "".join(reversed(characters))


def _parameter_scope(node: Node) -> Node | None:
    current = node.parent
    while current is not None:
        if current.type == "lambda_expression" or current.type in _CALLABLE_NODES:
            return current
        current = current.parent
    return None


def _nearest_callable(node: Node) -> Node | None:
    return ancestor(node, _CALLABLE_NODES)


def _local_scope(node: Node) -> Node | None:
    current = node.parent
    callable_node = _nearest_callable(node)
    while current is not None and current != callable_node:
        if current.type in {
            "block",
            "for_statement",
            "enhanced_for_statement",
            "try_with_resources_statement",
        }:
            return current
        current = current.parent
    return callable_node


def _is_reference_identifier(node: Node) -> bool:
    parent = node.parent
    if parent is None:
        return False
    if parent.type == "scoped_identifier":
        return False
    if parent.type == "field_access" and parent.child_by_field_name("field") == node:
        return False
    if parent.type in _REFERENCE_NAME_PARENTS:
        name = parent.child_by_field_name("name")
        if name == node:
            return False
        if parent.type in {
            "break_statement",
            "continue_statement",
            "labeled_statement",
        }:
            return False
    return True
