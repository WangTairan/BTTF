from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


OUTPUT_POLICY_OVERWRITE = "overwrite"
OUTPUT_POLICY_CONFIGURED_HISTORY = "configured_history"

COGNASCORE_DEFAULT_MODEL = "nomic-ai/nomic-embed-text-v1.5"
COGNASCORE_EMBEDDING_MODELS = (
    COGNASCORE_DEFAULT_MODEL,
    "jinaai/jina-embeddings-v2-base-code",
    "Qwen/Qwen3-Embedding-0.6B",
    "voyageai/voyage-4-nano",
    "Snowflake/snowflake-arctic-embed-m-v2.0",
)
COGNASCORE_DEFAULT_CACHE_DIR = Path("models")


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    path: Path
    modality: str
    label_type: str
    primary_metric: str


@dataclass(frozen=True)
class MethodSpec:
    key: str
    output_key: str
    output_policy: str
    deterministic: bool
    supports_code: bool = True


DATASETS: dict[str, DatasetSpec] = {
    "mbjp": DatasetSpec(
        key="mbjp",
        path=Path("datasets/mbjp_dev_dataset/readability_dataset.json"),
        modality="code",
        label_type="continuous",
        primary_metric="spearman",
    ),
    "scalabrino": DatasetSpec(
        key="scalabrino",
        path=Path("datasets/scalabrino/dataset"),
        modality="code",
        label_type="continuous",
        primary_metric="spearman",
    ),
    "buse": DatasetSpec(
        key="buse",
        path=Path("datasets/buse"),
        modality="code",
        label_type="continuous",
        primary_metric="spearman",
    ),
    "jetbrains": DatasetSpec(
        key="jetbrains",
        path=Path("datasets/jetbrains"),
        modality="code",
        label_type="binary",
        primary_metric="mcc_best_threshold",
    ),
    "schnappinger": DatasetSpec(
        key="schnappinger",
        path=Path("datasets/schnappinger"),
        modality="code",
        label_type="continuous",
        primary_metric="spearman",
    ),
    "dorn": DatasetSpec(
        key="dorn",
        path=Path("datasets/dorn/dataset"),
        modality="code",
        label_type="continuous",
        primary_metric="spearman",
    ),
    "generated_readability_90": DatasetSpec(
        key="generated_readability_90",
        path=Path("datasets/readability_dataset_90.jsonl"),
        modality="code",
        label_type="ordinal",
        primary_metric="spearman",
    ),
    "generated_binary_readability": DatasetSpec(
        key="generated_binary_readability",
        path=Path("datasets/readability_binary.jsonl"),
        modality="code",
        label_type="binary",
        primary_metric="mcc_best_threshold",
    ),
}

METHODS: dict[str, MethodSpec] = {
    "posnett": MethodSpec(
        key="posnett",
        output_key="posnett",
        output_policy=OUTPUT_POLICY_OVERWRITE,
        deterministic=True,
    ),
    "scalabrino": MethodSpec(
        key="scalabrino",
        output_key="scalabrino",
        output_policy=OUTPUT_POLICY_OVERWRITE,
        deterministic=True,
    ),
    "llm": MethodSpec(
        key="llm",
        output_key="llm_prompt",
        output_policy=OUTPUT_POLICY_CONFIGURED_HISTORY,
        deterministic=False,
    ),
    "rmc": MethodSpec(
        key="rmc",
        output_key="rmc",
        output_policy=OUTPUT_POLICY_CONFIGURED_HISTORY,
        deterministic=False,
    ),
}

UNSUPPORTED_METHOD_DATASETS = set()


def method_choices() -> tuple[str, ...]:
    return tuple(key for key in METHODS if key != "rmc")


def method_output_key(method: str) -> str:
    return METHODS[method].output_key


def method_history_policy(method: str) -> str:
    return METHODS[method].output_policy


def dataset_spec_for_path(path: Path) -> DatasetSpec | None:
    candidate = path.resolve()
    for spec in DATASETS.values():
        try:
            if spec.path.resolve() == candidate:
                return spec
        except FileNotFoundError:
            if spec.path == path:
                return spec
    return None


def dataset_key_for_path(path: Path) -> str | None:
    spec = dataset_spec_for_path(path)
    if spec is not None:
        return spec.key
    lower_name = path.name.lower()
    for spec in DATASETS.values():
        if spec.path.name.lower() == lower_name:
            return spec.key
    return None


def is_method_dataset_supported(method: str, dataset_path: Path) -> bool:
    dataset_key = dataset_key_for_path(dataset_path)
    if dataset_key is None:
        return True
    return (method, dataset_key) not in UNSUPPORTED_METHOD_DATASETS
