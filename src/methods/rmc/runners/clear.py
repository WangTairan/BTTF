import argparse
from pathlib import Path

from src.datasets.clear import load_dataset as load_clear_dataset
from src.methods.rmc import DEFAULT_CONSTRAINTS
from src.methods.rmc.runners.dataset import (
    add_common_args,
    build_config,
    run_dataset,
)
from src.methods.rmc.text_units import split_paragraphs, split_sentences


DEFAULT_DATASET = Path("datasets/CLEAR-Corpus-main/CLEAR_corpus_final.xlsx")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RMC over the CLEAR corpus.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help=f"Dataset xlsx path, defaults to {DEFAULT_DATASET}",
    )
    add_common_args(parser)
    parser.add_argument(
        "--nl-granularity",
        choices=("paragraph", "sentence"),
        default="sentence",
        help="Natural-language unit granularity to mask, defaults to sentence.",
    )
    parser.add_argument(
        "--nl-min-words",
        type=int,
        default=8,
        help="Minimum words in one natural-language mask unit, defaults to 8.",
    )
    parser.add_argument("--id-column", default="ID")
    parser.add_argument("--text-column", default="Excerpt")
    parser.add_argument("--score-column", default="BT_easiness")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config(
        args=args,
        prompt_mode="natural_language",
        source_label="CLEAR",
        text_unit=args.nl_granularity,
        line_numbering=f"cleaned_{args.nl_granularity}_1_based",
        constraints=DEFAULT_CONSTRAINTS,
        mask_strategy="natural_language_stratified_v1",
    )
    splitter = split_paragraphs if args.nl_granularity == "paragraph" else split_sentences
    run_dataset(
        items=load_dataset(args),
        config=config,
        source_units=lambda item: splitter(item.content),
        args=args,
        summary_extra={
            "text_column": args.text_column,
            "score_column": args.score_column,
        },
    )


def load_dataset(args: argparse.Namespace):
    return load_clear_dataset(
        args.dataset,
        id_column=args.id_column,
        text_column=args.text_column,
        score_column=args.score_column,
    )


if __name__ == "__main__":
    main()
