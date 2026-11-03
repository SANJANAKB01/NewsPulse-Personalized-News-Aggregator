"""Bookmark routes."""
from __future__ import annotations

from flask import Blueprint, request, jsonify

from ..extensions import db
from ..models import Bookmark, Article
from ..utils.decorators import require_auth
from ..utils.errors import APIError

bookmarks_bp = Blueprint("bookmarks", __name__)


@bookmarks_bp.get("/bookmarks")
@require_auth
def list_bookmarks(current_user):
    rows = (
        Bookmark.query
        .filter_by(user_id=current_user.id)
        .order_by(Bookmark.saved_at.desc())
        .all()
    )
    return jsonify({
        "articles": [
            {**bm.article.to_dict(), "saved_at": bm.saved_at.isoformat()}
            for bm in rows if bm.article
        ],
        "count": len(rows),
    })


@bookmarks_bp.post("/bookmarks/<int:article_id>")
@require_auth
def add_bookmark(article_id: int, current_user):
    article = db.session.get(Article, article_id)
    if not article:
        raise APIError("Article not found", 404)
    existing = Bookmark.query.filter_by(user_id=current_user.id, article_id=article_id).first()
    if existing:
        return jsonify({"ok": True, "message": "Already bookmarked"})
    db.session.add(Bookmark(user_id=current_user.id, article_id=article_id))
    db.session.commit()
    return jsonify({"ok": True}), 201


@bookmarks_bp.delete("/bookmarks/<int:article_id>")
@require_auth
def remove_bookmark(article_id: int, current_user):
    bm = Bookmark.query.filter_by(user_id=current_user.id, article_id=article_id).first()
    if not bm:
        raise APIError("Bookmark not found", 404)
    db.session.delete(bm)
    db.session.commit()
    return jsonify({"ok": True})


@bookmarks_bp.get("/bookmarks/ids")
@require_auth
def bookmark_ids(current_user):
    ids = [
        row[0] for row in
        db.session.query(Bookmark.article_id).filter_by(user_id=current_user.id).all()
    ]
    return jsonify({"ids": ids})


@bookmarks_bp.get("/history")
@require_auth
def reading_history(current_user):
    from ..models import ReadingHistory
    rows = (
        ReadingHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(ReadingHistory.read_at.desc())
        .limit(100)
        .all()
    )
    return jsonify({
        "history": [
            {
                "article": rh.article.to_dict() if rh.article else None,
                "read_at": rh.read_at.isoformat(),
            }
            for rh in rows
        ],
        "count": len(rows),
    })
