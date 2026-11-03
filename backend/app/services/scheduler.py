"""Background scheduler: periodic fetch + processing + newsletter digest."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from ..extensions import db

log = logging.getLogger(__name__)


def register_jobs(app, scheduler) -> None:
    cfg = app.config
    fetch_minutes = max(5, int(cfg.get("SCHEDULER_FETCH_MINUTES", 60)))

    scheduler.add_job(
        _fetch_and_process_job,
        "interval",
        minutes=fetch_minutes,
        id="fetch-news",
        args=[app],
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )

    scheduler.add_job(
        _send_newsletter_digests,
        "cron",
        hour=8,
        minute=0,
        id="newsletter-digest",
        args=[app],
        replace_existing=True,
    )

    log.info("Scheduler registered: fetch every %dm, daily newsletter at 08:00 UTC", fetch_minutes)


def _fetch_and_process_job(app) -> None:
    from .fetcher import fetch_all
    from .processor import tokenize, categorize
    from .sentiment import analyze
    from ..models import Article, estimate_reading_time

    with app.app_context():
        log.info("Scheduled fetch starting at %s", datetime.now(timezone.utc).isoformat())
        try:
            raw = fetch_all(app.config)
        except Exception as exc:
            log.error("Fetch failed: %s", exc)
            return

        if not raw:
            log.info("No articles fetched")
            return

        existing_ids = {
            row[0]
            for row in db.session.query(Article.external_id)
            .filter(Article.external_id.in_([a["external_id"] for a in raw if a.get("external_id")]))
            .all()
        }

        new_count = 0
        for raw_article in raw:
            ext_id = raw_article.get("external_id")
            if not ext_id or ext_id in existing_ids:
                continue
            if not raw_article.get("title") or not raw_article.get("url"):
                continue

            tokens = tokenize(
                (raw_article.get("title") or "") + " " + (raw_article.get("content") or "")
                + " " + (raw_article.get("description") or "")
            )
            topic = categorize(tokens, default=raw_article.get("category") or "world")
            sentiment_score, sentiment_label = analyze(
                (raw_article.get("title") or "") + " " + (raw_article.get("description") or "")
            )

            article = Article(
                external_id=ext_id,
                source=raw_article.get("source"),
                source_name=raw_article.get("source_name"),
                title=raw_article.get("title"),
                description=raw_article.get("description"),
                url=raw_article.get("url"),
                url_to_image=raw_article.get("url_to_image"),
                content=raw_article.get("content"),
                author=raw_article.get("author"),
                category=raw_article.get("category") or topic,
                topic=topic,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                reading_time_min=estimate_reading_time(raw_article.get("content")),
                published_at=raw_article.get("published_at"),
                is_breaking=_is_breaking(raw_article, topic, sentiment_label),
            )

            if app.config.get("USE_EMBEDDINGS", False):
                try:
                    from .recommender import embed_text
                    emb = embed_text(article.title + " " + (article.description or ""))
                    if emb:
                        article.embedding = json.dumps(emb)
                except Exception as exc:
                    log.debug("Embedding skipped: %s", exc)

            db.session.add(article)
            new_count += 1

        try:
            db.session.commit()
            log.info("Ingested %d new articles", new_count)
        except Exception as exc:
            db.session.rollback()
            log.error("Ingest commit failed: %s", exc)


def _is_breaking(raw_article, topic, sentiment):
    title = (raw_article.get("title") or "").lower()
    keywords = ["breaking", "urgent", "just in", "live", "alert", "developing"]
    return any(kw in title for kw in keywords)


def _send_newsletter_digests(app) -> None:
    from ..models import NewsletterSubscriber

    with app.app_context():
        subscribers = NewsletterSubscriber.query.filter_by(confirmed=True, frequency="daily").all()
        log.info("Newsletter digest: %d subscribers", len(subscribers))
        for sub in subscribers:
            log.info("Would send digest to %s", sub.email)
