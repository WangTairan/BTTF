from __future__ import annotations

import json
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from readability_experiments.behavior_prediction.builder import (
    build_candidate as build_behavior_candidate,
)
from readability_experiments.test_guided_repair.builder import (
    build_candidate as build_repair_candidate,
)

from .anchors import java_mutation_anchors, python_mutation_anchors
from .catalog import Corpus, dataset_fingerprint, relative_path
from .tests_index import find_test_references


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _variant_summary(
    record: dict[str, object], corpus: Corpus, workspace: Path
) -> dict[str, object]:
    return {
        "variant_id": record["variant_id"],
        "interference": record.get("interference"),
        "category": record["category"],
        "content_sha256": record["content_sha256"],
        "changed_from_original": record["content_sha256"]
        != record["original_content_sha256"],
        "local_path": relative_path(
            corpus.dataset_root / str(record["local_path"]), workspace
        ),
    }


def build_candidate_experiments(
    corpora: list[Corpus],
    output_root: Path,
    workspace: Path,
) -> dict[str, object]:
    behavior: list[dict[str, object]] = []
    repair: list[dict[str, object]] = []
    source_fingerprints = {
        corpus.language: dataset_fingerprint(corpus.dataset_root) for corpus in corpora
    }
    scan_counts: dict[str, dict[str, int]] = {}

    for corpus in corpora:
        grouped = corpus.grouped_records()
        originals = [rows[0] for rows in grouped.values()]
        names_by_project: dict[str, set[str]] = {}
        for record in originals:
            names_by_project.setdefault(str(record["source"]), set()).add(
                str(record["unit_name"])
            )
        references_by_project: dict[str, dict[str, list[str]]] = {}
        language_scan = Counter()
        for project, names in names_by_project.items():
            references, files_scanned = find_test_references(
                corpus.raw_roots[project], corpus.language, names
            )
            references_by_project[project] = references
            language_scan["test_files_scanned"] += files_scanned

        for original in originals:
            project = str(original["source"])
            unit_name = str(original["unit_name"])
            test_refs = references_by_project[project].get(unit_name, [])
            if not test_refs:
                continue
            base_id = str(original["base_sample_id"])
            source_path = corpus.dataset_root / str(original["local_path"])
            common = {
                "schema_version": 1,
                "candidate_status": "static_candidate",
                "language": corpus.language,
                "base_sample_id": base_id,
                "project": project,
                "unit_name": unit_name,
                "unit_kind": original["unit_kind"],
                "upstream_source_path": str(original["source_path"]),
                "test_reference_files": test_refs,
                "test_reference_count": len(test_refs),
                "variants": [
                    _variant_summary(row, corpus, workspace) for row in grouped[base_id]
                ],
            }
            behavior.append(build_behavior_candidate(common))
            anchors = (
                java_mutation_anchors(source_path, base_id)
                if corpus.language == "java"
                else python_mutation_anchors(source_path, base_id)
            )
            repair_candidate = build_repair_candidate(common, anchors)
            if repair_candidate is not None:
                repair.append(repair_candidate)
        scan_counts[corpus.language] = dict(language_scan)

    behavior.sort(
        key=lambda row: (
            str(row["language"]),
            str(row["project"]),
            str(row["base_sample_id"]),
        )
    )
    repair.sort(
        key=lambda row: (
            str(row["language"]),
            str(row["project"]),
            str(row["base_sample_id"]),
        )
    )

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}-", dir=output_root.parent)
    )
    try:
        generated_at = datetime.now(timezone.utc).isoformat()
        for name, records in (
            ("behavior-prediction", behavior),
            ("test-guided-repair", repair),
        ):
            directory = staging / name
            directory.mkdir()
            _write_jsonl(directory / "candidates.jsonl", records)
            by_language = Counter(str(record["language"]) for record in records)
            by_project = Counter(str(record["project"]) for record in records)
            report = {
                "schema_version": 1,
                "experiment": name,
                "generated_at": generated_at,
                "status": "static_candidate_inventory",
                "candidate_count": len(records),
                "candidate_counts_by_language": dict(sorted(by_language.items())),
                "candidate_counts_by_project": dict(sorted(by_project.items())),
                "source_dataset_fingerprints": source_fingerprints,
                "test_scan": scan_counts,
                "note": "Candidates are not executable tasks until all required validation steps pass.",
            }
            (directory / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        output_root.mkdir(parents=True, exist_ok=True)
        for name in ("behavior-prediction", "test-guided-repair"):
            target = output_root / name
            if target.exists():
                shutil.rmtree(target)
            (staging / name).replace(target)
        shutil.rmtree(staging)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return {
        "output": relative_path(output_root, workspace),
        "behavior_candidates": len(behavior),
        "repair_candidates": len(repair),
        "source_dataset_fingerprints": source_fingerprints,
    }
