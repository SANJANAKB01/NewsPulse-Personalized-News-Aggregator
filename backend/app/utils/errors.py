"""Custom error handlers and helpers."""
from flask import jsonify


class APIError(Exception):
    """Raised to return a JSON error response."""

    def __init__(self, message: str, status_code: int = 400, payload: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_response(self):
        body = {"error": self.message, **self.payload}
        return jsonify(body), self.status_code


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err: APIError):
        return err.to_response()

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_405(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_500(err):
        app.logger.exception("Unhandled server error: %s", err)
        return jsonify({"error": "Internal server error"}), 500
