from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class MaskConstraints:
    nmin: int
    nmax: int
    lmin: int
    lmax: int

    def validate(self) -> None:
        if self.nmin < 1:
            raise ValueError("nmin must be >= 1")
        if self.nmax < self.nmin:
            raise ValueError("nmax must be >= nmin")
        if self.lmin < 1:
            raise ValueError("lmin must be >= 1")
        if self.lmax < self.lmin:
            raise ValueError("lmax must be >= lmin")


@dataclass(frozen=True)
class MaskSpan:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class MaskedSequence:
    lines: Tuple[str, ...]
    spans: Tuple[MaskSpan, ...]
    granularity: int
    masked_segments: int
    selected_segments: int
    index: Optional[int] = None
    strategy: str = "sequence"
    node_type: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    token_count: Optional[int] = None
    ast_role: Optional[str] = None
    ast_granularity: Optional[str] = None
    node_types: Tuple[str, ...] = ()
    ast_roles: Tuple[str, ...] = ()
    char_spans: Tuple[Tuple[int, int], ...] = ()
    stratum_total: Optional[int] = None
    stratum_sampled: Optional[int] = None
    sampling_seed: Optional[int] = None

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


@dataclass(frozen=True)
class RecoveryResult:
    masked: MaskedSequence
    recovered: str
    expected: str
    completion: str
    completion_line_indexes: Tuple[int, ...]
    alignment_failed: bool
    extraction_failed: bool
    recovery_attempts: int
    similarity: float
    expected_mask_count: Optional[int] = None
    recovered_mask_count: Optional[int] = None
    mask_count_mismatch: Optional[bool] = None


@dataclass(frozen=True)
class ComplexityResult:
    score: Optional[float]
    profile: Tuple[RecoveryResult, ...]
    masks: Tuple[MaskedSequence, ...]
