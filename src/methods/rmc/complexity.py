import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple, Union

from .masking import delta_mask
from .prompts import build_recovery_prompt
from .similarity import mean, sequence_similarity
from .types import ComplexityResult, MaskConstraints, MaskSpan, RecoveryResult


SimilarityFn = Callable[[str, str], float]
AggregateFn = Callable[[Sequence[float]], float]
RecoverFn = Callable[[str], str]
BatchRecoverFn = Callable[[Sequence[str]], Sequence[str]]
BatchProgressFn = Callable[[str, int, int], None]
ProgressFn = Callable[[int, int], None]
WarningFn = Callable[[str], None]
MaskGeneratorFn = Callable[[Sequence[str], MaskConstraints], Sequence]


@dataclass(frozen=True)
class ExtractedText:
    text: str
    failed: bool


def recursive_masking_complexity(
    sequence: Union[str, Sequence[str]],
    recover: RecoverFn,
    constraints: MaskConstraints,
    similarity: SimilarityFn = sequence_similarity,
    aggregate: AggregateFn = mean,
    progress: Optional[ProgressFn] = None,
    warning: Optional[WarningFn] = None,
    extract_markdown: bool = True,
    mask_indices: Optional[Sequence[int]] = None,
    mask_generator: Optional[MaskGeneratorFn] = None,
    enforce_sequence_bounds: bool = True,
) -> ComplexityResult:
    constraints.validate()
    lines = tuple(sequence.splitlines()) if isinstance(sequence, str) else tuple(sequence)

    if enforce_sequence_bounds:
        if len(lines) < constraints.nmin * constraints.lmin:
            return ComplexityResult(score=None, profile=(), masks=())
        if len(lines) > constraints.nmax * constraints.lmax:
            return ComplexityResult(score=None, profile=(), masks=())

    generated = (
        tuple(mask_generator(lines, constraints))
        if mask_generator is not None
        else delta_mask(lines, constraints)
    )
    masks = select_indexed_masks(generated, mask_indices)
    if not masks:
        return ComplexityResult(score=None, profile=(), masks=())

    profile = []
    scores = []
    total = len(masks)
    for index, masked in enumerate(masks, start=1):
        if progress is not None:
            progress(index, total)
        recovered = recover(masked.text)
        item, score = evaluate_scored_recovery(
            lines=lines,
            masked=masked,
            recovered=recovered,
            similarity=similarity,
            task_index=index,
            task_total=total,
            warning=warning,
            extract_markdown=extract_markdown,
        )
        profile.append(item)
        scores.append(score)

    return ComplexityResult(
        score=aggregate(scores),
        profile=tuple(profile),
        masks=masks,
    )


def recursive_masking_complexity_batch(
    sequence: Union[str, Sequence[str]],
    batch_recover: BatchRecoverFn,
    constraints: MaskConstraints,
    similarity: SimilarityFn = sequence_similarity,
    aggregate: AggregateFn = mean,
    warning: Optional[WarningFn] = None,
    extract_markdown: bool = True,
    mask_indices: Optional[Sequence[int]] = None,
    mask_generator: Optional[MaskGeneratorFn] = None,
    enforce_sequence_bounds: bool = True,
) -> ComplexityResult:
    constraints.validate()
    lines = tuple(sequence.splitlines()) if isinstance(sequence, str) else tuple(sequence)

    if enforce_sequence_bounds:
        if len(lines) < constraints.nmin * constraints.lmin:
            return ComplexityResult(score=None, profile=(), masks=())
        if len(lines) > constraints.nmax * constraints.lmax:
            return ComplexityResult(score=None, profile=(), masks=())

    generated = (
        tuple(mask_generator(lines, constraints))
        if mask_generator is not None
        else delta_mask(lines, constraints)
    )
    masks = select_indexed_masks(generated, mask_indices)
    if not masks:
        return ComplexityResult(score=None, profile=(), masks=())

    profile = []
    scores = []
    recovered_texts = tuple(batch_recover([masked.text for masked in masks]))

    if len(recovered_texts) != len(masks):
        raise ValueError("batch_recover must return one recovery for each masked sequence")

    total = len(masks)
    for index, (masked, recovered) in enumerate(zip(masks, recovered_texts), start=1):
        item, score = evaluate_scored_recovery(
            lines=lines,
            masked=masked,
            recovered=recovered,
            similarity=similarity,
            task_index=index,
            task_total=total,
            warning=warning,
            extract_markdown=extract_markdown,
        )
        profile.append(item)
        scores.append(score)

    return ComplexityResult(
        score=aggregate(scores),
        profile=tuple(profile),
        masks=masks,
    )


def select_indexed_masks(
    masks: Sequence,
    mask_indices: Optional[Sequence[int]],
) -> Tuple:
    indexed = tuple(replace(mask, index=index) for index, mask in enumerate(masks))
    if mask_indices is None:
        return indexed

    selected = set(mask_indices)
    unknown = sorted(selected - set(range(len(indexed))))
    if unknown:
        raise ValueError(f"Unknown mask indices for this input: {unknown}")
    return tuple(mask for mask in indexed if mask.index in selected)


def sequential_batch_recover(
    recover: RecoverFn,
    progress: Optional[ProgressFn] = None,
) -> BatchRecoverFn:
    def batch_recover(masked_texts: Sequence[str]) -> Sequence[str]:
        total = len(masked_texts)
        recovered = []
        for index, masked_text in enumerate(masked_texts, start=1):
            if progress is not None:
                progress(index, total)
            recovered.append(recover(masked_text))
        return recovered

    return batch_recover


def evaluate_scored_recovery(
    lines: Sequence[str],
    masked,
    recovered: str,
    similarity: SimilarityFn,
    task_index: int,
    task_total: int,
    warning: Optional[WarningFn],
    extract_markdown: bool,
) -> Tuple[RecoveryResult, float]:
    extracted = (
        extract_text_from_markdown(recovered)
        if extract_markdown
        else ExtractedText(text=recovered.strip(), failed=False)
    )
    cleaned_recovered = clean_blank_lines(extracted.text)
    expected = "\n".join(lines).strip()
    completion = cleaned_recovered
    score = similarity(expected, completion)
    return (
        RecoveryResult(
            masked=masked,
            recovered=cleaned_recovered,
            expected=expected,
            completion=completion,
            completion_line_indexes=(),
            alignment_failed=False,
            extraction_failed=extracted.failed,
            recovery_attempts=1,
            similarity=score,
        ),
        score,
    )


def evaluate_exact_mask_recovery(
    lines: Sequence[str],
    masked,
    recovered: str,
    similarity: SimilarityFn,
    task_index: int,
    task_total: int,
    warning: Optional[WarningFn],
) -> Tuple[RecoveryResult, float]:
    expected_parts = expected_mask_parts(lines, masked)
    parsed, failed = extract_mask_json(recovered)
    mask_count_mismatch = len(parsed) != len(expected_parts)
    recovered_parts = parsed[: len(expected_parts)]
    if len(recovered_parts) < len(expected_parts):
        recovered_parts.extend([""] * (len(expected_parts) - len(recovered_parts)))
    scores = [
        similarity(expected, completion)
        for expected, completion in zip(expected_parts, recovered_parts)
    ]
    score = mean(scores) if scores else 0.0
    if mask_count_mismatch:
        denominator = max(len(expected_parts), len(parsed), 1)
        score *= min(len(expected_parts), len(parsed)) / denominator
    if failed and warning is not None:
        warning(f"Mask JSON extraction failed for recovery {task_index}/{task_total}")
    elif mask_count_mismatch and warning is not None:
        warning(
            "Mask JSON count mismatch for recovery "
            f"{task_index}/{task_total}: expected {len(expected_parts)}, got {len(parsed)}"
        )
    return (
        RecoveryResult(
            masked=masked,
            recovered=recovered.strip(),
            expected="\n<mask>\n".join(expected_parts),
            completion="\n<mask>\n".join(recovered_parts),
            completion_line_indexes=(),
            alignment_failed=False,
            extraction_failed=failed,
            recovery_attempts=1,
            similarity=score,
            expected_mask_count=len(expected_parts),
            recovered_mask_count=len(parsed),
            mask_count_mismatch=mask_count_mismatch,
        ),
        score,
    )


def extract_mask_json(text: str) -> tuple[list[str], bool]:
    cleaned = text.strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            payload = json.loads(find_json_object(cleaned))
        except Exception:
            return [], True
    if not isinstance(payload, dict):
        return [], True
    keyed = extract_keyed_masks(payload)
    if keyed is not None:
        return keyed, False
    if not isinstance(payload.get("masks"), list):
        return [], True
    return [str(item).strip() for item in payload["masks"]], False


def extract_keyed_masks(payload: dict) -> list[str] | None:
    indexes = []
    for key in payload:
        if not isinstance(key, str) or not key.startswith("mask_"):
            continue
        suffix = key[len("mask_"):]
        if suffix.isdigit() and int(suffix) >= 1:
            indexes.append(int(suffix))
    if not indexes:
        return None
    ordered = sorted(set(indexes))
    if ordered != list(range(1, max(ordered) + 1)):
        return None
    return [str(payload[f"mask_{index}"]).strip() for index in ordered]


def find_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found")
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError("JSON object was not closed")


def expected_mask_parts(lines: Sequence[str], masked) -> list[str]:
    source = "\n".join(lines)
    if getattr(masked, "char_spans", None):
        return [
            source[start:end].strip()
            for start, end in masked.char_spans
        ]
    return [
        "\n".join(lines[span.start : span.end]).strip()
        for span in masked.spans
    ]


def make_llm_recover(model_name: str, prompt_mode: str = "code") -> RecoverFn:
    from src.services.llm import chat

    def recover(masked_text: str) -> str:
        return chat(model_name, build_recovery_prompt(masked_text, mode=prompt_mode))

    return recover


def make_llm_batch_recover(
    model_name: str,
    prompt_mode: str = "code",
    state_path: Path | str | None = None,
    progress: Optional[BatchProgressFn] = None,
) -> BatchRecoverFn:
    from src.services.llm import batch_chat_prompts

    def batch_recover(masked_texts: Sequence[str]) -> Sequence[str]:
        prompts = [
            build_recovery_prompt(masked_text, mode=prompt_mode)
            for masked_text in masked_texts
        ]
        return batch_chat_prompts(
            model_name,
            prompts,
            state_path=state_path,
            progress=progress,
        )

    return batch_recover


def extract_text_from_markdown(text: str) -> ExtractedText:
    match = re.search(r"```[^\n`]*\n?(.*?)```", text, flags=re.DOTALL)
    if match is None:
        return ExtractedText(text=text.strip(), failed=True)
    return ExtractedText(text=match.group(1).strip(), failed=False)


def clean_blank_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if line.strip())


def masked_span_text(lines: Sequence[str], spans: Sequence[MaskSpan]) -> str:
    parts = []
    for span in spans:
        parts.extend(lines[span.start : span.end])
    return "\n".join(parts).strip()
