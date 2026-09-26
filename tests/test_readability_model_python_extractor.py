from src.methods.readability_model.extractors import (
    PythonAstLexemeExtractor,
    extractor_for_language,
)


PYTHON_SOURCE = '''
import os
import re

class Calculator:
    """Compute a normalized value."""

    def compute(self, value):
        # Keep the intermediate value visible.
        subtotal = value + 1
        if subtotal > 2 and value:
            return re.match(r"[a-z]+", str(subtotal))
        return None
'''


def test_python_extractor_uses_ast_taxonomy() -> None:
    extractor = extractor_for_language("python")
    assert isinstance(extractor, PythonAstLexemeExtractor)

    chunks, used_fallback = extractor.extract_with_member_fallback(PYTHON_SOURCE)
    by_type: dict[str, list[str]] = {}
    for chunk in chunks:
        by_type.setdefault(chunk.type, []).append(chunk.lexeme)

    assert used_fallback is False
    assert len(by_type["COMMENT"]) == 2  # docstring and line comment
    assert any("Calculator" in value for value in by_type["DECLARATION"])
    assert any("match" in value for value in by_type["CALL"])
    assert by_type["ASSIGNMENT"]
    assert by_type["ARITHMETIC"]
    assert by_type["COMPARISON"]
    assert by_type["LOGICAL"]
    assert by_type["CONTROL_FLOW"]
    assert by_type["REGEX"] == ["regex_[a-z]+"]
    assert any("import_stdlib_re" == value for value in by_type["IMPORT"])
    assert any("unused_import_stdlib_os" == value for value in by_type["UNUSED_IMPORT"])


def test_python_extractor_does_not_swallow_syntax_errors() -> None:
    try:
        PythonAstLexemeExtractor().extract("def broken(:\n    pass\n")
    except SyntaxError:
        return
    raise AssertionError("Invalid Python source did not raise SyntaxError")


def test_python_fragment_mode_is_explicit_and_bounded() -> None:
    source = "        value = legacy_call(item)\n        print value\n"
    extractor = PythonAstLexemeExtractor(allow_fragments=True)

    chunks, used_fragment_mode = extractor.extract_with_member_fallback(source)

    assert used_fragment_mode is True
    assert any(chunk.type == "CALL" and "legacy_call" in chunk.lexeme for chunk in chunks)
    assert any(chunk.type == "ASSIGNMENT" for chunk in chunks)


def test_extractor_rejects_unknown_languages() -> None:
    try:
        extractor_for_language("brainfuck")
    except ValueError as exc:
        assert "Unsupported readability-model language" in str(exc)
    else:
        raise AssertionError("Unknown languages must not silently use the Java extractor")
