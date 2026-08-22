from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np


WHOLE_CODE_CONTEXT_TYPE = "__WHOLE_CODE_CONTEXT__"
ANCHOR_DATASET = "__cognascore_anchor__"
MATH_ANCHOR_TASK = "math_context"
BUSINESS_ANCHOR_TASK = "business_context"
NON_MATH_ANCHOR_TASK = "non_math_context"
SHORT_IDENTIFIER_GATE_THRESHOLD = 0.03
SHORT_IDENTIFIER_CANDIDATES = frozenset(("a", "b", "c", "d", "e", "i", "j", "k", "m", "n", "x", "y", "z"))
DEFAULT_WHOLE_CODE_CONTEXT_MAX_CHARS = 6000
DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_CHARS = 3000
DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_OVERLAP = 300


@dataclass(frozen=True)
class CodeAnchor:
    name: str
    code: str


MATH_CONTEXT_ANCHORS = (
    CodeAnchor("arithmetic_update", "def compute_value(a, b):\n    c = a * b\n    d = c + a\n    return d"),
    CodeAnchor("gcd_modulo", "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a"),
    CodeAnchor("vector_dot", "def dot_product(xs, ys):\n    total = 0.0\n    for x, y in zip(xs, ys):\n        total += x * y\n    return total"),
    CodeAnchor("distance_formula", "def euclidean_distance(x1, y1, x2, y2):\n    dx = x2 - x1\n    dy = y2 - y1\n    return (dx * dx + dy * dy) ** 0.5"),
    CodeAnchor("statistics_mean", "def mean_center(values):\n    mean = sum(values) / len(values)\n    return [x - mean for x in values]"),
    CodeAnchor("matrix_multiply", "def matmul(a, b):\n    rows = len(a)\n    cols = len(b[0])\n    out = [[0 for _ in range(cols)] for _ in range(rows)]\n    for i in range(rows):\n        for j in range(cols):\n            for k in range(len(b)):\n                out[i][j] += a[i][k] * b[k][j]\n    return out"),
    CodeAnchor("quadratic_discriminant", "def roots(a, b, c):\n    d = b * b - 4 * a * c\n    r = d ** 0.5\n    return ((-b + r) / (2 * a), (-b - r) / (2 * a))"),
    CodeAnchor("numeric_clamp", "def clamp_value(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x"),
)


BUSINESS_CONTEXT_ANCHORS = (
    CodeAnchor("user_request", "def process_user(user, request):\n    name = user.get(\"name\")\n    result = request.strip()\n    return name + result"),
    CodeAnchor("order_total", "def build_order_summary(order):\n    customer = order.get(\"customer\")\n    status = order.get(\"status\")\n    return f\"{customer}:{status}\""),
    CodeAnchor("email_profile", "def normalize_profile(profile):\n    email = profile[\"email\"].lower().strip()\n    display_name = profile.get(\"display_name\", \"\")\n    return {\"email\": email, \"name\": display_name}"),
    CodeAnchor("session_auth", "def is_authorized(session, permission):\n    user = session.get(\"user\")\n    roles = user.get(\"roles\", [])\n    return permission in roles"),
    CodeAnchor("config_lookup", "def read_setting(config, key):\n    value = config.get(key)\n    if value is None:\n        return \"\"\n    return str(value).strip()"),
    CodeAnchor("short_vars_get_strip", "def extract(a, b):\n    c = a.get(\"name\", \"\")\n    return c + b.strip()"),
    CodeAnchor("short_vars_record_update", "def update_record(a, b, c):\n    a[\"email\"] = b.lower().strip()\n    a[\"status\"] = c.get(\"status\", \"active\")\n    return a"),
    CodeAnchor("invoice_line", "def format_invoice(invoice):\n    number = invoice.get(\"number\")\n    customer = invoice.get(\"customer_name\")\n    return f\"Invoice {number} for {customer}\""),
    CodeAnchor("short_vars_request_headers", "def read_header(a, b):\n    c = a.headers.get(b, \"\")\n    return c.strip().lower()"),
    CodeAnchor("cache_lookup", "def get_cached_value(cache, key, default):\n    if key in cache:\n        return cache[key]\n    return default"),
    CodeAnchor("invoice_total_arithmetic", "def compute_invoice_total(invoice):\n    price = invoice.get(\"price\", 0)\n    quantity = invoice.get(\"quantity\", 1)\n    tax = invoice.get(\"tax\", 0)\n    return price * quantity + tax"),
    CodeAnchor("discounted_order_arithmetic", "def apply_discount(order):\n    subtotal = order[\"unit_price\"] * order[\"quantity\"]\n    discount = order.get(\"discount\", 0)\n    return subtotal - discount"),
    CodeAnchor("short_vars_business_total", "def total(a, b):\n    c = a.get(\"price\", 0) * a.get(\"quantity\", 1)\n    return c + b.get(\"tax\", 0)"),
)


NON_MATH_CONTEXT_ANCHORS = (
    CodeAnchor("weak_passthrough", "def handle(a, b):\n    c = a\n    if c:\n        return b\n    return None"),
    CodeAnchor("weak_callback_loop", "def apply_all(items, fn):\n    out = []\n    for item in items:\n        out.append(fn(item))\n    return out"),
    CodeAnchor("weak_short_callback_loop", "def run(a, b):\n    c = []\n    for d in a:\n        c.append(b(d))\n    return c"),
    CodeAnchor("weak_branch_values", "def choose(a, b, c):\n    if a:\n        return b\n    return c"),
    CodeAnchor("weak_temp_result", "def transform(value):\n    temp = value\n    result = temp\n    return result"),
    CodeAnchor("weak_dict_fill", "def pack(a, b):\n    c = {}\n    c[\"first\"] = a\n    c[\"second\"] = b\n    return c"),
    CodeAnchor("weak_nested_calls", "def execute(a, b, c):\n    if b(a):\n        return c(a)\n    return a"),
    CodeAnchor("weak_item_merge", "def merge(data, item):\n    temp = data.copy()\n    temp[\"item\"] = item\n    return temp"),
)


def all_context_anchor_texts() -> list[str]:
    return [anchor.code for anchor in (*MATH_CONTEXT_ANCHORS, *BUSINESS_CONTEXT_ANCHORS, *NON_MATH_CONTEXT_ANCHORS)]


def whole_code_context_segments(
    code: str,
    *,
    segment_chars: int = DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_CHARS,
    overlap_chars: int = DEFAULT_WHOLE_CODE_CONTEXT_SEGMENT_OVERLAP,
    max_total_chars: int | None = DEFAULT_WHOLE_CODE_CONTEXT_MAX_CHARS,
) -> list[str]:
    text = code if max_total_chars is None or max_total_chars <= 0 else whole_code_context_text(code, max_chars=max_total_chars)
    if segment_chars <= 0 or len(text) <= segment_chars:
        return [text]
    step = max(segment_chars - max(overlap_chars, 0), 1)
    segments = []
    start = 0
    while start < len(text):
        segment = text[start:start + segment_chars]
        if segment:
            segments.append(segment)
        if start + segment_chars >= len(text):
            break
        start += step
    return segments


def whole_code_context_text(code: str, *, max_chars: int | None = DEFAULT_WHOLE_CODE_CONTEXT_MAX_CHARS) -> str:
    if max_chars is None or max_chars <= 0 or len(code) <= max_chars:
        return code
    if max_chars < 32:
        return code[:max_chars]
    marker = "\n\n# ... CognaScore semantic-context middle truncation ...\n\n"
    budget = max_chars - len(marker)
    if budget <= 0:
        return code[:max_chars]
    head_chars = budget // 2
    tail_chars = budget - head_chars
    return code[:head_chars] + marker + code[-tail_chars:]


def context_anchor_groups() -> dict[str, tuple[CodeAnchor, ...]]:
    return {
        MATH_ANCHOR_TASK: MATH_CONTEXT_ANCHORS,
        BUSINESS_ANCHOR_TASK: BUSINESS_CONTEXT_ANCHORS,
        NON_MATH_ANCHOR_TASK: NON_MATH_CONTEXT_ANCHORS,
    }


def semantic_context_feature_names() -> list[str]:
    return [
        "short_identifier_candidate_ratio",
        "short_identifier_math_gate_delta",
        "short_identifier_non_math_risk",
    ]


def semantic_context_features(
    *,
    code_vector: np.ndarray | None,
    code_segment_vectors: list[tuple[str, np.ndarray]] | None = None,
    identifier_lexemes: list[str],
    math_centroid: np.ndarray | None,
    business_centroid: np.ndarray | None,
    non_math_centroid: np.ndarray | None,
) -> dict[str, float]:
    ratio = short_identifier_candidate_ratio(identifier_lexemes)
    gate_delta = 0.0
    non_math_risk_delta = 0.0
    if ratio > 0.0 and math_centroid is not None and business_centroid is not None and non_math_centroid is not None:
        segment_vectors = code_segment_vectors or []
        candidate_segment_vectors = [
            vector for text, vector in segment_vectors
            if contains_short_identifier_candidate(text)
        ]
        if candidate_segment_vectors:
            deltas = [
                math_gate_delta(vector, math_centroid, business_centroid, non_math_centroid)
                for vector in candidate_segment_vectors
            ]
            gate_delta = min(deltas)
        elif code_vector is not None:
            gate_delta = math_gate_delta(code_vector, math_centroid, business_centroid, non_math_centroid)
    return {
        "short_identifier_candidate_ratio": ratio,
        "short_identifier_math_gate_delta": gate_delta,
        "short_identifier_non_math_risk": ratio * max(0.0, -gate_delta),
    }


def short_identifier_candidate_ratio(identifier_lexemes: list[str]) -> float:
    if not identifier_lexemes:
        return 0.0
    candidate_count = sum(1 for lexeme in identifier_lexemes if lexeme in SHORT_IDENTIFIER_CANDIDATES)
    return candidate_count / len(identifier_lexemes)


def contains_short_identifier_candidate(text: str) -> bool:
    for candidate in SHORT_IDENTIFIER_CANDIDATES:
        if re.search(rf"(?<![A-Za-z0-9_$]){re.escape(candidate)}(?![A-Za-z0-9_$])", text):
            return True
    return False


def math_gate_delta(
    vector: np.ndarray,
    math_centroid: np.ndarray,
    business_centroid: np.ndarray,
    non_math_centroid: np.ndarray,
) -> float:
    x = normalize_vector(vector)
    s_math = float(x @ math_centroid)
    s_business = float(x @ business_centroid)
    s_non_math = float(x @ non_math_centroid)
    return s_math - max(s_business, s_non_math)


def centroid(vectors: list[np.ndarray]) -> np.ndarray | None:
    if not vectors:
        return None
    normalized = np.stack([normalize_vector(vector) for vector in vectors]).astype(np.float64)
    return normalize_vector(np.mean(normalized, axis=0))


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    x = np.asarray(vector, dtype=np.float64)
    norm = float(math.sqrt(float(x @ x)))
    if norm <= 0.0:
        return np.zeros_like(x, dtype=np.float64)
    return x / norm
