import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import DiscussionItem
from app.pipeline.fetchers.reddit import classify_discussion, fetch_reddit_discussions
from app.pipeline.fetchers.twitter import fetch_twitter_discussions

logger = logging.getLogger(__name__)

_last_run_at: datetime | None = None


def _cleanup_old_discussions(db: Session) -> None:
    # Keep items from the last 7 days for history
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    deleted = db.query(DiscussionItem).filter(DiscussionItem.published_at < cutoff).delete(synchronize_session=False)
    if deleted:
        logger.info("Cleaned up %d discussion items older than 7 days.", deleted)


def run_discussion_pipeline(db: Session) -> dict:
    global _last_run_at

    _cleanup_old_discussions(db)

    reddit_items = fetch_reddit_discussions()
    twitter_items = fetch_twitter_discussions(settings.twitter_bearer_token)

    all_items = reddit_items + twitter_items
    existing_ids = {row[0] for row in db.query(DiscussionItem.external_id).all() if row[0]}

    saved = 0
    for item in all_items:
        if item["external_id"] in existing_ids:
            continue

        topics = classify_discussion(item["title"], item.get("content"))

        record = DiscussionItem(
            external_id=item["external_id"],
            title=item["title"],
            content=item.get("content"),
            source=item["source"],
            source_url=item.get("source_url"),
            thumbnail_url=item.get("thumbnail_url"),
            author=item.get("author"),
            score=item.get("score", 0),
            num_comments=item.get("num_comments", 0),
            topics=topics,
            published_at=item.get("published_at"),
        )
        db.add(record)
        saved += 1

    try:
        db.commit()
    except Exception as e:
        logger.exception("Failed to save discussion items")
        db.rollback()
        return {"items_fetched": len(all_items), "items_saved": 0, "message": "Failed to save discussions"}

    _last_run_at = datetime.now(timezone.utc)
    logger.info(f"Discussion pipeline: fetched {len(all_items)}, saved {saved}")
    return {
        "items_fetched": len(all_items),
        "items_saved": saved,
        "message": f"Fetched {len(all_items)} discussions, saved {saved} new.",
    }


def get_discussion_items(
    db: Session,
    topic: str | None = None,
    search: str | None = None,
    sort: str = "comments",
    limit: int = 50,
) -> list[DiscussionItem]:
    query = db.query(DiscussionItem)

    if topic and topic != "All":
        query = query.filter(DiscussionItem.topics.contains([topic]))

    if search:
        query = query.filter(
            DiscussionItem.title.ilike(f"%{search}%")
            | DiscussionItem.content.ilike(f"%{search}%")
        )

    if sort == "score":
        query = query.order_by(DiscussionItem.score.desc())
    elif sort == "new":
        query = query.order_by(DiscussionItem.published_at.desc().nullslast())
    else:
        query = query.order_by(DiscussionItem.num_comments.desc())

    return query.limit(limit).all()


def get_discussion_status() -> dict:
    return {
        "last_run_at": _last_run_at,
    }
