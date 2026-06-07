def classify_similarity(score: float) -> str:
    if score >= 95:
        return "High"
    if score >= 80:
        return "Suspicious"
    if score >= 60:
        return "Moderate"
    return "Low"


def highest_similarity_score(matches: list[dict]) -> float:
    if not matches:
        return 0.0
    return float(max(match.get("score", 0.0) for match in matches))


def strongest_match(matches: list[dict]) -> dict | None:
    if not matches:
        return None
    return max(matches, key=lambda match: float(match.get("score", 0.0)))
