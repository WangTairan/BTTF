"""Embed the frozen external semantic-anchor corpus without touching dataset sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.methods.cognascore.embedding_cache import EmbeddingCache, embedding_cache_path
from src.methods.cognascore.embeddings import NomicEmbedder
from src.methods.cognascore.paths import CALIBRATION_ROOT, EMBEDDING_CACHE_ROOT
from src.methods.cognascore.results import model_slug

from src.methods.cognascore.semantic_anchor_corpus import CORPUS_ROOT, MANIFEST_PATH

from .materialize_semantic_anchor_corpus import verify


DEFAULT_MODELS = (
    "nomic-ai/nomic-embed-text-v1.5",
    "Qwen/Qwen3-Embedding-0.6B",
    "jinaai/jina-embeddings-v2-base-code",
    "Snowflake/snowflake-arctic-embed-m-v2.0",
    "voyageai/voyage-4-nano",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-model", action="append", default=[])
    parser.add_argument("--models", type=Path, default=Path("models"))
    parser.add_argument("--embedding-cache-root", type=Path, default=EMBEDDING_CACHE_ROOT)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = verify()
    rows = list(manifest["samples"])
    texts = [(CORPUS_ROOT / row["snippet_path"]).read_text(encoding="utf-8") for row in rows]
    manifest_hash = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    for model_name in tuple(args.embedding_model or DEFAULT_MODELS):
        cache_path = embedding_cache_path(args.embedding_cache_root, model_name)
        with EmbeddingCache(cache_path, model_name=model_name) as cache:
            missing = cache.missing_texts(texts)
            print(f"{model_name}: {len(missing)}/{len(texts)} frozen anchors missing", flush=True)
            if missing:
                embedder = NomicEmbedder(
                    model_name=model_name,
                    device=args.device,
                    cache_dir=args.models,
                    max_length=args.max_length,
                )
                for start in range(0, len(missing), args.batch_size):
                    batch = missing[start:start + args.batch_size]
                    cache.upsert_embeddings(batch, embedder.embed_texts(batch))
                    print(f"  embedded {min(start + len(batch), len(missing))}/{len(missing)}", flush=True)
            if len(cache.vectors_for_texts(texts)) != len(texts):
                raise RuntimeError(f"Incomplete frozen anchor embeddings for {model_name}")
        output = CALIBRATION_ROOT / "sampled_semantic_anchors" / model_slug(model_name)
        output.mkdir(parents=True, exist_ok=True)
        metadata = {
            "schema_version": 1,
            "embedding_model": model_name,
            "max_length": args.max_length,
            "pooling": "attention-mask-aware mean pooling",
            "manifest": str(MANIFEST_PATH),
            "manifest_sha256": manifest_hash,
            "sample_count": len(texts),
            "category_language_counts": {
                f"{category}:{language}": sum(
                    row["category"] == category and row["language"] == language for row in rows
                )
                for category in ("mathematical", "application")
                for language in ("python", "java")
            },
        }
        (output / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"wrote: {output / 'metadata.json'}", flush=True)


if __name__ == "__main__":
    main()
