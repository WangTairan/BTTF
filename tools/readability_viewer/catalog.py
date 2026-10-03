"""Browse all registered samples and diagnose source-matched cached features."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import zlib
from pathlib import Path
from functools import lru_cache

from src.datasets import load_code_dataset
from src.experiments.registry import DATASETS
from src.methods.readability_model.paths import BASE_FEATURE_ROOT, EMBEDDING_FEATURE_ROOT, LLM_FEATURE_ROOT, LLM_SURPRISAL_CACHE_ROOT
from src.methods.readability_model.results import model_slug
from .diagnosis import ARTIFACT, ROOT, decompose, model_metadata, source_regions
from .snapshot import load_snapshot
from .public_catalog import SOURCE_DIRECTORIES, public_items, source_digest, source_lines

ORDER = ("mbjp", "buse", "scalabrino", "dorn", "schnappinger", "jetbrains", "java_comparative_obfuscation", "python_comparative_degradation")
LABELS = {"mbjp": "MBJP", "buse": "Buse", "scalabrino": "Scalabrino",
          "dorn": "Dorn", "schnappinger": "Schnappinger", "jetbrains": "JetBrains",
          "java_comparative_obfuscation": "Java transformations",
          "python_comparative_degradation": "Python transformations"}


class Catalog:
    def __init__(self):
        self.manifest = model_metadata()

    @lru_cache(maxsize=8)
    def dataset(self, key):
        if key not in DATASETS:
            raise ValueError("Unknown dataset")
        from src.methods.readability_model.runners.supervised_ridge import load_combined_features
        items = (public_items(key) if key in SOURCE_DIRECTORIES and not (ROOT / SOURCE_DIRECTORIES[key]).is_dir()
                 else load_code_dataset(ROOT / DATASETS[key].path))
        values, hashes, traces = {}, {}, {}
        try:
            frame = load_combined_features(key, ROOT / BASE_FEATURE_ROOT, ROOT / EMBEDDING_FEATURE_ROOT,
                self.manifest["features"]["ordered_names"], llm_feature_root=ROOT / LLM_FEATURE_ROOT,
                embedding_model=self.manifest["embedding_model"], llm_model=self.manifest["llm_feature_model"])
            values = {str(row["task_id"]): row for row in frame.to_dict("records")}
            base = json.loads((ROOT / BASE_FEATURE_ROOT / key / "nomic-ai-nomic-embed-text-v1.5/metadata.json").read_text())
            embedding = json.loads((ROOT / EMBEDDING_FEATURE_ROOT / key / model_slug(self.manifest["embedding_model"]) / "metadata.json").read_text())
            causal = json.loads((ROOT / LLM_FEATURE_ROOT / key / model_slug(self.manifest["llm_feature_model"]) / "metadata.json").read_text())
            causal_rows = {row["task_id"]: row for row in causal["rows"]}
            for item in items:
                candidate = base.get("source_sha256_by_task", {}).get(item.task_id)
                if candidate and candidate == embedding.get("source_sha256_by_task", {}).get(item.task_id) == causal_rows.get(item.task_id, {}).get("source_sha256"):
                    hashes[item.task_id] = candidate
            traces = {"configuration": causal["configuration"]["trace"], "rows": causal_rows}
        except (FileNotFoundError, KeyError):
            # A clean checkout still lists its datasets. Selected samples can
            # be measured using locally installed weights instead.
            values, hashes, traces = {}, {}, {}
        published = load_snapshot(key)
        for item in items:
            row = published.get(item.task_id)
            digest = source_digest(item)
            if row and row['source_sha256'] == digest and item.task_id not in hashes:
                values[item.task_id] = row['features']
                hashes[item.task_id] = digest
        return {"items": items, "values": values, "hashes": hashes, "traces": traces, "published": published}

    def datasets(self):
        return [{"key": key, "name": LABELS[key], "count": len(self.dataset(key)["items"]),
                 "kind": "controlled" if DATASETS[key].label_type == "paired_direction" else "human-rated"}
                for key in ORDER]

    def export_dataset(self, dataset):
        items = self.dataset(dataset)["items"]
        controlled = DATASETS[dataset].label_type == "paired_direction"
        return {"dataset": dataset, "name": LABELS[dataset],
                "kind": "controlled" if controlled else "human-rated",
                "samples": [{"task_id": item.task_id, "source": item.content,
                             "human_rating": None if controlled else item.readability_score,
                             "metadata": item.metadata} for item in items]}

    def cached_values(self, dataset, item):
        bundle = self.dataset(dataset)
        digest = source_digest(item)
        if bundle["hashes"].get(item.task_id) != digest:
            return None
        return bundle["values"].get(item.task_id)

    def samples(self, dataset, query="", page=0, sort="source"):
        bundle = self.dataset(dataset)
        records = []
        controlled = DATASETS[dataset].label_type == "paired_direction"
        for index, item in enumerate(bundle["items"]):
            if query and query.lower() not in (item.task_id + " " + item.content).lower():
                continue
            values = self.cached_values(dataset, item)
            score = decompose(values)["score"] if values else None
            records.append({"index": index, "task_id": item.task_id,
                            "language": item.metadata.get("language", "java"),
                            "human_score": None if controlled else item.readability_score,
                            "score": score, "variant": item.metadata.get("display_label"),
                            "group": item.metadata.get("group_id"),
                            "lines": source_lines(item)})
        if sort == "score":
            records.sort(key=lambda row: (row["score"] is None, row["score"] if row["score"] is not None else 0))
        start = max(0, page) * 50
        return {"dataset": dataset, "kind": "controlled" if controlled else "human-rated",
                "total": len(records), "page": max(0, page), "samples": records[start:start + 50]}

    def diagnosis(self, dataset, index, analyzer):
        bundle = self.dataset(dataset)
        if not 0 <= index < len(bundle["items"]):
            raise ValueError("Unknown sample")
        item = bundle["items"][index]
        values = self.cached_values(dataset, item)
        from src.methods.readability_model.runners.llm_surprisal_features import _source_policy
        language, fragments, members = _source_policy(item, dataset)
        if item.metadata.get('source_omitted'):
            if values is None:
                raise ValueError('Missing published feature measurements')
            result = decompose(values, self.manifest)
            for feature in result['features']:
                feature['regions'] = []
            result.update(source='', source_sha256=source_digest(item), language=language,
                          measurement_origin='Published source-matched measurements', trace_available=False)
        elif values is None:
            result = analyzer.analyze(item.content, language, fragments, allow_class_members=members)
            result["measurement_origin"] = "Local feature extraction"
        else:
            from src.methods.readability_model.llm_features.source_spans import analyze_source
            result = decompose(values, self.manifest)
            analysis = analyze_source(item.content, language, allow_fragments=fragments, allow_class_members=members)
            digest = hashlib.sha256(item.content.encode()).hexdigest()
            losses = self.cached_trace(bundle["traces"]["configuration"], digest,
                                       bundle["traces"]["rows"][item.task_id].get("trace_token_count")) if bundle['traces'] else []
            published = bundle['published'].get(item.task_id, {})
            matching = published.get('source_sha256') == digest
            for feature in result["features"]:
                feature["regions"] = ([dict(region, text=item.content[region['start']:region['end']])
                                       for region in published['regions'][feature['key']]] if not losses and matching
                                      else source_regions(item.content, analysis, losses, feature))
            result.update(source=item.content, language=language, source_sha256=digest,
                          model=self.manifest["name"], embedding_model=self.manifest["embedding_model"],
                          causal_model=self.manifest["llm_feature_model"],
                          measurement_origin="Source-matched cached feature tables" if bundle['traces'] else "Published source-matched measurements",
                          trace_available=bool(losses) or (matching and published.get('trace_available', False)))
        result.update(dataset=dataset, dataset_name=LABELS[dataset], task_id=item.task_id,
                      sample_index=index, human_score=item.readability_score if DATASETS[dataset].label_type != "paired_direction" else None,
                      variant=item.metadata.get("display_label"), group=item.metadata.get("group_id"),
                      source_form="snippet" if fragments else "class_members" if members else "program",
                      score_protocol="Frozen full-pool model; these are diagnostic scores, not CV or LODO predictions.")
        return result

    @staticmethod
    def cached_trace(configuration, digest, expected_count):
        from src.methods.readability_model.llm_features.scoring import TraceConfiguration
        from src.methods.readability_model.llm_features.types import TokenLoss
        path = ROOT / LLM_SURPRISAL_CACHE_ROOT / model_slug(configuration["model_name"]) / "traces.sqlite"
        if not path.exists():
            return []
        trace = TraceConfiguration(**configuration)
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
            windows = connection.execute("SELECT token_start,token_stop,payload FROM trace_windows WHERE source_sha256=? AND trace_sha256=? AND kind='global' ORDER BY token_start", (digest, trace.fingerprint_for("global"))).fetchall()
        losses = []
        for start, stop, payload in windows:
            rows = [TokenLoss(*row) for row in json.loads(zlib.decompress(payload))]
            if start != len(losses) or stop != start + len(rows):
                return []
            losses.extend(rows)
        return losses if expected_count is not None and len(losses) == expected_count else []
