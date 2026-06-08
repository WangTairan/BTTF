from __future__ import annotations

import argparse
from pathlib import Path

from src.datasets import DatasetItem, load_code_dataset
from src.experiments.registry import (
    COGNASCORE_DEFAULT_CACHE_DIR,
    COGNASCORE_DEFAULT_MODEL,
    is_method_dataset_supported,
)
from src.experiments.paths import dataset_name_for_path, output_dir

from ..results import model_slug


def validate_supported_dataset(path: Path) -> None:
    if not is_method_dataset_supported("cognascore", path):
        raise SystemExit(
            "CognaScore does not support the Dorn dataset: its samples are "
            "structurally truncated Java fragments rather than parseable "
            "compilation units or class-member snippets."
        )


def add_scoring_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--models", type=Path, default=COGNASCORE_DEFAULT_CACHE_DIR)
    parser.add_argument("--eps", type=float, default=0.18)
    parser.add_argument("--min-pts", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default=None, help="cpu, cuda, mps, or auto.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output root. Defaults to automatic paths under output/cognascore/.",
    )


def build_scorer(args: argparse.Namespace):
    from ..method import CognaScoreScorer

    return CognaScoreScorer(
        model_name=args.embedding_model,
        eps=args.eps,
        min_pts=args.min_pts,
        batch_size=args.batch_size,
        device=args.device,
        cache_dir=args.models,
    )


def configured_output_dir(args: argparse.Namespace, dataset_name: str) -> Path:
    return output_dir(
        args.output,
        "cognascore",
        dataset_name,
        model_slug(args.embedding_model),
    )


def load_items(path: Path) -> list[DatasetItem]:
    validate_supported_dataset(path)
    return load_code_dataset(path)


def dataset_output_name(path: Path) -> str:
    return dataset_name_for_path(path)
