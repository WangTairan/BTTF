from __future__ import annotations

from dataclasses import replace

from .ast_masking import AST_GRANULARITIES, _ast_granularity, _candidates, _parse_java, _tokens
from .config import DEFAULT_AST_MIN_TOKENS
from .types import MaskConstraints, MaskSpan, MaskedSequence


JAVA_AST_PREFIX_STRATEGY = "java_ast_prefix_v1"


def java_ast_prefixes(
    source: str,
    constraints: MaskConstraints,
    min_tokens: int = DEFAULT_AST_MIN_TOKENS,
    ast_granularity: str = "control",
) -> tuple[MaskedSequence, ...]:
    """Produce prefix-continuation tasks at AST boundaries."""
    constraints.validate()
    if min_tokens < 1:
        raise ValueError("min_tokens must be >= 1")
    if ast_granularity not in AST_GRANULARITIES:
        raise ValueError(f"ast_granularity must be one of {AST_GRANULARITIES}")

    tree, parsed_source, prefix_length = _parse_java(source)
    tokens = _tokens(parsed_source)
    candidates = [
        candidate
        for candidate in _candidates(tree, tokens, prefix_length, len(source))
        if candidate.token_count >= min_tokens and _ast_granularity(candidate) == ast_granularity
    ]
    if not candidates:
        return ()

    cuts = sorted({candidate.end for candidate in candidates if 0 < candidate.end < len(source)})
    if not cuts:
        cuts = sorted({candidate.start for candidate in candidates if 0 <= candidate.start < len(source)})

    masks = []
    for step, cut in enumerate(cuts, start=1):
        preceding = [candidate for candidate in candidates if candidate.end <= cut]
        boundary = preceding[-1] if preceding else min(candidates, key=lambda item: abs(item.start - cut))
        masks.append(
            MaskedSequence(
                lines=tuple(source[:cut].splitlines()),
                spans=(MaskSpan(source.count("\n", 0, cut), source.count("\n") + 1),),
                granularity=step,
                masked_segments=1,
                selected_segments=step,
                strategy=JAVA_AST_PREFIX_STRATEGY,
                node_type=boundary.node_type,
                char_start=cut,
                char_end=len(source),
                token_count=boundary.token_count,
                ast_role=boundary.ast_role,
                ast_granularity=ast_granularity,
                node_types=(boundary.node_type,),
                ast_roles=(boundary.ast_role,),
                char_spans=((cut, len(source)),),
                stratum_total=len(cuts),
                stratum_sampled=len(cuts),
            )
        )
    return tuple(replace(mask, index=index) for index, mask in enumerate(masks))
