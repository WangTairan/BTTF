#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python}"

"$PYTHON_BIN" -m experiments.dorn.six_dataset_evaluation \
  --folds 10 \
  --ridge-alpha 200
