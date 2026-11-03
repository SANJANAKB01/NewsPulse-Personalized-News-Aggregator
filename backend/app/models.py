"""SQLAlchemy models for users, articles, bookmarks, history and newsletter."""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    Index,
    LargeBinary,
)
from sqlalchemy.orm import relationship

from .extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    preferences = Column(Text, default="[]")  # JSON list of preferred topics
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    bookmarks = relationship(
        "Bookmark", back_populates="user", cascade="all, delete-orphan"
    )
    history = relationship(
        "ReadingHistory", back_populates="user", cascade="all, delete-orphan"
    )
    shares = relationship(
        "ShareEvent", back_populates="user", cascade="all, delete-orphan"
    )

    def set_preferences(self, prefs: list[str]) -> None:
        self.preferences = json.dumps(prefs)

    def get_preferences(self) -> list[str]:
        try:
            return json.loads(self.preferences or "[]")
        except json.JSONDecodeError:
            return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "preferences": self.get_preferences(),
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Article(db.Model):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), unique=True, index=True)
    source = Column(String(255))  # 'newsapi', 'reddit', 'gdelt'
    source_name = Column(String(255))  # display name e.g. "BBC", "r/worldnews"
    title = Column(Text, nullable=False)
    description = Column(Text)
    url = Column(Text, nullable=False, index=True)
    url_to_image = Column(Text)
    content = Column(Text)
    author = Column(String(255))
    category = Column(String(80), index=True)  # raw source category
    topic = Column(String(80), index=True)  # processed topic
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default="neutral")
    reading_time_min = Column(Integer, default=1)
    published_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), default=_utcnow)
    is_breaking = Column(Boolean, default=False)
    share_count = Column(Integer, default=0)

    # Store embedding as JSON text (floats). Binary column kept for future use.
    embedding = Column(Text)

    bookmarks = relationship("Bookmark", back_populates="article")
    history = relationship("ReadingHistory", back_populates="article")
    shares = relationship("ShareEvent", back_populates="article")

    def to_dict(self, include_content: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "external_id": self.external_id,
            "source": self.source,
            "source_name": self.source_name,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "url_to_image": self.url_to_image,
            "author": self.author,
            "category": self.category,
            "topic": self.topic,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "reading_time_min": self.reading_time_min,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "is_breaking": self.is_breaking,
            "share_count": self.share_count,
        }
        if include_content:
            data["content"] = self.content
        return data

    def get_embedding(self) -> list[float] | None:
        if not self.embedding:
            return None
        try:
            return json.loads(self.embedding)
        except json.JSONDecodeError:
            return None


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    saved_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article", back_populates="bookmarks")

    __table_args__ = (Index("uq_user_article_bookmark", "user_id", "article_id", unique=True),)


class ReadingHistory(db.Model):
    __tablename__ = "reading_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="history")
    article = relationship("Article", back_populates="history")

    __table_args__ = (Index("ix_user_read", "user_id", "read_at"),)


class ShareEvent(db.Model):
    __tablename__ = "share_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(40), nullable=False)  # twitter, facebook, linkedin, email, copy
    shared_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user = relationship("User", back_populates="shares")
    article = relationship("Article", back_populates="shares")


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    frequency = Column(String(20), default="daily")  # daily, weekly, off
    topics = Column(Text, default="[]")  # JSON list of topics to include
    confirmed = Column(Boolean, default=False)
    confirm_token = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        try:
            topics = json.loads(self.topics or "[]")
        except json.JSONDecodeError:
            topics = []
        return {
            "id": self.id,
            "email": self.email,
            "frequency": self.frequency,
            "topics": topics,
            "confirmed": self.confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def estimate_reading_time(text: str | None) -> int:
    """Estimate reading time in minutes (~200 wpm)."""
    if not text:
        return 1
    words = len(text.split())
    return max(1, math.ceil(words / 200))
