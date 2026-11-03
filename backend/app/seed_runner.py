"""Seed runner that can be called from app/__init__.py to auto-populate the DB.

Used on Render's ephemeral filesystem — re-seeds from news_data.json on every
boot if the DB is empty.
"""
import json
import os
from datetime import datetime, timezone

from .extensions import db
from .models import Article, estimate_reading_time
from .services.processor import tokenize, categorize
from .services.sentiment import analyze


def run_seed(app):
    """Import articles from news_data.json into the database."""
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "news_data.json")
    if not os.path.exists(json_path):
        app.logger.warning("news_data.json not found at %s - skipping seed", json_path)
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_articles = data.get("articles", []) if isinstance(data, dict) else []
    if not raw_articles:
        app.logger.warning("No articles found in news_data.json")
        return 0

    ext_ids_to_check = [f"newsapi::{a.get('url')}" for a in raw_articles if a.get("url")]
    existing_ids = set()
    if ext_ids_to_check:
        existing_ids = {
            row[0] for row in
            db.session.query(Article.external_id).filter(
                Article.external_id.in_(ext_ids_to_check)
            ).all()
        }

    inserted = 0
    for raw in raw_articles:
        url = raw.get("url")
        if not url:
            continue
        ext_id = f"newsapi::{url}"
        if ext_id in existing_ids:
            continue

        published_at = None
        if raw.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(raw["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        title = raw.get("title") or ""
        description = raw.get("description") or ""
        content = raw.get("content") or ""
        combined = f"{title} {description} {content}"
        tokens = tokenize(combined)
        topic = categorize(tokens, default=raw.get("category") or "world")
        sentiment_score, sentiment_label = analyze(f"{title} {description}")

        article = Article(
            external_id=ext_id,
            source="newsapi",
            source_name=(raw.get("source") or {}).get("name") or "NewsAPI",
            title=title,
            description=description,
            url=url,
            url_to_image=raw.get("urlToImage"),
            content=content,
            author=raw.get("author"),
            category=raw.get("category") or topic,
            topic=topic,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            reading_time_min=estimate_reading_time(content),
            published_at=published_at,
            fetched_at=datetime.now(timezone.utc),
            is_breaking=any(
                kw in title.lower()
                for kw in ["breaking", "urgent", "just in", "live", "alert", "developing"]
            ),
        )
        db.session.add(article)
        inserted += 1

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise exc

    return inserted