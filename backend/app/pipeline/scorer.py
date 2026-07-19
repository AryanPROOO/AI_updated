from datetime import datetime, timezone

from app.pipeline.normalizer import RawItem


def freshness_score(published_at: datetime | None) -> float:
    if not published_at:
        return 0.4
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 86400)
    if age_days <= 1:
        return 1.0
    if age_days <= 3:
        return 0.85
    if age_days <= 7:
        return 0.65
    if age_days <= 14:
        return 0.45
    return 0.25


def impact_score(item: RawItem, topics: list[str]) -> float:
    score = 0.35
    if item.code_url:
        score += 0.25
    if item.source == "huggingface":
        score += 0.15
    if len(topics) > 1:
        score += 0.1
    if item.pdf_url:
        score += 0.1
    return min(1.0, score)


def total_score(relevance: float, freshness: float, impact: float) -> float:
    return round(relevance * 0.45 + freshness * 0.35 + impact * 0.2, 4)
