"""
Simplified Centralized Logging Setup for Course Creator Platform
"""
import logging
import logging.handlers
import os
import socket
import sys
from pathlib import Path


def setup_syslog_logging(service_name: str, log_level: str = "INFO", log_dir: str = "/var/log/course-creator") -> logging.Logger:
    """
    Setup centralized logging for a service with syslog format
    
    Args:
        service_name: Name of the service
        log_level: Logging level
        log_dir: Directory to write log files
    """
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Get hostname for syslog format
    hostname = socket.gethostname()
    pid = os.getpid()
    
    # Syslog format: timestamp hostname service[pid]: level - message
    syslog_format = f"%(asctime)s {hostname} {service_name}[{pid}]: %(levelname)s - %(message)s"
    detailed_format = f"%(asctime)s {hostname} {service_name}[{pid}]: %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    
    # Configure root logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with syslog format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter(
        syslog_format,
        datefmt="%b %d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with detailed format
    log_file = Path(log_dir) / f"{service_name}.log"
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            detailed_format,
            datefmt="%b %d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
    
    # Setup other loggers to use the same format
    for logger_name in ['uvicorn', 'uvicorn.access', 'fastapi']:
        other_logger = logging.getLogger(logger_name)
        other_logger.handlers.clear()
        other_logger.addHandler(console_handler)
        if 'file_handler' in locals():
            other_logger.addHandler(file_handler)
        other_logger.setLevel(logging.INFO)
        other_logger.propagate = False
    
    # Set root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    if 'file_handler' in locals():
        root_logger.addHandler(file_handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    logger.info(f"Logging initialized for {service_name} - Level: {log_level} - Log file: {log_file}")
    return logger


def setup_docker_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging specifically for Docker containers
    """
    # Check if running in Docker
    if os.environ.get('DOCKER_CONTAINER', 'false').lower() == 'true':
        log_dir = "/var/log/course-creator"
    else:
        # Fallback to local logs directory for development
        log_dir = os.path.join(os.getcwd(), "logs")
        
    return setup_syslog_logging(service_name, log_level, log_dir)