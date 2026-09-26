#!/usr/bin/env bash
# Sequential, incremental causal-LM feature production; no model refitting.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."
PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-${TMPDIR:-/tmp}/readability_model_pycache}"
MODEL_KEY="${MODEL_KEY:-qwen}"
TRUST_REMOTE_CODE=0

case "${MODEL_KEY}" in
  qwen)
    MODEL_NAME="Qwen/Qwen2.5-Coder-0.5B"
    MODEL_REVISION="8123ea2e9354afb7ffcc6c8641d1b2f5ecf18301"
    ;;
  deepseek)
    MODEL_NAME="deepseek-ai/deepseek-coder-1.3b-base"
    MODEL_REVISION="c919139c3a9b4070729c8b2cca4847ab29ca8d94"
    ;;
  opencoder)
    MODEL_NAME="infly/OpenCoder-1.5B-Base"
    MODEL_REVISION="32c4ba568028ffbacc81440697418304bac7f8e2"
    TRUST_REMOTE_CODE=1
    ;;
  *)
    echo "Unknown MODEL_KEY=${MODEL_KEY}; expected qwen, deepseek, or opencoder." >&2
    exit 2
    ;;
esac

if [[ "$#" -eq 0 ]]; then
  set -- \
    datasets/mbjp_dev_dataset/readability_dataset.json \
    datasets/buse \
    datasets/scalabrino/dataset \
    datasets/jetbrains \
    datasets/dorn/dataset \
    datasets/schnappinger \
    datasets/constructed/java-comparative-obfuscation-class-100 \
    datasets/constructed/python-comparative-degradation-class-100
fi

COMMAND=("${PYTHON_BIN}" -m src.methods.readability_model.runners.llm_surprisal_features \
  "$@" \
  --model "${MODEL_NAME}" \
  --revision "${MODEL_REVISION}" \
  --device "${DEVICE:-auto}" \
  --compute-dtype "${COMPUTE_DTYPE:-auto}" \
  --window-tokens 512 \
  --stride-tokens 384 \
  --context-target-tokens 32 \
  --comment-target-tokens 128 \
  --short-context-tokens 32 \
  --long-context-tokens 256 \
  --local-block-tokens 32 \
  --tail-fraction 0.20 \
  --checkpoint-every 1 \
  --quiet-reuse)

if [[ "${TRUST_REMOTE_CODE}" == "1" ]]; then
  COMMAND+=(--trust-remote-code)
fi
if [[ "${LOCAL_FILES_ONLY:-0}" == "1" ]]; then
  COMMAND+=(--local-files-only)
fi

"${COMMAND[@]}"
