from types import SimpleNamespace

import pytest

from experiments.supplementary.comment_validity.comment_span_features import (
    comment_form,
    noncomment_intervals,
)


@pytest.mark.parametrize("source,language,expected", [
    ("// ordinary", "java", "line"),
    ("# ordinary", "python", "line"),
    ("/* ordinary */", "java", "block"),
    ("/** documentation */", "java", "documentation"),
    ('"""documentation"""', "python", "documentation"),
])
def test_forms_use_actual_comment_spans(source, language, expected):
    assert comment_form(source, SimpleNamespace(start=0, end=len(source)), language) == expected


def test_code_complement_merges_overlapping_comment_spans():
    assert noncomment_intervals(10, [(2, 5), (4, 7)]) == [(0, 2), (7, 10)]
