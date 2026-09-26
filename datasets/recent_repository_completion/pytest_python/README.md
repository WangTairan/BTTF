# Recent Python repository-completion dataset

This directory is the local, versioned input to the Python completion and
readability-interference experiment. **No repository download is needed** to
evaluate these tasks. The source snapshot and task manifest are both included;
`manifest.json` records their SHA-256 checksums.

| Item | Provenance |
| --- | --- |
| Upstream repository | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| License | MIT (the upstream license is in the source archive) |
| Pinned commit | `53bc06b9933eb50b40cd904aa50bcd1b6cf2a49c` |
| Commit date | 2026-09-14 22:15:02 UTC (upstream commit timestamp, not a release date) |
| Language | Python |
| Source / test roots | `src/_pytest/` / `testing/` |
| Benchmark tasks | 507: 48 original holes and 459 independently perturbed variants, from 26 targets |
| Construction seed | `20260823` |

`pytest-source.tar.gz` is a Git archive of the *exact pinned commit*, without
the upstream `.git` history or local environment. `tasks.jsonl.gz` contains
the complete task records, including the prompt, masked source, expected source
hashes, perturbation condition, and task-specific `test_command`. The tests are
**not** part of the model prompt. `report.json` summarizes construction and
native prevalidation. The source archive includes the original tests required
by each task's test command; validation still requires the Python dependencies
for pytest to be installed locally. The original validation environment used
Python 3.11.14 and an editable install of this pinned pytest snapshot. The
per-task `test_command` invokes `<snapshot>/.venv/bin/python`; on a fresh
machine, create that environment once after restoration, for example:

```bash
python3.11 -m venv artifacts/source_interference/data/raw/completion_pilot/pytest/.venv
artifacts/source_interference/data/raw/completion_pilot/pytest/.venv/bin/python -m pip install -e artifacts/source_interference/data/raw/completion_pilot/pytest
```

Installing dependencies may require package-index access; restoring the
benchmark's source and task data does not. Python package versions used in
the original local run were pytest `9.2.0.dev317+g53bc06b99`, pluggy
`1.6.0`, iniconfig `2.3.0`, packaging `26.3`, and Pygments `2.21.0`.

From the repository root, restore the working copy and uncompressed task list:

```bash
python scripts/local_recent_completion_dataset.py verify
python scripts/local_recent_completion_dataset.py restore
```

Restoration writes under `artifacts/source_interference/`, does not access the
network, and does not overwrite an existing source checkout. An existing task
list must match the archived checksum. This is deliberately safe while a
validation run is in progress. The experiment runner can then use its existing
`--workspace artifacts/source_interference` and task-list paths.

To regenerate this archive from a prepared pinned checkout and completed local
task build, run `python scripts/local_recent_completion_dataset.py pack`. This
is a release-maintenance operation, **not** part of ordinary evaluation.
