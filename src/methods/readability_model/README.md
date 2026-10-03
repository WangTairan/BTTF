# Primary readability model

This package extracts three feature families and fits fixed-feature Ridge
predictors. It does not contain benchmark-specific feature searches.

| Area | Responsibility |
| --- | --- |
| `extractors/`, `feature_database.py` | AST-tagged snippets and code-level features (`base__`, `compression__`) |
| `embedding_cache.py`, `embedding_features.py`, `semantic_context.py` | Reusable chunk vectors, geometry, clustering, and short-identifier context (`embedding__`, `semantic__`) |
| `llm_features/` | Local causal-LM predictability measurements (`llm__`) |
| `runners/` | Incremental feature production, validation, and Ridge materialization |
| `feature_schema.py`, `paths.py` | Column contracts and storage locations |

The primary retained feature sets have 11 and 18 columns. Each embedding
model is instantiated and fitted separately; embeddings from different
models are not concatenated. Candidate screening and benchmark evaluation
are documented in [`experiments/main/readability_model/`](../../../experiments/main/readability_model/).

Run commands from the repository root. To reuse cached embeddings and rebuild
only derived feature tables:

```bash
bash scripts/rebuild_readability_feature_tables.sh
```

After an extractor change, update embeddings and feature tables sequentially:

```bash
bash scripts/refresh_readability_after_extractor_change.sh
```

Generate the local causal-LM feature family separately:

```bash
python -m pip install -r requirements/llm.txt
bash scripts/run_llm_feature_tables.sh
```

Production caches and feature tables remain under the historical
`artifacts/cognascore/` namespace. Fitted predictors remain under
`frozen_models/cognascore/`. These storage names preserve published artifact
references and do not identify the active Python package. Replacing a
fitted artifact is explicit:

```bash
python -m src.methods.readability_model.runners.supervised_ridge --overwrite-artifact
```

See [`runners/README.md`](runners/README.md) for command boundaries and
[`llm_features/README.md`](llm_features/README.md) for the local LM module.
