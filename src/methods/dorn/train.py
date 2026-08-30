from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np
from scipy.io import arff
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ARFF_URL = (
    "https://dibt-research.unimol.it/report/readability/files/"
    "DATASET_DORN_EXTENSION.arff"
)
ARFF_SHA256 = "0ddfa25b7267d1fb0d329789a1756bba8abd0dc600d7b448c89a5579567621e4"
DEFAULT_ARFF = Path("artifacts/baselines/dorn/DATASET_DORN_EXTENSION.arff")
DEFAULT_MODEL = Path("frozen_models/dorn_retrained/model.json")
SELECTED_FEATURE_COUNT = 7
MIN_FINITE_COVERAGE = 0.8
RANDOM_SEED = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the paper-aligned Dorn readability baseline."
    )
    parser.add_argument("--arff", type=Path, default=DEFAULT_ARFF)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--force-download", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_arff(args.arff, force=args.force_download)
    all_names, all_matrix, labels = load_dorn_arff(args.arff)
    finite_coverage = np.isfinite(all_matrix).mean(axis=0)
    eligible_indices = np.flatnonzero(finite_coverage >= MIN_FINITE_COVERAGE)
    names = [all_names[index] for index in eligible_indices]
    matrix = all_matrix[:, eligible_indices]
    folds = StratifiedKFold(n_splits=10, shuffle=True, random_state=RANDOM_SEED)
    estimator = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(C=1e8, max_iter=5000, random_state=RANDOM_SEED),
    )
    selected_indices = forward_wrapper_selection(
        estimator,
        matrix,
        labels,
        folds,
        count=SELECTED_FEATURE_COUNT,
    )
    selected_names = [names[index] for index in selected_indices]
    selected_matrix = matrix[:, selected_indices]

    imputer = SimpleImputer(strategy="median")
    imputed = imputer.fit_transform(selected_matrix)
    scaler = StandardScaler()
    standardized = scaler.fit_transform(imputed)
    classifier = LogisticRegression(
        C=1e8,
        max_iter=5000,
        random_state=RANDOM_SEED,
    )
    classifier.fit(standardized, labels)
    cv_accuracy = float(cross_val_score(estimator, selected_matrix, labels, cv=folds).mean())

    payload = {
        "name": "Dorn (retrained)",
        "protocol": (
            "Scalabrino-released Dorn feature implementation; >=80% finite-coverage "
            "filter; seven-feature forward wrapper selection; logistic regression "
            "trained on the public Dorn ARFF"
        ),
        "source_arff_url": ARFF_URL,
        "source_arff_sha256": ARFF_SHA256,
        "training_rows": int(matrix.shape[0]),
        "candidate_feature_count": len(all_names),
        "eligible_feature_count": len(names),
        "minimum_finite_coverage": MIN_FINITE_COVERAGE,
        "selected_feature_count": len(selected_names),
        "selected_features": selected_names,
        "selection_cv_folds": 10,
        "wrapper_objective_accuracy": cv_accuracy,
        "random_seed": RANDOM_SEED,
        "imputation_medians": imputer.statistics_.tolist(),
        "standardization_means": scaler.mean_.tolist(),
        "standardization_scales": scaler.scale_.tolist(),
        "coefficients": classifier.coef_[0].tolist(),
        "intercept": float(classifier.intercept_[0]),
        "positive_class": "Readable=1",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)
    print(f"Wrote {args.output}", flush=True)


def ensure_arff(path: Path, force: bool) -> None:
    if force or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {ARFF_URL}", flush=True)
        urllib.request.urlretrieve(ARFF_URL, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != ARFF_SHA256:
        raise ValueError(
            f"Unexpected Dorn ARFF checksum for {path}: {digest}; expected {ARFF_SHA256}"
        )


def load_dorn_arff(path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    rows, _ = arff.loadarff(path)
    names = [name for name in rows.dtype.names if name.startswith("Dorn-")]
    if len(names) != 59:
        raise ValueError(f"Expected 59 Dorn features in {path}, found {len(names)}")
    matrix = np.column_stack([np.asarray(rows[name], dtype=float) for name in names])
    labels = np.asarray(
        [
            int(value.decode("ascii") if isinstance(value, bytes) else value)
            for value in rows["Readable"]
        ],
        dtype=int,
    )
    return names, matrix, labels


def forward_wrapper_selection(
    estimator,
    matrix: np.ndarray,
    labels: np.ndarray,
    folds: StratifiedKFold,
    count: int,
) -> np.ndarray:
    """Greedy wrapper selection while fitting imputation inside every CV fold."""
    selected: list[int] = []
    remaining = list(range(matrix.shape[1]))
    for step in range(count):
        scored: list[tuple[float, int]] = []
        for candidate in remaining:
            subset = selected + [candidate]
            accuracy = float(
                cross_val_score(
                    estimator,
                    matrix[:, subset],
                    labels,
                    cv=folds,
                    scoring="accuracy",
                    n_jobs=1,
                ).mean()
            )
            scored.append((accuracy, candidate))
        best_accuracy, best_candidate = max(scored, key=lambda row: (row[0], -row[1]))
        selected.append(best_candidate)
        remaining.remove(best_candidate)
        print(
            f"Wrapper step {step + 1}/{count}: feature={best_candidate}, "
            f"CV accuracy={best_accuracy:.6f}",
            flush=True,
        )
    return np.asarray(selected, dtype=int)


if __name__ == "__main__":
    main()
