import argparse
from collections.abc import Callable
from pathlib import Path

from src.datasets import DatasetItem
from src.methods.rmc import DEFAULT_CONSTRAINTS
from src.methods.rmc.runners.dataset import add_common_args, build_config, run_dataset


LoadDatasetFn = Callable[[Path], list[DatasetItem]]


def add_rmc_em_dataset_args(parser: argparse.ArgumentParser, default_dataset: Path) -> None:
    parser.add_argument(
        "--dataset",
        type=Path,
        default=default_dataset,
        help=f"Dataset path, defaults to {default_dataset}",
    )
    add_common_args(parser)


def run_rmc_em_java_dataset(
    args: argparse.Namespace,
    load_dataset: LoadDatasetFn,
    source_label: str,
) -> Path:
    config = build_config(
        args=args,
        prompt_mode="code_mask_json",
        source_label=source_label,
        text_unit="code_line",
        line_numbering="cleaned_non_blank_1_based",
        constraints=DEFAULT_CONSTRAINTS,
        mask_strategy="java_ast_stratified_v7",
    )
    return run_dataset(
        items=load_dataset(args.dataset),
        config=config,
        source_units=lambda item: item.content.splitlines(),
        args=args,
    )

