from pathlib import Path

import pytest

from tools.readability_viewer.export_site import portable_html, validate_site, RecordedOnly


def test_favicon_links_support_project_pages_and_local_server():
    from tools.readability_viewer.site import page
    from tools.readability_viewer.diagnosis import ROOT
    import xml.etree.ElementTree as ET
    output = portable_html(page('Example', ''), 'samples/buse/0.html')
    assert 'href="../../assets/favicon-light.svg"' in output
    for theme in ('light', 'dark'):
        icon = ROOT / f'docs/assets/favicon-{theme}.svg'
        assert ET.parse(icon).getroot().attrib['viewBox'] == '0 0 64 64'


def test_relative_links_and_static_diagnosis_preserve_source_text():
    content = '<a href="/">Home</a><script src="/assets/app.js"></script><div id="mode-bttf"></div><code>&lt;a href=&quot;/private&quot;&gt;</code>'
    converted = portable_html(content, 'samples/buse/0.html', '../../diagnoses/buse/0.json')
    assert 'href="../../index.html"' in converted
    assert 'src="../../assets/app.js"' in converted
    assert 'data-diagnosis-url="../../diagnoses/buse/0.json"' in converted
    assert '&lt;a href=&quot;/private&quot;&gt;' in converted


def test_static_export_never_runs_inference():
    with pytest.raises(RuntimeError, match='inference is disabled'):
        RecordedOnly().analyze('class A {}')


def test_validation_rejects_missing_or_root_relative_links(tmp_path):
    page = tmp_path / 'index.html'
    page.write_text('<a href="missing.html">Missing</a>')
    with pytest.raises(ValueError, match='Missing target'):
        validate_site(tmp_path)
    page.write_text('<a href="/assets/style.css">Root link</a>')
    with pytest.raises(ValueError, match='Nonportable'):
        validate_site(tmp_path)
    page.write_text('<a href="https://example.org/">Source</a>')
    assert validate_site(tmp_path)[0] == 1
