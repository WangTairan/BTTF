from __future__ import annotations

import os
from pathlib import Path
import re

from .lexeme import LexemeChunk

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")


SUPPORTED_EMBEDDING_MODELS = {
    "nomic-ai/nomic-embed-text-v1.5": "Default general-purpose embedding model used by existing CognaScore runs.",
    "jinaai/jina-embeddings-v2-base-code": "Code-oriented Jina embedding model for code/search/docstring style inputs.",
    "Qwen/Qwen3-Embedding-0.6B": "Recent Qwen3 embedding model with multilingual, long-context, code-retrieval, classification, and clustering support.",
}


class NomicEmbedder:
    DEFAULT_MODEL = "nomic-ai/nomic-embed-text-v1.5"
    DEFAULT_CACHE_DIR = Path("models")
    STRUCT_TOKEN_WEIGHT = 1.0
    DOWNWEIGHT_TOKENS = {"for", "if", "def", "while", "else", "elif", "switch", "import"}

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
        input_ids = inputs["input_ids"]

        embeddings: list[list[float]] = []
        for row in range(len(texts)):
            keep = attention_mask[row].bool()
            ids = input_ids[row][keep].tolist()
            tokens = self.tokenizer.convert_ids_to_tokens(ids)
            vectors = last_hidden[row][keep]
            embeddings.append(self._weighted_average(tokens, vectors))
        return embeddings

    def embed_lexemes(self, chunks: list[LexemeChunk], batch_size: int = 32) -> list[list[float]]:
        return embed_lexemes(chunks, self, batch_size=batch_size)

    def _weighted_average(self, tokens: list[str], vectors) -> list[float]:
        if not tokens:
            return []

        dim = int(vectors.shape[-1])
        acc = self.torch.zeros(dim, device=vectors.device)
        sum_weight = 0.0

        for token, vector in zip(tokens, vectors):
            weight = self.weight_for_token(token)
            if weight <= 0.0:
                continue
            acc += vector * weight
            sum_weight += weight

        if sum_weight <= 0.0:
            return [0.0] * dim
        return (acc / sum_weight).detach().cpu().tolist()

    def _resolve_device(self, requested: str | None) -> str:
        if requested and requested != "auto":
            return requested
        if self.torch.cuda.is_available():
            return "cuda"
        if hasattr(self.torch.backends, "mps") and self.torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @classmethod
    def weight_for_token(cls, raw_token: str) -> float:
        token = normalize_token(raw_token)
        if is_all_underscore(token):
            return 0.0
        return cls.STRUCT_TOKEN_WEIGHT if token in cls.DOWNWEIGHT_TOKENS else 1.0


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


def normalize_token(token: str | None) -> str:
    if token is None:
        return ""
    return re.sub(r"^(?:[▁Ġ]+|##|@@)+", "", token)


def is_all_underscore(token: str) -> bool:
    return bool(token) and all(char == "_" for char in token)
