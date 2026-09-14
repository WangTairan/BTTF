from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import tree_sitter_java
from tree_sitter import Language, Parser

JAVA_OPERATORS = {"+", "-", "*", "==", "!=", "<", "<=", ">", ">=", "&&", "||"}
PYTHON_OPERATORS = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.MatMult: "@",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.And: "and",
    ast.Or: "or",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
}


def _anchor_id(
    language: str, base_sample_id: str, method: int, site: int, kind: str, value: str
) -> str:
    payload = f"{language}:{base_sample_id}:{method}:{site}:{kind}:{value}"
    return "mutation-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _walk_java(node):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.named_children))


def java_mutation_anchors(path: Path, base_sample_id: str) -> list[dict[str, object]]:
    source = path.read_bytes()
    parser = Parser(Language(tree_sitter_java.language()))
    root = parser.parse(source).root_node
    methods = [
        node
        for node in _walk_java(root)
        if node.type == "method_declaration"
        and node.child_by_field_name("body") is not None
    ]
    anchors: list[dict[str, object]] = []
    for method_index, method in enumerate(methods):
        name_node = method.child_by_field_name("name")
        method_name = (
            source[name_node.start_byte : name_node.end_byte].decode("utf-8")
            if name_node
            else "<unknown>"
        )
        sites: list[tuple[object, str, str]] = []
        for node in _walk_java(method.child_by_field_name("body")):
            if node.type in {"true", "false"}:
                sites.append((node, "boolean_literal", node.type))
            elif node.type == "binary_expression":
                operator = next(
                    (
                        child.type
                        for child in node.children
                        if child.type in JAVA_OPERATORS
                    ),
                    None,
                )
                if operator is not None:
                    sites.append((node, "binary_operator", operator))
        for site_index, (node, kind, value) in enumerate(sites):
            anchors.append(
                {
                    "mutation_id": _anchor_id(
                        "java", base_sample_id, method_index, site_index, kind, value
                    ),
                    "method_index": method_index,
                    "method_name": method_name,
                    "site_index_in_method": site_index,
                    "kind": kind,
                    "original_value": value,
                    "start_line": node.start_point.row + 1,
                    "start_column": node.start_point.column,
                }
            )
    return anchors


def _python_class_methods(
    module: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    parents = {
        child: parent
        for parent in ast.walk(module)
        for child in ast.iter_child_nodes(parent)
    }
    return [
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and isinstance(parents.get(node), ast.ClassDef)
    ]


def _method_nodes(method: ast.FunctionDef | ast.AsyncFunctionDef):
    """Walk one method without attributing nested functions/classes to it."""
    stack: list[ast.AST] = list(reversed(method.body))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def python_mutation_anchors(path: Path, base_sample_id: str) -> list[dict[str, object]]:
    module = ast.parse(path.read_text(encoding="utf-8"))
    anchors: list[dict[str, object]] = []
    for method_index, method in enumerate(_python_class_methods(module)):
        sites: list[tuple[ast.AST, str, str]] = []
        for node in _method_nodes(method):
            if isinstance(node, ast.BinOp) and type(node.op) in PYTHON_OPERATORS:
                sites.append((node, "binary_operator", PYTHON_OPERATORS[type(node.op)]))
            elif isinstance(node, ast.Compare):
                for operator in node.ops:
                    if type(operator) in PYTHON_OPERATORS:
                        sites.append(
                            (
                                node,
                                "comparison_operator",
                                PYTHON_OPERATORS[type(operator)],
                            )
                        )
            elif isinstance(node, ast.BoolOp) and type(node.op) in PYTHON_OPERATORS:
                sites.append(
                    (node, "boolean_operator", PYTHON_OPERATORS[type(node.op)])
                )
            elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
                sites.append((node, "boolean_literal", str(node.value).lower()))
        sites.sort(
            key=lambda item: (
                getattr(item[0], "lineno", 0),
                getattr(item[0], "col_offset", 0),
                item[1],
                item[2],
            )
        )
        for site_index, (node, kind, value) in enumerate(sites):
            anchors.append(
                {
                    "mutation_id": _anchor_id(
                        "python", base_sample_id, method_index, site_index, kind, value
                    ),
                    "method_index": method_index,
                    "method_name": method.name,
                    "site_index_in_method": site_index,
                    "kind": kind,
                    "original_value": value,
                    "start_line": node.lineno,
                    "start_column": node.col_offset,
                }
            )
    return anchors
