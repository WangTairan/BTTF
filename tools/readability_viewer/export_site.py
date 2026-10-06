"""Export the existing viewer for static hosting, using recorded measurements only."""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .catalog import Catalog, ORDER
from .diagnosis import ROOT
from .site import METHODS, ResultSite
from .source_access import public_diagnosis, source_restricted
from .source_import import OFFICIAL_ARCHIVES, source_manifest


class RecordedOnly:
    def analyze(self, *args, **kwargs):
        raise RuntimeError("Static export requires recorded features; inference is disabled.")


def portable_html(content, filename, diagnosis=None):
    """Relative URLs work on project Pages, custom domains, and local previews."""
    parent = posixpath.dirname(filename) or '.'
    def replace(match):
        target = html.unescape(match.group(2))[1:] or 'index.html'
        return match.group(1) + '="' + html.escape(posixpath.relpath(target, parent), quote=True) + '"'
    content = re.sub(r'(href|src|data-source-manifest-url)="(/(?!/)[^"]*)"', replace, content)
    if diagnosis:
        content = content.replace('id="mode-bttf"',
            'id="mode-bttf" data-diagnosis-url="' + html.escape(diagnosis, quote=True) + '"')
    return content


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src', 'data-diagnosis-url', 'data-source-manifest-url'} and value:
                self.targets.append(value)


def validate_site(output):
    pages = list(output.rglob('*.html'))
    for page in pages:
        parser = Links()
        parser.feed(page.read_text(encoding='utf-8'))
        for link in parser.targets:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            if url.path.startswith('/'):
                raise ValueError(f'Nonportable link in {page}: {link}')
            target = (page.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(output.resolve()) or not target.is_file():
                raise ValueError(f'Missing target in {page}: {link}')
    size = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    if size > 900_000_000:
        raise ValueError(f'Static site exceeds the publication size budget: {size} bytes')
    return len(pages), size


def export_site(output):
    output = Path(output).resolve()
    # Never overwrite an existing directory or the repository itself.
    output.mkdir(parents=True, exist_ok=False)
    catalog = Catalog()
    site = ResultSite(catalog)
    analyzer = RecordedOnly()

    def write(filename, content, diagnosis=None):
        path = output / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(portable_html(content, filename, diagnosis), encoding='utf-8')

    shutil.copytree(ROOT / 'docs/assets', output / 'assets')
    (output / '.nojekyll').touch()
    for dataset in OFFICIAL_ARCHIVES:
        path = output / 'source-manifests' / f'{dataset}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(source_manifest(dataset), ensure_ascii=False, allow_nan=False), encoding='utf-8')
    write('index.html', site.home())
    write('explainability.html', site.explainability_page())
    for method in METHODS:
        write(f'methods/{method}.html', site.method_page(method))
    sample_count = 0
    for dataset in ORDER:
        write(f'datasets/{dataset}.html', site.dataset_page(dataset))
        if not source_restricted(dataset):
            path = output / 'downloads' / f'{dataset}.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(catalog.export_dataset(dataset), ensure_ascii=False,
                                       allow_nan=False), encoding='utf-8')
        for index, item in enumerate(catalog.dataset(dataset)['items']):
            result = public_diagnosis(catalog.diagnosis(dataset, index, analyzer),
                                     site.source_visible(dataset, index), dataset)
            path = output / 'diagnoses' / dataset / f'{index}.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding='utf-8')
            write(f'samples/{dataset}/{index}.html', site.sample_page(dataset, index),
                  f'../../diagnoses/{dataset}/{index}.json')
            sample_count += 1
        print(f'Exported {dataset}', flush=True)
    for case in site.explanation_samples():
        write(f'explainability/{case["review_id"]}.html', site.explainability_page(case['review_id']),
              f'../diagnoses/{case["dataset"]}/{case["index"]}.json')
    pages, size = validate_site(output)
    print(f'Validated {pages} pages, {sample_count} sample diagnoses, {size / 1_000_000:.1f} MB.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New output directory (must not already exist).')
    export_site(parser.parse_args().output)


if __name__ == '__main__':
    main()
