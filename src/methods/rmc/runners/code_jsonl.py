import argparse
from dataclasses import replace
from pathlib import Path

from src.datasets.code_jsonl import load_dataset as load_code_jsonl_dataset
from src.methods.rmc import DEFAULT_CONSTRAINTS, java_ast_masks
from src.methods.rmc.runners.dataset import (
    add_common_args,
    build_config,
    run_dataset,
)
from src.methods.rmc.text_units import clean_blank_units, normalize_escaped_newlines


def add_code_jsonl_args(
    parser: argparse.ArgumentParser,
    default_dataset: Path,
) -> None:
    parser.add_argument(
        "--dataset",
        type=Path,
        default=default_dataset,
        help=f"Dataset JSONL path, defaults to {default_dataset}",
    )
    parser.add_argument(
        "--include-short",
        action="store_true",
        help=(
            "Include snippets that do not support the configured --mask-index values. "
            "Only applies when --mask-index is set."
        ),
    )
    add_common_args(parser)


def run_code_jsonl_dataset(
    args: argparse.Namespace,
    source_label: str,
) -> Path:
    items, skipped = prepare_items(
        args.dataset,
        required_mask_indices=tuple(args.mask_index or ()),
        skip_short=args.mask_index is not None and not args.include_short,
        ast_min_tokens=args.ast_min_tokens,
        ast_granularity=args.ast_granularity,
        max_combination_size=args.max_combination_size,
        max_samples_per_stratum=args.max_samples_per_stratum,
        sampling_seed=args.sampling_seed,
    )
    config = build_config(
        args=args,
        prompt_mode="code",
        source_label=source_label,
        text_unit="code_line",
        line_numbering="cleaned_non_blank_1_based",
        constraints=DEFAULT_CONSTRAINTS,
        mask_strategy="java_ast_stratified_v7",
    )
    return run_dataset(
        items=items,
        config=config,
        source_units=lambda item: normalize_escaped_newlines(item.content).splitlines(),
        args=args,
        summary_extra={
            "skipped_short_count": skipped,
            "selected_mask_indices": list(args.mask_index or ()),
        },
    )


def prepare_items(
    path: Path,
    required_mask_indices: tuple[int, ...],
    skip_short: bool,
    ast_min_tokens: int,
    ast_granularity: str,
    max_combination_size: int,
    max_samples_per_stratum: int | None,
    sampling_seed: int,
):
    items = []
    skipped = 0
    required = set(required_mask_indices)
    for item in load_code_jsonl_dataset(path):
        units = clean_blank_units(normalize_escaped_newlines(item.content).splitlines())
        masks = java_ast_masks(
            "\n".join(units),
            DEFAULT_CONSTRAINTS,
            min_tokens=ast_min_tokens,
            ast_granularity=ast_granularity,
            max_combination_size=max_combination_size,
            max_samples_per_stratum=max_samples_per_stratum,
            sampling_seed=sampling_seed,
        )
        available = set(range(len(masks)))
        missing = sorted(required - available)
        if skip_short and missing:
            skipped += 1
            continue
        metadata = dict(item.metadata)
        metadata.update(
            {
                "source_line_count": len(units),
                "available_mask_count": len(masks),
                "missing_required_masks": missing,
            }
        )
        items.append(replace(item, metadata=metadata))
    print(f"Prepared {len(items)} RMC items; skipped {skipped} short items", flush=True)
    return items, skipped
