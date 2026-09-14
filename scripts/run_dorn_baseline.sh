#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python}"

if [[ ! -f frozen_models/dorn_retrained/model.json ]]; then
  "$PYTHON_BIN" -m src.methods.dorn.train
fi

datasets=(
  datasets/mbjp_dev_dataset/readability_dataset.json
  datasets/buse
  datasets/scalabrino/dataset
  datasets/jetbrains
  datasets/dorn/dataset
  datasets/schnappinger
  datasets/constructed/java-comparative-obfuscation-class-100
  datasets/constructed/python-comparative-degradation-class-100
)

for dataset in "${datasets[@]}"; do
  "$PYTHON_BIN" -m src.experiments.evaluate_method \
    "$dataset" \
    --method dorn
done
