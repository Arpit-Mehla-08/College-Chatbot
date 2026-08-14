"""Logging configuration for console and file output."""

import logging
import sys
from app.core.config import settings

def setup_logging():
    """Configure logging to output to both console and file with detailed format."""

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.is_development else logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with detailed format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # File handler (optional, for persistence)
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)

    # Detailed formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Set library loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)

    return logger

# Initialize on import
logger = setup_logging()
