"""News fetchers for NewsAPI, Reddit and GDELT."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import requests

log = logging.getLogger(__name__)

CATEGORIES = ["technology", "sports", "business", "entertainment", "health", "science"]


def _iso(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_newsapi(api_key, base_url="https://newsapi.org/v2"):
    if not api_key:
        log.warning("NEWSAPI_KEY missing - skipping NewsAPI fetch")
        return []
    out = []
    for category in CATEGORIES:
        url = f"{base_url}/top-headlines"
        params = {"country": "us", "category": category, "apiKey": api_key, "pageSize": 40}
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            log.warning("NewsAPI %s failed: %s", category, exc)
            continue
        for article in data.get("articles", []):
            out.append({
                "external_id": f"newsapi::{article.get('url')}",
                "source": "newsapi",
                "source_name": (article.get("source") or {}).get("name") or "NewsAPI",
                "title": article.get("title") or "",
                "description": article.get("description") or "",
                "url": article.get("url") or "",
                "url_to_image": article.get("urlToImage"),
                "content": article.get("content") or "",
                "author": article.get("author"),
                "category": category,
                "published_at": _iso(article.get("publishedAt")),
            })
        time.sleep(0.4)
    log.info("NewsAPI fetched %d articles", len(out))
    return out


def fetch_reddit(client_id, client_secret, user_agent, subreddits):
    if not client_id or not client_secret:
        log.warning("REDDIT_CLIENT_ID/SECRET missing - skipping Reddit fetch")
        return []
    try:
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        token_resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": user_agent},
            timeout=15,
        )
        token_resp.raise_for_status()
        token = token_resp.json().get("access_token")
        if not token:
            log.warning("Reddit OAuth returned no token")
            return []
    except requests.RequestException as exc:
        log.warning("Reddit OAuth failed: %s", exc)
        return []
    headers = {"Authorization": f"bearer {token}", "User-Agent": user_agent}
    out = []
    for sub in subreddits:
        try:
            url = f"https://oauth.reddit.com/r/{sub.strip()}/top"
            resp = requests.get(url, headers=headers, params={"limit": 25, "t": "day"}, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("children", [])
        except requests.RequestException as exc:
            log.warning("Reddit r/%s failed: %s", sub, exc)
            continue
        for child in data:
            post = child.get("data", {})
            permalink = post.get("permalink")
            full_url = f"https://www.reddit.com{permalink}" if permalink else ""
            out.append({
                "external_id": f"reddit::{post.get('id')}",
                "source": "reddit",
                "source_name": f"r/{sub.strip()}",
                "title": post.get("title") or "",
                "description": post.get("selftext")[:300] if post.get("selftext") else "",
                "url": full_url,
                "url_to_image": _extract_image(post),
                "content": post.get("selftext") or post.get("title") or "",
                "author": post.get("author"),
                "category": _subreddit_topic(sub.strip()),
                "published_at": datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc),
            })
        time.sleep(0.3)
    log.info("Reddit fetched %d posts", len(out))
    return out


def _extract_image(post):
    preview = post.get("preview") or {}
    images = preview.get("images") or []
    if images:
        return images[0].get("source", {}).get("url")
    return None


def _subreddit_topic(sub):
    mapping = {
        "worldnews": "world", "technology": "technology", "science": "science",
        "business": "business", "sports": "sports", "upliftingnews": "world",
        "entertainment": "entertainment", "health": "health", "politics": "politics", "finance": "finance",
    }
    return mapping.get(sub.lower(), "world")


def fetch_gdelt(base_url="https://api.gdeltproject.org/api/v2"):
    out = []
    themes = [
        ("ENV_WEATHER", "science"), ("HEALTH_VACCINATION", "health"),
        ("ECON_FINANCE", "finance"), ("TECHNOLOGY", "technology"),
        ("SPORT", "sports"), ("MILITARY", "world"),
    ]
    for theme, topic in themes:
        try:
            url = f"{base_url}/doc/doc"
            params = {"query": theme, "mode": "ArtList", "maxrecords": 25, "sort": "DateDesc", "format": "json"}
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError:
                continue
        except requests.RequestException as exc:
            log.warning("GDELT theme %s failed: %s", theme, exc)
            continue
        for art in data.get("articles", []):
            out.append({
                "external_id": f"gdelt::{art.get('url')}",
                "source": "gdelt",
                "source_name": art.get("domain") or "GDELT",
                "title": art.get("title") or "",
                "description": "",
                "url": art.get("url") or "",
                "url_to_image": art.get("socialimage") or None,
                "content": art.get("title") or "",
                "author": None,
                "category": topic,
                "published_at": _iso(art.get("seendate")),
            })
        time.sleep(0.3)
    log.info("GDELT fetched %d articles", len(out))
    return out


def fetch_all(config):
    """Run all configured fetchers and merge results."""
    articles = []
    articles.extend(fetch_newsapi(config.NEWSAPI_KEY, config.NEWSAPI_BASE))
    articles.extend(fetch_reddit(config.REDDIT_CLIENT_ID, config.REDDIT_CLIENT_SECRET, config.REDDIT_USER_AGENT, config.REDDIT_SUBREDDITS))
    articles.extend(fetch_gdelt(config.GDELT_BASE))

    try:
        from .more_fetchers import (
            fetch_guardian, fetch_nyt, fetch_hackernews, fetch_rss_feeds,
            fetch_newsdata, fetch_gnews,
        )
        if getattr(config, "ENABLE_GUARDIAN", True):
            try:
                articles.extend(fetch_guardian(config.GUARDIAN_API_KEY or "test"))
            except Exception as exc:
                log.warning("Guardian fetch failed: %s", exc)
        if getattr(config, "ENABLE_NYT", False) and config.NYT_API_KEY:
            try:
                articles.extend(fetch_nyt(config.NYT_API_KEY, query="news"))
            except Exception as exc:
                log.warning("NYT fetch failed: %s", exc)
        if getattr(config, "ENABLE_HACKERNEWS", True):
            try:
                articles.extend(fetch_hackernews(getattr(config, "HACKERNEWS_TOP_N", 30)))
            except Exception as exc:
                log.warning("Hacker News fetch failed: %s", exc)
        if getattr(config, "ENABLE_RSS", True):
            try:
                articles.extend(fetch_rss_feeds())
            except Exception as exc:
                log.warning("RSS fetch failed: %s", exc)
        if getattr(config, "ENABLE_NEWDATA", False) and config.NEWSDATA_API_KEY:
            try:
                articles.extend(fetch_newsdata(config.NEWSDATA_API_KEY))
            except Exception as exc:
                log.warning("NewsData fetch failed: %s", exc)
        if getattr(config, "ENABLE_GNEWS", False) and config.GNEWS_API_KEY:
            try:
                articles.extend(fetch_gnews(config.GNEWS_API_KEY))
            except Exception as exc:
                log.warning("GNews fetch failed: %s", exc)
    except ImportError as exc:
        log.warning("more_fetchers not available: %s", exc)

    log.info("Total fetched across all sources: %d", len(articles))
    return articles