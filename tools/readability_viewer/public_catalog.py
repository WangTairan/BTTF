"""Source-free sample index and the fixed, explicitly displayed case sources."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from src.datasets.types import DatasetItem

DATA = Path(__file__).resolve().parent / 'data'
SOURCE_DIRECTORIES = {
    'buse': 'datasets/buse/snippets',
    'dorn': 'datasets/dorn/dataset/snippets',
    'scalabrino': 'datasets/scalabrino/dataset/Snippets',
}


def source_digest(item):
    if item.metadata.get('source_omitted'):
        return item.metadata['source_sha256']
    return hashlib.sha256(item.content.encode()).hexdigest()


def source_lines(item):
    return item.metadata.get('source_line_count', len(item.content.splitlines()))


@lru_cache(maxsize=1)
def index_document():
    return json.loads((DATA / 'public_sample_index.json').read_text())


def public_items(dataset):
    cases = json.loads((DATA / 'case_sources.json').read_text())['sources']
    items = []
    for row in index_document()['datasets'][dataset]:
        source = cases.get(dataset, {}).get(row['task_id'])
        metadata = dict(row['metadata'], source_omitted=source is None,
                        source_sha256=row['source_sha256'], source_line_count=row['lines'])
        item = DatasetItem(row['task_id'], source or '', row['human_score'], metadata=metadata)
        if source is not None and source_digest(item) != row['source_sha256']:
            raise ValueError('Case source does not match its published measurements')
        items.append(item)
    return items
