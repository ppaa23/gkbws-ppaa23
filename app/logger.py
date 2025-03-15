# app/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with console and file handlers"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create logger
        self.logger = logging.getLogger('gene_explorer')
        self.logger.setLevel(logging.INFO)

        # Prevent propagation to the root logger (suppress console output)
        self.logger.propagate = False

        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File handler (rotating to keep log size manageable)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger


# Convenience function to get logger instance
def get_logger():
    return Logger().get_logger()