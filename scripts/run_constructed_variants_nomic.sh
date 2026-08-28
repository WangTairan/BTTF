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
MODEL="nomic-ai/nomic-embed-text-v1.5"
MODEL_SLUG="nomic-ai-nomic-embed-text-v1.5"

DATASETS=(
  "datasets/constructed/java-progressive-obfuscation-class-100"
  "datasets/constructed/java-comparative-obfuscation-class-100"
)
DATASET_KEYS=(
  "java_progressive_obfuscation"
  "java_comparative_obfuscation"
)

for index in "${!DATASETS[@]}"; do
  dataset="${DATASETS[$index]}"
  dataset_key="${DATASET_KEYS[$index]}"
  base_table="artifacts/cognascore/features/base/${dataset_key}/${MODEL_SLUG}/features.csv"

  echo "[$((index + 1))/${#DATASETS[@]}] Preparing ${dataset_key}."
  if [[ "${REBUILD_BASE:-0}" == "1" || ! -f "${base_table}" ]]; then
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
      -m src.methods.cognascore.runners.features \
      "${dataset}" \
      --embedding-model "${MODEL}"
  else
    echo "Reusing ${base_table}. Set REBUILD_BASE=1 to replace it."
  fi

  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
    -m src.methods.cognascore.runners.embeddings \
    "${dataset}" \
    --embedding-model "${MODEL}" \
    --device "${DEVICE}" \
    --batch-size "${BATCH_SIZE}" \
    --max-length "${MAX_LENGTH}" \
    --missing-order shortest-first \
    --replace-sources \
    --quiet

  embedding_feature_args=(--resume --update-incomplete)
  if [[ "${UPDATE_ALL:-0}" == "1" ]]; then
    embedding_feature_args=(--resume --update-all)
  fi
  if [[ "${REPLACE_EMBEDDING_FEATURES:-0}" == "1" ]]; then
    embedding_feature_args+=(--replace-existing)
  fi
  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
    -m src.methods.cognascore.runners.embedding_features \
    "${dataset}" \
    --embedding-model "${MODEL}" \
    --max-vectors-per-task 512 \
    "${embedding_feature_args[@]}"
done

echo "Evaluating the frozen CognaScore model on the progressive dataset."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m experiments.cognascore.evaluate_progressive_obfuscation

echo "Evaluating the frozen CognaScore model on the comparative dataset."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m experiments.cognascore.evaluate_constructed_variants \
  --dataset "java_comparative_obfuscation"

echo "Both constructed-dataset evaluations are complete."
