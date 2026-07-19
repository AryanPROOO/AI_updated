import logging
import re
from datetime import datetime

from openai import OpenAI

from app.config import settings
from app.pipeline.normalizer import RawItem


logger = logging.getLogger(__name__)


TECH_KEYWORDS = re.compile(
    r"\b(?:transformer architecture|attention mechanism|state-of-the-art|SOTA|"
    r"end-to-end|multi-modal|foundation model|pre-training|fine-tuning|"
    r"zero-shot|few-shot|baseline model|embedding vector|latent space|"
    r"backbone|encoder-decoder|self-attention|cross-attention|"  # simplified, but we try
    r"benchmark suite|ablation study|SGD|backpropagation|gradient descent|tokenization|"
    r"parameter efficient|inference time|autoregressive|diffusion process)\b",
    re.IGNORECASE,
)


def _simplify_text(text: str) -> str:
    replacements = {
        "leverages": "uses",
        "utilizes": "uses",
        "demonstrates": "shows",
        "exhibits": "shows",
        "facilitates": "helps",
        "optimizes": "improves",
        "robust": "reliable",
        "novel": "new",
        "state-of-the-art": "top",
        "leverage": "use",
        "utilize": "use",
        "framework": "approach",
        "paradigm": "approach",
        "architecture": "design",
        "pipeline": "process",
        "corpus": "dataset",
        "empirical": "practical",
    }
    for old, new in replacements.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text, flags=re.IGNORECASE)
    return text


def _clean_github_snippet(snippet: str) -> tuple[str, str | None, str | None]:
    parts = [p.strip() for p in snippet.split("|")]
    description = parts[0] if parts else snippet
    language = None
    stars = None
    for p in parts[1:]:
        if p.lower().startswith("language:"):
            language = p.split(":", 1)[1].strip()
        elif p.lower().startswith("stars:"):
            stars = p.split(":", 1)[1].strip()
    return description, language, stars


def _fallback_summary(item: RawItem) -> tuple[str, str]:
    snippet = (item.snippet or "").strip()

    if item.source == "github_trending" and snippet:
        description, lang, stars = _clean_github_snippet(snippet)
        # Short summary: what it is
        summary = description[:120].strip().rstrip(".")
        # Short why: what problem it solves
        why = f"Solves: {summary.lower()}"
        return summary, why

    if snippet:
        # Take first sentence only, keep it short
        first_sentence = re.split(r'[.!?]', snippet)[0].strip()
        summary = first_sentence[:150].rstrip(".")
    else:
        summary = f"New {item.source} update about {_simplify_text(item.title)}"

    # Short why: what problem it solves
    why = f"Solves: {summary.lower()}"
    return summary, why


def summarize_item(item: RawItem, topics: list[str]) -> tuple[str, str]:
    if not settings.openai_api_key:
        return _fallback_summary(item)

    prompt = (
        "Write a ONE-LINE summary of what this paper/repo does (max 15 words).\n"
        "Then write a ONE-LINE description of what problem it solves (max 20 words).\n"
        "Keep it simple, no jargon.\n\n"
        "Format:\n"
        "SUMMARY: [what it does in one short line]\n"
        "WHY: [what problem it solves in one short line]\n\n"
        f"Title: {item.title}\n"
        f"Snippet: {(item.snippet or 'N/A')[:300]}\n"
        f"Source: {item.source}\n"
    )

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You explain AI research in simple, beginner-friendly language. "
                        "Avoid technical jargon and buzzwords. "
                        "Write like you are explaining to someone new to AI."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=250,
        )
        text = response.choices[0].message.content or ""
        summary_line = ""
        why_line = ""
        for line in text.splitlines():
            upper = line.strip().upper()
            if upper.startswith("SUMMARY:"):
                summary_line = line.split(":", 1)[1].strip()
            elif upper.startswith("WHY:"):
                why_line = line.split(":", 1)[1].strip()

        if summary_line and why_line:
            return summary_line, why_line
        else:
            logger.warning("LLM response missing SUMMARY or WHY. Response: %s", text)

    except Exception as e:
        logger.exception(f"LLM summarization failed: {e}, using fallback")

    return _fallback_summary(item)
