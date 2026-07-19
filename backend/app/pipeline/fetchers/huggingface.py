import logging
from datetime import datetime, timezone

import httpx

from app.pipeline.normalizer import RawItem

logger = logging.getLogger(__name__)

HF_DAILY_PAPERS_URL = "https://huggingface.co/api/daily_papers"


def _parse_hf_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_huggingface_items(max_items: int = 30) -> list[RawItem]:
    items: list[RawItem] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(HF_DAILY_PAPERS_URL)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        logger.exception("Failed to fetch Hugging Face daily papers")
        return items

    papers = payload if isinstance(payload, list) else payload.get("papers", [])
    for entry in papers[:max_items]:
        paper = entry.get("paper", entry)
        paper_id = paper.get("id") or paper.get("arxivId") or paper.get("title")
        if not paper_id:
            continue

        title = (paper.get("title") or "Untitled paper").strip()
        snippet = paper.get("summary") or paper.get("abstract")
        authors = [author.get("name", "") for author in paper.get("authors", []) if author.get("name")]

        arxiv_id = paper.get("arxivId")
        paper_url = paper.get("url")
        if not paper_url and arxiv_id:
            paper_url = f"https://arxiv.org/abs/{arxiv_id}"
        if not paper_url:
            paper_url = f"https://huggingface.co/papers/{paper_id}"

        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None
        published_at = _parse_hf_date(paper.get("publishedAt") or entry.get("publishedAt"))

        items.append(
            RawItem(
                external_id=str(paper_id),
                title=title,
                snippet=snippet,
                authors=authors,
                source="huggingface",
                bucket="research",
                published_at=published_at or datetime.now(timezone.utc),
                paper_url=paper_url,
                pdf_url=pdf_url,
                code_url=paper.get("githubRepo") or paper.get("githubUrl"),
                read_more_url=paper_url,
            )
        )

    return items
