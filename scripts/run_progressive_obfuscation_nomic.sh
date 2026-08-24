#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYCACHE="${PYTHONPYCACHEPREFIX:-/tmp/readability_pycache}"
DEVICE="${DEVICE:-cpu}"
BATCH_SIZE="${BATCH_SIZE:-64}"
MAX_LENGTH="${MAX_LENGTH:-256}"
DATASET="datasets/constructed/java-progressive-obfuscation-class-100"
MODEL="nomic-ai/nomic-embed-text-v1.5"
MODEL_SLUG="nomic-ai-nomic-embed-text-v1.5"
BASE_TABLE="artifacts/cognascore/features/base/java_progressive_obfuscation/${MODEL_SLUG}/features.csv"

if [[ "${REBUILD_BASE:-0}" == "1" || ! -f "${BASE_TABLE}" ]]; then
  echo "[1/4] Extracting model-independent features."
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
    -m src.methods.cognascore.runners.features \
    "${DATASET}" \
    --embedding-model "${MODEL}"
else
  echo "[1/4] Reusing ${BASE_TABLE}. Set REBUILD_BASE=1 to replace it."
fi

echo "[2/4] Updating Nomic references and embedding only missing texts."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.methods.cognascore.runners.embeddings \
  "${DATASET}" \
  --embedding-model "${MODEL}" \
  --device "${DEVICE}" \
  --batch-size "${BATCH_SIZE}" \
  --max-length "${MAX_LENGTH}" \
  --missing-order shortest-first \
  --replace-sources \
  --quiet

echo "[3/4] Deriving Nomic embedding and clustering features."
EMBEDDING_FEATURE_UPDATE_FLAG="--update-incomplete"
if [[ "${UPDATE_ALL:-0}" == "1" ]]; then
  EMBEDDING_FEATURE_UPDATE_FLAG="--update-all"
fi
EMBEDDING_FEATURE_ARGS=("--resume" "${EMBEDDING_FEATURE_UPDATE_FLAG}")
if [[ "${REPLACE_EMBEDDING_FEATURES:-0}" == "1" ]]; then
  EMBEDDING_FEATURE_ARGS+=("--replace-existing")
fi
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.methods.cognascore.runners.embedding_features \
  "${DATASET}" \
  --embedding-model "${MODEL}" \
  --max-vectors-per-task 512 \
  "${EMBEDDING_FEATURE_ARGS[@]}"

echo "[4/4] Evaluating the frozen six-dataset CognaScore model."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m experiments.cognascore.evaluate_progressive_obfuscation
