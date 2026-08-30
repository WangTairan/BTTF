#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
PYCACHE="${PYTHONPYCACHEPREFIX:-/tmp/readability_pycache}"
DEVICE="${DEVICE:-cpu}"

echo "[1/3] Training and freezing the Mi ConvNetCR reproduction."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.methods.mi_convnet_cr.train \
  --device "${DEVICE}"

echo "[2/3] Evaluating on the external Java interference dataset."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.experiments.evaluate_method \
  datasets/constructed/java-comparative-obfuscation-class-100 \
  --method mi_convnet_cr \
  --prune-retired

echo "[3/3] Summarizing paired interference responses."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m experiments.cognascore.summarize_constructed_method \
  --dataset java_comparative_obfuscation \
  --method mi_convnet_cr
