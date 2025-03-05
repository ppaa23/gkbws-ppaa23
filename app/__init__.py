# app/__init__.py
from flask import Flask


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Import routes after app creation to avoid circular imports
    from app import routes
    routes.init_routes(app)

    return app