# JetBrains human-rated readability dataset

Source: Agnia Sergeyuk, Olga Lvova, Sergey Titov, Anastasiia Serova, Farid
Bagirov, Evgeniia Kirillova, and Timofey Bryksin, *Reassessing Java Code
Readability Models with a Human-Centered Approach*.

Official replication package (v3): <https://zenodo.org/records/10550937>.
DOI: `10.5281/zenodo.10550937`. The publisher's record metadata declare
**CC BY 4.0**; the complete text is in
[`CC-BY-4.0.txt`](../../licenses/third_party/CC-BY-4.0.txt).

The retained upstream tables are `snippets.csv`, `aggregated.csv`, and
`snippets_with_human_scores.csv`. The 119 human-rated programs used by this
study are loaded from the snippet and counted-score tables. The adapter derives
each target as readable votes divided by readable plus unreadable votes; it
does not overwrite the original tables. The original raw survey export is not
bundled. Cite the original paper and data release when reusing these materials.
