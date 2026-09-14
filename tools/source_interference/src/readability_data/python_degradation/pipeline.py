from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from readability_data.shared.alignment import INTERFERENCE_SPEC_BY_SLUG
from readability_data.shared.explorer import write_degradation_report

from .core import Context, validate
from .registry import INTERFERENCES
from .sampling import PROJECTS, REPOSITORIES, extract_balanced_classes


def construct_python_dataset(
    roots: dict[str, Path], output: Path, per_project: int = 25, seed: int = 20260823
) -> dict[str, object]:
    """Select a balanced class corpus and apply every plugin to original source."""
    if output.exists():
        raise ValueError(f"output path already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    selected_parent = Path(tempfile.mkdtemp(prefix="python-selected-"))
    selected = selected_parent / "corpus"
    try:
        source_records = extract_balanced_classes(roots, selected, per_project, seed)
        sources = {
            str(record["base_sample_id"]): (
                selected / str(record["local_path"])
            ).read_text(encoding="utf-8")
            for record in source_records
        }
        records: list[dict[str, object]] = []
        for source_record in source_records:
            identity = str(source_record["base_sample_id"])
            source = sources[identity]
            records.append(_write(staging, source_record, source, 0, None, {}, None))
            for order, plugin in enumerate(INTERFERENCES.values(), 1):
                result = plugin.apply(source, Context(seed, identity))
                validate(result.source)
                records.append(
                    _write(
                        staging,
                        source_record,
                        result.source,
                        order,
                        plugin,
                        result.stats,
                        str(records[-order]["variant_id"]),
                    )
                )
        source_commits = {
            project: next(
                str(r["source_commit"])
                for r in source_records
                if r["source"] == project
            )
            for project in PROJECTS
        }
        provenance = {
            "module": "python-source-interference",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "language": "Python",
            "granularity": "class",
            "application_mode": "independent-interference",
            "seed": seed,
            "sampling": {
                "projects": list(PROJECTS),
                "classes_per_project": per_project,
                "policy": "complete top-level production classes; method-bearing classes prioritized; tests, docs, examples, and migrations excluded",
                "source_commits": source_commits,
                "source_repositories": REPOSITORIES,
            },
            "base_class_count": len(source_records),
            "base_counts_by_source": dict(
                sorted(Counter(str(r["source"]) for r in source_records).items())
            ),
            "interference_count": len(INTERFERENCES),
            "variant_count_including_originals": len(records),
            "counts_by_interference": {
                slug: len(source_records) for slug in INTERFERENCES
            },
            "interferences": [
                {
                    "order": i,
                    "category": p.category,
                    "slug": p.slug,
                    "description": p.description,
                    "target_policy": INTERFERENCE_SPEC_BY_SLUG[p.slug].target_policy,
                    "template_count": INTERFERENCE_SPEC_BY_SLUG[p.slug].template_count,
                    "application": "original-source",
                    "implementation": f"{p.__class__.__module__}.{p.__class__.__name__}",
                }
                for i, p in enumerate(INTERFERENCES.values(), 1)
            ],
            "validation": {
                "parser": "Python stdlib ast.parse",
                "policy": "every extracted class and every generated variant must be UTF-8 and syntactically valid",
                "semantic_scope": "transformations are source-local; project-level execution and strict semantic equivalence are not claimed",
            },
        }
        (staging / "manifest.jsonl").write_text(
            "".join(
                json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                for r in records
            ),
            encoding="utf-8",
        )
        (staging / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_degradation_report(
            staging, records, "Python Interference Explorer", language="python"
        )
        staging.replace(output)
        return provenance
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(selected_parent, ignore_errors=True)


def _write(root, base, source, order, plugin, stats, parent_id):
    slug = "original" if plugin is None else plugin.slug
    category = "source" if plugin is None else plugin.category
    digest = hashlib.sha256(f"{base['base_sample_id']}:{slug}".encode()).hexdigest()[
        :12
    ]
    label = "SRC" if order == 0 else f"I{order:02d}"
    filename = f"{label}__{base['source']}__{base['unit_name']}__{digest[-8:]}.py"
    relative = (
        Path("source-original" if order == 0 else f"{category}/{slug}") / filename
    )
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source, encoding="utf-8")
    return {
        "variant_id": f"pyint-{digest}-{label}",
        "base_sample_id": base["base_sample_id"],
        "parent_variant_id": parent_id,
        "order": order,
        "level": order,
        "display_label": label,
        "stage": slug,
        "interference": None if plugin is None else slug,
        "category": category,
        "description": "Unmodified source class"
        if plugin is None
        else plugin.description,
        "application_mode": "independent-interference",
        "applied_interferences": [] if plugin is None else [slug],
        "transformation_stats": stats,
        "construction_source": "pluggable-python-degrader",
        "readability_direction": "baseline" if order == 0 else "decreasing",
        "granularity": "class",
        "source": base["source"],
        "source_name": base["source_name"],
        "source_commit": base["source_commit"],
        "source_repository": base["source_repository"],
        "source_path": base["source_path"],
        "unit_kind": "class",
        "unit_name": base["unit_name"],
        "original_content_sha256": base["content_sha256"],
        "content_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "line_count": len(source.splitlines()),
        "local_path": relative.as_posix(),
    }
