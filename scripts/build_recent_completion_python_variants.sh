#!/usr/bin/env bash
# Build the full Python original-versus-interference completion task manifest.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
WORKSPACE="${WORKSPACE:-${PWD}/artifacts/source_interference}"
OUTPUT="${OUTPUT:-${WORKSPACE}/data/experiments/recent-repository-completion/python-interference}"
export PYTHONPATH="${PWD}/tools/source_interference/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_completion_pycache}"

"${PYTHON_BIN}" -m readability_experiments.repository_completion.variants \
  --workspace "${WORKSPACE}" \
  --targets "${WORKSPACE}/data/experiments/recent-repository-completion/native-validation/qualified_targets.jsonl" \
  --holes "${WORKSPACE}/data/experiments/recent-repository-completion/native-validation/qualified_holes.jsonl" \
  --output "${OUTPUT}" \
  "$@"
