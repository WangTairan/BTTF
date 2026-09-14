from __future__ import annotations

import argparse
import json
from pathlib import Path

from readability_data.java_degradation import (
    construct_interference_dataset,
)
from readability_data.java_degradation.registry import interference_registry
from readability_data.python_degradation import construct_python_dataset
from readability_data.python_degradation.registry import (
    INTERFERENCES as PYTHON_INTERFERENCES,
)
from readability_data.shared.alignment import INTERFERENCE_SPEC_BY_SLUG


def build_parser() -> argparse.ArgumentParser:
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(
        prog="readability-data",
        description="Construct reproducible source-level Java and Python degradation datasets.",
        formatter_class=formatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    interfere = subparsers.add_parser(
        "java-interfere",
        aliases=["interfere"],
        help="apply each selected interference separately to every Java file",
        description=(
            "Build one original-source variant and one direct-source variant per "
            "selected interference. No interference consumes another interference."
        ),
        formatter_class=formatter,
    )
    interfere.add_argument(
        "--input",
        type=Path,
        required=True,
        help="directory containing complete Java source classes",
    )
    interfere.add_argument("--output", type=Path, required=True)
    interfere.add_argument(
        "--interferences",
        nargs="+",
        choices=tuple(interference_registry()),
        default=None,
        help="interferences to generate; omit to use the complete catalog",
    )
    interfere.add_argument("--seed", type=int, default=20260823)

    subparsers.add_parser(
        "list-java-interferences",
        aliases=["list-interferences"],
        help="list registered pluggable interference implementations",
        formatter_class=formatter,
    )

    python_construct = subparsers.add_parser(
        "python-construct",
        help="sample four Python projects and construct independent degradation variants",
        description=(
            "Select a balanced corpus of complete production classes from Django, Flask, "
            "Requests, and attrs, then apply all 13 interferences independently to source."
        ),
        formatter_class=formatter,
    )
    python_construct.add_argument("--django-root", type=Path, required=True)
    python_construct.add_argument("--flask-root", type=Path, required=True)
    python_construct.add_argument("--requests-root", type=Path, required=True)
    python_construct.add_argument("--attrs-root", type=Path, required=True)
    python_construct.add_argument("--output", type=Path, required=True)
    python_construct.add_argument("--per-project", type=int, default=25)
    python_construct.add_argument("--seed", type=int, default=20260823)
    subparsers.add_parser(
        "list-python-interferences",
        help="list registered Python interference implementations",
        formatter_class=formatter,
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "python-construct":
        provenance = construct_python_dataset(
            {
                "django": args.django_root,
                "flask": args.flask_root,
                "requests": args.requests_root,
                "attrs": args.attrs_root,
            },
            args.output,
            args.per_project,
            args.seed,
        )
        print(json.dumps(provenance, ensure_ascii=False, indent=2))
        return
    if args.command == "list-python-interferences":
        print(
            json.dumps(
                [
                    {
                        "category": plugin.category,
                        "interference": plugin.slug,
                        "description": plugin.description,
                        "target_policy": INTERFERENCE_SPEC_BY_SLUG[
                            plugin.slug
                        ].target_policy,
                        "template_count": INTERFERENCE_SPEC_BY_SLUG[
                            plugin.slug
                        ].template_count,
                        "implementation": (
                            f"{plugin.__class__.__module__}.{plugin.__class__.__name__}"
                        ),
                    }
                    for plugin in PYTHON_INTERFERENCES.values()
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    if args.command in {"list-interferences", "list-java-interferences"}:
        rows = []
        for interference in interference_registry().values():
            rows.append(
                {
                    "category": interference.category,
                    "interference": interference.slug,
                    "description": interference.description,
                    "target_policy": INTERFERENCE_SPEC_BY_SLUG[
                        interference.slug
                    ].target_policy,
                    "template_count": INTERFERENCE_SPEC_BY_SLUG[
                        interference.slug
                    ].template_count,
                    "implementation": (
                        f"{interference.__class__.__module__}."
                        f"{interference.__class__.__name__}"
                    ),
                }
            )
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    provenance = construct_interference_dataset(
        args.input,
        args.output,
        args.seed,
        args.interferences,
    )
    print(json.dumps(provenance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
