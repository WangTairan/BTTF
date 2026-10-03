from src.methods.lloc_baseline.runners import logical_loc


def test_java_lloc_counts_declarations_and_statements() -> None:
    source = """
    class Example {
        int field = 1;
        int value() {
            int local = field + 1;
            if (local > 1) return local;
            return 0;
        }
    }
    """
    assert logical_loc(source, "java") == 6


def test_python_lloc_ignores_comments_and_blank_lines() -> None:
    source = """
    # explanation
    def value(x):

        y = x + 1
        if y > 1:
            return y
        return 0
    """
    assert logical_loc(source, "python") == 5


def test_cpp_lloc_uses_cpp_grammar_for_cuda() -> None:
    source = """
    int value(int x) {
        int y = x + 1;
        if (y > 1) return y;
        return 0;
    }
    """
    assert logical_loc(source, "cuda") == 5
