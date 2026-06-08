# CognaScore

CognaScore extracts Java lexeme-level signals, embeds each unique lexeme with a
local Hugging Face model, clusters embeddings with DBSCAN, and uses mean
within-cluster diameter as its score.

Java member snippets are parsed by falling back to a synthetic enclosing class
when they are not standalone compilation units. Results record this as
`wrapped_snippet=true`. Structurally truncated fragments that remain invalid
after wrapping are reported as parsing errors.

## Contents

- `method.py`: reusable scorer API.
- `extractors/python/`: active Java lexeme extractor based on `javalang`.
- `extractors/java/`: reference Java extractor retained from the original implementation.
- `embeddings.py`: local Nomic embedding stage.
- `clustering.py`: DBSCAN clustering and cluster diameter calculation.
- `visualization.py` and `templates/`: browsable output rendering.
- `runners/`: single-file and dataset commands.

## Defaults

- Embedding model: `nomic-ai/nomic-embed-text-v1.5`
- DBSCAN `eps`: `0.18`
- DBSCAN `min_pts`: `2`
- Embedding batch size: `32`
- Model cache directory: `models/`

## Commands

```bash
python -m src.methods.cognascore.runners.file
python -m src.methods.cognascore.runners.dataset datasets/mbjp_dev_dataset/readability_dataset.json --limit 1
python -m src.methods.cognascore.runners.dataset datasets/schnappinger --limit 1
python -m src.methods.cognascore.runners.dataset datasets/jetbrains --limit 1
python -m src.methods.cognascore.runners.dataset datasets/scalabrino/dataset --limit 1
```

Dedicated CognaScore runners also write an HTML cluster visualization. Results
are keyed by embedding model; changing DBSCAN parameters for the same model
overwrites that model's result directory, with the active parameters recorded
in `summary.json` or `manifest.json`.

```text
output/cognascore/<dataset>/<embedding-model>/
```

The Dorn dataset is intentionally excluded from CognaScore experiments: it
contains structurally truncated snippets across Java, Python, and CUDA, and is
not recoverable by the Java lexeme extractor's conservative enclosing-class
preparation. CLEAR is natural language and is outside this Java lexeme method's
scope.
