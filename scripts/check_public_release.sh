#!/usr/bin/env bash
# Offline checks for the publication package; no external data downloads.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/bttf_public_pycache}"
export PYTHONPATH="${PWD}/tools/source_interference/src:${PWD}${PYTHONPATH:+:${PYTHONPATH}}"
for script in scripts/*.sh; do bash -n "${script}"; done
"${PYTHON_BIN}" -m compileall -q src experiments figures tools/readability_viewer
"${PYTHON_BIN}" -m pytest -q \
  tests/test_readability_viewer.py \
  tests/test_viewer_source_access.py \
  tests/test_source_import.py \
  tests/test_static_viewer.py \
  tests/test_direct_llm_archive.py \
  tests/test_publication_contract.py \
  tests/test_documented_commands.py \
  tests/test_third_party_release.py
"${PYTHON_BIN}" -m pytest -q -c tools/source_interference/pyproject.toml tools/source_interference/tests
