"""
Logging setup for Organization Management Service
Follows centralized syslog format as defined in CLAUDE.md
"""
import logging
import logging.handlers
import os
import socket
from pathlib import Path


def setup_docker_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Setup centralized syslog format logging for Docker environment
    Format: Jul 31 08:46:30 hostname service[pid]: LEVEL - filename:line - message
    """
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Get hostname
    hostname = socket.gethostname()

    # Custom formatter for syslog format
    class SyslogFormatter(logging.Formatter):
        def format(self, record):
            # Get filename and line number
            filename = record.pathname
            line_number = record.lineno

            # Format timestamp (syslog style)
            timestamp = self.formatTime(record, '%b %d %H:%M:%S')

            # Build syslog format message
            message = f"{timestamp} {hostname} {service_name}[{os.getpid()}]: {record.levelname} - {filename}:{line_number} - {record.getMessage()}"

            return message

    formatter = SyslogFormatter()

    # Console handler (for Docker logs)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(console_handler)

    # File handler (for persistent logs)
    log_dir = Path("/var/log/course-creator")
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{service_name}.log"

    # Rotating file handler (50MB max, 10 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # File gets all levels
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger