#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
PYCACHE="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/cognascore_pycache}"
DEVICE="${DEVICE:-auto}"

TRANSFORMERS_OFFLINE=0 HF_HUB_OFFLINE=0 \
PYTHONPYCACHEPREFIX="${PYCACHE}" "${PYTHON_BIN}" \
  -m src.methods.cognascore.runners.llm_surprisal_features \
  --model Qwen/Qwen2.5-Coder-0.5B \
  --revision 8123ea2e9354afb7ffcc6c8641d1b2f5ecf18301 \
  --device "${DEVICE}" \
  --window-tokens 512 \
  --stride-tokens 384 \
  --local-block-tokens 32 \
  --tail-fraction 0.20 \
  --checkpoint-every 10 \
  --quiet-reuse
