"""Frozen-model inference for the Mi ConvNetCR reproduction."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np

from .model import MiConvNetCR, torch
from .representation import CharacterMatrixSpec, encode_character_matrix


DEFAULT_MODEL_DIR = Path("frozen_models/mi_convnet_cr")


@dataclass(frozen=True)
class MiConvNetCRResult:
    score: float
    unreadable_probability: float
    predicted_label: str
    implementation: str


_MODEL_CACHE: dict[tuple[Path, str], tuple[MiConvNetCR, CharacterMatrixSpec, dict]] = {}


def mi_convnet_cr_model(
    code: str,
    *,
    model_dir: Path = DEFAULT_MODEL_DIR,
    device: str = "cpu",
) -> MiConvNetCRResult:
    model, matrix_spec, manifest = load_frozen_model(model_dir, device=device)
    matrix = encode_character_matrix(code, matrix_spec)
    tensor = torch.from_numpy(np.asarray(matrix)).unsqueeze(0).to(device)
    with torch.no_grad():
        probabilities = torch.softmax(model(tensor), dim=1)[0].cpu().numpy()
    readable = float(probabilities[1])
    unreadable = float(probabilities[0])
    return MiConvNetCRResult(
        score=readable,
        unreadable_probability=unreadable,
        predicted_label="readable" if readable >= 0.5 else "unreadable",
        implementation=str(manifest["implementation"]),
    )


def load_frozen_model(
    model_dir: Path,
    *,
    device: str,
) -> tuple[MiConvNetCR, CharacterMatrixSpec, dict[str, Any]]:
    resolved = model_dir.resolve()
    cache_key = (resolved, device)
    cached = _MODEL_CACHE.get(cache_key)
    if cached is not None:
        return cached
    manifest_path = resolved / "manifest.json"
    weights_path = resolved / "weights.pt"
    if not manifest_path.is_file() or not weights_path.is_file():
        raise FileNotFoundError(
            f"Missing frozen Mi ConvNetCR model under {resolved}. "
            "Run python -m src.methods.mi_convnet_cr.train first."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    matrix_spec = CharacterMatrixSpec.from_dict(manifest["character_matrix"])
    architecture = manifest["architecture"]
    model = MiConvNetCR(
        line_width=matrix_spec.max_line_width,
        filter_heights=tuple(architecture["filter_heights"]),
        feature_maps=int(architecture["feature_maps"]),
        dropout=float(architecture["dropout"]),
    )
    state = torch.load(weights_path, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    payload = (model, matrix_spec, manifest)
    _MODEL_CACHE[cache_key] = payload
    return payload
