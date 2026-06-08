import argparse
from pathlib import Path

from src.datasets.code_jsonl import load_dataset as load_code_jsonl_dataset
from src.methods.rmc import DEFAULT_CONSTRAINTS
from src.methods.rmc.runners.dataset import add_common_args, build_config, run_dataset
from src.methods.rmc.text_units import normalize_escaped_newlines


def add_prefix_code_jsonl_args(parser: argparse.ArgumentParser, default_dataset: Path) -> None:
    parser.add_argument(
        "--dataset",
        type=Path,
        default=default_dataset,
        help=f"Dataset JSONL path, defaults to {default_dataset}",
    )
    add_common_args(parser)


def run_prefix_code_jsonl_dataset(args: argparse.Namespace, source_label: str) -> Path:
    config = build_config(
        args=args,
        prompt_mode="code_prefix",
        source_label=source_label,
        text_unit="code_line",
        line_numbering="cleaned_non_blank_1_based",
        constraints=DEFAULT_CONSTRAINTS,
        mask_strategy="java_ast_prefix_v1",
    )
    return run_dataset(
        items=load_code_jsonl_dataset(args.dataset),
        config=config,
        source_units=lambda item: normalize_escaped_newlines(item.content).splitlines(),
        args=args,
    )
