import hashlib
import re
from urllib.parse import urlparse

from app.pipeline.normalizer import RawItem


def _normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_arxiv_id(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url, re.I)
    if match:
        return match.group(1).split("v")[0]
    return None


def content_hash(item: RawItem) -> str:
    arxiv_id = _extract_arxiv_id(item.paper_url) or _extract_arxiv_id(item.pdf_url)
    if arxiv_id:
        key = f"arxiv:{arxiv_id}"
    else:
        key = f"{item.source}:{_normalize_title(item.title)}"
    return hashlib.sha256(key.encode()).hexdigest()


def is_duplicate(existing_hashes: set[str], item: RawItem) -> bool:
    return content_hash(item) in existing_hashes
