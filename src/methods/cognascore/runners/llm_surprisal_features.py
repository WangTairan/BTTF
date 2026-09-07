from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn.functional as F

import transformers.utils.import_utils as transformers_import_utils

transformers_import_utils._torchvision_available = False

from transformers import AutoModelForCausalLM, AutoTokenizer

from src.datasets import load_code_dataset
from src.experiments.paths import dataset_name_for_path
from src.experiments.registry import DATASETS

from ..dataset_io import item_source_sha256
from ..llm_surprisal import (
    LLM_SURPRISAL_FEATURE_NAMES,
    DEFAULT_CAUSAL_LM,
    DEFAULT_CAUSAL_LM_REVISION,
    SurprisalConfiguration,
    SurprisalFeatureCache,
    TokenLoss,
    aggregate_surprisal_features,
    identifier_spans,
)
from ..paths import LLM_FEATURE_ROOT, LLM_SURPRISAL_CACHE_ROOT
from ..results import model_slug


DEFAULT_DATASETS = (
    "mbjp",
    "buse",
    "scalabrino",
    "jetbrains",
    "dorn",
    "schnappinger",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute incremental causal-code-LM surprisal features."
    )
    parser.add_argument(
        "datasets",
        nargs="*",
        type=Path,
        help="Dataset paths. Defaults to the six human-rated datasets.",
    )
    parser.add_argument("--model", default=DEFAULT_CAUSAL_LM)
    parser.add_argument("--revision", default=DEFAULT_CAUSAL_LM_REVISION)
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    parser.add_argument("--window-tokens", type=int, default=512)
    parser.add_argument("--stride-tokens", type=int, default=384)
    parser.add_argument("--local-block-tokens", type=int, default=32)
    parser.add_argument("--tail-fraction", type=float, default=0.20)
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--task-id",
        action="append",
        help="Score only the requested task ID. Repeat to select several tasks.",
    )
    parser.add_argument("--cache-root", type=Path, default=LLM_SURPRISAL_CACHE_ROOT)
    parser.add_argument("--output-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--quiet-reuse", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _validate_args(args)
    device = _resolve_device(args.device)
    dtype = torch.float16 if device in {"mps", "cuda"} else torch.float32
    print(f"Loading {args.model} ({args.revision}) on {device} with {dtype}.", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        revision=args.revision,
        cache_dir="models",
        use_fast=True,
    )
    if not tokenizer.is_fast:
        raise RuntimeError("A fast tokenizer with offset mappings is required.")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        revision=args.revision,
        cache_dir="models",
        dtype=dtype,
    )
    model.to(device)
    model.eval()
    model_context_limit = int(getattr(model.config, "max_position_embeddings", 0) or 0)
    if model_context_limit and args.window_tokens > model_context_limit:
        raise ValueError(
            f"--window-tokens={args.window_tokens} exceeds the model context limit "
            f"of {model_context_limit}."
        )
    boundary_token_id = tokenizer.bos_token_id
    if boundary_token_id is None:
        boundary_token_id = tokenizer.eos_token_id
    if boundary_token_id is None:
        raise RuntimeError("The tokenizer provides neither a BOS nor an EOS boundary token.")
    resolved_revision = str(getattr(model.config, "_commit_hash", None) or args.revision)
    configuration = SurprisalConfiguration(
        model_name=args.model,
        resolved_revision=resolved_revision,
        window_tokens=args.window_tokens,
        stride_tokens=args.stride_tokens,
        local_block_tokens=args.local_block_tokens,
        tail_fraction=args.tail_fraction,
    )
    print(
        f"Resolved model revision {resolved_revision}; configuration "
        f"{configuration.fingerprint[:12]}.",
        flush=True,
    )

    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASETS]
    cache_path = args.cache_root / model_slug(args.model) / "features.sqlite"
    with SurprisalFeatureCache(cache_path) as cache:
        for dataset_path in dataset_paths:
            _process_dataset(
                dataset_path=dataset_path,
                args=args,
                tokenizer=tokenizer,
                model=model,
                device=device,
                boundary_token_id=int(boundary_token_id),
                configuration=configuration,
                cache=cache,
            )


def _process_dataset(
    *,
    dataset_path: Path,
    args: argparse.Namespace,
    tokenizer,
    model,
    device: str,
    boundary_token_id: int,
    configuration: SurprisalConfiguration,
    cache: SurprisalFeatureCache,
) -> None:
    dataset = dataset_name_for_path(dataset_path)
    items = load_code_dataset(dataset_path)
    full_dataset_size = len(items)
    partial_selection = bool(args.task_id or args.limit is not None)
    if args.task_id:
        requested = set(args.task_id)
        items = [item for item in items if item.task_id in requested]
        missing = requested - {item.task_id for item in items}
        if missing:
            raise ValueError(
                f"Task IDs not found in {dataset}: {', '.join(sorted(missing))}"
            )
    if args.limit is not None:
        items = items[: args.limit]
    output_dir = args.output_root / dataset / model_slug(args.model)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "features.csv"
    metadata_path = output_dir / "metadata.json"
    rows = []
    computed = 0
    reused = 0
    for index, item in enumerate(items, start=1):
        source_hash = item_source_sha256(item)
        features = cache.get(source_hash, configuration.fingerprint)
        if features is None:
            print(f"[{index}/{len(items)}] Scoring {dataset} {item.task_id}", flush=True)
            try:
                # Score original source, including comments and strings.
                # Identifier-only lexical masking is applied separately below
                # for loss aggregation, never as an experimental intervention.
                encoding = tokenizer(
                    item.content,
                    add_special_tokens=False,
                    return_offsets_mapping=True,
                )
                input_ids = [int(value) for value in encoding["input_ids"]]
                offsets = [(int(left), int(right)) for left, right in encoding["offset_mapping"]]
                losses = _score_tokens(
                    input_ids=input_ids,
                    offsets=offsets,
                    model=model,
                    device=device,
                    boundary_token_id=boundary_token_id,
                    window_tokens=args.window_tokens,
                    stride_tokens=args.stride_tokens,
                )
                language = str(item.metadata.get("language", "java"))
                features = aggregate_surprisal_features(
                    item.content,
                    losses,
                    identifier_spans=identifier_spans(
                        item.content,
                        language=language,
                        allow_fragments=item.metadata.get("source_form") == "snippet",
                    ),
                    local_block_tokens=args.local_block_tokens,
                    tail_fraction=args.tail_fraction,
                )
                cache.upsert(
                    source_sha256=source_hash,
                    configuration=configuration,
                    token_count=len(input_ids),
                    features=features,
                )
            except Exception as exc:
                _append_failure(
                    output_dir / "failures.jsonl",
                    dataset=dataset,
                    task_id=item.task_id,
                    item_index=index,
                    source_sha256=source_hash,
                    configuration=configuration,
                    error=exc,
                )
                raise
            computed += 1
            action = "Scored"
        else:
            reused += 1
            action = "Reused"
        rows.append(
            {
                "dataset": dataset,
                "task_id": item.task_id,
                "readability_score": item.readability_score,
                **features,
            }
        )
        if action == "Scored" or not args.quiet_reuse:
            print(f"[{index}/{len(items)}] {action} {dataset} {item.task_id}", flush=True)
        if index % args.checkpoint_every == 0:
            _write_table(csv_path, rows)
            _write_metadata(
                metadata_path,
                dataset=dataset,
                dataset_path=dataset_path,
                configuration=configuration,
                completed=len(rows),
                expected=full_dataset_size,
                computed=computed,
                reused=reused,
                complete=False,
            )
            print(f"Checkpointed {len(rows)} rows to {csv_path}", flush=True)
    _write_table(csv_path, rows)
    _write_metadata(
        metadata_path,
        dataset=dataset,
        dataset_path=dataset_path,
        configuration=configuration,
        completed=len(rows),
        expected=full_dataset_size,
        computed=computed,
        reused=reused,
        complete=not partial_selection and len(rows) == full_dataset_size,
    )
    print(f"Wrote {csv_path} (scored={computed}, reused={reused})", flush=True)


def _score_tokens(
    *,
    input_ids: list[int],
    offsets: list[tuple[int, int]],
    model,
    device: str,
    boundary_token_id: int,
    window_tokens: int,
    stride_tokens: int,
) -> list[TokenLoss]:
    if len(input_ids) != len(offsets):
        raise ValueError("Tokenizer IDs and offsets have different lengths.")
    if not input_ids:
        raise ValueError("Source code tokenized to zero tokens.")
    # The document boundary makes the first source token scoreable and also
    # gives one-token snippets a mathematically defined conditional loss.
    scored_input_ids = [boundary_token_id, *input_ids]
    scored_offsets = [(0, 0), *offsets]
    rows: list[TokenLoss] = []
    target_start = 1
    prefix_tokens = window_tokens - stride_tokens
    while target_start < len(scored_input_ids):
        target_end = min(target_start + stride_tokens, len(scored_input_ids))
        input_start = max(0, target_start - prefix_tokens)
        window = torch.tensor(
            [scored_input_ids[input_start:target_end]],
            dtype=torch.long,
            device=device,
        )
        with torch.inference_mode():
            logits = model(input_ids=window, use_cache=False).logits
            token_nll = F.cross_entropy(
                # Keep compact model weights on FP16 MPS/CUDA, but calculate
                # log-sum-exp in FP32 so rare tokens cannot overflow the loss.
                logits[:, :-1, :].float().transpose(1, 2),
                window[:, 1:],
                reduction="none",
            )[0]
        first_local_target = target_start - input_start
        last_local_target = target_end - input_start
        selected = token_nll[first_local_target - 1:last_local_target - 1]
        selected_values = selected.detach().to("cpu", dtype=torch.float32).tolist()
        for global_index, nll in zip(range(target_start, target_end), selected_values):
            left, right = scored_offsets[global_index]
            rows.append(TokenLoss(global_index - 1, left, right, float(nll)))
        target_start = target_end
    if len(rows) != len(input_ids):
        raise RuntimeError(
            f"Expected {len(input_ids)} token losses, obtained {len(rows)}."
        )
    return rows


def _write_table(path: Path, rows: list[dict]) -> None:
    temporary = path.with_suffix(".csv.tmp")
    fieldnames = ["dataset", "task_id", "readability_score", *LLM_SURPRISAL_FEATURE_NAMES]
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _write_metadata(
    path: Path,
    *,
    dataset: str,
    dataset_path: Path,
    configuration: SurprisalConfiguration,
    completed: int,
    expected: int,
    computed: int,
    reused: int,
    complete: bool,
) -> None:
    payload = {
        "dataset": dataset,
        "dataset_path": str(dataset_path),
        "feature_family": "causal_llm_surprisal",
        "features": list(LLM_SURPRISAL_FEATURE_NAMES),
        "configuration": {
            "model_name": configuration.model_name,
            "resolved_revision": configuration.resolved_revision,
            "window_tokens": configuration.window_tokens,
            "stride_tokens": configuration.stride_tokens,
            "local_block_tokens": configuration.local_block_tokens,
            "tail_fraction": configuration.tail_fraction,
            "build_version": configuration.build_version,
            "configuration_sha256": configuration.fingerprint,
        },
        "completed_rows": completed,
        "expected_rows": expected,
        "computed_rows": computed,
        "reused_rows": reused,
        "complete": complete,
    }
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _append_failure(
    path: Path,
    *,
    dataset: str,
    task_id: str,
    item_index: int,
    source_sha256: str,
    configuration: SurprisalConfiguration,
    error: Exception,
) -> None:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset,
        "task_id": task_id,
        "item_index": item_index,
        "source_sha256": source_sha256,
        "configuration_sha256": configuration.fingerprint,
        "error_type": type(error).__name__,
        "error": repr(error),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _resolve_device(requested: str) -> str:
    if requested != "auto":
        if requested == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS was requested but is unavailable.")
        if requested == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is unavailable.")
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _validate_args(args: argparse.Namespace) -> None:
    if args.window_tokens < 2:
        raise SystemExit("--window-tokens must be at least 2.")
    if args.stride_tokens < 1 or args.stride_tokens >= args.window_tokens:
        raise SystemExit("--stride-tokens must be positive and smaller than --window-tokens.")
    if args.local_block_tokens < 1:
        raise SystemExit("--local-block-tokens must be positive.")
    if not 0.0 < args.tail_fraction <= 1.0:
        raise SystemExit("--tail-fraction must be in (0, 1].")
    if args.checkpoint_every < 1:
        raise SystemExit("--checkpoint-every must be positive.")


if __name__ == "__main__":
    main()
