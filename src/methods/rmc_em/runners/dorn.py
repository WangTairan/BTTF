import argparse
from collections import Counter
from pathlib import Path

from src.datasets.dorn import load_dataset
from src.methods.rmc import DEFAULT_CONSTRAINTS
from src.methods.rmc.fragment_masking import java_fragment_control_masks
from src.methods.rmc.runners.dataset import build_config, run_dataset
from src.methods.rmc.text_units import clean_blank_units
from src.methods.rmc_em.runners.common import add_rmc_em_dataset_args


DEFAULT_DATASET = Path("datasets/dorn/dataset")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RMC_EM over the Dorn dataset.")
    add_rmc_em_dataset_args(parser, DEFAULT_DATASET)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.ast_granularity != "control":
        raise SystemExit("Dorn fragment runner only supports --ast-granularity control")
    items, skipped_no_masks, language_counts, skipped_no_masks_by_language = prepare_items(args)
    config = build_config(
        args=args,
        prompt_mode="code_mask_json",
        source_label="Dorn",
        text_unit="code_line",
        line_numbering="cleaned_non_blank_1_based",
        constraints=DEFAULT_CONSTRAINTS,
        mask_strategy="java_fragment_control_v1",
    )
    run_dataset(
        items=items,
        config=config,
        source_units=lambda item: item.content.splitlines(),
        args=args,
        summary_extra={
            "language_filter": "all",
            "languages": sorted(language_counts),
            "selected_by_language": dict(sorted(language_counts.items())),
            "skipped_no_masks": skipped_no_masks,
            "skipped_no_masks_by_language": dict(sorted(skipped_no_masks_by_language.items())),
            "fragment_parser": "token_brace_control_matcher",
        },
    )


def prepare_items(args: argparse.Namespace):
    items = []
    skipped_no_masks = 0
    language_counts: Counter[str] = Counter()
    skipped_no_masks_by_language: Counter[str] = Counter()
    for item in load_dataset(args.dataset):
        language = str(item.metadata.get("language", "unknown"))
        units = clean_blank_units(item.content.splitlines())
        masks = java_fragment_control_masks(
            "\n".join(units),
            DEFAULT_CONSTRAINTS,
            min_tokens=args.ast_min_tokens,
            max_combination_size=args.max_combination_size,
            max_samples_per_stratum=args.max_samples_per_stratum,
            sampling_seed=args.sampling_seed,
        )
        if not masks:
            skipped_no_masks += 1
            skipped_no_masks_by_language[language] += 1
            continue
        language_counts[language] += 1
        items.append(item)
    print(
        "Prepared Dorn fragment-control items: "
        f"{len(items)} selected, {skipped_no_masks} without masks, "
        f"selected_by_language={dict(sorted(language_counts.items()))}",
        flush=True,
    )
    return items, skipped_no_masks, language_counts, skipped_no_masks_by_language


if __name__ == "__main__":
    main()

