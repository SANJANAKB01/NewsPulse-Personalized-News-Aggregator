"""Semantic recommendation engine using sentence-transformers.

Falls back to keyword matching if sentence-transformers is not installed or if the
model is unavailable (e.g. offline first run).
"""
from __future__ import annotations

import json
import logging
import math
from typing import Iterable

from ..models import Article
from ..extensions import db

log = logging.getLogger(__name__)

_model = None


def _load_model(model_name: str):
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(model_name)
        log.info("Loaded embedding model %s", model_name)
    except Exception as exc:  # noqa: BLE001
        log.warning("sentence-transformers unavailable (%s); using keyword fallback", exc)
        _model = False  # mark tried
    return _model


def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> list[float] | None:
    """Return an embedding vector for the given text, or None if unavailable."""
    model = _load_model(model_name)
    if not model:
        return None
    try:
        vec = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        return vec.tolist()
    except Exception as exc:  # noqa: BLE001
        log.warning("Embedding failed: %s", exc)
        return None


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def recommend(
    preferences: list[str],
    top_k: int = 30,
    exclude_ids: Iterable[int] | None = None,
) -> list[Article]:
    """Return ranked articles matching the user's preference topics.

    Uses semantic embeddings if available, otherwise falls back to topic-keyword matching.
    """
    exclude_ids = set(exclude_ids or [])
    prefs = [p.lower() for p in preferences if p]

    if not prefs:
        # No preferences: just return latest articles
        q = Article.query.order_by(Article.published_at.desc().nullslast())
        if exclude_ids:
            q = q.filter(~Article.id.in_(exclude_ids))
        return q.limit(top_k).all()

    model = _load_model("all-MiniLM-L6-v2")
    query_text = " ".join(prefs)

    if model:
        query_vec = embed_text(query_text)
        if query_vec:
            # Pull candidate articles that match preferred topics first
            candidates = (
                Article.query
                .filter(Article.topic.in_(prefs))
                .order_by(Article.published_at.desc().nullslast())
                .limit(400)
                .all()
            )
            # If too few candidates, broaden to all recent
            if len(candidates) < 20:
                candidates = (
                    Article.query
                    .order_by(Article.published_at.desc().nullslast())
                    .limit(200)
                    .all()
                )
            scored = []
            for art in candidates:
                if art.id in exclude_ids:
                    continue
                emb = art.get_embedding()
                if not emb:
                    continue
                score = cosine(query_vec, emb)
                scored.append((score, art))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [art for _, art in scored[:top_k]]

    # Fallback: topic matching
    q = (
        Article.query
        .filter(Article.topic.in_(prefs))
        .order_by(Article.published_at.desc().nullslast())
    )
    if exclude_ids:
        q = q.filter(~Article.id.in_(exclude_ids))
    return q.limit(top_k).all()
