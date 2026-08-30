"""Train and freeze the paper-aligned Mi ConvNetCR reproduction."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean
from typing import Iterable

import numpy as np

from src.datasets import DatasetItem, load_code_dataset
from src.methods.cognascore.dataset_io import item_source_sha256

from .model import MiConvNetCR, torch
from .representation import (
    CharacterMatrixSpec,
    encode_character_matrix,
    fit_character_matrix_spec,
)


DEFAULT_OUTPUT = Path("frozen_models/mi_convnet_cr")
DATASET_PATHS = {
    "buse": Path("datasets/buse"),
    "dorn": Path("datasets/dorn/dataset"),
    "scalabrino": Path("datasets/scalabrino/dataset"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train an independent reconstruction of Mi et al.'s character-level "
            "code-readability ConvNet on the paper's DCRS protocol."
        )
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=2018)
    parser.add_argument("--cv-folds", type=int, default=10)
    parser.add_argument(
        "--skip-cv",
        action="store_true",
        help="Train the final model without the paper-aligned cross-validation diagnostic.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validate_args(args)
    samples, selection = load_dcrs_extreme_quartiles()
    matrix_spec = fit_character_matrix_spec([item.content for item, _ in samples])
    matrices = np.stack(
        [encode_character_matrix(item.content, matrix_spec) for item, _ in samples]
    )
    labels = np.asarray([label for _, label in samples], dtype=np.int64)
    cv = None
    if not args.skip_cv:
        cv = cross_validate(
            matrices,
            labels,
            matrix_spec,
            folds=args.cv_folds,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            seed=args.seed,
            device=args.device,
        )
        print(
            f"{args.cv_folds}-fold CV: accuracy={cv['accuracy']:.4f}, "
            f"macro_f1={cv['macro_f1']:.4f}",
            flush=True,
        )
    model = train_model(
        matrices,
        labels,
        matrix_spec,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
        device=args.device,
    )
    write_frozen_model(
        args.output,
        model,
        matrix_spec,
        samples,
        selection,
        args,
        cv,
    )
    print(f"Wrote frozen Mi ConvNetCR reproduction to {args.output}", flush=True)


def validate_args(args: argparse.Namespace) -> None:
    if args.epochs < 1:
        raise ValueError("epochs must be positive")
    if args.batch_size < 1:
        raise ValueError("batch-size must be positive")
    if args.cv_folds < 2 and not args.skip_cv:
        raise ValueError("cv-folds must be at least 2")


def load_dcrs_extreme_quartiles() -> tuple[
    list[tuple[DatasetItem, int]], dict[str, dict]
]:
    selected: list[tuple[DatasetItem, int]] = []
    report: dict[str, dict] = {}
    for dataset, path in DATASET_PATHS.items():
        items = load_code_dataset(path)
        if dataset == "dorn":
            items = [
                item
                for item in items
                if str(item.metadata.get("language", "")).lower() == "java"
            ]
        if any(item.readability_score is None for item in items):
            raise ValueError(f"{dataset} contains missing human readability scores")
        ordered = sorted(
            items,
            key=lambda item: (float(item.readability_score), item.task_id),
        )
        quartile_size = math.floor(len(ordered) * 0.25)
        if quartile_size < 1:
            raise ValueError(f"{dataset} is too small for extreme-quartile selection")
        unreadable = ordered[:quartile_size]
        readable = ordered[-quartile_size:]
        selected.extend((item, 0) for item in unreadable)
        selected.extend((item, 1) for item in readable)
        report[dataset] = {
            "source_count": len(items),
            "quartile_size": quartile_size,
            "selected_count": 2 * quartile_size,
            "unreadable_max_score": max(float(item.readability_score) for item in unreadable),
            "readable_min_score": min(float(item.readability_score) for item in readable),
        }
    return selected, report


def cross_validate(
    matrices: np.ndarray,
    labels: np.ndarray,
    matrix_spec: CharacterMatrixSpec,
    *,
    folds: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    device: str,
) -> dict:
    from sklearn.model_selection import StratifiedKFold

    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    predictions = np.full(len(labels), -1, dtype=np.int64)
    probabilities = np.full(len(labels), np.nan, dtype=np.float64)
    fold_rows = []
    for fold, (train_indices, test_indices) in enumerate(
        splitter.split(matrices, labels), start=1
    ):
        model = train_model(
            matrices[train_indices],
            labels[train_indices],
            matrix_spec,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            seed=seed + fold,
            device=device,
        )
        fold_probabilities = predict_probabilities(
            model,
            matrices[test_indices],
            batch_size=batch_size,
            device=device,
        )
        fold_predictions = (fold_probabilities >= 0.5).astype(np.int64)
        predictions[test_indices] = fold_predictions
        probabilities[test_indices] = fold_probabilities
        fold_rows.append(
            {
                "fold": fold,
                "test_count": len(test_indices),
                "accuracy": float(np.mean(fold_predictions == labels[test_indices])),
            }
        )
    if np.any(predictions < 0) or np.any(~np.isfinite(probabilities)):
        raise RuntimeError("Cross-validation did not produce complete out-of-fold predictions")
    return {
        "folds": folds,
        "accuracy": float(np.mean(predictions == labels)),
        "macro_f1": macro_f1(labels, predictions),
        "fold_results": fold_rows,
        "oof_readable_probabilities": probabilities.tolist(),
        "oof_predictions": predictions.tolist(),
    }


def train_model(
    matrices: np.ndarray,
    labels: np.ndarray,
    matrix_spec: CharacterMatrixSpec,
    *,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    device: str,
) -> MiConvNetCR:
    seed_everything(seed)
    model = MiConvNetCR(line_width=matrix_spec.max_line_width).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_function = torch.nn.CrossEntropyLoss()
    generator = torch.Generator().manual_seed(seed)
    matrix_tensor = torch.from_numpy(matrices)
    label_tensor = torch.from_numpy(labels)
    dataset = torch.utils.data.TensorDataset(matrix_tensor, label_tensor)
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )
    model.train()
    for _ in range(epochs):
        for batch_matrices, batch_labels in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch_matrices.to(device))
            loss = loss_function(logits, batch_labels.to(device))
            loss.backward()
            optimizer.step()
    model.eval()
    return model


def predict_probabilities(
    model: MiConvNetCR,
    matrices: np.ndarray,
    *,
    batch_size: int,
    device: str,
) -> np.ndarray:
    output = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(matrices), batch_size):
            batch = torch.from_numpy(matrices[start : start + batch_size]).to(device)
            probabilities = torch.softmax(model(batch), dim=1)[:, 1]
            output.extend(probabilities.cpu().numpy().tolist())
    return np.asarray(output, dtype=np.float64)


def macro_f1(actual: np.ndarray, predicted: np.ndarray) -> float:
    values = []
    for label in (0, 1):
        true_positive = int(np.sum((actual == label) & (predicted == label)))
        false_positive = int(np.sum((actual != label) & (predicted == label)))
        false_negative = int(np.sum((actual == label) & (predicted != label)))
        denominator = 2 * true_positive + false_positive + false_negative
        values.append(0.0 if denominator == 0 else (2 * true_positive) / denominator)
    return mean(values)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


def write_frozen_model(
    output: Path,
    model: MiConvNetCR,
    matrix_spec: CharacterMatrixSpec,
    samples: list[tuple[DatasetItem, int]],
    selection: dict,
    args: argparse.Namespace,
    cross_validation: dict | None,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    weights_path = output / "weights.pt"
    torch.save(model.cpu().state_dict(), weights_path)
    manifest = {
        "format_version": 1,
        "method": "mi_convnet_cr",
        "implementation": "independent_paper_aligned_reproduction",
        "paper": {
            "title": "Improving Code Readability Classification Using Convolutional Neural Networks",
            "authors": "Mi et al.",
            "year": 2018,
            "doi": "10.1016/j.infsof.2018.07.006",
        },
        "scope": (
            "Character-level ConvNetCR component, not the unavailable frozen "
            "three-branch DeepCRM ensemble."
        ),
        "architecture": {
            "filter_heights": [2, 2, 2],
            "feature_maps": 100,
            "dropout": 0.5,
            "classes": ["unreadable", "readable"],
        },
        "character_matrix": {
            **matrix_spec.to_dict(),
            "padding_value": -1,
            "encoding": "unicode_codepoint_0_255_else_unknown_256",
            "normalization": "codepoint_divided_by_256",
            "truncation": "right_and_bottom_at_training_matrix_dimensions",
        },
        "training": {
            "datasets": list(DATASET_PATHS),
            "selection": "top_and_bottom_25_percent_within_each_dataset",
            "middle_50_percent_excluded": True,
            "selection_details": selection,
            "sample_count": len(samples),
            "class_counts": {
                "unreadable": sum(label == 0 for _, label in samples),
                "readable": sum(label == 1 for _, label in samples),
            },
            "optimizer": "Adam",
            "learning_rate": args.learning_rate,
            "batch_size": args.batch_size,
            "epochs": args.epochs,
            "seed": args.seed,
            "paper_specified": [
                "optimizer",
                "learning_rate",
                "batch_size",
                "filter_heights",
                "feature_maps",
                "dropout",
                "extreme_quartile_labels",
            ],
            "reproduction_specified_because_release_is_incomplete": [
                "epochs",
                "seed",
                "character_dictionary",
                "character_normalization",
            ],
            "samples": [
                {
                    "task_id": item.task_id,
                    "label": label,
                    "readability_score": float(item.readability_score),
                    "source_sha256": item_source_sha256(item),
                }
                for item, label in samples
            ],
        },
        "cross_validation": cross_validation,
        "weights": {
            "file": weights_path.name,
            "sha256": hashlib.sha256(weights_path.read_bytes()).hexdigest(),
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
