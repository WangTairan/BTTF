#!/usr/bin/env bash
# Generate reproduction copies only; never refit a model or rebuild embeddings.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_model_pycache}"
WORKSPACE="${WORKSPACE:-${PWD}/artifacts/source_interference}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${WORKSPACE}/reproductions}"
JAVA_INPUT="${JAVA_INPUT:-${WORKSPACE}/data/base/java-readable-class-100/source-original}"
RAW_ROOT="${RAW_ROOT:-${WORKSPACE}/data/raw}"
SEED="${SEED:-20260823}"
JAVA_OUTPUT="${OUTPUT_ROOT}/java-comparative-obfuscation-class-100"
PYTHON_OUTPUT="${OUTPUT_ROOT}/python-comparative-degradation-class-100"

for input in "${JAVA_INPUT}" "${RAW_ROOT}/django" "${RAW_ROOT}/flask" "${RAW_ROOT}/requests" "${RAW_ROOT}/attrs"; do
  if [[ ! -d "${input}" ]]; then
    printf 'Missing source directory: %s\n' "${input}" >&2
    exit 1
  fi
done
for output in "${JAVA_OUTPUT}" "${PYTHON_OUTPUT}"; do
  if [[ -e "${output}" ]]; then
    printf 'Refusing to overwrite existing dataset: %s\nSet OUTPUT_ROOT to a new directory.\n' "${output}" >&2
    exit 1
  fi
done

"${PYTHON_BIN}" -m readability_data.cli java-interfere \
  --input "${JAVA_INPUT}" --output "${JAVA_OUTPUT}" --seed "${SEED}"
"${PYTHON_BIN}" -m readability_data.cli python-construct \
  --django-root "${RAW_ROOT}/django" --flask-root "${RAW_ROOT}/flask" \
  --requests-root "${RAW_ROOT}/requests" --attrs-root "${RAW_ROOT}/attrs" \
  --output "${PYTHON_OUTPUT}" --per-project 25 --seed "${SEED}"
