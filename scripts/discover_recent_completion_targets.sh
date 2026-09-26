#!/usr/bin/env bash
# Build a hash-pinned 25-Java + 25-Python recent completion target manifest.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
WORKSPACE="${WORKSPACE:-${PWD}/artifacts/source_interference}"
export PYTHONPATH="${PWD}/tools/source_interference/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_completion_pycache}"

"${PYTHON_BIN}" -m readability_experiments.repository_completion.discovery \
  --workspace "${WORKSPACE}" \
  --per-language "${PER_LANGUAGE:-25}" \
  --output "${WORKSPACE}/data/experiments/recent-repository-completion/candidate_manifest.jsonl"
