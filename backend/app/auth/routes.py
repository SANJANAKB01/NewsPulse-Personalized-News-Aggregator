"""Authentication routes: register, login, me, update preferences."""
from __future__ import annotations

import re

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity

from ..extensions import db
from ..models import User
from ..utils.decorators import require_auth
from ..utils.errors import APIError

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

VALID_TOPICS = {
    "technology", "sports", "finance", "business", "travel",
    "entertainment", "health", "science", "politics", "world",
}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not EMAIL_RE.match(email):
        raise APIError("Invalid email address", 422)
    if len(username) < 3:
        raise APIError("Username must be at least 3 characters", 422)
    if len(password) < 8:
        raise APIError("Password must be at least 8 characters", 422)

    if User.query.filter_by(email=email).first():
        raise APIError("Email already registered", 409)
    if User.query.filter_by(username=username).first():
        raise APIError("Username already taken", 409)

    user = User(
        email=email,
        username=username,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        preferences="[]",
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or data.get("email") or data.get("username") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        raise APIError("Missing credentials", 422)

    user = User.query.filter(
        (User.email == identifier.lower()) | (User.username == identifier)
    ).first()

    if not user or not check_password_hash(user.password_hash, password):
        raise APIError("Invalid credentials", 401)

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@require_auth
def me(current_user: User):
    return jsonify({"user": current_user.to_dict()})


@auth_bp.put("/preferences")
@require_auth
def update_preferences(current_user: User):
    data = request.get_json(silent=True) or {}
    prefs = data.get("preferences") or []
    if not isinstance(prefs, list):
        raise APIError("preferences must be a list of topic strings", 422)

    cleaned: list[str] = []
    for p in prefs:
        if not isinstance(p, str):
            continue
        topic = p.strip().lower()
        if not topic:
            continue
        if topic not in VALID_TOPICS:
            raise APIError(
                f"Unknown topic: {topic}. Valid: {', '.join(sorted(VALID_TOPICS))}",
                422,
            )
        cleaned.append(topic)

    current_user.set_preferences(cleaned)
    db.session.commit()
    return jsonify({"user": current_user.to_dict()})


@auth_bp.put("/password")
@require_auth
def change_password(current_user: User):
    from werkzeug.security import check_password_hash, generate_password_hash

    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new_pw = data.get("new_password") or ""

    if not check_password_hash(current_user.password_hash, current):
        raise APIError("Current password is incorrect", 401)
    if len(new_pw) < 8:
        raise APIError("New password must be at least 8 characters", 422)

    current_user.password_hash = generate_password_hash(new_pw, method="pbkdf2:sha256")
    db.session.commit()
    return jsonify({"message": "Password updated"})
