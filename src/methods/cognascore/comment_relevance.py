"""Model-specific calibration for comment-to-code semantic alignment."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from statistics import mean, pstdev
from typing import TYPE_CHECKING, Any, Sequence

import numpy as np

if TYPE_CHECKING:
    from .embedding_cache import EmbeddingCache


COMMENT_RELEVANCE_ANCHOR_DATASET = "__cognascore_comment_relevance_anchor__"
COMMENT_RELEVANCE_ANCHOR_VERSION = 1
COMMENT_RELEVANCE_CODE_PREFIX = "CODE__"
COMMENT_RELEVANCE_POSITIVE_TYPE = "RELEVANT_COMMENT"
COMMENT_RELEVANCE_NEGATIVE_TYPE = "IRRELEVANT_COMMENT"


@dataclass(frozen=True)
class CommentRelevanceAnchor:
    name: str
    language: str
    code: str
    relevant_comment: str


# These examples are calibration resources, not readability training data. The
# negative for each item is deterministically borrowed from the next item in
# the same language, so negatives remain realistic technical comments.
COMMENT_RELEVANCE_ANCHORS = (
    CommentRelevanceAnchor(
        "java_binary_search", "java",
        "int find(int[] values, int target) { int lo = 0, hi = values.length - 1; while (lo <= hi) { int mid = (lo + hi) >>> 1; if (values[mid] < target) lo = mid + 1; else if (values[mid] > target) hi = mid - 1; else return mid; } return -1; }",
        "Move the search boundary according to how the midpoint compares with the target.",
    ),
    CommentRelevanceAnchor(
        "java_cache_lookup", "java",
        "String lookup(Map<String, String> cache, String key) { if (cache.containsKey(key)) return cache.get(key); return null; }",
        "Return the cached value when the requested key is present.",
    ),
    CommentRelevanceAnchor(
        "java_retry_loop", "java",
        "Response send(Request request) { for (int attempt = 0; attempt < 3; attempt++) { Response response = client.send(request); if (response.isSuccessful()) return response; } throw new IllegalStateException(); }",
        "Retry the request up to three times and stop after the first successful response.",
    ),
    CommentRelevanceAnchor(
        "java_running_total", "java",
        "long sum(List<Integer> values) { long total = 0; for (int value : values) total += value; return total; }",
        "Accumulate every input value into the running total.",
    ),
    CommentRelevanceAnchor(
        "java_filter_users", "java",
        "List<User> active(List<User> users) { List<User> result = new ArrayList<>(); for (User user : users) if (user.isActive()) result.add(user); return result; }",
        "Keep only users whose active flag is set.",
    ),
    CommentRelevanceAnchor(
        "java_parse_port", "java",
        "int parsePort(String text) { int port = Integer.parseInt(text); if (port < 1 || port > 65535) throw new IllegalArgumentException(); return port; }",
        "Reject parsed port numbers outside the valid network port range.",
    ),
    CommentRelevanceAnchor(
        "java_close_resources", "java",
        "void closeAll(List<Closeable> resources) throws IOException { IOException failure = null; for (Closeable resource : resources) { try { resource.close(); } catch (IOException error) { failure = error; } } if (failure != null) throw failure; }",
        "Close every resource and rethrow the last I/O failure after cleanup.",
    ),
    CommentRelevanceAnchor(
        "java_normalize_email", "java",
        "String normalizeEmail(String email) { return email.trim().toLowerCase(Locale.ROOT); }",
        "Remove surrounding whitespace and normalize the email address to lower case.",
    ),
    CommentRelevanceAnchor(
        "python_group_counts", "python",
        "def count_groups(items):\n    counts = {}\n    for item in items:\n        counts[item.group] = counts.get(item.group, 0) + 1\n    return counts",
        "Count how many items belong to each group.",
    ),
    CommentRelevanceAnchor(
        "python_safe_divide", "python",
        "def safe_divide(total, count):\n    if count == 0:\n        return 0.0\n    return total / count",
        "Avoid division by zero when no values were counted.",
    ),
    CommentRelevanceAnchor(
        "python_merge_settings", "python",
        "def merge_settings(defaults, overrides):\n    result = defaults.copy()\n    result.update(overrides)\n    return result",
        "Apply explicit overrides on top of the default settings.",
    ),
    CommentRelevanceAnchor(
        "python_read_chunks", "python",
        "def read_chunks(stream, size):\n    while True:\n        block = stream.read(size)\n        if not block:\n            break\n        yield block",
        "Yield fixed-size blocks until the input stream is exhausted.",
    ),
    CommentRelevanceAnchor(
        "python_clamp", "python",
        "def clamp(value, lower, upper):\n    return max(lower, min(value, upper))",
        "Constrain the value to the inclusive lower and upper bounds.",
    ),
    CommentRelevanceAnchor(
        "python_unique_order", "python",
        "def unique_in_order(values):\n    seen = set()\n    result = []\n    for value in values:\n        if value not in seen:\n            seen.add(value)\n            result.append(value)\n    return result",
        "Remove duplicates while preserving the first occurrence order.",
    ),
    CommentRelevanceAnchor(
        "python_expired_sessions", "python",
        "def expired_sessions(sessions, now):\n    return [session for session in sessions if session.expires_at <= now]",
        "Select sessions whose expiration time has already been reached.",
    ),
    CommentRelevanceAnchor(
        "python_path_extension", "python",
        "def extension(path):\n    name = path.rsplit('/', 1)[-1]\n    if '.' not in name:\n        return ''\n    return name.rsplit('.', 1)[-1].lower()",
        "Extract and normalize the final suffix from the file name.",
    ),
    CommentRelevanceAnchor(
        "javascript_debounce", "javascript",
        "function debounce(fn, delay) { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); }; }",
        "Cancel the previous timer so only the most recent call is delivered.",
    ),
    CommentRelevanceAnchor(
        "javascript_index_by_id", "javascript",
        "function indexById(records) { const index = new Map(); for (const record of records) index.set(record.id, record); return index; }",
        "Build a lookup table from record identifiers to records.",
    ),
    CommentRelevanceAnchor(
        "javascript_fetch_json", "javascript",
        "async function fetchJson(url) { const response = await fetch(url); if (!response.ok) throw new Error(response.statusText); return response.json(); }",
        "Reject unsuccessful HTTP responses before decoding the JSON body.",
    ),
    CommentRelevanceAnchor(
        "javascript_flatten", "javascript",
        "function flatten(groups) { const result = []; for (const group of groups) result.push(...group); return result; }",
        "Append every group into one flat result array.",
    ),
    CommentRelevanceAnchor(
        "javascript_toggle", "javascript",
        "function toggle(selected, key) { const next = new Set(selected); if (next.has(key)) next.delete(key); else next.add(key); return next; }",
        "Remove an existing key or add it when it is not selected.",
    ),
    CommentRelevanceAnchor(
        "javascript_escape_html", "javascript",
        "function escapeHtml(text) { return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;'); }",
        "Replace markup delimiters with their HTML entity representations.",
    ),
    CommentRelevanceAnchor(
        "javascript_partition", "javascript",
        "function partition(values, predicate) { const yes = [], no = []; for (const value of values) (predicate(value) ? yes : no).push(value); return [yes, no]; }",
        "Split the values according to whether they satisfy the predicate.",
    ),
    CommentRelevanceAnchor(
        "javascript_page_count", "javascript",
        "function pageCount(total, pageSize) { if (pageSize <= 0) throw new RangeError('pageSize'); return Math.ceil(total / pageSize); }",
        "Round up the division to include a final partially filled page.",
    ),
)


@dataclass(frozen=True)
class CommentRelevanceCalibration:
    threshold: float
    anchor_version: int
    anchor_sha256: str
    sample_count: int
    relevant_mean: float
    irrelevant_mean: float
    calibration_balanced_accuracy: float
    leave_one_anchor_out_balanced_accuracy: float
    leave_one_anchor_out_threshold_mean: float
    leave_one_anchor_out_threshold_std: float

    def as_metadata(self) -> dict[str, Any]:
        return asdict(self)


def comment_embedding_text(comment: str) -> str:
    normalized = re.sub(r"\s+", "_", comment.strip())
    return f"comment_{normalized}"


def negative_comment_for(anchor: CommentRelevanceAnchor) -> str:
    same_language = [item for item in COMMENT_RELEVANCE_ANCHORS if item.language == anchor.language]
    index = same_language.index(anchor)
    return same_language[(index + 1) % len(same_language)].relevant_comment


def comment_relevance_anchor_sha256() -> str:
    payload = {
        "version": COMMENT_RELEVANCE_ANCHOR_VERSION,
        "negative_rule": "next_anchor_within_language",
        "anchors": [asdict(anchor) for anchor in COMMENT_RELEVANCE_ANCHORS],
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def calibrate_comment_relevance(cache: EmbeddingCache) -> CommentRelevanceCalibration:
    samples: list[tuple[str, int, float]] = []
    missing: list[str] = []
    for anchor in COMMENT_RELEVANCE_ANCHORS:
        rows = cache.task_vectors(COMMENT_RELEVANCE_ANCHOR_DATASET, anchor.name)
        code_rows = [row for row in rows if row[0].startswith(COMMENT_RELEVANCE_CODE_PREFIX)]
        positive_rows = [row for row in rows if row[0] == COMMENT_RELEVANCE_POSITIVE_TYPE]
        negative_rows = [row for row in rows if row[0] == COMMENT_RELEVANCE_NEGATIVE_TYPE]
        if not code_rows or len(positive_rows) != 1 or len(negative_rows) != 1:
            missing.append(anchor.name)
            continue
        code_matrix = normalized_code_matrix(code_rows)
        samples.append((anchor.name, 1, maximum_cosine_to_code(positive_rows[0][3], code_matrix)))
        samples.append((anchor.name, 0, maximum_cosine_to_code(negative_rows[0][3], code_matrix)))
    if missing:
        raise ValueError(
            "Missing comment-relevance calibration embeddings; run the embeddings "
            f"runner first. Missing anchors: {', '.join(missing[:10])}"
        )

    labels = np.asarray([label for _, label, _ in samples], dtype=int)
    scores = np.asarray([score for _, _, score in samples], dtype=float)
    threshold, balanced_accuracy = select_balanced_threshold(labels, scores)
    held_out_predictions: list[int] = []
    held_out_labels: list[int] = []
    fold_thresholds: list[float] = []
    for anchor in COMMENT_RELEVANCE_ANCHORS:
        train = np.asarray([name != anchor.name for name, _, _ in samples], dtype=bool)
        test = ~train
        fold_threshold, _ = select_balanced_threshold(labels[train], scores[train])
        fold_thresholds.append(fold_threshold)
        held_out_labels.extend(labels[test].tolist())
        held_out_predictions.extend((scores[test] >= fold_threshold).astype(int).tolist())
    return CommentRelevanceCalibration(
        threshold=threshold,
        anchor_version=COMMENT_RELEVANCE_ANCHOR_VERSION,
        anchor_sha256=comment_relevance_anchor_sha256(),
        sample_count=len(samples),
        relevant_mean=float(np.mean(scores[labels == 1])),
        irrelevant_mean=float(np.mean(scores[labels == 0])),
        calibration_balanced_accuracy=balanced_accuracy,
        leave_one_anchor_out_balanced_accuracy=balanced_accuracy_from_predictions(
            np.asarray(held_out_labels), np.asarray(held_out_predictions)
        ),
        leave_one_anchor_out_threshold_mean=float(mean(fold_thresholds)),
        leave_one_anchor_out_threshold_std=float(pstdev(fold_thresholds)),
    )


def normalized_code_matrix(
    rows: Sequence[tuple[str, str, int, np.ndarray]],
) -> np.ndarray:
    if not rows:
        raise ValueError("Cannot compute comment alignment without code embeddings")
    return np.stack([normalize_vector(row[3]) for row in rows])


def maximum_cosine_to_code(vector: np.ndarray, code_matrix: np.ndarray) -> float:
    return float(np.max(code_matrix @ normalize_vector(vector)))


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    array = np.asarray(vector, dtype=np.float64)
    norm = float(math.sqrt(float(array @ array)))
    return array / norm if norm > 0 else np.zeros_like(array)


def select_balanced_threshold(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    unique = np.unique(scores)
    candidates = [float(np.nextafter(unique[-1], np.inf))]
    candidates.extend(float((left + right) / 2.0) for left, right in zip(unique[:-1], unique[1:]))
    candidates.append(float(np.nextafter(unique[0], -np.inf)))
    evaluated = [
        (threshold, balanced_accuracy_from_predictions(labels, scores >= threshold))
        for threshold in candidates
    ]
    best = max(value for _, value in evaluated)
    optimal = [threshold for threshold, value in evaluated if math.isclose(value, best)]
    return float(np.median(optimal)), float(best)


def balanced_accuracy_from_predictions(labels: np.ndarray, predictions: np.ndarray) -> float:
    positive = labels == 1
    negative = labels == 0
    if not positive.any() or not negative.any():
        raise ValueError("Balanced accuracy requires both calibration labels")
    true_positive_rate = float(np.mean(predictions[positive] == 1))
    true_negative_rate = float(np.mean(predictions[negative] == 0))
    return (true_positive_rate + true_negative_rate) / 2.0
