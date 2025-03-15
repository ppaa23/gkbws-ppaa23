import sys
from app import create_app
from app.logger import get_logger

logger = get_logger()


def main():
    try:
        logger.info("Starting Gene Explorer application")
        app = create_app()

        logger.info("Running on http://127.0.0.1:5000")
        app.run(host='127.0.0.1', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()