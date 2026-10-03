from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

from tree_sitter import Language, Parser
import tree_sitter_cpp
import tree_sitter_java
import tree_sitter_python

from src.datasets import load_code_dataset
from src.experiments.statistics import matthews_correlation_coefficient, spearman
from src.methods.readability_model.dataset_io import item_source_sha256


DATASETS: dict[str, Path] = {
    "mbjp": Path("datasets/mbjp_dev_dataset/readability_dataset.json"),
    "buse": Path("datasets/buse"),
    "scalabrino": Path("datasets/scalabrino/dataset"),
    "jetbrains": Path("datasets/jetbrains"),
    "dorn": Path("datasets/dorn/dataset"),
    "schnappinger": Path("datasets/schnappinger"),
    "java_comparative_obfuscation": Path(
        "datasets/constructed/java-comparative-obfuscation-class-100"
    ),
    "python_comparative_degradation": Path(
        "datasets/constructed/python-comparative-degradation-class-100"
    ),
}


PARSERS = {
    "java": Parser(Language(tree_sitter_java.language())),
    "python": Parser(Language(tree_sitter_python.language())),
    "cpp": Parser(Language(tree_sitter_cpp.language())),
}


def logical_loc(content: str, language: str) -> int:
    """Count language-aware statement and declaration nodes in source code."""
    normalized = language.lower()
    parser_key = "python" if normalized == "python" else "cpp" if normalized in {
        "c", "cpp", "c++", "cuda"
    } else "java"
    tree = PARSERS[parser_key].parse(content.encode("utf-8"))
    count = 0
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        kind = node.type
        if parser_key == "java":
            selected = kind.endswith("_statement") or kind in {
                "local_variable_declaration",
                "field_declaration",
                "method_declaration",
                "constructor_declaration",
            }
        elif parser_key == "python":
            selected = kind.endswith("_statement") or kind in {
                "function_definition",
                "class_definition",
            }
        else:
            selected = (
                kind.endswith("_statement") and kind != "compound_statement"
            ) or kind in {"declaration", "function_definition"}
        count += int(selected)
        stack.extend(node.children)
    return max(count, 1)


def item_language(dataset_name: str, metadata: dict) -> str:
    language = str(metadata.get("language") or "").lower()
    if language:
        return language
    if dataset_name in {"mbjp", "buse", "scalabrino", "schnappinger", "jetbrains"}:
        return "java"
    return "java"


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


def write_dataset(
    dataset_name: str,
    dataset_path: Path,
    output_root: Path,
    *,
    skip_existing: bool = False,
) -> Path:
    items = load_code_dataset(dataset_path)
    output_dir = output_root / "lloc_baseline" / dataset_name
    summary_path = output_dir / "summary.json"
    reusable_by_task, reusable_by_hash = load_reusable_rows(summary_path) if skip_existing else ({}, {})
    rows = []
    computed_count = 0
    reused_count = 0
    for item in items:
        source_hash = item_source_sha256(item)
        existing = reusable_by_task.get(item.task_id)
        if existing is None or result_source_sha256(existing) != source_hash:
            existing = reusable_by_hash.get(source_hash)
        if existing is not None:
            row = dict(existing)
            row.update(
                task_id=item.task_id,
                readability_score=item.readability_score,
                source_sha256=source_hash,
                metadata=item.metadata,
            )
            reused_count += 1
        else:
            line_count = logical_loc(
                item.content, item_language(dataset_name, item.metadata)
            )
            row = {
                "task_id": item.task_id,
                "readability_score": item.readability_score,
                "method": "lloc_baseline",
                "source_sha256": source_hash,
                "score": float(line_count),
                "result": {
                    "score": float(line_count),
                    "lloc": line_count,
                    "formula": "score = LLOC; lower LLOC predicts higher readability",
                },
                "metadata": item.metadata,
            }
            reusable_by_hash[source_hash] = row
            computed_count += 1
        rows.append(row)

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
        "method": "lloc_baseline",
        "model": None,
        "configuration": "ast_statement_declaration_count",
        "output_policy": "overwrite",
        "incremental_resume": skip_existing,
        "computed_count": computed_count,
        "reused_count": reused_count,
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
            "name": "LLOC baseline",
            "formula": "score = LLOC",
            "description": "A language-aware size baseline that counts AST statement and declaration nodes; comments and blank lines are excluded. Continuous datasets report the raw LLOC correlation with readability.",
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary_path


def load_reusable_rows(path: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    if not path.is_file():
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_task: dict[str, dict] = {}
    by_hash: dict[str, dict] = {}
    for row in payload.get("results", []):
        task_id = str(row.get("task_id") or "")
        source_hash = result_source_sha256(row)
        if task_id:
            by_task[task_id] = row
        if source_hash:
            by_hash.setdefault(source_hash, row)
    return by_task, by_hash


def result_source_sha256(row: dict) -> str | None:
    value = row.get("source_sha256") or row.get("metadata", {}).get("content_sha256")
    return str(value) if value else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LLOC readability baseline.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("results/methods"),
        help="Root method-results directory.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse LLOC rows with an unchanged source SHA-256.",
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
        path = write_dataset(
            name,
            DATASETS[name],
            args.output_root,
            skip_existing=args.skip_existing,
        )
        print(path)


if __name__ == "__main__":
    main()
