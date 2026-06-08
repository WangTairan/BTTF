import argparse
from pathlib import Path

from src.datasets.scalabrino import load_dataset
from src.methods.rmc_em.runners.common import add_rmc_em_dataset_args, run_rmc_em_java_dataset


DEFAULT_DATASET = Path("datasets/scalabrino/dataset")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RMC_EM over the Scalabrino dataset.")
    add_rmc_em_dataset_args(parser, DEFAULT_DATASET)
    return parser.parse_args()


def main() -> None:
    run_rmc_em_java_dataset(parse_args(), load_dataset, source_label="Scalabrino")


if __name__ == "__main__":
    main()

