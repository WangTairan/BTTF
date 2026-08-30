#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m experiments.dorn.six_dataset_evaluation \
  --folds 10 \
  --ridge-alpha 200
