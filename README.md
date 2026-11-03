# NewsPulse — Personalized News Aggregator

An AI-powered news aggregator that pulls articles from **9 sources** (NewsAPI, Reddit, GDELT, The Guardian, NYT, Hacker News, RSS feeds, NewsData, GNews), processes them with NLP, and recommends stories using **semantic embeddings** (sentence-transformers). Built with a **Flask + PostgreSQL** backend and a **React + Vite + Tailwind** frontend.

This is a significant upgrade from the original single-file Flask + Bootstrap demo. The original `app.py`, `fetch_news.py`, and `process_data.py` are still here conceptually — they've been split into modular services and the data flow has been expanded.

---

## ✨ Features

- **User accounts** — JWT-based auth, saved bookmarks, reading history, editable topic preferences
- **AI recommendations** — articles embedded with `all-MiniLM-L6-v2` and ranked by cosine similarity to the user's preferred topics (graceful keyword-based fallback if the model is unavailable)
- **9 news sources** — NewsAPI, Reddit, GDELT, The Guardian (since 1999), NYT (since 1851!), Hacker News, RSS feeds (BBC/Wired/NASA/etc.), NewsData.io, GNews
- **Historical news fetcher** — pull articles from any year (back to 1851 with NYT) via the Search page UI
- **Search & filters** — full-text search across title/description/content with topic, source, sentiment, date-range, and sort filters; pagination
- **Dashboard & charts** — trending topics bar chart, topic distribution donut, sentiment breakdown, stat cards; built with Recharts
- **Live updates** — APScheduler background job fetches fresh news every 30 min (configurable) from all enabled sources, processes with NLTK + VADER sentiment, and ingests into Postgres
- **Newsletter & sharing** — subscribe with topic selection + frequency, share articles to Twitter / Facebook / LinkedIn / Email / clipboard, share counts tracked
- **Breaking news banner** — auto-detects breaking/urgent stories and rotates them in the header
- **Dark mode** — system-aware with manual toggle, persisted to localStorage
- **Modern dashboard UI** — magazine-style cards, responsive grid, Inter font, brand palette

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       React + Vite + Tailwind                    │
│  Dashboard · Feed · Search · Bookmarks · Newsletter · Profile    │
│  Search page has "Fetch Historical News" panel (any date range)   │
│         Auth Context (JWT) · Theme Context (dark mode)            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ axios → /api/* (proxied by Vite)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                            Flask API                              │
│  /api/auth/*       /api/news/*      /api/news/bookmarks/*        │
│  register, login   feed, search,    add, remove, list, history    │
│  me, preferences   trending, stats                                  │
│                    categories, sentiment, breaking, share         │
│                    fetch-historical (pull from any year!)          │
│                    /api/newsletter/* (subscribe, confirm, list)    │
└─────────┬──────────────────────────────┬───────────────────────────┘
          │                              │
          ▼                              ▼
┌──────────────────────┐    ┌─────────────────────────────────────┐
│  APScheduler (bg)    │    │     PostgreSQL (or SQLite lite mode)   │
│  every 30 min:       │    │  users, articles, bookmarks,         │
│   fetch → process →  │    │  reading_history, share_events,       │
│   embed → ingest     │    │  newsletter_subscribers               │
│  daily 08:00 UTC:    │    └─────────────────────────────────────┘
│   newsletter digest  │
└──────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    9 External news sources                        │
│                                                                   │
│  Always-on (no key needed):                                       │
│   • Hacker News (top stories)                                     │
│   • RSS feeds (BBC, Wired, NASA, NYT, Al Jazeera, ESPN, etc.)   │
│   • GDELT DOC (global events)                                     │
│                                                                   │
│  With API key:                                                    │
│   • NewsAPI (top-headlines, 100 req/day free)                    │
│   • Reddit OAuth (top posts per subreddit)                       │
│   • The Guardian (since 1999, 5K req/day free)                  │
│   • New York Times (since 1851!, 500 req/day free)              │
│   • NewsData.io (50 countries, 200 req/day free)                │
│   • GNews (multilingual, 100 req/day free)                      │
└─────────────────────────────────────────────────────────────────┘
```

**Processing pipeline (per article):**
1. Fetch from source (NewsAPI / Reddit / GDELT / Guardian / NYT / Hacker News / RSS / NewsData / GNews)
2. Tokenize + remove stopwords (NLTK)
3. Categorize into 10 topics using keyword matching
4. VADER sentiment analysis → score + label (positive/negative/neutral)
5. Estimate reading time (~200 wpm)
6. Detect breaking news (title keywords: "breaking", "urgent", etc.)
7. Embed title+description with `all-MiniLM-L6-v2` (skipped if unavailable)
8. Insert into DB (deduped by `external_id`)

---

## 📁 Project structure

```
news-aggregator/
├── docker-compose.yml         # Postgres 16
├── .env.example               # copy → backend/.env
├── .gitignore
├── README.md
│
├── backend/
│   ├── app/
│   │   ├── __init__.py        # Flask app factory + scheduler setup
│   │   ├── config.py          # env-driven config (9 source toggles)
│   │   ├── extensions.py      # db, jwt, cors, migrate, scheduler
│   │   ├── models.py          # User, Article, Bookmark, ReadingHistory,
│   │   │                       # ShareEvent, NewsletterSubscriber
│   │   ├── auth/routes.py     # register / login / me / preferences
│   │   ├── news/
│   │   │   ├── routes.py      # feed / search / trending / categories /
│   │   │   │                   # sentiment / breaking / topics / sources /
│   │   │   │                   # stats / refresh / fetch-historical /
│   │   │   │                   # article / read / share
│   │   │   ├── bookmarks.py    # list / add / remove / ids / history
│   │   │   └── newsletter.py   # subscribe / confirm / unsubscribe / list
│   │   ├── services/
│   │   │   ├── fetcher.py      # NewsAPI + Reddit + GDELT + dispatcher
│   │   │   │                   # to all 9 sources via more_fetchers
│   │   │   ├── more_fetchers.py # Guardian + NYT + HackerNews + RSS +
│   │   │   │                   # NewsData + GNews + historical fetcher
│   │   │   ├── processor.py    # NLTK tokenize + topic categorization
│   │   │   ├── recommender.py  # sentence-transformers semantic ranking
│   │   │   ├── sentiment.py     # VADER sentiment
│   │   │   └── scheduler.py    # APScheduler background jobs
│   │   └── utils/
│   │       ├── errors.py       # APIError + error handlers
│   │       └── decorators.py   # require_auth / get_current_user
│   ├── tests/
│   │   ├── test_app.py         # 8 pytest tests (auth, search, etc.)
│   │   └── conftest.py
│   ├── news_data.json          # 110 articles from original project (seed)
│   ├── seed.py                 # imports JSON or fetches fresh data
│   ├── run.py                  # `python run.py` → dev server
│   ├── requirements.txt
│   ├── .env.example
│   └── .flaskenv
│
└── frontend/
    ├── package.json
    ├── vite.config.ts          # proxies /api → :5000
    ├── tsconfig.json
    ├── tailwind.config.js      # dark mode: class, brand palette, animations
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx             # routes + providers
        ├── index.css           # Tailwind + component classes
        ├── api/
        │   ├── client.ts       # axios + JWT interceptor + 401 redirect
        │   └── endpoints.ts    # authApi, newsApi, bookmarksApi, newsletterApi
        ├── contexts/
        │   ├── AuthContext.tsx
        │   └── ThemeContext.tsx
        ├── components/
        │   ├── Navbar.tsx
        │   ├── ArticleCard.tsx          # bookmark, share menu, read tracking
        │   ├── BreakingNewsBanner.tsx   # auto-rotating breaking items
        │   ├── CategoryFilter.tsx
        │   ├── SearchBar.tsx
        │   ├── TrendingChart.tsx        # Recharts bar chart
        │   ├── CategoryChart.tsx        # Recharts donut
        │   ├── SentimentChart.tsx       # Recharts horizontal bar
        │   ├── DarkModeToggle.tsx
        │   └── ProtectedRoute.tsx
        ├── pages/
        │   ├── Dashboard.tsx
        │   ├── Feed.tsx
        │   ├── Search.tsx                # now includes Historical Fetch panel
        │   ├── Bookmarks.tsx
        │   ├── Login.tsx
        │   ├── Register.tsx
        │   ├── Profile.tsx
        │   ├── Newsletter.tsx
        │   └── NotFound.tsx
        └── types/index.ts
```

---

## 🚀 Quick start

### 1. Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Node.js 18+** (Node 20+ recommended)
- **Docker** (only for Postgres — or use SQLite, see below)
- API keys (all free — see "News source setup" below for details)

### 2. Start the database

**Option A — SQLite (lightweight, no install, recommended for low-memory machines):**
Edit `backend/.env` and set:
```
DATABASE_URL=sqlite:///news.db
```
That's it — no Docker needed. The DB is a single file in `backend/`.

**Option B — PostgreSQL via Docker:**
```bash
cd news-aggregator
docker compose up -d          # starts Postgres on localhost:5432
```

If you don't want Docker, install Postgres locally and create a `news_aggregator` database with a `news` user.

### 3. Backend setup

```bash
cd backend

# Create & activate venv
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# Install deps (full version with AI embeddings)
pip install -r requirements.txt

# OR install the lite version (no torch, ~80 MB instead of ~900 MB):
#   Create requirements-lite.txt with: Flask, Flask-SQLAlchemy,
#   Flask-Migrate, Flask-JWT-Extended, Flask-CORS, SQLAlchemy,
#   psycopg2-binary, Werkzeug, requests, APScheduler, nltk, numpy,
#   pandas, python-dotenv, gunicorn, pytest
#   Then: pip install -r requirements-lite.txt

# Configure environment
cp .env.example .env              # Windows: copy .env.example .env

# Create DB tables + seed the database
python seed.py                    # imports the 110 articles from news_data.json
# OR fetch fresh data from all 9 sources:
python seed.py --fetch

# Run the API
python run.py                     # serves on http://localhost:5000
```

Verify: <http://localhost:5000/api/health> → `{"status":"ok",...}`

### 4. Frontend setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev                       # serves on http://localhost:5173
```

Open <http://localhost:5173> — you should see the dashboard populated with seeded articles.

### 5. Run tests

```bash
cd backend
pytest tests/test_app.py -v       # 8 tests covering auth, search, newsletter
```

---

## 🔧 News source setup

All sources are **optional and gracefully skipped** if their key is missing — except the 3 keyless sources (Hacker News, RSS, GDELT) which always work.

### Keyless sources (work out of the box)

| Source | What you get | Notes |
|---|---|---|
| **Hacker News** | Top 30 trending tech stories | Uses Firebase API, no key, no rate limit |
| **RSS feeds** | 18 feeds (BBC, Reuters, Wired, NYT, NASA, ESPN, Al Jazeera, etc.) | Pure stdlib XML parser |
| **GDELT DOC** | Global events from 6 themes | No key, but slower |

### Sources requiring a free API key

| Source | Sign-up URL | Free tier | Special power |
|---|---|---|---|
| **NewsAPI** | <https://newsapi.org/register> | 100 req/day | Top headlines, 6 categories |
| **Reddit** | <https://www.reddit.com/prefs/apps> (script app) | 60 req/min | Top posts per subreddit |
| **The Guardian** | <https://open-platform.theguardian.com/access/> | 5,000 req/day | Articles back to **1999** |
| **NYT Article Search** | <https://developer.nytimes.com/get-started> | 500 req/day | Articles back to **1851!** |
| **NewsData.io** | <https://newsdata.io/register> | 200 req/day | 50 countries, 11 languages |
| **GNews** | <https://gnews.io/register> | 100 req/day | Multilingual |

### Enable a new source

1. Sign up at the URL above and copy your API key
2. Open `backend/.env` and fill in the corresponding variable (e.g. `GUARDIAN_API_KEY=abc123...`)
3. Set the corresponding `ENABLE_*` flag to `1` (e.g. `ENABLE_GUARDIAN=1`)
4. Restart the backend (`Ctrl+C` → `python run.py`)
5. Click "Refresh feed" on the dashboard, or wait for the next scheduler run

### Historical news (any year!)

The Search page has a **"📅 Fetch Historical News"** panel. Pick a date range (e.g. `2020-03-01` to `2020-04-30`) and a query (e.g. `"covid"`), then click **Fetch historical articles**. The backend pulls articles from The Guardian and/or NYT for that period, processes them, and ingests them into your DB — then auto-refreshes the search results to show them.

- **Guardian historical** works with the test key (rate-limited) or your free key (5K req/day)
- **NYT historical** requires `NYT_API_KEY` in `.env` (sign up at developer.nytimes.com)

---

## 🔧 Configuration

All config is env-driven — see `backend/.env.example` for the full list. Key ones:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://news:news@localhost:5432/news_aggregator` | Postgres connection. Set to `sqlite:///news.db` for lite mode |
| `NEWSAPI_KEY` | (your existing key) | NewsAPI access |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | (empty) | Reddit OAuth — leave empty to skip Reddit |
| `GUARDIAN_API_KEY` | (empty) | The Guardian — empty uses 'test' key (rate-limited) |
| `NYT_API_KEY` | (empty) | NYT Article Search — required for historical fetches |
| `NEWSDATA_API_KEY` | (empty) | NewsData.io |
| `GNEWS_API_KEY` | (empty) | GNews |
| `ENABLE_HACKERNEWS` | `1` | Toggle Hacker News fetcher |
| `ENABLE_RSS` | `1` | Toggle RSS feeds fetcher (18 feeds) |
| `ENABLE_GUARDIAN` | `1` | Toggle Guardian fetcher |
| `ENABLE_NYT` | `0` | Toggle NYT fetcher (off by default — slow due to rate limit) |
| `ENABLE_NEWDATA` | `0` | Toggle NewsData fetcher |
| `ENABLE_GNEWS` | `0` | Toggle GNews fetcher |
| `USE_EMBEDDINGS` | `1` | Set to `0` to use keyword fallback (faster startup, no torch download) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace model — first run downloads ~90 MB |
| `SCHEDULER_ENABLED` | `1` | Set to `0` to disable background fetching |
| `SCHEDULER_FETCH_MINUTES` | `30` | How often to fetch fresh news |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated list of allowed frontend origins |

### Recommendation engine without torch

If you don't want to install PyTorch (~700 MB) on first run, set `USE_EMBEDDINGS=0` in `.env`. The recommender will fall back to topic-keyword matching — same UX, slightly less semantic, much faster startup.

---

## 📡 API reference

All endpoints are JSON, all authenticated routes expect `Authorization: Bearer <token>`.

### Auth
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register` | `{email, username, password}` | `{token, user}` |
| POST | `/api/auth/login` | `{identifier, password}` | `{token, user}` |
| GET | `/api/auth/me` | — | `{user}` |
| PUT | `/api/auth/preferences` | `{preferences: [topic, ...]}` | `{user}` |

### News
| Method | Path | Notes |
|---|---|---|
| GET | `/api/news/feed` | `?limit=30&preferences=technology,science&exclude_read=1` |
| GET | `/api/news/search` | `?q=&topic=&source=&from=&to=&sentiment=&sort=&page=&page_size=` |
| GET | `/api/news/article/<id>` | single article with full content |
| POST | `/api/news/article/<id>/read` | marks as read |
| POST | `/api/news/article/<id>/share` | `{platform: twitter\|facebook\|linkedin\|email\|copy}` |
| GET | `/api/news/trending` | top topics in last 24h |
| GET | `/api/news/categories` | topic + source distribution |
| GET | `/api/news/sentiment` | sentiment distribution + avg score |
| GET | `/api/news/breaking` | `?limit=10` recent breaking stories |
| GET | `/api/news/topics` | all topics + their keyword sets |
| GET | `/api/news/sources` | list of all sources with counts |
| GET | `/api/news/stats` | total / breaking / last 24h counts |
| POST | `/api/news/refresh` | (auth) manually trigger a fetch from all enabled sources |
| **POST** | **`/api/news/fetch-historical`** | **(auth) `{from_date, to_date, query?, sources?}` → pulls historical articles from Guardian/NYT and ingests them** |

### Bookmarks (auth required)
| Method | Path |
|---|---|
| GET | `/api/news/bookmarks` |
| GET | `/api/news/bookmarks/ids` |
| POST | `/api/news/bookmarks/<article_id>` |
| DELETE | `/api/news/bookmarks/<article_id>` |
| GET | `/api/news/history` |

### Newsletter
| Method | Path |
|---|---|
| POST | `/api/newsletter/subscribe` `{email, frequency, topics}` |
| GET | `/api/newsletter/confirm/<token>` |
| POST | `/api/newsletter/unsubscribe` `{email}` |
| GET | `/api/newsletter/subscribers` |

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

8 tests cover:
- Health check
- Register / login / `me` flow
- Duplicate email rejection
- Preferences validation (good + bad topics)
- Empty feed
- Full-text search with topic filter
- Newsletter subscribe + confirm
- Breaking news + stats endpoints

The frontend has a `npm run lint` script (`tsc --noEmit`) for type-checking.

---

## 🐛 Troubleshooting

**`psycopg2.OperationalError: could not connect to server`**
Postgres isn't running. Either start it with `docker compose up -d`, or switch to SQLite by setting `DATABASE_URL=sqlite:///news.db` in `backend/.env`.

**`.env` changes aren't being picked up**
Make sure `load_dotenv()` is called in `backend/app/__init__.py` (top of file, before `from flask import`). Without it, `python run.py` ignores your `.env` file.

**First request hangs / downloads a big model**
The first `/api/news/refresh` or `python seed.py --fetch` will download `all-MiniLM-L6-v2` (~90 MB) and PyTorch (~700 MB on CPU). To skip this, set `USE_EMBEDDINGS=0` in `.env` — recommendations will use the keyword fallback.

**`No module named 'nltk_data'` warnings on first run**
NLTK will download stopwords + punkt + vader_lexicon on demand. If your environment blocks downloads, run once manually:
```bash
python -c "import nltk; [nltk.download(p) for p in ['stopwords','punkt','punkt_tab','vader_lexicon']]"
```

**Reddit returns 401 / empty results**
Make sure your Reddit app is type "script" (not "web app"), and that `REDDIT_USER_AGENT` describes your app (e.g. `news-aggregator/1.0 by your_username`). Reddit aggressively blocks generic user-agents.

**NewsAPI returns 429 (rate limit)**
The dev tier is 100 requests/day. The scheduler fetches 6 categories every 30 min = ~288 req/day. Either lower `SCHEDULER_FETCH_MINUTES`, remove categories in `app/services/fetcher.py`, set `SCHEDULER_ENABLED=0`, or upgrade to a paid plan. Other sources (Hacker News, RSS, Guardian) are unaffected.

**Historical fetch returns "No articles returned"**
Two common causes:
1. **Guardian test key is rate-limited** — sign up at <https://open-platform.theguardian.com/access/> for a free key (5K req/day) and put it in `GUARDIAN_API_KEY`.
2. **NYT key missing** — sign up at <https://developer.nytimes.com/get-started> and put it in `NYT_API_KEY`. Without a key, NYT historical fetches are silently skipped.

**Frontend shows empty dashboard after seeding**
The dashboard's "Trending Topics" chart filters to last 24h. If you only ran `seed.py` (which imports Feb-2025 data from the original project), there's nothing "recent". Either:
- Click **Refresh feed** in the dashboard (calls `/api/news/refresh` to fetch fresh articles), or
- Run `python seed.py --fetch` to pull current news from all 9 sources, or
- Use the **Fetch Historical News** panel on the Search page to pull articles from any date range

**`JWT_SECRET_KEY` too short warning**
Generate a 32+ char secret: `python -c "import secrets; print(secrets.token_hex(32))"` and put it in `.env`.

**Disk space issue on Windows (`No space left on device` during `pip install`)**
Use the lite install (see Quick Start step 3) — it skips PyTorch (159 MB) and sentence-transformers, total ~80 MB instead of ~900 MB. Also clear pip cache: `pip cache purge`.

---

## 📦 What changed from the original project

| Before | After |
|---|---|
| Single 250-line `app.py` with everything | Modular Flask app with blueprints + services + models |
| `processed_news.csv` | PostgreSQL with `articles`, `users`, `bookmarks`, etc. (or SQLite lite) |
| NewsAPI only | **9 sources**: NewsAPI + Reddit + GDELT + Guardian + NYT + Hacker News + RSS + NewsData + GNews |
| No historical news | **Fetch articles from any year** (NYT back to 1851, Guardian back to 1999) |
| Keyword topic matching | Keyword fallback + optional `sentence-transformers` semantic ranking |
| No sentiment | VADER sentiment analysis on every article |
| Bootstrap form | React + Vite + Tailwind dashboard with charts |
| No auth | JWT auth, bookmarks, reading history |
| No scheduler | APScheduler fetches every 30 min from all enabled sources |
| No newsletter | Newsletter subscriptions with topic + frequency |
| No dark mode | System-aware dark mode with toggle |

The original `news_data.json` (110 articles from your existing project) is included at `backend/news_data.json` and gets imported by `python seed.py` — so you can see the dashboard populated immediately without needing API keys.

---

## 📝 License

MIT — do whatever you want. Article content remains the property of the original publishers (NewsAPI sources, Reddit posts, GDELT, The Guardian, NYT, etc.).
