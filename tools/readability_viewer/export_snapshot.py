"""Export source-matched measurements for browsing a fresh public checkout."""
from __future__ import annotations

import gzip
import argparse
import hashlib
import json
import math

from .catalog import Catalog, ORDER
from .site import METHODS, ResultSite
from .snapshot import DATA


def public_detail(method, detail):
    # Publish only inputs used by the feature panels, never stdout or file paths.
    fields = {
        'posnett': ('lines', 'halstead_volume', 'byte_entropy', 'z_value', 'score'),
        'dorn_retrained': ('raw_features', 'score'),
        'mi_convnet_cr_reproduction': ('score',),
        'scalabrino': ('score',),
        'lloc_baseline': ('score',),
    }
    return {key: detail[key] for key in fields.get(method, ()) if key in detail}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    catalog = Catalog()
    site = ResultSite(catalog)
    DATA.mkdir(exist_ok=True)
    for dataset in ORDER:
        bundle = catalog.dataset(dataset)
        scores, details = site.scores(dataset)
        records = []
        for index, item in enumerate(bundle['items']):
            values = catalog.cached_values(dataset, item)
            if values is None:
                raise ValueError(f'Missing source-matched measurements: {dataset}/{index}')
            diagnosis = catalog.diagnosis(dataset, index, None)
            record = {
                'task_id': item.task_id,
                'source_sha256': hashlib.sha256(item.content.encode()).hexdigest(),
                'features': {key: float(values[key]) if values[key] is not None and math.isfinite(values[key]) else None
                             for key in catalog.manifest['features']['ordered_names']},
                'regions': {feature['key']: [{key: region[key] for key in ('start', 'end', 'line', 'bpb')}
                                            for region in feature['regions']] for feature in diagnosis['features']},
                'trace_available': diagnosis['trace_available'],
                'methods': {},
            }
            for method in METHODS:
                if method in ('dsv4-pro', 'gpt61-sol', 'readability_model_consensus11_opencoder_jina'):
                    continue
                score = scores.get(method, {}).get(item.task_id)
                if score is not None:
                    record['methods'][method] = {'score': score, 'detail': public_detail(method, details.get(method, {}).get(item.task_id, {}))}
            records.append(record)
        path = DATA / f'{dataset}.json.gz'
        payload = json.dumps({'schema_version': 1, 'dataset': dataset, 'samples': records},
                             ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
        path.write_bytes(gzip.compress(payload, mtime=0))
        print(f'{dataset}: {len(records)} samples, {path.stat().st_size / 1024:.0f} KiB', flush=True)


if __name__ == '__main__':
    main()
