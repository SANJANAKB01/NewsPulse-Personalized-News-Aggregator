"""Unit tests for the Flask API. Run with: pytest tests/test_app.py"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from app.extensions import db
from app.models import User, Article


@pytest.fixture
def client():
    db_path = tempfile.mktemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["SCHEDULER_ENABLED"] = "0"
    os.environ["USE_EMBEDDINGS"] = "0"
    app = create_app("testing")
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_register_login_me(client):
    resp = client.post("/api/auth/register", json={
        "email": "user@example.com",
        "username": "user1",
        "password": "password123",
    })
    assert resp.status_code == 201
    token = resp.get_json()["token"]

    resp = client.post("/api/auth/login", json={
        "identifier": "user@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    assert resp.get_json()["token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "user@example.com"


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={
        "email": "user@example.com",
        "username": "user1",
        "password": "password123",
    })
    resp = client.post("/api/auth/register", json={
        "email": "user@example.com",
        "username": "user2",
        "password": "password123",
    })
    assert resp.status_code == 409


def test_preferences(client):
    resp = client.post("/api/auth/register", json={
        "email": "user@example.com",
        "username": "user1",
        "password": "password123",
    })
    token = resp.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put("/api/auth/preferences", headers=headers, json={
        "preferences": ["technology", "science"],
    })
    assert resp.status_code == 200
    assert "technology" in resp.get_json()["user"]["preferences"]

    resp = client.put("/api/auth/preferences", headers=headers, json={
        "preferences": ["nonexistent_topic"],
    })
    assert resp.status_code == 422


def test_feed_empty(client):
    resp = client.get("/api/news/feed")
    assert resp.status_code == 200
    assert resp.get_json()["articles"] == []


def test_search_with_filters(client):
    with client.application.app_context():
        art = Article(
            external_id="newsapi::test1",
            source="newsapi",
            source_name="Test Source",
            title="Big Tech Earnings Beat Expectations",
            description="Apple and Google reported strong quarterly results.",
            url="https://example.com/article1",
            content="Apple and Google posted record profits this quarter.",
            category="technology",
            topic="technology",
            sentiment_label="positive",
            sentiment_score=0.7,
        )
        db.session.add(art)
        db.session.commit()
        art_id = art.id

    resp = client.get("/api/news/search?q=earnings")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["total"] >= 1
    assert any(a["id"] == art_id for a in data["articles"])

    resp = client.get("/api/news/search?topic=technology")
    assert resp.get_json()["total"] >= 1


def test_newsletter_subscribe(client):
    resp = client.post("/api/newsletter/subscribe", json={
        "email": "subscriber@example.com",
        "frequency": "daily",
        "topics": ["technology"],
    })
    assert resp.status_code == 201
    token = resp.get_json()["confirm_token"]

    resp = client.get(f"/api/newsletter/confirm/{token}")
    assert resp.status_code == 200
    assert resp.get_json()["confirmed"] is True


def test_breaking_and_stats(client):
    with client.application.app_context():
        art = Article(
            external_id="newsapi::breaking1",
            source="newsapi",
            source_name="Breaking Source",
            title="Breaking: Major Earthquake Strikes",
            description="A powerful earthquake has been reported.",
            url="https://example.com/breaking",
            content="Breaking news content here.",
            category="world",
            topic="world",
            is_breaking=True,
            sentiment_label="negative",
            sentiment_score=-0.5,
        )
        db.session.add(art)
        db.session.commit()

    resp = client.get("/api/news/breaking")
    assert resp.status_code == 200
    assert resp.get_json()["count"] >= 1

    resp = client.get("/api/news/stats")
    assert resp.get_json()["total_articles"] >= 1
