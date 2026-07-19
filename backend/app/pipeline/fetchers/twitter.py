import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

TWITTER_API_URL = "https://api.twitter.com/2"


def fetch_twitter_discussions(bearer_token: str | None) -> list[dict]:
    if not bearer_token:
        logger.info("No TWITTER_BEARER_TOKEN set, skipping Twitter fetch")
        return []

    headers = {"Authorization": f"Bearer {bearer_token}"}
    items = []

    query = "(AI OR artificial intelligence OR machine learning OR LLM OR GPT) -is:retweet lang:en"
    url = f"{TWITTER_API_URL}/tweets/search/recent"
    params = {
        "query": query,
        "max_results": 50,
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "name,username,profile_image_url",
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            for tweet in data.get("data", []):
                author = users.get(tweet.get("author_id", ""), {})

                engagement = tweet.get("public_metrics", {})
                items.append({
                    "external_id": f"twitter_{tweet['id']}",
                    "title": tweet["text"][:200],
                    "content": tweet["text"],
                    "source": "twitter",
                    "source_url": f"https://twitter.com/{author.get('username', '')}/status/{tweet['id']}",
                    "thumbnail_url": author.get("profile_image_url", "").replace("_normal", ""),
                    "author": author.get("name"),
                    "score": engagement.get("like_count", 0),
                    "num_comments": engagement.get("reply_count", 0) + engagement.get("retweet_count", 0),
                    "published_at": (
                        datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
                        if tweet.get("created_at") else None
                    ),
                })

    except Exception as e:
        logger.warning(f"Twitter API fetch failed: {e}")

    return items
