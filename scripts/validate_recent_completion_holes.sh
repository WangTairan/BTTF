#!/usr/bin/env bash
# Validate that every method- and statement-level hole is caught by native tests.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
WORKSPACE="${WORKSPACE:-${PWD}/artifacts/source_interference}"
export PYTHONPATH="${PWD}/tools/source_interference/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_completion_pycache}"

args=(
  --workspace "${WORKSPACE}"
  --manifest "${WORKSPACE}/data/experiments/recent-repository-completion/candidate_manifest.jsonl"
  --output "${WORKSPACE}/data/experiments/recent-repository-completion/native-validation"
  --retain-per-language "${RETAIN_PER_LANGUAGE:-25}"
)
if [[ -n "${PER_LANGUAGE:-}" ]]; then
  args+=(--per-language "${PER_LANGUAGE}")
fi
if [[ "${REPLACE:-0}" == "1" ]]; then
  args+=(--replace)
fi

"${PYTHON_BIN}" -m readability_experiments.repository_completion.validate_manifest "${args[@]}"
