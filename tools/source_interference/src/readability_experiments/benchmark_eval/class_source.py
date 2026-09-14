"""Locate and replace one complete top-level class inside a source file."""

from __future__ import annotations

import ast
from collections.abc import Callable

from readability_data.java_degradation.interferences.core.java import tree, walk


def transform_python_class(
    source: str,
    class_name: str,
    transform: Callable[[str], str],
) -> str:
    module = ast.parse(source)
    matches = [
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one top-level Python class {class_name!r}, found {len(matches)}"
        )
    node = matches[0]
    starts = [0]
    for line in source.splitlines(keepends=True):
        starts.append(starts[-1] + len(line.encode("utf-8")))
    start = starts[node.lineno - 1] + node.col_offset
    end = starts[node.end_lineno - 1] + node.end_col_offset
    data = source.encode("utf-8")
    replacement = transform(data[start:end].decode("utf-8")).encode("utf-8")
    result = (data[:start] + replacement + data[end:]).decode("utf-8")
    ast.parse(result)
    return result


def transform_java_class(
    source: bytes,
    class_name: str,
    transform: Callable[[bytes], bytes],
) -> bytes:
    matches = []
    for node in walk(tree(source).root_node):
        if node.type not in {
            "class_declaration",
            "enum_declaration",
            "interface_declaration",
            "record_declaration",
        }:
            continue
        name = node.child_by_field_name("name")
        if (
            name is not None
            and source[name.start_byte : name.end_byte].decode("utf-8") == class_name
        ):
            matches.append(node)
    top_level = [
        node for node in matches if node.parent and node.parent.type == "program"
    ]
    if len(top_level) != 1:
        raise ValueError(
            f"expected one top-level Java class {class_name!r}, found {len(top_level)}"
        )
    node = top_level[0]
    replacement = transform(source[node.start_byte : node.end_byte])
    result = source[: node.start_byte] + replacement + source[node.end_byte :]
    parsed = tree(result)
    if parsed.root_node.has_error:
        raise ValueError(f"transformed Java file for {class_name} does not parse")
    return result
