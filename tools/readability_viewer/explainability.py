"""Fixed random sample for inspecting recorded explanations and exact attribution."""
from __future__ import annotations

import gzip
import hashlib
import json
import random
from collections import defaultdict

from .catalog import ORDER
from .diagnosis import ROOT, decompose
from .public_catalog import source_digest

SEED = 42
SAMPLE_SIZE = 30


def sample_explanations(catalog):
    records = defaultdict(list)
    for path in sorted((ROOT / 'results/direct_llm/gpt61-sol').glob('run_*.jsonl.gz')):
        with gzip.open(path, 'rt') as handle:
            for line in handle:
                row = json.loads(line)
                if row['dataset'] in ORDER[:6]:
                    records[(row['dataset'], row['task_id'])].append(row)
    pool = []
    for dataset in ORDER[:6]:
        for index, item in enumerate(catalog.dataset(dataset)['items']):
            runs = sorted(records[(dataset, item.task_id)], key=lambda row: row['run'])
            digest = source_digest(item)
            if ([row['run'] for row in runs] != [1, 2, 3]
                    or any(row['source_sha256'] != digest or not row.get('explanation')
                           or row.get('llm_readability_score') is None for row in runs)):
                raise ValueError('Explanation records are incomplete or source-mismatched')
            pool.append({'dataset': dataset, 'index': index, 'task_id': item.task_id,
                         'source_sha256': digest, 'runs': runs})
    pool.sort(key=lambda row: (row['dataset'], row['task_id']))
    if len(pool) != 1100:
        raise ValueError('The fixed explanation population must contain 1,100 samples')
    selected = random.Random(SEED).sample(pool, SAMPLE_SIZE)
    for number, row in enumerate(selected, 1):
        row['review_id'] = f'E{number:02d}'
        item = catalog.dataset(row['dataset'])['items'][row['index']]
        values = catalog.cached_values(row['dataset'], item)
        if values is None:
            raise ValueError('Selected sample has no source-matched BTTF measurements')
        row['bttf'] = decompose(values)
    return selected
