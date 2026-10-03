from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results" / "direct_llm"
EXPECTED_DATASETS = {
    "mbjp": 17,
    "buse": 100,
    "scalabrino": 200,
    "dorn": 360,
    "schnappinger": 304,
    "jetbrains": 119,
    "java_comparative_obfuscation": 1400,
    "python_comparative_degradation": 1400,
}
REQUIRED_FIELDS = {
    "schema_version",
    "model",
    "run",
    "dataset",
    "task_id",
    "source_sha256",
    "human_readability_score",
    "llm_readability_score",
    "explanation",
    "token_usage",
}


def test_direct_llm_archive_has_one_aligned_schema() -> None:
    manifest = json.loads((ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    assert {(entry["model"], entry["run"]) for entry in files} == {
        (model, run)
        for model in ("dsv4-pro", "gpt6-sol", "gpt61-sol")
        for run in (1, 2, 3)
    }

    reference_identities = None
    for entry in files:
        path = ARCHIVE / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            records = [json.loads(line) for line in stream]

        assert len(records) == entry["records"] == 3900
        assert Counter(record["dataset"] for record in records) == EXPECTED_DATASETS
        assert all(set(record) == REQUIRED_FIELDS for record in records)
        assert all(record["model"] == entry["model"] for record in records)
        assert all(record["run"] == entry["run"] for record in records)
        assert all(record["llm_readability_score"] is not None for record in records)

        identities = {
            (record["dataset"], record["task_id"], record["source_sha256"])
            for record in records
        }
        if reference_identities is None:
            reference_identities = identities
        else:
            assert identities == reference_identities
