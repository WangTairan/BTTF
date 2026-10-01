import json
import re
from pathlib import Path
from typing import Callable, Sequence

from src.services.llm import batch_chat_prompts_with_metadata, chat_with_metadata


STRUCTURED_RETRY_LIMIT = 2
LLM_READABILITY_PROMPT_TEMPLATE = """You are a software engineer evaluating code readability.

Evaluate the following code on a scale from 0 (unreadable) to 20 (highly readable),
explicitly using these criteria:

1. Code Structure - logical organization vs tangled code
2. Nesting - flat vs deeply nested
3. Clarity of intent - clear purpose vs ambiguous
4. Code length - concise vs unnecessarily long
5. Action granularity - one action per line vs multiple
6. Reading flow - natural vs disorganized

Return ONLY JSON:
{{
  "score": "0-20",
  "reasoning": "concise explanation (max 200 words)"
}}

Code:
```code
{code}
```
"""


def llm_prompt_engineering_score(code: str, model_name: str = "dsv4-pro") -> dict:
    prompt = build_llm_readability_prompt(code)
    last_error = None

    for _ in range(STRUCTURED_RETRY_LIMIT):
        response_record = chat_with_metadata(model_name, prompt)
        response = str(response_record["content"])
        try:
            result = validate_llm_readability_payload(extract_json_object(response))
            result["raw_response"] = response
            result["response_metadata"] = {
                key: value
                for key, value in response_record.items()
                if key not in {"content", "api_response"}
            }
            result["api_response"] = response_record["api_response"]
            return result
        except Exception as exc:
            last_error = exc

    raise ValueError(f"LLM readability response was not valid JSON: {last_error}")


def llm_prompt_engineering_scores(
    codes: Sequence[str],
    model_name: str = "dsv4-pro",
    *,
    state_path: Path | str | None = None,
    progress: Callable[[str, int, int], None] | None = None,
) -> list[dict]:
    prompts = [build_llm_readability_prompt(code) for code in codes]
    response_records = batch_chat_prompts_with_metadata(
        model_name,
        prompts,
        state_path=state_path,
        metadata={"method": "llm_prompt", "model": model_name},
        progress=progress,
        retry_failed_individually=False,
    )
    results = []
    for code, response_record in zip(codes, response_records):
        response = str(response_record["content"])
        try:
            result = validate_llm_readability_payload(extract_json_object(response))
            result["raw_response"] = response
            result["response_metadata"] = {
                key: value
                for key, value in response_record.items()
                if key not in {"content", "api_response"}
            }
            result["api_response"] = response_record["api_response"]
            results.append(result)
        except Exception:
            results.append(llm_prompt_engineering_score(code, model_name=model_name))
    return results


def build_llm_readability_prompt(code: str) -> str:
    return LLM_READABILITY_PROMPT_TEMPLATE.format(code=code)


def validate_llm_readability_payload(payload: dict) -> dict:
    if "score" not in payload:
        raise ValueError("Missing score")
    if "reasoning" not in payload:
        raise ValueError("Missing reasoning")

    score = float(str(payload["score"]).strip())
    if score < 0 or score > 20:
        raise ValueError(f"score must be in [0, 20], got {score}")

    reasoning = str(payload["reasoning"]).strip()
    if not reasoning:
        raise ValueError("reasoning must be non-empty")

    return {"score": score, "reasoning": reasoning}


def extract_json_object(text: str) -> dict:
    cleaned = strip_markdown_fence(text).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        payload = json.loads(find_json_object(cleaned))
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return payload


def strip_markdown_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else text


def find_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object found")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
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

    raise ValueError("Unterminated JSON object")
