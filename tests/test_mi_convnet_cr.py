import numpy as np

from src.methods.mi_convnet_cr.model import MiConvNetCR, torch
from src.methods.mi_convnet_cr.representation import (
    CharacterMatrixSpec,
    encode_character_matrix,
    fit_character_matrix_spec,
)


def test_character_matrix_preserves_layout_and_padding() -> None:
    spec = CharacterMatrixSpec(max_lines=3, max_line_width=4)
    matrix = encode_character_matrix("a b\n\tç", spec)

    assert matrix.shape == (3, 4)
    assert matrix.dtype == np.float32
    assert matrix[0, 0] == ord("a") / 256
    assert matrix[0, 1] == ord(" ") / 256
    assert matrix[1, 0] == ord("\t") / 256
    assert matrix[1, 1] == ord("ç") / 256
    assert matrix[2, 0] == -1


def test_fit_spec_and_model_forward() -> None:
    spec = fit_character_matrix_spec(["ab\ncd", "abcdef"])
    assert spec == CharacterMatrixSpec(max_lines=2, max_line_width=6)

    model = MiConvNetCR(line_width=spec.max_line_width)
    batch = torch.from_numpy(
        np.stack(
            [
                encode_character_matrix("ab\ncd", spec),
                encode_character_matrix("abcdef", spec),
            ]
        )
    )
    assert tuple(model(batch).shape) == (2, 2)
