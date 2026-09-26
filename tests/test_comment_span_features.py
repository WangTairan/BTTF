from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from experiments.supplementary.comment_validity.comment_span_features import (
    COMMENT,
    DOCUMENTATION_COMMENT,
    FORMS,
    CommentTransform,
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


def example():
    frame = pd.DataFrame({COMMENT: [1.0, 3.0, np.nan], "noncomment_code_bpb": [2.0, 2.0, 2.0]})
    for form in FORMS:
        frame[f"{form}_bpb"] = [1.0, 3.0, np.nan]
        frame[f"{form}_bytes"] = [10.0, 20.0, 0.0]
    return frame


@pytest.mark.parametrize("mode", ["centered_gated", "form_centered_gated", "form_minus_code_centered_gated"])
def test_calibration_uses_training_only_and_missing_is_neutral(mode):
    train = example()
    transform = CommentTransform(mode).fit(train)
    validation = example()
    validation.loc[0, COMMENT] = 100.0
    for form in FORMS:
        validation.loc[0, f"{form}_bpb"] = 100.0
    result, features, probes = transform.transform(validation, [COMMENT])
    assert features == probes
    assert result[probes[0]].tolist() == pytest.approx([98.0, 1.0, 0.0])
    assert transform.means.get("all", transform.means.get("line")) == pytest.approx(0.0 if "minus_code" in mode else 2.0)


def test_form_split_distinguishes_missing_from_zero_raw_difficulty():
    frame = example()
    transform = CommentTransform("form_split_raw").fit(frame)
    result, features, probes = transform.transform(frame, [COMMENT])
    assert len(features) == len(probes) == 3
    assert result.loc[2, probes].isna().all()


def test_documentation_only_replaces_exactly_one_feature():
    frame = example()
    frame["documentation_bpb"] = [2.0, 4.0, np.nan]
    transform = CommentTransform("documentation_only").fit(frame)
    result, features, probes = transform.transform(frame, ["base__x", COMMENT])
    assert features == ["base__x", DOCUMENTATION_COMMENT]
    assert probes == [DOCUMENTATION_COMMENT]
    assert result[DOCUMENTATION_COMMENT].iloc[:2].tolist() == [2.0, 4.0]
    assert pd.isna(result[DOCUMENTATION_COMMENT].iloc[2])


def test_ratio_does_not_invent_epsilon_for_zero_denominator():
    frame = example()
    frame.loc[0, "noncomment_code_bpb"] = 0.0
    result, _, probes = CommentTransform("ratio_to_code").fit(frame).transform(frame, [COMMENT])
    assert pd.isna(result.loc[0, probes[0]])
    assert result.loc[1, probes[0]] == 1.5


def test_no_training_observations_for_form_raises():
    frame = example()
    frame["block_bpb"] = np.nan
    with pytest.raises(ValueError, match="No training observations for block"):
        CommentTransform("form_centered_gated").fit(frame)


def test_form_standardization_uses_train_scale_and_byte_weights():
    frame = example()
    frame["block_bpb"] = [2.0, 6.0, np.nan]
    frame["documentation_bpb"] = [3.0, 9.0, np.nan]
    transform = CommentTransform("form_standardized_gated").fit(frame)
    result, _, probes = transform.transform(frame, [COMMENT])
    assert transform.scales == {"line": 1.0, "block": 2.0, "documentation": 3.0}
    assert result[probes[0]].tolist() == pytest.approx([-1.0, 1.0, 0.0])


def test_form_standardization_rejects_zero_variance_without_magic_epsilon():
    frame = example()
    frame["block_bpb"] = [2.0, 2.0, np.nan]
    with pytest.raises(ValueError, match="Zero training variance for block"):
        CommentTransform("form_standardized_gated").fit(frame)
