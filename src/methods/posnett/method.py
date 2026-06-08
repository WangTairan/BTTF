import math
import re
from collections import Counter
from dataclasses import dataclass


JAVA_OPERATORS = {
    ">>>=", ">>=", "<<=", "++", "--", "==", "!=", ">=", "<=", "&&", "||",
    "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<", ">>", ">>>",
    "->", "::", "=", "+", "-", "*", "/", "%", ">", "<", "!", "~", "&",
    "|", "^", "?", ":", ".", ",", ";", "(", ")", "{", "}", "[", "]",
}

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while",
}

TOKEN_PATTERN = re.compile(
    r">>>=|>>=|<<=|\+\+|--|==|!=|>=|<=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>>|>>|->|::"
    r"|[A-Za-z_$][A-Za-z0-9_$]*"
    r"|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[A-Za-z]*"
    r"|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'"
    r"|[{}()[\];,.:?~!%^&*+\-/=<>|]"
)


@dataclass
class PosnettReadabilityResult:
    score: float
    probability: float
    z_value: float
    lines: int
    halstead_volume: float
    byte_entropy: float
    token_count: int
    vocabulary_size: int


def posnett_model(code: str) -> PosnettReadabilityResult:
    tokens = _java_tokens(strip_comments(code))
    lines = _line_count(code)
    volume = _halstead_volume(tokens)
    entropy = _byte_entropy(code)

    z_value = 8.87 - 0.033 * volume + 0.40 * lines - 1.5 * entropy
    probability = _sigmoid(z_value)

    return PosnettReadabilityResult(
        score=probability,
        probability=probability,
        z_value=z_value,
        lines=lines,
        halstead_volume=volume,
        byte_entropy=entropy,
        token_count=len(tokens),
        vocabulary_size=len(set(tokens)),
    )


def _java_tokens(code: str) -> list[str]:
    return [match.group(0) for match in TOKEN_PATTERN.finditer(code)]


def strip_comments(code: str) -> str:
    result = []
    index = 0
    state = "code"
    while index < len(code):
        char = code[index]
        next_char = code[index + 1] if index + 1 < len(code) else ""

        if state == "code":
            if char == "/" and next_char == "/":
                state = "line_comment"
                index += 2
                continue
            if char == "/" and next_char == "*":
                state = "block_comment"
                index += 2
                continue
            result.append(char)
            if char == '"':
                state = "double_string"
            elif char == "'":
                state = "single_string"
            index += 1
            continue

        if state == "line_comment":
            if char == "\n":
                result.append(char)
                state = "code"
            index += 1
            continue

        if state == "block_comment":
            if char == "*" and next_char == "/":
                state = "code"
                index += 2
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue

        result.append(char)
        if char == "\\":
            if index + 1 < len(code):
                result.append(code[index + 1])
                index += 2
            else:
                index += 1
            continue
        if state == "double_string" and char == '"':
            state = "code"
        elif state == "single_string" and char == "'":
            state = "code"
        index += 1

    return "".join(result)


def _line_count(code: str) -> int:
    return len(code.splitlines())


def _halstead_volume(tokens: list[str]) -> float:
    if not tokens:
        return 0.0

    operators = []
    operands = []
    for token in tokens:
        if token in JAVA_OPERATORS or token in JAVA_KEYWORDS:
            operators.append(token)
        else:
            operands.append(token)

    program_length = len(operators) + len(operands)
    vocabulary_size = len(set(operators)) + len(set(operands))
    if program_length == 0 or vocabulary_size <= 1:
        return 0.0
    return program_length * math.log2(vocabulary_size)


def _byte_entropy(code: str) -> float:
    data = code.encode("utf-8")
    if not data:
        return 0.0

    total = len(data)
    counts = Counter(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _sigmoid(value: float) -> float:
    if value >= 0:
        factor = math.exp(-value)
        return 1 / (1 + factor)
    factor = math.exp(value)
    return factor / (1 + factor)
