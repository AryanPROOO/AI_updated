import logging
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List

import feedparser
import httpx

from app.config import settings
from app.pipeline.normalizer import RawItem

logger = logging.getLogger(__name__)


def _parse_date(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    if getattr(entry, "published", None):
        try:
            return parsedate_to_datetime(entry.published)
        except (TypeError, ValueError):
            pass
    return None


def _extract_authors(entry) -> list[str]:
    if hasattr(entry, "authors") and entry.authors:
        return [author.get("name", "").strip() for author in entry.authors if author.get("name")]
    if getattr(entry, "author", None):
        return [entry.author.strip()]
    return []


def _extract_arxiv_links(entry) -> tuple[str | None, str | None]:
    paper_url = getattr(entry, "link", None)
    pdf_url = None
    for link in getattr(entry, "links", []) or []:
        href = link.get("href")
        if href and "pdf" in href:
            pdf_url = href
            break
    if paper_url and not pdf_url:
        match = re.search(r"arxiv\.org/abs/([^/?#]+)", paper_url)
        if match:
            pdf_url = f"https://arxiv.org/pdf/{match.group(1)}.pdf"
    return paper_url, pdf_url


def _fetch_arxiv_api(categories: list[str], max_items: int) -> list[RawItem]:
    per_category = max(5, max_items // max(len(categories), 1))
    query = "+OR+".join(f"cat:{category}" for category in categories)
    
    # Extended search with additional keywords for better discovery
    search_terms = [
        query,
        f"({query}) AND (machine learning OR deep learning OR neural network OR AI)",
        f"({query}) AND (large language model OR transformer OR llm OR gpt)",
    ]
    
    items: list[RawItem] = []
    seen_ids = set()
    
    for search_query in search_terms:
        api_url = (
            "https://export.arxiv.org/api/query"
            f"?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results={per_category}"
        )
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(api_url)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
                
                for entry in parsed.entries:
                    # Avoid duplicates from different search queries
                    entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                    if entry_id and entry_id in seen_ids:
                        continue
                    if entry_id:
                        seen_ids.add(entry_id)
                    
                    paper_url = getattr(entry, "link", None)
                    pdf_url = None
                    for link in getattr(entry, "links", []) or []:
                        if link.get("type") == "application/pdf":
                            pdf_url = link.get("href")
                            break
                    if paper_url and not pdf_url:
                        match = re.search(r"arxiv\.org/abs/([^/?#]+)", paper_url)
                        if match:
                            pdf_url = f"https://arxiv.org/pdf/{match.group(1)}.pdf"
                    
                    external_id = entry_id or entry.title
                    items.append(
                        RawItem(
                            external_id=str(external_id),
                            title=entry.title.replace("\n", " ").strip(),
                            snippet=getattr(entry, "summary", None),
                            authors=_extract_authors(entry),
                            source="arxiv",
                            bucket="research",
                            published_at=_parse_date(entry),
                            paper_url=paper_url,
                            pdf_url=pdf_url,
                            read_more_url=paper_url,
                        )
                    )
        except httpx.RequestError as e:
            logger.error(f"HTTP Request failed for arXiv API query '{search_query}': {e}")
        except Exception:
            logger.exception(f"Failed to process arXiv API results for query '{search_query}'")
            
    return items


def fetch_arxiv_items(max_items: int = 40) -> list[RawItem]:
    categories = [c.strip() for c in settings.arxiv_categories.split(",") if c.strip()]
    items: list[RawItem] = []

    for category in categories:
        feed_url = f"https://export.arxiv.org/rss/{category}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(feed_url)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
        except httpx.RequestError as e:
            logger.error(f"HTTP Request failed for arXiv feed '{feed_url}': {e}")
            continue
        except Exception:
            logger.exception(f"Failed to fetch arXiv feed for {category}")
            continue

        for entry in parsed.entries[: max_items // max(len(categories), 1)]:
            paper_url, pdf_url = _extract_arxiv_links(entry)
            external_id = getattr(entry, "id", None) or paper_url or entry.title
            items.append(
                RawItem(
                    external_id=str(external_id),
                    title=entry.title.strip(),
                    snippet=getattr(entry, "summary", None),
                    authors=_extract_authors(entry),
                    source="arxiv",
                    bucket="research",
                    published_at=_parse_date(entry),
                    paper_url=paper_url,
                    pdf_url=pdf_url,
                    read_more_url=paper_url,
                )
            )

    if not items:
        logger.info("arXiv RSS empty (often on weekends) - falling back to arXiv API.")
        items.extend(_fetch_arxiv_api(categories, max_items))

    return items

