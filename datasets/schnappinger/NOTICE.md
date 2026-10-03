# Curated Schnappinger release

Dataset: Markus Schnappinger, Arnaud Fietzke, and Alexander Pretschner,
*A Software Maintainability Dataset*, version 3 (2020),
<https://doi.org/10.6084/m9.figshare.12801215.v3>.
The dataset release declares CC BY 4.0; see
[`CC-BY-4.0.txt`](../../licenses/third_party/CC-BY-4.0.txt).
Cite both the dataset and its associated ICSME 2020 paper, as requested in the
original `README.md`.

This repository curates the original archive to the 304 Java source files
referenced by `labels.csv`, retaining their original paths and bytes. Labels
are unchanged. Unused project sources, compiled classes, JAR dependencies,
project websites, manuals, and third-party papers are omitted. Original
license/copyright/NOTICE texts are retained even where the corresponding
auxiliary archive component is no longer included.

The dataset license does not replace licenses on the included project code:

| Project | Source license information |
| --- | --- |
| ArgoUML | Retained file headers specify applicable terms, including EPL-1.0; the archive also includes BSD notices. Full EPL text: [`EPL-1.0.txt`](../../licenses/third_party/EPL-1.0.txt) |
| Art of Illusion | GPL-2.0 text retained at `aoi/sourcefiles/LICENSE`; consult source headers for the applicable version wording |
| JUnit 4 | EPL-1.0 and original NOTICE retained at `junit4/sourcefiles/` |
| JSweet | Mixed terms: core Apache-2.0, transpiler/candy generator GPLv3, documentation CC-BY-SA; original subproject licenses and copyright texts retained |
| Diary Management | The [original project page](https://sourceforge.net/projects/diarymanagement/) declares MPL-1.1; full text: [`MPL-1.1.txt`](../../licenses/third_party/MPL-1.1.txt) |

`source_inventory.json` lists every retained evaluated source and its SHA-256.
The original complete archive can be obtained from the Figshare release above;
it is not needed to load or evaluate this curated benchmark.
