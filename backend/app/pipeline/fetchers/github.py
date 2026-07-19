import logging
import re
from datetime import datetime, timezone
from typing import List

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.pipeline.normalizer import RawItem

logger = logging.getLogger(__name__)

GITHUB_TRENDING_URL = "https://github.com/trending"

def fetch_github_trending_items(max_items: int = 20) -> list[RawItem]:
    items: list[RawItem] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(GITHUB_TRENDING_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logger.exception(f"Failed to fetch GitHub trending page: {e}")
        return items

    articles = soup.find_all("article", class_="Box-row")

    for article in articles[:max_items]:
        try:
            title_tag = article.find("h2", class_="h3")
            title = title_tag.text.strip().replace("\n", " ").replace(" ", "") if title_tag else "Untitled Repository"
            
            # Extract owner and repo name for URL generation
            repo_link_tag = title_tag.find("a") if title_tag else None
            repo_path = repo_link_tag['href'] if repo_link_tag else None

            full_title = title.replace("Trending/", "").strip()
            
            # Description
            description_tag = article.find("p", class_="col-9")
            description = description_tag.text.strip() if description_tag else "No description provided."

            # Stars and language
            star_tag = article.find("a", href=lambda href: href and "/stargazers" in href)
            stars = star_tag.text.strip().replace(",", "") if star_tag else "0"
            
            language_tag = article.find("span", itemprop="programmingLanguage")
            language = language_tag.text.strip() if language_tag else "N/A"

            # Construct URL
            repo_url = f"https://github.com{repo_path}" if repo_path else None

            # Approximate published date (trending page doesn't provide exact dates easily)
            # We'll use current date as a placeholder, as trending implies recent activity
            published_at = datetime.now(timezone.utc)

            items.append(
                RawItem(
                    external_id=repo_url or title, # Use URL as ID if available
                    title=full_title,
                    snippet=f"{description} | Language: {language} | Stars: {stars}",
                    authors=["GitHub Trending"], # Indicate source broadly
                    source="github_trending",
                    bucket="research",
                    published_at=published_at,
                    paper_url=repo_url, # Use repo URL as paper URL
                    pdf_url=None, # No PDF for trending repos
                    code_url=repo_url, # Link to the repo for code
                    read_more_url=repo_url,
                )
            )
        except Exception as e:
            logger.error(f"Failed to parse GitHub trending repository item: {e}")
            continue
            
    return items

