"""Generate source-free result metadata and the unchanged fixed case sample."""
import json

from .catalog import Catalog
from .site import ResultSite
from .public_catalog import DATA, SOURCE_DIRECTORIES, source_digest, source_lines


def main():
    catalog = Catalog()
    site = ResultSite(catalog)
    selected = {(row['dataset'], row['index']) for row in site.explanation_samples()}
    datasets, sources = {}, {}
    for dataset in SOURCE_DIRECTORIES:
        datasets[dataset], sources[dataset] = [], {}
        for index, item in enumerate(catalog.dataset(dataset)['items']):
            if item.metadata.get('source_omitted'):
                raise ValueError('Export requires the complete local source datasets')
            datasets[dataset].append({'task_id': item.task_id, 'human_score': item.readability_score,
                                     'source_sha256': source_digest(item), 'lines': source_lines(item),
                                     'metadata': item.metadata})
            if (dataset, index) in selected:
                sources[dataset][item.task_id] = item.content
    DATA.mkdir(exist_ok=True)
    for name, document in [('public_sample_index', {'schema_version': 1, 'datasets': datasets}),
                           ('case_sources', {'schema_version': 1, 'seed': 42, 'sources': sources})]:
        (DATA / f'{name}.json').write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n')
    print(f'Indexed {sum(map(len, datasets.values()))} samples; retained {sum(map(len, sources.values()))} fixed case sources.')


if __name__ == '__main__':
    main()
