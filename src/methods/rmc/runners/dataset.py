import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence

from src.datasets import DatasetItem
from src.methods.rmc import (
    ComplexityResult,
    DEFAULT_AST_GRANULARITY,
    DEFAULT_AST_MAX_COMBINATION_SIZE,
    DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
    DEFAULT_AST_MIN_TOKENS,
    DEFAULT_AST_SAMPLING_SEED,
    DEFAULT_CONSTRAINTS,
    MaskConstraints,
    make_llm_batch_recover,
    recursive_masking_complexity,
    recursive_masking_complexity_batch,
    sequence_similarity,
    java_ast_masks,
    java_ast_prefixes,
    natural_language_masks,
)
from src.methods.rmc.complexity import (
    evaluate_exact_mask_recovery,
    evaluate_scored_recovery,
    select_indexed_masks,
)
from src.methods.rmc.fragment_masking import java_fragment_control_masks
from src.methods.rmc.masking import delta_mask
from src.methods.rmc.report import result_to_dict, write_html_report, write_json_report
from src.methods.rmc.similarity import mean
from src.methods.rmc.text_units import clean_blank_units
from src.experiments.paths import dataset_name_for_path, output_dir, safe_path_part
from src.experiments.progress import DatasetProgress


@dataclass(frozen=True)
class RunnerConfig:
    dataset_path: Path
    output_root: Path | None
    model: str | None
    mock_recover: bool
    prompt_mode: str
    source_label: str
    text_unit: str
    line_numbering: str
    constraints: MaskConstraints = DEFAULT_CONSTRAINTS
    mask_indices: Sequence[int] | None = None
    mask_strategy: str = "sequence"
    ast_min_tokens: int = DEFAULT_AST_MIN_TOKENS
    ast_granularity: str = DEFAULT_AST_GRANULARITY
    max_combination_size: int = DEFAULT_AST_MAX_COMBINATION_SIZE
    max_samples_per_stratum: int | None = DEFAULT_AST_MAX_SAMPLES_PER_STRATUM
    sampling_seed: int = DEFAULT_AST_SAMPLING_SEED
    nl_granularity: str | None = None
    nl_min_words: int | None = None


SourceUnitsFn = Callable[[DatasetItem], Sequence[str]]


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", help="Model key from src/services/llm.py")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Output root directory. Defaults to automatic paths under "
            "output/<rmc-experiment>/<dataset>/<model>/<granularity>/."
        ),
    )
    parser.add_argument(
        "--mock-recover",
        action="store_true",
        help="Use deterministic local recovery instead of calling an LLM",
    )
    parser.add_argument("--limit", type=int, help="Run at most this many items")
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index after filtering, defaults to 0",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        help="Run only the given task_id. Can be repeated.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip items whose result.json already exists",
    )
    parser.add_argument(
        "--mask-index",
        action="append",
        type=int,
        help=(
            "Run only this original mask index. Can be repeated. "
            "By default all generated masks are run."
        ),
    )
    parser.add_argument(
        "--ast-min-tokens",
        type=int,
        default=DEFAULT_AST_MIN_TOKENS,
        help="Minimum lexical tokens in one Java AST hole, defaults to 8.",
    )
    parser.add_argument(
        "--ast-granularity",
        choices=("control", "statement"),
        default=DEFAULT_AST_GRANULARITY,
        help="Single Java AST granularity to run separately, defaults to control.",
    )
    parser.add_argument(
        "--max-combination-size",
        type=int,
        default=DEFAULT_AST_MAX_COMBINATION_SIZE,
        help="Maximum number of same-granularity Java AST holes masked together, defaults to 3.",
    )
    parser.add_argument(
        "--max-samples-per-stratum",
        type=int,
        default=DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
        help=(
            "Maximum sampled combinations per Java (granularity, size) stratum. "
            "Defaults to no limit."
        ),
    )
    parser.add_argument(
        "--sampling-seed",
        type=int,
        default=DEFAULT_AST_SAMPLING_SEED,
        help="Deterministic Java AST combination sampling seed, defaults to 42.",
    )


def build_config(
    args: argparse.Namespace,
    prompt_mode: str,
    source_label: str,
    text_unit: str,
    line_numbering: str,
    constraints: MaskConstraints = DEFAULT_CONSTRAINTS,
    mask_strategy: str = "sequence",
) -> RunnerConfig:
    if not args.mock_recover and not args.model:
        raise SystemExit("--model is required unless --mock-recover is set")
    if args.ast_min_tokens < 1:
        raise SystemExit("--ast-min-tokens must be >= 1")
    if args.max_combination_size < 1:
        raise SystemExit("--max-combination-size must be >= 1")
    if args.max_samples_per_stratum is not None and args.max_samples_per_stratum < 1:
        raise SystemExit("--max-samples-per-stratum must be >= 1")
    nl_min_words = getattr(args, "nl_min_words", None)
    if nl_min_words is not None and nl_min_words < 1:
        raise SystemExit("--nl-min-words must be >= 1")

    return RunnerConfig(
        dataset_path=args.dataset,
        output_root=args.output,
        model=args.model,
        mock_recover=args.mock_recover,
        prompt_mode=prompt_mode,
        source_label=source_label,
        text_unit=text_unit,
        line_numbering=line_numbering,
        constraints=constraints,
        mask_indices=tuple(args.mask_index) if args.mask_index is not None else None,
        mask_strategy=mask_strategy,
        ast_min_tokens=args.ast_min_tokens,
        ast_granularity=args.ast_granularity,
        max_combination_size=args.max_combination_size,
        max_samples_per_stratum=args.max_samples_per_stratum,
        sampling_seed=args.sampling_seed,
        nl_granularity=getattr(args, "nl_granularity", None),
        nl_min_words=nl_min_words,
    )


def run_dataset(
    items: Iterable[DatasetItem],
    config: RunnerConfig,
    source_units: SourceUnitsFn,
    args: argparse.Namespace,
    summary_extra: Dict[str, Any] | None = None,
) -> Path:
    recover = make_recover(config) if config.mock_recover else None
    selected_items = list(select_items(items, args.task_id))
    if args.start:
        selected_items = selected_items[args.start :]
    if args.limit is not None:
        selected_items = selected_items[: args.limit]

    model_name = "mock" if config.mock_recover else str(config.model)
    dataset_name = dataset_output_name(config.dataset_path)
    result_dir = rmc_output_dir(config, dataset_name, model_name)
    result_dir.mkdir(parents=True, exist_ok=True)
    write_run_config(result_dir, config)

    if not config.mock_recover:
        return run_dataset_batch(
            selected_items=selected_items,
            config=config,
            source_units=source_units,
            args=args,
            output_dir=result_dir,
            model_name=model_name,
            summary_extra=summary_extra,
        )

    rows: List[Dict[str, Any]] = []
    total = len(selected_items)
    dataset_progress = DatasetProgress(total)
    for index, item in enumerate(selected_items, start=1):
        task_dir = result_dir / safe_path_part(item.task_id)
        json_path = task_dir / "result.json"
        html_path = task_dir / "report.html"
        batch_state_path = task_dir / ".batch_state.json"

        if args.skip_existing and json_path.exists():
            write_task_config(task_dir, config, item)
            dataset_progress.skipping(index, item.task_id)
            rows.append(load_summary_row(json_path))
            continue

        task_dir.mkdir(parents=True, exist_ok=True)
        dataset_progress.running(index, item.task_id)
        units = clean_blank_units(list(source_units(item)))
        progress = dataset_progress.bar(index, item.task_id)
        batch_recover = make_batch_recover(config, batch_state_path, progress.update)
        try:
            if config.prompt_mode == "code_mask_json":
                masks = select_indexed_masks(generate_masks(units, config), config.mask_indices)
                recovered_texts = tuple(batch_recover([mask.text for mask in masks])) if masks else ()
                result = build_result_from_recoveries(
                    units=units,
                    masks=masks,
                    recovered_texts=recovered_texts,
                    extract_markdown=False,
                    exact_mask_mode=True,
                )
            elif config.mock_recover:
                result = recursive_masking_complexity(
                    sequence=units,
                    recover=recover,
                    constraints=config.constraints,
                    similarity=sequence_similarity,
                    progress=lambda completed, mask_total: progress.update("recovering", completed, mask_total),
                    warning=print_warning,
                    extract_markdown=config.prompt_mode == "code",
                    mask_indices=config.mask_indices,
                    mask_generator=mask_generator(config),
                    enforce_sequence_bounds=not is_stratified_mask_strategy(config.mask_strategy),
                )
            else:
                result = recursive_masking_complexity_batch(
                    sequence=units,
                    batch_recover=batch_recover,
                    constraints=config.constraints,
                    similarity=sequence_similarity,
                    warning=print_warning,
                    extract_markdown=config.prompt_mode == "code",
                    mask_indices=config.mask_indices,
                    mask_generator=mask_generator(config),
                    enforce_sequence_bounds=not is_stratified_mask_strategy(config.mask_strategy),
                )
        finally:
            progress.finish()
        result = aggregate_result_for_config(result, config)
        data = result_to_dict(
            result=result,
            source_path=item.task_id,
            model_name=model_name,
            constraints=config.constraints,
            source_lines=units,
            line_numbering=config.line_numbering,
        )
        data["dataset_item"] = dataset_item_payload(item, config)
        if is_stratified_mask_strategy(config.mask_strategy):
            data["ast_strata"] = ast_stratum_scores(result)
        task_dir.mkdir(parents=True, exist_ok=True)
        write_task_config(task_dir, config, item)
        write_json_report(data, json_path)
        write_html_report(data, html_path)
        rows.append(summary_row(data))
        write_summary(result_dir, config, rows, summary_extra)
        dataset_progress.wrote(index, str(json_path))

    summary_path = write_summary(result_dir, config, rows, summary_extra)
    print(f"Wrote {summary_path}", flush=True)
    return summary_path


def run_dataset_batch(
    selected_items: Sequence[DatasetItem],
    config: RunnerConfig,
    source_units: SourceUnitsFn,
    args: argparse.Namespace,
    output_dir: Path,
    model_name: str,
    summary_extra: Dict[str, Any] | None = None,
) -> Path:
    rows: List[Dict[str, Any]] = []
    prepared_tasks = []
    masked_texts = []
    total = len(selected_items)
    dataset_progress = DatasetProgress(total)

    for index, item in enumerate(selected_items, start=1):
        task_dir = output_dir / safe_path_part(item.task_id)
        json_path = task_dir / "result.json"
        html_path = task_dir / "report.html"

        if args.skip_existing and json_path.exists():
            write_task_config(task_dir, config, item)
            dataset_progress.skipping(index, item.task_id)
            rows.append(load_summary_row(json_path))
            continue

        units = clean_blank_units(list(source_units(item)))
        masks = generate_masks(units, config)
        if not masks:
            result = ComplexityResult(score=None, profile=(), masks=())
            write_result(
                item=item,
                result=result,
                config=config,
                model_name=model_name,
                units=units,
                task_dir=task_dir,
                json_path=json_path,
                html_path=html_path,
            )
            rows.append(load_summary_row(json_path))
            continue

        masks = select_indexed_masks(
            masks,
            config.mask_indices,
        )
        prepared_tasks.append(
            {
                "index": index,
                "item": item,
                "task_dir": task_dir,
                "json_path": json_path,
                "html_path": html_path,
                "units": units,
                "masks": masks,
                "start": len(masked_texts),
            }
        )
        masked_texts.extend(mask.text for mask in masks)

    print(
        f"Processing dataset batch: {len(masked_texts)} recoveries "
        f"for {len(prepared_tasks)} tasks",
        flush=True,
    )
    progress = dataset_progress.bar(0, "dataset batch")
    batch_recover = make_batch_recover(
        config,
        output_dir / ".batch_state.json",
        progress.update,
    )
    try:
        recovered_texts = tuple(batch_recover(masked_texts)) if masked_texts else ()
    finally:
        progress.finish()
    if len(recovered_texts) != len(masked_texts):
        raise ValueError("Dataset batch returned the wrong number of recoveries")

    for task in prepared_tasks:
        item = task["item"]
        start = task["start"]
        masks = task["masks"]
        task_recovered = recovered_texts[start : start + len(masks)]
        dataset_progress.writing(task["index"], item.task_id)
        result = build_result_from_recoveries(
            units=task["units"],
            masks=masks,
            recovered_texts=task_recovered,
            extract_markdown=config.prompt_mode == "code",
            exact_mask_mode=config.prompt_mode == "code_mask_json",
        )
        result = aggregate_result_for_config(result, config)
        write_result(
            item=item,
            result=result,
            config=config,
            model_name=model_name,
            units=task["units"],
            task_dir=task["task_dir"],
            json_path=task["json_path"],
            html_path=task["html_path"],
        )
        rows.append(load_summary_row(task["json_path"]))

    extra = dict(summary_extra or {})
    extra["batch_mode"] = "dataset"
    extra["batch_recovery_count"] = len(masked_texts)
    summary_path = write_summary(output_dir, config, rows, extra)
    print(f"Wrote {summary_path}", flush=True)
    return summary_path


def build_result_from_recoveries(
    units: Sequence[str],
    masks: Sequence,
    recovered_texts: Sequence[str],
    extract_markdown: bool,
    exact_mask_mode: bool = False,
) -> ComplexityResult:
    profile = []
    scores = []
    total = len(masks)
    for index, (masked, recovered) in enumerate(zip(masks, recovered_texts), start=1):
        if exact_mask_mode:
            item, score = evaluate_exact_mask_recovery(
                lines=units,
                masked=masked,
                recovered=recovered,
                similarity=sequence_similarity,
                task_index=index,
                task_total=total,
                warning=print_warning,
            )
        else:
            item, score = evaluate_scored_recovery(
                lines=units,
                masked=masked,
                recovered=recovered,
                similarity=sequence_similarity,
                task_index=index,
                task_total=total,
                warning=print_warning,
                extract_markdown=extract_markdown,
            )
        profile.append(item)
        scores.append(score)

    return ComplexityResult(
        score=mean(scores) if scores else None,
        profile=tuple(profile),
        masks=tuple(masks),
    )


def write_result(
    item: DatasetItem,
    result: ComplexityResult,
    config: RunnerConfig,
    model_name: str,
    units: Sequence[str],
    task_dir: Path,
    json_path: Path,
    html_path: Path,
) -> None:
    result = aggregate_result_for_config(result, config)
    data = result_to_dict(
        result=result,
        source_path=item.task_id,
        model_name=model_name,
        constraints=config.constraints,
        source_lines=units,
        line_numbering=config.line_numbering,
    )
    data["dataset_item"] = dataset_item_payload(item, config)
    if is_stratified_mask_strategy(config.mask_strategy):
        data["ast_strata"] = ast_stratum_scores(result)
    task_dir.mkdir(parents=True, exist_ok=True)
    write_task_config(task_dir, config, item)
    write_json_report(data, json_path)
    write_html_report(data, html_path)


def dataset_output_name(path: Path) -> str:
    return dataset_name_for_path(path)


def make_recover(config: RunnerConfig):
    if config.mock_recover:
        return lambda masked_text: mock_recover(masked_text, config.prompt_mode)
    raise RuntimeError("Non-mock dataset runs should use make_batch_recover")


def make_batch_recover(
    config: RunnerConfig,
    state_path: Path | None = None,
    progress=None,
):
    if config.mock_recover:
        return lambda masked_texts: [
            mock_recover(masked_text, config.prompt_mode)
            for masked_text in masked_texts
        ]
    return make_llm_batch_recover(
        str(config.model),
        prompt_mode=config.prompt_mode,
        state_path=state_path,
        progress=progress,
    )


def mask_generator(config: RunnerConfig):
    if config.mask_strategy.startswith("natural_language_stratified"):
        return lambda lines, constraints: natural_language_masks(
            lines,
            constraints,
            granularity=str(config.nl_granularity),
            min_words=int(config.nl_min_words or config.ast_min_tokens),
            max_combination_size=config.max_combination_size,
            max_samples_per_stratum=config.max_samples_per_stratum,
            sampling_seed=config.sampling_seed,
        )
    if config.mask_strategy.startswith("java_ast_prefix"):
        return lambda lines, constraints: java_ast_prefixes(
            "\n".join(lines),
            constraints,
            min_tokens=config.ast_min_tokens,
            ast_granularity=config.ast_granularity,
        )
    if config.mask_strategy.startswith("java_fragment_control"):
        return lambda lines, constraints: java_fragment_control_masks(
            "\n".join(lines),
            constraints,
            min_tokens=config.ast_min_tokens,
            max_combination_size=config.max_combination_size,
            max_samples_per_stratum=config.max_samples_per_stratum,
            sampling_seed=config.sampling_seed,
        )
    if config.mask_strategy.startswith("java_ast"):
        return lambda lines, constraints: java_ast_masks(
            "\n".join(lines),
            constraints,
            min_tokens=config.ast_min_tokens,
            max_combination_size=config.max_combination_size,
            max_samples_per_stratum=config.max_samples_per_stratum,
            sampling_seed=config.sampling_seed,
            ast_granularity=config.ast_granularity,
        )
    return None


def generate_masks(units: Sequence[str], config: RunnerConfig):
    if config.mask_strategy.startswith("natural_language_stratified"):
        return natural_language_masks(
            units,
            config.constraints,
            granularity=str(config.nl_granularity),
            min_words=int(config.nl_min_words or config.ast_min_tokens),
            max_combination_size=config.max_combination_size,
            max_samples_per_stratum=config.max_samples_per_stratum,
            sampling_seed=config.sampling_seed,
        )
    if config.mask_strategy.startswith("java_ast_prefix"):
        return java_ast_prefixes(
            "\n".join(units),
            config.constraints,
            min_tokens=config.ast_min_tokens,
            ast_granularity=config.ast_granularity,
        )
    if config.mask_strategy.startswith("java_fragment_control"):
        return java_fragment_control_masks(
            "\n".join(units),
            config.constraints,
            min_tokens=config.ast_min_tokens,
            max_combination_size=config.max_combination_size,
            max_samples_per_stratum=config.max_samples_per_stratum,
            sampling_seed=config.sampling_seed,
        )
    if config.mask_strategy.startswith("java_ast"):
        return java_ast_masks(
            "\n".join(units),
            config.constraints,
            min_tokens=config.ast_min_tokens,
            max_combination_size=config.max_combination_size,
            max_samples_per_stratum=config.max_samples_per_stratum,
            sampling_seed=config.sampling_seed,
            ast_granularity=config.ast_granularity,
        )
    if len(units) < config.constraints.nmin * config.constraints.lmin:
        return ()
    if len(units) > config.constraints.nmax * config.constraints.lmax:
        return ()
    return delta_mask(units, config.constraints)


def mock_recover(masked_text: str, prompt_mode: str) -> str:
    if prompt_mode == "code":
        return f"```\n{masked_text.replace('<mask>', '# mock recovery')}\n```"
    if prompt_mode == "code_mask_json":
        return json.dumps(
            {
                f"mask_{index}": "# mock recovery"
                for index in range(1, masked_text.count("<mask>") + 1)
            }
        )
    if prompt_mode == "code_prefix":
        return f"```\n{masked_text}\n```"
    if prompt_mode == "natural_language":
        return masked_text.replace("<mask>", "[mock recovery]")
    raise ValueError(f"Unknown prompt mode: {prompt_mode}")


def aggregate_result_for_config(result: ComplexityResult, config: RunnerConfig) -> ComplexityResult:
    if not is_stratified_mask_strategy(config.mask_strategy) or not result.profile:
        return result
    if config.prompt_mode == "code_mask_json":
        fallback_score = fallback_selected_segments_score(result)
        return replace(result, score=fallback_score)
    strata = ast_stratum_scores(result)
    return replace(result, score=mean([item["score"] for item in strata]))


def fallback_selected_segments_score(result: ComplexityResult) -> float | None:
    groups: Dict[int, list[float]] = defaultdict(list)
    for recovery in result.profile:
        groups[int(recovery.masked.selected_segments)].append(float(recovery.similarity))
    for selected_segments in (3, 2, 1):
        scores = groups.get(selected_segments)
        if scores:
            return mean(scores)
    return None


def is_stratified_mask_strategy(mask_strategy: str) -> bool:
    return (
        mask_strategy.startswith("java_ast")
        or mask_strategy.startswith("java_fragment_control")
        or mask_strategy.startswith("natural_language_stratified")
    )


def rmc_output_dir(config: RunnerConfig, dataset_name: str, model_name: str) -> Path:
    if config.prompt_mode == "code_mask_json":
        return output_dir(config.output_root, rmc_experiment_name(config), dataset_name, model_name)
    if config.mask_strategy.startswith("java_ast_prefix"):
        return output_dir(config.output_root, "rmc_prefix", dataset_name, model_name)
    if config.mask_strategy.startswith("java_ast") or config.mask_strategy.startswith("java_fragment_control"):
        return output_dir(config.output_root, "rmc_masked", dataset_name, model_name)
    if config.mask_strategy.startswith("natural_language_stratified"):
        return output_dir(
            config.output_root,
            "rmc_natural_language",
            dataset_name,
            model_name,
        )
    return output_dir(config.output_root, "rmc_sequence", dataset_name, model_name)


def sample_budget_label(max_samples_per_stratum: int | None) -> str:
    return "all" if max_samples_per_stratum is None else str(max_samples_per_stratum)


def ast_stratum_scores(result: ComplexityResult) -> list[Dict[str, Any]]:
    groups: Dict[tuple[str, int], list[float]] = defaultdict(list)
    populations: Dict[tuple[str, int], int] = {}
    for recovery in result.profile:
        mask = recovery.masked
        key = (str(mask.ast_granularity), int(mask.selected_segments))
        groups[key].append(float(recovery.similarity))
        populations[key] = max(
            populations.get(key, 0),
            int(mask.stratum_total) if mask.stratum_total is not None else len(groups[key]),
        )
    return [
        {
            "ast_granularity": granularity,
            "selected_segments": selected_segments,
            "sample_count": len(scores),
            "population_size": populations[(granularity, selected_segments)],
            "score": mean(scores),
        }
        for (granularity, selected_segments), scores in sorted(groups.items())
    ]


def select_items(
    items: Iterable[DatasetItem],
    task_ids: List[str] | None,
) -> Iterable[DatasetItem]:
    if not task_ids:
        return items
    selected = set(task_ids)
    return (item for item in items if item.task_id in selected)


def dataset_item_payload(item: DatasetItem, config: RunnerConfig) -> Dict[str, Any]:
    payload = {
        "task_id": item.task_id,
        "readability_score": item.readability_score,
        "readability_prompt": item.readability_prompt,
        "source": config.source_label,
        "text_unit": config.text_unit,
    }
    payload.update(item.metadata)
    return payload


def print_warning(message: str) -> None:
    print(message, flush=True)


def summary_row(data: Dict[str, Any]) -> Dict[str, Any]:
    item = data["dataset_item"]
    summary = data["summary"]
    mask_counts = mask_count_summary(data.get("masks", []))
    return {
        "task_id": item["task_id"],
        "readability_score": item.get("readability_score"),
        "readability_prompt": item.get("readability_prompt"),
        "rmc_score": summary["score"],
        "mask_count": summary["mask_count"],
        "profile_count": summary["profile_count"],
        "source_line_count": len(data["source_lines"]),
        **mask_counts,
    }


def load_summary_row(path: Path) -> Dict[str, Any]:
    return summary_row(json.loads(path.read_text(encoding="utf-8")))


def mask_count_summary(masks: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_selected_segments: Dict[str, int] = defaultdict(int)
    by_ast_granularity: Dict[str, int] = defaultdict(int)
    by_node_type: Dict[str, int] = defaultdict(int)
    by_stratum: Dict[tuple[str, int], Dict[str, Any]] = {}
    for mask in masks:
        selected_segments = int(mask.get("selected_segments") or mask.get("granularity") or 0)
        granularity = str(mask.get("ast_granularity") or "unknown")
        by_selected_segments[str(selected_segments)] += 1
        by_ast_granularity[granularity] += 1
        node_type = mask.get("node_type")
        if node_type:
            by_node_type[str(node_type)] += 1
        key = (granularity, selected_segments)
        stratum = by_stratum.setdefault(
            key,
            {
                "ast_granularity": granularity,
                "selected_segments": selected_segments,
                "mask_count": 0,
                "population_size": 0,
            },
        )
        stratum["mask_count"] += 1
        stratum["population_size"] = max(
            int(stratum["population_size"]),
            int(mask.get("stratum_total") or 0),
            int(stratum["mask_count"]),
        )
    return {
        "mask_count_by_selected_segments": dict(sorted(by_selected_segments.items())),
        "mask_count_by_ast_granularity": dict(sorted(by_ast_granularity.items())),
        "mask_count_by_node_type": dict(sorted(by_node_type.items())),
        "mask_count_by_stratum": [
            by_stratum[key]
            for key in sorted(by_stratum, key=lambda item: (item[0], item[1]))
        ],
    }


def aggregate_mask_count_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    selected_totals: Dict[str, int] = defaultdict(int)
    granularity_totals: Dict[str, int] = defaultdict(int)
    node_type_totals: Dict[str, int] = defaultdict(int)
    stratum_totals: Dict[tuple[str, int], Dict[str, Any]] = {}
    for row in rows:
        for key, value in row.get("mask_count_by_selected_segments", {}).items():
            selected_totals[str(key)] += int(value)
        for key, value in row.get("mask_count_by_ast_granularity", {}).items():
            granularity_totals[str(key)] += int(value)
        for key, value in row.get("mask_count_by_node_type", {}).items():
            node_type_totals[str(key)] += int(value)
        for item in row.get("mask_count_by_stratum", []):
            key = (str(item["ast_granularity"]), int(item["selected_segments"]))
            target = stratum_totals.setdefault(
                key,
                {
                    "ast_granularity": key[0],
                    "selected_segments": key[1],
                    "mask_count": 0,
                    "population_size": 0,
                },
            )
            target["mask_count"] += int(item["mask_count"])
            target["population_size"] += int(item["population_size"])
    return {
        "total_mask_count": sum(int(row.get("mask_count") or 0) for row in rows),
        "total_profile_count": sum(int(row.get("profile_count") or 0) for row in rows),
        "mask_count_by_selected_segments": dict(sorted(selected_totals.items())),
        "mask_count_by_ast_granularity": dict(sorted(granularity_totals.items())),
        "mask_count_by_node_type": dict(sorted(node_type_totals.items())),
        "mask_count_by_stratum": [
            stratum_totals[key]
            for key in sorted(stratum_totals, key=lambda item: (item[0], item[1]))
        ],
    }


def write_run_config(output_dir: Path, config: RunnerConfig) -> Path:
    path = output_dir / "config.json"
    path.write_text(
        json.dumps(run_config_payload(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def write_task_config(task_dir: Path, config: RunnerConfig, item: DatasetItem) -> Path:
    task_dir.mkdir(parents=True, exist_ok=True)
    payload = run_config_payload(config)
    payload["task"] = dataset_item_payload(item, config)
    path = task_dir / "config.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run_config_payload(config: RunnerConfig) -> Dict[str, Any]:
    model_name = "mock" if config.mock_recover else config.model
    return {
        "method": "rmc_em" if config.prompt_mode == "code_mask_json" else "rmc",
        "experiment": rmc_experiment_name(config),
        "dataset": str(config.dataset_path),
        "dataset_key": dataset_output_name(config.dataset_path),
        "model": model_name,
        "mock_recover": config.mock_recover,
        "similarity": "sequence",
        "prompt_mode": config.prompt_mode,
        "source": config.source_label,
        "text_unit": config.text_unit,
        "constraints": {
            "nmin": config.constraints.nmin,
            "nmax": config.constraints.nmax,
            "lmin": config.constraints.lmin,
            "lmax": config.constraints.lmax,
        },
        "mask_indices": list(config.mask_indices) if config.mask_indices is not None else None,
        "mask_strategy": config.mask_strategy,
        "ast_min_tokens": (
            config.ast_min_tokens
            if config.mask_strategy.startswith("java_ast")
            or config.mask_strategy.startswith("java_fragment_control")
            else None
        ),
        "ast_granularity": (
            config.ast_granularity
            if config.mask_strategy.startswith("java_ast")
            or config.mask_strategy.startswith("java_fragment_control")
            else None
        ),
        "nl_granularity": (
            config.nl_granularity if config.mask_strategy.startswith("natural_language_stratified") else None
        ),
        "nl_min_words": (
            config.nl_min_words if config.mask_strategy.startswith("natural_language_stratified") else None
        ),
        "max_combination_size": (
            config.max_combination_size
            if is_stratified_mask_strategy(config.mask_strategy)
            else None
        ),
        "max_samples_per_stratum": (
            config.max_samples_per_stratum
            if is_stratified_mask_strategy(config.mask_strategy)
            else None
        ),
        "sampling_mode": (
            "all"
            if is_stratified_mask_strategy(config.mask_strategy)
            and config.max_samples_per_stratum is None
            else "sampled"
            if is_stratified_mask_strategy(config.mask_strategy)
            else None
        ),
        "sampling_seed": (
            config.sampling_seed
            if is_stratified_mask_strategy(config.mask_strategy)
            and config.max_samples_per_stratum is not None
            else None
        ),
        "ast_granularities": (
            [config.ast_granularity]
            if config.mask_strategy.startswith("java_ast")
            or config.mask_strategy.startswith("java_fragment_control")
            else None
        ),
        "ast_combination_policy": (
            {
                "same_granularity_only": True,
                "non_overlapping_only": True,
                "maximum_selected_nodes": config.max_combination_size,
                "max_samples_per_stratum": config.max_samples_per_stratum,
                "sampling_seed": (
                    config.sampling_seed
                    if config.max_samples_per_stratum is not None
                    else None
                ),
            }
            if config.mask_strategy == "java_ast_stratified_v7"
            or config.mask_strategy == "java_fragment_control_v1"
            else None
        ),
        "score_aggregation": score_aggregation_name(config),
        "line_numbering": config.line_numbering,
    }


def rmc_experiment_name(config: RunnerConfig) -> str:
    if config.prompt_mode == "code_mask_json":
        return "rmc_em"
    if config.mask_strategy.startswith("java_ast_prefix"):
        return "rmc_prefix"
    if config.mask_strategy.startswith("java_ast") or config.mask_strategy.startswith("java_fragment_control"):
        return "rmc_masked"
    if config.mask_strategy.startswith("natural_language_stratified"):
        return "rmc_natural_language"
    return "rmc_sequence"


def score_aggregation_name(config: RunnerConfig) -> str:
    if config.prompt_mode == "code_mask_json":
        return "fallback_mean_over_exact_mask_recovery_strata"
    if config.mask_strategy.startswith("java_ast_prefix"):
        return "equal_mean_over_prefix_positions"
    if config.mask_strategy.startswith("java_ast") or config.mask_strategy.startswith("java_fragment_control"):
        return "equal_mean_over_selected_segments_strata_within_ast_granularity"
    if config.mask_strategy.startswith("natural_language_stratified"):
        return "equal_mean_over_selected_segments_strata_within_natural_granularity"
    return "mean_over_masks"


def write_summary(
    output_dir: Path,
    config: RunnerConfig,
    rows: List[Dict[str, Any]],
    summary_extra: Dict[str, Any] | None = None,
) -> Path:
    path = output_dir / "summary.json"
    payload = {
        **run_config_payload(config),
        "count": len(rows),
        **aggregate_mask_count_summary(rows),
        "results": rows,
    }
    if summary_extra:
        payload.update(summary_extra)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
