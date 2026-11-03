"""Seed the database from existing news_data.json or run a fresh fetch.

Usage:
    python seed.py            # import upload/news_data.json if available
    python seed.py --fetch    # fetch fresh data via NewsAPI/Reddit/GDELT
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Allow running as `python seed.py` from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import Article, estimate_reading_time
from app.services.processor import tokenize, categorize
from app.services.sentiment import analyze


def import_json_file(path: str) -> int:
    if not os.path.exists(path):
        print(f"[seed] JSON file not found: {path}")
        return 0
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_articles = data.get("articles", []) if isinstance(data, dict) else []
    print(f"[seed] Loaded {len(raw_articles)} articles from {path}")

    existing = {
        row[0] for row in
        db.session.query(Article.external_id).filter(Article.external_id.in_(
            [f"newsapi::{a.get('url')}" for a in raw_articles]
        )).all()
    }

    inserted = 0
    for raw in raw_articles:
        url = raw.get("url")
        if not url:
            continue
        ext_id = f"newsapi::{url}"
        if ext_id in existing:
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

    db.session.commit()
    print(f"[seed] Inserted {inserted} new articles")
    return inserted


def fetch_and_seed() -> int:
    from app.services.fetcher import fetch_all
    from app.services.scheduler import _fetch_and_process_job
    from flask import current_app
    print("[seed] Fetching fresh articles from NewsAPI/Reddit/GDELT...")
    _fetch_and_process_job(current_app)
    print("[seed] Fetch complete")
    return Article.query.count()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch live data instead of importing JSON")
    parser.add_argument("--json", default=None, help="Path to news_data.json")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()
        if args.fetch:
            fetch_and_seed()
        else:
            json_path = args.json or os.environ.get(
                "NEWS_DATA_JSON",
                os.path.join(os.path.dirname(__file__), "news_data.json"),
            )
            import_json_file(json_path)

        # Try to compute embeddings for any articles missing them
        try:
            from app.services.recommender import embed_text, _load_model
            model = _load_model(app.config.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
            if model:
                missing = Article.query.filter(Article.embedding.is_(None)).limit(200).all()
                print(f"[seed] Computing embeddings for {len(missing)} articles...")
                for art in missing:
                    emb = embed_text(f"{art.title} {art.description or ''}")
                    if emb:
                        art.embedding = json.dumps(emb)
                db.session.commit()
                print("[seed] Embeddings done")
            else:
                print("[seed] sentence-transformers unavailable - skipping embeddings")
        except Exception as exc:  # noqa: BLE001
            print(f"[seed] Embedding step skipped: {exc}")

        print(f"[seed] Total articles in DB: {Article.query.count()}")


if __name__ == "__main__":
    main()
