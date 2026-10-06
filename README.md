# BTTF: Back to the Future

This research repository contains the final code, recorded results, and
interactive viewer, together with locally retained reproduction materials.
The viewer follows the public BTTF source-access policy: complete Buse, Dorn,
and Scalabrino sources are loaded by users from official downloads, while
sample results and the fixed 30-case analysis remain directly available.

**Publication status:** this checkout retains its original Git history and
tracked third-party reproduction inputs. The viewer is publication-filtered;
the repository itself has not yet been cleared for public release. Ignore
rules do not remove previously tracked files or historical copies. See
`RELEASING.md` and `THIRD_PARTY.md` before changing repository visibility.

Code and reproduction materials for BTTF, an interpretable code-readability model built from
traditional code measurements, embedding-space organization, and causal-LM
predictability. The repository contains the frozen models, datasets, selection
evidence, evaluation code, controlled transformations, and figure sources used
in the paper, *Back to the Future: Regressing Readability Features from LLMs*.

Large downloaded model weights and regenerable caches are not bundled.
External resources and retrieval commands are documented alongside the
components that use them.

Citation metadata is available in [`CITATION.cff`](CITATION.cff).

## Interactive diagnosis

The online viewer is published at [BTTF interactive results](https://wangtairan.github.io/BTTF/)
once GitHub Pages is enabled. It includes the same tables, sample diagnoses,
and 30-case analysis as the local viewer.

After installing the dependencies below, run:

```bash
python -m tools.readability_viewer.server
```

Open `http://127.0.0.1:8765` to browse benchmark results, controlled
transformations, and sample-level diagnoses. Each BTTF score is decomposed into
11 feature contributions linked to the source. The explainability module
compares three recorded GPT-6.1 Sol and DeepSeek V4 Pro responses on 30 fixed
random samples.

Published display measurements are bundled, so browsing the supplied samples
does not require model downloads, provider credentials, or local experiment
caches. Measuring new code requires the local pretrained models.
See the [viewer guide](tools/readability_viewer/README.md).

## Supplementary material

The paper's supplementary material is available in
[`bttf-fse-supplement.pdf`](bttf-fse-supplement.pdf).

## Repository map

| Location | Contents |
| --- | --- |
| [`src/methods/readability_model/`](src/methods/readability_model/) | Feature extraction and Ridge prediction |
| [`experiments/main/readability_model/`](experiments/main/readability_model/) | Selection, benchmark evaluation, robustness, ablation, and uncertainty analyses |
| [`experiments/baselines/`](experiments/baselines/) | Published and reproduced comparison methods |
| [`experiments/supplementary/`](experiments/supplementary/) | Paper-reported semantic-anchor and comment diagnostics |
| [`tools/source_interference/`](tools/source_interference/) | Controlled Java/Python readability transformations |
| [`tools/readability_viewer/`](tools/readability_viewer/) | Interactive results, source-linked diagnoses, and compact display data |
| [`datasets/`](datasets/) | Human-rated and controlled-interference datasets |
| [`results/direct_llm/`](results/direct_llm/) | Archived per-sample predictions from the direct-LLM baselines |
| [`frozen_models/`](frozen_models/) | Final 11-feature model, 18-feature predecessor, and fitted baselines |
| [`figures/`](figures/) | Publication figures, plotting scripts, and retained plotting data |
| [`requirements/`](requirements/) | Pinned environments for strict reproduction and causal-LM regeneration |

The reference final model uses OpenCoder-1.5B-Base predictability features and
Jina Embeddings v2 Base Code. The separately selected 18-feature
embedding-only predecessor also uses Jina. Historical artifact directories
retain the `cognascore/` namespace solely to preserve provenance.

## Setup

Use Python 3.11 from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements/reproduction.txt
```

Install [`requirements/llm.txt`](requirements/llm.txt) only when regenerating
causal-LM feature tables. The root [`requirements.txt`](requirements.txt) is
the complete default environment; the files under `requirements/` provide
task-specific pinned variants.
Some baselines require a JDK, and the direct-LLM baseline requires provider
credentials. Installation and release checks do not call external APIs.

Retrieve the official Scalabrino binary assets and verify their published
checksums with:

```bash
bash scripts/fetch_scalabrino_tool.sh
```

## Verify the release

```bash
bash scripts/check_public_release.sh
```

This checks the publication package, viewer, archived results, and dataset
tools without downloading model weights or overwriting publication results.
The complete research checks in `scripts/check_release.sh` additionally
require the separately obtained source collections and baseline binaries.

The verification suite is the recommended quick check. It does not regenerate
the pretrained-model feature tables, which requires downloading the model
checkpoints listed in `requirements/llm.txt` and the method documentation.

## Reproduce the main analyses

```bash
python -m experiments.main.readability_model.evaluation.cross_validate_fixed \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json

python -m experiments.main.readability_model.evaluation.leave_one_dataset_out \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json

python -m experiments.main.readability_model.evaluation.ablate_final_representation \
  --selected-features-metadata \
  experiments/main/readability_model/configs/consensus11_6dataset_three_llm_opencoder_jina.json

python -m experiments.main.readability_model.evaluation.evaluate_constructed_variants
```

These evaluations require locally generated feature tables under `artifacts/`.
Generation is documented in the [method README](src/methods/readability_model/README.md).
Dataset provenance and immutable inputs are documented in
[`datasets/README.md`](datasets/README.md).

Generated caches and downloaded weights are not tracked. The published display
data and direct-LLM records are retained separately from intermediate run logs.
Dataset and third-party asset provenance is documented in
[`THIRD_PARTY.md`](THIRD_PARTY.md).

## License

Unless otherwise indicated, this repository's original source code is licensed
under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution.
Third-party datasets, source excerpts, tools, and pretrained models retain
their respective licenses; see [THIRD_PARTY.md](THIRD_PARTY.md).
The code license does not relicense the paper, third-party materials, or data,
and does not grant rights to materials whose redistribution permission remains
unconfirmed.
