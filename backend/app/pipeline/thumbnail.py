import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Topic-based images from Unsplash (reliable, free, no rate limits)
TOPIC_IMAGES = {
    "LLM": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=300&fit=crop",
    "Agents": "https://images.unsplash.com/photo-1677442135136-67e0a4b3e4b3?w=400&h=300&fit=crop",
    "Edge AI": "https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?w=400&h=300&fit=crop",
    "Robotics": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=300&fit=crop",
    "Computer Vision": "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=400&h=300&fit=crop",
    "Reinforcement Learning": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=400&h=300&fit=crop",
    "default": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=300&fit=crop",
}

# Fallback images that are known to work
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?w=400&h=300&fit=crop",
]
_next_fallback = 0


def _fallback_image() -> str:
    """Get a fallback image based on simple rotation."""
    global _next_fallback
    url = FALLBACK_IMAGES[_next_fallback % len(FALLBACK_IMAGES)]
    _next_fallback += 1
    return url


def _get_topic_image(topics: list[str]) -> str:
    """Get an image based on the paper's topics."""
    for topic in topics:
        if topic in TOPIC_IMAGES:
            return TOPIC_IMAGES[topic]
    return TOPIC_IMAGES["default"]


def search_wikimedia_image(query: str, topics: list[str] | None = None) -> Optional[str]:
    """Get a relevant image for a research item.

    Uses topic-based Unsplash images for reliability.
    """
    # Use topic-based image if available
    if topics:
        return _get_topic_image(topics)

    # Final fallback
    return _fallback_image()
