#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -ne 1 ]]; then
  echo "Usage: bash scripts/update_constructed_nomic_incremental.sh DATASET_DIR" >&2
  exit 2
fi

DATASET="$1"
if [[ ! -f "${DATASET}/manifest.jsonl" || ! -f "${DATASET}/provenance.json" ]]; then
  echo "Not a constructed dataset directory: ${DATASET}" >&2
  exit 2
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
PYCACHE="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/cognascore_pycache}"
DEVICE="${DEVICE:-cpu}"
BATCH_SIZE="${BATCH_SIZE:-64}"
MAX_LENGTH="${MAX_LENGTH:-256}"
MODEL="nomic-ai/nomic-embed-text-v1.5"

echo "[1/3] Incrementally updating model-independent features by source SHA-256."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.methods.cognascore.runners.features \
  "${DATASET}" \
  --embedding-model "${MODEL}" \
  --resume \
  --quiet-reuse

echo "[2/3] Replacing task source references and embedding only missing text hashes."
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

echo "[3/3] Incrementally updating embedding-derived features by source SHA-256."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.methods.cognascore.runners.embedding_features \
  "${DATASET}" \
  --embedding-model "${MODEL}" \
  --max-vectors-per-task 512 \
  --resume \
  --update-incomplete \
  --checkpoint-every 50 \
  --quiet-reuse

echo "Incremental constructed-dataset update complete."
