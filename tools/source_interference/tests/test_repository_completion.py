from __future__ import annotations

from readability_experiments.repository_completion.builder import (
    HOLE,
    LocatedSpan,
    _canonical_completion,
    _replace_span,
    source_with_completion,
    source_with_hole,
)
from readability_experiments.repository_completion.discovery import (
    discover_functions,
)
from readability_experiments.repository_completion.tasks import (
    _replace_span as task_replace_span,
)
from readability_experiments.repository_completion.validator import (
    normalize_completion,
)
from readability_experiments.repository_completion.variants import (
    envelope_source,
    unwrap_envelope,
)
from readability_experiments.repository_completion.validate_manifest import (
    _syntax_valid,
    validation_hole_source,
)


def test_completion_round_trip_preserves_python_indentation() -> None:
    source = "def f(value):\n    return value + 1\n"
    start = source.index("return")
    end = source.index("\n", start)
    span = LocatedSpan(start, end, "    ", "return value + 1")
    sentinel = _replace_span(source, span, "__READABILITY_HOLE_SENTINEL__()")
    hole = source_with_hole(sentinel)
    assert hole.count(HOLE) == 1
    assert source_with_completion(hole, span.completion) == source


def test_canonical_completion_removes_continuation_indent() -> None:
    raw = "if ready:\n        return value\n    return fallback"
    assert _canonical_completion(raw, "    ") == (
        "if ready:\n    return value\nreturn fallback"
    )


def test_python_discovery_exposes_method_and_statement_spans() -> None:
    source = (
        "class Calculator:\n"
        "    def total(self, values):\n"
        "        result = sum(values)\n"
        "        return result\n"
    )
    candidates = discover_functions(source, "python")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.qualified_name == "Calculator.total"
    assert candidate.method.text == "result = sum(values)\n        return result"
    assert [span.text for span in candidate.statements] == [
        "result = sum(values)",
        "return result",
    ]


def test_java_discovery_exposes_method_and_statement_spans() -> None:
    source = (
        "class Calculator {\n"
        "    int total(int left, int right) {\n"
        "        int result = left + right;\n"
        "        return result;\n"
        "    }\n"
        "}\n"
    )
    candidates = discover_functions(source, "java")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.symbol == "total"
    assert candidate.method.text.startswith("int result = left + right;")
    assert {span.text for span in candidate.statements} == {
        "int result = left + right;",
        "return result;",
    }


def test_validation_holes_remain_parseable() -> None:
    python_source = "def total(values):\n    result = sum(values)\n    return result\n"
    python_candidate = discover_functions(python_source, "python")[0]
    python_row = {
        "language": "python",
        "method_span": {
            "start_byte": python_candidate.method.start_byte,
            "end_byte": python_candidate.method.end_byte,
        },
        "statement_span": {
            "start_byte": python_candidate.statements[0].start_byte,
            "end_byte": python_candidate.statements[0].end_byte,
        },
    }
    for granularity in ("method_body", "statement"):
        source = validation_hole_source(python_source, python_row, granularity)
        assert _syntax_valid(source, "python") == (True, None)

    java_source = (
        "class Calculator {\n"
        "    int total(int left, int right) {\n"
        "        int result = left + right;\n"
        "        return result;\n"
        "    }\n"
        "}\n"
    )
    java_candidate = discover_functions(java_source, "java")[0]
    java_row = {
        "language": "java",
        "method_span": {
            "start_byte": java_candidate.method.start_byte,
            "end_byte": java_candidate.method.end_byte,
        },
        "statement_span": {
            "start_byte": java_candidate.statements[0].start_byte,
            "end_byte": java_candidate.statements[0].end_byte,
        },
    }
    for granularity in ("method_body", "statement"):
        source = validation_hole_source(java_source, java_row, granularity)
        assert _syntax_valid(source, "java") == (True, None)


def test_model_task_and_completion_round_trip_python() -> None:
    source = "def add(left, right):\n    return left + right\n"
    start = source.index("return")
    end = source.index("\n", start)
    span = {"start_byte": start, "end_byte": end}
    holed = task_replace_span(source, span, HOLE)
    assert "    <READABILITY_HOLE>" in holed
    assert source_with_completion(holed, "return left + right") == source


def test_normalize_completion_accepts_fenced_python() -> None:
    assert normalize_completion("```python\n    return value\n```", "python") == (
        "return value"
    )


def test_interference_envelope_round_trip_and_visible_change() -> None:
    source = (
        "def add(left, right):\n"
        "    total = left + right\n"
        "    return total\n"
        "\n"
        "VALUE = 1\n"
    )
    start = source.index("total =")
    end = source.index("\n\n", start)
    enveloped = envelope_source(
        source, {"start_byte": start, "end_byte": end}
    )
    gold, prompt = unwrap_envelope(enveloped)
    assert gold == source
    assert source_with_completion(
        prompt, "total = left + right\nreturn total"
    ) == source

    changed = enveloped.replace("VALUE = 1", "VALUE = 0x1")
    changed_gold, changed_prompt = unwrap_envelope(changed)
    assert changed_gold.endswith("VALUE = 0x1\n")
    assert changed_prompt != prompt
