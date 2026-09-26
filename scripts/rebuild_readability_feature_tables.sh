#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PYCACHE="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_model_pycache}"
MAX_VECTORS_PER_TASK="${MAX_VECTORS_PER_TASK:-512}"
BASE_ONLY="${BASE_ONLY:-0}"
INCLUDE_CONSTRUCTED_ALL_MODELS="${INCLUDE_CONSTRUCTED_ALL_MODELS:-0}"
if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" != "0" && "${INCLUDE_CONSTRUCTED_ALL_MODELS}" != "1" ]]; then
  echo "INCLUDE_CONSTRUCTED_ALL_MODELS must be 0 or 1." >&2
  exit 2
fi

DATASET_PATHS=(
  "datasets/mbjp_dev_dataset/readability_dataset.json"
  "datasets/buse"
  "datasets/scalabrino/dataset"
  "datasets/jetbrains"
  "datasets/dorn/dataset"
  "datasets/schnappinger"
  "datasets/constructed/java-comparative-obfuscation-class-100"
  "datasets/constructed/python-comparative-degradation-class-100"
)

DATASET_NAMES=(
  "mbjp"
  "buse"
  "scalabrino"
  "jetbrains"
  "dorn"
  "schnappinger"
  "java_comparative_obfuscation"
  "python_comparative_degradation"
)

EMBEDDING_MODELS=(
  "nomic-ai/nomic-embed-text-v1.5"
  "Qwen/Qwen3-Embedding-0.6B"
  "jinaai/jina-embeddings-v2-base-code"
  "Snowflake/snowflake-arctic-embed-m-v2.0"
  "voyageai/voyage-4-nano"
)

EMBEDDING_DATASET_PATHS=("${DATASET_PATHS[@]:0:6}")
if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" == "1" ]]; then
  EMBEDDING_DATASET_PATHS=("${DATASET_PATHS[@]}")
fi

echo "Rebuilding model-independent base features once per dataset."
for index in "${!DATASET_PATHS[@]}"; do
  dataset_path="${DATASET_PATHS[$index]}"
  dataset_name="${DATASET_NAMES[$index]}"
  echo "Base features: ${dataset_name}"
  base_command=(
    "${PYTHON_BIN}" -m src.methods.readability_model.runners.features
    "${dataset_path}"
  )
  if (( index < 6 )) || [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" == "1" ]]; then
    for embedding_model in "${EMBEDDING_MODELS[@]}"; do
      base_command+=(--embedding-model "${embedding_model}")
    done
  else
    base_command+=(--embedding-model "jinaai/jina-embeddings-v2-base-code")
  fi
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${base_command[@]}"
done

if [[ "${BASE_ONLY}" == "1" ]]; then
  echo "BASE_ONLY=1: skipping all embedding-derived feature updates."
else
  echo "Rebuilding embedding-derived feature tables from existing embedding caches."
  for embedding_model in "${EMBEDDING_MODELS[@]}"; do
    echo "Embedding features: ${embedding_model}"
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.readability_model.runners.embedding_features \
      "${EMBEDDING_DATASET_PATHS[@]}" \
      --embedding-model "${embedding_model}" \
      --max-vectors-per-task "${MAX_VECTORS_PER_TASK}" \
      --resume \
      --checkpoint-every 50
  done
  if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" == "0" ]]; then
    echo "Embedding features for the Jina reference model on controlled datasets."
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.readability_model.runners.embedding_features \
      "${DATASET_PATHS[@]:6:2}" \
      --embedding-model "jinaai/jina-embeddings-v2-base-code" \
      --max-vectors-per-task "${MAX_VECTORS_PER_TASK}" \
      --resume \
      --checkpoint-every 50
  fi
fi

echo "Validating feature schema."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.readability_model.runners.validate_feature_tables \
  --dataset mbjp \
  --dataset buse \
  --dataset scalabrino \
  --dataset jetbrains \
  --dataset dorn \
  --dataset schnappinger \
  --embedding-model "nomic-ai/nomic-embed-text-v1.5" \
  --embedding-model "Qwen/Qwen3-Embedding-0.6B" \
  --embedding-model "jinaai/jina-embeddings-v2-base-code" \
  --embedding-model "Snowflake/snowflake-arctic-embed-m-v2.0" \
  --embedding-model "voyageai/voyage-4-nano"

echo "Validating additional datasets."
ADDITIONAL_MODELS=("jinaai/jina-embeddings-v2-base-code")
if [[ "${INCLUDE_CONSTRUCTED_ALL_MODELS}" == "1" ]]; then
  ADDITIONAL_MODELS=("${EMBEDDING_MODELS[@]}")
fi
validation_command=("${PYTHON_BIN}" -m src.methods.readability_model.runners.validate_feature_tables
  --dataset java_comparative_obfuscation
  --dataset python_comparative_degradation)
for embedding_model in "${ADDITIONAL_MODELS[@]}"; do
  validation_command+=(--embedding-model "${embedding_model}")
done
PYTHONPYCACHEPREFIX="${PYCACHE}" "${validation_command[@]}"

echo "Done."
