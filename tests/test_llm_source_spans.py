"""Theoretical role boundaries, source mapping, and confirmed name bindings."""

import pytest

from src.methods.readability_model.llm_features.source_spans import (
    ROLES,
    SOURCE_ANALYSIS_VERSION,
    SourceParseError,
    analyze_source,
)


def values(source, analysis, role):
    return [
        source[span.start : span.end] for span in analysis.spans if span.role == role
    ]


def occurrences(source, analysis, name):
    return [
        span
        for span in analysis.spans
        if span.role == "identifier" and source[span.start : span.end] == name
    ]


def test_python_role_boundaries_are_actual_source():
    source = "def compute(a: int):\n    b: int = a + 10\n    if b > 8:\n        return account.update(b * 2)\n"
    analysis = analyze_source(source, "python")
    assert analysis.roles_available == ROLES
    assert values(source, analysis, "declaration_header") == [
        "def compute(a: int):",
        "b: int",
    ]
    assert values(source, analysis, "call_target") == ["update"]
    assert values(source, analysis, "assignment_rhs") == ["a + 10"]
    assert values(source, analysis, "expression") == ["a + 10", "b > 8", "b * 2"]
    assert values(source, analysis, "control_header") == [
        "if b > 8:",
        "return account.update(b * 2)",
    ]
    assert all(
        "return" not in header
        for header in values(source, analysis, "declaration_header")
    )


@pytest.mark.parametrize(
    "language,source",
    [
        (
            "java",
            "class Demo { int f(int a) { int b = a + 10; if (b > 8) return account.update(b * 2); return b; }}",
        ),
        (
            "cpp",
            "int f(int a) { int b = a + 10; if (b > 8) return account.update(b * 2); return b; }",
        ),
        (
            "c",
            "int f(int a) { int b = a + 10; if (b > 8) return update(b * 2); return b; }",
        ),
    ],
)
def test_brace_language_role_boundaries(language, source):
    analysis = analyze_source(source, language)
    assert values(source, analysis, "call_target") == ["update"]
    assert values(source, analysis, "assignment_rhs") == ["a + 10"]
    assert values(source, analysis, "expression") == ["a + 10", "b > 8", "b * 2"]
    assert "int b" in values(source, analysis, "declaration_header")
    control = values(source, analysis, "control_header")
    assert "if (b > 8)" in control
    assert not any("if" in header and "update" in header for header in control)
    assert all(
        "=" not in header for header in values(source, analysis, "declaration_header")
    )


@pytest.mark.parametrize(
    "language,source",
    [
        ("python", 'def f(数量):\n    文本 = "你好"\n    return 数量 + 1\n'),
        (
            "java",
            'class 演示 { int f(int 数量) { String 文本 = "你好"; return 数量 + 1; } }',
        ),
    ],
)
def test_multibyte_identifiers_map_back_to_unicode_characters(language, source):
    analysis = analyze_source(source, language)
    identifiers = values(source, analysis, "identifier")
    assert identifiers.count("数量") == 2
    assert "文本" in identifiers
    assert '"你好"' in values(source, analysis, "literal")
    names = occurrences(source, analysis, "数量")
    assert names[0].binding == names[1].binding
    assert names[0].binding is not None


def test_python_docstrings_are_comments_not_literals_or_names():
    source = '"""module: misleading_name"""\ndef f(a):\n    """Describe misleading_name."""\n    # misleading_name is just text\n    message = "misleading_name"\n    return a\n'
    analysis = analyze_source(source, "python")
    assert len(values(source, analysis, "comment")) == 3
    assert values(source, analysis, "literal") == ['"misleading_name"']
    assert "misleading_name" not in values(source, analysis, "identifier")


def test_java_strings_and_comments_do_not_pollute_identifier_inventory():
    source = 'class Demo { void f() { /* aaaa */ String message = "bbbb"; // cccc\n }}'
    analysis = analyze_source(source, "java")
    assert "aaaa" not in values(source, analysis, "identifier")
    assert "bbbb" not in values(source, analysis, "identifier")
    assert "cccc" not in values(source, analysis, "identifier")


def test_python_shadowing_and_closure_bindings():
    source = "def outer(a):\n    b = a\n    def inner(a):\n        return a + b\n    return a + inner(b)\n"
    analysis = analyze_source(source, "python")
    a = occurrences(source, analysis, "a")
    b = occurrences(source, analysis, "b")
    assert a[0].binding == a[1].binding == a[4].binding
    assert a[2].binding == a[3].binding
    assert a[0].binding != a[2].binding
    assert len({span.binding for span in b}) == 1
    assert all(span.binding is None for span in occurrences(source, analysis, "inner"))


def test_python_class_attributes_do_not_capture_method_local_names():
    source = "class Demo:\n    a = 4\n    def f(self, a):\n        return self.a + a\n"
    analysis = analyze_source(source, "python")
    a = occurrences(source, analysis, "a")
    assert a[0].binding is None
    assert a[2].binding is None
    assert a[1].binding == a[3].binding


def test_python_default_evaluates_in_enclosing_scope():
    source = (
        "def outer(a):\n    def inner(a=a):\n        return a\n    return inner(a)\n"
    )
    analysis = analyze_source(source, "python")
    a = occurrences(source, analysis, "a")
    assert a[0].binding == a[2].binding == a[4].binding
    assert a[1].binding == a[3].binding
    assert a[0].binding != a[1].binding


def test_java_nested_block_shadowing_and_member_exclusion():
    source = "class Demo { int a; void f(int a) { int b=a; {int b=3; consume(b);} consume(b); consume(this.a); } }"
    analysis = analyze_source(source, "java")
    b = occurrences(source, analysis, "b")
    a = occurrences(source, analysis, "a")
    assert b[0].binding == b[3].binding
    assert b[1].binding == b[2].binding
    assert b[0].binding != b[1].binding
    assert a[0].binding is None and a[-1].binding is None
    assert a[1].binding == a[2].binding


def test_java_enhanced_for_variable_does_not_bind_iterable():
    source = "class Demo { void f(int a) {for (int a : a) {consume(a);} consume(a);} }"
    analysis = analyze_source(source, "java")
    a = occurrences(source, analysis, "a")
    assert a[0].binding == a[2].binding == a[4].binding
    assert a[1].binding == a[3].binding
    assert a[0].binding != a[1].binding


def test_java_fragment_wrapper_has_no_synthetic_names():
    source = "public int f(int a) { return a + 1; }"
    analysis = analyze_source(source, "java", allow_fragments=True)
    assert analysis.metadata["structural_available"]
    assert not any("__" in name for name in values(source, analysis, "identifier"))
    assert all(0 <= span.start < span.end <= len(source) for span in analysis.spans)


def test_java_constructor_member_parse_is_strict_and_source_aligned():
    source = (
        "/** Constructs the chart panel. */\n"
        "public ChartPanel(JFreeChart chart) {\n"
        "    this(chart, DEFAULT_WIDTH, true);\n"
        "}\n"
    )
    with pytest.raises(SourceParseError):
        analyze_source(source, "java")
    analysis = analyze_source(source, "java", allow_class_members=True)
    assert analysis.metadata["parse_mode"] == "class_members"
    assert analysis.metadata["structural_available"]
    assert analysis.roles_available == ROLES
    assert "__Fragment__" not in values(source, analysis, "identifier")
    assert values(source, analysis, "declaration_header") == [
        "public ChartPanel(JFreeChart chart)"
    ]
    chart = occurrences(source, analysis, "chart")
    assert chart[0].binding == chart[1].binding
    assert chart[0].binding is not None
    assert all(0 <= span.start < span.end <= len(source) for span in analysis.spans)


@pytest.mark.parametrize(
    "source",
    [
        "public ChartPanel(JFreeChart chart) { this(chart,); }",
        "public int f(int a) { if (a > 0) {",
        "class Demo { void f() { if ( > ) {} } }",
    ],
)
def test_java_member_policy_does_not_admit_invalid_source(source):
    with pytest.raises(SourceParseError):
        analyze_source(source, "java", allow_class_members=True)


def test_java_member_policy_leaves_complete_program_parse_unchanged():
    source = "class Demo { int f(int a) { return a + 1; } }"
    strict = analyze_source(source, "java")
    member_aware = analyze_source(source, "java", allow_class_members=True)
    assert member_aware.metadata["parse_mode"] == "original"
    assert strict.spans == member_aware.spans
    assert strict.metadata == member_aware.metadata
    with pytest.raises(ValueError, match="only supported for Java"):
        analyze_source("def f(): pass", "python", allow_class_members=True)


def test_python_indented_fragment_wrapper_maps_source_without_injected_spaces():
    source = "    if a > 0:\n        value = a + 1\n        return value\n"
    analysis = analyze_source(source, "python", allow_fragments=True)
    assert analysis.metadata["structural_available"]
    assert values(source, analysis, "assignment_rhs") == ["a + 1"]
    assert values(source, analysis, "expression") == ["a > 0", "a + 1"]
    assert "__fragment__" not in values(source, analysis, "identifier")


@pytest.mark.parametrize(
    "language,source",
    [
        ("python", "def f(a):\n    if a:\n"),
        ("java", "class Demo { void f(int a) { if (a > 0) {"),
        ("c", "int f(int a) { if (a > 0) {"),
    ],
)
def test_complete_source_parse_errors_are_not_swallowed(language, source):
    with pytest.raises(SourceParseError):
        analyze_source(source, language)
    fragment = analyze_source(source, language, allow_fragments=True)
    assert not fragment.metadata["structural_available"]
    assert "expression" not in fragment.roles_available
    assert fragment.metadata["parse_diagnostics"]
    assert fragment.metadata["binding_count"] == 0


@pytest.mark.parametrize(
    "language,source,expected",
    [
        ("python", "def f(a):\n    return (a + 2) * (a - 3)\n", "(a + 2) * (a - 3)"),
        ("java", "class D { int f(int a) { return (a+2)*(a-3); } }", "(a+2)*(a-3)"),
    ],
)
def test_nested_expression_intervals_are_not_counted_twice(language, source, expected):
    analysis = analyze_source(source, language)
    assert values(source, analysis, "expression") == [expected]
    assert len(occurrences(source, analysis, "a")) == 3


@pytest.mark.parametrize(
    "language,source",
    [
        (
            "python",
            "def f(a):\n    # describe first\n    b = a + 1\n    c = b + 1  # trailing text\n    return c\n    # trailing final comment\n",
        ),
        (
            "java",
            "class D { void f(int a) {\n    // describe first\n    int b = a+1;\n    int c = b+1; // trailing text\n    consume(c);\n    // trailing final comment\n} }",
        ),
        (
            "c",
            "void f(int a) {\n    // describe first\n    int b = a+1;\n    int c = b+1; // trailing text\n    consume(c);\n    // trailing final comment\n}",
        ),
    ],
)
def test_comment_targets_are_front_comment_same_scope_only(language, source):
    analysis = analyze_source(source, language)
    targets = analysis.metadata["comment_targets"]
    assert len(targets) == 1
    target = targets[0]
    assert "describe first" in source[target["comment_start"] : target["comment_end"]]
    assert "b = a" in source[target["target_start"] : target["target_end"]]


def test_python_docstring_targets_next_statement_in_same_body():
    source = 'def f(a):\n    """Add one to a."""\n    b = a + 1\n    return b\n'
    analysis = analyze_source(source, "python")
    targets = analysis.metadata["comment_targets"]
    assert len(targets) == 1
    target = targets[0]
    assert source[target["target_start"] : target["target_end"]] == "b = a + 1"


@pytest.mark.parametrize(
    "language,source",
    [
        (
            "python",
            "def f(a):\n    # first explanation\n    # second explanation\n    return a + 1\n",
        ),
        (
            "java",
            "class D { int f(int a) {\n    // first explanation\n    // second explanation\n    return a + 1;\n} }",
        ),
    ],
)
def test_leading_comment_chain_has_exactly_one_paired_code_target(language, source):
    analysis = analyze_source(source, language)
    targets = analysis.metadata["comment_targets"]
    assert len(targets) == 1
    target = targets[0]
    comment = source[target["comment_start"] : target["comment_end"]]
    assert "first explanation" in comment and "second explanation" in comment
    assert "return a + 1" in source[target["target_start"] : target["target_end"]]


def test_python_leading_comment_and_docstring_target_code_not_docstring():
    source = '# explain\n"""module documentation"""\nf()\n'
    analysis = analyze_source(source, "python")
    targets = analysis.metadata["comment_targets"]
    assert len(targets) == 1
    target = targets[0]
    assert source[target["target_start"] : target["target_end"]] == "f()"
    assert (
        "module documentation"
        in source[target["comment_start"] : target["comment_end"]]
    )


def test_python_exception_and_import_declarations_are_first_bound_occurrences():
    source = "def f():\n    import helper as bar\n    try:\n        return bar()\n    except Exception as exc:\n        return str(exc)\n"
    analysis = analyze_source(source, "python")
    for name in ("bar", "exc"):
        identifiers = occurrences(source, analysis, name)
        assert len(identifiers) == 2
        assert identifiers[0].binding is not None
        assert identifiers[0].binding == identifiers[1].binding


def test_python_fstring_embedded_expressions_are_not_a_single_literal():
    source = 'def f(x, obj):\n    return f"value={x + 1}; {obj.field}; {obj.call(x)}"\n'
    analysis = analyze_source(source, "python")
    x = occurrences(source, analysis, "x")
    assert len(x) == 3 and len({span.binding for span in x}) == 1
    assert "field" in values(source, analysis, "identifier")
    assert "call" in values(source, analysis, "identifier")
    assert values(source, analysis, "call_target") == ["call"]
    literals = values(source, analysis, "literal")
    assert "1" in literals and "value=" in literals
    assert not any("{x" in value for value in literals)


def test_python_concatenated_fstrings_keep_literal_text_separate_from_interpolation():
    source = 'def f(x):\n    return f"value={x}" "suffix"\n'
    analysis = analyze_source(source, "python")
    assert len(occurrences(source, analysis, "x")) == 2
    literals = values(source, analysis, "literal")
    assert "value=" in literals and '"suffix"' in literals
    assert not any("{x}" in value for value in literals)


def test_python_match_keywords_wildcards_and_bindings_are_context_sensitive():
    source = 'def f(value, match, case):\n    match value:\n        case {"a": captured}:\n            return captured + case\n        case _:\n            return match\n'
    analysis = analyze_source(source, "python")
    assert len(occurrences(source, analysis, "match")) == 2
    assert len(occurrences(source, analysis, "case")) == 2
    assert not occurrences(source, analysis, "_")
    captured = occurrences(source, analysis, "captured")
    assert captured[0].binding is not None
    assert captured[0].binding == captured[1].binding
    headers = values(source, analysis, "control_header")
    assert (
        "match value:" in headers
        and 'case {"a": captured}:' in headers
        and "case _:" in headers
    )


def test_java_var_is_contextual_keyword_not_an_identifier():
    source = "class D { void f(){var value = 1; consume(value); var();} void var(){} }"
    analysis = analyze_source(source, "java")
    assert len(occurrences(source, analysis, "var")) == 2  # call and method name only
    assert "var value" in values(source, analysis, "declaration_header")


def test_java_resources_and_abstract_methods_have_exact_role_boundaries():
    source = "abstract class D { abstract void g(int a); void f(){try(InputStream in=open(); InputStream out=other(in)){work(in);}catch(Exception ex){throw ex;}finally{cleanup();}} }"
    analysis = analyze_source(source, "java")
    declarations = values(source, analysis, "declaration_header")
    assert "abstract void g(int a)" in declarations
    assert "InputStream in" in declarations and "InputStream out" in declarations
    assert "open()" in values(source, analysis, "assignment_rhs")
    assert "other(in)" in values(source, analysis, "assignment_rhs")
    headers = values(source, analysis, "control_header")
    assert "try(InputStream in=open(); InputStream out=other(in))" in headers
    assert "finally" in headers
    assert not any("try" in header and "work" in header for header in headers)
    resource = occurrences(source, analysis, "in")
    assert len(resource) == 3 and len({span.binding for span in resource}) == 1
    assert resource[0].binding is not None


def test_version_is_explicit_and_unsupported_languages_fail():
    assert SOURCE_ANALYSIS_VERSION >= 1
    assert (
        analyze_source("a = 1", "python").metadata["source_analysis_version"]
        == SOURCE_ANALYSIS_VERSION
    )
    with pytest.raises(ValueError, match="Unsupported"):
        analyze_source("let a=1;", "rust")


@pytest.mark.parametrize(
    "language,source",
    [
        ("python", "def f(a):\n    return (a + 1"),
        ("java", 'class D { String text = "unterminated text'),
    ],
)
def test_incomplete_tokenization_does_not_report_partial_roles_as_complete(
    language, source
):
    analysis = analyze_source(source, language, allow_fragments=True)
    assert analysis.metadata["tokenization_diagnostic"]
    assert not analysis.roles_available
    assert not analysis.spans
