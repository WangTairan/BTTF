#!/usr/bin/env bash
# Build and evaluate a cheap Python-only repository-completion solvability pilot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
WORKSPACE="${WORKSPACE:-${PWD}/artifacts/source_interference}"
LIMIT_TARGETS="${LIMIT_TARGETS:-5}"
MODEL="${MODEL:-deepseek-flash}"
TASKS="${WORKSPACE}/data/experiments/recent-repository-completion/model-tasks/python-shortest-${LIMIT_TARGETS}.jsonl"
RESULTS="${PWD}/results/experiments/source_interference/deepseek-recent-completion-python-pilot"
export PYTHONPATH="${PWD}/tools/source_interference/src${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_completion_pycache}"

"${PYTHON_BIN}" -m readability_experiments.repository_completion.tasks \
  --workspace "${WORKSPACE}" \
  --language python \
  --limit-targets "${LIMIT_TARGETS}" \
  --shortest-first \
  --output "${TASKS}"

"${PYTHON_BIN}" -m readability_experiments.deepseek_cli run \
  --workspace "${WORKSPACE}" \
  --input "${TASKS}" \
  --output-root "${RESULTS}" \
  --models "${MODEL}" \
  --max-tokens 4000 \
  --thinking enabled \
  --reasoning-effort low \
  --validation-timeout-seconds 180 \
  --trigger-tests-only
