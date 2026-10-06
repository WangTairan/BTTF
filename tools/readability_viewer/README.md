# BTTF dataset and diagnosis viewer

Browse the six human-rated datasets and both
Java/Python transformation corpora. Select a sample to see its source,
human rating where applicable, current method scores, and the BTTF diagnosis tab
with all 11 feature values, contributions, and source-linked diagnosis.
Select a feature to highlight its measured regions and read its description.
The viewer uses the paper's final model and feature names.

Buse, Dorn, and Scalabrino retain complete sample lists, scores, recorded
LLM replies, and numeric feature contributions. Source views are limited to
the fixed 30-case analysis; other samples and dataset downloads link to the
official source. This display policy is centralized in `source_access.py`.
When the complete local source directories are absent, `public_catalog.py`
loads `data/public_sample_index.json` and the fixed excerpts in
`data/case_sources.json`. Full sample lists, human targets, model scores,
line counts, and numeric contributions remain available in a public checkout.
After confirming permission, add the dataset key to `FULL_SOURCE_DATASETS`
to restore its source views and downloads. Local evaluation data are unchanged.

## Load complete sources in your browser

On a Buse, Dorn, or Scalabrino dataset page, select **Download official ZIP**,
then **Load ZIP** and choose the downloaded archive.
If the browser automatically extracts downloads, select **Load folder** and
choose the resulting folder instead. No download directory is assumed or
preselected; both paths use the same source-hash verification.
No manual extraction, installation, or directory configuration is needed.
The browser matches the
entire dataset against the published source hashes and restores source views,
feature highlighting, and code copying on its sample pages. Nonmatching
archives are rejected without changing the recorded scores.

Imported code stays in the browser's local IndexedDB storage; it is not sent
to the viewer server or included in the repository or static export. It is
restored on subsequent visits to the same browser and site. **Clear local
data** removes it. Private browsing, site-data clearing, or storage restrictions
can remove or prevent persistence. Fixed 30-case examples remain directly
viewable without an import.

The importer uses the pinned, locally bundled fflate 0.8.3 ZIP reader, not a
runtime CDN. Its source-free manifests contain hashes and numeric feature
offsets only. Original dataset terms continue to apply to imported materials.

## Recorded results

The result matrix and controlled-response overview use the current local
result summaries and the archived three-run DeepSeek V4 Pro/GPT-6.1 Sol
scores. Sample pages retain baseline measurement tables and recorded cloud
explanations. Controlled samples link back to their matched original.

Run from the repository root:

```bash
python -m tools.readability_viewer.server
```

Open `http://127.0.0.1:8765`. The bundled files under `data/` contain the
11 feature measurements, source highlights, and baseline scores for the
supplied samples. They are matched to source SHA-256 hashes, not local paths.
Direct-LLM replies are read from `results/direct_llm/`.

## Online publication

In GitHub Settings → Pages, select **GitHub Actions** as the source.
The `pages.yml` workflow exports and checks the complete viewer on each push
to `main`. It publishes recorded diagnoses, without inference or API calls.
The existing source-display restrictions also apply to the online version.

To preview the static version locally, choose a new output directory:

```bash
python -m tools.readability_viewer.export_site --output /tmp/bttf-site
python -m http.server 8768 --directory /tmp/bttf-site --bind 127.0.0.1
```

Relative links support both the GitHub Pages `/BTTF/` prefix and custom domains.
The independent BTTF browser icon follows the selected light/dark theme.
Replace `docs/assets/favicon-light.svg` and `favicon-dark.svg` to customize
the two variants without changing page templates.

If local feature tables exist, sample diagnoses reuse the publication feature
tables under `artifacts/cognascore/features/` only when all three feature
families match the displayed source hash. Source-aligned token traces are read
from the causal-LM cache without changing the stored measurements. If traces
are absent, the viewer shows structural source regions without region BPB;
it does not guess token difficulty or select an invented literal tail.

Browsing the supplied samples requires neither neural checkpoints nor API
credentials. Measuring new source code requires locally downloaded Jina
Embeddings v2 Base Code and OpenCoder-1.5B-Base checkpoints. Regeneration is
documented in the [method guide](../../src/methods/readability_model/README.md).
The viewer never requests an API key or downloads a model.
CPU/float32 is the default; `--device mps` or `--device cuda` selects another
local device.

Scores use the frozen full-pool 11-feature predictor, including its original
imputation, training-range clipping, standardization, and coefficients.
These are diagnostic scores, not held-out CV/LODO benchmark predictions.
Human ratings retain each dataset's original scale. Controlled variants have
transformation labels, not human readability ratings.

Source highlights show where a property is measured, not how a whole-feature
contribution is allocated to tokens. Density and embedding statistics describe
groups of elements; declaration variation describes declaration headers.
Missing measurements use the frozen training
median and remain visibly labelled as imputed.

The frontend assets are in `docs/assets/`. To refresh bundled display data
after a deliberate model or dataset update, regenerate the feature tables and
baseline scores, then run:

```bash
python -m tools.readability_viewer.export_snapshot
```

This exports recorded measurements only; it does not refit models, call cloud
providers, or change the archived experiment results.
