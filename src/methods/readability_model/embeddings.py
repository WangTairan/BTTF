from __future__ import annotations

import os
from pathlib import Path

from .lexeme import LexemeChunk

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")


SUPPORTED_EMBEDDING_MODELS = {
    "nomic-ai/nomic-embed-text-v1.5": "General-purpose embedding model retained for robustness experiments.",
    "jinaai/jina-embeddings-v2-base-code": "Code-oriented Jina embedding model for code/search/docstring style inputs.",
    "Qwen/Qwen3-Embedding-0.6B": "Recent Qwen3 embedding model with multilingual, long-context, code-retrieval, classification, and clustering support.",
    "voyageai/voyage-4-nano": "Apache-2.0 Voyage 4 nano embedding model, multilingual, 32k context, compact frontier retrieval model.",
    "Snowflake/snowflake-arctic-embed-m-v2.0": "Apache-2.0 Arctic Embed 2.0 medium model, multilingual retrieval model with efficient 0.3B-scale inference.",
}

MODEL_LOAD_KWARGS = {
    "Snowflake/snowflake-arctic-embed-m-v2.0": {
        "add_pooling_layer": False,
        "use_memory_efficient_attention": False,
    },
}


class NomicEmbedder:
    DEFAULT_MODEL = "nomic-ai/nomic-embed-text-v1.5"
    DEFAULT_CACHE_DIR = Path("models")

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
        cache_dir: Path | str | None = DEFAULT_CACHE_DIR,
        max_length: int | None = None,
    ) -> None:
        try:
            import torch
            import transformers.utils.import_utils as transformers_import_utils

            transformers_import_utils._torchvision_available = False
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "Missing local embedding dependencies. Install them with "
                "`python3 -m pip install -r requirements.txt`."
            ) from exc

        self.torch = torch
        self.device = self._resolve_device(device)
        cache_path = Path(cache_dir) if cache_dir is not None else None
        if cache_path is not None:
            cache_path.mkdir(parents=True, exist_ok=True)
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            local_files_only=True,
            cache_dir=str(cache_path) if cache_path else None,
        )
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            local_files_only=True,
            cache_dir=str(cache_path) if cache_path else None,
            **MODEL_LOAD_KWARGS.get(model_name, {}),
        )
        self.model.eval()
        self.model.to(self.device)
        self.model_name = model_name
        self.max_length = max_length

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with self.torch.inference_mode():
            outputs = self.model(**inputs)

        last_hidden = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]
        return [
            self._mean_pool(last_hidden[row], attention_mask[row])
            for row in range(len(texts))
        ]

    def embed_lexemes(self, chunks: list[LexemeChunk], batch_size: int = 32) -> list[list[float]]:
        return embed_lexemes(chunks, self, batch_size=batch_size)

    def _mean_pool(self, vectors, attention_mask) -> list[float]:
        keep = attention_mask.bool()
        selected = vectors[keep]
        if selected.shape[0] == 0:
            dim = int(vectors.shape[-1])
            return [0.0] * dim
        return selected.mean(dim=0).detach().cpu().tolist()

    def _resolve_device(self, requested: str | None) -> str:
        if requested and requested != "auto":
            return requested
        if self.torch.cuda.is_available():
            return "cuda"
        if hasattr(self.torch.backends, "mps") and self.torch.backends.mps.is_available():
            return "mps"
        return "cpu"


def embed_lexemes(chunks: list[LexemeChunk], embedder: NomicEmbedder, batch_size: int = 32) -> list[list[float]]:
    cache: dict[str, list[float]] = {}
    ordered_unique = []
    for chunk in chunks:
        if chunk.lexeme not in cache:
            cache[chunk.lexeme] = []
            ordered_unique.append(chunk.lexeme)

    for start in range(0, len(ordered_unique), batch_size):
        batch = ordered_unique[start:start + batch_size]
        vectors = embedder.embed_texts(batch)
        for lexeme, vector in zip(batch, vectors):
            cache[lexeme] = vector

    return [cache[chunk.lexeme] for chunk in chunks]
