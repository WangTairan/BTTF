from __future__ import annotations

import ast
import keyword
import re
import string

from readability_data.python_degradation.core import (
    Context,
    Interference,
    Result,
    apply_edits,
    offsets,
    span,
)
from readability_data.shared.meaningful_names import (
    LOCAL_MEANINGFUL_NAMES,
    METHOD_MEANINGFUL_NAMES,
    choose_misleading_name,
)


class RenameIdentifiers(Interference):
    category = "identifiers"

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.slug = {
            "short": "shorten-identifiers",
            "misleading": "mislead-identifiers",
            "garbled": "garble-identifiers",
        }[mode]
        self.description = {
            "short": "Shorten method, parameter, and local names without collisions",
            "misleading": "Replace names with length-matched meaningful but unrelated identifiers",
            "garbled": "Replace names with deterministic minifier-style shortest identifiers",
        }[mode]

    def apply(self, source: str, context: Context) -> Result:
        tree = ast.parse(source)
        starts = offsets(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        functions = [
            n
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        methods = [
            n
            for n in functions
            if isinstance(parents.get(n), ast.ClassDef)
            and n.name != "__init__"
            and not (n.name.startswith("__") and n.name.endswith("__"))
        ]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        scoped_misleading = self.mode == "misleading"
        existing = {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        } | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        legacy_used = set(existing)
        method_mapping: dict[object, str] = {}
        local_mapping: dict[tuple[ast.AST, str], str] = {}
        method_used = {
            class_node: {
                function.name
                for function in functions
                if parents.get(function) is class_node
            }
            for class_node in classes
        }
        collisions = 0
        declaration_count = 0
        method_metrics = {
            "collision_candidates_skipped": 0,
            "alphabetic_fallbacks_used": 0,
        }
        local_metrics = {
            "collision_candidates_skipped": 0,
            "alphabetic_fallbacks_used": 0,
        }
        for method in sorted(methods, key=lambda n: (n.lineno, n.col_offset)):
            class_node = parents[method]
            used = method_used[class_node] if scoped_misleading else legacy_used
            replacement = self._name(
                method.name,
                span(method, starts)[0],
                True,
                context,
                used,
                identity_suffix=f":method:{span(class_node, starts)[0]}",
                misleading_metrics=method_metrics,
            )
            method_key = (class_node, method.name) if scoped_misleading else method.name
            method_mapping[method_key] = replacement
            used.add(replacement)
            declaration_count += 1
        for function in sorted(functions, key=lambda n: (n.lineno, n.col_offset)):
            declarations: dict[str, ast.AST] = {}
            args = [
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            ]
            if function.args.vararg:
                args.append(function.args.vararg)
            if function.args.kwarg:
                args.append(function.args.kwarg)
            for arg in args:
                if arg.arg not in {"self", "cls"}:
                    declarations.setdefault(arg.arg, arg)
            for node in ast.walk(function):
                if (
                    isinstance(node, ast.Name)
                    and isinstance(node.ctx, ast.Store)
                    and _nearest_function(node, parents) is function
                ):
                    declarations.setdefault(node.id, node)
            function_used = (
                {
                    item.id
                    for item in ast.walk(function)
                    if isinstance(item, ast.Name)
                    and _nearest_function(item, parents) is function
                }
                | {argument.arg for argument in args}
                if scoped_misleading
                else legacy_used
            )
            for name, node in sorted(
                declarations.items(),
                key=lambda item: (item[1].lineno, item[1].col_offset),
            ):
                replacement = self._name(
                    name,
                    span(node, starts)[0],
                    False,
                    context,
                    function_used,
                    misleading_metrics=local_metrics,
                )
                local_mapping[(function, name)] = replacement
                function_used.add(replacement)
                declaration_count += 1
        edits: dict[tuple[int, int], str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                function = _nearest_function(node, parents)
                replacement = (
                    local_mapping.get((function, node.id)) if function else None
                )
                if replacement:
                    edits[span(node, starts)] = replacement
            elif isinstance(node, ast.arg):
                function = _nearest_function(node, parents)
                replacement = (
                    local_mapping.get((function, node.arg)) if function else None
                )
                if replacement:
                    start, _ = span(node, starts)
                    edits[(start, start + len(node.arg.encode()))] = replacement
            elif isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and isinstance(parents.get(node), ast.ClassDef):
                method_key = (
                    (parents[node], node.name) if scoped_misleading else node.name
                )
                if method_key not in method_mapping:
                    continue
                line_start = starts[node.lineno - 1]
                header_end = starts[node.lineno]
                chunk = source.encode()[line_start:header_end]
                match = re.search(
                    rb"\b" + re.escape(node.name.encode()) + rb"\s*\(", chunk
                )
                if match:
                    start = line_start + match.start()
                    replacement = method_mapping[method_key]
                    edits[(start, start + len(node.name.encode()))] = replacement
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if scoped_misleading:
                    owner = _method_call_owner(node, classes, parents)
                    replacement = (
                        method_mapping.get((owner, node.attr)) if owner else None
                    )
                elif node.value.id in {
                    "self",
                    "cls",
                    *(class_node.name for class_node in classes),
                }:
                    replacement = method_mapping.get(node.attr)
                else:
                    replacement = None
                if replacement:
                    _, end = span(node, starts)
                    edits[(end - len(node.attr.encode()), end)] = replacement
        result = apply_edits(source, [(a, b, v) for (a, b), v in edits.items()])
        stats = {
            "identifiers_declared": declaration_count,
            "identifier_occurrences_renamed": len(edits),
            "collisions_avoided": collisions,
        }
        if self.mode == "misleading":
            stats.update(
                {
                    "local_candidate_pool_size": len(LOCAL_MEANINGFUL_NAMES),
                    "method_candidate_pool_size": len(METHOD_MEANINGFUL_NAMES),
                    "local_random_pool_selections": (
                        declaration_count
                        - len(methods)
                        - local_metrics["alphabetic_fallbacks_used"]
                    ),
                    "method_random_pool_selections": len(methods)
                    - method_metrics["alphabetic_fallbacks_used"],
                    "local_collision_candidates_skipped": local_metrics[
                        "collision_candidates_skipped"
                    ],
                    "method_collision_candidates_skipped": method_metrics[
                        "collision_candidates_skipped"
                    ],
                    "local_alphabetic_fallbacks_used": local_metrics[
                        "alphabetic_fallbacks_used"
                    ],
                    "method_alphabetic_fallbacks_used": method_metrics[
                        "alphabetic_fallbacks_used"
                    ],
                    "local_exact_length_matches": sum(
                        len(replacement) == len(original)
                        for (_, original), replacement in local_mapping.items()
                    ),
                    "local_total_length_difference": sum(
                        abs(len(replacement) - len(original))
                        for (_, original), replacement in local_mapping.items()
                    ),
                    "method_exact_length_matches": sum(
                        len(replacement) == len(key[1])
                        for key, replacement in method_mapping.items()
                    ),
                    "method_total_length_difference": sum(
                        abs(len(replacement) - len(key[1]))
                        for key, replacement in method_mapping.items()
                    ),
                }
            )
        return Result(result, stats)

    def _name(
        self,
        original: str,
        offset: int,
        method: bool,
        context: Context,
        used: set[str],
        identity_suffix: str = "",
        misleading_metrics: dict[str, int] | None = None,
    ) -> str:
        if self.mode == "short":
            pieces = [piece for piece in re.split(r"_+", original) if piece]
            token_source = pieces[0] if pieces else original
            words = re.findall(
                r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+",
                token_source,
            )
            if len(pieces) > 1 or len(words) > 1:
                base = words[0] if words else token_source
            else:
                base = token_source[:3]
            base = (base[:1].lower() + base[1:]) or "var"
            return _available(base, used)
        if self.mode == "garbled":
            for candidate in _short_names():
                if candidate not in used and not keyword.iskeyword(candidate):
                    return candidate
        choice = choose_misleading_name(
            original,
            context,
            offset,
            method=method,
            identity_suffix=identity_suffix,
            used=used,
            forbidden=set(keyword.kwlist),
        )
        if misleading_metrics is not None:
            misleading_metrics["collision_candidates_skipped"] += (
                choice.collision_candidates_skipped
            )
            misleading_metrics["alphabetic_fallbacks_used"] += int(
                choice.used_alphabetic_fallback
            )
        return choice.name


def _available(base: str, used: set[str]) -> str:
    if base not in used and not keyword.iskeyword(base):
        return base
    index = 2
    while f"{base}{index}" in used:
        index += 1
    return f"{base}{index}"


def _nearest_function(node: ast.AST, parents: dict[ast.AST, ast.AST]):
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    return None


def _nearest_class(node: ast.AST, parents: dict[ast.AST, ast.AST]):
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.ClassDef):
            return node
    return None


def _method_call_owner(
    node: ast.Attribute,
    classes: list[ast.ClassDef],
    parents: dict[ast.AST, ast.AST],
) -> ast.ClassDef | None:
    if not isinstance(node.value, ast.Name):
        return None
    if node.value.id in {"self", "cls"}:
        return _nearest_class(node, parents)
    return next(
        (class_node for class_node in classes if class_node.name == node.value.id),
        None,
    )


def _short_names():
    alphabet = string.ascii_lowercase + string.ascii_uppercase
    width = 1
    while True:
        count = len(alphabet) ** width
        for number in range(count):
            chars = []
            for _ in range(width):
                chars.append(alphabet[number % len(alphabet)])
                number //= len(alphabet)
            yield "".join(reversed(chars))
        width += 1


PLUGINS = (
    RenameIdentifiers("short"),
    RenameIdentifiers("misleading"),
    RenameIdentifiers("garbled"),
)
