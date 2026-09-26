"""Bounded, source-aligned causal-LM traces and matched context contrasts.

Each source token is scored exactly once in each complete trace. Short and
long context traces use identical target blocks and target token IDs; only
their preceding context differs. Comment contrasts hold the original code
prefix range and target IDs fixed while deleting comment characters from
that prefix. Neither contrast scores normalized chunk strings.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Literal

# NumPy must initialize its numerical runtime before PyTorch on macOS.
import numpy as np

from .types import DEFAULT_CAUSAL_LM, DEFAULT_CAUSAL_LM_REVISION, TokenLoss

TRACE_BUILD_VERSION = 1
BOUNDARY_POLICY = "bos_else_eos_document_boundary_v1"
COMMENT_BUILD_VERSION = 1
TraceKind = Literal["global", "short", "long"]
TraceCheckpoint = Callable[[str, int, list[TokenLoss]], None]


@dataclass(frozen=True)
class TraceConfiguration:
    model_name: str = DEFAULT_CAUSAL_LM
    revision: str = DEFAULT_CAUSAL_LM_REVISION
    compute_dtype: str = "float32"
    window_tokens: int = 512
    stride_tokens: int = 384
    context_target_tokens: int = 32
    comment_target_tokens: int = 128
    short_context_tokens: int = 32
    long_context_tokens: int = 256
    tokenizer_version: str = version("tokenizers")
    transformers_version: str = version("transformers")
    torch_version: str = version("torch")
    boundary_policy: str = BOUNDARY_POLICY
    trust_remote_code: bool = False
    build_version: int = TRACE_BUILD_VERSION

    def __post_init__(self) -> None:
        if len(self.revision) != 40 or any(
            character not in "0123456789abcdef" for character in self.revision
        ):
            raise ValueError(
                "Trace caching requires a pinned 40-character model revision."
            )
        if self.window_tokens < 2:
            raise ValueError("window_tokens must be at least two.")
        if not 0 < self.stride_tokens < self.window_tokens:
            raise ValueError(
                "stride_tokens must be positive and smaller than the window."
            )
        if self.context_target_tokens < 1:
            raise ValueError("context_target_tokens must be positive.")
        if self.comment_target_tokens < 1:
            raise ValueError("comment_target_tokens must be positive.")
        if not 0 <= self.short_context_tokens < self.long_context_tokens:
            raise ValueError("Context lengths must satisfy 0 <= short < long.")
        if (
            self.context_target_tokens + max(1, self.long_context_tokens)
            > self.window_tokens
        ):
            raise ValueError("Context plus target block exceeds the model window.")
        if (
            self.comment_target_tokens + max(1, self.long_context_tokens)
            > self.window_tokens
        ):
            raise ValueError(
                "Comment context plus target block exceeds the model window."
            )
        if self.compute_dtype not in {"float32", "float16", "bfloat16"}:
            raise ValueError(f"Unsupported computation dtype: {self.compute_dtype!r}")
        if self.boundary_policy != BOUNDARY_POLICY:
            raise ValueError(
                f"Unsupported document boundary policy: {self.boundary_policy!r}"
            )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(asdict(self))

    @property
    def tokenization_fingerprint(self) -> str:
        """Tokenization is independent of inference and summary protocols."""
        return _fingerprint(
            {
                "model_name": self.model_name,
                "revision": self.revision,
                "tokenizer_version": self.tokenizer_version,
                "transformers_version": self.transformers_version,
                "boundary_policy": self.boundary_policy,
                "trust_remote_code": self.trust_remote_code,
            }
        )

    def fingerprint_for(self, kind: str) -> str:
        """Fingerprint only parameters that change this trace's model inputs.

        Short/long/comment inputs do not depend on the global sliding window
        and stride, provided the independently validated capacity can hold them.
        Aggregation block sizes/tail fractions do not enter any trace key.
        """
        payload = {
            "kind": kind,
            "tokenization_fingerprint": self.tokenization_fingerprint,
            "compute_dtype": self.compute_dtype,
            "torch_version": self.torch_version,
            "build_version": self.build_version,
        }
        if kind == "global":
            payload.update(
                window_tokens=self.window_tokens, stride_tokens=self.stride_tokens
            )
        elif kind in {"short", "long"}:
            payload.update(
                target_tokens=self.context_target_tokens,
                prefix_tokens=self.short_context_tokens
                if kind == "short"
                else self.long_context_tokens,
            )
        elif kind == "comment":
            payload.update(
                target_tokens=self.comment_target_tokens,
                prefix_tokens=self.long_context_tokens,
                comment_build_version=COMMENT_BUILD_VERSION,
            )
        else:
            raise ValueError(f"Unknown scoring protocol: {kind!r}")
        return _fingerprint(payload)


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TokenizedSource:
    input_ids: list[int]
    offsets: list[tuple[int, int]]
    boundary_token_id: int

    def __post_init__(self) -> None:
        if len(self.input_ids) != len(self.offsets):
            raise ValueError("Tokenizer IDs and source offsets have different lengths.")
        if not self.input_ids:
            raise ValueError("Source code tokenized to zero tokens.")
        if any(left < 0 or right < left for left, right in self.offsets):
            raise ValueError("Tokenizer returned an invalid source offset.")
        if not any(right > left for left, right in self.offsets):
            raise ValueError("Tokenized source covers no source characters.")


@dataclass(frozen=True)
class CommentTarget:
    comment_start: int
    comment_end: int
    target_start: int
    target_end: int


@dataclass(frozen=True)
class CommentEffect:
    target: CommentTarget
    present_losses: list[TokenLoss]
    removed_losses: list[TokenLoss]
    visible_comment_bytes: int


CommentCheckpoint = Callable[[int, CommentEffect], None]


class LazyCausalScorer:
    """Load a tokenizer/model only when tokenization/inference is required.

    Optional injected tokenizer/model objects support numerical unit tests.
    Loading and inference failures propagate to the caller; no alternative
    model, truncation, or numerical fallback is used.
    """

    def __init__(
        self,
        configuration: TraceConfiguration,
        *,
        device: str,
        cache_dir: Path | str = "models",
        local_files_only: bool = False,
        tokenizer=None,
        model=None,
    ) -> None:
        self.configuration = configuration
        self.device = device
        self.cache_dir = Path(cache_dir)
        self.local_files_only = local_files_only
        self._tokenizer = tokenizer
        self._model = model
        self._model_validated = False

    @property
    def model_loaded(self) -> bool:
        return self._model is not None

    def _ensure_tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.configuration.model_name,
                revision=self.configuration.revision,
                cache_dir=self.cache_dir,
                use_fast=True,
                local_files_only=self.local_files_only,
                trust_remote_code=self.configuration.trust_remote_code,
            )
        if not self._tokenizer.is_fast and not _supports_sentencepiece_offsets(
            self._tokenizer
        ):
            raise RuntimeError(
                "Source alignment requires either a fast tokenizer or an audited "
                "SentencePiece tokenizer exposing sp_model and pre_tokenizer."
            )
        return self._tokenizer

    def _ensure_model(self):
        if self._model is None:
            import torch
            from transformers import AutoModelForCausalLM

            self._model = AutoModelForCausalLM.from_pretrained(
                self.configuration.model_name,
                revision=self.configuration.revision,
                cache_dir=self.cache_dir,
                dtype=getattr(torch, self.configuration.compute_dtype),
                local_files_only=self.local_files_only,
                trust_remote_code=self.configuration.trust_remote_code,
            )
            self._model.to(self.device)
            self._model.eval()
        if not self._model_validated:
            context_limit = int(
                getattr(self._model.config, "max_position_embeddings", 0) or 0
            )
            if context_limit and self.configuration.window_tokens > context_limit:
                raise ValueError(
                    f"The requested window {self.configuration.window_tokens} exceeds "
                    f"the model context limit {context_limit}."
                )
            resolved_revision = getattr(self._model.config, "_commit_hash", None)
            requested_revision = self.configuration.revision
            if (
                len(requested_revision) == 40
                and resolved_revision
                and str(resolved_revision) != requested_revision
            ):
                raise RuntimeError(
                    "Loaded model revision does not match the pinned revision."
                )
            self._model_validated = True
        return self._model

    def tokenize(self, source: str) -> TokenizedSource:
        tokenizer = self._ensure_tokenizer()
        if tokenizer.is_fast:
            encoding = tokenizer(
                source, add_special_tokens=False, return_offsets_mapping=True
            )
            input_ids = [int(value) for value in encoding["input_ids"]]
            offsets = [
                (int(left), int(right)) for left, right in encoding["offset_mapping"]
            ]
        else:
            input_ids, offsets = _sentencepiece_tokenize_with_offsets(
                tokenizer, source
            )
        boundary = tokenizer.bos_token_id
        if boundary is None:
            # Qwen2.5-Coder has EOS but no distinct BOS: EOS is an explicitly
            # documented document-boundary context, not a fallback prediction.
            boundary = tokenizer.eos_token_id
        if boundary is None:
            raise RuntimeError(
                "Tokenizer supplies neither a BOS nor an EOS boundary token."
            )
        tokenized = TokenizedSource(
            input_ids=input_ids,
            offsets=offsets,
            boundary_token_id=int(boundary),
        )
        if any(right > len(source) for _, right in tokenized.offsets):
            raise ValueError("Tokenizer offsets extend beyond the original source.")
        return tokenized
    def score_trace(
        self,
        tokenized: TokenizedSource,
        *,
        kind: TraceKind,
        existing_losses: Sequence[TokenLoss] = (),
        checkpoint: TraceCheckpoint | None = None,
    ) -> list[TokenLoss]:
        """Return a complete original-token loss trace, resuming a prefix.

        The checkpoint receives newly scored losses and the next unscored
        original token index after each bounded forward pass.
        """
        if kind not in {"global", "short", "long"}:
            raise ValueError(f"Unknown loss trace kind: {kind!r}")
        rows = list(existing_losses)
        self._validate_existing_trace(tokenized, rows)
        configuration = self.configuration
        target_size = (
            configuration.stride_tokens
            if kind == "global"
            else configuration.context_target_tokens
        )
        context_size = {
            "global": configuration.window_tokens - configuration.stride_tokens,
            "short": configuration.short_context_tokens,
            "long": configuration.long_context_tokens,
        }[kind]
        target_start = len(rows)
        if target_start < len(tokenized.input_ids) and target_start % target_size:
            raise ValueError(
                "A resumed trace must end at a complete target-block boundary."
            )
        while target_start < len(tokenized.input_ids):
            target_end = min(target_start + target_size, len(tokenized.input_ids))
            prefix_start = max(0, target_start - context_size)
            prefix = tokenized.input_ids[prefix_start:target_start]
            if prefix_start == 0 and len(prefix) < context_size:
                # Include the boundary exactly when it lies inside the fixed
                # prefix budget, matching the original global sliding scheme.
                prefix = [tokenized.boundary_token_id, *prefix]
            if not prefix:
                prefix = [tokenized.boundary_token_id]
            new_rows = self._score_targets(
                prefix,
                tokenized.input_ids[target_start:target_end],
                range(target_start, target_end),
                tokenized.offsets,
            )
            rows.extend(new_rows)
            target_start = target_end
            if checkpoint is not None:
                checkpoint(kind, target_start, new_rows)
        return rows

    def score_comment_effects(
        self,
        source: str,
        tokenized: TokenizedSource,
        targets: Sequence[CommentTarget],
        *,
        existing_effects: Sequence[CommentEffect] = (),
        checkpoint: CommentCheckpoint | None = None,
    ) -> list[CommentEffect]:
        """Contrast front comments against their following code statements.

        Targets must be scope-validated by source analysis. Trailing comments
        and comments without following code are not targets. A very long
        following statement contributes only its first bounded target block;
        this limitation applies identically to both conditions.
        """
        effects = list(existing_effects)
        if len(effects) > len(targets):
            raise ValueError("Cached comment effects exceed the source targets.")
        for cached, requested in zip(effects, targets):
            if cached.target != requested:
                raise ValueError(
                    "Cached comment target does not match source analysis."
                )
            expected_indices = [
                index
                for index, (left, right) in enumerate(tokenized.offsets)
                if requested.target_start <= left < right <= requested.target_end
            ][: self.configuration.comment_target_tokens]
            for condition in (cached.present_losses, cached.removed_losses):
                if [row.token_index for row in condition] != expected_indices:
                    raise ValueError(
                        "Cached comment contrast has mismatched target tokens."
                    )
                for row in condition:
                    if (row.start, row.end) != tokenized.offsets[row.token_index]:
                        raise ValueError("Cached comment loss is not source-aligned.")
                    if not math.isfinite(row.nll) or row.nll < 0.0:
                        raise ValueError("Cached comment loss is invalid.")
            if cached.visible_comment_bytes <= 0:
                raise ValueError(
                    "Cached comment effect has no visible comment context."
                )
        tokenizer = None
        for target_index in range(len(effects), len(targets)):
            target = targets[target_index]
            if not (
                0
                <= target.comment_start
                < target.comment_end
                <= target.target_start
                < target.target_end
                <= len(source)
            ):
                raise ValueError(
                    "A comment contrast requires a strictly preceding comment."
                )
            indices = [
                index
                for index, (left, right) in enumerate(tokenized.offsets)
                if target.target_start <= left < right <= target.target_end
            ][: self.configuration.comment_target_tokens]
            if not indices:
                raise ValueError(
                    "A comment target contains no complete original source token."
                )
            if indices != list(range(indices[0], indices[-1] + 1)):
                raise ValueError(
                    "Comment target tokens must form a contiguous source block."
                )
            first_target = indices[0]
            prefix_start = max(0, first_target - self.configuration.long_context_tokens)
            prefix_char_start = tokenized.offsets[prefix_start][0]
            prefix_char_end = tokenized.offsets[first_target][0]
            visible_start = max(prefix_char_start, target.comment_start)
            visible_end = min(prefix_char_end, target.comment_end)
            if visible_start >= visible_end:
                raise ValueError(
                    "The front comment is outside the bounded target prefix."
                )
            original_prefix = tokenized.input_ids[prefix_start:first_target]
            boundary_included = (
                prefix_start == 0
                and len(original_prefix) < self.configuration.long_context_tokens
            )
            if boundary_included:
                original_prefix = [tokenized.boundary_token_id, *original_prefix]
            if not original_prefix:
                original_prefix = [tokenized.boundary_token_id]
            # Retokenize only the exact, bounded original prefix after deleting
            # comment characters. This avoids deleting non-comment code when a
            # BPE token straddles a comment boundary, and never adds older code.
            removed_prefix_source = (
                source[prefix_char_start:visible_start]
                + source[visible_end:prefix_char_end]
            )
            if tokenizer is None:
                tokenizer = self._ensure_tokenizer()
            removed_encoding = tokenizer(
                removed_prefix_source, add_special_tokens=False
            )
            removed_prefix = [int(value) for value in removed_encoding["input_ids"]]
            if boundary_included:
                removed_prefix = [tokenized.boundary_token_id, *removed_prefix]
            if not removed_prefix:
                removed_prefix = [tokenized.boundary_token_id]
            target_ids = [tokenized.input_ids[index] for index in indices]
            if (
                max(len(original_prefix), len(removed_prefix)) + len(target_ids)
                > self.configuration.window_tokens
            ):
                raise ValueError(
                    "The comment counterfactual exceeds the bounded model window."
                )
            present = self._score_targets(
                original_prefix, target_ids, indices, tokenized.offsets
            )
            removed = self._score_targets(
                removed_prefix, target_ids, indices, tokenized.offsets
            )
            effect = CommentEffect(
                target=target,
                present_losses=present,
                removed_losses=removed,
                visible_comment_bytes=len(
                    source[visible_start:visible_end].encode("utf-8")
                ),
            )
            effects.append(effect)
            if checkpoint is not None:
                checkpoint(target_index + 1, effect)
        return effects

    def _score_targets(
        self,
        prefix: list[int],
        target_ids: list[int],
        indices: Sequence[int],
        offsets: Sequence[tuple[int, int]],
    ) -> list[TokenLoss]:
        import torch
        from torch.nn import functional

        if not prefix or not target_ids or len(target_ids) != len(indices):
            raise ValueError(
                "A conditional score requires a prefix and aligned target IDs."
            )
        if len(prefix) + len(target_ids) > self.configuration.window_tokens:
            raise ValueError("A forward pass would exceed the configured token window.")
        model = self._ensure_model()
        inputs = torch.tensor(
            [prefix + target_ids], dtype=torch.long, device=self.device
        )
        with torch.inference_mode():
            output = model(input_ids=inputs, use_cache=False)
            logits = output.logits
            target_logits = logits[
                0, len(prefix) - 1 : len(prefix) + len(target_ids) - 1, :
            ].float()
            labels = inputs[0, len(prefix) :]
            values = functional.cross_entropy(target_logits, labels, reduction="none")
            nlls = values.detach().to("cpu", dtype=torch.float32).tolist()
            del labels, target_logits, values, logits, output
        del inputs
        if not np.isfinite(nlls).all() or any(value < 0.0 for value in nlls):
            raise RuntimeError(
                "The causal model produced an invalid target token loss."
            )
        return [
            TokenLoss(
                int(index), int(offsets[index][0]), int(offsets[index][1]), float(nll)
            )
            for index, nll in zip(indices, nlls)
        ]

    @staticmethod
    def _validate_existing_trace(
        tokenized: TokenizedSource, existing: Sequence[TokenLoss]
    ) -> None:
        if len(existing) > len(tokenized.input_ids):
            raise ValueError("Cached trace exceeds the original source token count.")
        for index, row in enumerate(existing):
            if (
                row.token_index != index
                or (row.start, row.end) != tokenized.offsets[index]
            ):
                raise ValueError(
                    "Cached losses are not an aligned contiguous source prefix."
                )
            if not math.isfinite(row.nll) or row.nll < 0.0:
                raise ValueError("Cached token loss is invalid.")


def _supports_sentencepiece_offsets(tokenizer) -> bool:
    """Return whether exact offsets can be reconstructed from tokenizer internals."""
    return hasattr(tokenizer, "sp_model") and hasattr(tokenizer, "pre_tokenizer")


def _sentencepiece_tokenize_with_offsets(
    tokenizer, source: str
) -> tuple[list[int], list[tuple[int, int]]]:
    """Reconstruct exact character offsets for audited slow SentencePiece tokenizers.

    OpenCoder first partitions source text with a Rust ``Split`` pre-tokenizer and
    then applies SentencePiece independently to each partition. SentencePiece's
    proto output reports UTF-8 byte offsets, so they are converted back to Python
    character offsets here. The resulting IDs must exactly match the official
    tokenizer; otherwise alignment fails rather than silently approximating it.
    """
    if not _supports_sentencepiece_offsets(tokenizer):
        raise RuntimeError("Tokenizer does not expose the required alignment APIs.")

    input_ids: list[int] = []
    offsets: list[tuple[int, int]] = []
    for text, (source_start, source_end) in tokenizer.pre_tokenizer.pre_tokenize_str(
        source
    ):
        if source[source_start:source_end] != text:
            raise ValueError("Pre-tokenizer offsets do not reproduce the source text.")
        byte_to_character = {0: 0}
        byte_position = 0
        for character_position, character in enumerate(text, start=1):
            byte_position += len(character.encode("utf-8"))
            byte_to_character[byte_position] = character_position

        proto = tokenizer.sp_model.encode(text, return_type="proto")
        for piece in proto.pieces:
            left = int(piece.begin)
            right = int(piece.end)
            if left not in byte_to_character or right not in byte_to_character:
                raise ValueError(
                    "SentencePiece returned an offset inside a UTF-8 character."
                )
            input_ids.append(int(piece.id))
            offsets.append(
                (
                    source_start + byte_to_character[left],
                    source_start + byte_to_character[right],
                )
            )

    official_ids = [
        int(value)
        for value in tokenizer(source, add_special_tokens=False)["input_ids"]
    ]
    if input_ids != official_ids:
        raise ValueError(
            "Reconstructed SentencePiece IDs differ from the official tokenizer."
        )
    return input_ids, offsets
