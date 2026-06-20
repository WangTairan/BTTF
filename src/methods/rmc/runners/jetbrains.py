import argparse
from pathlib import Path

from src.datasets.jetbrains import load_dataset
from src.methods.rmc.runners.common import add_rmc_dataset_args, run_rmc_java_dataset


DEFAULT_DATASET = Path("datasets/jetbrains")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RMC over the JetBrains dataset.")
    add_rmc_dataset_args(parser, DEFAULT_DATASET)
    return parser.parse_args()


def main() -> None:
    run_rmc_java_dataset(parse_args(), load_dataset, source_label="JetBrains")


if __name__ == "__main__":
    main()

