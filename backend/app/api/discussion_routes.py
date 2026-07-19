import html

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.pipeline.discussion_runner import (
    get_discussion_items,
    get_discussion_status,
    run_discussion_pipeline,
)
from app.schemas import DiscussionItemOut

router = APIRouter(prefix="/discussions")


def _decode_item(item):
    """Decode HTML entities in all text fields of a discussion item."""
    item.title = html.unescape(item.title)
    if item.content:
        item.content = html.unescape(item.content)
    if item.author:
        item.author = html.unescape(item.author)
    return item


@router.get("", response_model=list[DiscussionItemOut])
def list_discussions(
    topic: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort: str = Query(default="comments"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = get_discussion_items(db, topic, search, sort, limit)
    return [_decode_item(item) for item in items]


@router.get("/status")
def discussion_status():
    return get_discussion_status()


@router.post("/run")
def trigger_discussions(db: Session = Depends(get_db)):
    return run_discussion_pipeline(db)
