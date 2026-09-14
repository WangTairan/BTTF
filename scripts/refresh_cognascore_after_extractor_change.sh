#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PYCACHE="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/cognascore_pycache}"
BATCH_SIZE="${BATCH_SIZE:-64}"
DEVICE="${DEVICE:-cpu}"
MAX_LENGTH="${MAX_LENGTH:-256}"
INCLUDE_CONSTRUCTED_ALL_MODELS="${INCLUDE_CONSTRUCTED_ALL_MODELS:-0}"
if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" != "0" && "${INCLUDE_CONSTRUCTED_ALL_MODELS}" != "1" ]]; then
  echo "INCLUDE_CONSTRUCTED_ALL_MODELS must be 0 or 1." >&2
  exit 2
fi

CORE_DATASET_PATHS=(
  "datasets/mbjp_dev_dataset/readability_dataset.json"
  "datasets/buse"
  "datasets/scalabrino/dataset"
  "datasets/jetbrains"
  "datasets/dorn/dataset"
  "datasets/schnappinger"
)

NOMIC_ONLY_DATASET_PATHS=(
  "datasets/constructed/java-comparative-obfuscation-class-100"
  "datasets/constructed/python-comparative-degradation-class-100"
)

EMBEDDING_MODELS=(
  "nomic-ai/nomic-embed-text-v1.5"
  "Qwen/Qwen3-Embedding-0.6B"
  "jinaai/jina-embeddings-v2-base-code"
  "Snowflake/snowflake-arctic-embed-m-v2.0"
  "voyageai/voyage-4-nano"
)

MODEL_DATASET_PATHS=("${CORE_DATASET_PATHS[@]}")
if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" == "1" ]]; then
  MODEL_DATASET_PATHS+=("${NOMIC_ONLY_DATASET_PATHS[@]}")
fi

echo "Refreshing embedding source references after extractor changes."
echo "Existing embedding vectors are reused; only newly introduced chunk texts are embedded."
for embedding_model in "${EMBEDDING_MODELS[@]}"; do
  echo "Core-dataset embedding cache refresh: ${embedding_model}"
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.embeddings \
    "${MODEL_DATASET_PATHS[@]}" \
    --embedding-model "${embedding_model}" \
    --device "${DEVICE}" \
    --batch-size "${BATCH_SIZE}" \
    --max-length "${MAX_LENGTH}" \
    --missing-order shortest-first \
    --replace-sources \
    --quiet
done

if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" == "0" ]]; then
  echo "Nomic-only additional-dataset cache refresh."
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.embeddings \
    "${NOMIC_ONLY_DATASET_PATHS[@]}" \
    --embedding-model "nomic-ai/nomic-embed-text-v1.5" \
    --device "${DEVICE}" \
    --batch-size "${BATCH_SIZE}" \
    --max-length "${MAX_LENGTH}" \
    --missing-order shortest-first \
    --replace-sources \
    --quiet
fi

INCLUDE_CONSTRUCTED_ALL_MODELS="${INCLUDE_CONSTRUCTED_ALL_MODELS}" \
  PYTHONPYCACHEPREFIX="${PYCACHE}" bash scripts/rebuild_cognascore_feature_tables.sh
