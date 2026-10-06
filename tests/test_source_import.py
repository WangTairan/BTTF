import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.readability_viewer.catalog import Catalog
from tools.readability_viewer.export_site import portable_html
from tools.readability_viewer.site import ResultSite
from tools.readability_viewer.source_import import source_manifest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('dataset,count', [('buse', 100), ('dorn', 360), ('scalabrino', 200)])
def test_import_manifest_contains_only_identity_hashes_and_numeric_offsets(dataset, count):
    manifest = source_manifest(dataset)
    assert len(manifest['samples']) == count
    for row in manifest['samples']:
        assert set(row) == {'index', 'task_id', 'sha256', 'regions'}
        assert len(row['sha256']) == 64
        for regions in row['regions'].values():
            for region in regions:
                assert set(region) == {'start', 'end', 'line'}
                assert all(isinstance(value, int) for value in region.values())
                assert 0 <= region['start'] <= region['end']
    assert json.loads(json.dumps(manifest)) == manifest


def test_import_controls_are_not_added_to_fixed_examples():
    site = ResultSite(Catalog())
    assert 'data-source-import="buse"' in site.dataset_page('buse')
    assert 'webkitdirectory multiple data-source-folder' in site.dataset_page('buse')
    assert 'data-source-load-folder' in site.dataset_page('buse')
    assert 'data-source-import="buse"' in site.sample_page('buse', 65)
    assert 'data-source-import' not in site.explainability_page('E01')
    for case in site.explanation_samples():
        assert 'data-source-import' not in site.sample_page(case['dataset'], case['index'])
    assert 'data-source-import' not in site.dataset_page('jetbrains')


def test_manifest_links_are_portable_on_project_pages():
    site = ResultSite(Catalog())
    html = portable_html(site.sample_page('buse', 65), 'samples/buse/65.html')
    assert 'data-source-manifest-url="../../source-manifests/buse.json"' in html
    assert 'src="../../assets/source-import.js"' in html


def test_browser_archive_matching_and_failure_cases():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node.js is needed for browser ZIP parser checks')
    subprocess.run([node, str(ROOT / 'tests/source_import_smoke.cjs')], cwd=ROOT, check=True)
