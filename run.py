# run.py
import os
import sys
from app import create_app
from app.logger import get_logger

logger = get_logger()


def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting Gene Explorer application")
        app = create_app()

        # Get port from environment variable or use default
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

        if debug:
            logger.info(f"Running in debug mode on port {port}")
        else:
            logger.info(f"Running in production mode on port {port}")

        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()