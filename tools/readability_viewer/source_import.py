"""Source-free manifests and browser-local import controls for full datasets."""
import hashlib
import json
from functools import lru_cache
from html import escape

from .public_catalog import index_document
from .snapshot import load_snapshot

OFFICIAL_ARCHIVES = {
    'buse': 'https://web.eecs.umich.edu/~weimerw/data/readability/readability-snippets.zip',
    'dorn': 'https://dibt-research.unimol.it/report/readability/files/DatasetDorn.zip',
    'scalabrino': 'https://dibt-research.unimol.it/report/readability/files/Dataset.zip',
}
IMPORT_ASSETS = ('<link rel="stylesheet" href="/assets/source-import.css">'
                 '<script src="/assets/fflate-0.8.3.js" defer></script>'
                 '<script src="/assets/source-import.js" defer></script>')


@lru_cache(maxsize=3)
def source_manifest(dataset):
    if dataset not in OFFICIAL_ARCHIVES:
        raise ValueError('Unsupported source import dataset')
    snapshots = load_snapshot(dataset)
    samples = []
    for index, row in enumerate(index_document()['datasets'][dataset]):
        snapshot = snapshots[row['task_id']]
        if snapshot['source_sha256'] != row['source_sha256']:
            raise ValueError('Import manifest does not match recorded measurements')
        # Only numeric offsets leave the exporter, never source fragments.
        regions = {key: [{field: region[field] for field in ('start', 'end', 'line')}
                         for region in entries]
                   for key, entries in snapshot['regions'].items()}
        samples.append({'index': index, 'task_id': row['task_id'],
                        'sha256': row['source_sha256'], 'regions': regions})
    revision = hashlib.sha256(json.dumps(samples, sort_keys=True).encode()).hexdigest()
    return {'schema_version': 1, 'dataset': dataset, 'revision': revision,
            'official_url': OFFICIAL_ARCHIVES[dataset], 'samples': samples}


def source_import_control(dataset):
    return f'''<div class="source-import" data-source-import="{escape(dataset)}"
data-source-manifest-url="/source-manifests/{escape(dataset)}.json">
<div class="source-import-actions"><a class="source-import-button" href="{OFFICIAL_ARCHIVES[dataset]}" target="_blank" rel="noopener noreferrer">Download official ZIP ↗</a>
<button class="source-import-button" type="button" data-source-load>Load ZIP</button>
<input type="file" accept=".zip,application/zip" data-source-file hidden>
<button class="source-import-button" type="button" data-source-load-folder>Load folder</button>
<input type="file" webkitdirectory multiple data-source-folder hidden>
<button class="source-import-button source-import-clear" type="button" data-source-clear disabled>Clear local data</button>
<button class="help-marker" type="button" aria-label="Where imported source code is stored" title="Imported code is saved in this browser's IndexedDB, only for this site. It stays available after refresh or reopening the tab and is not uploaded. Clearing it does not delete your downloaded ZIP or folder.">?</button></div>
<p class="source-import-status" role="status" aria-live="polite">Select the downloaded ZIP or its extracted folder. Files stay in your browser.</p></div>'''
