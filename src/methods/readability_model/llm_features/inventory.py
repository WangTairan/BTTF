"""Deterministic inventory of causal-LM readability candidate measurements.

All measurements belong to the physical ``llm`` feature family. Subfamilies
describe what is measured, not additional model inputs or prediction models.
Q(c) is the original-source loss in bits divided by covered UTF-8 bytes.
Context gains compare prefixes preceding matched target blocks. Both traces
share the teacher-forced tokens within each block. Only complete occurrences
whose intersecting blocks have additional measurable source-prefix context
are eligible; early targets are not interpreted as zero context benefit.
"""

from __future__ import annotations

from dataclasses import dataclass

LLM_FEATURE_BUILD_VERSION = 5
ROLE_NAMES = (
    "identifier",
    "declaration_header",
    "call_target",
    "control_header",
    "assignment_rhs",
    "expression",
    "literal",
    "comment",
)
ROLE_DIFFICULTY_NAMES = tuple(role for role in ROLE_NAMES if role != "comment")


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    subfamily: str
    description: str
    formula: str
    required_roles: tuple[str, ...] = ()


def _definition(name, subfamily, description, formula, *roles):
    return FeatureDefinition(
        f"llm__{name}", subfamily, description, formula, tuple(roles)
    )


_ROLE_DESCRIPTIONS = {
    "identifier": "Original identifier occurrences, excluding keywords, comments and string contents",
    "declaration_header": "Declaration/signature headers excluding bodies and variable initializers; signature defaults remain part of the interface",
    "call_target": "Invocation targets only, excluding argument expressions",
    "control_header": "Execution-control headers or predicates, excluding controlled bodies",
    "assignment_rhs": "Initializer and assignment right-hand-side expressions",
    "expression": "Arithmetic, comparison, logical and bitwise expressions",
    "literal": "Original constant literals, excluding documentation strings",
    "comment": "Comment text and documentation strings; this does not measure relevance",
}


def _inventory() -> tuple[FeatureDefinition, ...]:
    definitions = [
        _definition(
            "code_perplexity",
            "global",
            "Token-level perplexity of the complete source",
            "exp(mean(token NLL))",
        ),
        _definition(
            "code_bits_per_byte",
            "global",
            "Prediction difficulty per covered source byte",
            "sum(token NLL)/log(2)/covered_UTF8_bytes",
        ),
        _definition(
            "local_surprisal_concentration",
            "global",
            "Mean difficulty of the most surprising local token blocks",
            "mean(top ceil(B*tail_fraction) block BPB values)",
        ),
    ]
    for role in ROLE_DIFFICULTY_NAMES:
        description = _ROLE_DESCRIPTIONS[role]
        definitions.extend(
            (
                _definition(
                    "assignment_value_difficulty" if role == "assignment_rhs" else f"{role}__bpb_mean",
                    "role_difficulty",
                    description + ": covered-byte-weighted difficulty",
                    "bits(role span union)/bytes(role span union)",
                    role,
                ),
                _definition(
                    "literal_tail_difficulty" if role == "literal" else f"{role}__bpb_tail_mean",
                    "role_difficulty",
                    description + ": difficult occurrence tail",
                    "mean(top ceil(n*tail_fraction) occurrence Q values)",
                    role,
                ),
                _definition(
                    "declaration_difficulty_variation" if role == "declaration_header" else f"{role}__bpb_std",
                    "role_difficulty",
                    description + ": occurrence-to-occurrence variation",
                    "population_std(occurrence Q values)",
                    role,
                ),
            )
        )
    definitions.extend(
        (
            _definition(
                "block_bpb_std",
                "local_organization",
                "Variation in difficulty across fixed-size token blocks",
                "population_std(block BPB values)",
            ),
            _definition(
                "block_tail_to_global_ratio",
                "local_organization",
                "Relative concentration of difficulty in the block tail",
                "local_surprisal_concentration/code_bits_per_byte",
            ),
            _definition(
                "block_surprisal_jump_mean",
                "local_organization",
                "Mean difficulty change between adjacent blocks",
                "mean(abs(diff(block BPB values)))",
            ),
            _definition(
                "block_surprisal_jump_q90",
                "local_organization",
                "Large adjacent-block difficulty changes",
                "quantile(abs(diff(block BPB values)), 0.9)",
            ),
            _definition(
                "hard_block_run_ratio",
                "local_organization",
                "Longest consecutive run above the block difficulty 80th percentile",
                "longest_run(block BPB > quantile(block BPB,0.8))/B",
            ),
            _definition(
                "block_bpb_gini",
                "local_organization",
                "Inequality of prediction difficulty across blocks",
                "sum_i sum_j abs(b_i-b_j)/(2*B*sum_i b_i)",
            ),
            _definition(
                "identifier_first_occurrence_bpb",
                "identifier_learning",
                "Difficulty of first occurrences of confirmed local/parameter bindings",
                "bits(first confirmed binding occurrences)/covered_bytes",
                "identifier",
            ),
            _definition(
                "identifier_reuse_bpb",
                "identifier_learning",
                "Difficulty of later occurrences of those same confirmed bindings",
                "bits(later confirmed binding occurrences)/covered_bytes",
                "identifier",
            ),
            _definition(
                "identifier_reuse_tail_bpb",
                "identifier_learning",
                "Difficult tail of later confirmed-binding occurrences",
                "mean(top ceil(n*tail_fraction) later occurrence Q values)",
                "identifier",
            ),
            _definition(
                "identifier_reuse_difficulty_increase",
                "identifier_learning",
                "Positive increases in difficulty relative to each binding's first occurrence",
                "mean_over_reused_bindings(mean_later(max(Q_later-Q_first,0)))",
                "identifier",
            ),
            _definition(
                "identifier_within_binding_bpb_std",
                "identifier_learning",
                "Within-binding variation, without conflating equal names in different scopes",
                "mean_over_reused_bindings(population_std(Q_all_occurrences))",
                "identifier",
            ),
            _definition(
                "short_identifier_bpb",
                "identifier_learning",
                "Difficulty of identifiers in the existing short-name candidate set",
                "bits(short identifier span union)/bytes(short identifier span union)",
                "identifier",
            ),
            _definition(
                "identifier_onset_difficulty",
                "identifier_learning",
                "Difficulty allocated to the first tokenizer piece of each identifier",
                "sum(first-piece allocated bits)/sum(first-piece allocated bytes)",
                "identifier",
            ),
            _definition(
                "identifier_continuation_bpb",
                "identifier_learning",
                "Difficulty allocated to subsequent tokenizer pieces of identifiers",
                "sum(continuation-piece allocated bits)/sum(continuation-piece allocated bytes)",
                "identifier",
            ),
            _definition(
                "identifier_context_gain_mean",
                "context_support",
                "Mean block-prefix difficulty difference of identical eligible identifier targets",
                "mean_over_eligible_occurrences(Q_short_block_prefix(identifier)-Q_long_block_prefix(identifier))",
                "identifier",
            ),
            _definition(
                "identifier_context_gain_q10",
                "context_support",
                "Weakly supported eligible identifier targets under additional block-prefix context",
                "quantile_over_eligible_occurrences(Q_short_block_prefix(identifier)-Q_long_block_prefix(identifier),0.1)",
                "identifier",
            ),
            _definition(
                "short_identifier_context_dependence",
                "context_support",
                "Block-prefix context support for eligible short names, not an automatic mathematical exemption",
                "mean_over_eligible_occurrences(Q_short_block_prefix(short identifier)-Q_long_block_prefix(short identifier))",
                "identifier",
            ),
            _definition(
                "call_target_context_gain_mean",
                "context_support",
                "Block-prefix context support for eligible invocation targets, excluding arguments",
                "mean_over_eligible_occurrences(Q_short_block_prefix(call_target)-Q_long_block_prefix(call_target))",
                "call_target",
            ),
            _definition(
                "expression_context_gain_mean",
                "context_support",
                "Block-prefix context support for eligible computation and predicate expressions",
                "mean_over_eligible_occurrences(Q_short_block_prefix(expression)-Q_long_block_prefix(expression))",
                "expression",
            ),
            _definition(
                "assignment_rhs_context_gain_mean",
                "context_support",
                "Block-prefix context support for eligible assignment values and initializers",
                "mean_over_eligible_occurrences(Q_short_block_prefix(assignment_rhs)-Q_long_block_prefix(assignment_rhs))",
                "assignment_rhs",
            ),
            _definition(
                "control_header_context_gain_mean",
                "context_support",
                "Block-prefix context support for eligible control predicates or headers, excluding bodies",
                "mean_over_eligible_occurrences(Q_short_block_prefix(control_header)-Q_long_block_prefix(control_header))",
                "control_header",
            ),
            _definition(
                "comment_code_prediction_gain",
                "context_support",
                "Information provided by preceding comments for identical subsequent code targets",
                "Q(code | matched prefix without comment)-Q(code | matched prefix with comment)",
                "comment",
            ),
            _definition(
                "comment_code_prediction_gain_source_density",
                "context_support",
                "Whole-source density of prediction bits supplied by eligible preceding comments",
                "sum(bits(code | prefix without comment)-bits(code | prefix with comment))/source_UTF8_bytes",
                "comment",
            ),
        )
    )
    return tuple(definitions)


LLM_FEATURE_INVENTORY = _inventory()
LLM_FEATURE_NAMES = tuple(definition.name for definition in LLM_FEATURE_INVENTORY)
assert len(LLM_FEATURE_NAMES) == 47 and len(set(LLM_FEATURE_NAMES)) == 47
