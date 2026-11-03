"""Text processing: tokenization, stopword removal, topic categorization, reading time."""
from __future__ import annotations

import logging
import re
from typing import Iterable

import nltk

log = logging.getLogger(__name__)

_TOPICS: dict[str, set[str]] = {
    "technology": {
        "technology", "ai", "apple", "google", "microsoft", "android", "iphone",
        "software", "hardware", "smartphone", "laptop", "chip", "semiconductor",
        "startup", "internet", "cloud", "cyber", "robot", "automation",
    },
    "sports": {
        "sports", "nba", "soccer", "football", "tennis", "baseball", "hockey",
        "game", "match", "tournament", "league", "athlete", "olympic", "nfl",
        "mlb", "nhl", "fifa", "racing", "golf",
    },
    "finance": {
        "finance", "stock", "market", "investment", "bank", "money", "economy",
        "bitcoin", "crypto", "trading", "bonds", "dividend", "inflation", "interest",
        "fed", "treasury", "wall street",
    },
    "business": {
        "business", "company", "corporate", "entrepreneur", "industry", "merger",
        "acquisition", "ceo", "startup", "revenue", "profit", "earnings", "layoff",
        "supply chain", "retail",
    },
    "travel": {
        "travel", "trip", "flight", "vacation", "hotel", "tourism", "airline",
        "destination", "cruise", "resort", "itinerary", "tourist", "passport",
    },
    "entertainment": {
        "entertainment", "movie", "film", "music", "celebrity", "show", "netflix",
        "tv", "actor", "actress", "singer", "concert", "award", "oscar", "grammy",
        "festival", "streaming", "disney",
    },
    "health": {
        "health", "medicine", "doctor", "hospital", "disease", "fitness", "wellness",
        "vaccine", "virus", "cancer", "mental", "nutrition", "diet", "exercise",
        "outbreak", "pandemic", "flu", "cdc", "fda",
    },
    "science": {
        "science", "research", "study", "space", "biology", "chemistry", "physics",
        "astronomy", "nasa", "spacex", "quantum", "neuroscience", "genetics",
        "climate", "ecosystem", "evolution", "fossil", "experiment",
    },
    "politics": {
        "politics", "election", "congress", "senate", "president", "government",
        "policy", "democrat", "republican", "trump", "biden", "campaign", "vote",
        "lawmaker", "parliament",
    },
    "world": {
        "world", "global", "country", "nation", "war", "conflict", "crisis",
        "treaty", "summit", "refugee", "humanitarian", "u.n.", "un security",
        "geopolitics", "diplomacy",
    },
}

_nltk_ready = False


def ensure_nltk() -> None:
    global _nltk_ready
    if _nltk_ready:
        return
    for resource in [("stopwords", "corpora/stopwords"), ("punkt", "tokenizers/punkt"),
                     ("punkt_tab", "tokenizers/punkt_tab")]:
        try:
            nltk.data.find(resource[1])
        except LookupError:
            try:
                nltk.download(resource[0], quiet=True)
            except Exception as exc:  # noqa: BLE001
                log.warning("NLTK download %s failed: %s", resource[0], exc)
    _nltk_ready = True


def tokenize(text: str | None) -> list[str]:
    ensure_nltk()
    if not text:
        return []
    try:
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize

        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words("english"))
        return [t for t in tokens if t.isalnum() and t not in stop_words and len(t) > 1]
    except Exception as exc:  # noqa: BLE001
        # Fallback: simple split if NLTK data missing
        log.warning("NLTK tokenize failed, using fallback: %s", exc)
        words = re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
        return words


def categorize(tokens: Iterable[str], default: str | None = None) -> str:
    """Return the topic whose keyword set matches first."""
    token_set = set(tokens)
    for topic, keywords in _TOPICS.items():
        if token_set & keywords:
            return topic
    return default or "world"


def topic_keywords() -> dict[str, set[str]]:
    """Expose the topic-to-keyword mapping (used by frontend)."""
    return {topic: sorted(words) for topic, words in _TOPICS.items()}


def all_topics() -> list[str]:
    return list(_TOPICS.keys())
