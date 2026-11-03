<<<<<<< HEAD
"""WSGI entry point for production (gunicorn, Render, Heroku, etc.).

Usage:
    gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
=======
"""WSGI entry point for production (gunicorn, Render, Heroku, etc.)."""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
>>>>>>> 385e7fb4506a8b97a43c05200c25bb5b106c63c5
