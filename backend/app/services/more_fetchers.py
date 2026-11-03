"""Additional news fetchers: Guardian, NYT, Hacker News, RSS, NewsData, GNews."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

import requests

log = logging.getLogger(__name__)


def _iso(dt_str):
    if not dt_str:
        return None
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)
    except ValueError:
        try:
            return datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def _safe_get(url, params=None, headers=None, timeout=20):
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.warning("GET %s failed: %s", url, exc)
        return None
    except ValueError:
        log.warning("GET %s returned non-JSON", url)
        return None


def fetch_guardian(api_key, page_size=50, query=None, from_date=None, to_date=None):
    if not api_key:
        api_key = "test"
    base = "https://content.guardianapis.com/search"
    out = []
    params = {
        "api-key": api_key,
        "page-size": min(page_size, 50),
        "show-fields": "headline,trailText,thumbnail,bodyText,byline",
        "order-by": "newest",
        "q": query or "",
    }
    if from_date:
        params["from-date"] = from_date
    if to_date:
        params["to-date"] = to_date
    data = _safe_get(base, params=params)
    if not data:
        return out
    results = data.get("response", {}).get("results", [])
    for r in results:
        fields = r.get("fields", {})
        out.append({
            "external_id": f"guardian::{r.get('id')}",
            "source": "guardian",
            "source_name": "The Guardian",
            "title": r.get("webTitle") or fields.get("headline") or "",
            "description": fields.get("trailText") or "",
            "url": r.get("webUrl") or "",
            "url_to_image": fields.get("thumbnail"),
            "content": (fields.get("bodyText") or "")[:4000],
            "author": fields.get("byline"),
            "category": (r.get("sectionName") or "world").lower(),
            "published_at": _iso(r.get("webPublicationDate")),
        })
    log.info("Guardian fetched %d articles", len(out))
    return out


def fetch_nyt(api_key, query="news", page=0, from_date=None, to_date=None):
    if not api_key:
        log.warning("NYT_API_KEY missing - skipping NYT fetch")
        return []
    base = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    out = []
    pages = 5 if not from_date else 2
    for p in range(page, page + pages):
        params = {"api-key": api_key, "q": query, "page": p, "sort": "newest" if not from_date else "oldest"}
        if from_date:
            params["begin_date"] = from_date.replace("-", "")[:8]
        if to_date:
            params["end_date"] = to_date.replace("-", "")[:8]
        data = _safe_get(base, params=params)
        if not data:
            break
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            break
        for doc in docs:
            headline = doc.get("headline", {}) or {}
            title = headline.get("main") or headline.get("print_headline") or ""
            multimedia = doc.get("multimedia") or []
            image_url = None
            if multimedia:
                for m in multimedia:
                    if m.get("subtype") == "xlarge" or m.get("width", 0) >= 600:
                        image_url = "https://www.nytimes.com/" + m.get("url", "")
                        break
                if not image_url:
                    image_url = "https://www.nytimes.com/" + multimedia[0].get("url", "")
            out.append({
                "external_id": f"nyt::{doc.get('_id') or doc.get('web_url')}",
                "source": "nyt",
                "source_name": "The New York Times",
                "title": title,
                "description": doc.get("abstract") or doc.get("lead_paragraph") or "",
                "url": doc.get("web_url") or "",
                "url_to_image": image_url,
                "content": (doc.get("lead_paragraph") or "") + " " + (doc.get("snippet") or ""),
                "author": doc.get("byline", {}).get("original"),
                "category": (doc.get("section_name") or "world").lower(),
                "published_at": _iso(doc.get("pub_date")),
            })
        time.sleep(12)
    log.info("NYT fetched %d articles", len(out))
    return out


def fetch_hackernews(top_n=30):
    out = []
    ids = _safe_get("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not isinstance(ids, list):
        return out
    for item_id in ids[:top_n]:
        item = _safe_get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
        if not item or not isinstance(item, dict):
            continue
        if item.get("type") != "story":
            continue
        title = item.get("title") or ""
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        out.append({
            "external_id": f"hn::{item_id}",
            "source": "hackernews",
            "source_name": "Hacker News",
            "title": title,
            "description": f"HN discussion ({item.get('score', 0)} points, {item.get('descendants', 0)} comments)",
            "url": url,
            "url_to_image": None,
            "content": title,
            "author": item.get("by"),
            "category": "technology",
            "published_at": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc) if item.get("time") else None,
        })
        time.sleep(0.1)
    log.info("Hacker News fetched %d articles", len(out))
    return out


RSS_FEEDS = [
    ("https://feeds.bbci.co.uk/news/rss.xml", "BBC News", "world"),
    ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC World", "world"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml", "BBC Business", "business"),
    ("https://feeds.bbci.co.uk/news/technology/rss.xml", "BBC Technology", "technology"),
    ("https://feeds.bbci.co.uk/news/science/rss.xml", "BBC Science", "science"),
    ("https://feeds.bbci.co.uk/news/health/rss.xml", "BBC Health", "health"),
    ("https://www.nasa.gov/feed/", "NASA", "science"),
    ("https://www.wired.com/feed/rss", "Wired", "technology"),
    ("https://www.theverge.com/rss/index.xml", "The Verge", "technology"),
    ("https://techcrunch.com/feed/", "TechCrunch", "technology"),
    ("https://www.cnet.com/rss/news/", "CNET", "technology"),
    ("https://www.espn.com/espn/rss/news", "ESPN", "sports"),
    ("https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "NYT (RSS)", "world"),
    ("https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "NYT Technology (RSS)", "technology"),
    ("https://www.theguardian.com/world/rss", "Guardian World (RSS)", "world"),
    ("https://www.theguardian.com/technology/rss", "Guardian Tech (RSS)", "technology"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera", "world"),
    ("https://www.nationalgeographic.com/news/rss/", "National Geographic", "science"),
]


def _parse_rss_date(date_str):
    if not date_str:
        return None
    formats = ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def fetch_rss_feeds(feeds=None):
    feeds = feeds or RSS_FEEDS
    out = []
    try:
        import xml.etree.ElementTree as ET
    except ImportError:
        log.error("xml.etree.ElementTree not available")
        return out
    for url, source_name, category in feeds:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "news-aggregator/1.0"})
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as exc:
            log.warning("RSS %s failed: %s", source_name, exc)
            continue
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date = item.findtext("pubDate")
            author = item.findtext("{http://purl.org/dc/elements/1.1/creator}")
            if not author:
                author_el = item.find("{http://purl.org/dc/elements/1.1/creator}")
                if author_el is not None:
                    author = author_el.text
            if not title or not link:
                continue
            image_url = None
            enclosure = item.find("enclosure")
            if enclosure is not None and "image" in (enclosure.get("type") or ""):
                image_url = enclosure.get("url")
            if not image_url:
                media = item.find("{http://search.yahoo.com/mrss/}content")
                if media is not None:
                    image_url = media.get("url")
            out.append({
                "external_id": f"rss::{link}",
                "source": "rss",
                "source_name": source_name,
                "title": title,
                "description": description,
                "url": link,
                "url_to_image": image_url,
                "content": description or title,
                "author": author,
                "category": category,
                "published_at": _parse_rss_date(pub_date),
            })
        time.sleep(0.2)
    log.info("RSS fetched %d articles from %d feeds", len(out), len(feeds))
    return out


def fetch_newsdata(api_key, country="us", category=None, query=None):
    if not api_key:
        log.warning("NEWSDATA_API_KEY missing - skipping NewsData")
        return []
    out = []
    params = {"apikey": api_key, "country": country, "size": 10}
    if category:
        params["category"] = category
    if query:
        params["q"] = query
    categories = [category] if category else ["business", "technology", "world", "science", "health", "sports"]
    for cat in categories:
        params["category"] = cat
        data = _safe_get("https://newsdata.io/api/1/news", params=params)
        if not data:
            continue
        for art in data.get("results", []):
            out.append({
                "external_id": f"newsdata::{art.get('article_id') or art.get('link')}",
                "source": "newsdata",
                "source_name": art.get("source_id") or "NewsData",
                "title": art.get("title") or "",
                "description": art.get("description") or "",
                "url": art.get("link") or "",
                "url_to_image": art.get("image_url"),
                "content": (art.get("content") or "")[:4000],
                "author": art.get("creator"),
                "category": cat,
                "published_at": _iso(art.get("pubDate")),
            })
        time.sleep(1.5)
    log.info("NewsData fetched %d articles", len(out))
    return out


def fetch_gnews(api_key, query="breaking news", max_articles=10):
    if not api_key:
        log.warning("GNEWS_API_KEY missing - skipping GNews")
        return []
    out = []
    queries = [query, "technology", "world", "business"] if query == "breaking news" else [query]
    for q in queries:
        params = {"apikey": api_key, "q": q, "max": min(max_articles, 10), "lang": "en", "country": "us"}
        data = _safe_get("https://gnews.io/api/v4/search", params=params)
        if not data:
            continue
        for art in data.get("articles", []):
            out.append({
                "external_id": f"gnews::{art.get('url')}",
                "source": "gnews",
                "source_name": (art.get("source") or {}).get("name") or "GNews",
                "title": art.get("title") or "",
                "description": art.get("description") or "",
                "url": art.get("url") or "",
                "url_to_image": art.get("image"),
                "content": (art.get("content") or "")[:4000],
                "author": None,
                "category": "world",
                "published_at": _iso(art.get("publishedAt")),
            })
        time.sleep(2)
    log.info("GNews fetched %d articles", len(out))
    return out


def fetch_historical(sources, from_date, to_date, query="news", config=None):
    articles = []
    if config is None:
        return articles
    if "guardian" in sources:
        guardian_key = getattr(config, "GUARDIAN_API_KEY", "") or "test"
        articles.extend(fetch_guardian(guardian_key, page_size=50, query=query, from_date=from_date, to_date=to_date))
    if "nyt" in sources:
        nyt_key = getattr(config, "NYT_API_KEY", "")
        if nyt_key:
            articles.extend(fetch_nyt(nyt_key, query=query, from_date=from_date, to_date=to_date))
        else:
            log.warning("NYT_API_KEY missing - skipping NYT historical fetch")
    return articles