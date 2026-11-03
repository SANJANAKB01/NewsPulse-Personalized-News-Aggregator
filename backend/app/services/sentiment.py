"""VADER sentiment analysis wrapper."""
from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)

_vader = None


def _ensure_vader():
    global _vader
    if _vader is not None:
        return _vader
    try:
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer

        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)
        _vader = SentimentIntensityAnalyzer()
    except Exception as exc:  # noqa: BLE001
        log.warning("VADER unavailable (%s) - using lexicon fallback", exc)
        _vader = False  # mark as tried
    return _vader


_POSITIVE = {
    "win", "wins", "won", "victory", "success", "growth", "breakthrough",
    "boost", "rally", "gain", "rise", "record", "approval", "hope", "peace",
    "deal", "recover", "investment", "uplift", "achieve", "launch", "innovate",
    "benefit", "improve", "positive", "strong", "good", "great", "best",
}
_NEGATIVE = {
    "loss", "lose", "lost", "defeat", "crash", "collapse", "crisis", "disaster",
    "war", "death", "kill", "attack", "breach", "hack", "fraud", "lawsuit",
    "arrest", "fall", "drop", "plunge", "scandal", "outbreak", "fear", "concern",
    "warning", "threat", "violation", "decline", "weak", "bad", "worst",
}


def analyze(text: str | None) -> tuple[float, str]:
    """Return (compound_score, label)."""
    if not text:
        return 0.0, "neutral"

    analyzer = _ensure_vader()
    if analyzer:
        try:
            scores = analyzer.polarity_scores(text)
            compound = scores["compound"]
            label = "positive" if compound >= 0.15 else (
                "negative" if compound <= -0.15 else "neutral"
            )
            return round(compound, 4), label
        except Exception as exc:  # noqa: BLE001
            log.warning("VADER analyze failed: %s", exc)

    # Fallback: lexicon-based
    tokens = set(re.findall(r"\b[a-z]{2,}\b", text.lower()))
    pos = len(tokens & _POSITIVE)
    neg = len(tokens & _NEGATIVE)
    score = (pos - neg) / max(1, pos + neg)
    label = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
    return round(score, 4), label
