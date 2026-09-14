from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common.build import build_candidate_experiments
from .common.catalog import Corpus
from .common.paths import constructed_dataset, default_workspace
from .pilot import build_python_pilot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readability-experiments",
        description="Build isolated LLM-task candidate datasets from immutable readability corpora.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument(
        "--java-dataset", type=Path, default=constructed_dataset("java")
    )
    parser.add_argument(
        "--python-dataset", type=Path, default=constructed_dataset("python")
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("data/experiments"))
    parser.add_argument(
        "--python-pilot",
        action="store_true",
        help="validate selected Python behavior-and-repair tasks in upstream projects",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    workspace = args.workspace.resolve()
    resolve = lambda path: path if path.is_absolute() else workspace / path
    raw = resolve(args.raw_root)
    if args.python_pilot:
        result = build_python_pilot(
            workspace,
            resolve(args.output) / "validated-pilot" / "python-multi-project",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return
    corpora = [
        Corpus(
            "java",
            resolve(args.java_dataset),
            {
                "apache-kafka": raw / "kafka",
                "google-guava": raw / "guava",
                "netty": raw / "netty",
                "spring-framework": raw / "spring-framework",
            },
        ),
        Corpus(
            "python",
            resolve(args.python_dataset),
            {
                "attrs": raw / "attrs",
                "django": raw / "django",
                "flask": raw / "flask",
                "requests": raw / "requests",
            },
        ),
    ]
    result = build_candidate_experiments(corpora, resolve(args.output), workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
