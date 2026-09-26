#!/usr/bin/env bash
# Read-only release checks: never rebuild embeddings, refit weights, or publish.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_model_pycache}"

for script in scripts/*.sh; do
  bash -n "${script}"
done
export PYTHONPATH="${PWD}/tools/source_interference/src:${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
"${PYTHON_BIN}" -m compileall -q src experiments figures tools/source_interference/src
"${PYTHON_BIN}" -m pytest -q tests
"${PYTHON_BIN}" -m pytest -q -c tools/source_interference/pyproject.toml tools/source_interference/tests
