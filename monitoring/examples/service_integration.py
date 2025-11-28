"""
Example: Integrating Observability into a FastAPI Service

This example demonstrates how to integrate the structured logging and metrics
collection into a FastAPI-based microservice.

Business Context:
- Enables comprehensive monitoring of service health and performance
- Provides detailed logging for debugging and audit trails
- Supports distributed tracing across microservices
- Facilitates proactive issue detection and resolution

Usage:
    1. Copy relevant sections to your service's main.py
    2. Adjust service name and configuration
    3. Add metrics to your endpoints and middleware
    4. Deploy and verify metrics appear in Prometheus
"""

import sys
import os
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Add shared directory to path for observability module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.observability import (
    setup_logging,
    get_logger,
    track_operation,
    log_request,
    set_correlation_id,
    generate_correlation_id
)


# ============================================================================
# STEP 1: Define Prometheus Metrics
# ============================================================================

# Request counter with labels for method, endpoint, and status code
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status_code']
)

# Request duration histogram for latency tracking
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['service', 'method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

# In-flight requests gauge
REQUESTS_IN_FLIGHT = Gauge(
    'http_requests_in_flight',
    'Current number of in-flight HTTP requests',
    ['service']
)

# Custom business metrics examples
USER_OPERATIONS = Counter(
    'user_operations_total',
    'Total user operations',
    ['service', 'operation', 'status']
)

DATABASE_OPERATIONS = Counter(
    'database_operations_total',
    'Total database operations',
    ['service', 'operation', 'table', 'status']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['service', 'operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['service', 'operation', 'status']
)

EXTERNAL_SERVICE_CALLS = Counter(
    'external_service_calls_total',
    'Total calls to external services',
    ['service', 'target_service', 'status']
)

EXTERNAL_SERVICE_DURATION = Histogram(
    'external_service_call_duration_seconds',
    'External service call duration in seconds',
    ['service', 'target_service'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)


# ============================================================================
# STEP 2: Setup Application with Observability
# ============================================================================

SERVICE_NAME = "example-service"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events including logging initialization.
    """
    # Startup: Initialize logging
    setup_logging(
        service_name=SERVICE_NAME,
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        enable_console=True,
        enable_json=True
    )

    logger = get_logger(__name__)
    logger.info(f"{SERVICE_NAME} starting up", extra={
        'extra_fields': {
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'version': '1.0.0'
        }
    })

    yield

    # Shutdown: Log graceful shutdown
    logger.info(f"{SERVICE_NAME} shutting down")


app = FastAPI(
    title=f"Course Creator - {SERVICE_NAME}",
    description="Example service with comprehensive observability",
    version="1.0.0",
    lifespan=lifespan
)

logger = get_logger(__name__)


# ============================================================================
# STEP 3: Add Metrics Endpoint
# ============================================================================

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Prometheus metrics endpoint.

    Exposes metrics in Prometheus format for scraping.
    This endpoint should be called by Prometheus every scrape_interval.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# STEP 4: Add Request Tracking Middleware
# ============================================================================

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """
    Middleware to track all HTTP requests with metrics and logging.

    Captures:
    - Request timing
    - Status codes
    - Correlation IDs for distributed tracing
    - Structured logging
    """
    # Generate/extract correlation ID
    correlation_id = request.headers.get('X-Correlation-ID', generate_correlation_id())
    set_correlation_id(correlation_id)

    # Extract user context if available
    user_id = request.headers.get('X-User-ID')
    org_id = request.headers.get('X-Organization-ID')

    # Track in-flight requests
    REQUESTS_IN_FLIGHT.labels(service=SERVICE_NAME).inc()

    # Time the request
    start_time = time.time()

    try:
        # Process request
        response = await call_next(request)
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            service=SERVICE_NAME,
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()

        REQUEST_DURATION.labels(
            service=SERVICE_NAME,
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        # Log request
        log_request(
            logger,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration=duration,
            user_id=int(user_id) if user_id else None,
            organization_id=int(org_id) if org_id else None,
            request_id=correlation_id
        )

        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = correlation_id

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Record error metrics
        REQUEST_COUNT.labels(
            service=SERVICE_NAME,
            method=request.method,
            endpoint=request.url.path,
            status_code=500
        ).inc()

        # Log error
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                'duration': duration,
                'correlation_id': correlation_id,
                'user_id': user_id,
                'organization_id': org_id,
                'extra_fields': {'error': str(e)}
            },
            exc_info=True
        )

        raise

    finally:
        # Decrement in-flight counter
        REQUESTS_IN_FLIGHT.labels(service=SERVICE_NAME).dec()


# ============================================================================
# STEP 5: Example Endpoints with Observability
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns service health status. Should be used by Docker healthcheck
    and load balancers.
    """
    logger.debug("Health check requested")
    return {"status": "healthy", "service": SERVICE_NAME}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    Example endpoint demonstrating operation tracking and custom metrics.
    """
    logger.info(f"Fetching user {user_id}", extra={
        'extra_fields': {'user_id': user_id}
    })

    # Track the operation with timing
    with track_operation("get_user", extra_fields={'user_id': user_id}):
        # Simulate database query
        with track_operation("database_query", extra_fields={'table': 'users'}):
            # Record database metrics
            query_start = time.time()

            try:
                # Simulate query (replace with actual database call)
                time.sleep(0.01)  # Simulate 10ms query
                user_data = {"id": user_id, "name": "Example User"}

                query_duration = time.time() - query_start

                DATABASE_OPERATIONS.labels(
                    service=SERVICE_NAME,
                    operation='SELECT',
                    table='users',
                    status='success'
                ).inc()

                DATABASE_QUERY_DURATION.labels(
                    service=SERVICE_NAME,
                    operation='SELECT',
                    table='users'
                ).observe(query_duration)

            except Exception as e:
                DATABASE_OPERATIONS.labels(
                    service=SERVICE_NAME,
                    operation='SELECT',
                    table='users',
                    status='error'
                ).inc()
                raise

        # Record successful user operation
        USER_OPERATIONS.labels(
            service=SERVICE_NAME,
            operation='get_user',
            status='success'
        ).inc()

        return user_data


@app.post("/users")
async def create_user(request: Request):
    """
    Example endpoint demonstrating creation operation tracking.
    """
    user_data = await request.json()

    logger.info("Creating new user", extra={
        'extra_fields': {'email': user_data.get('email')}
    })

    with track_operation("create_user", extra_fields=user_data):
        # Simulate database insert
        query_start = time.time()

        try:
            # Simulate insertion (replace with actual database call)
            time.sleep(0.02)  # Simulate 20ms insert
            new_user_id = 123

            query_duration = time.time() - query_start

            DATABASE_OPERATIONS.labels(
                service=SERVICE_NAME,
                operation='INSERT',
                table='users',
                status='success'
            ).inc()

            DATABASE_QUERY_DURATION.labels(
                service=SERVICE_NAME,
                operation='INSERT',
                table='users'
            ).observe(query_duration)

            USER_OPERATIONS.labels(
                service=SERVICE_NAME,
                operation='create_user',
                status='success'
            ).inc()

            logger.info(f"User created successfully", extra={
                'extra_fields': {
                    'user_id': new_user_id,
                    'email': user_data.get('email')
                }
            })

            return {"id": new_user_id, **user_data}

        except Exception as e:
            DATABASE_OPERATIONS.labels(
                service=SERVICE_NAME,
                operation='INSERT',
                table='users',
                status='error'
            ).inc()

            USER_OPERATIONS.labels(
                service=SERVICE_NAME,
                operation='create_user',
                status='error'
            ).inc()

            raise


@app.get("/users/{user_id}/external-data")
async def get_external_data(user_id: int):
    """
    Example endpoint demonstrating external service call tracking.
    """
    target_service = "external-api"

    logger.info(f"Calling external service for user {user_id}", extra={
        'extra_fields': {
            'user_id': user_id,
            'target_service': target_service
        }
    })

    call_start = time.time()

    try:
        # Simulate external API call
        time.sleep(0.15)  # Simulate 150ms external call
        external_data = {"external_id": "ext-123", "data": "example"}

        call_duration = time.time() - call_start

        EXTERNAL_SERVICE_CALLS.labels(
            service=SERVICE_NAME,
            target_service=target_service,
            status='success'
        ).inc()

        EXTERNAL_SERVICE_DURATION.labels(
            service=SERVICE_NAME,
            target_service=target_service
        ).observe(call_duration)

        logger.info(f"External service call successful", extra={
            'duration': call_duration,
            'extra_fields': {
                'target_service': target_service,
                'user_id': user_id
            }
        })

        return external_data

    except Exception as e:
        EXTERNAL_SERVICE_CALLS.labels(
            service=SERVICE_NAME,
            target_service=target_service,
            status='error'
        ).inc()

        logger.error(f"External service call failed", extra={
            'extra_fields': {
                'target_service': target_service,
                'user_id': user_id,
                'error': str(e)
            }
        }, exc_info=True)

        raise HTTPException(status_code=502, detail="External service unavailable")


# ============================================================================
# STEP 6: Run the Service
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Disable uvicorn's default logging to use our structured logging
    )
