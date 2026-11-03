"""Application configuration loaded from environment variables."""
import os
from datetime import timedelta


def _env(key, default=""):
    return os.environ.get(key, default)


class BaseConfig:
    SECRET_KEY = _env("SECRET_KEY", "dev-secret-change-me-in-production")
    DEBUG = _env("FLASK_DEBUG", "0") == "1"

    SQLALCHEMY_DATABASE_URI = _env("DATABASE_URL", "sqlite:///news.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_SECRET_KEY = _env("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    JWT_TOKEN_LOCATION = ["headers"]

    CORS_ORIGINS = _env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

    NEWSAPI_KEY = _env("NEWSAPI_KEY", "ef8b3f9a030b4a4b9537a77c307a68bd")
    NEWSAPI_BASE = "https://newsapi.org/v2"

    REDDIT_CLIENT_ID = _env("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = _env("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = _env("REDDIT_USER_AGENT", "news-aggregator/1.0")
    REDDIT_SUBREDDITS = _env("REDDIT_SUBREDDITS", "worldnews,technology,science,business,sports,UpliftingNews").split(",")

    GDELT_BASE = "https://api.gdeltproject.org/api/v2"

    GUARDIAN_API_KEY = _env("GUARDIAN_API_KEY", "")
    NYT_API_KEY = _env("NYT_API_KEY", "")
    HACKERNEWS_TOP_N = int(_env("HACKERNEWS_TOP_N", "30"))
    NEWSDATA_API_KEY = _env("NEWSDATA_API_KEY", "")
    GNEWS_API_KEY = _env("GNEWS_API_KEY", "")

    ENABLE_HACKERNEWS = _env("ENABLE_HACKERNEWS", "1") == "1"
    ENABLE_RSS = _env("ENABLE_RSS", "1") == "1"
    ENABLE_GUARDIAN = _env("ENABLE_GUARDIAN", "1") == "1"
    ENABLE_NYT = _env("ENABLE_NYT", "0") == "1"
    ENABLE_NEWDATA = _env("ENABLE_NEWDATA", "0") == "1"
    ENABLE_GNEWS = _env("ENABLE_GNEWS", "0") == "1"

    EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    USE_EMBEDDINGS = _env("USE_EMBEDDINGS", "0") == "1"
    RECOMMEND_TOP_K = int(_env("RECOMMEND_TOP_K", "30"))

    SCHEDULER_FETCH_MINUTES = int(_env("SCHEDULER_FETCH_MINUTES", "60"))
    SCHEDULER_ENABLED = _env("SCHEDULER_ENABLED", "1") == "1"

    SMTP_HOST = _env("SMTP_HOST", "")
    SMTP_PORT = int(_env("SMTP_PORT", "587"))
    SMTP_USER = _env("SMTP_USER", "")
    SMTP_PASSWORD = _env("SMTP_PASSWORD", "")
    NEWSLETTER_FROM = _env("NEWSLETTER_FROM", "digest@news-aggregator.local")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SCHEDULER_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.environ.get("FLASK_ENV", "development")
    return config_map.get(name, DevelopmentConfig)
