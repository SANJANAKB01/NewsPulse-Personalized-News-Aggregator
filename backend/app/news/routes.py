"""News routes: feed, search, trending, categories, sentiment, breaking, share."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc

from ..extensions import db
from ..models import Article, ShareEvent, ReadingHistory, User
from ..utils.decorators import get_current_user, require_auth
from ..utils.errors import APIError
from ..services.recommender import recommend
from ..services.processor import all_topics, topic_keywords

news_bp = Blueprint("news", __name__)


@news_bp.get("/feed")
def feed():
    limit = min(int(request.args.get("limit", "30")), 100)
    prefs_param = request.args.get("preferences", "").strip()
    preferences = [p.strip().lower() for p in prefs_param.split(",") if p.strip()]
    exclude_read = request.args.get("exclude_read", "0") == "1"

    user = get_current_user()
    exclude_ids = set()
    if not preferences and user:
        preferences = user.get_preferences()
    if exclude_read and user:
        exclude_ids = {hid for (hid,) in db.session.query(ReadingHistory.article_id).filter_by(user_id=user.id).all()}

    articles = recommend(preferences, top_k=limit, exclude_ids=exclude_ids)
    return jsonify({"articles": [a.to_dict() for a in articles], "preferences_used": preferences, "count": len(articles)})


@news_bp.get("/search")
def search():
    q = (request.args.get("q") or "").strip()
    category = request.args.get("category")
    topic = request.args.get("topic")
    source = request.args.get("source")
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    sentiment = request.args.get("sentiment")
    sort = request.args.get("sort", "recent")
    page = max(1, int(request.args.get("page", "1")))
    page_size = min(int(request.args.get("page_size", "20")), 50)

    stmt = Article.query
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.filter((func.lower(Article.title).like(like)) | (func.lower(Article.description).like(like)) | (func.lower(Article.content).like(like)))
    if category:
        stmt = stmt.filter(Article.category == category)
    if topic:
        stmt = stmt.filter(Article.topic == topic)
    if source:
        stmt = stmt.filter(Article.source == source)
    if sentiment:
        stmt = stmt.filter(Article.sentiment_label == sentiment)
    if date_from:
        try:
            stmt = stmt.filter(Article.published_at >= datetime.fromisoformat(date_from))
        except ValueError:
            raise APIError("'from' must be ISO 8601 date", 422)
    if date_to:
        try:
            stmt = stmt.filter(Article.published_at <= datetime.fromisoformat(date_to))
        except ValueError:
            raise APIError("'to' must be ISO 8601 date", 422)
    if sort == "popular":
        stmt = stmt.order_by(desc(Article.share_count), desc(Article.published_at))
    elif sort == "sentiment_pos":
        stmt = stmt.order_by(desc(Article.sentiment_score))
    elif sort == "sentiment_neg":
        stmt = stmt.order_by(Article.sentiment_score)
    else:
        stmt = stmt.order_by(desc(Article.published_at).nullslast())

    total = stmt.count()
    rows = stmt.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({"articles": [a.to_dict() for a in rows], "page": page, "page_size": page_size, "total": total, "pages": (total + page_size - 1) // page_size})


@news_bp.get("/article/<int:article_id>")
def get_article(article_id):
    article = db.session.get(Article, article_id)
    if not article:
        raise APIError("Article not found", 404)
    return jsonify({"article": article.to_dict(include_content=True)})


@news_bp.post("/article/<int:article_id>/read")
def mark_read(article_id):
    user = get_current_user()
    if not user:
        return jsonify({"ok": True, "tracked": False}), 200
    article = db.session.get(Article, article_id)
    if not article:
        raise APIError("Article not found", 404)
    existing = ReadingHistory.query.filter_by(user_id=user.id, article_id=article_id).first()
    if not existing:
        db.session.add(ReadingHistory(user_id=user.id, article_id=article_id))
        db.session.commit()
    return jsonify({"ok": True})


@news_bp.post("/article/<int:article_id>/share")
def share_article(article_id):
    data = request.get_json(silent=True) or {}
    platform = (data.get("platform") or "copy").lower()
    if platform not in {"twitter", "facebook", "linkedin", "email", "copy"}:
        raise APIError("Invalid share platform", 422)
    article = db.session.get(Article, article_id)
    if not article:
        raise APIError("Article not found", 404)
    article.share_count = (article.share_count or 0) + 1
    user = get_current_user()
    if user:
        db.session.add(ShareEvent(user_id=user.id, article_id=article_id, platform=platform))
    db.session.commit()
    return jsonify({"ok": True, "share_count": article.share_count})


@news_bp.get("/trending")
def trending():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    rows = db.session.query(Article.topic, func.count(Article.id)).filter(Article.published_at >= cutoff).group_by(Article.topic).order_by(desc(func.count(Article.id))).all()
    return jsonify({"trending": [{"topic": topic, "count": count} for topic, count in rows if topic], "since": cutoff.isoformat()})


@news_bp.get("/categories")
def categories():
    rows = db.session.query(Article.topic, func.count(Article.id)).group_by(Article.topic).all()
    sources = db.session.query(Article.source, func.count(Article.id)).group_by(Article.source).all()
    return jsonify({"by_topic": [{"topic": t, "count": c} for t, c in rows], "by_source": [{"source": s, "count": c} for s, c in sources]})


@news_bp.get("/sentiment")
def sentiment():
    rows = db.session.query(Article.sentiment_label, func.count(Article.id)).group_by(Article.sentiment_label).all()
    avg = db.session.query(func.avg(Article.sentiment_score)).filter(Article.sentiment_score.isnot(None)).scalar()
    return jsonify({"distribution": [{"label": label, "count": count} for label, count in rows if label], "average_score": float(avg) if avg is not None else 0.0})


@news_bp.get("/breaking")
def breaking():
    limit = min(int(request.args.get("limit", "10")), 50)
    rows = Article.query.filter_by(is_breaking=True).order_by(desc(Article.published_at).nullslast()).limit(limit).all()
    return jsonify({"articles": [a.to_dict() for a in rows], "count": len(rows)})


@news_bp.get("/topics")
def topics():
    return jsonify({"topics": all_topics(), "keywords": topic_keywords()})


@news_bp.get("/sources")
def sources():
    rows = db.session.query(Article.source, Article.source_name, func.count(Article.id)).group_by(Article.source, Article.source_name).order_by(desc(func.count(Article.id))).all()
    return jsonify({"sources": [{"source": s, "name": n, "count": c} for s, n, c in rows]})


@news_bp.post("/refresh")
@require_auth
def refresh(current_user):
    from ..services.scheduler import _fetch_and_process_job
    from flask import current_app
    _fetch_and_process_job(current_app)
    return jsonify({"ok": True, "message": "Refresh triggered"})


@news_bp.post("/fetch-historical")
@require_auth
def fetch_historical_endpoint(current_user):
    from flask import current_app
    from ..services.more_fetchers import fetch_historical
    from ..services.processor import tokenize, categorize
    from ..services.sentiment import analyze
    from ..models import Article, estimate_reading_time

    data = request.get_json(silent=True) or {}
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    query = data.get("query") or "news"
    sources = data.get("sources") or ["guardian", "nyt"]

    if not from_date or not to_date:
        raise APIError("from_date and to_date are required (YYYY-MM-DD)", 422)
    try:
        datetime.fromisoformat(from_date)
        datetime.fromisoformat(to_date)
    except ValueError:
        raise APIError("Dates must be ISO 8601 format YYYY-MM-DD", 422)
    if from_date > to_date:
        raise APIError("from_date must be before to_date", 422)

    raw_articles = fetch_historical(sources=sources, from_date=from_date, to_date=to_date, query=query, config=current_app.config)

    if not raw_articles:
        return jsonify({"ok": True, "fetched": 0, "inserted": 0, "message": "No articles returned. Check your API keys (NYT_API_KEY, GUARDIAN_API_KEY)."})

    ext_ids = [a.get("external_id") for a in raw_articles if a.get("external_id")]
    existing_ids = set()
    if ext_ids:
        existing_ids = {row[0] for row in db.session.query(Article.external_id).filter(Article.external_id.in_(ext_ids)).all()}

    inserted = 0
    for raw in raw_articles:
        ext_id = raw.get("external_id")
        if not ext_id or ext_id in existing_ids:
            continue
        if not raw.get("title") or not raw.get("url"):
            continue
        tokens = tokenize((raw.get("title") or "") + " " + (raw.get("content") or "") + " " + (raw.get("description") or ""))
        topic = categorize(tokens, default=raw.get("category") or "world")
        sentiment_score, sentiment_label = analyze((raw.get("title") or "") + " " + (raw.get("description") or ""))
        article = Article(
            external_id=ext_id, source=raw.get("source"), source_name=raw.get("source_name"),
            title=raw.get("title"), description=raw.get("description"), url=raw.get("url"),
            url_to_image=raw.get("url_to_image"), content=raw.get("content"), author=raw.get("author"),
            category=raw.get("category") or topic, topic=topic,
            sentiment_score=sentiment_score, sentiment_label=sentiment_label,
            reading_time_min=estimate_reading_time(raw.get("content")),
            published_at=raw.get("published_at"), is_breaking=False,
        )
        db.session.add(article)
        inserted += 1
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise APIError(f"Database insert failed: {exc}", 500)
    return jsonify({"ok": True, "fetched": len(raw_articles), "inserted": inserted, "skipped": len(raw_articles) - inserted, "sources": sources, "from_date": from_date, "to_date": to_date, "query": query})


@news_bp.get("/stats")
def stats():
    total_articles = Article.query.count()
    total_breaking = Article.query.filter_by(is_breaking=True).count()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = Article.query.filter(Article.published_at >= cutoff).count()
    return jsonify({"total_articles": total_articles, "breaking_articles": total_breaking, "articles_last_24h": recent})