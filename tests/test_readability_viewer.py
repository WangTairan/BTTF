"""Check numerical fidelity and source evidence without loading neural models."""

import joblib
import numpy as np
import pytest

from tools.readability_viewer.diagnosis import ARTIFACT, decompose, model_metadata
from tools.readability_viewer.catalog import Catalog


def test_viewer_scores_match_serialized_predictor_with_missing_and_clipping():
    manifest = model_metadata()
    names = manifest["features"]["ordered_names"]
    parameters = manifest["pipeline"]
    predictor = joblib.load(ARTIFACT.with_name("model.joblib"))
    generator = np.random.default_rng(42)
    rows = generator.uniform(parameters["training_feature_min"], parameters["training_feature_max"], size=(8, 11))
    rows[0, 0] = np.nan
    rows[1, 1] = parameters["training_feature_max"][1] * 2
    rows[2, 2] = -100
    for row, expected in zip(rows, predictor.predict(rows)):
        result = decompose(dict(zip(names, row)))
        assert result["score"] == pytest.approx(expected, abs=1e-12)
        assert result["unbounded_score"] == pytest.approx(result["intercept"] + sum(f["contribution"] for f in result["features"]))


def test_catalog_lists_each_registered_dataset():
    from src.experiments.registry import DATASETS
    from tools.readability_viewer.catalog import ORDER
    assert set(ORDER) == set(DATASETS)


def test_missing_feature_key_and_infinite_value_are_not_silently_accepted():
    with pytest.raises(ValueError, match="All 11"):
        decompose({})
    manifest = model_metadata()
    values = dict(zip(manifest["features"]["ordered_names"], manifest["pipeline"]["imputer_statistics"]))
    values["base__operator_density"] = float("inf")
    with pytest.raises(ValueError, match="infinite"):
        decompose(values)


def test_sample_search_and_invalid_dataset():
    catalog = Catalog()
    records = catalog.samples("buse", "Buse/66")
    assert records["total"] == 1
    assert records["samples"][0]["task_id"] == "Buse/66"
    with pytest.raises(ValueError, match="Unknown dataset"):
        catalog.samples("not-a-dataset")


def test_original_site_layout_and_current_sample_tabs():
    from tools.readability_viewer.site import ResultSite
    site = ResultSite(Catalog())
    dataset = site.dataset_page("buse")
    assert 'data-sortable-samples' in dataset
    assert '/samples/buse/65.html' in dataset
    sample = site.sample_page("mbjp", 0)
    assert 'MBJP' in sample
    assert 'BTTF diagnosis' in sample
    assert 'data-mode-target="mode-code"' not in sample
    assert 'class="persistent-source"' in sample
    assert 'class="method-views bttf-view"' in sample
    assert 'GPT-4.1' not in sample
    assert 'CognaScore' not in sample
    assert 'Logical lines; fewer is more readable' in sample
    assert 'mean of three runs' in sample
    assert sample.count('<details open><summary>Run 1</summary>') == 2
    assert 'Halstead volume' in sample
    assert 'Identifier layout (horizontal)' in sample


def test_baseline_contributions_reconstruct_all_recorded_scores():
    import json
    from tools.readability_viewer.diagnosis import ROOT
    from tools.readability_viewer.baseline_diagnosis import decompose_baseline
    for method, count in [('posnett', 3), ('dorn_retrained', 7)]:
        for path in (ROOT / 'results/methods' / method).rglob('summary.json'):
            for row in json.loads(path.read_text())['results']:
                if row.get('score') is None:
                    continue
                result = decompose_baseline(method, row['result'])
                assert len(result['features']) == count
                assert result['score'] == pytest.approx(row['score'], rel=1e-10, abs=1e-12)
                assert result['logit'] == pytest.approx(result['intercept'] + sum(f['contribution'] for f in result['features']))


def test_presentation_hides_local_paths_and_redundant_diagnostics():
    from tools.readability_viewer.site import ResultSite, measurement_table, display_text
    content = measurement_table({'file_name': '/private/tmp/abc/Snippet.java',
                                'raw_output': 'readability /Users/example/Snippet.java 0.5',
                                'score': .5, 'note': 'missing /private/var/folders/abc/model.json'})
    assert 'Snippet.java' not in content
    assert '/private/' not in content
    assert '/Users/' not in content
    assert 'Raw output' not in content
    assert 'Score' in content
    assert '/home/' not in display_text('Error loading /home/example/model.json')
    site = ResultSite(Catalog())
    for content in [site.sample_page('buse', 65), site.explainability_page('E01')]:
        assert 'id="regions"' not in content
        assert 'id="suggestion"' not in content


def test_sample_score_comparison_uses_dataset_ranks_and_human_reference():
    from tools.readability_viewer.site import ResultSite
    site = ResultSite(Catalog())
    table = site.sample_scores_table('buse', 65)
    assert 'class="human-reference"' in table
    assert 'Dataset rank' in table
    assert 'class="help-marker"' in table
    assert 'average rank − 1' in table
    assert 'Ranks are percentiles within Buse' not in table
    assert site.human_targets('buse')[65] == pytest.approx(15/99)
    scores, _ = site.scores('buse')
    assert table.count('model-rank-marker') == 1 + sum(values.get('Buse/66') is not None for values in scores.values())
    ranks = site.score_ranks('buse')
    scores, _ = site.scores('buse')
    shortest = min(scores['lloc_baseline'], key=scores['lloc_baseline'].get)
    longest = max(scores['lloc_baseline'], key=scores['lloc_baseline'].get)
    assert ranks['lloc_baseline'][shortest] > ranks['lloc_baseline'][longest]
    assert 'human-reference' not in site.sample_scores_table('java_comparative_obfuscation', 1)
    assert 'human-reference' in site.explainability_page('E01')


def test_controlled_samples_link_original_without_human_ratings():
    from tools.readability_viewer.site import ResultSite
    site = ResultSite(Catalog())
    sample = site.sample_page("java_comparative_obfuscation", 1)
    assert 'Matched original source' in sample
    assert '<span>Human</span>' not in sample
    with pytest.raises(ValueError, match="Unknown sample"):
        site.sample_page("buse", -1)


def test_method_links_and_current_method_pages():
    from tools.readability_viewer.site import METHODS, ResultSite, method_link
    site = ResultSite(Catalog())
    for method, name in METHODS.items():
        assert f'/methods/{method}.html' in method_link(method)
        assert f'<h1>{name}</h1>' in site.method_page(method)
    bttf = site.method_page("readability_model_consensus11_opencoder_jina")
    assert 'Selected features' in bttf
    assert 'Assignment-value surprisal' in bttf
    with pytest.raises(ValueError, match="Unknown method"):
        site.method_page("obsolete-model")


def test_main_list_order_matches_paper():
    from tools.readability_viewer.catalog import ORDER, LABELS
    from tools.readability_viewer.site import METHODS
    assert [LABELS[key] for key in ORDER[:6]] == ["MBJP", "Buse", "Scalabrino", "Dorn", "Schnappinger", "JetBrains"]
    assert list(METHODS.values()) == ["Posnett", "Scalabrino", "Dorn", "Mi", "LLOC", "DeepSeek V4 Pro", "GPT-6.1 Sol", "BTTF"]


def test_dataset_descriptions_cover_current_catalog():
    from tools.readability_viewer.site import DATASET_DESCRIPTIONS, ResultSite
    from tools.readability_viewer.catalog import ORDER
    assert set(DATASET_DESCRIPTIONS) == set(ORDER)
    site = ResultSite(Catalog())
    assert '121 human readability ratings' in site.dataset_page("buse")
    assert 'fraction of readable votes' in site.dataset_page("jetbrains")
    assert '896 variants' in site.dataset_page("java_comparative_obfuscation")
    assert '920 variants' in site.dataset_page("python_comparative_degradation")


def test_dataset_downloads_preserve_source_ratings_and_pairing():
    import json
    from tools.readability_viewer.catalog import ORDER
    from tools.readability_viewer.site import ResultSite
    catalog = Catalog()
    site = ResultSite(catalog)
    for key in ORDER:
        exported = catalog.export_dataset(key)
        assert len(exported["samples"]) == len(catalog.dataset(key)["items"])
        assert exported["samples"][0]["source"] == catalog.dataset(key)["items"][0].content
        json.dumps(exported, allow_nan=False)
        from tools.readability_viewer.source_access import OFFICIAL_SOURCES
        link = OFFICIAL_SOURCES.get(key, f'/downloads/{key}.json')
        assert link in site.dataset_page(key)
    controlled = catalog.export_dataset("python_comparative_degradation")
    assert all(row["human_rating"] is None for row in controlled["samples"])
    assert controlled["samples"][0]["metadata"]["group_id"]


def test_explainability_sample_and_exact_attribution():
    from tools.readability_viewer.site import ResultSite
    site = ResultSite(Catalog())
    samples = site.explanation_samples()
    assert len(samples) == 30
    assert len({(row['dataset'], row['task_id']) for row in samples}) == 30
    assert samples[0]['task_id'] == 'Dorn/java/109'
    assert samples[-1]['task_id'] == 'Scalabrio83'
    for row in samples:
        result = row['bttf']
        assert len(result['features']) == 11
        assert result['intercept'] + sum(f['contribution'] for f in result['features']) == pytest.approx(result['unbounded_score'], abs=1e-12)
    overview = site.explainability_page()
    assert '14/30 (46.7%)' in overview
    assert 'Three runs per sample · 0–20 scale' in overview
    assert '<td>0.53</td>' in overview
    assert 'Score consistency across runs' in overview
    assert 'data-gap-key="gap-ds"' in overview
    assert 'Different scores across runs' not in overview
    assert 'These statistics describe scores' not in overview
    assert 'What can be inspected' not in overview
    detail = site.explainability_page('E01')
    assert 'BTTF feature contributions' in detail
    assert 'explanation-comparison' in detail
    assert detail.index('Source code') < detail.index('GPT-6.1 Sol explanations') < detail.index('BTTF feature contributions')
    assert 'Run 1 · 17/20' in detail
    assert 'Run 3 · 16/20' in detail
    assert 'name="explanation-model" value="gpt61-sol" checked' in detail
    assert 'name="explanation-model" value="dsv4-pro"' in detail
    assert 'data-explanation-model="dsv4-pro" hidden' in detail
    assert detail.count('class="explanation-run"') == 6
    with pytest.raises(ValueError, match='Unknown explanation example'):
        site.explainability_page('E99')


def test_interference_rates_match_published_paired_summaries():
    import json
    from tools.readability_viewer.site import ResultSite, interference_response
    from tools.readability_viewer.diagnosis import ROOT
    site = ResultSite(Catalog())
    for dataset in ('java_comparative_obfuscation', 'python_comparative_degradation'):
        items = site.catalog.dataset(dataset)['items']
        for method in ('posnett', 'scalabrino', 'dorn_retrained', 'mi_convnet_cr_reproduction', 'lloc_baseline'):
            path = ROOT / 'results/methods' / method / dataset / 'paired_summary.json'
            if not path.exists():
                continue
            expected = json.loads(path.read_text())['overall']
            rate, count = interference_response(items, site.scores(dataset)[0][method], lower_is_better=method == 'lloc_baseline')
            assert count == expected['changed_pair_count']
            assert rate == pytest.approx(expected['changed_only_score_decrease_rate'], abs=1e-15)
        expected_rates = {'java_comparative_obfuscation': {'dsv4-pro': 94.5, 'gpt61-sol': 95.5, 'readability_model_consensus11_opencoder_jina': 93.8},
                          'python_comparative_degradation': {'dsv4-pro': 89.8, 'gpt61-sol': 92.7, 'readability_model_consensus11_opencoder_jina': 87.6}}
        for method, expected in expected_rates[dataset].items():
            rate, _ = interference_response(items, site.scores(dataset)[0][method])
            assert round(100 * rate, 1) == expected


def test_tiny_score_changes_are_ties_not_successful_responses():
    from types import SimpleNamespace
    from tools.readability_viewer.site import interference_response
    original = SimpleNamespace(task_id='original', content='a', metadata={'group_id': 'g', 'is_baseline_variant': True})
    variant = SimpleNamespace(task_id='variant', content='b', metadata={'group_id': 'g', 'is_baseline_variant': False})
    rate, count = interference_response([original, variant], {'original': 1e-40, 'variant': 1e-50})
    assert (rate, count) == (0, 1)


def test_feature_explanations_are_present_in_both_sample_views():
    from tools.readability_viewer.site import ResultSite
    from tools.readability_viewer.diagnosis import DESCRIPTIONS
    site = ResultSite(Catalog())
    for html in (site.sample_page('buse', 0), site.explainability_page('E01')):
        assert 'id="selected-name"' in html
        assert 'id="description"' in html
        assert '<p id="description"></p><p id="equation"></p>' in html
        assert 'class="feature-list-scroll"' in html
        assert 'id="suggestion"' not in html
        assert 'id="regions"' not in html
    html = site.sample_page('buse', 0)
    assert html.count('class="baseline-description"') == 10
    assert all(description and len(description.split('. ')) <= 2
               for description, _ in DESCRIPTIONS.values())


def test_gap_sort_uses_full_dataset_percentiles():
    import re
    from tools.readability_viewer.site import ResultSite
    site = ResultSite(Catalog())
    html = site.dataset_page('buse')
    assert 'data-gap-key="gap-lloc_baseline"' in html
    rows = re.findall(r'<tr ([^>]*data-order="\d+"[^>]*)>', html)
    for index, attrs in enumerate(rows):
        match = re.search(r'data-gap-lloc_baseline="([^"]*)"', attrs)
        item = site.catalog.dataset('buse')['items'][index]
        expected = abs(site.score_ranks('buse')['lloc_baseline'][item.task_id]
                       - 100 * float(site.human_targets('buse')[index]))
        assert float(match.group(1)) == pytest.approx(expected)
    assert 'data-gap-key="gap-gpt"' in site.explainability_page()
    assert 'data-gap-key=' not in site.dataset_page('python_comparative_degradation')


def test_header_returns_to_parent_in_every_module():
    from tools.readability_viewer.site import ResultSite
    site = ResultSite(Catalog())
    for html, parent in [
        (site.dataset_page('buse'), '/'),
        (site.method_page('posnett'), '/'),
        (site.explainability_page(), '/'),
        (site.explainability_page('E01'), '/explainability.html'),
        (site.sample_page('buse', 65), '/datasets/buse.html'),
    ]:
        if parent == '/':
            assert 'class="header-parent"' not in html
        else:
            assert f'class="header-parent" href="{parent}"' in html
        assert 'All 30 examples' not in html
        assert '>Next</a>' not in html
        assert '>Previous</a>' not in html
        assert 'Back to samples' not in html


def test_display_precision_does_not_add_redundant_zeros():
    from tools.readability_viewer.site import num, score_num
    assert num(0.63123) == '0.631'
    assert num(2) == '2'
    assert num(-0.00001) == '0'
    assert num(None) == 'n/a'
    assert num(1.8889, 2) == '1.89'
    assert score_num('gpt61-sol', 12.333333) == '12.33'
    assert score_num('lloc_baseline', 11) == '11'


def test_public_viewer_works_without_development_caches(tmp_path, monkeypatch):
    import tools.readability_viewer.catalog as catalog_module
    import tools.readability_viewer.site as site_module
    from tools.readability_viewer.diagnosis import ROOT
    reference = site_module.ResultSite(Catalog())
    expected_scores = {method: {task: value for task, value in values.items() if value is not None}
                       for method, values in reference.scores('buse')[0].items()}
    expected_diagnosis = reference.catalog.diagnosis('buse', 65, None)
    (tmp_path / 'datasets').symlink_to(ROOT / 'datasets', target_is_directory=True)
    (tmp_path / 'results').mkdir()
    (tmp_path / 'results/direct_llm').symlink_to(ROOT / 'results/direct_llm', target_is_directory=True)
    monkeypatch.setattr(catalog_module, 'ROOT', tmp_path)
    monkeypatch.setattr(site_module, 'ROOT', tmp_path)
    fresh = site_module.ResultSite(Catalog())
    assert not fresh.catalog.dataset('buse')['traces']
    actual_scores = fresh.scores('buse')[0]
    assert actual_scores == expected_scores
    actual = fresh.catalog.diagnosis('buse', 65, None)
    assert actual['score'] == expected_diagnosis['score']
    for left, right in zip(actual['features'], expected_diagnosis['features']):
        assert left['contribution'] == right['contribution']
        assert left['regions'] == right['regions']
    assert fresh.explainability_page().count('data-score-ds=') == 30


def test_public_display_snapshots_match_sources_and_strip_run_metadata():
    from tools.readability_viewer.public_catalog import source_digest
    from tools.readability_viewer.snapshot import load_snapshot
    from tools.readability_viewer.catalog import ORDER
    catalog = Catalog()
    for dataset in ORDER:
        snapshot = load_snapshot(dataset)
        items = catalog.dataset(dataset)['items']
        assert len(snapshot) == len(items)
        for item in items:
            row = snapshot[item.task_id]
            assert row['source_sha256'] == source_digest(item)
            assert len(row['features']) == 11
            for method in row['methods'].values():
                assert not {'file_name', 'raw_output', 'stdout', 'stderr', 'source_path'} & method['detail'].keys()
