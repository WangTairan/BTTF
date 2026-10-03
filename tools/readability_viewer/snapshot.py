"""Portable display data; no model weights or machine-specific run metadata."""
from __future__ import annotations

import gzip
import json
from functools import lru_cache
from pathlib import Path


DATA = Path(__file__).resolve().parent / 'data'


@lru_cache(maxsize=8)
def load_snapshot(dataset):
    path = DATA / f'{dataset}.json.gz'
    if not path.exists():
        return {}
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        document = json.load(handle)
    if document['schema_version'] != 1 or document['dataset'] != dataset:
        raise ValueError('Unsupported viewer snapshot')
    return {row['task_id']: row for row in document['samples']}
