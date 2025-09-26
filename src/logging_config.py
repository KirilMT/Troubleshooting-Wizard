import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logging() -> None:
    """Configures a robust logging system for the application."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure the root logger with more detailed formatter
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for development

    # File handler with daily rotation
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # Console handler for real-time feedback during development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logging.info("Logging system initialized with DEBUG level")
