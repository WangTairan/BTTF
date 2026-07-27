from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.experiments.registry import COGNASCORE_DEFAULT_CACHE_DIR, COGNASCORE_EMBEDDING_MODELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download CognaScore embedding models into the local model cache.")
    parser.add_argument(
        "models",
        nargs="*",
        choices=COGNASCORE_EMBEDDING_MODELS,
        help="Embedding model names. Defaults to all supported CognaScore embedding models.",
    )
    parser.add_argument("--cache-dir", type=Path, default=COGNASCORE_DEFAULT_CACHE_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_names = args.models or list(COGNASCORE_EMBEDDING_MODELS)
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
        )
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
