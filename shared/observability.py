"""
Structured Logging and Observability Configuration for Course Creator Platform

This module provides comprehensive logging, metrics, and tracing configuration
for all microservices in the platform. It implements structured logging with
JSON formatting, correlation IDs, and integration with Prometheus metrics.

Business Context:
- Enables centralized log aggregation and analysis
- Provides real-time monitoring and alerting capabilities
- Supports distributed tracing across microservices
- Facilitates debugging and performance optimization
- Ensures compliance with audit and security requirements

Technical Implementation:
- Uses Python's logging module with custom formatters
- Integrates with Prometheus for metrics collection
- Supports correlation ID tracking for request tracing
- Provides context managers for operation timing
- Includes utility functions for common logging patterns

Usage:
    from shared.observability import setup_logging, get_logger, track_operation

    # Setup logging at application startup
    setup_logging(service_name="user-management", log_level="INFO")

    # Get a logger for your module
    logger = get_logger(__name__)

    # Log structured messages
    logger.info("User created", extra={"user_id": user.id, "email": user.email})

    # Track operation timing
    with track_operation("database_query"):
        result = db.query(...)
"""

import logging
import logging.handlers
import json
import sys
import time
import os
import uuid
from typing import Any, Dict, Optional
from contextlib import contextmanager
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON objects with consistent structure including
    timestamp, level, message, service name, correlation ID, and custom fields.

    This enables easy parsing and analysis by log aggregation systems like
    ELK stack, Splunk, or CloudWatch Logs.
    """

    def __init__(self, service_name: str):
        """
        Initialize JSON formatter with service identification.

        Args:
            service_name: Name of the microservice generating logs
        """
        super().__init__()
        self.service_name = service_name
        self.hostname = os.getenv('HOSTNAME', 'unknown')
        self.environment = os.getenv('ENVIRONMENT', 'development')

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Build base log entry
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': self.service_name,
            'environment': self.environment,
            'hostname': self.hostname,
        }

        # Add correlation ID if present
        correlation_id = getattr(record, 'correlation_id', None)
        if correlation_id:
            log_entry['correlation_id'] = correlation_id

        # Add request ID if present (for HTTP requests)
        request_id = getattr(record, 'request_id', None)
        if request_id:
            log_entry['request_id'] = request_id

        # Add user ID if present
        user_id = getattr(record, 'user_id', None)
        if user_id:
            log_entry['user_id'] = user_id

        # Add organization ID if present
        org_id = getattr(record, 'organization_id', None)
        if org_id:
            log_entry['organization_id'] = org_id

        # Add file and line information
        log_entry['location'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }

        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # Add any custom fields from extra parameter
        if hasattr(record, 'extra_fields'):
            log_entry['data'] = record.extra_fields

        # Add duration if this is a performance log
        duration = getattr(record, 'duration', None)
        if duration is not None:
            log_entry['duration_ms'] = round(duration * 1000, 2)

        # Add operation name if present
        operation = getattr(record, 'operation', None)
        if operation:
            log_entry['operation'] = operation

        return json.dumps(log_entry)


class CorrelationIDFilter(logging.Filter):
    """
    Logging filter to add correlation IDs to log records.

    Correlation IDs enable tracking requests across multiple microservices
    and operations, facilitating distributed tracing and debugging.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to log record if not already present.

        Args:
            record: Log record to enhance

        Returns:
            True (always allow record to pass)
        """
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = _get_correlation_id()
        return True


# Thread-local storage for correlation IDs
import threading
_correlation_context = threading.local()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for current thread/request context.

    Args:
        correlation_id: Unique identifier for request correlation
    """
    _correlation_context.correlation_id = correlation_id


def _get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from current context.

    Returns:
        Correlation ID if set, None otherwise
    """
    return getattr(_correlation_context, 'correlation_id', None)


def generate_correlation_id() -> str:
    """
    Generate new correlation ID.

    Returns:
        UUID4-based correlation ID
    """
    return str(uuid.uuid4())


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_json: bool = True
) -> None:
    """
    Configure structured logging for the service.

    Sets up logging with JSON formatting, file rotation, and console output.
    Should be called once at application startup.

    Args:
        service_name: Name of the microservice
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, uses /var/log/course-creator/{service_name}.log)
        enable_console: Whether to log to console/stdout
        enable_json: Whether to use JSON formatting (True) or plain text (False)

    Example:
        setup_logging(
            service_name="user-management",
            log_level="INFO",
            enable_console=True,
            enable_json=True
        )
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if enable_json:
        formatter = JSONFormatter(service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Add correlation ID filter
    correlation_filter = CorrelationIDFilter()

    # Setup console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(correlation_filter)
        root_logger.addHandler(console_handler)

    # Setup file handler with rotation
    if log_file is None:
        log_dir = os.getenv('LOG_DIR', '/var/log/course-creator')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'{service_name}.log')

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # If file logging fails, log to console only
        console_logger = logging.getLogger(__name__)
        console_logger.warning(
            f"Failed to setup file logging: {e}. Using console logging only."
        )

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized for {service_name}",
        extra={
            'extra_fields': {
                'log_level': log_level,
                'log_file': log_file,
                'json_enabled': enable_json
            }
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Operation completed", extra={'extra_fields': {'count': 42}})
    """
    return logging.getLogger(name)


@contextmanager
def track_operation(
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    log_level: str = "INFO",
    extra_fields: Optional[Dict[str, Any]] = None
):
    """
    Context manager to track operation timing and log results.

    Measures execution time and logs start/completion with duration.
    Useful for performance monitoring and identifying bottlenecks.

    Args:
        operation_name: Name of the operation being tracked
        logger: Logger instance (if None, uses root logger)
        log_level: Log level for operation messages
        extra_fields: Additional fields to include in log entries

    Yields:
        Dictionary where operation can store result data

    Example:
        with track_operation("database_query", extra_fields={"table": "users"}):
            result = db.query("SELECT * FROM users")

        # Automatically logs:
        # - Operation start
        # - Operation completion with duration
        # - Any exceptions that occur
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if extra_fields is None:
        extra_fields = {}

    level = getattr(logging, log_level.upper())
    start_time = time.time()

    # Create context for operation results
    context = {}

    # Log operation start
    logger.log(
        level,
        f"Starting operation: {operation_name}",
        extra={
            'operation': operation_name,
            'extra_fields': extra_fields
        }
    )

    try:
        yield context

        # Log successful completion
        duration = time.time() - start_time
        result_fields = {**extra_fields, **context}

        logger.log(
            level,
            f"Completed operation: {operation_name}",
            extra={
                'operation': operation_name,
                'duration': duration,
                'extra_fields': result_fields
            }
        )

    except Exception as e:
        # Log operation failure
        duration = time.time() - start_time

        logger.exception(
            f"Failed operation: {operation_name}",
            extra={
                'operation': operation_name,
                'duration': duration,
                'extra_fields': {**extra_fields, 'error': str(e)}
            }
        )
        raise


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    request_id: Optional[str] = None
) -> None:
    """
    Log HTTP request with structured fields.

    Standardized logging for HTTP requests across all services.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration: Request duration in seconds
        user_id: ID of authenticated user (if applicable)
        organization_id: ID of user's organization (if applicable)
        request_id: Unique request identifier

    Example:
        log_request(
            logger,
            method="POST",
            path="/api/v1/users",
            status_code=201,
            duration=0.125,
            user_id=42,
            request_id="abc-123"
        )
    """
    extra_fields = {
        'http_method': method,
        'http_path': path,
        'http_status': status_code,
    }

    extra_record = {
        'duration': duration,
        'extra_fields': extra_fields
    }

    if request_id:
        extra_record['request_id'] = request_id
    if user_id:
        extra_record['user_id'] = user_id
    if organization_id:
        extra_record['organization_id'] = organization_id

    # Determine log level based on status code
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO

    logger.log(
        level,
        f"{method} {path} - {status_code}",
        extra=extra_record
    )


def log_database_query(
    logger: logging.Logger,
    query_type: str,
    table: str,
    duration: float,
    rows_affected: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Log database query execution.

    Standardized logging for database operations to track performance
    and identify slow queries.

    Args:
        logger: Logger instance
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Database table name
        duration: Query duration in seconds
        rows_affected: Number of rows affected/returned
        error: Error message if query failed

    Example:
        log_database_query(
            logger,
            query_type="SELECT",
            table="users",
            duration=0.045,
            rows_affected=10
        )
    """
    extra_fields = {
        'query_type': query_type,
        'table': table,
    }

    if rows_affected is not None:
        extra_fields['rows_affected'] = rows_affected

    if error:
        extra_fields['error'] = error
        level = logging.ERROR
        message = f"Database query failed: {query_type} {table}"
    else:
        level = logging.INFO
        message = f"Database query: {query_type} {table}"

    logger.log(
        level,
        message,
        extra={
            'duration': duration,
            'operation': 'database_query',
            'extra_fields': extra_fields
        }
    )


def log_service_call(
    logger: logging.Logger,
    service_name: str,
    endpoint: str,
    duration: float,
    status_code: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Log inter-service communication.

    Track calls between microservices for distributed tracing and
    performance analysis.

    Args:
        logger: Logger instance
        service_name: Name of the called service
        endpoint: Service endpoint path
        duration: Call duration in seconds
        status_code: HTTP status code received
        error: Error message if call failed

    Example:
        log_service_call(
            logger,
            service_name="user-management",
            endpoint="/api/v1/users/me",
            duration=0.089,
            status_code=200
        )
    """
    extra_fields = {
        'target_service': service_name,
        'endpoint': endpoint,
    }

    if status_code:
        extra_fields['status_code'] = status_code

    if error:
        extra_fields['error'] = error
        level = logging.ERROR
        message = f"Service call failed: {service_name}{endpoint}"
    else:
        level = logging.INFO
        message = f"Service call: {service_name}{endpoint}"

    logger.log(
        level,
        message,
        extra={
            'duration': duration,
            'operation': 'service_call',
            'extra_fields': extra_fields
        }
    )


# Metrics helpers for Prometheus integration
# These can be expanded based on prometheus_client library

def record_metric(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """
    Record a metric value (placeholder for Prometheus integration).

    This function provides a standardized interface for recording metrics.
    Implementation can be extended to use prometheus_client library.

    Args:
        metric_name: Name of the metric
        value: Metric value
        labels: Optional labels for the metric

    Example:
        record_metric("request_duration_seconds", 0.125, {"method": "POST", "endpoint": "/users"})
    """
    # Placeholder - implement with prometheus_client when added to dependencies
    logger = logging.getLogger(__name__)
    logger.debug(
        f"Metric recorded: {metric_name}",
        extra={
            'extra_fields': {
                'metric_name': metric_name,
                'value': value,
                'labels': labels or {}
            }
        }
    )


# Export commonly used functions
__all__ = [
    'setup_logging',
    'get_logger',
    'track_operation',
    'log_request',
    'log_database_query',
    'log_service_call',
    'set_correlation_id',
    'generate_correlation_id',
    'record_metric',
]
