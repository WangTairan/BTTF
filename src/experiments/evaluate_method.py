import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Iterable

from src.datasets import DatasetItem, load_code_dataset
from src.experiments.registry import (
    COGNASCORE_DEFAULT_CACHE_DIR,
    COGNASCORE_DEFAULT_MODEL,
    method_choices,
    is_method_dataset_supported,
    method_history_policy,
    method_output_key,
)
from src.experiments.paths import dataset_name_for_path, output_dir, safe_path_part
from src.experiments.progress import DatasetProgress, batch_progress
from src.experiments.statistics import matthews_correlation_coefficient, spearman


MethodFn = Callable[[str], dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate readability methods over code datasets."
    )
    parser.add_argument(
        "dataset",
        type=Path,
        help="Dataset path or directory. Supports all code adapters under src/datasets/.",
    )
    parser.add_argument(
        "--method",
        choices=method_choices(),
        required=True,
        help="Readability method to run.",
    )
    parser.add_argument("--model", default="gpt41-nano", help="LLM model key for --method llm.")
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--models", type=Path, default=COGNASCORE_DEFAULT_CACHE_DIR)
    parser.add_argument("--eps", type=float, default=0.18, help="CognaScore DBSCAN eps.")
    parser.add_argument("--min-pts", type=int, default=2, help="CognaScore DBSCAN min_pts.")
    parser.add_argument("--batch-size", type=int, default=32, help="CognaScore embedding batch size.")
    parser.add_argument("--device", help="CognaScore embedding device: cpu, cuda, mps, or auto.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Output root. Defaults to automatic paths under "
            "output/<method>/<dataset>/."
        ),
    )
    parser.add_argument("--limit", type=int, help="Run at most this many items.")
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_method_dataset(args)
    items = list(load_items(args.dataset))
    if args.limit is not None:
        items = items[: args.limit]

    method = build_method(args)
    dataset_name = dataset_name_for_path(args.dataset)
    method_name = method_output_key(args.method)
    result_dir = output_dir(args.output, method_name, dataset_name, *method_output_parts(args))
    result_dir.mkdir(parents=True, exist_ok=True)
    if args.method == "llm":
        summary_path = run_llm_batch(args, items, result_dir)
        print(f"Wrote {summary_path}", flush=True)
        return

    rows = []
    progress = DatasetProgress(len(items))
    for index, item in enumerate(items, start=1):
        output_path = result_dir / f"{safe_path_part(item.task_id)}.json"
        if args.skip_existing and output_path.exists():
            row = json.loads(output_path.read_text(encoding="utf-8"))
            rows.append(row)
            progress.skipping(index, item.task_id)
            continue

        progress.running(index, item.task_id)
        try:
            result = method(item.content)
            score = normalize_score(result.get("score"))
            row = {
                "task_id": item.task_id,
                "readability_score": item.readability_score,
                "method": args.method,
                "score": score,
                "result": result,
                "metadata": item.metadata,
            }
        except Exception as exc:
            row = {
                "task_id": item.task_id,
                "readability_score": item.readability_score,
                "method": args.method,
                "score": None,
                "error": repr(exc),
                "metadata": item.metadata,
            }
        output_path.write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
        rows.append(row)

    summary_path = write_summary(result_dir, args, rows)
    print(f"Wrote {summary_path}", flush=True)


def run_llm_batch(args: argparse.Namespace, items: list[DatasetItem], result_dir: Path) -> Path:
    from src.methods.llm_prompt import llm_prompt_engineering_scores

    rows_by_task: dict[str, dict[str, Any]] = {}
    pending: list[tuple[int, DatasetItem, Path]] = []
    progress = DatasetProgress(len(items))
    for index, item in enumerate(items, start=1):
        output_path = result_dir / f"{safe_path_part(item.task_id)}.json"
        if args.skip_existing and output_path.exists():
            row = json.loads(output_path.read_text(encoding="utf-8"))
            rows_by_task[item.task_id] = row
            progress.skipping(index, item.task_id)
        else:
            pending.append((index, item, output_path))

    if pending:
        print(f"Submitting LLM batch: {len(pending)} pending / {len(items)} total", flush=True)
        codes = [item.content for _, item, _ in pending]
        batch_state_path = result_dir / ".batch_state.json"
        results = llm_prompt_engineering_scores(
            codes,
            model_name=args.model,
            state_path=batch_state_path,
            progress=batch_progress("llm batch"),
        )
        for (index, item, output_path), result in zip(pending, results):
            progress.writing(index, item.task_id)
            try:
                score = normalize_score(result.get("score"))
                row = {
                    "task_id": item.task_id,
                    "readability_score": item.readability_score,
                    "method": args.method,
                    "score": score,
                    "result": result,
                    "metadata": item.metadata,
                }
            except Exception as exc:
                row = {
                    "task_id": item.task_id,
                    "readability_score": item.readability_score,
                    "method": args.method,
                    "score": None,
                    "error": repr(exc),
                    "metadata": item.metadata,
                }
            output_path.write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
            rows_by_task[item.task_id] = row

    rows = [rows_by_task[item.task_id] for item in items if item.task_id in rows_by_task]
    return write_summary(result_dir, args, rows)


def load_items(path: Path) -> Iterable[DatasetItem]:
    return load_code_dataset(path)


def validate_method_dataset(args: argparse.Namespace) -> None:
    if not is_method_dataset_supported(args.method, args.dataset):
        raise SystemExit(
            "CognaScore does not support the Dorn dataset: its samples are "
            "structurally truncated Java fragments rather than parseable "
            "compilation units or class-member snippets."
        )


def build_method(args: argparse.Namespace) -> MethodFn:
    if args.method == "posnett":
        from src.methods.posnett import posnett_model

        return lambda code: posnett_model(code).__dict__
    if args.method == "scalabrino":
        from src.methods.scalabrino import scalabrino_model

        return lambda code: scalabrino_model(code).__dict__
    if args.method == "cognascore":
        from src.methods.cognascore import CognaScoreScorer

        scorer = CognaScoreScorer(
            model_name=args.embedding_model,
            eps=args.eps,
            min_pts=args.min_pts,
            batch_size=args.batch_size,
            device=args.device,
            cache_dir=args.models,
        )
        return lambda code: scorer.score(code).__dict__
    if args.method == "llm":
        from src.methods.llm_prompt import llm_prompt_engineering_score

        return lambda code: llm_prompt_engineering_score(code, model_name=args.model)
    raise ValueError(f"Unknown method: {args.method}")


def method_config_name(args: argparse.Namespace) -> str | None:
    if args.method == "llm":
        return args.model
    if args.method == "cognascore":
        return args.embedding_model
    return None


def method_full_config_name(args: argparse.Namespace) -> str | None:
    if args.method == "cognascore":
        from src.methods.cognascore.results import parameter_slug

        return parameter_slug(args.embedding_model, args.eps, args.min_pts)
    return method_config_name(args)


def method_output_parts(args: argparse.Namespace) -> tuple[str, ...]:
    if args.method == "llm":
        return (args.model,)
    if args.method == "cognascore":
        from src.methods.cognascore.results import model_slug

        return (model_slug(args.embedding_model),)
    return ()


def normalize_score(value: Any) -> float:
    score = float(value)
    if not math.isfinite(score):
        raise ValueError(f"Method returned a non-finite score: {value}")
    return score


def best_binary_threshold(
    rows: list[dict],
) -> tuple[float | None, float | None, dict[str, int] | None, int | None]:
    scores = sorted({float(row["score"]) for row in rows})
    if not scores:
        return None, None, None, None
    if len(scores) == 1:
        candidates = [scores[0] - 1e-12, scores[0] + 1e-12]
    else:
        candidates = [scores[0] - 1e-12]
        candidates.extend((left + right) / 2 for left, right in zip(scores, scores[1:]))
        candidates.append(scores[-1] + 1e-12)

    actual = [int(float(row["readability_score"])) for row in rows]
    best: tuple[float, float, dict[str, int], int] | None = None
    for threshold in candidates:
        predicted = [int(float(row["score"]) >= threshold) for row in rows]
        mcc = matthews_correlation_coefficient(predicted, actual)
        confusion_matrix = {
            "true_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 1),
            "true_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 0),
            "false_positive": sum(1 for p, a in zip(predicted, actual) if p == 1 and a == 0),
            "false_negative": sum(1 for p, a in zip(predicted, actual) if p == 0 and a == 1),
        }
        predicted_positive = sum(predicted)
        candidate = (threshold, mcc, confusion_matrix, predicted_positive)
        if best is None or candidate[1] > best[1]:
            best = candidate
    assert best is not None
    return best


def write_summary(output_dir: Path, args: argparse.Namespace, rows: list[dict]) -> Path:
    valid = [
        row
        for row in rows
        if row.get("score") is not None
        and row.get("readability_score") is not None
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
        threshold, mcc, confusion_matrix, predicted_positive_count = best_binary_threshold(valid)
    elif not binary and len(valid) >= 2:
        rho = spearman(
            [float(row["score"]) for row in valid],
            [float(row["readability_score"]) for row in valid],
        )
    evaluation_metric = "mcc" if binary else "spearman"
    payload = {
        "dataset": str(args.dataset),
        "method": args.method,
        "model": method_config_name(args),
        "configuration": method_full_config_name(args),
        "embedding_model": args.embedding_model if args.method == "cognascore" else None,
        "dbscan": (
            {
                "eps": args.eps,
                "min_pts": args.min_pts,
            }
            if args.method == "cognascore"
            else None
        ),
        "output_policy": method_history_policy(args.method),
        "count": len(rows),
        "valid_count": len(valid),
        "error_count": sum(1 for row in rows if row.get("score") is None),
        "evaluation_metric": evaluation_metric,
        "classification_threshold": threshold,
        "classification_threshold_policy": "best_on_dataset" if binary else None,
        "classification_direction": "score>=threshold" if binary else None,
        "predicted_positive_count": predicted_positive_count,
        "spearman": rho,
        "mcc": mcc,
        "confusion_matrix": confusion_matrix,
        "mean_score": mean(float(row["score"]) for row in valid) if valid else None,
        "results": rows,
    }
    path = output_dir / "summary.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    main()
