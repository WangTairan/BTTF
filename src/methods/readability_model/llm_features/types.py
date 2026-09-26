"""Shared causal-LM model identity and original-source token-loss records."""

from dataclasses import dataclass

DEFAULT_CAUSAL_LM = "Qwen/Qwen2.5-Coder-0.5B"
DEFAULT_CAUSAL_LM_REVISION = "8123ea2e9354afb7ffcc6c8641d1b2f5ecf18301"


@dataclass(frozen=True)
class TokenLoss:
    """Natural-log conditional loss with original Unicode character offsets."""

    token_index: int
    start: int
    end: int
    nll: float
