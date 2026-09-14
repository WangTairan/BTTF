from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonl_write(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _jsonl_read(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class RunStore:
    """One immutable-on-completion directory for one model experiment run."""

    def __init__(self, run_directory: Path) -> None:
        self.directory = run_directory
        self.responses_path = run_directory / "responses.jsonl"

    @classmethod
    def create(
        cls,
        output_root: Path,
        run_name: str,
        tasks: list[dict[str, Any]],
        configuration: dict[str, Any],
        *,
        secret_sources: list[str] | None = None,
    ) -> "RunStore":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        directory = output_root / run_name / f"run-{stamp}"
        directory.mkdir(parents=True, exist_ok=False)
        store = cls(directory)
        _jsonl_write(directory / "tasks.jsonl", tasks)
        task_bytes = (directory / "tasks.jsonl").read_bytes()
        metadata = {
            "schema_version": 1,
            "run_id": directory.name,
            "run_name": run_name,
            "status": "running",
            "started_at": utc_now(),
            "finished_at": None,
            "task_count": len(tasks),
            "task_manifest_sha256": hashlib.sha256(task_bytes).hexdigest(),
            "configuration": configuration,
            "secret_sources": secret_sources or ["DEEPSEEK_API_KEY"],
            "secrets_stored": False,
        }
        store._write_json("run.json", metadata)
        return store

    def _write_json(self, name: str, value: dict[str, Any]) -> None:
        path = self.directory / name
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def append(self, record: dict[str, Any]) -> None:
        with self.responses_path.open("a", encoding="utf-8") as stream:
            # Preserve the documented field order. In particular, provider
            # metadata is deliberately kept at the end of every record.
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def responses(self) -> list[dict[str, Any]]:
        if not self.responses_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.responses_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def replace_responses(self, records: list[dict[str, Any]]) -> None:
        temporary = self.responses_path.with_suffix(".jsonl.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        temporary.replace(self.responses_path)

    @staticmethod
    def _group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        evaluated = [row for row in rows if row.get("correct") is not None]
        correct = [row for row in evaluated if row.get("correct") is True]
        usage_keys = (
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "prompt_cache_hit_tokens",
            "prompt_cache_miss_tokens",
        )
        token_totals = {
            key: sum(int(row.get("usage", {}).get(key, 0) or 0) for row in rows)
            for key in usage_keys
        }
        reasoning_tokens = sum(
            int(
                row.get("usage", {})
                .get("completion_tokens_details", {})
                .get("reasoning_tokens", 0)
                or 0
            )
            for row in rows
        )
        token_totals["reasoning_tokens"] = reasoning_tokens
        token_totals["visible_completion_tokens"] = max(
            0, token_totals["completion_tokens"] - reasoning_tokens
        )
        messages = [
            (row.get("raw_response", {}).get("choices") or [{}])[0].get("message", {})
            for row in rows
        ]
        reasoning = [
            str(message.get("reasoning_content") or message.get("reasoning") or "")
            for message in messages
        ]
        finish_reasons = [
            str(
                (row.get("raw_response", {}).get("choices") or [{}])[0].get(
                    "finish_reason"
                )
            )
            for row in rows
        ]
        return {
            "requests": len(rows),
            "evaluated": len(evaluated),
            "unevaluated": len(rows) - len(evaluated),
            "correct": len(correct),
            "incorrect": len(evaluated) - len(correct),
            "accuracy": len(correct) / len(evaluated) if evaluated else None,
            "token_totals": token_totals,
            "mean_total_tokens": token_totals["total_tokens"] / len(rows)
            if rows
            else None,
            "reasoning": {
                "responses_with_reasoning": sum(bool(text) for text in reasoning),
                "total_characters": sum(len(text) for text in reasoning),
            },
            "response_content": {
                "total_characters": sum(
                    len(str(row.get("answer") or "")) for row in rows
                ),
            },
            "finish_reasons": dict(sorted(Counter(finish_reasons).items())),
        }

    @staticmethod
    def _paired_summary(
        rows: list[dict[str, Any]], tasks: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Summarize transformed outcomes against each base bug's original."""
        indexed = {
            (
                str(row.get("model")),
                str(tasks.get(str(row.get("task_id")), {}).get("base_task_id")),
                str(tasks.get(str(row.get("task_id")), {}).get("condition")),
            ): row.get("correct")
            for row in rows
            if row.get("correct") is not None
        }
        transitions: dict[str, Counter[str]] = defaultdict(Counter)
        for (model, base_id, condition), transformed in indexed.items():
            if condition in {"None", "original"}:
                continue
            original = indexed.get((model, base_id, "original"))
            if original is None:
                continue
            label = {
                (True, True): "robust_success",
                (True, False): "degraded",
                (False, True): "improved",
                (False, False): "persistent_failure",
            }[(bool(original), bool(transformed))]
            transitions[condition][label] += 1

        def summarize(counts: Counter[str]) -> dict[str, Any]:
            pairs = sum(counts.values())
            original_success = counts["robust_success"] + counts["degraded"]
            return {
                "pairs": pairs,
                "robust_success": counts["robust_success"],
                "degraded": counts["degraded"],
                "improved": counts["improved"],
                "persistent_failure": counts["persistent_failure"],
                "conditional_degradation_rate": (
                    counts["degraded"] / original_success if original_success else None
                ),
            }

        overall: Counter[str] = Counter()
        for counts in transitions.values():
            overall.update(counts)
        return {
            "overall": summarize(overall),
            "by_condition": {
                condition: summarize(counts)
                for condition, counts in sorted(transitions.items())
            },
        }

    def finalize(self) -> dict[str, Any]:
        rows = self.responses()
        tasks = {
            str(task["task_id"]): task
            for task in _jsonl_read(self.directory / "tasks.jsonl")
        }
        by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_experiment: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_model[str(row["model"])].append(row)
            by_experiment[
                str(tasks.get(str(row["task_id"]), {}).get("experiment"))
            ].append(row)
            by_condition[
                str(tasks.get(str(row["task_id"]), {}).get("condition"))
            ].append(row)
        summary = {
            "schema_version": 1,
            "run_id": self.directory.name,
            "overall": self._group_summary(rows),
            "by_model": {
                key: self._group_summary(value)
                for key, value in sorted(by_model.items())
            },
            "by_experiment": {
                key: self._group_summary(value)
                for key, value in sorted(by_experiment.items())
            },
            "by_condition": {
                key: self._group_summary(value)
                for key, value in sorted(by_condition.items())
            },
            "paired_outcomes": self._paired_summary(rows, tasks),
        }
        self._write_json("summary.json", summary)
        metadata = json.loads((self.directory / "run.json").read_text(encoding="utf-8"))
        metadata["status"] = "completed"
        if not metadata.get("finished_at"):
            metadata["finished_at"] = utc_now()
        metadata["response_count"] = len(rows)
        self._write_json("run.json", metadata)
        (self.directory.parent / "latest.json").write_text(
            json.dumps(
                {
                    "run_id": self.directory.name,
                    "run_directory": self.directory.as_posix(),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        self._update_provider_index()
        return summary

    def _update_provider_index(self) -> None:
        provider_root = self.directory.parents[1]
        runs = []
        for metadata_path in sorted(provider_root.glob("*/run-*/run.json")):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            summary_path = metadata_path.parent / "summary.json"
            overall = {}
            if summary_path.is_file():
                overall = json.loads(summary_path.read_text(encoding="utf-8")).get(
                    "overall", {}
                )
            runs.append(
                {
                    "run_id": metadata.get("run_id"),
                    "run_name": metadata.get("run_name"),
                    "run_directory": metadata_path.parent.relative_to(
                        provider_root
                    ).as_posix(),
                    "status": metadata.get("status"),
                    "started_at": metadata.get("started_at"),
                    "finished_at": metadata.get("finished_at"),
                    "requests": overall.get("requests"),
                    "accuracy": overall.get("accuracy"),
                    "total_tokens": overall.get("token_totals", {}).get("total_tokens"),
                }
            )
        temporary = provider_root / "index.json.tmp"
        temporary.write_text(
            json.dumps(
                {"schema_version": 1, "runs": runs},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(provider_root / "index.json")
