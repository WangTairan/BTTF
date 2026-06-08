def normalize_scores(scores):
    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)
    spread = maximum - minimum

    if spread == 0:
        return [0.0 for _ in scores]

    normalized = []
    for score in scores:
        normalized.append((score - minimum) / spread)

    return normalized


if __name__ == "__main__":
    print(normalize_scores([10, 20, 30]))
