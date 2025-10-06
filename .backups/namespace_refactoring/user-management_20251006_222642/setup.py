"""
Centralized Logging Setup for Course Creator Platform
Implements syslog format logging with centralized log directory
"""
import logging
import logging.config
import os
import socket
import sys
from pathlib import Path
from typing import Dict, Any
import yaml


class SyslogFormatter(logging.Formatter):
    """Custom formatter that adds hostname and follows syslog format"""
    
    def __init__(self, service_name: str):
        self.hostname = socket.gethostname()
        self.service_name = service_name
        super().__init__()
    
    def format(self, record):
        # Add hostname to the record
        record.hostname = self.hostname
        record.service_name = self.service_name
        
        # Syslog format: timestamp hostname service[pid]: level - message
        formatted_time = self.formatTime(record, "%b %d %H:%M:%S")
        
        if record.levelno >= logging.ERROR:
            level_name = "ERROR"
        elif record.levelno >= logging.WARNING:
            level_name = "WARN"
        elif record.levelno >= logging.INFO:
            level_name = "INFO"
        else:
            level_name = "DEBUG"
        
        # Include filename and line number for detailed logging
        if hasattr(record, 'filename') and hasattr(record, 'lineno'):
            location = f"{record.filename}:{record.lineno}"
            message = f"{formatted_time} {self.hostname} {self.service_name}[{os.getpid()}]: {level_name} - {location} - {record.getMessage()}"
        else:
            message = f"{formatted_time} {self.hostname} {self.service_name}[{os.getpid()}]: {level_name} - {record.getMessage()}"
        
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return message


def setup_logging(service_name: str, log_level: str = "INFO", log_dir: str = "/var/log/course-creator") -> None:
    """
    Setup centralized logging for a service with syslog format
    
    Args:
        service_name: Name of the service (e.g., 'user-management', 'course-generator')
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory to write log files
    """
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    log_file = Path(log_dir) / f"{service_name}.log"
    
    # Create custom formatters
    console_formatter = SyslogFormatter(service_name)
    file_formatter = SyslogFormatter(service_name)
    
    # Configure handlers
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'syslog',
            'stream': sys.stdout
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed_syslog',
            'filename': str(log_file),
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'encoding': 'utf8'
        }
    }
    
    # Add syslog handler if available (Linux/Unix systems)
    if hasattr(logging.handlers, 'SysLogHandler'):
        try:
            handlers['syslog'] = {
                'class': 'logging.handlers.SysLogHandler',
                'level': 'INFO',
                'formatter': 'syslog',
                'address': ('localhost', 514),
                'facility': 'user'
            }
        except Exception:
            # Syslog not available, skip
            pass
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'syslog': {
                '()': SyslogFormatter,
                'service_name': service_name
            },
            'detailed_syslog': {
                '()': SyslogFormatter,
                'service_name': service_name
            }
        },
        'handlers': handlers,
        'loggers': {
            service_name: {
                'level': 'DEBUG',
                'handlers': list(handlers.keys()),
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': list(handlers.keys()),
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': list(handlers.keys()),
                'propagate': False
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': list(handlers.keys()),
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': list(handlers.keys())
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    # Get logger and log startup message
    logger = logging.getLogger(service_name)
    logger.info(f"Logging initialized for {service_name} - Level: {log_level} - Log file: {log_file}")
    
    return logger


def setup_docker_logging(service_name: str, log_level: str = "INFO") -> None:
    """
    Setup logging specifically for Docker containers with volume mounts
    """
    # Check if running in Docker (common environment variable)
    if os.environ.get('DOCKER_CONTAINER', 'false').lower() == 'true':
        log_dir = "/var/log/course-creator"
    else:
        # Fallback to local logs directory for development
        log_dir = os.path.join(os.getcwd(), "logs")
        
    return setup_logging(service_name, log_level, log_dir)


if __name__ == "__main__":
    # Test the logging setup
    logger = setup_logging("test-service", "DEBUG")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")