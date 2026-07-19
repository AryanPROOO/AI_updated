from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResearchItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    title: str
    snippet: str | None
    authors: list[str] | None
    source: str
    bucket: str
    published_at: datetime | None
    topics: list[str]
    summary: str | None
    why_it_matters: str | None
    paper_url: str | None
    pdf_url: str | None
    code_url: str | None
    read_more_url: str | None
    thumbnail_url: str | None
    relevance_score: float
    freshness_score: float
    impact_score: float
    total_score: float
    is_favorite: bool
    created_at: datetime


class PipelineStatusOut(BaseModel):
    last_run_at: datetime | None
    items_fetched: int
    items_saved: int
    message: str


class StatsOut(BaseModel):
    total_items: int
    by_topic: dict[str, int]
    by_source: dict[str, int]


class DiscussionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str | None
    source: str
    source_url: str | None
    thumbnail_url: str | None
    author: str | None
    score: int
    num_comments: int
    topics: list[str]
    published_at: datetime | None
    created_at: datetime
