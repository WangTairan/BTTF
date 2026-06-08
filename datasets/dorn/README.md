# Dorn Dataset

This folder contains the official Dorn readability dataset.

Files:

```text
dataset/  official extracted raw files used by runners
```

The files were downloaded from the official archive:

```text
https://dibt.unimol.it/report/readability/files/DatasetDorn.zip
```

Archive checksum:

```text
DatasetDorn.zip  56df86ae823f2a8953b84e5dd143d0058a1239ce4cfac7764efd48ba8e439346
```

The zip file is not stored in the repository. The runner reads the extracted
original files directly from `dataset/`:

```text
cuda    120
java    121
python  119
total   360
```

```text
dataset/experience.csv
dataset/scores/cuda.csv
dataset/scores/java.csv
dataset/scores/python.csv
dataset/snippets/cuda/*.jsnp
dataset/snippets/java/*.jsnp
dataset/snippets/python/*.jsnp
```

The dataset adapter computes each snippet's readability score as the mean of
the non-empty ratings in the corresponding score column.

Each loaded item has:

```text
task_id            Dorn/<language>/<source_id>
content            original snippet text
readability_score  mean human readability rating
metadata.language  cuda, java, or python
metadata.source_id original snippet id
metadata.rating_count number of non-empty ratings used for the mean
```

JSONL conversion files are not used; runners read the original files directly.
