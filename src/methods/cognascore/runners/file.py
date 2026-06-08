from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..visualization import write_visualization
from .common import add_scoring_args, build_scorer, configured_output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CognaScore over one Java source file.")
    parser.add_argument("source", type=Path, nargs="?", default=Path("examples/cognascore_example.java"))
    add_scoring_args(parser)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result_dir = configured_output_dir(args, args.source.stem)
    result_dir.mkdir(parents=True, exist_ok=True)
    source = args.source.read_text(encoding="utf-8")
    scorer = build_scorer(args)
    record = scorer.process(source, task_id=str(args.source))
    description = (
        f"model={args.embedding_model}, DBSCAN eps={args.eps}, minPts={args.min_pts}"
    )
    payload = {
        "meta": {
            "dataset": args.source.stem,
            "description": description,
            "embedding_model": args.embedding_model,
            "dbscan": {
                "eps": args.eps,
                "min_pts": args.min_pts,
            },
        },
        "record": record.to_json(),
    }
    result_path = result_dir / "result.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_visualization(
        result_dir / "visualization",
        dataset=args.source.stem,
        description=description,
        records=[record],
    )
    print(f"Wrote {result_path}", flush=True)
    print(f"Wrote {result_dir / 'visualization' / 'visualize.html'}", flush=True)


if __name__ == "__main__":
    main()
