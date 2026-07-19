from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawItem:
    external_id: str
    title: str
    snippet: str | None
    authors: list[str] = field(default_factory=list)
    source: str = ""
    bucket: str = "research"
    published_at: datetime | None = None
    paper_url: str | None = None
    pdf_url: str | None = None
    code_url: str | None = None
    read_more_url: str | None = None
