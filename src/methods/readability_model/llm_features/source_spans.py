"""Original-source intervals for role-conditioned causal-LM measurements.

Intervals are Unicode character offsets, not normalized extractor strings or
parser byte offsets. A role measures a deliberately bounded source object:
calls exclude arguments, variable declarations exclude initializers, and
function signatures retain defaults but exclude their bodies. Likewise,
control headers exclude their bodies. Cross-role overlap is intentional;
within-role containing intervals are coalesced to avoid counting nested
expressions twice.

Complete programs must parse. Explicit fragments may be wrapped without
changing their mapped source, or receive lexical-only measurements with a
visible parse diagnostic. Unresolved names never acquire guessed bindings.
"""

from __future__ import annotations

import ast
import bisect
import io
import keyword
import re
import tokenize
from dataclasses import dataclass, field
from typing import Any

ROLES = frozenset(
    {
        "identifier",
        "declaration_header",
        "call_target",
        "control_header",
        "assignment_rhs",
        "expression",
        "literal",
        "comment",
    }
)
SOURCE_ANALYSIS_VERSION = 1
LEXICAL_ROLES = frozenset({"identifier", "literal", "comment"})
_LANGUAGES = {
    "python": "python",
    "py": "python",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "cuda": "cpp",
    "cu": "cpp",
}


@dataclass(frozen=True)
class SourceSpan:
    start: int
    end: int
    role: str
    binding: str | None = None


@dataclass
class SourceAnalysis:
    spans: list[SourceSpan]
    roles_available: set[str]
    metadata: dict[str, Any]


class SourceParseError(ValueError):
    """A complete source program could not be structurally analyzed."""


@dataclass
class _MappedSource:
    text: str
    # One entry per transformed Unicode character; synthetic characters are None.
    original: list[int | None]
    byte_starts: list[int] = field(init=False)

    def __post_init__(self) -> None:
        self.byte_starts = [0]
        for character in self.text:
            self.byte_starts.append(
                self.byte_starts[-1] + len(character.encode("utf-8"))
            )

    @classmethod
    def wrap(
        cls, source: str, prefix: str = "", suffix: str = "", indent: str = ""
    ) -> _MappedSource:
        chars = list(prefix)
        origins: list[int | None] = [None] * len(prefix)
        for index, char in enumerate(source):
            if indent and (index == 0 or source[index - 1] == "\n"):
                chars.extend(indent)
                origins.extend([None] * len(indent))
            chars.append(char)
            origins.append(index)
        chars.extend(suffix)
        origins.extend([None] * len(suffix))
        return cls("".join(chars), origins)

    def interval(self, start_byte: int, end_byte: int) -> tuple[int, int] | None:
        start = bisect.bisect_left(self.byte_starts, start_byte)
        end = bisect.bisect_left(self.byte_starts, end_byte)
        if start >= end or end > len(self.original):
            return None
        # Reject enclosing synthetic declarations, not merely trim wrappers.
        if self.original[start] is None or self.original[end - 1] is None:
            return None
        return int(self.original[start]), int(self.original[end - 1]) + 1


def _finalize(
    source: str, spans: list[SourceSpan], roles: set[str], metadata: dict[str, Any]
) -> SourceAnalysis:
    result: list[SourceSpan] = []
    for role in sorted(roles):
        candidates = sorted(
            {span for span in spans if span.role == role},
            key=lambda span: (span.start, -span.end),
        )
        retained: list[SourceSpan] = []
        for span in candidates:
            if not 0 <= span.start < span.end <= len(source):
                raise ValueError(f"Invalid original-source span: {span}")
            # An identifier is an occurrence, never deduplicated by spelling.
            if role != "identifier" and retained and span.end <= retained[-1].end:
                continue
            retained.append(span)
        result.extend(retained)
    metadata["role_counts"] = {
        role: sum(span.role == role for span in result) for role in sorted(ROLES)
    }
    metadata["binding_count"] = len(
        {span.binding for span in result if span.binding is not None}
    )
    metadata["source_analysis_version"] = SOURCE_ANALYSIS_VERSION
    metadata["declaration_header_policy"] = (
        "variable declarations exclude initializers; function/class signatures "
        "exclude bodies and retain parameter defaults"
    )
    return SourceAnalysis(
        sorted(result, key=lambda span: (span.start, span.end, span.role)),
        roles,
        metadata,
    )


def analyze_source(
    source: str,
    language: str,
    allow_fragments: bool = False,
    *,
    allow_class_members: bool = False,
) -> SourceAnalysis:
    """Analyze raw code without renaming, repairing or truncating its source.

    ``allow_fragments`` is a caller-declared source-form policy, not a blanket
    exception handler for complete programs. If every parse candidate fails,
    only tokenizer-backed lexical roles remain available and diagnostics say so.
    ``allow_class_members`` permits a verified enclosing-class parse for Java
    method/constructor snippets, without enabling lexical-only measurements.
    """
    if not isinstance(source, str):
        raise TypeError("source must be a Unicode string")
    normalized = _LANGUAGES.get(language.lower())
    if normalized is None:
        raise ValueError(f"Unsupported LLM source language: {language!r}")
    if allow_class_members and normalized != "java":
        raise ValueError("Class-member source form is only supported for Java.")
    if normalized == "python":
        return _python_analysis(source, allow_fragments)
    return _tree_analysis(source, normalized, allow_fragments, allow_class_members)


def _line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(index + 1 for index, char in enumerate(text) if char == "\n")
    return starts


def _python_tokens(
    source: str, allow_fragments: bool
) -> tuple[list[tokenize.TokenInfo], str | None]:
    tokens: list[tokenize.TokenInfo] = []
    try:
        tokens.extend(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError) as exc:
        if not allow_fragments:
            raise SourceParseError(f"Python tokenization failed: {exc}") from exc
        return tokens, str(exc)
    return tokens, None


def _fstring_fixed_intervals(
    source: str, start: int, end: int
) -> list[tuple[int, int]]:
    """Locate literal text outside interpolation fields of a validated f-string.

    Python 3.11's AST locates embedded expressions precisely but gives each
    fixed-text Constant the entire f-string interval. We therefore scan only
    interpolation boundaries, respecting nested braces and quoted expressions.
    Formatting directives inside fields are not ordinary literal text.
    """
    token = source[start:end]
    opening = re.match(r"(?i)([rubf]*)(\"\"\"|'''|\"|')", token)
    if opening is None or "f" not in opening.group(1).lower():
        return []
    quote = opening.group(2)
    body_start = start + opening.end()
    body_end = end - len(quote)
    fixed_start = body_start
    index = body_start
    result = []
    while index < body_end:
        if source[index : index + 2] in {"{{", "}}"}:
            index += 2
            continue
        if source[index] != "{":
            index += 1
            continue
        if fixed_start < index:
            result.append((fixed_start, index))
        depth = 1
        index += 1
        while index < body_end and depth:
            character = source[index]
            if character in {'"', "'"}:
                expression_quote = (
                    source[index : index + 3]
                    if source[index : index + 3] in {'"""', "'''"}
                    else character
                )
                index += len(expression_quote)
                while index < body_end:
                    if source[index] == "\\":
                        index += 2
                    elif source.startswith(expression_quote, index):
                        index += len(expression_quote)
                        break
                    else:
                        index += 1
                continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            index += 1
        if depth:
            raise SourceParseError(
                "Validated f-string has unlocatable interpolation boundaries"
            )
        fixed_start = index
    if fixed_start < body_end:
        result.append((fixed_start, body_end))
    return result


def _python_analysis(source: str, allow_fragments: bool) -> SourceAnalysis:
    candidates = [("original", _MappedSource.wrap(source))]
    if allow_fragments:
        candidates.extend(
            [
                (
                    "function_body",
                    _MappedSource.wrap(source, "def __fragment__():\n", "\n", "    "),
                ),
                ("enclosing_suite", _MappedSource.wrap(source, "if True:\n", "\n")),
            ]
        )
    failures: list[str] = []
    for mode, mapped in candidates:
        try:
            tree = ast.parse(mapped.text)
        except SyntaxError as exc:
            failures.append(f"{mode}: {exc.msg} at {exc.lineno}:{exc.offset}")
            continue
        tokens, token_error = _python_tokens(mapped.text, False)
        collector = _PythonCollector(source, mapped, tokens)
        collector.collect(tree)
        return _finalize(
            source,
            collector.spans,
            set(ROLES),
            {
                "language": "python",
                "parser": "ast+tokenize",
                "parse_mode": mode,
                "structural_available": True,
                "parse_diagnostics": failures,
                "tokenization_diagnostic": token_error,
                "comment_targets": collector.comment_targets,
            },
        )
    if not allow_fragments:
        raise SourceParseError("; ".join(failures))
    tokens, token_error = _python_tokens(source, True)
    mapped = _MappedSource.wrap(source)
    collector = _PythonCollector(source, mapped, tokens)
    collector.lexical()
    return _finalize(
        source,
        collector.spans,
        set(LEXICAL_ROLES) if token_error is None else set(),
        {
            "language": "python",
            "parser": "tokenize",
            "parse_mode": "lexical_fragment",
            "structural_available": False,
            "parse_diagnostics": failures,
            "tokenization_diagnostic": token_error,
            "comment_targets": [],
        },
    )


@dataclass
class _PythonScope:
    parent: _PythonScope | None
    kind: str
    start: int
    end: int
    names: dict[str, str] = field(default_factory=dict)
    global_names: set[str] = field(default_factory=set)
    nonlocal_names: set[str] = field(default_factory=set)

    def resolve(self, name: str) -> str | None:
        if name in self.global_names:
            return None
        if name in self.names and name not in self.nonlocal_names:
            return self.names[name]
        parent = self.parent
        # A method does not lexically close over its class namespace.
        while parent is not None and parent.kind == "class":
            parent = parent.parent
        return parent.resolve(name) if parent is not None else None


class _PythonCollector:
    def __init__(
        self, source: str, mapped: _MappedSource, tokens: list[tokenize.TokenInfo]
    ) -> None:
        self.source = source
        self.mapped = mapped
        self.tokens = tokens
        self.lines = _line_starts(mapped.text)
        self.token_starts = [self.character(token.start) for token in tokens]
        self.name_tokens = {
            self.character(token.start): token
            for token in tokens
            if token.type == tokenize.NAME
        }
        self.spans: list[SourceSpan] = []
        self.docstrings: set[tuple[int, int]] = set()
        self.dynamic_strings: set[tuple[int, int]] = set()
        self.dynamic_node_intervals: set[tuple[int, int]] = set()
        self.soft_keywords: set[tuple[int, int]] = set()
        self.scopes: dict[int, _PythonScope] = {}
        self.bindings: dict[tuple[int, int], str] = {}
        self.comment_targets: list[dict[str, int]] = []

    def character(
        self, position: tuple[int, int], *, bytes_column: bool = False
    ) -> int:
        line, column = position
        if not bytes_column and line > len(self.lines):
            return len(self.mapped.text)  # tokenize's synthetic EOF line.
        start = self.lines[line - 1]
        if bytes_column:
            text = self.mapped.text[start:]
            prefix = text.encode("utf-8")[:column].decode("utf-8")
            return start + len(prefix)
        return start + column

    def node_interval(self, node: ast.AST) -> tuple[int, int]:
        return (
            self.character((node.lineno, node.col_offset), bytes_column=True),
            self.character((node.end_lineno, node.end_col_offset), bytes_column=True),
        )

    def add(self, start: int, end: int, role: str, binding: str | None = None) -> None:
        byte_start = self.mapped.byte_starts[start]
        byte_end = self.mapped.byte_starts[end]
        interval = self.mapped.interval(byte_start, byte_end)
        if interval is not None:
            self.spans.append(SourceSpan(*interval, role, binding))

    def add_node(self, node: ast.AST, role: str) -> None:
        self.add(*self.node_interval(node), role)

    def header_end(self, node: ast.AST) -> int:
        start, end = self.node_interval(node)
        return self.header_end_interval(start, end)

    def header_end_interval(self, start: int, end: int) -> int:
        depth = 0
        for token in self.tokens[bisect.bisect_left(self.token_starts, start) :]:
            token_start = self.character(token.start)
            if token_start < start:
                continue
            if token_start >= end:
                break
            if token.type == tokenize.OP:
                if token.string in "([{":
                    depth += 1
                elif token.string in ")]}":
                    depth -= 1
                elif token.string == ":" and depth == 0:
                    return self.character(token.end)
        return end

    def lexical(self) -> None:
        docstrings = sorted(self.docstrings)
        docstring_starts = [interval[0] for interval in docstrings]
        for token in self.tokens:
            if token.type not in {
                tokenize.NAME,
                tokenize.COMMENT,
                tokenize.NUMBER,
                tokenize.STRING,
            }:
                continue
            start = self.character(token.start)
            end = self.character(token.end)
            if start == end:
                continue
            if token.type == tokenize.NAME and not keyword.iskeyword(token.string):
                if (start, end) not in self.soft_keywords:
                    self.add(start, end, "identifier", self.bindings.get((start, end)))
            elif token.type == tokenize.NAME and token.string in {
                "True",
                "False",
                "None",
            }:
                self.add(start, end, "literal")
            elif token.type == tokenize.COMMENT:
                self.add(start, end, "comment")
            elif token.type in {tokenize.NUMBER, tokenize.STRING}:
                if (start, end) in self.dynamic_strings:
                    continue
                doc_index = bisect.bisect_right(docstring_starts, start) - 1
                is_docstring = doc_index >= 0 and end <= docstrings[doc_index][1]
                role = "comment" if is_docstring else "literal"
                self.add(start, end, role)

    def bind_name(self, scope: _PythonScope, name: str, position: int) -> None:
        if scope.kind not in {"function", "lambda", "comprehension"}:
            return
        interval = self.mapped.interval(
            self.mapped.byte_starts[position],
            self.mapped.byte_starts[min(position + 1, len(self.mapped.text))],
        )
        if interval is not None:
            scope.names.setdefault(
                name, f"python:{scope.kind}:{scope.start}:{interval[0]}:{name}"
            )

    def collect_scope_names(self, node: ast.AST, scope: _PythonScope) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = node.args
            for argument in [
                *args.posonlyargs,
                *args.args,
                *args.kwonlyargs,
                args.vararg,
                args.kwarg,
            ]:
                if argument is not None:
                    self.bind_name(scope, argument.arg, self.node_interval(argument)[0])

        def visit(child: ast.AST) -> None:
            if child is not node and isinstance(
                child,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                return
            if isinstance(child, ast.Global):
                scope.global_names.update(child.names)
            elif isinstance(child, ast.Nonlocal):
                scope.nonlocal_names.update(child.names)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                self.bind_name(scope, child.id, self.node_interval(child)[0])
            elif (
                isinstance(child, ast.ExceptHandler)
                and child.name is not None
                or (
                    isinstance(child, (ast.MatchAs, ast.MatchStar))
                    and child.name is not None
                )
            ):
                self.bind_name(scope, child.name, self.node_interval(child)[0])
            elif isinstance(child, ast.MatchMapping) and child.rest is not None:
                self.bind_name(scope, child.rest, self.node_interval(child)[0])
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    self.bind_name(
                        scope,
                        alias.asname or alias.name.split(".")[0],
                        self.node_interval(child)[0],
                    )
            for grandchild in ast.iter_child_nodes(child):
                visit(grandchild)

        visit(node)
        for name in scope.global_names | scope.nonlocal_names:
            scope.names.pop(name, None)

    def record_binding(self, node: ast.AST, scope: _PythonScope) -> None:
        if isinstance(node, ast.Name):
            interval = self.node_interval(node)
            binding = scope.resolve(node.id)
            self.add(*interval, "identifier", binding)
            if binding:
                self.bindings[interval] = binding
        elif isinstance(node, ast.arg):
            start, _ = self.node_interval(node)
            binding = scope.resolve(node.arg)
            if binding:
                token = self.name_tokens.get(start)
                if token is not None:
                    self.bindings[(start, self.character(token.end))] = binding
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            start, _ = self.node_interval(node)
            end = self.header_end(node)
            binding = scope.resolve(node.name)
            self.record_declaration_token(node.name, start, end, binding, last=True)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                start, end = self.node_interval(alias)
                self.record_declaration_token(
                    name, start, end, scope.resolve(name), last=alias.asname is not None
                )
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None:
            start, end = self.node_interval(node)
            self.record_declaration_token(
                node.name, start, end, scope.resolve(node.name), last=True
            )
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            start, end = self.node_interval(node)
            self.record_declaration_token(
                node.rest, start, end, scope.resolve(node.rest), last=True
            )

    def record_declaration_token(
        self, name: str, start: int, end: int, binding: str | None, *, last: bool
    ) -> None:
        if binding is None:
            return
        first_index = bisect.bisect_left(self.token_starts, start)
        last_index = bisect.bisect_left(self.token_starts, end)
        matching = [
            token
            for token in self.tokens[first_index:last_index]
            if token.type == tokenize.NAME and token.string == name
        ]
        if matching:
            token = matching[-1] if last else matching[0]
            self.bindings[(self.character(token.start), self.character(token.end))] = (
                binding
            )

    def collect(self, tree: ast.AST) -> None:
        root = _PythonScope(None, "module", 0, len(self.mapped.text))

        def visit(node: ast.AST, scope: _PythonScope) -> None:
            enclosing_scope = scope
            is_function = isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
            )
            is_class = isinstance(node, ast.ClassDef)
            is_comprehension = isinstance(
                node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
            )
            if is_function or is_class or is_comprehension:
                start, end = self.node_interval(node)
                kind = (
                    "class"
                    if is_class
                    else "comprehension"
                    if is_comprehension
                    else "lambda"
                    if isinstance(node, ast.Lambda)
                    else "function"
                )
                new_scope = _PythonScope(scope, kind, start, end)
                self.collect_scope_names(node, new_scope)
                if is_comprehension:
                    for generator in node.generators:
                        for target in ast.walk(generator.target):
                            if isinstance(target, ast.Name):
                                self.bind_name(
                                    new_scope, target.id, self.node_interval(target)[0]
                                )
                scope = new_scope
            self.record_binding(node, scope)
            if isinstance(node, ast.JoinedStr):
                interval = self.node_interval(node)
                if interval not in self.dynamic_node_intervals:
                    self.dynamic_node_intervals.add(interval)
                    first = bisect.bisect_left(self.token_starts, interval[0])
                    last = bisect.bisect_left(self.token_starts, interval[1])
                    string_tokens = [
                        token
                        for token in self.tokens[first:last]
                        if token.type == tokenize.STRING
                    ]
                    for token in string_tokens:
                        token_start, token_end = (
                            self.character(token.start),
                            self.character(token.end),
                        )
                        prefix = re.match(
                            r"(?i)([rubf]*)(\"\"\"|'''|\"|')", token.string
                        )
                        if prefix is not None and "f" in prefix.group(1).lower():
                            self.dynamic_strings.add((token_start, token_end))
                            for a, b in _fstring_fixed_intervals(
                                self.mapped.text, token_start, token_end
                            ):
                                self.add(a, b, "literal")
            elif isinstance(node, ast.Constant):
                interval = self.node_interval(node)
                if (
                    interval not in self.dynamic_node_intervals
                    and interval not in self.docstrings
                ):
                    self.add(*interval, "literal")
            elif isinstance(node, ast.Attribute):
                start, end = self.node_interval(node)
                attribute = self.trailing_name(start, end)
                if attribute:
                    self.add(*attribute, "identifier")
            elif isinstance(node, ast.Match):
                start, _ = self.node_interval(node)
                token = self.name_tokens.get(start)
                if token is not None:
                    self.soft_keywords.add((start, self.character(token.end)))
            elif (
                isinstance(node, ast.MatchAs)
                and node.name is None
                and node.pattern is None
            ):
                self.soft_keywords.add(self.node_interval(node))
            elif isinstance(node, ast.match_case):
                pattern_start, _ = self.node_interval(node.pattern)
                preceding = bisect.bisect_left(self.token_starts, pattern_start) - 1
                while preceding >= 0 and self.tokens[preceding].string != "case":
                    preceding -= 1
                if preceding >= 0:
                    token = self.tokens[preceding]
                    start = self.character(token.start)
                    self.soft_keywords.add((start, self.character(token.end)))
                    body_start, _ = self.node_interval(node.body[0])
                    self.add(
                        start,
                        self.header_end_interval(start, body_start),
                        "control_header",
                    )
            if (
                isinstance(
                    node,
                    (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                )
                and node.body
            ):
                first = node.body[0]
                if (
                    isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)
                ):
                    self.docstrings.add(self.node_interval(first.value))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start, _ = self.node_interval(node)
                self.add(start, self.header_end(node), "declaration_header")
            elif isinstance(node, ast.AnnAssign):
                start, _ = self.node_interval(node)
                self.add(
                    start, self.node_interval(node.annotation)[1], "declaration_header"
                )
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.add_node(node.func, "call_target")
                elif isinstance(node.func, ast.Attribute):
                    start, end = self.node_interval(node.func)
                    target = self.trailing_name(start, end)
                    if target:
                        self.add(*target, "call_target")
            if (
                isinstance(
                    node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)
                )
                and node.value is not None
            ):
                self.add_node(node.value, "assignment_rhs")
            if isinstance(
                node, (ast.BinOp, ast.BoolOp, ast.Compare, ast.UnaryOp, ast.AugAssign)
            ):
                self.add_node(node, "expression")
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                    ast.ExceptHandler,
                    ast.Match,
                ),
            ):
                start, _ = self.node_interval(node)
                self.add(start, self.header_end(node), "control_header")
            elif isinstance(
                node, (ast.Return, ast.Raise, ast.Break, ast.Continue, ast.Assert)
            ):
                self.add_node(node, "control_header")
            if is_comprehension:
                # The first iterable is evaluated outside the comprehension scope.
                first_iter = node.generators[0].iter
                visit(first_iter, scope.parent)
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.comprehension):
                        visit(child.target, scope)
                        if child.iter is not first_iter:
                            visit(child.iter, scope)
                        for predicate in child.ifs:
                            visit(predicate, scope)
                    else:
                        visit(child, scope)
                return
            if is_function:
                # Defaults, decorators and annotations execute outside the new
                # function's local namespace; only its body and parameter names
                # acquire the parameter/local bindings.
                arguments = node.args
                for argument in [
                    *arguments.posonlyargs,
                    *arguments.args,
                    *arguments.kwonlyargs,
                    arguments.vararg,
                    arguments.kwarg,
                ]:
                    if argument is not None:
                        self.record_binding(argument, scope)
                        if argument.annotation is not None:
                            visit(argument.annotation, enclosing_scope)
                for default in [*arguments.defaults, *arguments.kw_defaults]:
                    if default is not None:
                        visit(default, enclosing_scope)
                if isinstance(node, ast.Lambda):
                    visit(node.body, scope)
                else:
                    for statement in node.body:
                        visit(statement, scope)
                    for decorator in node.decorator_list:
                        visit(decorator, enclosing_scope)
                    if node.returns is not None:
                        visit(node.returns, enclosing_scope)
                return
            for child in ast.iter_child_nodes(node):
                visit(child, scope)

        visit(tree, root)
        self.lexical()
        self.collect_comment_targets(tree)

    def trailing_name(self, start: int, end: int) -> tuple[int, int] | None:
        # tokenizing an Attribute source slice also works inside Python 3.11
        # f-strings, where the outer tokenizer emits a single STRING token.
        text = self.mapped.text[start:end]
        tokens, diagnostic = _python_tokens(text, True)
        if diagnostic is not None:
            return None
        lines = _line_starts(text)
        names = [token for token in tokens if token.type == tokenize.NAME]
        if not names:
            return None
        token = names[-1]
        return start + lines[token.start[0] - 1] + token.start[1], start + lines[
            token.end[0] - 1
        ] + token.end[1]

    def collect_comment_targets(self, tree: ast.AST) -> None:
        statements = [node for node in ast.walk(tree) if isinstance(node, ast.stmt)]
        comments = sorted(
            (span for span in self.spans if span.role == "comment"),
            key=lambda span: span.start,
        )
        original_statements = []
        for statement in statements:
            start, end = self.node_interval(statement)
            if (
                isinstance(statement, ast.Expr)
                and self.node_interval(statement.value) in self.docstrings
            ):
                continue  # A docstring is not a future code prediction target.
            interval = self.mapped.interval(
                self.mapped.byte_starts[start], self.mapped.byte_starts[end]
            )
            if interval:
                original_statements.append(interval)
        original_statements.sort()
        statement_starts = [interval[0] for interval in original_statements]
        groups: list[tuple[int, int, str]] = []
        for comment in comments:
            line_start = self.source.rfind("\n", 0, comment.start) + 1
            prefix = self.source[line_start : comment.start]
            if prefix.strip():
                continue  # A trailing comment cannot explain preceding code.
            if (
                groups
                and groups[-1][2] == prefix
                and not self.source[groups[-1][1] : comment.start].strip()
            ):
                groups[-1] = (groups[-1][0], comment.end, prefix)
            else:
                groups.append((comment.start, comment.end, prefix))
        for comment_start, comment_end, prefix in groups:
            first_index = bisect.bisect_left(statement_starts, comment_end)
            for start, end in original_statements[first_index : first_index + 1]:
                between = self.source[comment_end:start]
                if between.strip():
                    break
                target_line = self.source.rfind("\n", 0, start) + 1
                if self.source[target_line:start] != prefix:
                    break
                self.comment_targets.append(
                    {
                        "comment_start": comment_start,
                        "comment_end": comment_end,
                        "target_start": start,
                        "target_end": end,
                    }
                )
                break
        self.comment_targets = list(
            {
                tuple(sorted(target.items())): target for target in self.comment_targets
            }.values()
        )


def _parser(language: str) -> Any:
    from tree_sitter import Language, Parser

    if language == "java":
        import tree_sitter_java as grammar
    elif language == "c":
        import tree_sitter_c as grammar
    else:
        import tree_sitter_cpp as grammar
    return Parser(Language(grammar.language()))


def _tree_analysis(
    source: str, language: str, allow_fragments: bool, allow_class_members: bool
) -> SourceAnalysis:
    parser = _parser(language)
    candidates = [("original", _MappedSource.wrap(source))]
    if language == "java" and (allow_class_members or allow_fragments):
        candidates.append(
            (
                "class_members",
                _MappedSource.wrap(source, "class __Fragment__ {\n", "\n}"),
            )
        )
    if allow_fragments:
        if language == "java":
            candidates.extend(
                [
                    (
                        "method_body",
                        _MappedSource.wrap(
                            source, "class __Fragment__ { void __body__() {\n", "\n} }"
                        ),
                    ),
                    (
                        "expression",
                        _MappedSource.wrap(
                            source, "class __Fragment__ { Object __value__ = ", "; }"
                        ),
                    ),
                ]
            )
        else:
            candidates.extend(
                [
                    (
                        "function_body",
                        _MappedSource.wrap(source, "void __fragment__() {\n", "\n}"),
                    ),
                    (
                        "expression",
                        _MappedSource.wrap(
                            source, "void __fragment__() { auto __value__ = ", "; }"
                        ),
                    ),
                ]
            )
    failures: list[str] = []
    for mode, mapped in candidates:
        tree = parser.parse(mapped.text.encode("utf-8"))
        if tree.root_node.has_error:
            errors = []
            stack = [tree.root_node]
            while stack and len(errors) < 4:
                node = stack.pop()
                if node.is_error or node.is_missing:
                    errors.append(
                        f"{node.type}@{node.start_point.row + 1}:{node.start_point.column + 1}"
                    )
                stack.extend(reversed(node.named_children))
            failures.append(f"{mode}: {', '.join(errors) or 'invalid syntax'}")
            continue
        collector = _TreeCollector(source, mapped, language)
        collector.collect(tree.root_node)
        return _finalize(
            source,
            collector.spans,
            set(ROLES),
            {
                "language": language,
                "parser": f"tree_sitter_{language}",
                "parse_mode": mode,
                "structural_available": True,
                "parse_diagnostics": failures,
                "comment_targets": collector.comment_targets,
            },
        )
    if not allow_fragments:
        raise SourceParseError("; ".join(failures))
    spans, lexical_diagnostic = _brace_lexical(source)
    return _finalize(
        source,
        spans,
        set(LEXICAL_ROLES) if lexical_diagnostic is None else set(),
        {
            "language": language,
            "parser": "lexical_fragment",
            "parse_mode": "lexical_fragment",
            "structural_available": False,
            "parse_diagnostics": failures,
            "tokenization_diagnostic": lexical_diagnostic,
            "comment_targets": [],
        },
    )


@dataclass(frozen=True)
class _TreeBinding:
    name: str
    scope_start: int
    scope_end: int
    visible_start: int
    depth: int
    declaration_start: int
    binding: str
    function_start: int


def _ancestors(node: Any) -> list[Any]:
    result = []
    while node.parent is not None:
        node = node.parent
        result.append(node)
    return result


class _TreeCollector:
    def __init__(self, source: str, mapped: _MappedSource, language: str) -> None:
        self.source = source
        self.mapped = mapped
        self.language = language
        self.encoded = mapped.text.encode("utf-8")
        self.spans: list[SourceSpan] = []
        self.bindings: list[_TreeBinding] = []
        self.bindings_by_name: dict[str, list[_TreeBinding]] = {}
        self.comment_targets: list[dict[str, int]] = []

    def text(self, node: Any) -> str:
        return self.encoded[node.start_byte : node.end_byte].decode("utf-8")

    def add(self, start: int, end: int, role: str, binding: str | None = None) -> None:
        interval = self.mapped.interval(start, end)
        if interval is not None:
            self.spans.append(SourceSpan(*interval, role, binding))

    def add_node(self, node: Any, role: str) -> None:
        if node is not None:
            self.add(node.start_byte, node.end_byte, role)

    def declarator_name(self, node: Any) -> Any | None:
        if node is None:
            return None
        if node.type == "identifier":
            return node
        declaration = node.child_by_field_name("declarator")
        if declaration is not None:
            return self.declarator_name(declaration)
        return None

    def add_binding(
        self,
        name: Any,
        scope: Any,
        visible_start: int | None = None,
        scope_end: int | None = None,
    ) -> None:
        if name is None or scope is None:
            return
        interval = self.mapped.interval(name.start_byte, name.end_byte)
        if interval is None:
            return
        self.bindings.append(
            _TreeBinding(
                self.text(name),
                scope.start_byte,
                scope.end_byte if scope_end is None else scope_end,
                name.start_byte if visible_start is None else visible_start,
                len(_ancestors(scope)),
                name.start_byte,
                f"{self.language}:local:{interval[0]}:{self.text(name)}",
                next(
                    (
                        node.start_byte
                        for node in [scope, *_ancestors(scope)]
                        if node.type
                        in {
                            "method_declaration",
                            "constructor_declaration",
                            "function_definition",
                        }
                    ),
                    -1,
                ),
            )
        )
        self.bindings_by_name.setdefault(self.text(name), []).append(self.bindings[-1])

    def collect_bindings(self, nodes: list[Any]) -> None:
        for node in nodes:
            ancestors = _ancestors(node)
            functions = [
                a
                for a in ancestors
                if a.type
                in {
                    "method_declaration",
                    "constructor_declaration",
                    "lambda_expression",
                    "function_definition",
                }
            ]
            if not functions:
                continue
            function = functions[0]
            if self.language == "java":
                if node.type in {
                    "formal_parameter",
                    "spread_parameter",
                    "catch_formal_parameter",
                }:
                    scope = next(
                        (a for a in ancestors if a.type == "catch_clause"), function
                    )
                    self.add_binding(
                        node.child_by_field_name("name"), scope, scope.start_byte
                    )
                elif (
                    node.type == "variable_declarator"
                    and node.parent.type == "local_variable_declaration"
                ):
                    scope = next(
                        (
                            a
                            for a in ancestors
                            if a.type in {"block", "for_statement", "switch_block"}
                        ),
                        None,
                    )
                    self.add_binding(node.child_by_field_name("name"), scope)
                elif node.type == "resource":
                    scope = next(
                        (
                            a
                            for a in ancestors
                            if a.type == "try_with_resources_statement"
                        ),
                        None,
                    )
                    if scope is not None:
                        self.add_binding(
                            node.child_by_field_name("name"),
                            scope,
                            scope_end=scope.child_by_field_name("body").end_byte,
                        )
                elif node.type == "enhanced_for_statement":
                    body = node.child_by_field_name("body")
                    self.add_binding(
                        node.child_by_field_name("name"), node, body.start_byte
                    )
                    # Its declaration occurrence itself is recorded separately.
                elif (
                    node.type == "inferred_parameters"
                    and node.parent.type == "lambda_expression"
                ):
                    for name in node.named_children:
                        if name.type == "identifier":
                            self.add_binding(name, node.parent, node.parent.start_byte)
                elif (
                    node.type == "identifier"
                    and node.parent.type == "lambda_expression"
                    and node.parent.child_by_field_name("parameters") == node
                ):
                    self.add_binding(node, node.parent, node.parent.start_byte)
            else:
                if node.type in {
                    "parameter_declaration",
                    "optional_parameter_declaration",
                }:
                    self.add_binding(
                        self.declarator_name(node.child_by_field_name("declarator")),
                        function,
                        function.start_byte,
                    )
                elif node.type in {"declaration", "for_range_loop"}:
                    scope = next(
                        (
                            a
                            for a in ancestors
                            if a.type
                            in {"compound_statement", "for_statement", "for_range_loop"}
                        ),
                        None,
                    )
                    if node.type == "for_range_loop":
                        scope = node
                    for index, child in enumerate(node.children):
                        # Local function prototypes are not variable bindings.
                        if (
                            node.field_name_for_child(index) == "declarator"
                            and child.type != "function_declarator"
                        ):
                            self.add_binding(self.declarator_name(child), scope)

    def identifier_binding(self, node: Any) -> str | None:
        parent = node.parent
        if parent is None:
            return None
        if self.language == "java":
            excluded_fields = {
                "name": {
                    "method_declaration",
                    "constructor_declaration",
                    "method_invocation",
                    "class_declaration",
                    "interface_declaration",
                    "enum_declaration",
                },
                "field": {"field_access"},
            }
            for field_name, types in excluded_fields.items():
                if (
                    parent.type in types
                    and parent.child_by_field_name(field_name) == node
                ):
                    return None
            if parent.type in {
                "scoped_identifier",
                "scoped_type_identifier",
                "import_declaration",
                "package_declaration",
            }:
                return None
        else:
            if (
                parent.type
                in {
                    "field_expression",
                    "qualified_identifier",
                    "namespace_definition",
                }
                and parent.child_by_field_name("argument") != node
            ):
                return None
            if (
                parent.type == "function_declarator"
                and parent.child_by_field_name("declarator") == node
            ):
                return None
        name = self.text(node)
        function_start = next(
            (
                ancestor.start_byte
                for ancestor in _ancestors(node)
                if ancestor.type
                in {
                    "method_declaration",
                    "constructor_declaration",
                    "function_definition",
                }
            ),
            -1,
        )
        matches = [
            binding
            for binding in self.bindings_by_name.get(name, [])
            if binding.function_start == function_start
            and binding.scope_start <= node.start_byte < binding.scope_end
            and (
                node.start_byte >= binding.visible_start
                or node.start_byte == binding.declaration_start
            )
        ]
        return (
            max(
                matches, key=lambda binding: (binding.depth, binding.declaration_start)
            ).binding
            if matches
            else None
        )

    def collect(self, root: Any) -> None:
        nodes = []
        stack = [root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            stack.extend(reversed(node.named_children))
        self.collect_bindings(nodes)
        literals = {
            "decimal_integer_literal",
            "hex_integer_literal",
            "octal_integer_literal",
            "binary_integer_literal",
            "decimal_floating_point_literal",
            "hex_floating_point_literal",
            "string_literal",
            "character_literal",
            "true",
            "false",
            "null_literal",
            "number_literal",
            "char_literal",
            "raw_string_literal",
            "concatenated_string",
            "nullptr",
        }
        declaration_types = {
            "method_declaration",
            "constructor_declaration",
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
            "function_definition",
            "struct_specifier",
            "class_specifier",
        }
        body_fields = ("body", "consequence")
        for node in nodes:
            kind = node.type
            if kind in {"identifier", "field_identifier", "type_identifier"}:
                contextual_var = (
                    self.language == "java"
                    and kind == "type_identifier"
                    and self.text(node) == "var"
                    and node.parent.type
                    in {
                        "local_variable_declaration",
                        "enhanced_for_statement",
                        "resource",
                    }
                    and node.parent.child_by_field_name("type") == node
                )
                if not contextual_var:
                    self.add(
                        node.start_byte,
                        node.end_byte,
                        "identifier",
                        self.identifier_binding(node) if kind == "identifier" else None,
                    )
            elif kind in {"line_comment", "block_comment", "comment"}:
                self.add_node(node, "comment")
            elif kind in literals:
                self.add_node(node, "literal")
            if kind in declaration_types:
                body = node.child_by_field_name("body")
                if body is not None:
                    end = body.start_byte
                    while (
                        end > node.start_byte
                        and self.encoded[end - 1 : end] in b" \t\r\n"
                    ):
                        end -= 1
                    self.add(node.start_byte, end, "declaration_header")
                elif kind in {"method_declaration", "constructor_declaration"}:
                    end = node.end_byte
                    while (
                        end > node.start_byte
                        and self.encoded[end - 1 : end] in b" \t\r\n;"
                    ):
                        end -= 1
                    self.add(node.start_byte, end, "declaration_header")
            elif kind in {
                "local_variable_declaration",
                "field_declaration",
                "declaration",
            }:
                # Every declarator is bounded separately and excludes its value.
                declarators = [
                    child
                    for i, child in enumerate(node.children)
                    if node.field_name_for_child(i) == "declarator"
                ]
                for index, declarator in enumerate(declarators):
                    value = declarator.child_by_field_name("value")
                    end = value.start_byte if value is not None else declarator.end_byte
                    while (
                        end > declarator.start_byte
                        and self.encoded[end - 1 : end] in b" \t\r\n="
                    ):
                        end -= 1
                    self.add(
                        node.start_byte if index == 0 else declarator.start_byte,
                        end,
                        "declaration_header",
                    )
            elif kind == "resource":
                name = node.child_by_field_name("name")
                if name is not None:
                    self.add(node.start_byte, name.end_byte, "declaration_header")
            if kind == "method_invocation":
                self.add_node(node.child_by_field_name("name"), "call_target")
            elif kind == "object_creation_expression":
                self.add_node(node.child_by_field_name("type"), "call_target")
            elif kind == "call_expression":
                function = node.child_by_field_name("function")
                if function is not None and function.type == "field_expression":
                    function = function.child_by_field_name("field")
                if function is not None and function.type in {
                    "identifier",
                    "field_identifier",
                    "qualified_identifier",
                    "template_function",
                    "template_method",
                }:
                    self.add_node(function, "call_target")
            elif kind == "new_expression":
                self.add_node(node.child_by_field_name("type"), "call_target")
            if kind in {
                "assignment_expression",
                "variable_declarator",
                "init_declarator",
                "resource",
            }:
                self.add_node(
                    node.child_by_field_name("right")
                    or node.child_by_field_name("value"),
                    "assignment_rhs",
                )
            if kind in {"binary_expression", "unary_expression", "update_expression"}:
                operator = node.child_by_field_name("operator")
                if (
                    kind == "unary_expression"
                    and operator is not None
                    and self.language != "java"
                    and self.text(operator) in {"*", "&"}
                ):
                    continue  # Address-taking/dereference is not bitwise arithmetic.
                self.add_node(node, "expression")
            elif kind == "assignment_expression":
                operator = node.child_by_field_name("operator")
                if operator is not None and self.text(operator) != "=":
                    self.add_node(node, "expression")
            if kind in {
                "if_statement",
                "while_statement",
                "for_statement",
                "enhanced_for_statement",
                "for_range_loop",
                "switch_statement",
                "switch_expression",
                "catch_clause",
                "synchronized_statement",
                "try_statement",
                "try_with_resources_statement",
            }:
                body = next(
                    (
                        node.child_by_field_name(field_name)
                        for field_name in body_fields
                        if node.child_by_field_name(field_name) is not None
                    ),
                    None,
                )
                if body is not None:
                    end = body.start_byte
                    while (
                        end > node.start_byte
                        and self.encoded[end - 1 : end] in b" \t\r\n"
                    ):
                        end -= 1
                    self.add(node.start_byte, end, "control_header")
            elif kind == "finally_clause":
                body = next(
                    (child for child in node.named_children if child.type == "block"),
                    None,
                )
                if body is not None:
                    end = body.start_byte
                    while (
                        end > node.start_byte
                        and self.encoded[end - 1 : end] in b" \t\r\n"
                    ):
                        end -= 1
                    self.add(node.start_byte, end, "control_header")
            elif kind == "do_statement":
                # The body precedes its predicate; never include that body.
                condition = node.child_by_field_name("condition")
                if condition is not None:
                    start = self.encoded.rfind(
                        b"while", node.start_byte, condition.start_byte
                    )
                    if start >= 0:
                        self.add(start, node.end_byte, "control_header")
            elif kind in {
                "return_statement",
                "throw_statement",
                "break_statement",
                "continue_statement",
                "goto_statement",
                "yield_statement",
                "assert_statement",
            }:
                self.add_node(node, "control_header")
        self.collect_comment_targets(nodes)

    def collect_comment_targets(self, nodes: list[Any]) -> None:
        comment_types = {"line_comment", "block_comment", "comment"}
        for node in nodes:
            if node.type not in {
                "program",
                "translation_unit",
                "block",
                "compound_statement",
                "class_body",
                "declaration_list",
            }:
                continue
            children = node.named_children
            handled_through = -1
            for index, child in enumerate(children):
                if index <= handled_through:
                    continue
                if child.type not in comment_types:
                    continue
                comment = self.mapped.interval(child.start_byte, child.end_byte)
                if comment is None:
                    continue
                line = self.source.rfind("\n", 0, comment[0]) + 1
                if self.source[line : comment[0]].strip():
                    continue
                final_index = index
                while (
                    final_index + 1 < len(children)
                    and children[final_index + 1].type in comment_types
                ):
                    final_index += 1
                handled_through = final_index
                if final_index + 1 >= len(children):
                    continue
                target_node = children[final_index + 1]
                if not (
                    target_node.type.endswith("statement")
                    or "declaration" in target_node.type
                    or target_node.type == "function_definition"
                ):
                    continue
                final_comment = self.mapped.interval(
                    children[final_index].start_byte, children[final_index].end_byte
                )
                target = self.mapped.interval(
                    target_node.start_byte, target_node.end_byte
                )
                if (
                    target
                    and final_comment
                    and not self.source[final_comment[1] : target[0]].strip()
                ):
                    self.comment_targets.append(
                        {
                            "comment_start": comment[0],
                            "comment_end": final_comment[1],
                            "target_start": target[0],
                            "target_end": target[1],
                        }
                    )


_BRACE_KEYWORDS = {
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
    "true",
    "false",
    "null",
    "record",
    "sealed",
    "permits",
    "var",
    "yield",
    "auto",
    "register",
    "signed",
    "sizeof",
    "struct",
    "typedef",
    "union",
    "unsigned",
    "_Bool",
    "inline",
    "restrict",
    "namespace",
    "template",
    "typename",
    "using",
    "virtual",
    "explicit",
    "friend",
    "operator",
    "bool",
    "wchar_t",
    "nullptr",
    "delete",
    "dynamic_cast",
    "static_cast",
    "reinterpret_cast",
    "const_cast",
    "constexpr",
    "consteval",
    "constinit",
    "decltype",
    "noexcept",
    "thread_local",
    "alignas",
    "alignof",
    "co_await",
    "co_return",
    "co_yield",
}
_BRACE_KEYWORDS.update(
    [
        "__global__",
        "__device__",
        "__host__",
        "__shared__",
        "__constant__",
        "__managed__",
        "__restrict__",
        "__launch_bounds__",
        "__align__",
        "__noinline__",
        "__forceinline__",
    ]
)
_BRACE_LEXEME = re.compile(
    r"(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)"
    r'|(?P<string>"""[\s\S]*?"""|(?:u8|[LuU])?"(?:\\[\s\S]|[^"\\])*"|(?:[LuU])?\'(?:\\[\s\S]|[^\'\\])*\')'
    r"|(?P<number>\b(?:0[xX][\da-fA-F]+|0[bB][01]+|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)[uUlLfFdD]*\b)"
    r"|(?P<name>[^\W\d][\w$]*|\$[\w$]+)",
    re.UNICODE,
)


def _brace_lexical(source: str) -> tuple[list[SourceSpan], str | None]:
    spans = []
    cursor = 0
    for match in _BRACE_LEXEME.finditer(source):
        # An unterminated string/comment is not identifier-rich ordinary code.
        gap = source[cursor : match.start()]
        if '"' in gap or "'" in gap or "/*" in gap:
            return spans, f"Unterminated lexical construct after character {cursor}"
        kind = match.lastgroup
        value = match.group()
        if kind == "comment":
            role = "comment"
        elif kind in {"string", "number"} or value in {
            "true",
            "false",
            "null",
            "nullptr",
        }:
            role = "literal"
        elif value not in _BRACE_KEYWORDS:
            role = "identifier"
        else:
            cursor = match.end()
            continue
        spans.append(SourceSpan(match.start(), match.end(), role))
        cursor = match.end()
    gap = source[cursor:]
    diagnostic = (
        f"Unterminated lexical construct after character {cursor}"
        if any(marker in gap for marker in ('"', "'", "/*"))
        else None
    )
    return spans, diagnostic
