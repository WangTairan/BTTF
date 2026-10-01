"""Repository-relative paths for readability artifacts and research results."""

from pathlib import Path


ARTIFACT_ROOT = Path("artifacts/cognascore")
EMBEDDING_CACHE_ROOT = ARTIFACT_ROOT / "embeddings"
BASE_FEATURE_ROOT = ARTIFACT_ROOT / "features" / "base"
EMBEDDING_FEATURE_ROOT = ARTIFACT_ROOT / "features" / "embedding"
LLM_FEATURE_ROOT = ARTIFACT_ROOT / "features" / "llm"
LLM_SURPRISAL_CACHE_ROOT = ARTIFACT_ROOT / "llm_surprisal"
CALIBRATION_ROOT = ARTIFACT_ROOT / "calibration"
TRAINED_MODEL_ROOT = Path("frozen_models/cognascore")
EXPERIMENT_RESULTS_ROOT = Path("results/experiments/readability_model")
