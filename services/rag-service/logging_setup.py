"""
RAG Service Logging Configuration - Syslog Format Implementation

BUSINESS REQUIREMENT:
Centralized logging system that provides comprehensive monitoring and debugging
capabilities for the RAG (Retrieval-Augmented Generation) service operations.

TECHNICAL IMPLEMENTATION:
Implements RFC 3164 syslog format logging with structured output for:
1. Vector database operations and performance metrics
2. Document ingestion and retrieval operations
3. AI interaction learning and optimization tracking
4. Service health monitoring and error diagnostics
5. ChromaDB connection status and collection statistics

LOGGING ARCHITECTURE:
- **Console Output**: Real-time monitoring with syslog format
- **File Output**: Persistent logging to /var/log/course-creator/rag-service.log
- **Rotation**: 50MB max file size with 10 backup files
- **Format**: RFC 3164 syslog format with hostname, PID, service name, and locations info

LOG LEVELS AND USAGE:
- **DEBUG**: Detailed RAG operations, vector similarity scores, retrieval metrics
- **INFO**: Document additions, successful queries, learning operations
- **WARNING**: Fallback operations, performance degradation, configuration issues
- **ERROR**: Failed operations, ChromaDB connection issues, critical failures
- **CRITICAL**: Service initialization failures, complete system unavailability

RAG-SPECIFIC LOGGING FEATURES:
- Document ingestion tracking with metadata preservation
- Query performance metrics and retrieval effectiveness
- Learning operation success/failure tracking
- ChromaDB collection health and statistics
- Vector embedding generation performance monitoring
"""

import logging
import logging.handlers
import os
import socket
from datetime import datetime
from typing import Optional

def setup_logging(name: str = __name__, level: str = "INFO") -> logging.Logger:
    """
    Setup comprehensive logging for RAG service with syslog format
    
    SYSLOG FORMAT IMPLEMENTATION:
    Follows RFC 3164 format: "MMM DD HH:MM:SS hostname service[pid]: LEVEL - locations - message"
    
    RAG SERVICE SPECIFIC CONFIGURATION:
    - Enhanced metadata for vector operations
    - Performance metrics logging
    - ChromaDB operation tracking
    - Learning effectiveness monitoring
    
    LOGGING DESTINATIONS:
    1. Console output for real-time monitoring
    2. File output for persistent storage and analysis
    3. Optional syslog integration for centralized log management
    
    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance for RAG service operations
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Get hostname for syslog format
    hostname = socket.gethostname()
    service_name = "rag-service"
    pid = os.getpid()
    
    """
    SYSLOG FORMAT FORMATTER CONFIGURATION
    
    FORMAT STRUCTURE:
    - Timestamp: MMM DD HH:MM:SS format for syslog compatibility
    - Hostname: System hostname for distributed logging identification
    - Service: rag-service identifier for log filtering and analysis
    - PID: Process ID for multi-instance deployment tracking
    - Level: Log level for severity-based filtering
    - Locations: File and line number for debugging precision
    - Message: Actual log message with RAG operation details
    
    METADATA PRESERVATION:
    The format preserves all critical information needed for:
    - RAG operation debugging and optimization
    - Performance analysis and bottleneck identification
    - ChromaDB connection and collection health monitoring
    - Vector search effectiveness tracking
    """
    
    class SyslogFormatter(logging.Formatter):
        """
        Custom formatter for RFC 3164 syslog format with RAG-specific enhancements
        
        ENHANCEMENT FEATURES:
        - Consistent timestamp formatting across all log entries
        - Service identification for multi-service log aggregation
        - Locations information for precise debugging
        - Structured format for automated log parsing and analysis
        """
        
        def format(self, record):
            # Create timestamp in syslog format
            timestamp = datetime.fromtimestamp(record.created).strftime('%b %d %H:%M:%S')
            
            # Extract filename and line number for locations tracking
            filename = os.path.basename(record.pathname)
            locations = f"{filename}:{record.lineno}"
            
            # Format: "MMM DD HH:MM:SS hostname service[pid]: LEVEL - locations - message"
            formatted_message = f"{timestamp} {hostname} {service_name}[{pid}]: {record.levelname} - {locations} - {record.getMessage()}"
            
            return formatted_message
    
    formatter = SyslogFormatter()
    
    """
    CONSOLE HANDLER CONFIGURATION
    
    PURPOSE: Real-time monitoring and development debugging
    - Immediate visibility into RAG operations
    - Interactive debugging for vector search tuning
    - Real-time performance monitoring
    - Development workflow optimization
    """
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    """
    FILE HANDLER CONFIGURATION
    
    PURPOSE: Persistent logging for analysis and troubleshooting
    - Long-term RAG performance trend analysis
    - Historical query pattern analysis
    - ChromaDB operation audit trail
    - Learning effectiveness tracking over time
    
    ROTATION STRATEGY:
    - 50MB max size to balance detail with storage efficiency
    - 10 backup files for adequate historical coverage
    - Automatic rotation to prevent disk space issues
    """
    log_dir = os.getenv("LOG_DIR", "/var/log/course-creator")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "rag-service.log")
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # File gets more detailed logging
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    """
    RAG SERVICE INITIALIZATION LOGGING
    
    STARTUP INFORMATION:
    - Service identification and version info
    - ChromaDB configuration and connection status
    - Embedding model initialization status
    - Collection initialization and health status
    - Performance configuration and optimization settings
    """
    logger.info(f"RAG Service logging initialized - Console: {level}, File: DEBUG")
    logger.info(f"Log file: {log_file}")
    logger.info(f"ChromaDB path: {os.getenv('CHROMADB_PATH', '/app/chromadb_data')}")
    logger.info(f"Service PID: {pid}, Hostname: {hostname}")
    
    return logger

def log_rag_operation(logger: logging.Logger, operation: str, details: dict, duration_ms: Optional[float] = None):
    """
    Log RAG-specific operations with structured metadata
    
    OPERATION TRACKING:
    Provides consistent logging format for RAG operations including:
    - Document ingestion with metadata preservation
    - Vector search queries with performance metrics
    - Learning operations with effectiveness tracking
    - ChromaDB operations with health status
    
    Args:
        logger: Logger instance
        operation: Operation type (e.g., 'document_add', 'vector_search', 'learn_interaction')
        details: Operation-specific metadata and results
        duration_ms: Operation duration in milliseconds for performance tracking
    """
    
    log_message_parts = [f"RAG_OPERATION: {operation}"]
    
    # Add performance metrics if available
    if duration_ms is not None:
        log_message_parts.append(f"duration={duration_ms:.2f}ms")
    
    # Add operation details
    for key, value in details.items():
        if isinstance(value, (str, int, float, bool)):
            log_message_parts.append(f"{key}={value}")
        else:
            log_message_parts.append(f"{key}={str(value)[:100]}")  # Truncate long values
    
    log_message = " | ".join(log_message_parts)
    logger.info(log_message)

def log_performance_metric(logger: logging.Logger, metric_name: str, value: float, unit: str = "", context: dict = None):
    """
    Log performance metrics for RAG operations monitoring
    
    PERFORMANCE TRACKING:
    Standardized performance metric logging for:
    - Vector search response times and accuracy
    - Document ingestion throughput and success rates
    - ChromaDB connection performance and health
    - Embedding generation speed and quality metrics
    - Memory usage and optimization effectiveness
    
    Args:
        logger: Logger instance
        metric_name: Name of the performance metric
        value: Metric value
        unit: Unit of measurement (ms, %, MB, etc.)
        context: Additional context information
    """
    
    context_str = ""
    if context:
        context_parts = [f"{k}={v}" for k, v in context.items()]
        context_str = f" | {' | '.join(context_parts)}"
    
    logger.info(f"PERFORMANCE_METRIC: {metric_name}={value}{unit}{context_str}")

# Export logging utilities for RAG service components
__all__ = ['setup_logging', 'log_rag_operation', 'log_performance_metric']