from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Iterable

from ...lexeme import LexemeChunk

try:
    import javalang
except ImportError:  # pragma: no cover
    javalang = None


class LexemeExtractor:
    MAX_LEXEME_CHARS = 256

    IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([^;]+);")
    MEMBER_SNIPPET_PREFIX = "class Snippet {\n"
    MEMBER_SNIPPET_SUFFIX = "\n}\n"
    METHOD_BODY_SNIPPET_PREFIX = "class Snippet {\nvoid __snippet__() {\n"
    METHOD_BODY_SNIPPET_SUFFIX = "\n}\n}\n"
    FALLBACK_TOKEN_RE = re.compile(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
        r'\b(?:0[xX][0-9A-Fa-f]+|\d+(?:\.\d+)?)\b|'
        r'\b[A-Za-z_]\w*\b|'
        r'==|!=|<=|>=|&&|\|\||<<|>>|\+\+|--|\+=|-=|\*=|/=|%=|'
        r'[()+\-*/%<>&|^~=!]'
    )
    CONTROL_WORDS = {
        "if", "else", "for", "while", "do", "switch", "case", "catch", "try",
        "return", "break", "continue",
    }
    DECLARATION_WORDS = {
        "class", "struct", "enum", "interface", "def", "function", "void", "int",
        "long", "short", "float", "double", "char", "bool", "boolean", "string", "String",
    }
    MODIFIER_WORDS = {
        "public", "private", "protected", "static", "final", "abstract", "native",
        "synchronized", "volatile", "transient", "const", "unsigned", "signed",
        "extern", "inline", "__global__", "__device__", "__host__",
    }

    def require_parser(self) -> None:
        self._require_parser()

    def extract(self, source: str) -> list[LexemeChunk]:
        self._require_parser()
        tree = javalang.parse.parse(source)

        chunks: list[LexemeChunk] = []
        chunks.extend(self._extract_imports(source))
        chunks.extend(self._extract_comments(source))
        chunks.extend(self._extract_ast(tree))
        return chunks

    def extract_with_member_fallback(self, source: str) -> tuple[list[LexemeChunk], bool]:
        chunks, mode = self.extract_with_fallback_mode(source)
        return chunks, mode != "direct_ast"

    def extract_with_fallback_mode(self, source: str) -> tuple[list[LexemeChunk], str]:
        """Extract chunks and return the parsing mode used for diagnostics."""
        self._require_parser()
        parse_errors = (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError, TypeError)
        try:
            return self.extract(source), "direct_ast"
        except parse_errors as initial_error:
            for mode, prefix, suffix, line_offset in (
                ("member_ast", self.MEMBER_SNIPPET_PREFIX, self.MEMBER_SNIPPET_SUFFIX, 1),
                ("method_body_ast", self.METHOD_BODY_SNIPPET_PREFIX, self.METHOD_BODY_SNIPPET_SUFFIX, 2),
            ):
                try:
                    wrapped_chunks = self.extract(prefix + source + suffix)
                except parse_errors:
                    continue
                chunks = [
                    replace(chunk, line=chunk.line - line_offset)
                    for chunk in wrapped_chunks
                    if chunk.line > line_offset
                ]
                if chunks:
                    return chunks, mode
            chunks = self._extract_lexical_fallback(source)
            if not chunks:
                raise initial_error
            return chunks, "lexical"

    def _extract_lexical_fallback(self, source: str) -> list[LexemeChunk]:
        """Extract language-neutral semantic chunks from incomplete or non-Java code."""
        chunks = self._extract_comments(source)
        masked = self._mask_comments(source)
        logical = {"&&", "||", "!"}
        comparison = {"==", "!=", "<", ">", "<=", ">="}
        bitwise = {"&", "|", "^", "~", "<<", ">>"}
        arithmetic = {"+", "-", "*", "/", "%", "++", "--"}
        assignments = {"=", "+=", "-=", "*=", "/=", "%="}
        for line_no, line in enumerate(masked.splitlines(), start=1):
            tokens = self.FALLBACK_TOKEN_RE.findall(line)
            for index, token in enumerate(tokens):
                next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
                if token in {"(", ")"}:
                    continue
                if token in self.CONTROL_WORDS:
                    kind, lexeme = "CONTROL_FLOW", token
                elif token in self.DECLARATION_WORDS:
                    kind, lexeme = "DECLARATION", token
                elif token in self.MODIFIER_WORDS:
                    continue
                elif token in logical:
                    kind, lexeme = "LOGICAL", token
                elif token in comparison:
                    kind, lexeme = "COMPARISON", token
                elif token in bitwise:
                    kind, lexeme = "BITWISE", token
                elif token in arithmetic:
                    kind, lexeme = "ARITHMETIC", token
                elif token in assignments:
                    kind, lexeme = "ASSIGNMENT", token
                elif token.startswith(('"', "'")) or token[0].isdigit():
                    kind, lexeme = "LITERAL", f"literal_{self._normalize(token)}"
                elif next_token == "(" and token not in self.CONTROL_WORDS:
                    kind, lexeme = "CALL", f"call_{self._normalize(token)}"
                else:
                    kind, lexeme = "IDENTIFIER", self._normalize(token)
                self._add(chunks, lexeme, line_no, kind)
        return chunks

    def _require_parser(self) -> None:
        if javalang is None:
            raise RuntimeError(
                "Missing dependency: javalang. Install it with "
                "`python3 -m pip install -r requirements.txt`."
            )

    def _extract_imports(self, source: str) -> list[LexemeChunk]:
        masked = self._mask_comments(source)
        code_without_imports = "\n".join(
            "" if self.IMPORT_RE.match(line) else line for line in masked.splitlines()
        )

        chunks: list[LexemeChunk] = []
        for line_no, line in enumerate(source.splitlines(), start=1):
            match = self.IMPORT_RE.match(line)
            if not match:
                continue
            imported = match.group(1).strip()
            category = "stdlib" if imported.startswith(("java.", "javax.")) else "external"
            parts = imported.split(".")
            base = f"{parts[-2]}_{parts[-1]}" if len(parts) >= 2 else parts[0]
            used = self._import_is_used(imported, code_without_imports)
            prefix = "import" if used else "unused_import"
            kind = "IMPORT" if used else "UNUSED_IMPORT"
            self._add(chunks, f"{prefix}_{category}_{base}", line_no, kind)
        return chunks

    def _import_is_used(self, imported: str, code_without_imports: str) -> bool:
        if imported.endswith(".*"):
            package = imported[:-2]
            if package == "java.lang":
                return True
            simple_names = {
                "java.lang": {"String", "StringBuilder", "Math", "Integer", "Double", "Boolean", "Character", "Object"},
                "java.util": {"List", "ArrayList", "Map", "HashMap", "Set", "HashSet", "Queue", "PriorityQueue", "Collections"},
                "java.util.regex": {"Pattern", "Matcher"},
                "java.io": {"File", "InputStream", "OutputStream", "Reader", "Writer", "BufferedReader", "IOException"},
                "java.math": {"BigInteger", "BigDecimal"},
            }.get(package, set())
            return any(re.search(rf"\b{re.escape(name)}\b", code_without_imports) for name in simple_names)
        simple_name = imported.rsplit(".", 1)[-1]
        return re.search(rf"\b{re.escape(simple_name)}\b", code_without_imports) is not None

    def _extract_comments(self, source: str) -> list[LexemeChunk]:
        chunks: list[LexemeChunk] = []
        for kind, start, end, line in self._comment_spans(source):
            if kind == "line":
                lexeme = self._comment_normalize(source[start + 2:end])
                self._add(chunks, f"comment_{lexeme}", line, "COMMENT")
                continue

            closing_chars = 2 if source[max(start, end - 2):end] == "*/" else 0
            raw = source[start + 2:end - closing_chars]
            for line_offset, raw_line in enumerate(raw.split("\n")):
                comment_line = re.sub(r"^\s*\*+", "", raw_line).strip()
                if not comment_line:
                    continue
                lexeme = self._comment_normalize(comment_line)
                self._add(chunks, f"comment_{lexeme}", line + line_offset, "COMMENT")
        return chunks

    def _comment_spans(self, source: str) -> list[tuple[str, int, int, int]]:
        """Return real Java/C-like comments, excluding markers inside literals."""

        spans: list[tuple[str, int, int, int]] = []
        index = 0
        line = 1
        while index < len(source):
            if source.startswith('"""', index):
                end = self._skip_quoted_literal(source, index, '"""')
                line += source[index:end].count("\n")
                index = end
                continue
            if source[index] in {'"', "'"}:
                end = self._skip_quoted_literal(source, index, source[index])
                line += source[index:end].count("\n")
                index = end
                continue
            if source.startswith("//", index):
                end = source.find("\n", index + 2)
                end = len(source) if end < 0 else end
                spans.append(("line", index, end, line))
                index = end
                continue
            if source.startswith("/*", index):
                closing = source.find("*/", index + 2)
                end = len(source) if closing < 0 else closing + 2
                spans.append(("block", index, end, line))
                line += source[index:end].count("\n")
                index = end
                continue
            if source[index] == "\n":
                line += 1
            index += 1
        return spans

    def _skip_quoted_literal(self, source: str, start: int, delimiter: str) -> int:
        index = start + len(delimiter)
        while index < len(source):
            if source.startswith(delimiter, index):
                return index + len(delimiter)
            if source[index] == "\\":
                index = min(index + 2, len(source))
            else:
                index += 1
        return len(source)

    def _extract_ast(self, tree) -> list[LexemeChunk]:
        chunks: list[LexemeChunk] = []
        self._walk(tree, chunks)
        return chunks

    def _walk(self, node, chunks: list[LexemeChunk]) -> None:
        if node is None or not self._is_node(node):
            return

        node_type = node.__class__.__name__
        if node_type == "Import":
            return

        handler = getattr(self, f"_handle_{node_type}", None)
        handled_children = False
        if handler is not None:
            handled_children = bool(handler(node, chunks))

        if not handled_children:
            for child in self._children(node):
                self._walk(child, chunks)

    def _handle_MethodDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        line = self._line(node)
        name = self._normalize(node.name)
        params = [self._normalize(param.name) for param in node.parameters or []]
        self._add(chunks, ["def", name, *params], line, "DECLARATION")
        self._add(chunks, name, line, "IDENTIFIER")
        for child in self._children(node):
            self._walk(child, chunks)
        return True

    def _handle_ClassDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        return self._handle_type_declaration(node, chunks, "class")

    def _handle_InterfaceDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        return self._handle_type_declaration(node, chunks, "interface")

    def _handle_EnumDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        return self._handle_type_declaration(node, chunks, "enum")

    def _handle_type_declaration(self, node, chunks: list[LexemeChunk], kind_name: str) -> bool:
        line = self._line(node)
        name = self._normalize(getattr(node, "name", ""))
        extends = self._type_to_str(getattr(node, "extends", None))
        implements = [self._type_to_str(item) for item in getattr(node, "implements", None) or []]
        self._add(chunks, name, line, "IDENTIFIER")
        self._add(chunks, [kind_name, name, extends, *implements], line, "DECLARATION")
        for child in self._children(node):
            self._walk(child, chunks)
        return True

    def _handle_ConstructorDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        line = self._line(node)
        name = self._normalize(getattr(node, "name", ""))
        params = [self._normalize(param.name) for param in getattr(node, "parameters", None) or []]
        self._add(chunks, ["constructor", name, *params], line, "DECLARATION")
        self._add(chunks, name, line, "IDENTIFIER")
        for child in self._children(node):
            self._walk(child, chunks)
        return True

    def _handle_FieldDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        type_name = self._type_to_str(getattr(node, "type", None))
        line = self._line(node)
        for declarator in getattr(node, "declarators", None) or []:
            name = self._normalize(declarator.name)
            declarator_line = self._line(declarator, line)
            self._add(chunks, name, declarator_line, "IDENTIFIER")
            self._add(chunks, [type_name, name], declarator_line, "DECLARATION")
            if declarator.initializer is not None:
                self._add(chunks, f"def_{name}", declarator_line, "DECLARATION")
                self._add(chunks, f"def_{name}_{self._expr(declarator.initializer)}", declarator_line, "DECLARATION")
                self._walk(declarator.initializer, chunks)
        return True

    def _handle_FormalParameter(self, node, chunks: list[LexemeChunk]) -> bool:
        line = self._line(node)
        name = self._normalize(node.name)
        type_name = self._type_to_str(node.type)
        self._add(chunks, name, line, "IDENTIFIER")
        self._add(chunks, [type_name, name], line, "DECLARATION")
        return True

    def _handle_LocalVariableDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        type_name = self._type_to_str(node.type)
        line = self._line(node)
        for declarator in node.declarators or []:
            name = self._normalize(declarator.name)
            self._add(chunks, name, self._line(declarator, line), "IDENTIFIER")
            self._add(chunks, [type_name, name], self._line(declarator, line), "DECLARATION")
            if declarator.initializer is not None:
                self._add(chunks, f"def_{name}", self._line(declarator, line), "DECLARATION")
                self._add(chunks, f"def_{name}_{self._expr(declarator.initializer)}", self._line(declarator, line), "DECLARATION")
                self._walk(declarator.initializer, chunks)
        return True

    def _handle_VariableDeclarator(self, node, chunks: list[LexemeChunk]) -> bool:
        return True

    def _handle_MemberReference(self, node, chunks: list[LexemeChunk]) -> bool:
        line = self._line(node)
        name = self._normalize(node.member)
        qualifier = self._normalize(getattr(node, "qualifier", ""))
        static_like_qualifier = bool(qualifier) and qualifier[0].isupper()
        if name and not static_like_qualifier:
            self._add(chunks, name, line, "IDENTIFIER")
        for op in node.prefix_operators or []:
            self._add(chunks, f"{op}{name}", line, "BITWISE" if op == "~" else "ARITHMETIC")
        for op in node.postfix_operators or []:
            self._add(chunks, f"{name}{op}", line, "ARITHMETIC")
        return True

    def _handle_Literal(self, node, chunks: list[LexemeChunk]) -> bool:
        raw_value = str(node.value)
        value = self._literal_expr(raw_value, node.prefix_operators or [])
        line = self._line(node)
        if raw_value.startswith('"') and raw_value.endswith('"'):
            string_value = self._java_string_value(raw_value)
            if self._is_regex(string_value):
                for token in self._tokenize_regex(string_value):
                    self._add(chunks, ["regex", token], line, "REGEX")
            else:
                self._add(chunks, f"literal_{self._normalize(string_value)}", line, "LITERAL")
            return True
        if value != "null":
            self._add(chunks, f"literal_{self._normalize(value)}", line, "LITERAL")
        return True

    def _handle_BinaryOperation(self, node, chunks: list[LexemeChunk]) -> bool:
        kind = self._operator_type(node.operator)
        self._add(chunks, self._expr(node), self._line(node), kind)
        current = node.operandl
        while self._is_node(current) and current.__class__.__name__ == "BinaryOperation" and current.operator == node.operator:
            nested_kind = self._operator_type(current.operator)
            self._add(chunks, self._expr(current), self._line(current), nested_kind)
            current = current.operandl
        self._walk(node.operandl, chunks)
        self._walk(node.operandr, chunks)
        return True

    def _handle_MethodInvocation(self, node, chunks: list[LexemeChunk]) -> bool:
        parts = [self._method_select(node)]
        parts.extend(self._expr(arg) for arg in node.arguments or [])
        self._add(chunks, parts, self._line(node), "CALL")
        if getattr(node, "prefix_operators", None):
            self._add(chunks, self._expr(node), self._line(node), "BITWISE" if "~" in node.prefix_operators else "CALL")
        base_expr = f"{self._method_select(node)}({','.join(self._expr(arg) for arg in node.arguments or [])})"
        for selector in node.selectors or []:
            if selector.__class__.__name__ == "MethodInvocation":
                selector_parts = [f"{base_expr}.{selector.member}"]
                selector_parts.extend(self._expr(arg) for arg in selector.arguments or [])
                self._add(chunks, selector_parts, self._line(selector, self._line(node)), "CALL")
                for arg in selector.arguments or []:
                    self._walk(arg, chunks)
                base_expr = f"{base_expr}.{selector.member}({','.join(self._expr(arg) for arg in selector.arguments or [])})"
            else:
                self._walk(selector, chunks)
        for arg in node.arguments or []:
            self._walk(arg, chunks)
        return True

    def _handle_IfStatement(self, node, chunks: list[LexemeChunk]) -> bool:
        self._add(chunks, ["if", self._expr(node.condition)], self._line(node), "CONTROL_FLOW")
        self._walk(node.condition, chunks)
        self._walk(node.then_statement, chunks)
        if node.else_statement is not None:
            if node.else_statement.__class__.__name__ == "IfStatement":
                self._handle_elif_chain(node.else_statement, [self._expr(node.condition)], chunks)
            else:
                self._add(chunks, ["else", f"not_{self._expr(node.condition)}"], self._line(node.else_statement), "CONTROL_FLOW")
                self._walk(node.else_statement, chunks)
        return True

    def _handle_elif_chain(self, node, seen: list[str], chunks: list[LexemeChunk]) -> None:
        condition = self._expr(node.condition)
        self._add(chunks, ["elif", condition], self._line(node), "CONTROL_FLOW")
        seen.append(condition)
        self._walk(node.condition, chunks)
        self._walk(node.then_statement, chunks)
        if node.else_statement is None:
            return
        if node.else_statement.__class__.__name__ == "IfStatement":
            self._handle_elif_chain(node.else_statement, seen, chunks)
            return
        self._add(chunks, ["else", *[f"not_{condition}" for condition in seen]], self._line(node.else_statement), "CONTROL_FLOW")
        self._walk(node.else_statement, chunks)

    def _handle_WhileStatement(self, node, chunks: list[LexemeChunk]) -> bool:
        self._add(chunks, ["while", self._expr(node.condition)], self._line(node), "CONTROL_FLOW")
        self._walk(node.condition, chunks)
        self._walk(node.body, chunks)
        return True

    def _handle_DoStatement(self, node, chunks: list[LexemeChunk]) -> bool:
        self._add(chunks, ["do-while", self._expr(node.condition)], self._line(node), "CONTROL_FLOW")
        self._walk(node.body, chunks)
        self._walk(node.condition, chunks)
        return True

    def _handle_ForStatement(self, node, chunks: list[LexemeChunk]) -> bool:
        control = node.control
        if control.__class__.__name__ == "EnhancedForControl":
            var_name = self._declaration_name(control.var)
            line = self._line(node)
            self._add(chunks, ["for", var_name, self._expr(control.iterable)], line, "CONTROL_FLOW")
            self._add(chunks, var_name, line, "IDENTIFIER")
            self._add(chunks, [self._type_to_str(control.var.type), var_name], line, "DECLARATION")
            self._walk(control.iterable, chunks)
            self._walk(node.body, chunks)
            return True

        init = self._as_list(control.init)
        condition = control.condition
        update = self._as_list(control.update)
        index = self._guess_index(init, update, condition)
        target = self._iter_target(condition, index)
        parts = ["for"]
        if target:
            parts.append(target)
        start = self._non_trivial_start(init)
        step = self._non_trivial_step(update)
        if start:
            parts.append(start)
        if step:
            parts.append(step)
        self._add(chunks, parts, self._line(node), "CONTROL_FLOW")

        for item in init:
            if item.__class__.__name__ in {"LocalVariableDeclaration", "VariableDeclaration"}:
                for declarator in item.declarators or []:
                    self._walk(declarator.initializer, chunks)
            else:
                self._walk(item, chunks)
        self._walk(condition, chunks)
        for item in update:
            self._walk(item, chunks)
        self._walk(node.body, chunks)
        return True

    def _as_list(self, value) -> list:
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def _handle_SwitchStatement(self, node, chunks: list[LexemeChunk]) -> bool:
        self._add(chunks, ["switch", self._expr(node.expression)], self._line(node), "CONTROL_FLOW")
        self._walk(node.expression, chunks)
        for case in node.cases or []:
            self._walk(case, chunks)
        return True

    def _handle_Assignment(self, node, chunks: list[LexemeChunk]) -> bool:
        self._add(chunks, self._expr(node), self._line(node), "ASSIGNMENT")
        self._walk(node.expressionl, chunks)
        self._walk(node.value, chunks)
        return True

    def _handle_VariableDeclaration(self, node, chunks: list[LexemeChunk]) -> bool:
        return self._handle_LocalVariableDeclaration(node, chunks)

    def _children(self, node) -> Iterable:
        if not self._is_node(node):
            return []
        children = []
        for attr in getattr(node, "attrs", []):
            value = getattr(node, attr)
            if isinstance(value, list):
                children.extend(value)
            elif self._is_node(value):
                children.append(value)
        return children

    def _is_node(self, value) -> bool:
        return hasattr(value, "attrs") and hasattr(value, "__class__")

    def _line(self, node, fallback: int = 1) -> int:
        position = getattr(node, "position", None)
        if position is not None:
            return position.line
        child_lines = []
        for child in self._children(node):
            line = self._line(child, fallback=0)
            if line > 0:
                child_lines.append(line)
        return min(child_lines) if child_lines else fallback

    def _expr(self, node) -> str:
        if node is None:
            return ""
        kind = node.__class__.__name__
        if kind == "Literal":
            raw_value = str(node.value)
            if raw_value.startswith('"') and raw_value.endswith('"'):
                return raw_value
            return self._literal_expr(raw_value, node.prefix_operators or [])
        if kind == "MemberReference":
            base = self._normalize(node.member)
            if node.qualifier:
                base = f"{self._normalize(node.qualifier)}.{base}"
            for op in node.prefix_operators or []:
                base = f"{op}{base}"
            for op in node.postfix_operators or []:
                base = f"{base}{op}"
            return base
        if kind == "BinaryOperation":
            return f"{self._expr(node.operandl)}{node.operator}{self._expr(node.operandr)}"
        if kind == "MethodInvocation":
            select = self._method_select(node)
            args = ",".join(self._expr(arg) for arg in node.arguments or [])
            base = f"{self._normalize(select)}({args})"
            for selector in node.selectors or []:
                if selector.__class__.__name__ == "MethodInvocation":
                    selector_args = ",".join(self._expr(arg) for arg in selector.arguments or [])
                    base = f"{base}.{selector.member}({selector_args})"
            return self._with_prefix_ops(node, base)
        if kind == "Assignment":
            return f"{self._expr(node.expressionl)}{node.type}{self._expr(node.value)}"
        if kind == "Cast":
            return f"({self._type_to_str(node.type)}){self._expr(node.expression)}"
        if kind == "TernaryExpression":
            return f"{self._expr(node.condition)}?{self._expr(node.if_true)}:{self._expr(node.if_false)}"
        if kind == "ClassCreator":
            args = ",".join(self._expr(arg) for arg in node.arguments or [])
            return f"new{self._type_to_str(node.type)}({args})"
        if kind == "ArrayCreator":
            dimensions = len(getattr(node, "dimensions", None) or [])
            initializer = getattr(node, "initializer", None)
            init_size = _initializer_size(initializer) if initializer is not None else 0
            suffix = f"_init{init_size}" if init_size else ""
            return f"new{self._type_to_str(node.type)}_array{dimensions}{suffix}"
        if kind == "ArrayInitializer":
            return f"array_init{_initializer_size(node)}"
        if kind == "LambdaExpression":
            params = ",".join(self._expr(param) for param in node.parameters or [])
            body = self._lambda_body_expr(node.body)
            return f"({params})->{{{body}}}"
        if kind == "This":
            return "this"
        return self._normalize(str(node))

    def _literal_expr(self, value: str, prefix_operators=None) -> str:
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        for op in prefix_operators or []:
            value = f"{op}{value}"
        return self._normalize(value)

    def _type_to_str(self, node) -> str:
        if node is None:
            return ""
        name = getattr(node, "name", "")
        args = getattr(node, "arguments", None)
        if args == []:
            name = f"{name}<>"
        elif args:
            rendered = []
            for arg in args:
                rendered.append(self._type_to_str(getattr(arg, "type", arg)))
            name = f"{name}<{','.join(rendered)}>"
        dimensions = "[]" * len(getattr(node, "dimensions", []) or [])
        sub_type = getattr(node, "sub_type", None)
        if sub_type is not None:
            name = f"{name}.{self._type_to_str(sub_type)}"
        return self._normalize(f"{name}{dimensions}")

    def _method_select(self, node) -> str:
        select = f"{node.qualifier}.{node.member}" if node.qualifier else node.member
        return self._normalize(select)

    def _with_prefix_ops(self, node, value: str) -> str:
        for op in getattr(node, "prefix_operators", None) or []:
            value = f"{op}{value}"
        for op in getattr(node, "postfix_operators", None) or []:
            value = f"{value}{op}"
        return value

    def _lambda_body_expr(self, body) -> str:
        if isinstance(body, list):
            return "".join(self._statement_expr(item) for item in body)
        return self._expr(body)

    def _statement_expr(self, node) -> str:
        kind = node.__class__.__name__
        if kind in {"LocalVariableDeclaration", "VariableDeclaration"}:
            type_name = self._type_to_str(node.type)
            parts = []
            for declarator in node.declarators or []:
                rhs = f"={self._expr(declarator.initializer)}" if declarator.initializer is not None else ""
                parts.append(f"{type_name}{self._normalize(declarator.name)}{rhs};")
            return "".join(parts)
        if kind == "StatementExpression":
            return f"{self._expr(node.expression)};"
        if kind == "ForStatement":
            return f"for({self._for_control_expr(node.control)}){{{self._statement_expr(node.body)}}}"
        if kind == "WhileStatement":
            return f"while({self._expr(node.condition)}){{{self._statement_expr(node.body)}}}"
        if kind == "IfStatement":
            return f"if({self._expr(node.condition)}){{{self._statement_expr(node.then_statement)}}}"
        if kind == "BlockStatement":
            return "".join(self._statement_expr(item) for item in node.statements or [])
        if kind == "BreakStatement":
            return "break;"
        return self._expr(node)

    def _for_control_expr(self, control) -> str:
        init = self._as_list(getattr(control, "init", None))
        update = self._as_list(getattr(control, "update", None))
        init_expr = ",".join(self._statement_expr(item).rstrip(";") for item in init)
        condition = self._expr(getattr(control, "condition", None))
        update_expr = ",".join(self._expr(item) for item in update)
        return f"{init_expr};{condition};{update_expr}"

    def _java_string_value(self, literal: str) -> str:
        try:
            return json.loads(literal)
        except Exception:
            return literal[1:-1]

    def _guess_index(self, init, update, condition) -> str:
        for item in init or []:
            if item.__class__.__name__ in {"LocalVariableDeclaration", "VariableDeclaration"} and item.declarators:
                return self._normalize(item.declarators[0].name)
        for item in update or []:
            expression = self._expr(item)
            if expression.endswith("++") or expression.endswith("--"):
                return expression[:-2]
            if expression.startswith("++") or expression.startswith("--"):
                return expression[2:]
            for op in ("+=", "-=", "="):
                if op in expression:
                    return expression.split(op, 1)[0]
        if condition is not None and condition.__class__.__name__ == "BinaryOperation":
            return self._expr(condition.operandl)
        return ""

    def _iter_target(self, condition, index: str) -> str:
        if condition is None or condition.__class__.__name__ != "BinaryOperation":
            return ""
        left = self._expr(condition.operandl)
        right = self._expr(condition.operandr)
        if index:
            if left == index:
                return right
            if right == index:
                return left
        right_looks = "." in right or right.endswith(")")
        left_looks = "." in left or left.endswith(")")
        if right_looks and not left_looks:
            return right
        if left_looks and not right_looks:
            return left
        return right

    def _declaration_name(self, node) -> str:
        name = getattr(node, "name", None)
        if name:
            return self._normalize(name)
        declarators = getattr(node, "declarators", None) or []
        if declarators:
            return self._normalize(declarators[0].name)
        return ""

    def _non_trivial_start(self, init) -> str:
        for item in init or []:
            if item.__class__.__name__ in {"LocalVariableDeclaration", "VariableDeclaration"} and item.declarators:
                declarator = item.declarators[0]
                if declarator.initializer is None:
                    continue
                rhs = self._expr(declarator.initializer)
                if rhs not in {"0", "1", "0L", "1L", "0.0", "1.0"}:
                    return f"{self._normalize(declarator.name)}={rhs}"
        return ""

    def _non_trivial_step(self, update) -> str:
        for item in update or []:
            expression = self._expr(item)
            if expression.endswith("++") or expression.startswith("++"):
                continue
            if expression.endswith("--") or expression.startswith("--"):
                continue
            return expression
        return ""

    def _add(
        self,
        chunks: list[LexemeChunk],
        lexeme: str | Iterable[str],
        line: int,
        kind: str,
    ) -> None:
        if not isinstance(lexeme, str):
            lexeme = self._join(lexeme)
        normalized = self._normalize(lexeme)
        if normalized and len(normalized) <= self.MAX_LEXEME_CHARS:
            chunks.append(LexemeChunk(normalized, line, kind))

    def _join(self, parts: Iterable[str]) -> str:
        return "_".join(part for part in (self._normalize(part) for part in parts) if part)

    def _normalize(self, value: object | None) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", "", str(value).strip())

    def _operator_type(self, operator: str) -> str:
        if operator in {"&", "|", "^", "<<", ">>", ">>>"}:
            return "BITWISE"
        if operator in {"==", "!=", "<", ">", "<=", ">=", "instanceof"}:
            return "COMPARISON"
        if operator in {"&&", "||"}:
            return "LOGICAL"
        return "ARITHMETIC"

    def _comment_normalize(self, value: str) -> str:
        return re.sub(r"\s+", "_", value.strip())

    def _split_block_comment(self, raw: str) -> list[str]:
        out = []
        first = True
        for line in raw.split("\n"):
            if first:
                first = False
                line = re.sub(r"^\s*/?\*+", "", line)
            line = re.sub(r"^\s*\*+", "", line).strip()
            if line:
                out.append(line)
        return out

    def _mask_comments(self, source: str) -> str:
        result = list(source)
        for _, start, end, _ in self._comment_spans(source):
            for index in range(start, end):
                if result[index] != "\n":
                    result[index] = " "
        return "".join(result)

    def _is_regex(self, value: str) -> bool:
        if len(value) < 2 or not self._looks_like_regex(value):
            return False
        try:
            re.compile(value)
            return True
        except re.error:
            return False

    def _looks_like_regex(self, value: str) -> bool:
        """Conservatively identify strings that intentionally use regex syntax."""
        if re.search(r"\\[dDsSwWbBAZzG]", value):
            return True
        if re.search(r"\\[.^$*+?{}\[\]|()]", value):
            return True
        if re.search(r"\[[^\]\n]*(?:\^|-|\\)[^\]\n]*\]", value):
            return True
        regex_context = any(marker in value for marker in ("^", "$", "|", "\\", "(", ")"))
        if (".*" in value or ".+" in value) and regex_context:
            return True
        if (value.startswith("^") or value.endswith("$")) and len(value) > 2:
            return True
        if "|" in value and "||" not in value and regex_context:
            return True
        return False

    def _tokenize_regex(self, value: str) -> list[str]:
        out: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            if buffer:
                out.append("".join(buffer))
                buffer.clear()

        i = 0
        while i < len(value):
            char = value[i]
            if char == "[":
                flush()
                j = i + 1
                escaped = False
                while j < len(value):
                    nxt = value[j]
                    if escaped:
                        escaped = False
                    elif nxt == "\\":
                        escaped = True
                    elif nxt == "]":
                        j += 1
                        break
                    j += 1
                out.append(value[i:min(j, len(value))])
                i = j
                continue
            if char == "(":
                flush()
                if i + 1 < len(value) and value[i + 1] == "?":
                    j = i + 2
                    while j < len(value) and value[j] not in ":)":
                        j += 1
                    if j < len(value):
                        j += 1
                    out.append(value[i:min(j, len(value))])
                    i = j
                else:
                    out.append("(")
                    i += 1
                continue
            if char in ")*+?|^$":
                flush()
                out.append(char)
                i += 1
                continue
            if char == "{":
                flush()
                j = value.find("}", i + 1)
                j = len(value) if j == -1 else j + 1
                if j < len(value) and value[j] == "?":
                    j += 1
                out.append(value[i:j])
                i = j
                continue
            if char == "\\":
                flush()
                out.append(value[i:i + 2] if i + 1 < len(value) else "\\")
                i += 2
                continue
            buffer.append(char)
            i += 1
        flush()
        return out


def _initializer_size(node) -> int:
    if node is None:
        return 0
    initializers = getattr(node, "initializers", None)
    if isinstance(initializers, list):
        return len(initializers)
    return 0
