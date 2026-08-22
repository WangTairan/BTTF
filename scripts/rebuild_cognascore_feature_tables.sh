#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYCACHE="${PYTHONPYCACHEPREFIX:-/tmp/readability_pycache}"
MAX_VECTORS_PER_TASK="${MAX_VECTORS_PER_TASK:-512}"
REBUILD_EMBEDDING_FEATURES="${REBUILD_EMBEDDING_FEATURES:-1}"

DATASET_PATHS=(
  "datasets/mbjp_dev_dataset/readability_dataset.json"
  "datasets/buse"
  "datasets/scalabrino/dataset"
  "datasets/jetbrains"
  "datasets/dorn/dataset"
  "datasets/schnappinger"
  "datasets/readability_dataset_90.jsonl"
  "datasets/readability_binary.jsonl"
)

DATASET_NAMES=(
  "mbjp"
  "buse"
  "scalabrino"
  "jetbrains"
  "dorn"
  "schnappinger"
  "generated_readability_90"
  "generated_binary_readability"
)

EMBEDDING_MODELS=(
  "nomic-ai/nomic-embed-text-v1.5"
  "Qwen/Qwen3-Embedding-0.6B"
  "jinaai/jina-embeddings-v2-base-code"
  "Snowflake/snowflake-arctic-embed-m-v2.0"
  "voyageai/voyage-4-nano"
)

echo "Rebuilding base CognaScore feature tables for every embedding-model slug."
for embedding_model in "${EMBEDDING_MODELS[@]}"; do
  for index in "${!DATASET_PATHS[@]}"; do
    dataset_path="${DATASET_PATHS[$index]}"
    dataset_name="${DATASET_NAMES[$index]}"
    echo "Base features: ${embedding_model} / ${dataset_name}"
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.features \
      "${dataset_path}" \
      --embedding-model "${embedding_model}"
  done
done

if [[ "${REBUILD_EMBEDDING_FEATURES}" != "0" ]]; then
  echo "Rebuilding embedding-derived feature tables from existing embedding caches."
  for embedding_model in "${EMBEDDING_MODELS[@]}"; do
    echo "Embedding features: ${embedding_model}"
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.embedding_features \
      "${DATASET_PATHS[@]}" \
      --embedding-model "${embedding_model}" \
      --max-vectors-per-task "${MAX_VECTORS_PER_TASK}" \
      --replace-existing \
      --resume \
      --update-all \
      --checkpoint-every 50
  done
else
  echo "Skipping embedding-derived feature rebuild because REBUILD_EMBEDDING_FEATURES=0."
fi

echo "Validating feature schema."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.validate_feature_tables \
  --embedding-model "nomic-ai/nomic-embed-text-v1.5" \
  --embedding-model "Qwen/Qwen3-Embedding-0.6B" \
  --embedding-model "jinaai/jina-embeddings-v2-base-code" \
  --embedding-model "Snowflake/snowflake-arctic-embed-m-v2.0" \
  --embedding-model "voyageai/voyage-4-nano"

echo "Done."
