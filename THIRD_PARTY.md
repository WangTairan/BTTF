# Third-party materials

Third-party datasets, source programs, model weights, and tools are not covered
by the Apache-2.0 license for this repository's original code. Preserve their
copyright notices and consult their original distribution terms before reuse.

| Material | Provenance |
| --- | --- |
| Browser ZIP reader (fflate 0.8.3) | [Upstream](https://github.com/101arrowz/fflate); MIT, retained in `licenses/third_party/fflate-MIT.txt`; the pinned UMD bundle is vendored in `docs/assets/` |
| MBJP-derived development set | [`NOTICE`](datasets/mbjp_dev_dataset/NOTICE.md); MBXP data are CC BY 4.0, distinct from the upstream evaluation code's Apache-2.0 license |
| JetBrains benchmark | [`README`](datasets/jetbrains/README.md); official Zenodo record declares CC BY 4.0 |
| Schnappinger benchmark and project sources | [`NOTICE`](datasets/schnappinger/NOTICE.md); dataset CC BY 4.0, project source licenses remain separate; only 304 evaluated sources and original notices are retained |
| Buse, Dorn, Scalabrino benchmarks | [`datasets/README.md`](datasets/README.md) and dataset-specific READMEs; public downloads found, explicit dataset redistribution terms not yet confirmed |
| Controlled Java sources | [`NOTICE`](datasets/constructed/java-comparative-obfuscation-class-100/NOTICE.md); Apache-2.0 sources and per-file transformation provenance |
| Controlled Python sources | [`NOTICE`](datasets/constructed/python-comparative-degradation-class-100/NOTICE.md); BSD-3-Clause, Apache-2.0, MIT, and applicable additional Python notices |
| Semantic-anchor excerpts | [`NOTICE`](src/methods/readability_model/resources/semantic_anchor_corpus/NOTICE.md); source revisions and licenses recorded in the manifest |
| Scalabrino compiled tool | [`src/methods/scalabrino/README.md`](src/methods/scalabrino/README.md); official download and SHA-256 checksums are documented |
| Pretrained embeddings and causal models | [`src/methods/readability_model/README.md`](src/methods/readability_model/README.md); weights are downloaded separately and retain the providers' terms |

Full texts for identified licenses and upstream notices are in
[`licenses/third_party/`](licenses/third_party/). These are not a license for
this repository's original code. Dataset extraction, target derivation, and
controlled transformations are identified in the corresponding notices.

Public availability of a download is not, by itself, a redistribution license.

## Publication exclusions: redistribution permission pending

This category is separate from generated caches, private credentials, and
obsolete experiments. Complete Buse, Dorn, and Scalabrino source collections
and their source archives are retained as research inputs. They are excluded
from the exported viewer, but remain tracked in this research checkout and
its history. They must not be treated as excluded from the repository merely
because ignore rules have been added. Repository publication remains pending.

| Excluded source material | Official source |
| --- | --- |
| `datasets/buse/snippets/`, `datasets/buse/raw/readability-snippets.zip` | [Buse and Weimer](https://web.eecs.umich.edu/~weimerw/data/readability/) |
| `datasets/dorn/dataset/snippets/` | [Readability datasets](https://dibt-research.unimol.it/report/readability/) |
| `datasets/scalabrino/dataset/Snippets/` | [Readability datasets](https://dibt-research.unimol.it/report/readability/) |
| `src/methods/scalabrino/official_tool/rsm.jar`, `readability.classifier` | [Scalabrino official tool](https://dibt.unimol.it/report/readability/files/readability.zip) |

Complete sample identifiers, aggregate human ratings, stored model results,
and recorded LLM replies remain available. The viewer uses a source-free
index for the excluded collections, with source excerpts for its unchanged
fixed 30-case analysis stored separately. This distinction records the
release scope; it is not a claim that the case excerpts have an express
redistribution license. Source access can be restored through the centralized
viewer policy after permission is confirmed. The viewer can also display a
user's official ZIP after browser-local import and
source-hash verification, without hosting or uploading those source files.
The import manifests contain only identities, hashes, and numeric region
offsets. This facility does not change the upstream distribution terms.
The public viewer implementation has been merged into this research repository
without deleting research inputs or rewriting its original history.

## Compiled baseline tool

The Scalabrino binary archive does not include a license statement for the
authors' tool and classifier in its supplied README. Its JAR includes licenses
for dependencies, which do not establish a license for the authors' own assets.
Confirm the authors' terms before redistributing those assets. The retrieval script is
[`scripts/fetch_scalabrino_tool.sh`](scripts/fetch_scalabrino_tool.sh).
The JAR and classifier remain tracked research inputs; they are not copied
into the exported viewer. Retrieve them from the official download to run the
Scalabrino baseline or the Dorn feature extractor. Stored viewer results do
not require these binaries.

Participant-identifying raw JetBrains survey data, private credentials, local
paper copies, and downloaded checkpoints are excluded by `.gitignore`.
