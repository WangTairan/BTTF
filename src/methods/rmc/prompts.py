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

ORIGINAL_PROMPT_VARIANT = "original"
GENERALIST_NEGATIVE_3SHOT_VARIANT = "generalist_negative_3shot"
GENERALIST_POSITIVE_3SHOT_VARIANT = "generalist_positive_3shot"
PROMPT_VARIANTS = (
    ORIGINAL_PROMPT_VARIANT,
    GENERALIST_NEGATIVE_3SHOT_VARIANT,
    GENERALIST_POSITIVE_3SHOT_VARIANT,
)

SINGLE_MASK_OUTPUT_RULES = """The final code contains exactly one missing region.
Return only valid JSON in this exact form: {"mask_1":"replacement code"}.
The value must contain the complete replacement, including every
statement or line in that region. Do not include explanations, Markdown, or
visible code outside the missing region."""

GENERALIST_EXAMPLES = """The following are three independent examples. Each
example contains its own single <mask> and its own response. They are
demonstrations, not part of the final task.

<example_1>

Input:
private boolean isUnequivocallyNonDirty(Object entity) {
    if (entity instanceof SelfDirtinessTracker) {
        <mask>
    }
    return false;
}

The visible code does not define any internal method exposed by
SelfDirtinessTracker. A conservative completion does not invent one.

Output:
{"mask_1":"return false;"}
</example_1>

<example_2>

Input:
public FrontBaseDialect() {
    registerColumnType(Types.CHAR, "char(1)");
    registerColumnType(Types.VARCHAR, <mask>);
}

The visible code establishes that the second argument is a database type name,
but it defines no additional placeholder language.

Output:
{"mask_1":"\\"varchar\\""}
</example_2>

<example_3>

Input:
switch (LA(1)) {
case 'A': case 'B': case 'C': case 'D': case 'E': case 'F': {
    matchRange('A', 'F');
    break;
}
case 'a': case 'b': case 'c': case 'd': case 'e': case 'f': {
    <mask>
}
}

The adjacent branch provides a complete local pattern, so it can be followed
without knowledge of the surrounding framework.

Output:
{"mask_1":"matchRange('a', 'f');\\nbreak;"}
</example_3>"""

POSITIVE_GENERALIST_EXAMPLES = """The following are three independent examples.
Each example contains its own single <mask> and its own response. They are
demonstrations, separate from the final task.

<example_1>

Input:
private boolean isUnequivocallyNonDirty(Object entity) {
    if (entity instanceof SelfDirtinessTracker) {
        <mask>
    }
    return false;
}

The visible branch supports a direct conservative Boolean result expressed
with basic Java syntax.

Output:
{"mask_1":"return false;"}
</example_1>

<example_2>

Input:
public FrontBaseDialect() {
    registerColumnType(Types.CHAR, "char(1)");
    registerColumnType(Types.VARCHAR, <mask>);
}

The visible call pattern supports the standard SQL type name as a direct string
value.

Output:
{"mask_1":"\\"varchar\\""}
</example_2>

<example_3>

Input:
switch (LA(1)) {
case 'A': case 'B': case 'C': case 'D': case 'E': case 'F': {
    matchRange('A', 'F');
    break;
}
case 'a': case 'b': case 'c': case 'd': case 'e': case 'f': {
    <mask>
}
}

The adjacent branch provides a complete local pattern. Apply the same structure
to the lowercase range.

Output:
{"mask_1":"matchRange('a', 'f');\\nbreak;"}
</example_3>"""

POSITIVE_SINGLE_MASK_OUTPUT_RULES = """The final code contains exactly one
missing region. Return exactly one valid JSON object in this form:
{"mask_1":"replacement code"}. The value contains the complete replacement,
including every statement or line in that region. The response consists solely
of this JSON object."""

GENERALIST_NEGATIVE_3SHOT_PROMPT_TEMPLATE = """Fill the missing region in the code.

Use only information explicitly available in the current code, general
programming knowledge, language knowledge, and standard-library knowledge.

- Do not rely on internal implementation details of a particular library or framework.
- Do not assume internal API names that the current code does not define.
- Do not use naming conventions specific to an unfamiliar project.
- Do not reconstruct a complete code-generator template from its fixed format.
- Do not assume familiarity with the code's application domain.
- Do not identify and reproduce a known source file from names or formatting.

When the visible code is insufficient to determine the original implementation,
give the reasonable completion an experienced generalist developer could make
from the local context alone.

{examples}

The examples are complete. The following <task> is the only code to complete.
It contains exactly one <mask>.

<task>

{output_rules}

{masked_text}
</task>"""

GENERALIST_POSITIVE_3SHOT_PROMPT_TEMPLATE = """You are an experienced generalist
software developer. You are skilled in programming languages, control flow,
data structures, debugging, testing, standard libraries, and common software
design.

Complete code using basic language syntax, standard-library facilities, visible
identifiers, and relationships established by the local context. Prefer direct,
conventional, executable implementations. Follow visible names, types, comments,
data flow, control flow, repeated structures, and local style. When several
implementations are reasonable, choose the simplest complete implementation
supported by the visible evidence.

{examples}

The examples are complete. The following <task> is the only code to complete.
Act as the same experienced generalist developer. The task contains exactly one
<mask>.

<task>

{output_rules}

{masked_text}
</task>"""

RECOVERY_PROMPT_TEMPLATE = CODE_MASK_JSON_PROMPT_TEMPLATE


def build_recovery_prompt(
    masked_text: str,
    mode: str = "code_mask_json",
    variant: str = ORIGINAL_PROMPT_VARIANT,
) -> str:
    if mode != "code_mask_json":
        raise ValueError(f"Unknown recovery prompt mode: {mode}")
    if variant == ORIGINAL_PROMPT_VARIANT:
        return CODE_MASK_JSON_PROMPT_TEMPLATE.format(masked_text=masked_text)
    templates = {
        GENERALIST_NEGATIVE_3SHOT_VARIANT: GENERALIST_NEGATIVE_3SHOT_PROMPT_TEMPLATE,
        GENERALIST_POSITIVE_3SHOT_VARIANT: GENERALIST_POSITIVE_3SHOT_PROMPT_TEMPLATE,
    }
    try:
        template = templates[variant]
    except KeyError as exc:
        raise ValueError(f"Unknown recovery prompt variant: {variant}") from exc
    return template.format(
        examples=(
            POSITIVE_GENERALIST_EXAMPLES
            if variant == GENERALIST_POSITIVE_3SHOT_VARIANT
            else GENERALIST_EXAMPLES
        ),
        output_rules=(
            POSITIVE_SINGLE_MASK_OUTPUT_RULES
            if variant == GENERALIST_POSITIVE_3SHOT_VARIANT
            else SINGLE_MASK_OUTPUT_RULES
        ),
        masked_text=masked_text,
    )


def build_recovery_messages(
    masked_text: str,
    mode: str = "code_mask_json",
    variant: str = ORIGINAL_PROMPT_VARIANT,
) -> list[dict[str, str]]:
    return [
        {
            "role": "user",
            "content": build_recovery_prompt(masked_text, mode=mode, variant=variant),
        }
    ]
