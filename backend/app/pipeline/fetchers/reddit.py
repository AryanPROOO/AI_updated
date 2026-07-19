import html
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx

logger = logging.getLogger(__name__)

SUBREDDITS = ["artificial", "MachineLearning", "AI", "singularity", "OpenAI", "artificialintelligence"]

AI_TOPICS = {
    "LLM": ["llm", "language model", "gpt", "chatgpt", "claude", "gemini", "openai", "anthropic", "llama", "mistral"],
    "Agents": ["agent", "autonomous", "tool use", "agentic"],
    "Computer Vision": ["vision", "image", "video generation", "sora", "dall-e", "stable diffusion"],
    "Edge AI": ["edge", "on-device", "mobile ai"],
    "Robotics": ["robot", "humanoid", "self-driving", "robotics"],
    "Reinforcement Learning": ["reinforcement learning", "rl"],
}


def classify_discussion(title: str, content: Optional[str]) -> list[str]:
    text = f"{title} {(content or '')}".lower()
    matched = []
    for topic, keywords in AI_TOPICS.items():
        if any(k in text for k in keywords):
            matched.append(topic)
    if not matched:
        matched.append("General AI")
    return matched


def _extract_thumbnail(entry) -> str | None:
    media = entry.get("media_content") or entry.get("media_thumbnail") or []
    if media:
        url = media[0].get("url")
        if url:
            return url.split("?")[0]
    content_html = entry.get("content", [{}])[0].get("value", "")
    match = re.search(r'<img[^>]+src="([^"]+)"', content_html)
    if match:
        return match.group(1)
    return None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]


def fetch_reddit_discussions() -> list[dict]:
    items = []
    seen_ids = set()

    for subreddit in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/.rss"
            resp = httpx.get(url, headers={"User-Agent": "AI-Research-Agent/1.0"}, timeout=30)
            resp.raise_for_status()

            feed = feedparser.parse(resp.text)

            for entry in feed.entries:
                post_id = entry.get("id", "")
                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                published = None
                if entry.get("published_parsed"):
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                content_text = _strip_html(entry.get("summary", "") or entry.get("content", [{}])[0].get("value", ""))
                thumbnail = _extract_thumbnail(entry)

                raw_title = entry.get("title", "")
                raw_content = content_text
                raw_author = entry.get("author") or ""

                items.append({
                    "external_id": post_id,
                    "title": html.unescape(raw_title),
                    "content": html.unescape(raw_content) if raw_content else None,
                    "source": "reddit",
                    "source_url": entry.get("link", ""),
                    "thumbnail_url": thumbnail,
                    "author": html.unescape(raw_author) if raw_author else None,
                    "score": 0,
                    "num_comments": 0,
                    "published_at": published,
                })

        except Exception as e:
            logger.warning(f"Failed to fetch r/{subreddit} RSS: {e}")

    return items
