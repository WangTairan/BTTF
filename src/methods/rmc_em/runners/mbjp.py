import argparse
from pathlib import Path

from src.datasets.mbjp import load_dataset
from src.methods.rmc import DEFAULT_CONSTRAINTS
from src.methods.rmc.runners.dataset import build_config, run_dataset
from src.methods.rmc.text_units import normalize_escaped_newlines
from src.methods.rmc_em.runners.common import add_rmc_em_dataset_args


DEFAULT_DATASET = Path("datasets/mbjp_dev_dataset/readability_dataset.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RMC_EM over the MBJP dataset.")
    add_rmc_em_dataset_args(parser, DEFAULT_DATASET)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config(
        args=args,
        prompt_mode="code_mask_json",
        source_label="MBJP",
        text_unit="code_line",
        line_numbering="cleaned_non_blank_1_based",
        constraints=DEFAULT_CONSTRAINTS,
        mask_strategy="java_ast_stratified_v7",
    )
    run_dataset(
        items=load_dataset(args.dataset),
        config=config,
        source_units=lambda item: normalize_escaped_newlines(item.content).splitlines(),
        args=args,
    )


if __name__ == "__main__":
    main()

