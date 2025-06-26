# logging.py: Utilities for logging events, errors, and process information in the supply chain system.
# Provides standardized logging setup for use across modules and the Streamlit app.

import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a configured logger for the project.
    Step-by-step:
    1. Get or create a logger with the given name.
    2. If the logger has no handlers, add a StreamHandler with a custom formatter.
    3. Set the logger level to INFO.
    4. Return the logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger 