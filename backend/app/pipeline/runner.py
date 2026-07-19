import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import ResearchItem
from app.pipeline.classifier import classify_topics, relevance_score
from app.pipeline.dedup import content_hash, is_duplicate
from app.pipeline.fetchers.arxiv import fetch_arxiv_items
from app.pipeline.fetchers.github import fetch_github_trending_items
from app.pipeline.fetchers.huggingface import fetch_huggingface_items
from app.pipeline.fetchers.openalex import fetch_openalex_items
from app.pipeline.normalizer import RawItem
from app.pipeline.scorer import freshness_score, impact_score, total_score
from app.pipeline.summarizer import summarize_item
from app.pipeline.thumbnail import search_wikimedia_image

logger = logging.getLogger(__name__)

_last_run_at: datetime | None = None
_last_run_stats = {"items_fetched": 0, "items_saved": 0, "message": "Pipeline not run yet."}


@dataclass
class PipelineResult:
    items_fetched: int
    items_saved: int
    message: str


def get_pipeline_status() -> dict:
    return {
        "last_run_at": _last_run_at,
        "items_fetched": _last_run_stats["items_fetched"],
        "items_saved": _last_run_stats["items_saved"],
        "message": _last_run_stats["message"],
    }


def _save_item(db: Session, item: RawItem) -> ResearchItem | None:
    topics = classify_topics(item.title, item.snippet)
    summary, why = summarize_item(item, topics)
    rel = relevance_score(topics)
    fresh = freshness_score(item.published_at)
    impact = impact_score(item, topics)
    score = total_score(rel, fresh, impact)

    thumbnail_url = search_wikimedia_image(item.title, topics)

    record = ResearchItem(
        external_id=item.external_id,
        title=item.title,
        snippet=item.snippet,
        authors=item.authors,
        source=item.source,
        bucket=item.bucket,
        published_at=item.published_at,
        topics=topics,
        summary=summary,
        why_it_matters=why,
        paper_url=item.paper_url,
        pdf_url=item.pdf_url,
        code_url=item.code_url,
        read_more_url=item.read_more_url or item.paper_url,
        content_hash=content_hash(item),
        thumbnail_url=thumbnail_url,
        relevance_score=rel,
        freshness_score=fresh,
        impact_score=impact,
        total_score=score,
    )
    db.add(record)
    return record


def _cleanup_old_items(db: Session) -> None:
    # Keep items from the last 7 days for history
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    deleted = db.query(ResearchItem).filter(ResearchItem.published_at < cutoff).delete(synchronize_session=False)
    if deleted:
        logger.info("Cleaned up %d research items older than 7 days.", deleted)


def run_pipeline(db: Session) -> PipelineResult:
    global _last_run_at, _last_run_stats

    _cleanup_old_items(db)

    raw_items = fetch_arxiv_items() + fetch_huggingface_items() + fetch_github_trending_items() + fetch_openalex_items()
    existing_hashes = {row[0] for row in db.query(ResearchItem.content_hash).all() if row[0]}

    saved = 0
    for item in raw_items:
        if is_duplicate(existing_hashes, item):
            continue
        try:
            record = _save_item(db, item)
            if record:
                existing_hashes.add(record.content_hash)
                saved += 1
        except Exception:
            logger.exception("Failed to save item: %s", item.title)
            db.rollback()
            continue

    try:
        db.commit()
    except Exception:
        logger.exception("Failed to commit pipeline batch")
        db.rollback()
        return PipelineResult(
            items_fetched=len(raw_items),
            items_saved=0,
            message="Pipeline failed while saving to database.",
        )

    result = PipelineResult(
        items_fetched=len(raw_items),
        items_saved=saved,
        message=f"Fetched {len(raw_items)} items, saved {saved} new items.",
    )
    _last_run_at = datetime.now(timezone.utc)
    _last_run_stats = {
        "items_fetched": result.items_fetched,
        "items_saved": result.items_saved,
        "message": result.message,
    }
    logger.info(result.message)
    return result
