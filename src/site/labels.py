METHOD_LABELS = {
    "loc_baseline": "LOC",
    "posnett": "Posnett",
    "scalabrino": "Scalabrino",
    "dorn": "Dorn",
    "dorn_retrained": "Dorn",
    "mi_convnet_cr_reproduction": "Mi",
    "cognascore_ml_consensus18_6dataset_sampled_margin": "CognaScore ML",
    "llm": "LLM prompt",
    "llm_prompt": "LLM",
}

DATASET_LABELS = {
    "mbjp": "MBJP",
    "buse": "Buse",
    "scalabrino": "Scalabrino",
    "jetbrains": "JetBrains",
    "dorn": "Dorn",
    "schnappinger": "Schnappinger",
    "java_comparative_obfuscation": "Java Interferences",
    "python_comparative_degradation": "Python Interferences",
}

METHOD_ORDER = (
    "posnett",
    "scalabrino",
    "dorn",
    "dorn_retrained",
    "mi_convnet_cr_reproduction",
    "cognascore_ml_consensus18_6dataset_sampled_margin",
    "llm_prompt",
    "llm",
    "loc_baseline",
)

DATASET_ORDER = (
    "mbjp",
    "buse",
    "scalabrino",
    "jetbrains",
    "dorn",
    "schnappinger",
    "java_comparative_obfuscation",
    "python_comparative_degradation",
)

MODEL_LABELS = {
    "gpt41-nano": "4.1",
    "gpt-4.1-nano-2025-04-14": "4.1",
    "gpt5-nano": "5nano",
    "gpt-5-nano-2025-08-07": "5nano",
    "dsv4-pro": "DSV4 Pro",
    "deepseek-v4-pro": "DSV4 Pro",
    "nomic-ai-nomic-embed-text-v1.5": "Nomic",
    "nomic-ai/nomic-embed-text-v1.5": "Nomic",
    "jinaai-jina-embeddings-v2-base-code": "Jina Code",
    "jinaai/jina-embeddings-v2-base-code": "Jina Code",
    "Qwen-Qwen3-Embedding-0.6B": "Qwen3 0.6B",
    "Qwen/Qwen3-Embedding-0.6B": "Qwen3 0.6B",
    "dorn_retrained_7feature": "7 features",
    "mi_2018_convnet_cr_independent_reproduction": "ConvNetCR",
}


def method_label(method: str) -> str:
    return METHOD_LABELS.get(method, method.replace("_", " ").title())


def dataset_label(dataset: str) -> str:
    return DATASET_LABELS.get(dataset, dataset.replace("_", " ").title())


def method_rank(method: str) -> tuple[int, str]:
    return (METHOD_ORDER.index(method) if method in METHOD_ORDER else len(METHOD_ORDER), method)


def dataset_rank(dataset: str) -> tuple[int, str]:
    return (DATASET_ORDER.index(dataset) if dataset in DATASET_ORDER else len(DATASET_ORDER), dataset)


def short_model_label(model: str | None) -> str | None:
    if not model:
        return None
    return MODEL_LABELS.get(model, model)
