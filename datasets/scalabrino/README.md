# Scalabrino Dataset

This folder documents the official Scalabrino readability dataset. Complete
source snippets are local inputs, excluded from new public releases while
redistribution permission is unconfirmed. Download and extract the official
archive below before running source-based experiments. The viewer retains a
source-free result index and fixed case excerpts.

Files:

```text
dataset/  official extracted raw files used by runners
```

The files were downloaded from the official archive:

```text
https://dibt.unimol.it/report/readability/files/Dataset.zip
```

Archive checksum:

```text
Dataset.zip  8239ee0809cb9e95182bb019401b105ebd566b0dedfa707309753058d817d7ed
```

The zip file is not stored in the repository. The runner reads the extracted
original files directly from `dataset/`:

```text
dataset/scores.csv
dataset/Snippets/*.jsnp
```

Snippet count:

```text
java   200
```

The dataset adapter computes each snippet's readability score as the mean of
the non-empty ratings in the corresponding score column.

Each loaded item has:

```text
task_id            Scalabrio<source_id>
content            original snippet text
readability_score  mean human readability rating
metadata.language  java
metadata.source_id original snippet id
metadata.rating_count number of non-empty ratings used for the mean
```

JSONL conversion files are not used; runners read the original files directly.
