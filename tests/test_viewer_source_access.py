from html import escape

from tools.readability_viewer.catalog import Catalog
from tools.readability_viewer.site import ResultSite
from tools.readability_viewer.source_access import (
    FULL_SOURCE_DATASETS, OFFICIAL_SOURCES, public_diagnosis,
)


def test_reproduction_links_are_limited_to_requested_methods():
    from tools.readability_viewer.site import REPRODUCTION_LINKS
    assert set(REPRODUCTION_LINKS) == {'dorn_retrained', 'mi_convnet_cr_reproduction', 'scalabrino'}
    site = ResultSite(Catalog())
    for method, links in REPRODUCTION_LINKS.items():
        html = site.method_page(method)
        for label, url in links:
            assert f'<a href="{url}">{label}</a>' in html
    assert 'Reproduction code and instructions' not in site.method_page('posnett')


def test_results_and_replies_remain_while_ordinary_source_is_hidden():
    site = ResultSite(Catalog())
    for dataset in OFFICIAL_SOURCES:
        items = site.catalog.dataset(dataset)['items']
        index = next(i for i in range(len(items)) if not site.source_visible(dataset, i))
        html = site.sample_page(dataset, index)
        if items[index].content:
            assert escape(items[index].content) not in html
        assert site.sample_scores_table(dataset, index) in html
        assert OFFICIAL_SOURCES[dataset] in html
        _, details = site.scores(dataset)
        for method in ('dsv4-pro', 'gpt61-sol'):
            for reply in details[method][items[index].task_id]['explanations']:
                assert escape(reply) in html
        assert site.dataset_page(dataset).count('class="sample-id-link"') == len(items)


def test_fixed_30_cases_keep_source_views_and_policy_can_be_restored():
    site = ResultSite(Catalog())
    cases = site.explanation_samples()
    assert len(cases) == 30
    for case in cases:
        assert site.source_visible(case['dataset'], case['index'])
    assert not site.source_visible('buse', 65)
    FULL_SOURCE_DATASETS.add('buse')
    try:
        assert site.source_visible('buse', 65)
        assert '/downloads/buse.json' in site.dataset_page('buse')
    finally:
        FULL_SOURCE_DATASETS.remove('buse')


def test_public_diagnosis_hides_source_without_changing_measurements():
    original = {'source': 'secret code', 'score': 0.4,
                'features': [{'value': 3, 'contribution': -0.1,
                              'regions': [{'text': 'secret code'}]}]}
    restricted = public_diagnosis(original, False, 'buse')
    assert restricted['source'] == ''
    assert restricted['features'][0]['regions'] == []
    assert restricted['features'][0]['value'] == 3
    assert restricted['features'][0]['contribution'] == -0.1
    assert restricted['score'] == original['score']
    assert original['source'] == 'secret code'
    assert public_diagnosis(original, True, 'buse') is original


def test_fresh_public_checkout_preserves_all_scores_and_fixed_cases(tmp_path, monkeypatch):
    import tools.readability_viewer.catalog as catalog_module
    from tools.readability_viewer.diagnosis import ROOT
    from tools.readability_viewer.public_catalog import SOURCE_DIRECTORIES, source_lines
    reference = ResultSite(Catalog())
    expected = {key: reference.scores(key)[0] for key in SOURCE_DIRECTORIES}
    expected_cases = [(r['dataset'], r['task_id']) for r in reference.explanation_samples()]
    (tmp_path / 'datasets').mkdir()
    for path in (ROOT / 'datasets').iterdir():
        if path.name not in SOURCE_DIRECTORIES:
            (tmp_path / 'datasets' / path.name).symlink_to(path, target_is_directory=path.is_dir())
    monkeypatch.setattr(catalog_module, 'ROOT', tmp_path)
    fresh = ResultSite(Catalog())
    for key in SOURCE_DIRECTORIES:
        assert fresh.scores(key)[0] == expected[key]
        assert len(fresh.catalog.dataset(key)['items']) == len(reference.catalog.dataset(key)['items'])
        for original, item in zip(reference.catalog.dataset(key)['items'], fresh.catalog.dataset(key)['items']):
            assert source_lines(item) == source_lines(original)
        assert fresh.dataset_page(key).count('class="sample-id-link"') == len(reference.catalog.dataset(key)['items'])
    assert [(r['dataset'], r['task_id']) for r in fresh.explanation_samples()] == expected_cases
    for row in fresh.explanation_samples():
        item = fresh.catalog.dataset(row['dataset'])['items'][row['index']]
        assert item.content
    diagnosis = fresh.catalog.diagnosis('buse', 65, None)
    assert len(diagnosis['features']) == 11
    assert diagnosis['source'] == ''
    assert 'Official dataset source' in fresh.sample_page('buse', 65)
