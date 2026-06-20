CODE_MASK_JSON_PROMPT_TEMPLATE = """Fill only the <mask> regions in the code below.

- Return ONLY valid JSON.
- Use numbered keys for the masked regions: "mask_1", "mask_2", ...
- Include exactly one key for each <mask> region in the code.
- If there is exactly one <mask>, return exactly: {{"mask_1": "complete replacement code"}}.
- If a masked region contains multiple statements, branches, or lines, put the complete replacement in that one value.
- Each value must contain only the code that replaces the corresponding <mask>, in order.
- Do not include markdown fences or explanations.
- Do not repeat visible code outside the masks.

{masked_text}"""

RECOVERY_PROMPT_TEMPLATE = CODE_MASK_JSON_PROMPT_TEMPLATE


def build_recovery_prompt(masked_text: str, mode: str = "code_mask_json") -> str:
    if mode == "code_mask_json":
        return CODE_MASK_JSON_PROMPT_TEMPLATE.format(masked_text=masked_text)
    raise ValueError(f"Unknown recovery prompt mode: {mode}")
