from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..common.paths import default_workspace
from .catalog import build_benchmark_catalogs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-benchmarks",
        description="Catalog and validate executable repair benchmarks for readability experiments.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument(
        "--defects4j-root",
        type=Path,
        default=Path("data/benchmarks/frameworks/defects4j"),
    )
    parser.add_argument(
        "--bugsinpy-root",
        type=Path,
        default=Path("data/benchmarks/frameworks/bugsinpy"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/benchmarks/catalogs/repair-benchmarks"),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()

    def resolve(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (workspace / path).resolve()

    report = build_benchmark_catalogs(
        resolve(args.defects4j_root),
        resolve(args.bugsinpy_root),
        resolve(args.output),
        workspace,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
