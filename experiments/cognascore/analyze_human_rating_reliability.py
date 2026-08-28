"""Measure agreement and aggregate-score reliability in human-rated datasets.

The script intentionally distinguishes raw individual ratings from posterior
label probabilities.  Buse, Scalabrino, Dorn, and JetBrains retain individual
judgements.  Schnappinger retains only EM-aggregated class probabilities, so
only posterior certainty can be measured for that dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import median
from typing import Iterable, Sequence

import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "results/experiments/cognascore/human_rating_reliability"


def _finite_spearman(left: Sequence[float], right: Sequence[float]) -> float:
    value = float(spearmanr(left, right).statistic)
    return value if math.isfinite(value) else float("nan")


def krippendorff_alpha(
    item_ratings: Sequence[Sequence[float]], *, level: str
) -> float:
    """Krippendorff's alpha with missingness represented by absent ratings.

    ``interval`` uses squared numerical distance, appropriate when the 1--5
    scales are treated as equally spaced (as all three source datasets do when
    averaging ratings). ``nominal`` treats only equality/inequality as relevant.
    """

    usable = [np.asarray(values, dtype=float) for values in item_ratings if len(values) >= 2]
    pooled = np.concatenate(usable)
    total = int(sum(len(values) for values in usable))
    if total < 2:
        return float("nan")

    def disagreement(values: np.ndarray) -> float:
        if level == "interval":
            # Sum of all ordered squared pair distances, without constructing
            # the O(n^2) pairwise matrix.
            return float(
                2.0 * len(values) * np.square(values).sum()
                - 2.0 * np.square(values.sum())
            )
        if level == "nominal":
            _, counts = np.unique(values, return_counts=True)
            return float(len(values) ** 2 - np.square(counts).sum())
        raise ValueError(f"Unsupported measurement level: {level}")

    observed_numerator = sum(disagreement(values) / (len(values) - 1) for values in usable)
    observed = observed_numerator / total
    expected = (disagreement(pooled) / (total - 1)) / total
    return 1.0 - observed / expected if expected > 0 else float("nan")


def icc_two_way_random_absolute(matrix: np.ndarray) -> tuple[float, float]:
    """Return ICC(2,1) and ICC(2,k) for a complete items-by-raters matrix."""

    if np.isnan(matrix).any():
        raise ValueError("ICC(2) requires a complete rating matrix")
    n_items, n_raters = matrix.shape
    grand = float(matrix.mean())
    item_means = matrix.mean(axis=1)
    rater_means = matrix.mean(axis=0)
    ms_items = n_raters * float(np.square(item_means - grand).sum()) / (n_items - 1)
    ms_raters = n_items * float(np.square(rater_means - grand).sum()) / (n_raters - 1)
    residual = matrix - item_means[:, None] - rater_means[None, :] + grand
    ms_error = float(np.square(residual).sum()) / ((n_items - 1) * (n_raters - 1))
    single = (ms_items - ms_error) / (
        ms_items
        + (n_raters - 1) * ms_error
        + n_raters * (ms_raters - ms_error) / n_items
    )
    average = (ms_items - ms_error) / (
        ms_items + (ms_raters - ms_error) / n_items
    )
    return float(single), float(average)


def pairwise_rater_spearman(matrix: np.ndarray) -> dict[str, float]:
    values: list[float] = []
    for left in range(matrix.shape[1]):
        for right in range(left + 1, matrix.shape[1]):
            rho = _finite_spearman(matrix[:, left], matrix[:, right])
            if math.isfinite(rho):
                values.append(rho)
    return {
        "pair_count": len(values),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def split_half_reliability(
    item_ratings: Sequence[Sequence[float]], *, rounds: int, seed: int
) -> dict[str, float]:
    """Repeatedly split each item's votes, then correlate the two item means."""

    rng = np.random.default_rng(seed)
    usable = [np.asarray(values, dtype=float) for values in item_ratings if len(values) >= 2]
    raw: list[float] = []
    corrected: list[float] = []
    for _ in range(rounds):
        left_means: list[float] = []
        right_means: list[float] = []
        for values in usable:
            shuffled = rng.permutation(values)
            cut = len(shuffled) // 2
            left_means.append(float(shuffled[:cut].mean()))
            right_means.append(float(shuffled[cut:].mean()))
        rho = _finite_spearman(left_means, right_means)
        if not math.isfinite(rho):
            continue
        raw.append(rho)
        corrected.append(2.0 * rho / (1.0 + rho) if rho > -1 else -1.0)
    return {
        "rounds": len(raw),
        "raw_spearman_mean": float(np.mean(raw)),
        "raw_spearman_median": float(np.median(raw)),
        "spearman_brown_mean": float(np.mean(corrected)),
        "spearman_brown_median": float(np.median(corrected)),
        "spearman_brown_p05": float(np.quantile(corrected, 0.05)),
        "spearman_brown_p95": float(np.quantile(corrected, 0.95)),
    }


def split_half_complete_matrix_reliability(
    matrix: np.ndarray, *, rounds: int, seed: int
) -> dict[str, float]:
    """Split a complete crossed design into fixed groups of raters."""

    rng = np.random.default_rng(seed)
    raw: list[float] = []
    corrected: list[float] = []
    for _ in range(rounds):
        order = rng.permutation(matrix.shape[1])
        cut = len(order) // 2
        left = matrix[:, order[:cut]].mean(axis=1)
        right = matrix[:, order[cut:]].mean(axis=1)
        rho = _finite_spearman(left, right)
        if not math.isfinite(rho):
            continue
        raw.append(rho)
        corrected.append(2.0 * rho / (1.0 + rho) if rho > -1 else -1.0)
    return {
        "rounds": len(raw),
        "raw_spearman_mean": float(np.mean(raw)),
        "raw_spearman_median": float(np.median(raw)),
        "spearman_brown_mean": float(np.mean(corrected)),
        "spearman_brown_median": float(np.median(corrected)),
        "spearman_brown_p05": float(np.quantile(corrected, 0.05)),
        "spearman_brown_p95": float(np.quantile(corrected, 0.95)),
    }


def rating_summary(item_ratings: Sequence[Sequence[float]]) -> dict[str, float | int]:
    counts = [len(values) for values in item_ratings]
    return {
        "item_count": len(counts),
        "rating_count": sum(counts),
        "ratings_per_item_min": min(counts),
        "ratings_per_item_median": float(median(counts)),
        "ratings_per_item_max": max(counts),
    }


def weighted_cohen_kappa(
    left: Sequence[float], right: Sequence[float], *, quadratic: bool
) -> float:
    """Cohen's weighted kappa for two raters on the same ordinal scale."""

    categories = sorted(set(left) | set(right))
    indices = {value: index for index, value in enumerate(categories)}
    observed = np.zeros((len(categories), len(categories)), dtype=float)
    for first, second in zip(left, right, strict=True):
        observed[indices[first], indices[second]] += 1.0
    observed /= observed.sum()
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0))
    distance = np.abs(
        np.arange(len(categories))[:, None] - np.arange(len(categories))[None, :]
    ) / max(len(categories) - 1, 1)
    if quadratic:
        distance = np.square(distance)
    expected_disagreement = float((expected * distance).sum())
    observed_disagreement = float((observed * distance).sum())
    return 1.0 - observed_disagreement / expected_disagreement


def load_buse() -> tuple[list[list[float]], np.ndarray]:
    path = ROOT / "datasets/buse/raw/readability-votes.csv"
    people = np.asarray(
        [[float(value) for value in row[2:]] for row in csv.reader(path.open())],
        dtype=float,
    )
    matrix = people.T
    return [list(row) for row in matrix], matrix


def load_scalabrino() -> tuple[list[list[float]], np.ndarray]:
    path = ROOT / "datasets/scalabrino/dataset/scores.csv"
    rows = list(csv.reader(path.open()))[1:]
    people = np.asarray([[float(value) for value in row[1:]] for row in rows], dtype=float)
    matrix = people.T
    return [list(row) for row in matrix], matrix


def load_dorn() -> dict[str, list[list[float]]]:
    result: dict[str, list[list[float]]] = {}
    for language in ("java", "python", "cuda"):
        language_ratings: list[list[float]] = []
        path = ROOT / f"datasets/dorn/dataset/scores/{language}.csv"
        rows = list(csv.reader(path.open()))
        for column in range(1, max(map(len, rows))):
            ratings: list[float] = []
            for row in rows:
                if column < len(row) and row[column].strip():
                    ratings.append(float(row[column]))
            if ratings:
                language_ratings.append(ratings)
        result[language] = language_ratings
    return result


def load_jetbrains() -> list[list[float]]:
    # The released aggregate table contains four votes absent from raw_data.csv,
    # which is an event log rather than a clean response matrix.  Binary counts
    # retain everything required by the agreement measures used below.
    path = ROOT / "datasets/jetbrains/snippets_with_human_scores.csv"
    result: list[list[float]] = []
    for row in csv.DictReader(path.open()):
        readable = int(float(row["readable"]))
        unreadable = int(float(row["unreadable"]))
        result.append([1.0] * readable + [0.0] * unreadable)
    return result


def load_schnappinger_posteriors() -> list[list[float]]:
    path = ROOT / "datasets/schnappinger/labels.csv"
    result: list[list[float]] = []
    for row in csv.DictReader(path.open()):
        text = row["readability"].strip().strip("{}")
        values = [float(value) for value in text.split(",")]
        total = sum(values)
        result.append([value / total for value in values])
    return result


def load_mbjp() -> tuple[list[list[float]], np.ndarray]:
    metadata_path = ROOT / "datasets/mbjp_dev_dataset/human_ratings.csv"
    dataset_path = ROOT / "datasets/mbjp_dev_dataset/readability_dataset.json"
    dataset = {
        row["task_id"]: float(row["readability_score"])
        for row in json.loads(dataset_path.read_text())
    }
    rows = list(csv.DictReader(metadata_path.open()))
    metadata_ids = {row["task_id"] for row in rows}
    if metadata_ids != set(dataset):
        raise ValueError(
            "MBJP human-rating task IDs differ from readability_dataset.json: "
            f"missing={sorted(set(dataset) - metadata_ids)}, "
            f"extra={sorted(metadata_ids - set(dataset))}"
        )
    matrix: list[list[float]] = []
    for row in rows:
        first = float(row["rater_1_score"])
        second = float(row["rater_2_score"])
        stated_mean = float(row["mean_score"])
        computed_mean = (first + second) / 2.0
        if not math.isclose(computed_mean, stated_mean):
            raise ValueError(f"Incorrect stated MBJP mean for {row['task_id']}")
        if not math.isclose(stated_mean, dataset[row["task_id"]]):
            raise ValueError(
                f"MBJP mean disagrees with readability_score for {row['task_id']}"
            )
        matrix.append([first, second])
    array = np.asarray(matrix, dtype=float)
    return [list(row) for row in array], array


def continuous_report(
    item_ratings: list[list[float]], matrix: np.ndarray | None, *, rounds: int, seed: int
) -> dict[str, object]:
    report: dict[str, object] = rating_summary(item_ratings)
    report["scale"] = "1--5"
    report["krippendorff_alpha_interval"] = krippendorff_alpha(
        item_ratings, level="interval"
    )
    if matrix is not None:
        report["split_half_item_mean_reliability"] = (
            split_half_complete_matrix_reliability(matrix, rounds=rounds, seed=seed)
        )
        single, average = icc_two_way_random_absolute(matrix)
        report["icc_2_1"] = single
        report["icc_2_k"] = average
        report["pairwise_rater_spearman"] = pairwise_rater_spearman(matrix)
    else:
        report["split_half_item_mean_reliability"] = split_half_reliability(
            item_ratings, rounds=rounds, seed=seed
        )
    return report


def create_report(rounds: int, seed: int) -> dict[str, object]:
    buse_ratings, buse_matrix = load_buse()
    scalabrino_ratings, scalabrino_matrix = load_scalabrino()
    mbjp_ratings, mbjp_matrix = load_mbjp()
    dorn_by_language = load_dorn()
    dorn_ratings = [
        ratings
        for language_ratings in dorn_by_language.values()
        for ratings in language_ratings
    ]
    jetbrains_ratings = load_jetbrains()
    jet_majorities = [max(np.mean(values), 1.0 - np.mean(values)) for values in jetbrains_ratings]
    jet_agreement = [
        sum(value == other for index, value in enumerate(values) for other in values[index + 1 :])
        / (len(values) * (len(values) - 1) / 2)
        for values in jetbrains_ratings
    ]

    posteriors = np.asarray(load_schnappinger_posteriors(), dtype=float)
    log_posteriors = np.zeros_like(posteriors)
    np.log(posteriors, out=log_posteriors, where=posteriors > 0)
    normalized_entropy = -np.sum(posteriors * log_posteriors, axis=1) / math.log(
        posteriors.shape[1]
    )
    mbjp_report = continuous_report(
        mbjp_ratings, mbjp_matrix, rounds=rounds, seed=seed + 4
    )
    mbjp_report["exact_agreement_fraction"] = float(
        np.mean(mbjp_matrix[:, 0] == mbjp_matrix[:, 1])
    )
    mbjp_report["cohen_kappa_linear_weighted"] = weighted_cohen_kappa(
        mbjp_matrix[:, 0], mbjp_matrix[:, 1], quadratic=False
    )
    mbjp_report["cohen_kappa_quadratic_weighted"] = weighted_cohen_kappa(
        mbjp_matrix[:, 0], mbjp_matrix[:, 1], quadratic=True
    )

    return {
        "method_notes": {
            "continuous_ratings": (
                "Krippendorff alpha uses interval distance because source datasets average "
                "their 1--5 ratings. ICC(2,1)/(2,k) is reported only for complete crossed designs."
            ),
            "split_half": (
                "For complete crossed designs, raters are assigned to two fixed halves. For "
                "anonymous or aggregate votes, each item's votes are divided into two halves. "
                "The two item-mean vectors are correlated and Spearman--Brown corrected."
            ),
            "schnappinger": (
                "Only EM posterior class probabilities are available locally. These certainty "
                "statistics are not inter-rater agreement."
            ),
        },
        "buse": continuous_report(
            buse_ratings, buse_matrix, rounds=rounds, seed=seed
        ),
        "scalabrino": continuous_report(
            scalabrino_ratings, scalabrino_matrix, rounds=rounds, seed=seed + 1
        ),
        "mbjp": mbjp_report,
        "dorn": {
            **continuous_report(dorn_ratings, None, rounds=rounds, seed=seed + 2),
            "by_language": {
                language: continuous_report(
                    ratings, None, rounds=rounds, seed=seed + 20 + index
                )
                for index, (language, ratings) in enumerate(dorn_by_language.items())
            },
        },
        "jetbrains": {
            **rating_summary(jetbrains_ratings),
            "scale": "binary readable/unreadable",
            "krippendorff_alpha_nominal": krippendorff_alpha(
                jetbrains_ratings, level="nominal"
            ),
            "mean_pairwise_vote_agreement": float(np.mean(jet_agreement)),
            "mean_majority_fraction": float(np.mean(jet_majorities)),
            "median_majority_fraction": float(np.median(jet_majorities)),
            "unanimous_item_fraction": float(
                np.mean([len(set(values)) == 1 for values in jetbrains_ratings])
            ),
            "split_half_readable_fraction_reliability": split_half_reliability(
                jetbrains_ratings, rounds=rounds, seed=seed + 3
            ),
        },
        "schnappinger": {
            "item_count": int(len(posteriors)),
            "available_data": "EM posterior over four readability classes",
            "human_inter_rater_agreement_available": False,
            "mean_max_posterior": float(np.max(posteriors, axis=1).mean()),
            "median_max_posterior": float(np.median(np.max(posteriors, axis=1))),
            "mean_expected_same_class_probability": float(
                np.square(posteriors).sum(axis=1).mean()
            ),
            "mean_normalized_entropy": float(normalized_entropy.mean()),
            "mean_posterior_certainty_one_minus_entropy": float(
                1.0 - normalized_entropy.mean()
            ),
        },
        "not_human_rating_matrices": {
            "generated_readability_90": "Constructed dataset, not an individual human-rating matrix.",
            "java_progressive_obfuscation": "Constructed degradation levels, not human ratings.",
        },
    }


def write_summary_csv(report: dict[str, object], path: Path) -> None:
    rows = [
        {
            "dataset": "MBJP",
            "items": report["mbjp"]["item_count"],
            "ratings_per_item_median": report["mbjp"]["ratings_per_item_median"],
            "agreement_metric": "Krippendorff alpha (interval)",
            "agreement": report["mbjp"]["krippendorff_alpha_interval"],
            "aggregate_reliability": report["mbjp"]["icc_2_k"],
        },
        {
            "dataset": "Buse",
            "items": report["buse"]["item_count"],
            "ratings_per_item_median": report["buse"]["ratings_per_item_median"],
            "agreement_metric": "Krippendorff alpha (interval)",
            "agreement": report["buse"]["krippendorff_alpha_interval"],
            "aggregate_reliability": report["buse"]["split_half_item_mean_reliability"]["spearman_brown_mean"],
        },
        {
            "dataset": "Scalabrino",
            "items": report["scalabrino"]["item_count"],
            "ratings_per_item_median": report["scalabrino"]["ratings_per_item_median"],
            "agreement_metric": "Krippendorff alpha (interval)",
            "agreement": report["scalabrino"]["krippendorff_alpha_interval"],
            "aggregate_reliability": report["scalabrino"]["split_half_item_mean_reliability"]["spearman_brown_mean"],
        },
        {
            "dataset": "Dorn",
            "items": report["dorn"]["item_count"],
            "ratings_per_item_median": report["dorn"]["ratings_per_item_median"],
            "agreement_metric": "Krippendorff alpha (interval)",
            "agreement": report["dorn"]["krippendorff_alpha_interval"],
            "aggregate_reliability": report["dorn"]["split_half_item_mean_reliability"]["spearman_brown_mean"],
        },
        {
            "dataset": "JetBrains",
            "items": report["jetbrains"]["item_count"],
            "ratings_per_item_median": report["jetbrains"]["ratings_per_item_median"],
            "agreement_metric": "Krippendorff alpha (nominal)",
            "agreement": report["jetbrains"]["krippendorff_alpha_nominal"],
            "aggregate_reliability": report["jetbrains"]["split_half_readable_fraction_reliability"]["spearman_brown_mean"],
        },
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.rounds <= 0:
        parser.error("--rounds must be positive")

    report = create_report(args.rounds, args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "reliability.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    write_summary_csv(report, args.output / "summary.csv")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Wrote {args.output / 'reliability.json'}")
    print(f"Wrote {args.output / 'summary.csv'}")


if __name__ == "__main__":
    main()
