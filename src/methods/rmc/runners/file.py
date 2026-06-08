import argparse
import json
from pathlib import Path

from src.methods.rmc import (
    DEFAULT_AST_GRANULARITY,
    DEFAULT_AST_MAX_COMBINATION_SIZE,
    DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
    DEFAULT_AST_MIN_TOKENS,
    DEFAULT_AST_SAMPLING_SEED,
    MaskConstraints,
    cosine_similarity,
    edit_similarity,
    exact_match_similarity,
    rouge_l_similarity,
    token_jaccard_similarity,
    token_cosine_similarity,
    bleu_similarity,
    java_ast_masks,
    make_llm_recover,
    recursive_masking_complexity,
    sequence_similarity,
)
from src.methods.rmc.report import result_to_dict, write_html_report, write_json_report
from src.methods.rmc.text_units import clean_blank_units, split_sentences
from src.experiments.paths import output_dir
from src.methods.rmc.runners.dataset import mock_recover


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute Recursive Masking Complexity.")
    parser.add_argument("path", type=Path, help="File to analyze")
    parser.add_argument("--model", help="Model key from src/services/llm.py")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Output root directory. Defaults to automatic paths under "
            "output/<rmc-experiment>/<file>/<model>/<granularity>/."
        ),
    )
    parser.add_argument("--nmin", type=int, default=2)
    parser.add_argument("--nmax", type=int, default=8)
    parser.add_argument("--lmin", type=int, default=2)
    parser.add_argument("--lmax", type=int, default=20)
    parser.add_argument("--ast-min-tokens", type=int, default=DEFAULT_AST_MIN_TOKENS)
    parser.add_argument(
        "--ast-granularity",
        choices=("control", "statement"),
        default=DEFAULT_AST_GRANULARITY,
    )
    parser.add_argument(
        "--max-combination-size",
        type=int,
        default=DEFAULT_AST_MAX_COMBINATION_SIZE,
    )
    parser.add_argument(
        "--max-samples-per-stratum",
        type=int,
        default=DEFAULT_AST_MAX_SAMPLES_PER_STRATUM,
        help="Maximum sampled combinations per AST stratum. Defaults to no limit.",
    )
    parser.add_argument("--sampling-seed", type=int, default=DEFAULT_AST_SAMPLING_SEED)
    parser.add_argument(
        "--similarity",
        choices=(
            "sequence",
            "exact_match",
            "edit",
            "token_jaccard",
            "token_cosine",
            "bleu",
            "rouge_l",
            "cosine",
        ),
        default="sequence",
        help="Similarity metric, defaults to sequence",
    )
    parser.add_argument(
        "--mode",
        choices=("code", "natural_language"),
        default="code",
        help="Recovery prompt mode, defaults to code.",
    )
    parser.add_argument(
        "--mock-recover",
        action="store_true",
        help="Use deterministic local recovery for examples and smoke tests",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.mock_recover and not args.model:
        raise SystemExit("--model is required unless --mock-recover is set")
    if (
        args.ast_min_tokens < 1
        or args.max_combination_size < 1
        or (
            args.max_samples_per_stratum is not None
            and args.max_samples_per_stratum < 1
        )
    ):
        raise SystemExit("AST mask sizing and sampling arguments must be >= 1")

    constraints = MaskConstraints(
        nmin=args.nmin,
        nmax=args.nmax,
        lmin=args.lmin,
        lmax=args.lmax,
    )
    recover = (
        (lambda masked_text: mock_recover(masked_text, args.mode))
        if args.mock_recover
        else make_llm_recover(args.model, prompt_mode=args.mode)
    )
    model_name = "mock" if args.mock_recover else args.model
    result_dir = (
        output_dir(args.output, "rmc_masked", args.path.stem, model_name)
        if args.mode == "code"
        else output_dir(args.output, "rmc_natural_language", args.path.stem, model_name)
    )
    result_dir.mkdir(parents=True, exist_ok=True)

    source_text = args.path.read_text(encoding="utf-8")
    source_units = split_sentences(source_text) if args.mode == "natural_language" else source_text.splitlines()
    source_lines = clean_blank_units(source_units)
    result = recursive_masking_complexity(
        sequence=source_lines,
        recover=recover,
        constraints=constraints,
        similarity=get_similarity(args.similarity),
        progress=print_progress,
        warning=print_warning,
        extract_markdown=args.mode == "code",
        mask_generator=(
            (
                lambda lines, active_constraints: java_ast_masks(
                    "\n".join(lines),
                    active_constraints,
                    min_tokens=args.ast_min_tokens,
                    max_combination_size=args.max_combination_size,
                    max_samples_per_stratum=args.max_samples_per_stratum,
                    sampling_seed=args.sampling_seed,
                    ast_granularity=args.ast_granularity,
                )
            )
            if args.mode == "code"
            else None
        ),
        enforce_sequence_bounds=args.mode != "code",
    )
    data = result_to_dict(
        result=result,
        source_path=str(args.path),
        model_name=model_name,
        constraints=constraints,
        source_lines=source_lines,
        line_numbering=get_line_numbering(args.mode),
    )

    json_path = result_dir / "result.json"
    html_path = result_dir / "report.html"
    config_path = result_dir / "config.json"
    config_path.write_text(
        json.dumps(file_config_payload(args, constraints, model_name), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_json_report(data, json_path)
    write_html_report(data, html_path)
    print(f"Wrote {config_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}")


def file_config_payload(args: argparse.Namespace, constraints: MaskConstraints, model_name: str) -> dict:
    experiment = "rmc_masked" if args.mode == "code" else "rmc_natural_language"
    return {
        "method": "rmc",
        "experiment": experiment,
        "dataset": str(args.path),
        "dataset_key": args.path.stem,
        "model": model_name,
        "mock_recover": args.mock_recover,
        "similarity": args.similarity,
        "prompt_mode": args.mode,
        "source": args.path.stem,
        "text_unit": "sentence" if args.mode == "natural_language" else "code_line",
        "constraints": {
            "nmin": constraints.nmin,
            "nmax": constraints.nmax,
            "lmin": constraints.lmin,
            "lmax": constraints.lmax,
        },
        "mask_strategy": "java_ast_stratified_v7" if args.mode == "code" else "sequence",
        "ast_min_tokens": args.ast_min_tokens if args.mode == "code" else None,
        "ast_granularity": args.ast_granularity if args.mode == "code" else None,
        "max_combination_size": args.max_combination_size if args.mode == "code" else None,
        "max_samples_per_stratum": args.max_samples_per_stratum if args.mode == "code" else None,
        "sampling_mode": (
            "all"
            if args.mode == "code" and args.max_samples_per_stratum is None
            else "sampled"
            if args.mode == "code"
            else None
        ),
        "sampling_seed": (
            args.sampling_seed
            if args.mode == "code" and args.max_samples_per_stratum is not None
            else None
        ),
        "ast_granularities": [args.ast_granularity] if args.mode == "code" else None,
        "ast_combination_policy": (
            {
                "same_granularity_only": True,
                "non_overlapping_only": True,
                "maximum_selected_nodes": args.max_combination_size,
                "max_samples_per_stratum": args.max_samples_per_stratum,
                "sampling_seed": (
                    args.sampling_seed
                    if args.max_samples_per_stratum is not None
                    else None
                ),
            }
            if args.mode == "code"
            else None
        ),
        "score_aggregation": (
            "equal_mean_over_selected_segments_strata_within_ast_granularity"
            if args.mode == "code"
            else "mean_over_masks"
        ),
        "line_numbering": get_line_numbering(args.mode),
    }


def get_similarity(name: str):
    if name == "sequence":
        return sequence_similarity
    if name == "exact_match":
        return exact_match_similarity
    if name == "edit":
        return edit_similarity
    if name == "token_jaccard":
        return token_jaccard_similarity
    if name == "token_cosine":
        return token_cosine_similarity
    if name == "bleu":
        return bleu_similarity
    if name == "rouge_l":
        return rouge_l_similarity
    if name == "cosine":
        return cosine_similarity
    raise ValueError(f"Unknown similarity metric: {name}")


def get_line_numbering(mode: str) -> str:
    if mode == "natural_language":
        return "cleaned_sentence_1_based"
    return "cleaned_non_blank_1_based"


def print_progress(index: int, total: int) -> None:
    print(f"Recovering task {index}/{total}", flush=True)


def print_warning(message: str) -> None:
    print(message, flush=True)


if __name__ == "__main__":
    main()
