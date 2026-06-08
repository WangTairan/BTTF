import argparse
from pathlib import Path

from src.datasets.schnappinger import load_dataset
from src.methods.rmc.runners.java_dataset import add_java_dataset_args, run_java_dataset


DEFAULT_DATASET = Path("datasets/schnappinger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RMC over the Schnappinger dataset.")
    add_java_dataset_args(parser, DEFAULT_DATASET)
    return parser.parse_args()


def main() -> None:
    run_java_dataset(parse_args(), load_dataset, source_label="Schnappinger")


if __name__ == "__main__":
    main()
