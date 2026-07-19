import logging
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.pipeline.normalizer import RawItem

logger = logging.getLogger(__name__)

OPENALEX_API_URL = "https://api.openalex.org/works"

def fetch_openalex_items(max_items: int = 30) -> list[RawItem]:
    items: list[RawItem] = []
    # Example query: Fetch works related to AI, sorted by publication date descending
    # We can refine this query further based on specific needs (e.g., topics, authors)
    params: Dict[str, Any] = {
        "filter": "concepts.ids:c2497058",  # Filter for AI concept ID
        "sort": "publication_date:desc",
        "per_page": max_items,
        "select": "id,title,authorships,publication_date,abstract_inverted_index,primary_topic.display_name,host_organization.display_name"
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(OPENALEX_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as e:
        logger.error(f"HTTP Request failed for OpenAlex API: {e}")
        return items
    except Exception as e:
        logger.exception(f"Failed to fetch or parse OpenAlex data: {e}")
        return items

    results = data.get("results", [])
    for work in results[:max_items]:
        try:
            work_id = work.get("id")
            title = work.get("title", "Untitled Work").replace("\n", " ").strip()
            
            # Extract authors
            authors_data = work.get("authorships", [])
            authors = [author.get("author", {}).get("display_name", "Unknown Author") for author in authors_data]
            
            # Publication date
            pub_date_str = work.get("publication_date")
            published_at = datetime.strptime(pub_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) if pub_date_str else datetime.now(timezone.utc)
            
            # Snippet/Abstract - OpenAlex provides abstract_inverted_index which needs parsing
            # For simplicity, we'll use a placeholder or skip if not easily available.
            # A more robust solution would involve parsing the inverted index.
            snippet = work.get("abstract") or "Abstract not available in simple format." 
            # Trying to get a basic snippet if abstract is in inverted index
            if "abstract" not in work and work.get("abstract_inverted_index"):
                 snippet = "Abstract available via OpenAlex." # Placeholder

            # URLs
            paper_url = f"https://openalex.org/works/{work_id.split('/')[-1]}" if work_id else None
            
            # Topics/Primary Topic
            primary_topic = work.get("primary_topic", {}).get("display_name", "General AI")

            items.append(
                RawItem(
                    external_id=str(work_id),
                    title=title,
                    snippet=snippet,
                    authors=authors,
                    source="openalex",
                    bucket="research",
                    published_at=published_at,
                    paper_url=paper_url,
                    pdf_url=None, # OpenAlex links to the work page, not directly PDF
                    code_url=None, # Code URL not directly available from this endpoint
                    read_more_url=paper_url,
                    # We can add topics here if needed, based on 'concepts' field if available
                    # For now, using primary_topic for classification later
                    topics=[primary_topic] if primary_topic else ["General AI"]
                )
            )
        except Exception as e:
            logger.error(f"Failed to parse OpenAlex work item: {e}")
            continue
            
    return items

