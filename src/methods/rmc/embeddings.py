from __future__ import annotations

from functools import lru_cache
from math import sqrt
import os
from pathlib import Path
import re
from typing import Sequence

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")


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

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        inputs = self.tokenizer(
            list(texts),
            return_tensors="pt",
            padding=True,
            truncation=True,
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


@lru_cache(maxsize=1)
def get_default_embedder() -> NomicEmbedder:
    return NomicEmbedder()


@lru_cache(maxsize=20000)
def embed_text_cached(text: str) -> tuple[float, ...]:
    return tuple(get_default_embedder().embed_text(text))


def embed_texts_cached(texts: Sequence[str], batch_size: int = 32) -> dict[str, tuple[float, ...]]:
    cache: dict[str, tuple[float, ...]] = {}
    unique: list[str] = []
    for text in texts:
        if text not in cache:
            cache[text] = ()
            unique.append(text)

    embedder = get_default_embedder()
    for start in range(0, len(unique), batch_size):
        batch = unique[start : start + batch_size]
        vectors = embedder.embed_texts(batch)
        for text, vector in zip(batch, vectors):
            cache[text] = tuple(vector)
    return {text: cache[text] for text in texts}


def embedding_cosine_similarity(original: str, recovered: str) -> float:
    if not original.strip() and not recovered.strip():
        return 1.0
    if not original.strip() or not recovered.strip():
        return 0.0
    return vector_cosine(embed_text_cached(original), embed_text_cached(recovered))


def vector_cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def normalize_token(token: str | None) -> str:
    if token is None:
        return ""
    return re.sub(r"^(?:[▁Ġ]+|##|@@)+", "", token)


def is_all_underscore(token: str) -> bool:
    return bool(token) and all(char == "_" for char in token)
