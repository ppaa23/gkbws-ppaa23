# app/__init__.py
from flask import Flask
from app.logger import get_logger

logger = get_logger()


def create_app():
    """Create and configure Flask application"""
    logger.info("Creating Flask application")
    app = Flask(__name__)

    # Import routes after app creation to avoid circular imports
    from app import routes
    routes.init_routes(app)

    logger.info("Flask application created successfully")
    return app