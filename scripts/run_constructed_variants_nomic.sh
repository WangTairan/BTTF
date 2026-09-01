#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYCACHE="${PYTHONPYCACHEPREFIX:-/tmp/readability_pycache}"

DATASET_PATHS=(
  "datasets/constructed/java-comparative-obfuscation-class-100"
  "datasets/constructed/python-comparative-degradation-class-100"
)
DATASET_KEYS=(
  "java_comparative_obfuscation"
  "python_comparative_degradation"
)

for index in "${!DATASET_PATHS[@]}"; do
  echo "[$((index + 1))/${#DATASET_PATHS[@]}] Updating ${DATASET_KEYS[$index]}."
  PYTHONPYCACHEPREFIX="${PYCACHE}" \
    bash scripts/update_constructed_nomic_incremental.sh "${DATASET_PATHS[$index]}"
done

echo "Evaluating the frozen CognaScore model on both paired datasets."
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN:-python3}" \
  -m experiments.cognascore.evaluation.evaluate_constructed_variants

echo "Constructed-dataset feature and evaluation pipeline complete."
