#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYCACHE="${PYTHONPYCACHEPREFIX:-/tmp/readability_pycache}"
BATCH_SIZE="${BATCH_SIZE:-64}"
DEVICE="${DEVICE:-cpu}"
MAX_LENGTH="${MAX_LENGTH:-256}"

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

EMBEDDING_MODELS=(
  "nomic-ai/nomic-embed-text-v1.5"
  "Qwen/Qwen3-Embedding-0.6B"
  "jinaai/jina-embeddings-v2-base-code"
  "Snowflake/snowflake-arctic-embed-m-v2.0"
  "voyageai/voyage-4-nano"
)

echo "Refreshing embedding source references after extractor changes."
echo "Existing embedding vectors are reused; only newly introduced chunk texts are embedded."
for embedding_model in "${EMBEDDING_MODELS[@]}"; do
  echo "Embedding cache refresh: ${embedding_model}"
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" -m src.methods.cognascore.runners.embeddings \
    "${DATASET_PATHS[@]}" \
    --embedding-model "${embedding_model}" \
    --device "${DEVICE}" \
    --batch-size "${BATCH_SIZE}" \
    --max-length "${MAX_LENGTH}" \
    --missing-order shortest-first \
    --replace-sources \
    --quiet
done

PYTHONPYCACHEPREFIX="${PYCACHE}" bash scripts/rebuild_cognascore_feature_tables.sh
