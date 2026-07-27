from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from src.datasets import DatasetItem
from src.experiments.registry import (
    COGNASCORE_DEFAULT_CACHE_DIR,
    COGNASCORE_DEFAULT_MODEL,
    DATASETS,
)

from ..embedding_cache import EmbeddingCache, SourceReference, embedding_cache_path
from ..embeddings import NomicEmbedder
from ..extractors.python import LexemeExtractor
from .common import dataset_output_name, load_items


DEFAULT_DATASET_KEYS = ("mbjp", "buse", "scalabrino", "jetbrains", "dorn", "schnappinger")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize CognaScore lexeme embeddings into SQLite.")
    parser.add_argument(
        "datasets",
        nargs="*",
        type=Path,
        help="Dataset paths. Defaults to all current code datasets.",
    )
    parser.add_argument("--embedding-model", default=COGNASCORE_DEFAULT_MODEL)
    parser.add_argument("--models", type=Path, default=COGNASCORE_DEFAULT_CACHE_DIR)
    parser.add_argument("--output", type=Path, default=Path("output/cognascore_embeddings"))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--device", default=None, help="cpu, cuda, mps, or auto.")
    parser.add_argument("--max-length", type=int, help="Maximum tokenizer sequence length for embedding forward passes.")
    parser.add_argument(
        "--missing-order",
        choices=("source", "shortest-first"),
        default="source",
        help="Order selected missing texts before embedding. shortest-first reduces CPU memory spikes.",
    )
    parser.add_argument("--limit-per-dataset", type=int)
    parser.add_argument("--max-new-embeddings", type=int, help="Only embed this many missing texts in this run.")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-item collection logs.")
    parser.add_argument(
        "--replace-sources",
        action="store_true",
        help="Delete existing source references for the selected datasets before inserting refreshed references.",
    )
    parser.add_argument(
        "--sources-only",
        action="store_true",
        help="Update source references without computing missing embeddings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_paths = args.datasets or [DATASETS[key].path for key in DEFAULT_DATASET_KEYS]
    extractor = LexemeExtractor()
    references, unique_texts = _collect_references(
        dataset_paths,
        extractor=extractor,
        limit_per_dataset=args.limit_per_dataset,
        quiet=args.quiet,
    )
    cache_path = embedding_cache_path(args.output, args.embedding_model)
    with EmbeddingCache(cache_path, model_name=args.embedding_model) as cache:
        if args.replace_sources:
            dataset_names = [dataset_output_name(path) for path in dataset_paths]
            print(f"Deleting existing source references for datasets: {', '.join(dataset_names)}", flush=True)
            cache.delete_sources_for_datasets(dataset_names)
        print(f"Writing source references: {len(references)} rows", flush=True)
        cache.upsert_sources(references)
        missing = cache.missing_texts(unique_texts)
        if args.missing_order == "shortest-first":
            missing.sort(key=lambda text: (len(text), text))
        if args.max_new_embeddings is not None:
            missing = missing[: args.max_new_embeddings]
        print(
            f"Embedding cache: {len(unique_texts)} unique texts, {len(missing)} selected missing",
            flush=True,
        )
        if missing and not args.sources_only:
            embedder = NomicEmbedder(
                model_name=args.embedding_model,
                device=args.device,
                cache_dir=args.models,
                max_length=args.max_length,
            )
            for start in range(0, len(missing), args.batch_size):
                batch = missing[start:start + args.batch_size]
                end = min(start + len(batch), len(missing))
                print(
                    f"Embedding batch {start // args.batch_size + 1}: "
                    f"{start + 1}-{end}/{len(missing)} "
                    f"(batch_size={len(batch)}, max_chars={max(len(text) for text in batch)})",
                    flush=True,
                )
                vectors = embedder.embed_texts(batch)
                cache.upsert_embeddings(batch, vectors)
                print(
                    f"Embedded {min(start + len(batch), len(missing))}/{len(missing)} missing texts",
                    flush=True,
                )
        counts = cache.counts()
    print(f"Wrote {cache_path}", flush=True)
    print(f"Cache counts: {counts}", flush=True)


def _collect_references(
    dataset_paths: list[Path],
    *,
    extractor: LexemeExtractor,
    limit_per_dataset: int | None,
    quiet: bool,
) -> tuple[list[SourceReference], list[str]]:
    references: list[SourceReference] = []
    text_seen: set[str] = set()
    unique_texts: list[str] = []
    for path in dataset_paths:
        dataset = dataset_output_name(path)
        items = load_items(path)
        if limit_per_dataset is not None:
            items = items[:limit_per_dataset]
        print(f"Collecting {dataset}: {len(items)} items", flush=True)
        for index, item in enumerate(items, start=1):
            if not quiet:
                print(f"[{index}/{len(items)}] {dataset} {item.task_id}", flush=True)
            item_references = _references_for_item(dataset, item, extractor)
            references.extend(item_references)
            for reference in item_references:
                if reference.text not in text_seen:
                    text_seen.add(reference.text)
                    unique_texts.append(reference.text)
    return references, unique_texts


def _references_for_item(
    dataset: str,
    item: DatasetItem,
    extractor: LexemeExtractor,
) -> list[SourceReference]:
    chunks, _ = extractor.extract_with_member_fallback(item.content)
    counts: Counter[tuple[str, str]] = Counter((chunk.type, chunk.lexeme) for chunk in chunks)
    return [
        SourceReference(
            dataset=dataset,
            task_id=item.task_id,
            chunk_type=chunk_type,
            text=text,
            count=count,
        )
        for (chunk_type, text), count in sorted(counts.items())
    ]


if __name__ == "__main__":
    main()
