"""Public source-display policy, separate from evaluation data access."""

OFFICIAL_SOURCES = {
    "buse": "https://web.eecs.umich.edu/~weimerw/data/readability/",
    "dorn": "https://dibt-research.unimol.it/report/readability/",
    "scalabrino": "https://dibt-research.unimol.it/report/readability/",
}

# Add a dataset key here after permission is confirmed to restore full source
# views and downloads. Evaluation records and the fixed case sample are unchanged.
FULL_SOURCE_DATASETS = set()


def source_restricted(dataset):
    return dataset in OFFICIAL_SOURCES and dataset not in FULL_SOURCE_DATASETS


def public_diagnosis(result, visible, dataset):
    if visible:
        return result
    return dict(result, source="", source_visible=False,
                source_url=OFFICIAL_SOURCES[dataset],
                features=[dict(feature, regions=[]) for feature in result['features']])
