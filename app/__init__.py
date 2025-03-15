from flask import Flask
from app.logger import get_logger

logger = get_logger()


def create_app():
    logger.info("Creating Flask application")
    app = Flask(__name__)

    from app import routes
    routes.init_routes(app)

    logger.info("Flask application created successfully")
    return app