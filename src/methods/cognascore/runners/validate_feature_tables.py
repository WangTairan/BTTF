from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.experiments.registry import COGNASCORE_DEFAULT_MODEL

from ..embedding_features import embedding_feature_names
from ..feature_database import BASE_FEATURE_NAMES, TYPE_STAT_NAMES
from ..feature_schema import namespaced_feature
from ..paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT
from ..results import model_slug
from .supervised_ridge import EMBEDDING_MODEL as ML_EMBEDDING_MODEL
from .supervised_ridge import SELECTED_FEATURES


DEFAULT_DATASETS = (
    "mbjp",
    "buse",
    "scalabrino",
    "jetbrains",
    "dorn",
    "schnappinger",
)
IDENTITY_COLUMNS = {"dataset", "task_id", "readability_score"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CognaScore feature table schema alignment.")
    parser.add_argument(
        "--embedding-model",
        action="append",
        default=[],
        help="Embedding model whose embedding-derived feature tables should be validated. Can be repeated.",
    )
    parser.add_argument(
        "--base-model",
        default=COGNASCORE_DEFAULT_MODEL,
        help="Model slug used for the base CognaScore feature tables.",
    )
    parser.add_argument("--base-root", type=Path, default=BASE_FEATURE_ROOT)
    parser.add_argument("--embedding-root", type=Path, default=EMBEDDING_FEATURE_ROOT)
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        help="Dataset table to validate. Repeat as needed; defaults to the six established datasets.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = tuple(args.dataset) or DEFAULT_DATASETS
    embedding_models = args.embedding_model or [COGNASCORE_DEFAULT_MODEL]
    expected_embedding_columns = ["dataset", "task_id", "readability_score", *embedding_feature_names()]
    expected_base_feature_columns = [*BASE_FEATURE_NAMES, *TYPE_STAT_NAMES]
    if any("graph" in column for column in expected_embedding_columns):
        raise SystemExit("Internal schema still contains graph columns.")
    if len(embedding_feature_names()) != 102:
        raise SystemExit(f"Expected 102 embedding features, found {len(embedding_feature_names())}.")

    base_slug = model_slug(args.base_model)
    base_feature_columns: list[str] | None = None
    base_row_counts: dict[str, int] = {}
    for dataset in datasets:
        path = args.base_root / dataset / base_slug / "features.csv"
        columns, row_count = read_header_and_count(path)
        feature_columns = [column for column in columns if column not in IDENTITY_COLUMNS]
        if any("graph" in column for column in feature_columns):
            raise SystemExit(f"Graph column found in base table: {path}")
        if any("type_normal" in column for column in feature_columns):
            raise SystemExit(f"Legacy NORMAL chunk feature found in base table: {path}")
        if any("junk" in column for column in feature_columns):
            raise SystemExit(f"Junk feature found in base table: {path}")
        if feature_columns != expected_base_feature_columns:
            raise SystemExit(f"Base schema does not match production definitions: {path}")
        if base_feature_columns is None:
            base_feature_columns = feature_columns
        elif feature_columns != base_feature_columns:
            raise SystemExit(f"Base schema mismatch for {dataset}: {path}")
        base_row_counts[dataset] = row_count

    if base_feature_columns is None:
        raise SystemExit("No base feature tables found.")
    for embedding_model in embedding_models:
        slug = model_slug(embedding_model)
        embedding_row_counts: dict[str, int] = {}
        for dataset in datasets:
            path = args.embedding_root / dataset / slug / "features.csv"
            columns, row_count = read_header_and_count(path)
            if columns != expected_embedding_columns:
                raise SystemExit(f"Embedding schema mismatch for {dataset}/{slug}: {path}")
            if any("graph" in column for column in columns):
                raise SystemExit(f"Graph column found in embedding table: {path}")
            if any("type_normal" in column for column in columns):
                raise SystemExit(f"Legacy NORMAL chunk feature found in embedding table: {path}")
            if any("junk" in column for column in columns):
                raise SystemExit(f"Junk feature found in embedding table: {path}")
            embedding_row_counts[dataset] = row_count
        print(
            f"{embedding_model}: embedding schema OK, "
            f"{len(expected_embedding_columns) - 3} features, rows={embedding_row_counts}"
        )

    ml_base_schema = {namespaced_feature("base", column) for column in base_feature_columns}
    ml_embedding_schema = {namespaced_feature("embedding", column) for column in embedding_feature_names()}
    if model_slug(ML_EMBEDDING_MODEL) != base_slug:
        raise SystemExit(
            f"ML model expects {ML_EMBEDDING_MODEL}, but base validation model is {args.base_model}."
        )
    missing = [feature for feature in SELECTED_FEATURES if feature not in ml_base_schema | ml_embedding_schema]
    if missing:
        raise SystemExit(f"Selected ML features missing from current schema: {missing}")
    if any("graph" in feature for feature in SELECTED_FEATURES):
        raise SystemExit("Selected ML features still contain graph features.")
    print(f"base schema OK, {len(base_feature_columns)} features, rows={base_row_counts}")
    print(f"ML selected feature schema OK, {len(SELECTED_FEATURES)} selected features.")


def read_header_and_count(path: Path) -> tuple[list[str], int]:
    if not path.exists():
        raise SystemExit(f"Missing feature table: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        if columns is None:
            raise SystemExit(f"Missing CSV header: {path}")
        identities: set[tuple[str, str]] = set()
        row_count = 0
        for row in reader:
            row_count += 1
            identity = (str(row.get("dataset", "")), str(row.get("task_id", "")))
            if not all(identity):
                raise SystemExit(f"Missing row identity in {path}: row {row_count + 1}")
            if identity in identities:
                raise SystemExit(f"Duplicate row identity in {path}: {identity}")
            identities.add(identity)
    return columns, row_count


if __name__ == "__main__":
    main()
