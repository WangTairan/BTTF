from __future__ import annotations

import argparse
from pathlib import Path

from src.datasets import load_code_dataset
from src.experiments.paths import dataset_name_for_path
from src.experiments.registry import COGNASCORE_DEFAULT_MODEL

from ..feature_database import extract_feature_row, write_feature_database
from ..paths import BASE_FEATURE_ROOT
from ..results import model_slug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a stable CognaScore feature database.")
    parser.add_argument("dataset", type=Path, help="Supported code dataset path or directory.")
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=BASE_FEATURE_ROOT,
        help="Base-feature root. Defaults to artifacts/cognascore/features/base/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_name = dataset_name_for_path(args.dataset)
    items = load_code_dataset(args.dataset)
    if args.limit is not None:
        items = items[: args.limit]

    rows = []
    for index, item in enumerate(items, start=1):
        print(f"[{index}/{len(items)}] Extracting features for {item.task_id}", flush=True)
        rows.append(
            extract_feature_row(
                dataset=dataset_name,
                item=item,
            )
        )

    feature_dir = args.output / dataset_name / model_slug(args.embedding_model)
    csv_path, metadata_path = write_feature_database(
        rows=rows,
        output_dir=feature_dir,
        metadata={
            "dataset": dataset_name,
            "dataset_path": str(args.dataset),
            "embedding_model": args.embedding_model,
            "source": "direct_chunk_and_code_extraction",
        },
    )
    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {metadata_path}", flush=True)


if __name__ == "__main__":
    main()
