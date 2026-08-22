# Semantic-context experiments

This folder is reserved for validation and ablation studies of the
short-identifier mathematical-context hypothesis. Experimental datasets,
anchor comparisons, and probe scripts should live here rather than in the
stable CognaScore package.

The production feature definitions currently remain in
`src/methods/cognascore/semantic_context.py` because they are part of the
existing feature-table schema. Moving or removing them would require rebuilding
all embedding-derived feature tables and is intentionally outside this
structure-only refactor.
