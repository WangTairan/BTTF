"""Incremental original-source causal-LM feature production, without label fitting."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.datasets import load_code_dataset
from src.experiments.paths import dataset_name_for_path
from src.experiments.registry import DATASETS

from ..dataset_io import item_source_sha256
from ..llm_features.aggregate import aggregate_features
from ..llm_features.cache import LLMTraceCache, fingerprint
from ..llm_features.inventory import (
    LLM_FEATURE_BUILD_VERSION,
    LLM_FEATURE_INVENTORY,
    LLM_FEATURE_NAMES,
)
from ..llm_features.scoring import (
    CommentEffect,
    CommentTarget,
    LazyCausalScorer,
    TokenizedSource,
    TraceConfiguration,
)
from ..llm_features.source_spans import SOURCE_ANALYSIS_VERSION, analyze_source
from ..llm_features.types import (
    DEFAULT_CAUSAL_LM,
    DEFAULT_CAUSAL_LM_REVISION,
    TokenLoss,
)
from ..paths import LLM_FEATURE_ROOT, LLM_SURPRISAL_CACHE_ROOT
from ..results import model_slug

DEFAULT_DATASETS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate 47 causal-LM features with per-window resume."
    )
    parser.add_argument(
        "datasets",
        nargs="*",
        type=Path,
        help="Defaults to the six human-rated datasets.",
    )
    parser.add_argument("--model", default=DEFAULT_CAUSAL_LM)
    parser.add_argument(
        "--revision",
        default=DEFAULT_CAUSAL_LM_REVISION,
        help="Pinned 40-character model commit.",
    )
    parser.add_argument(
        "--device", choices=("auto", "cpu", "mps", "cuda"), default="auto"
    )
    parser.add_argument(
        "--compute-dtype",
        choices=("auto", "float32", "float16"),
        default="auto",
        help="Inference precision; float32 permits reuse of existing CPU traces on MPS.",
    )
    parser.add_argument("--window-tokens", type=int, default=512)
    parser.add_argument("--stride-tokens", type=int, default=384)
    parser.add_argument("--context-target-tokens", type=int, default=32)
    parser.add_argument("--comment-target-tokens", type=int, default=128)
    parser.add_argument("--short-context-tokens", type=int, default=32)
    parser.add_argument("--long-context-tokens", type=int, default=256)
    parser.add_argument("--local-block-tokens", type=int, default=32)
    parser.add_argument("--tail-fraction", type=float, default=0.20)
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1,
        help="CSV row interval; traces always commit per window.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Sample runs write under samples/, not over the complete table.",
    )
    parser.add_argument(
        "--task-id", action="append", help="Select task IDs; writes under samples/."
    )
    parser.add_argument("--cache-root", type=Path, default=LLM_SURPRISAL_CACHE_ROOT)
    parser.add_argument("--output-root", type=Path, default=LLM_FEATURE_ROOT)
    parser.add_argument("--model-cache-root", type=Path, default=Path("models"))
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Allow pinned model-repository tokenizer/model code when required.",
    )
    parser.add_argument(
        "--recompute-features",
        action="store_true",
        help="Reaggregate cached traces, without forcing inference.",
    )
    parser.add_argument("--quiet-reuse", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _validate_args(args)
    device = _resolve_device(args.device)
    configuration = TraceConfiguration(
        model_name=args.model,
        revision=args.revision,
        compute_dtype=(
            args.compute_dtype
            if args.compute_dtype != "auto"
            else "float16" if device in {"mps", "cuda"} else "float32"
        ),
        window_tokens=args.window_tokens,
        stride_tokens=args.stride_tokens,
        context_target_tokens=args.context_target_tokens,
        comment_target_tokens=args.comment_target_tokens,
        short_context_tokens=args.short_context_tokens,
        long_context_tokens=args.long_context_tokens,
        trust_remote_code=args.trust_remote_code,
    )
    scorer = LazyCausalScorer(
        configuration,
        device=device,
        cache_dir=args.model_cache_root,
        local_files_only=args.local_files_only,
    )
    print(
        f"LLM features: {len(LLM_FEATURE_NAMES)}; {args.model} ({args.revision}); "
        f"{device}/{configuration.compute_dtype}; trace={configuration.fingerprint[:12]}.",
        flush=True,
    )
    paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASETS]
    with LLMTraceCache(
        args.cache_root / model_slug(args.model) / "traces.sqlite"
    ) as cache:
        for path in paths:
            _process_dataset(path, args, scorer, configuration, cache)


def _source_policy(item, dataset: str) -> tuple[str, bool, bool]:
    language = str(item.metadata.get("language", "java")).lower()
    source_form = item.metadata.get("source_form")
    fragments = source_form == "snippet" or dataset in {
        "buse",
        "dorn",
    }
    class_members = source_form in {"method", "class_members"} or (
        source_form is None and dataset == "scalabrino"
    )
    return language, fragments, class_members


def _process_dataset(path, args, scorer, configuration, cache) -> None:
    dataset = dataset_name_for_path(path)
    items = load_code_dataset(path)
    expected = len(items)
    partial = bool(args.task_id or args.limit is not None)
    if args.task_id:
        requested = set(args.task_id)
        items = [item for item in items if item.task_id in requested]
        missing = requested - {item.task_id for item in items}
        if missing:
            raise ValueError(
                f"Unknown task IDs in {dataset}: {', '.join(sorted(missing))}"
            )
    if args.limit is not None:
        items = items[: args.limit]
    directory = args.output_root / dataset / model_slug(configuration.model_name)
    if partial:
        directory /= "samples"
    directory.mkdir(parents=True, exist_ok=True)
    rows, row_metadata = [], []
    computed, reused = 0, 0
    feature_config = {
        "trace": asdict(configuration),
        "feature_build_version": LLM_FEATURE_BUILD_VERSION,
        "source_analysis_version": SOURCE_ANALYSIS_VERSION,
        "local_block_tokens": args.local_block_tokens,
        "tail_fraction": args.tail_fraction,
        "feature_names": list(LLM_FEATURE_NAMES),
    }
    for index, item in enumerate(items, 1):
        source_hash = item_source_sha256(item)
        language, fragments, class_members = _source_policy(item, dataset)
        source_policy = {"language": language, "allow_fragments": fragments}
        if class_members:
            source_policy["allow_class_members"] = True
        feature_sha = fingerprint({**feature_config, **source_policy})
        stored = (
            None
            if args.recompute_features
            else cache.get_features(source_hash, feature_sha)
        )
        try:
            if stored is None:
                print(
                    f"[{index}/{len(items)}] LLM features for {dataset} {item.task_id}",
                    flush=True,
                )
                features, metadata = _compute_row(
                    item.content,
                    language,
                    fragments,
                    args,
                    scorer,
                    configuration,
                    cache,
                    source_hash,
                    allow_class_members=class_members,
                )
                if set(features) != set(LLM_FEATURE_NAMES):
                    raise RuntimeError(
                        "Aggregation returned a different feature inventory."
                    )
                if any(
                    value is not None and not math.isfinite(value)
                    for value in features.values()
                ):
                    raise RuntimeError(
                        "A feature is non-finite; missing values must be None."
                    )
                metadata["nonmissing_features"] = [
                    name for name, value in features.items() if value is not None
                ]
                cache.put_features(source_hash, feature_sha, features, metadata)
                computed += 1
            else:
                features, metadata = stored["features"], stored["metadata"]
                reused += 1
                if not args.quiet_reuse:
                    print(
                        f"[{index}/{len(items)}] Reused {dataset} {item.task_id}",
                        flush=True,
                    )
        except Exception as error:
            _append_failure(
                directory / "failures.jsonl",
                dataset,
                item.task_id,
                source_hash,
                feature_sha,
                error,
            )
            raise
        rows.append(
            {
                "dataset": dataset,
                "task_id": item.task_id,
                "readability_score": item.readability_score,
                **features,
            }
        )
        row_metadata.append(
            {
                "task_id": item.task_id,
                "source_sha256": source_hash,
                "feature_sha256": feature_sha,
                **metadata,
            }
        )
        if index % args.checkpoint_every == 0:
            _write_outputs(
                directory,
                rows,
                row_metadata,
                dataset,
                path,
                feature_config,
                expected,
                computed,
                reused,
                complete=False,
            )
    _write_outputs(
        directory,
        rows,
        row_metadata,
        dataset,
        path,
        feature_config,
        expected,
        computed,
        reused,
        complete=not partial and len(rows) == expected,
    )
    print(
        f"Wrote {directory / 'features.csv'} (computed={computed}, reused={reused})",
        flush=True,
    )


def _compute_row(
    source,
    language,
    fragments,
    args,
    scorer,
    configuration,
    cache,
    source_hash,
    *,
    allow_class_members=False,
):
    analysis = analyze_source(
        source,
        language,
        allow_fragments=fragments,
        allow_class_members=allow_class_members,
    )
    payload = cache.get_tokenization(
        source_hash, configuration.tokenization_fingerprint
    )
    if payload is None:
        tokenized = scorer.tokenize(source)
        payload = asdict(tokenized)
        payload["offsets"] = [list(offset) for offset in tokenized.offsets]
        cache.put_tokenization(
            source_hash, configuration.tokenization_fingerprint, payload
        )
    else:
        tokenized = TokenizedSource(
            payload["input_ids"],
            [tuple(offset) for offset in payload["offsets"]],
            payload["boundary_token_id"],
        )

    def checkpoint(kind, next_token, losses):
        cache.append_window(
            source_hash, configuration.fingerprint_for(kind), kind, next_token, losses
        )
        print(
            f"  {kind}: {next_token}/{len(tokenized.input_ids)} tokens checkpointed",
            flush=True,
        )

    traces = {"short": None, "long": None}
    context_available = _has_context_targets(analysis, tokenized, configuration)
    kinds = ("global", "short", "long") if context_available else ("global",)
    for kind in kinds:
        traces[kind] = scorer.score_trace(
            tokenized,
            kind=kind,
            existing_losses=cache.get_trace(
                source_hash, configuration.fingerprint_for(kind), kind
            ),
            checkpoint=checkpoint,
        )
    targets, skipped = _comment_targets(analysis.metadata, tokenized, configuration)
    effects_namespace = fingerprint(
        {
            "trace": configuration.fingerprint_for("comment"),
            "analysis": SOURCE_ANALYSIS_VERSION,
            "language": language,
            "allow_fragments": fragments,
        }
    )
    cached_effects = cache.get_comment_effects(source_hash, effects_namespace)
    existing = []
    for target in targets:
        if _comment_key(target) not in cached_effects:
            break
        existing.append(_decode_effect(cached_effects[_comment_key(target)]))

    def comment_checkpoint(next_index, effect):
        cache.put_comment_effect(
            source_hash, effects_namespace, _comment_key(effect.target), asdict(effect)
        )
        print(
            f"  comment contrast: {next_index}/{len(targets)} checkpointed", flush=True
        )

    effects = scorer.score_comment_effects(
        source,
        tokenized,
        targets,
        existing_effects=existing,
        checkpoint=comment_checkpoint,
    )
    comment_gain, comment_metadata = _comment_gain(source, effects)
    source_bytes = len(source.encode("utf-8"))
    if source_bytes <= 0:
        raise ValueError("Cannot normalize comment gain for an empty source.")
    comment_gain_source_density = (
        0.0
        if comment_gain is None
        else comment_gain * comment_metadata["scored_target_bytes"] / source_bytes
    )
    features, metadata = aggregate_features(
        source,
        traces["global"],
        analysis,
        local_block_tokens=args.local_block_tokens,
        tail_fraction=args.tail_fraction,
        short_context_losses=traces["short"],
        long_context_losses=traces["long"],
        context_target_tokens=configuration.context_target_tokens,
        short_context_tokens=configuration.short_context_tokens,
        comment_gain=comment_gain,
        comment_gain_source_density=comment_gain_source_density,
    )
    metadata.update(
        {
            "comment_contrast": {**comment_metadata, "skipped_targets": skipped},
            "trace_token_count": len(tokenized.input_ids),
            "context_missing_reason": None
            if context_available
            else "no_complete_role_occurrence_with_extra_source_prefix",
        }
    )
    return features, metadata


def _has_context_targets(analysis, tokenized, configuration):
    first_eligible_token = (
        configuration.short_context_tokens // configuration.context_target_tokens + 1
    ) * configuration.context_target_tokens
    if len(tokenized.input_ids) <= first_eligible_token:
        return False
    # Offsets are source ordered; a shared Unicode BPE character crossing the
    # eligibility boundary must be excluded in full, just as in aggregation.
    prefix_end = tokenized.offsets[first_eligible_token - 1][1]
    return any(
        span.role
        in {
            "identifier",
            "call_target",
            "expression",
            "assignment_rhs",
            "control_header",
        }
        and span.start >= prefix_end
        for span in analysis.spans
    )


def _comment_key(target):
    return f"{target.comment_start}:{target.comment_end}:{target.target_start}:{target.target_end}"


def _decode_effect(payload):
    return CommentEffect(
        CommentTarget(**payload["target"]),
        [TokenLoss(**row) for row in payload["present_losses"]],
        [TokenLoss(**row) for row in payload["removed_losses"]],
        int(payload["visible_comment_bytes"]),
    )


def _comment_targets(metadata, tokenized, configuration):
    targets, skipped = [], []
    for payload in metadata.get("comment_targets", []):
        target = CommentTarget(**payload)
        indices = [
            index
            for index, (start, stop) in enumerate(tokenized.offsets)
            if target.target_start <= start < stop <= target.target_end
        ]
        if not indices:
            skipped.append({**payload, "reason": "no_complete_target_token"})
            continue
        prefix_start = max(0, indices[0] - configuration.long_context_tokens)
        if tokenized.offsets[prefix_start][0] >= target.comment_end:
            skipped.append({**payload, "reason": "comment_outside_bounded_prefix"})
            continue
        targets.append(target)
    return targets, skipped


def _comment_gain(source, effects):
    total_bits, total_bytes, target_count = 0.0, 0, 0
    for effect in effects:
        present, removed = effect.present_losses, effect.removed_losses
        if [(row.token_index, row.start, row.end) for row in present] != [
            (row.token_index, row.start, row.end) for row in removed
        ]:
            raise ValueError("Comment conditions are not matched on source tokens.")
        union = []
        for start, stop in sorted(
            (row.start, row.end) for row in present if row.end > row.start
        ):
            if union and start <= union[-1][1]:
                union[-1] = (union[-1][0], max(stop, union[-1][1]))
            else:
                union.append((start, stop))
        byte_count = sum(
            len(source[start:stop].encode("utf-8")) for start, stop in union
        )
        if byte_count <= 0:
            raise ValueError("Comment conditions cover no target bytes.")
        total_bits += sum(
            after.nll - before.nll for before, after in zip(present, removed)
        ) / math.log(2)
        total_bytes += byte_count
        target_count += len(present)
    return (total_bits / total_bytes if total_bytes else None), {
        "eligible_pairs": len(effects),
        "scored_target_tokens": target_count,
        "scored_target_bytes": total_bytes,
        "visible_comment_bytes": sum(
            effect.visible_comment_bytes for effect in effects
        ),
        "target_policy": "first comment_target_tokens complete original tokens of same-scope following statement",
        "missing_reason": None if effects else "no_eligible_front_comment_pair",
    }


def _write_outputs(
    directory,
    rows,
    row_metadata,
    dataset,
    path,
    configuration,
    expected,
    computed,
    reused,
    *,
    complete,
):
    csv_path = directory / "features.csv"
    temporary = csv_path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset", "task_id", "readability_score", *LLM_FEATURE_NAMES],
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(csv_path)
    metadata = {
        "dataset": dataset,
        "dataset_path": str(path),
        "feature_family": "llm",
        "feature_count": len(LLM_FEATURE_NAMES),
        "features": list(LLM_FEATURE_NAMES),
        "feature_inventory": [
            asdict(definition) for definition in LLM_FEATURE_INVENTORY
        ],
        "configuration": configuration,
        "completed_rows": len(rows),
        "expected_rows": expected,
        "computed_rows": computed,
        "reused_rows": reused,
        "complete": complete,
        "nonmissing_feature_counts": {
            name: sum(name in row["nonmissing_features"] for row in row_metadata)
            for name in LLM_FEATURE_NAMES
        },
        "rows": row_metadata,
    }
    metadata_path = directory / "metadata.json"
    temporary = metadata_path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(metadata, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(metadata_path)


def _append_failure(path, dataset, task_id, source_hash, feature_sha, error):
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset,
        "task_id": task_id,
        "source_sha256": source_hash,
        "feature_sha256": feature_sha,
        "error_type": type(error).__name__,
        "error": repr(error),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _resolve_device(requested):
    import torch

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


def _validate_args(args):
    if args.local_block_tokens < 1:
        raise ValueError("--local-block-tokens must be positive.")
    if not 0 < args.tail_fraction <= 1:
        raise ValueError("--tail-fraction must be in (0, 1].")
    if args.checkpoint_every < 1:
        raise ValueError("--checkpoint-every must be positive.")
    if args.limit is not None and args.limit < 1:
        raise ValueError("--limit must be positive.")


if __name__ == "__main__":
    main()
