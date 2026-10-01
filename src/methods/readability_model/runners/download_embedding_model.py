from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.experiments.registry import READABILITY_MODEL_CACHE_DIR, READABILITY_MODEL_EMBEDDINGS
from src.methods.readability_model.embeddings import MODEL_LOAD_KWARGS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download supported embedding models into the local cache.")
    parser.add_argument(
        "models",
        nargs="*",
        help="Embedding model names. Defaults to all supported embedding models.",
    )
    parser.add_argument("--cache-dir", type=Path, default=READABILITY_MODEL_CACHE_DIR)
    args = parser.parse_args()
    unknown = [model for model in args.models if model not in READABILITY_MODEL_EMBEDDINGS]
    if unknown:
        parser.error(f"Unsupported embedding models: {', '.join(unknown)}")
    return args


def main() -> None:
    args = parse_args()
    model_names = args.models or list(READABILITY_MODEL_EMBEDDINGS)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["TRANSFORMERS_OFFLINE"] = "0"
    os.environ["HF_HUB_OFFLINE"] = "0"

    try:
        import transformers.utils.import_utils as transformers_import_utils

        transformers_import_utils._torchvision_available = False
        from transformers import AutoModel, AutoTokenizer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install embedding dependencies with `python3 -m pip install -r requirements.txt`.") from exc

    for model_name in model_names:
        print(f"Downloading {model_name} into {args.cache_dir}", flush=True)
        AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=str(args.cache_dir),
        )
        AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=str(args.cache_dir),
            **MODEL_LOAD_KWARGS.get(model_name, {}),
        )
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
