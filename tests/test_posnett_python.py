from src.methods.posnett import posnett_model


def test_posnett_python_tokenization_ignores_hash_comments() -> None:
    without_comment = "def add(left, right):\n    return left + right\n"
    with_comment = "# explain the addition\n" + without_comment

    plain = posnett_model(without_comment, language="python")
    commented = posnett_model(with_comment, language="python")

    assert plain.token_count == commented.token_count
    assert plain.vocabulary_size == commented.vocabulary_size
    assert commented.lines == plain.lines + 1


def test_posnett_java_default_is_unchanged() -> None:
    code = "int add(int left, int right) { return left + right; }"
    assert posnett_model(code) == posnett_model(code, language="java")


def test_posnett_cuda_uses_explicit_c_like_tokenization() -> None:
    code = "__global__ void add(float *x) { int i = threadIdx.x; x[i] += 1.0f; }"
    result = posnett_model(code, language="cuda")

    assert result.token_count > 0
    assert result.vocabulary_size > 0
    assert result.halstead_volume > 0


def test_posnett_python_fragment_mode_is_explicit() -> None:
    source = "        value = legacy_call(item)\n        print value\n"

    result = posnett_model(source, language="python", allow_fragments=True)

    assert result.token_count > 0
