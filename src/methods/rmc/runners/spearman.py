import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Callable, Iterable, Sequence

from src.experiments.statistics import spearman

ScoreAggregate = Callable[[Sequence[float]], float]
MaskFilter = Callable[[dict], bool]
EMBEDDING_CACHE_ID = "nomic-ai/nomic-embed-text-v1.5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute Spearman correlations between RMC scores and GT readability."
    )
    parser.add_argument(
        "result_path",
        type=Path,
        help="Directory containing per-task result.json files.",
    )
    parser.add_argument(
        "--segment-field",
        choices=("both", "selected_segments", "masked_segments"),
        default="both",
        help="Mask segment field used for filtering, defaults to both.",
    )
    parser.add_argument(
        "--similarity",
        choices=(
            "stored",
            "sequence",
            "exact_match",
            "edit",
            "token_jaccard",
            "token_cosine",
            "bleu",
            "rouge_l",
            "cosine",
        ),
        default="stored",
        help=(
            "Similarity source. stored uses result.json scores; exact/token/ngram "
            "metrics recompute locally; cosine uses local embeddings."
        ),
    )
    parser.add_argument(
        "--similarity-cache",
        type=Path,
        help=(
            "JSONL cache for recomputed similarity scores. Defaults to "
            "<result_path>/.similarity_cache.<similarity>.jsonl for cosine."
        ),
    )
    parser.add_argument(
        "--no-similarity-cache",
        action="store_true",
        help="Disable reading/writing the recomputed similarity cache.",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Populate the similarity cache and exit without printing diagnostics.",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Bootstrap resamples per diagnostic family, defaults to 1000.",
    )
    parser.add_argument(
        "--min-tasks",
        type=int,
        default=5,
        help="Only print families with at least this many tasks, defaults to 5.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result_files = sorted(args.result_path.glob("*/result.json"))
    if not result_files:
        raise SystemExit(f"No */result.json files found under {args.result_path}")

    segment_fields = get_segment_fields(args.segment_field)
    cache_path = resolve_similarity_cache_path(args)
    prepared_results = load_prepared_results(result_files, args.similarity, cache_path)

    print(f"path: {args.result_path}")
    print(f"similarity: {args.similarity}")
    if cache_path is not None:
        print(f"similarity_cache: {cache_path}")
    print("")
    if args.cache_only:
        return

    diagnostics = []
    if uses_stratified_ast_scoring(prepared_results):
        rows = collect_ast_stratified_rows(prepared_results)
        if len(rows) >= args.min_tasks:
            diagnostics.append(
                evaluate_family(
                    family={"family": "official:ast_strata"},
                    aggregate_name="mean",
                    rows=rows,
                    bootstrap_samples=args.bootstrap,
                )
            )
    for family in build_diagnostic_families(prepared_results, segment_fields):
        for aggregate_name, aggregate in (("mean", mean), ("median", median)):
            rows = collect_rows(prepared_results, family["filter"], aggregate)
            if len(rows) < args.min_tasks:
                continue
            diagnostics.append(
                evaluate_family(
                    family=family,
                    aggregate_name=aggregate_name,
                    rows=rows,
                    bootstrap_samples=args.bootstrap,
                )
            )

    diagnostics.sort(
        key=lambda item: (
            math.isnan(item["rho"]),
            -abs(item["rho"]) if not math.isnan(item["rho"]) else 0.0,
            item["family"],
            item["agg"],
        )
    )
    print_diagnostics(diagnostics)


def resolve_similarity_cache_path(args: argparse.Namespace) -> Path | None:
    if args.no_similarity_cache:
        return None
    if args.similarity_cache is not None:
        return args.similarity_cache
    if args.similarity == "cosine":
        return args.result_path / ".similarity_cache.cosine.jsonl"
    return None


def get_segment_fields(value: str) -> tuple[tuple[str, str], ...]:
    if value == "both":
        return (
            ("selected", "selected_segments"),
            ("masked", "masked_segments"),
        )
    if value == "selected_segments":
        return (("selected", "selected_segments"),)
    return (("masked", "masked_segments"),)


def build_filters(
    segment_field: str,
    segment_label: str,
    highest_segment_counts: tuple[int | None, int | None],
) -> tuple[tuple[str, MaskFilter], ...]:
    highest_one, highest_two = highest_segment_counts
    filters: list[tuple[str, MaskFilter]] = [
        ("all", lambda mask: True),
        ("drop1", lambda mask: mask.get(segment_field) != 1),
        (
            "drop1-2",
            lambda mask: mask.get(segment_field) not in (1, 2),
        ),
        (
            "drop1-3",
            lambda mask: mask.get(segment_field) not in (1, 2, 3),
        ),
    ]

    if segment_label == "selected":
        filters.append(
            (
                "drop123hi1",
                lambda mask: mask.get(segment_field) not in (1, 2, 3, highest_one),
            )
        )
        filters.append(
            (
            "drop123hi2",
            lambda mask: mask.get(segment_field) not in (1, 2, 3)
                and mask.get(segment_field) not in (highest_one, highest_two),
            )
        )

    return tuple(filters)


def build_diagnostic_families(
    prepared_results: Sequence[dict],
    segment_fields: tuple[tuple[str, str], ...],
) -> list[dict]:
    families: list[dict] = []

    for segment_label, segment_field in segment_fields:
        highest_segment_counts = get_highest_segment_counts(prepared_results, segment_field)
        for filter_label, mask_filter in build_filters(
            segment_field,
            segment_label,
            highest_segment_counts,
        ):
            families.append(
                {
                    "family": f"{segment_label}:{filter_label}",
                    "filter": mask_filter,
                }
            )

    ratio_bins = (
        ("ratio:00-10", 0.00, 0.10),
        ("ratio:10-20", 0.10, 0.20),
        ("ratio:20-35", 0.20, 0.35),
        ("ratio:35-50", 0.35, 0.50),
        ("ratio:50-75", 0.50, 0.75),
        ("ratio:75-100", 0.75, 1.01),
    )
    for label, low, high in ratio_bins:
        families.append(
            {
                "family": label,
                "filter": lambda mask, low=low, high=high: low <= mask["mask_ratio"] < high,
            }
        )

    position_bins = (
        ("pos:early", "early"),
        ("pos:middle", "middle"),
        ("pos:late", "late"),
        ("pos:mixed", "mixed"),
    )
    for label, value in position_bins:
        families.append(
            {
                "family": label,
                "filter": lambda mask, value=value: mask["position_bin"] == value,
            }
        )

    families.extend(
        [
            {
                "family": "rep:ratio20-50",
                "filter": lambda mask: 0.20 <= mask["mask_ratio"] < 0.50,
            },
            {
                "family": "rep:sel>=3_ratio20-50",
                "filter": lambda mask: mask["selected_segments"] >= 3
                and 0.20 <= mask["mask_ratio"] < 0.50,
            },
            {
                "family": "rep:sel>=4_ratio20-50",
                "filter": lambda mask: mask["selected_segments"] >= 4
                and 0.20 <= mask["mask_ratio"] < 0.50,
            },
            {
                "family": "rep:midpos_ratio20-50",
                "filter": lambda mask: mask["position_bin"] in ("middle", "mixed")
                and 0.20 <= mask["mask_ratio"] < 0.50,
            },
            {
                "family": "rep:nontrivial",
                "filter": lambda mask: mask["selected_segments"] >= 3
                and mask["selected_segments"] < mask["max_selected_segments"]
                and 0.15 <= mask["mask_ratio"] < 0.60,
            },
        ]
    )

    seen = set()
    unique = []
    for family in families:
        if family["family"] in seen:
            continue
        seen.add(family["family"])
        unique.append(family)
    return unique


def collect_rows(
    prepared_results: Iterable[dict],
    mask_filter: MaskFilter,
    aggregate: ScoreAggregate,
) -> list[dict]:
    rows = []
    for data in prepared_results:
        gt_score = data["gt_score"]
        masks_by_index = data["masks_by_index"]
        scores = [
            float(recovery["selected_similarity"])
            for recovery in data["recoveries"]
            if mask_filter(masks_by_index[recovery["index"]])
        ]
        if not scores:
            continue

        rows.append(
            {
                "task_id": get_task_id(data),
                "gt_score": gt_score,
                "rmc_score": float(aggregate(scores)),
                "mask_count": len(scores),
                "score_std": pstdev(scores) if len(scores) > 1 else 0.0,
            }
        )
    return rows


def uses_stratified_ast_scoring(prepared_results: Iterable[dict]) -> bool:
    return any(
        mask.get("strategy")
        in {
            "java_ast_stratified_v6",
            "java_ast_stratified_v7",
            "java_ast_prefix_v1",
            "natural_language_stratified_v1",
        }
        for data in prepared_results
        for mask in data.get("masks", ())
    )


def collect_ast_stratified_rows(prepared_results: Iterable[dict]) -> list[dict]:
    rows = []
    for data in prepared_results:
        groups: dict[tuple[str, int], list[float]] = {}
        for recovery in data["recoveries"]:
            mask = data["masks_by_index"][recovery["index"]]
            key = (str(mask.get("ast_granularity")), int(mask["selected_segments"]))
            groups.setdefault(key, []).append(float(recovery["selected_similarity"]))
        if not groups:
            continue
        stratum_scores = [mean(scores) for scores in groups.values()]
        rows.append(
            {
                "task_id": get_task_id(data),
                "gt_score": data["gt_score"],
                "rmc_score": float(mean(stratum_scores)),
                "mask_count": sum(len(scores) for scores in groups.values()),
                "score_std": pstdev(stratum_scores) if len(stratum_scores) > 1 else 0.0,
            }
        )
    return rows


def evaluate_family(
    family: dict,
    aggregate_name: str,
    rows: list[dict],
    bootstrap_samples: int,
) -> dict:
    rho = spearman(
        [row["rmc_score"] for row in rows],
        [row["gt_score"] for row in rows],
    )
    loo_min, loo_max = leave_one_out_range(rows)
    boot_low, boot_high = bootstrap_interval(rows, bootstrap_samples)
    return {
        "family": family["family"],
        "agg": aggregate_name,
        "n": len(rows),
        "rho": rho,
        "loo_min": loo_min,
        "loo_max": loo_max,
        "boot_low": boot_low,
        "boot_high": boot_high,
        "avg_masks": mean(row["mask_count"] for row in rows) if rows else math.nan,
        "samples": sum(row["mask_count"] for row in rows),
        "avg_std": mean(row["score_std"] for row in rows) if rows else math.nan,
    }


def leave_one_out_range(rows: Sequence[dict]) -> tuple[float, float]:
    if len(rows) < 3:
        return math.nan, math.nan
    values = []
    for index in range(len(rows)):
        kept = [row for row_index, row in enumerate(rows) if row_index != index]
        values.append(
            spearman(
                [row["rmc_score"] for row in kept],
                [row["gt_score"] for row in kept],
            )
        )
    values = [value for value in values if not math.isnan(value)]
    if not values:
        return math.nan, math.nan
    return min(values), max(values)


def bootstrap_interval(
    rows: Sequence[dict],
    samples: int,
    seed: int = 123,
) -> tuple[float, float]:
    if samples <= 0 or len(rows) < 3:
        return math.nan, math.nan
    rng = random.Random(seed)
    values = []
    for _ in range(samples):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        value = spearman(
            [row["rmc_score"] for row in sample],
            [row["gt_score"] for row in sample],
        )
        if not math.isnan(value):
            values.append(value)
    if not values:
        return math.nan, math.nan
    values.sort()
    low_index = int(0.025 * (len(values) - 1))
    high_index = int(0.975 * (len(values) - 1))
    return values[low_index], values[high_index]


def print_diagnostics(rows: Sequence[dict]) -> None:
    print(
        f"{'family':<28} {'agg':<6} {'n':>3} {'rho':>9} "
        f"{'loo_min':>9} {'loo_max':>9} {'boot_lo':>9} {'boot_hi':>9} "
        f"{'avg_masks':>9} {'samples':>7} {'avg_std':>8}"
    )
    print("-" * 119)
    for row in rows:
        print(
            f"{row['family']:<28} {row['agg']:<6} {row['n']:>3} "
            f"{format_float(row['rho']):>9} {format_float(row['loo_min']):>9} "
            f"{format_float(row['loo_max']):>9} {format_float(row['boot_low']):>9} "
            f"{format_float(row['boot_high']):>9} {format_float(row['avg_masks']):>9} "
            f"{row['samples']:>7} {format_float(row['avg_std']):>8}"
        )


def get_gt_score(data: dict) -> float | None:
    value = (data.get("dataset_item") or {}).get("readability_score")
    if value is None:
        return None
    return float(value)


def load_prepared_results(
    result_files: Iterable[Path],
    similarity: str = "stored",
    cache_path: Path | None = None,
) -> list[dict]:
    results = []
    for path in result_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        gt_score = get_gt_score(data)
        if gt_score is None:
            continue

        data["gt_score"] = gt_score
        data["masks_by_index"] = prepare_masks(data["masks"], len(data["source_lines"]))
        results.append(data)
    prepare_all_recovery_scores(results, similarity, cache_path)
    return results


def prepare_all_recovery_scores(
    results: list[dict],
    similarity: str,
    cache_path: Path | None = None,
) -> None:
    if similarity != "cosine":
        for data in results:
            prepare_recovery_scores(data, similarity)
        return

    from src.methods.rmc.embeddings import embed_texts_cached, vector_cosine

    cache = load_similarity_cache(cache_path)
    missing_pairs: dict[str, tuple[str, str]] = {}
    hits = 0
    total = 0
    for data in results:
        for recovery in data["recoveries"]:
            total += 1
            expected, recovered = recovery_text_pair(recovery)
            key = similarity_cache_key(similarity, expected, recovered)
            if key in cache:
                recovery["selected_similarity"] = cache[key]
                hits += 1
            else:
                missing_pairs[key] = (expected, recovered)

    texts: list[str] = []
    for expected, recovered in missing_pairs.values():
        texts.append(expected)
        texts.append(recovered)

    vectors = embed_texts_cached(texts) if texts else {}
    new_scores: dict[str, float] = {}
    for key, (expected, recovered) in missing_pairs.items():
        new_scores[key] = float(vector_cosine(vectors[expected], vectors[recovered]))

    if new_scores:
        append_similarity_cache(cache_path, similarity, missing_pairs, new_scores)

    for data in results:
        for recovery in data["recoveries"]:
            if "selected_similarity" in recovery:
                continue
            expected, recovered = recovery_text_pair(recovery)
            recovery["selected_similarity"] = new_scores[
                similarity_cache_key(similarity, expected, recovered)
            ]

    print(
        f"similarity cache: {hits}/{total} hits, {len(new_scores)} computed",
        flush=True,
    )


def recovery_text_pair(recovery: dict) -> tuple[str, str]:
    expected = recovery.get("expected_text") or recovery.get("expected_source") or ""
    recovered = recovery.get("recovered_text") or recovery.get("recovered_code") or ""
    return expected, recovered


def load_similarity_cache(cache_path: Path | None) -> dict[str, float]:
    if cache_path is None or not cache_path.exists():
        return {}

    cache: dict[str, float] = {}
    with cache_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(
                    f"Skipping malformed cache row {cache_path}:{line_number}",
                    flush=True,
                )
                continue
            key = row.get("key")
            score = row.get("score")
            if isinstance(key, str) and isinstance(score, (int, float)):
                cache[key] = float(score)
    return cache


def append_similarity_cache(
    cache_path: Path | None,
    similarity: str,
    pairs: dict[str, tuple[str, str]],
    scores: dict[str, float],
) -> None:
    if cache_path is None or not scores:
        return

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as handle:
        for key, score in scores.items():
            expected, recovered = pairs[key]
            row = {
                "key": key,
                "similarity": similarity,
                "embedder": EMBEDDING_CACHE_ID,
                "expected_sha256": sha256_text(expected),
                "recovered_sha256": sha256_text(recovered),
                "score": score,
            }
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def similarity_cache_key(similarity: str, expected: str, recovered: str) -> str:
    payload = {
        "similarity": similarity,
        "embedder": EMBEDDING_CACHE_ID,
        "expected_sha256": sha256_text(expected),
        "recovered_sha256": sha256_text(recovered),
        "version": 1,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prepare_recovery_scores(data: dict, similarity: str) -> None:
    if similarity == "stored":
        for recovery in data["recoveries"]:
            recovery["selected_similarity"] = float(recovery["similarity"])
        return

    if similarity == "sequence":
        from difflib import SequenceMatcher

        def score(left: str, right: str) -> float:
            return SequenceMatcher(None, left, right).ratio()

    elif similarity == "token_cosine":
        from src.methods.rmc.similarity import token_cosine_similarity

        score = token_cosine_similarity

    elif similarity == "exact_match":
        from src.methods.rmc.similarity import exact_match_similarity

        score = exact_match_similarity

    elif similarity == "edit":
        from src.methods.rmc.similarity import edit_similarity

        score = edit_similarity

    elif similarity == "token_jaccard":
        from src.methods.rmc.similarity import token_jaccard_similarity

        score = token_jaccard_similarity

    elif similarity == "bleu":
        from src.methods.rmc.similarity import bleu_similarity

        score = bleu_similarity

    elif similarity == "rouge_l":
        from src.methods.rmc.similarity import rouge_l_similarity

        score = rouge_l_similarity

    elif similarity == "cosine":
        from src.methods.rmc.similarity import cosine_similarity

        score = cosine_similarity
    else:
        raise ValueError(f"Unknown similarity: {similarity}")

    for recovery in data["recoveries"]:
        expected, recovered = recovery_text_pair(recovery)
        recovery["selected_similarity"] = float(score(expected, recovered))


def prepare_masks(masks: Sequence[dict], source_line_count: int) -> dict[int, dict]:
    prepared = {}
    for mask in masks:
        normalized = normalize_mask(mask, source_line_count)
        prepared[int(normalized["index"])] = normalized
    max_selected = max(
        (int(mask["selected_segments"]) for mask in prepared.values()),
        default=0,
    )
    for mask in prepared.values():
        mask["max_selected_segments"] = max_selected
    return prepared


def get_highest_segment_counts(
    prepared_results: Iterable[dict],
    segment_field: str,
) -> tuple[int | None, int | None]:
    values = {
        int(mask[segment_field])
        for data in prepared_results
        for mask in data["masks_by_index"].values()
    }
    ordered = sorted(values)
    if not ordered:
        return None, None
    highest_one = ordered[-1]
    highest_two = ordered[-2] if len(ordered) > 1 else ordered[-1]
    return highest_one, highest_two


def normalize_mask(mask: dict, source_line_count: int) -> dict:
    normalized = dict(mask)
    normalized["masked_segments"] = len(mask["spans"])
    if "selected_segments" not in normalized:
        normalized["selected_segments"] = infer_selected_segments(mask, source_line_count)
    masked_length = sum(int(span["length"]) for span in mask["spans"])
    normalized["masked_length"] = masked_length
    normalized["source_line_count"] = source_line_count
    normalized["mask_ratio"] = masked_length / source_line_count if source_line_count else 0.0
    normalized["position_bin"] = infer_position_bin(mask, source_line_count)
    return normalized


def infer_position_bin(mask: dict, source_line_count: int) -> str:
    if source_line_count <= 0 or not mask["spans"]:
        return "mixed"
    starts = [int(span["start"]) / source_line_count for span in mask["spans"]]
    ends = [int(span["end"]) / source_line_count for span in mask["spans"]]
    if min(starts) < 1 / 3 and max(ends) <= 1 / 3:
        return "early"
    if min(starts) >= 1 / 3 and max(ends) <= 2 / 3:
        return "middle"
    if min(starts) >= 2 / 3:
        return "late"
    return "mixed"


def infer_selected_segments(mask: dict, source_line_count: int) -> int:
    partitions = partition_indices(source_line_count, int(mask["granularity"]))
    selected = 0
    for span in mask["spans"]:
        selected += sum(
            1
            for start, end in partitions
            if start >= span["start"] and end <= span["end"]
        )
    return selected


def partition_indices(length: int, parts: int) -> list[tuple[int, int]]:
    return [
        ((index * length) // parts, ((index + 1) * length) // parts)
        for index in range(parts)
    ]


def get_task_id(data: dict) -> str:
    return str((data.get("dataset_item") or {}).get("task_id") or data["source_path"])


def format_float(value: float) -> str:
    if math.isnan(value):
        return "nan"
    return f"{value:.6f}"


if __name__ == "__main__":
    main()
