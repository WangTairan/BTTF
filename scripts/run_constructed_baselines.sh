#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PYCACHE="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_model_pycache}"

if [[ ! -f frozen_models/dorn_retrained/model.json ]]; then
  echo "Missing frozen_models/dorn_retrained/model.json; refusing implicit retraining." >&2
  exit 1
fi

DATASET_PATHS=(
  "datasets/constructed/java-comparative-obfuscation-class-100"
  "datasets/constructed/python-comparative-degradation-class-100"
)
DATASET_KEYS=(
  "java_comparative_obfuscation"
  "python_comparative_degradation"
)

for index in "${!DATASET_PATHS[@]}"; do
  dataset_path="${DATASET_PATHS[$index]}"
  dataset_key="${DATASET_KEYS[$index]}"
  echo "[$((index + 1))/${#DATASET_PATHS[@]}] Evaluating baselines on ${dataset_key}."

  for method in posnett dorn; do
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
      -m src.experiments.evaluate_method \
      "${dataset_path}" \
      --method "${method}" \
      --skip-existing \
      --prune-retired
  done

  PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
    -m src.methods.lloc_baseline.runners \
    --dataset "${dataset_key}" \
    --skip-existing

  for method in posnett dorn lloc; do
    PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
      -m experiments.main.readability_model.evaluation.summarize_constructed_method \
      --dataset "${dataset_key}" \
      --method "${method}"
  done
done

echo "Constructed-dataset baseline evaluation complete."
