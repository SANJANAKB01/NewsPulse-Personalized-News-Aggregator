"""Newsletter subscription routes."""
from __future__ import annotations

import json
import secrets

from flask import Blueprint, request, jsonify, url_for

from ..extensions import db
from ..models import NewsletterSubscriber
from ..utils.errors import APIError
from ..services.processor import all_topics

newsletter_bp = Blueprint("newsletter", __name__)


@newsletter_bp.post("/subscribe")
def subscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if "@" not in email or "." not in email:
        raise APIError("Valid email is required", 422)
    frequency = (data.get("frequency") or "daily").lower()
    if frequency not in {"daily", "weekly", "off"}:
        raise APIError("frequency must be daily|weekly|off", 422)
    topics = data.get("topics") or []
    if not isinstance(topics, list):
        raise APIError("topics must be a list", 422)
    valid_topics = set(all_topics())
    topics = [t for t in topics if isinstance(t, str) and t.lower() in valid_topics]

    sub = NewsletterSubscriber.query.filter_by(email=email).first()
    if sub:
        sub.frequency = frequency
        sub.topics = json.dumps(topics)
        db.session.commit()
        return jsonify({"ok": True, "subscriber": sub.to_dict()})

    token = secrets.token_urlsafe(32)
    sub = NewsletterSubscriber(
        email=email,
        frequency=frequency,
        topics=json.dumps(topics),
        confirm_token=token,
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({
        "ok": True,
        "subscriber": sub.to_dict(),
        "confirm_token": token,  # In production email this, don't return it
    }), 201


@newsletter_bp.get("/confirm/<token>")
def confirm(token: str):
    sub = NewsletterSubscriber.query.filter_by(confirm_token=token).first()
    if not sub:
        raise APIError("Invalid or expired token", 404)
    sub.confirmed = True
    db.session.commit()
    return jsonify({"ok": True, "email": sub.email, "confirmed": True})


@newsletter_bp.post("/unsubscribe")
def unsubscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise APIError("Email is required", 422)
    sub = NewsletterSubscriber.query.filter_by(email=email).first()
    if not sub:
        return jsonify({"ok": True, "message": "Not subscribed"})
    sub.frequency = "off"
    db.session.commit()
    return jsonify({"ok": True, "message": "Unsubscribed"})


@newsletter_bp.get("/subscribers")
def list_subscribers():
    """Dev endpoint to inspect subscribers."""
    subs = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()
    return jsonify({"subscribers": [s.to_dict() for s in subs], "count": len(subs)})
