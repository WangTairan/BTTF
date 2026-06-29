METHOD_LABELS = {
    "rmc": "RMC",
    "posnett": "Posnett",
    "scalabrino": "Scalabrino",
    "cognascore": "CognaScore",
    "llm": "LLM prompt",
    "llm_prompt": "LLM",
}

DATASET_LABELS = {
    "mbjp": "MBJP",
    "scalabrino": "Scalabrino",
    "jetbrains": "JetBrains",
    "dorn": "Dorn",
    "schnappinger": "Schnappinger",
    "clear": "CLEAR",
}

METHOD_ORDER = (
    "rmc",
    "posnett",
    "scalabrino",
    "cognascore",
    "llm_prompt",
    "llm",
)

DATASET_ORDER = ("mbjp", "scalabrino", "jetbrains", "dorn", "schnappinger", "clear")

MODEL_LABELS = {
    "gpt41-nano": "4.1",
    "gpt-4.1-nano-2025-04-14": "4.1",
    "gpt5-nano": "5nano",
    "gpt-5-nano-2025-08-07": "5nano",
    "dsv4-pro": "DSV4 Pro",
    "deepseek-v4-pro": "DSV4 Pro",
    "nomic-ai-nomic-embed-text-v1.5": "Nomic",
    "nomic-ai/nomic-embed-text-v1.5": "Nomic",
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
