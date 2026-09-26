#!/usr/bin/env bash
# Build and natively validate the two-target recent-repository completion pilot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
WORKSPACE="${WORKSPACE:-${PWD}/artifacts/source_interference}"
export PYTHONPATH="${PWD}/tools/source_interference/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_completion_pycache}"

"${PYTHON_BIN}" -m readability_experiments.repository_completion.builder \
  --workspace "${WORKSPACE}" \
  --output "${WORKSPACE}/data/experiments/recent-repository-completion/pilot"
