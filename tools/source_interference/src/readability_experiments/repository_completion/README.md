# Repository completion (supplementary experiment)

This package discovers recent source spans, constructs original/perturbed
completion tasks, and validates model answers with focused native tests. It is
separate from the six-dataset readability benchmark and from feature training.

The finalized Python task input and pinned pytest source are committed under
`datasets/recent_repository_completion/pytest_python/`. Restore that dataset
offline with `python scripts/local_recent_completion_dataset.py restore` before
evaluating a model. `discovery.py`, `validate_manifest.py`, and `variants.py`
are dataset-construction tools; `validator.py` is the answer checker.
