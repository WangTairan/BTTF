#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYCACHE="${PYTHONPYCACHEPREFIX:-/tmp/readability_pycache}"
MAX_VECTORS_PER_TASK="${MAX_VECTORS_PER_TASK:-512}"
REBUILD_EMBEDDING_FEATURES="${REBUILD_EMBEDDING_FEATURES:-1}"
BASE_ONLY="${BASE_ONLY:-0}"

DATASET_PATHS=(
  "datasets/mbjp_dev_dataset/readability_dataset.json"
  "datasets/buse"
  "datasets/scalabrino/dataset"
  "datasets/jetbrains"
  "datasets/dorn/dataset"
  "datasets/schnappinger"
  "datasets/generated_readability_90/dataset.jsonl"
  "datasets/constructed/java-progressive-obfuscation-class-100"
)

DATASET_NAMES=(
  "mbjp"
  "buse"
  "scalabrino"
  "jetbrains"
  "dorn"
  "schnappinger"
  "generated_readability_90"
  "java_progressive_obfuscation"
)

EMBEDDING_MODELS=(
  "nomic-ai/nomic-embed-text-v1.5"
  "Qwen/Qwen3-Embedding-0.6B"
  "jinaai/jina-embeddings-v2-base-code"
  "Snowflake/snowflake-arctic-embed-m-v2.0"
  "voyageai/voyage-4-nano"
)

echo "Rebuilding model-independent base features once per dataset."
for index in "${!DATASET_PATHS[@]}"; do
  dataset_path="${DATASET_PATHS[$index]}"
  dataset_name="${DATASET_NAMES[$index]}"
  echo "Base features: ${dataset_name}"
  base_command=(
    "${PYTHON_BIN}" -m src.methods.cognascore.runners.features
    "${dataset_path}"
  )
  for embedding_model in "${EMBEDDING_MODELS[@]}"; do
    base_command+=(--embedding-model "${embedding_model}")
  done
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${base_command[@]}"
done

if [[ "${BASE_ONLY}" == "1" ]]; then
  echo "BASE_ONLY=1: skipping all embedding-derived feature updates."
elif [[ "${REBUILD_EMBEDDING_FEATURES}" != "0" ]]; then
  echo "Rebuilding embedding-derived feature tables from existing embedding caches."
  for embedding_model in "${EMBEDDING_MODELS[@]}"; do
    echo "Embedding features: ${embedding_model}"
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.embedding_features \
      "${DATASET_PATHS[@]:0:6}" \
      --embedding-model "${embedding_model}" \
      --max-vectors-per-task "${MAX_VECTORS_PER_TASK}" \
      --replace-existing \
      --resume \
      --update-all \
      --checkpoint-every 50
  done
  echo "Embedding features for Nomic-only additional datasets."
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.embedding_features \
    "${DATASET_PATHS[@]:6:2}" \
    --embedding-model "nomic-ai/nomic-embed-text-v1.5" \
    --max-vectors-per-task "${MAX_VECTORS_PER_TASK}" \
    --replace-existing \
    --resume \
    --update-all \
    --checkpoint-every 50
else
  echo "Skipping full embedding-derived feature rebuild."
  echo "Updating only Scalabrino-inspired comment alignment columns from existing caches."
  for embedding_model in "${EMBEDDING_MODELS[@]}"; do
    echo "Comment alignment: ${embedding_model}"
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.comment_alignment_features \
      "${DATASET_PATHS[@]:0:6}" \
      --embedding-model "${embedding_model}" \
      --max-vectors-per-type "${MAX_VECTORS_PER_TASK}"
  done
  echo "Comment alignment for Nomic-only additional datasets."
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.comment_alignment_features \
    "${DATASET_PATHS[@]:6:2}" \
    --embedding-model "nomic-ai/nomic-embed-text-v1.5" \
    --max-vectors-per-type "${MAX_VECTORS_PER_TASK}"
fi

echo "Validating feature schema."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.validate_feature_tables \
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

echo "Done."
