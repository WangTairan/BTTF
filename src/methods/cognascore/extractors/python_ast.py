from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from collections.abc import Iterable

from ..lexeme import LexemeChunk


class PythonAstLexemeExtractor:
    """Strict Python extractor implementing the shared CognaScore taxonomy."""

    MAX_LEXEME_CHARS = 256
    REGEX_CALLS = {
        "compile",
        "findall",
        "finditer",
        "fullmatch",
        "match",
        "search",
        "split",
        "sub",
        "subn",
    }
    FRAGMENT_TOKEN_RE = re.compile(
        r"\#[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|"
        r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b|\b[A-Za-z_]\w*\b|"
        r"\*\*=|//=|<<=|>>=|==|!=|<=|>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|"
        r"\*\*|//|<<|>>|:=|->|[+\-*/%@&|^~<>=()]"
    )

    def __init__(self, *, allow_fragments: bool = False) -> None:
        self.allow_fragments = allow_fragments

    def require_parser(self) -> None:
        return None

    def extract(self, source: str) -> list[LexemeChunk]:
        tree = ast.parse(source)
        chunks = self._extract_comments(source)
        docstring_nodes = self._docstring_nodes(tree)

        used_names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
        for node in ast.walk(tree):
            chunks.extend(self._chunks_for_node(node, used_names, docstring_nodes))
        return chunks

    def extract_with_member_fallback(self, source: str) -> tuple[list[LexemeChunk], bool]:
        chunks, mode = self.extract_with_fallback_mode(source)
        return chunks, mode != "direct_python_ast"

    def extract_with_fallback_mode(self, source: str) -> tuple[list[LexemeChunk], str]:
        try:
            return self.extract(source), "direct_python_ast"
        except SyntaxError:
            if not self.allow_fragments:
                raise
        return self._extract_lexical_fragment(source), "python_lexical_fragment"

    def _extract_lexical_fragment(self, source: str) -> list[LexemeChunk]:
        """Lexically scan an explicitly declared snippet without accepting it as an AST."""
        chunks: list[LexemeChunk] = []
        control_words = {
            "if", "elif", "else", "for", "while", "try", "except", "finally",
            "with", "return", "raise", "break", "continue", "yield", "async",
            "await",
        }
        declaration_words = {"def", "class", "lambda"}
        logical_words = {"and", "or", "not"}
        comparison_words = {"in", "is"}
        assignment_ops = {"=", "+=", "-=", "*=", "/=", "//=", "%=", "**=", "&=", "|=", "^="}
        arithmetic_ops = {"+", "-", "*", "/", "//", "%", "**", "@"}
        bitwise_ops = {"&", "|", "^", "~", "<<", ">>"}
        comparison_ops = {"==", "!=", "<", ">", "<=", ">="}

        for line_number, line in enumerate(source.splitlines(), start=1):
            tokens = self.FRAGMENT_TOKEN_RE.findall(line)
            for index, text in enumerate(tokens):
                next_text = tokens[index + 1] if index + 1 < len(tokens) else ""
                if text.startswith("#"):
                    self._add(chunks, ["comment", text[1:]], line_number, "COMMENT")
                    break
                if text[0].isdigit() or text.startswith(("\"", "'")):
                    self._add(chunks, ["literal", text], line_number, "LITERAL")
                    continue
                if re.fullmatch(r"[A-Za-z_]\w*", text):
                    kind = "IDENTIFIER"
                    value: str | Iterable[str] = text
                    if text in control_words:
                        kind = "CONTROL_FLOW"
                    elif text in declaration_words:
                        kind = "DECLARATION"
                    elif text in logical_words:
                        kind = "LOGICAL"
                    elif text in comparison_words:
                        kind = "COMPARISON"
                    elif text in {"True", "False", "None"}:
                        kind, value = "LITERAL", ["literal", text]
                    elif next_text == "(":
                        kind, value = "CALL", ["call", text]
                    self._add(chunks, value, line_number, kind)
                    continue
                if text in assignment_ops:
                    kind = "ASSIGNMENT"
                elif text in arithmetic_ops:
                    kind = "ARITHMETIC"
                elif text in bitwise_ops:
                    kind = "BITWISE"
                elif text in comparison_ops:
                    kind = "COMPARISON"
                else:
                    continue
                self._add(chunks, text, line_number, kind)
        if not chunks:
            raise SyntaxError("Declared Python fragment produced no cognitive chunks")
        return chunks

    def _chunks_for_node(
        self,
        node: ast.AST,
        used_names: set[str],
        docstring_nodes: set[int],
    ) -> list[LexemeChunk]:
        line = int(getattr(node, "lineno", 1))
        chunks: list[LexemeChunk] = []

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parameters = [argument.arg for argument in self._function_arguments(node.args)]
            self._add(chunks, ["def", node.name, *parameters], line, "DECLARATION")
            self._add(chunks, node.name, line, "IDENTIFIER")
        elif isinstance(node, ast.ClassDef):
            self._add(chunks, ["class", node.name], line, "DECLARATION")
            self._add(chunks, node.name, line, "IDENTIFIER")
        elif isinstance(node, ast.arg):
            self._add(chunks, node.arg, line, "IDENTIFIER")
        elif isinstance(node, ast.Name):
            self._add(chunks, node.id, line, "IDENTIFIER")
        elif isinstance(node, ast.Attribute):
            self._add(chunks, node.attr, line, "IDENTIFIER")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            chunks.extend(self._import_chunks(node, used_names))
        elif isinstance(node, ast.Call):
            self._add(chunks, ["call", self._expression(node.func)], line, "CALL")
            chunks.extend(self._regex_chunks(node))
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            self._add(chunks, ["assign", self._expression(node)], line, "ASSIGNMENT")
        elif isinstance(node, ast.BinOp):
            kind = "BITWISE" if isinstance(
                node.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)
            ) else "ARITHMETIC"
            self._add(chunks, self._expression(node), line, kind)
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                kind = "LOGICAL"
            elif isinstance(node.op, ast.Invert):
                kind = "BITWISE"
            else:
                kind = "ARITHMETIC"
            self._add(chunks, self._expression(node), line, kind)
        elif isinstance(node, ast.BoolOp):
            self._add(chunks, self._expression(node), line, "LOGICAL")
        elif isinstance(node, ast.Compare):
            self._add(chunks, self._expression(node), line, "COMPARISON")
        elif isinstance(node, self._control_flow_types()):
            self._add(chunks, [node.__class__.__name__.lower(), self._control_subject(node)], line, "CONTROL_FLOW")
        elif isinstance(node, ast.Constant):
            if id(node) in docstring_nodes:
                self._add(chunks, ["comment", node.value], line, "COMMENT")
            else:
                self._add(chunks, ["literal", repr(node.value)], line, "LITERAL")
        return chunks

    def _import_chunks(
        self,
        node: ast.Import | ast.ImportFrom,
        used_names: set[str],
    ) -> list[LexemeChunk]:
        chunks: list[LexemeChunk] = []
        module = node.module if isinstance(node, ast.ImportFrom) else None
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            binding = alias.asname or (
                alias.name if isinstance(node, ast.ImportFrom) else alias.name.split(".", 1)[0]
            )
            root = (module or alias.name).split(".", 1)[0]
            origin = "stdlib" if root in sys.stdlib_module_names else "external"
            used = alias.name == "*" or binding in used_names
            chunk_type = "IMPORT" if used else "UNUSED_IMPORT"
            prefix = "import" if used else "unused_import"
            self._add(
                chunks,
                [prefix, origin, full_name.replace(".", "_")],
                int(getattr(node, "lineno", 1)),
                chunk_type,
            )
        return chunks

    def _regex_chunks(self, node: ast.Call) -> list[LexemeChunk]:
        if not (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"re", "regex"}
        ):
            return []
        name = self._call_name(node.func)
        if name not in self.REGEX_CALLS or not node.args:
            return []
        pattern = node.args[0]
        if not isinstance(pattern, ast.Constant) or not isinstance(pattern.value, str):
            return []
        chunks: list[LexemeChunk] = []
        self._add(chunks, ["regex", pattern.value], int(getattr(node, "lineno", 1)), "REGEX")
        return chunks

    def _extract_comments(self, source: str) -> list[LexemeChunk]:
        chunks: list[LexemeChunk] = []
        stream = io.StringIO(source).readline
        for token in tokenize.generate_tokens(stream):
            if token.type == tokenize.COMMENT:
                self._add(chunks, ["comment", token.string[1:]], token.start[0], "COMMENT")
        return chunks

    def _docstring_nodes(self, tree: ast.AST) -> set[int]:
        result: set[int] = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr):
                value = body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    result.add(id(value))
        return result

    @staticmethod
    def _function_arguments(arguments: ast.arguments) -> Iterable[ast.arg]:
        yield from arguments.posonlyargs
        yield from arguments.args
        if arguments.vararg is not None:
            yield arguments.vararg
        yield from arguments.kwonlyargs
        if arguments.kwarg is not None:
            yield arguments.kwarg

    @staticmethod
    def _control_flow_types() -> tuple[type[ast.AST], ...]:
        types: list[type[ast.AST]] = [
            ast.If,
            ast.For,
            ast.AsyncFor,
            ast.While,
            ast.Try,
            ast.With,
            ast.AsyncWith,
            ast.Return,
            ast.Raise,
            ast.Break,
            ast.Continue,
            ast.Yield,
            ast.YieldFrom,
            ast.Await,
        ]
        if hasattr(ast, "Match"):
            types.append(ast.Match)
        if hasattr(ast, "TryStar"):
            types.append(ast.TryStar)
        return tuple(types)

    def _control_subject(self, node: ast.AST) -> str:
        for attribute in ("test", "iter", "subject", "value", "exc"):
            value = getattr(node, attribute, None)
            if isinstance(value, ast.AST):
                return self._expression(value)
        return ""

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def _expression(self, node: ast.AST) -> str:
        return ast.unparse(node)

    def _add(
        self,
        chunks: list[LexemeChunk],
        value: str | Iterable[str],
        line: int,
        chunk_type: str,
    ) -> None:
        parts = [value] if isinstance(value, str) else list(value)
        normalized = "_".join(self._normalize(part) for part in parts if str(part).strip())
        if normalized:
            chunks.append(
                LexemeChunk(
                    lexeme=normalized[: self.MAX_LEXEME_CHARS],
                    line=max(int(line), 1),
                    type=chunk_type,
                )
            )

    @staticmethod
    def _normalize(value: object) -> str:
        text = re.sub(r"\s+", "_", str(value).strip())
        return re.sub(r"_+", "_", text).strip("_")
