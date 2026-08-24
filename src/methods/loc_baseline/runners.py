from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

from src.datasets import load_code_dataset
from src.experiments.statistics import matthews_correlation_coefficient, spearman


DATASETS: dict[str, Path] = {
    "mbjp": Path("datasets/mbjp_dev_dataset/readability_dataset.json"),
    "buse": Path("datasets/buse"),
    "scalabrino": Path("datasets/scalabrino/dataset"),
    "jetbrains": Path("datasets/jetbrains"),
    "dorn": Path("datasets/dorn/dataset"),
    "schnappinger": Path("datasets/schnappinger"),
    "generated_readability_90": Path("datasets/generated_readability_90/dataset.jsonl"),
    "java_progressive_obfuscation": Path(
        "datasets/constructed/java-progressive-obfuscation-class-100"
    ),
}


def loc(content: str) -> int:
    return sum(1 for line in content.splitlines() if line.strip())


def best_binary_threshold_lower_is_positive(
    rows: list[dict],
) -> tuple[float | None, float | None, dict[str, int] | None, int | None]:
    scores = sorted({float(row["score"]) for row in rows})
    if not scores:
        return None, None, None, None
    candidates = [scores[0] - 1e-12]
    candidates.extend((left + right) / 2 for left, right in zip(scores, scores[1:]))
    candidates.append(scores[-1] + 1e-12)

    actual = [int(float(row["readability_score"])) for row in rows]
    best: tuple[float, float, dict[str, int], int] | None = None
    for threshold in candidates:
        predicted = [int(float(row["score"]) <= threshold) for row in rows]
        mcc = matthews_correlation_coefficient(predicted, actual)
        confusion_matrix = {
            "true_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 1),
            "true_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 0),
            "false_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 0),
            "false_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 1),
        }
        candidate = (threshold, mcc, confusion_matrix, sum(predicted))
        if best is None or candidate[1] > best[1]:
            best = candidate
    assert best is not None
    return best


def write_dataset(dataset_name: str, dataset_path: Path, output_root: Path) -> Path:
    items = load_code_dataset(dataset_path)
    rows = []
    for item in items:
        line_count = loc(item.content)
        rows.append(
            {
                "task_id": item.task_id,
                "readability_score": item.readability_score,
                "method": "loc_baseline",
                "score": float(line_count),
                "result": {
                    "score": float(line_count),
                    "loc": line_count,
                    "formula": "score = LOC; lower LOC predicts higher readability",
                },
                "metadata": item.metadata,
            }
        )

    valid = [
        row
        for row in rows
        if row.get("readability_score") is not None
        and row.get("score") is not None
        and math.isfinite(float(row["score"]))
    ]
    binary = bool(valid) and all(
        row.get("metadata", {}).get("evaluation_metric") == "mcc"
        for row in valid
    )

    threshold = None
    rho = None
    mcc = None
    confusion_matrix = None
    predicted_positive_count = None
    if binary:
        threshold, mcc, confusion_matrix, predicted_positive_count = best_binary_threshold_lower_is_positive(valid)
    elif len(valid) >= 2:
        rho = spearman(
            [float(row["score"]) for row in valid],
            [float(row["readability_score"]) for row in valid],
        )

    payload = {
        "dataset": str(dataset_path),
        "method": "loc_baseline",
        "model": None,
        "configuration": "negative_nonempty_loc",
        "output_policy": "overwrite",
        "count": len(rows),
        "valid_count": len(valid),
        "error_count": len(rows) - len(valid),
        "evaluation_metric": "mcc" if binary else "spearman",
        "classification_threshold": threshold,
        "classification_threshold_policy": "best_on_dataset" if binary else None,
        "classification_direction": "score<=threshold" if binary else "lower_score_more_readable",
        "predicted_positive_count": predicted_positive_count,
        "spearman": rho,
        "mcc": mcc,
        "confusion_matrix": confusion_matrix,
        "mean_score": mean(float(row["score"]) for row in valid) if valid else None,
        "results": rows,
        "baseline": {
            "name": "LOC baseline",
            "formula": "score = LOC",
            "description": "A length-only sanity-check baseline: snippets with fewer non-empty source lines are predicted to be more readable. Continuous datasets report the raw LOC correlation with readability.",
        },
    }
    output_dir = output_root / "loc_baseline" / dataset_name
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "summary.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LOC-only readability baseline.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("results/methods"),
        help="Root method-results directory.",
    )
    parser.add_argument(
        "--dataset",
        choices=sorted(DATASETS),
        action="append",
        help="Dataset to run. Defaults to all supported benchmark datasets.",
    )
    args = parser.parse_args()

    selected = args.dataset or list(DATASETS)
    for name in selected:
        path = write_dataset(name, DATASETS[name], args.output_root)
        print(path)


if __name__ == "__main__":
    main()
