from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Combine high/low Java readability folders into one binary JSONL dataset."
    )
    parser.add_argument("--high-dir", type=Path, default=Path("datasets/high"))
    parser.add_argument("--low-dir", type=Path, default=Path("datasets/low"))
    parser.add_argument("-o", "--output", type=Path, default=Path("datasets/readability_binary.jsonl"))
    args = parser.parse_args()

    rows = []
    rows.extend(read_split(args.high_dir, label="high", score=1.0))
    rows.extend(read_split(args.low_dir, label="low", score=0.0))
    rows.sort(key=lambda row: (row["readability"], row["item_id"]))

    if not rows:
        raise SystemExit("No .java files found in the high/low input directories.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    counts = {
        "high": sum(1 for row in rows if row["readability"] == "high"),
        "low": sum(1 for row in rows if row["readability"] == "low"),
    }
    print(f"Wrote {len(rows)} rows to {args.output}")
    print(f"high={counts['high']} low={counts['low']}")


def read_split(directory: Path, *, label: str, score: float) -> list[dict]:
    if not directory.is_dir():
        raise SystemExit(f"Missing directory: {directory}")
    rows = []
    for path in sorted(directory.glob("*.java")):
        code = path.read_text(encoding="utf-8")
        rows.append(
            {
                "item_id": path.stem,
                "code": code,
                "readability": label,
                "score": score,
                "language": "java",
                "source_file": str(path),
                "evaluation_metric": "mcc",
            }
        )
    return rows


if __name__ == "__main__":
    main()
