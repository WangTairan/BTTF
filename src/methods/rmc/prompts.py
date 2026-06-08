CODE_RECOVERY_PROMPT_TEMPLATE = """Complete the code below.

- Fill in every <mask>.
- The final answer must not contain the literal token <mask>.
- If you are uncertain, replace each <mask> with your best-effort valid code instead of leaving it blank.
- Do not change any other code.
- Keep all existing lines after the masks, including closing braces.
- Return one complete code block with the full code.

{masked_text}"""

CODE_PREFIX_PROMPT_TEMPLATE = """Continue the code from the prefix below.

- The prefix is fixed context and must remain unchanged.
- Complete the rest of the code after the prefix.
- Return one complete code block containing the prefix followed by your continuation.
- Do not add explanations.

{masked_text}"""

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

NATURAL_LANGUAGE_RECOVERY_PROMPT_TEMPLATE = """Complete the passage below.

- Fill in every <mask>.
- Do not change any visible text outside the masks.
- Keep the same sentence order.
- Return the full completed passage only.

{masked_text}"""

RECOVERY_PROMPT_TEMPLATE = CODE_RECOVERY_PROMPT_TEMPLATE


def build_recovery_prompt(masked_text: str, mode: str = "code") -> str:
    if mode == "code":
        return CODE_RECOVERY_PROMPT_TEMPLATE.format(masked_text=masked_text)
    if mode == "code_mask_json":
        return CODE_MASK_JSON_PROMPT_TEMPLATE.format(masked_text=masked_text)
    if mode == "code_prefix":
        return CODE_PREFIX_PROMPT_TEMPLATE.format(masked_text=masked_text)
    if mode == "natural_language":
        return NATURAL_LANGUAGE_RECOVERY_PROMPT_TEMPLATE.format(masked_text=masked_text)
    raise ValueError(f"Unknown recovery prompt mode: {mode}")
