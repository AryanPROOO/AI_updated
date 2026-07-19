from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ResearchItem
from app.pipeline.runner import get_pipeline_status, run_pipeline
from app.pipeline.thumbnail import search_wikimedia_image
from app.schemas import PipelineStatusOut, ResearchItemOut, StatsOut

router = APIRouter()


class FavoriteRequest(BaseModel):
    favorite: bool


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/items", response_model=list[ResearchItemOut])
def list_items(
    topic: str | None = Query(default=None),
    source: str | None = Query(default=None),
    search: str | None = Query(default=None),
    custom_topics: list[str] | None = Query(default=None),
    is_favorite: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(ResearchItem).order_by(
        ResearchItem.total_score.desc(),
        ResearchItem.published_at.desc().nullslast(),
    )
    if topic:
        query = query.filter(ResearchItem.topics.contains([topic]))
    if source:
        query = query.filter(ResearchItem.source == source)
    if custom_topics:
        query = query.filter(ResearchItem.topics.overlap(custom_topics))
    if search:
        query = query.filter(
            ResearchItem.title.ilike(f"%{search}%")
            | ResearchItem.snippet.ilike(f"%{search}%")
            | ResearchItem.summary.ilike(f"%{search}%")
        )
    if is_favorite is not None:
        query = query.filter(ResearchItem.is_favorite == is_favorite)
    return query.limit(limit).all()


@router.get("/topics")
def list_topics():
    # Updated to include new topics
    return ["LLM", "Agents", "Edge AI", "Robotics", "Computer Vision", "Reinforcement Learning"]


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    items = db.query(ResearchItem).all()
    by_topic: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for item in items:
        by_source[item.source] = by_source.get(item.source, 0) + 1
        for topic in item.topics or []:
            by_topic[topic] = by_topic.get(topic, 0) + 1
    return StatsOut(total_items=len(items), by_topic=by_topic, by_source=by_source)


@router.post("/pipeline/run", response_model=PipelineStatusOut)
def trigger_pipeline(db: Session = Depends(get_db)):
    result = run_pipeline(db)
    status = get_pipeline_status()
    return PipelineStatusOut(
        last_run_at=status["last_run_at"],
        items_fetched=result.items_fetched,
        items_saved=result.items_saved,
        message=result.message,
    )


@router.post("/items/{item_id}/favorite", response_model=ResearchItemOut)
def favorite_item(item_id: int, body: FavoriteRequest, db: Session = Depends(get_db)):
    item = db.query(ResearchItem).filter(ResearchItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Research item not found")

    item.is_favorite = body.favorite
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/pipeline/status", response_model=PipelineStatusOut)
def pipeline_status():
    status = get_pipeline_status()
    return PipelineStatusOut(
        last_run_at=status["last_run_at"],
        items_fetched=status["items_fetched"],
        items_saved=status["items_saved"],
        message=status["message"],
    )


@router.post("/items/generate-thumbnails")
def generate_thumbnails(db: Session = Depends(get_db)):
    items = db.query(ResearchItem).filter(ResearchItem.thumbnail_url.is_(None)).limit(30).all()
    updated = 0
    for item in items:
        url = search_wikimedia_image(item.title, item.topics)
        if url:
            item.thumbnail_url = url
            updated += 1
        db.add(item)
    db.commit()
    return {"updated": updated, "total_without": len(items)}


@router.post("/items/regenerate-thumbnails")
def regenerate_thumbnails(db: Session = Depends(get_db)):
    items = db.query(ResearchItem).all()
    updated = 0
    for item in items:
        url = search_wikimedia_image(item.title, item.topics)
        if url:
            item.thumbnail_url = url
            updated += 1
        db.add(item)
    db.commit()
    return {"updated": updated, "total": len(items)}


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat_with_research(body: ChatRequest, db: Session = Depends(get_db)):
    """Search through research and discussions to answer user questions."""
    question = body.question.lower()
    keywords = [w for w in question.split() if len(w) > 2]

    # Search research items
    research_results = []
    for item in db.query(ResearchItem).all():
        score = 0
        text = f"{item.title} {item.snippet or ''} {item.summary or ''} {item.why_it_matters or ''}".lower()
        for kw in keywords:
            if kw in text:
                score += 1
        if score > 0:
            research_results.append({
                "type": "research",
                "title": item.title,
                "summary": item.summary or item.snippet or "",
                "why": item.why_it_matters or "",
                "topics": item.topics,
                "url": item.read_more_url or item.paper_url or "",
                "score": score,
                "source": item.source,
            })

    # Search discussion items
    from app.models import DiscussionItem
    discussion_results = []
    for item in db.query(DiscussionItem).all():
        score = 0
        text = f"{item.title} {item.content or ''}".lower()
        for kw in keywords:
            if kw in text:
                score += 1
        if score > 0:
            discussion_results.append({
                "type": "discussion",
                "title": item.title,
                "summary": (item.content or "")[:200],
                "url": item.source_url or "",
                "score": score,
                "source": item.source,
            })

    # Sort by relevance
    research_results.sort(key=lambda x: x["score"], reverse=True)
    discussion_results.sort(key=lambda x: x["score"], reverse=True)

    top_research = research_results[:5]
    top_discussions = discussion_results[:3]

    # Build response
    if not top_research and not top_discussions:
        return {
            "answer": f"I couldn't find specific papers about '{body.question}' in the current database. Try clicking 'Fetch Updates' to load the latest research, or rephrase your question.",
            "research": [],
            "discussions": [],
        }

    # Build a natural answer
    answer_parts = []
    if top_research:
        answer_parts.append(f"I found {len(top_research)} relevant research papers:")
        for i, r in enumerate(top_research[:3], 1):
            answer_parts.append(f"{i}. **{r['title']}** - {r['summary'][:100]}")

    if top_discussions:
        answer_parts.append(f"\nAnd {len(top_discussions)} related discussions:")
        for i, d in enumerate(top_discussions[:2], 1):
            answer_parts.append(f"{i}. **{d['title']}**")

    return {
        "answer": "\n".join(answer_parts),
        "research": top_research,
        "discussions": top_discussions,
    }
