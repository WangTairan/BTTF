from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .extractor import extract_dorn_features


DEFAULT_MODEL_PATH = Path("frozen_models/dorn_retrained/model.json")


@dataclass(frozen=True)
class DornReadabilityResult:
    score: float
    probability: float
    selected_feature_count: int
    model_protocol: str
    raw_features: dict[str, float | None]


def dorn_model(code: str, language: str = "java") -> DornReadabilityResult:
    model_path = Path(os.environ.get("DORN_MODEL_PATH", DEFAULT_MODEL_PATH))
    model = load_model(model_path)
    extracted = extract_dorn_features(code, language)
    values = np.asarray(
        [metric_value(extracted, name) for name in model["selected_features"]],
        dtype=float,
    )
    medians = np.asarray(model["imputation_medians"], dtype=float)
    means = np.asarray(model["standardization_means"], dtype=float)
    scales = np.asarray(model["standardization_scales"], dtype=float)
    coefficients = np.asarray(model["coefficients"], dtype=float)

    values = np.where(np.isfinite(values), values, medians)
    standardized = (values - means) / scales
    logit = float(model["intercept"]) + float(np.dot(coefficients, standardized))
    probability = stable_sigmoid(logit)
    raw_features = {
        name: (float(value) if math.isfinite(float(value)) else None)
        for name, value in zip(model["selected_features"], values)
    }
    return DornReadabilityResult(
        score=probability,
        probability=probability,
        selected_feature_count=len(model["selected_features"]),
        model_protocol=str(model["protocol"]),
        raw_features=raw_features,
    )


def load_model(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"Frozen Dorn model not found: {path}. "
            "Run `python -m src.methods.dorn.train` first."
        )
    model = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "selected_features",
        "imputation_medians",
        "standardization_means",
        "standardization_scales",
        "coefficients",
        "intercept",
        "protocol",
    }
    missing = sorted(required - set(model))
    if missing:
        raise ValueError(f"Invalid Dorn model {path}: missing {missing}")
    return model


def metric_value(metrics: dict[str, float], arff_name: str) -> float:
    if arff_name in metrics:
        return float(metrics[arff_name])
    extractor_name = arff_name.replace("-", " ")
    if extractor_name not in metrics:
        raise KeyError(
            f"Official extractor did not produce required Dorn metric {extractor_name!r}"
        )
    return float(metrics[extractor_name])


def stable_sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)
