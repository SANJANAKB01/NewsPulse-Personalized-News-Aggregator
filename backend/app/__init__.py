"""Flask application factory."""
from __future__ import annotations

import logging
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS

from .config import get_config
from .extensions import db, migrate, jwt, cors, scheduler
from .utils.errors import register_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # Logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Register blueprints
    from .auth.routes import auth_bp
    from .news.routes import news_bp
    from .news.bookmarks import bookmarks_bp
    from .news.newsletter import newsletter_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(news_bp, url_prefix="/api/news")
    app.register_blueprint(bookmarks_bp, url_prefix="/api/news")
    app.register_blueprint(newsletter_bp, url_prefix="/api/newsletter")

    # Health check
    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "news-aggregator-api",
                "db": "connected" if _check_db(app) else "unavailable",
            }
        )

    # Create tables and auto-seed if empty
    with app.app_context():
        try:
            db.create_all()
            from .models import Article
            count = Article.query.count()
            app.logger.info("DB check: %d articles found", count)
            if count == 0:
                app.logger.info("Database is empty - auto-seeding from news_data.json...")
                try:
                    from .seed_runner import run_seed
                    inserted = run_seed(app)
                    app.logger.info("Auto-seed complete: %d articles loaded", inserted)
                except Exception as seed_exc:
                    app.logger.error("Auto-seed failed: %s", seed_exc)
        except Exception as exc:
            app.logger.warning("db.create_all skipped: %s", exc)

    register_error_handlers(app)

    # Background scheduler for live updates
    if app.config.get("SCHEDULER_ENABLED", True) and not scheduler.running:
        try:
            from .services.scheduler import register_jobs
            register_jobs(app, scheduler)
            scheduler.start()
            app.logger.info("Scheduler started")
        except Exception as exc:
            app.logger.warning("Scheduler failed to start: %s", exc)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    return app


def _check_db(app: Flask) -> bool:
    try:
        db.session.execute(db.text("SELECT 1"))
        return True
    except Exception:
        return False
