"""Helper decorators and utilities."""
from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models import User
from .errors import APIError


def _parse_identity(identity) -> int | None:
    """Flask-JWT-Extended v4.6+ stores sub as string. Coerce to int."""
    if identity is None:
        return None
    try:
        return int(identity)
    except (TypeError, ValueError):
        return None


def get_current_user() -> User | None:
    """Return the current authenticated user or None."""
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return None
    user_id = _parse_identity(get_jwt_identity())
    if not user_id:
        return None
    return db.session.get(User, user_id)


def require_auth(fn):
    """Decorator: require a valid JWT and inject the user as current_user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = _parse_identity(get_jwt_identity())
        user = db.session.get(User, user_id) if user_id else None
        if not user:
            raise APIError("User not found", 401)
        return fn(*args, current_user=user, **kwargs)

    return wrapper


def parse_int_list(value: str | None) -> list[int]:
    if not value:
        return []
    out = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if chunk.isdigit():
            out.append(int(chunk))
    return out


def parse_str_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
