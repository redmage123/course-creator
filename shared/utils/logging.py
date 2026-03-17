"""Logging configuration for course creator services"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    service_name: Optional[str] = None
) -> logging.Logger:
    """Setup logging configuration"""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    logger = logging.getLogger(service_name or "course-creator")
    logger.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)
    
    return logger
