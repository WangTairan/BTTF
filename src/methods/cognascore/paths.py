"""Canonical local paths for CognaScore artifacts and research results."""

from pathlib import Path


ARTIFACT_ROOT = Path("artifacts/cognascore")
EMBEDDING_CACHE_ROOT = ARTIFACT_ROOT / "embeddings"
BASE_FEATURE_ROOT = ARTIFACT_ROOT / "features" / "base"
EMBEDDING_FEATURE_ROOT = ARTIFACT_ROOT / "features" / "embedding"
CALIBRATION_ROOT = ARTIFACT_ROOT / "calibration"
TRAINED_MODEL_ROOT = Path("frozen_models/cognascore")
EXPERIMENT_RESULTS_ROOT = Path("results/experiments/cognascore")
