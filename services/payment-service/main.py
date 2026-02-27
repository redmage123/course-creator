"""
Payment Service — Application Factory and Entry Point

Business Context:
The payment service provides provider-agnostic payment processing for the
Course Creator Platform. It manages subscriptions, invoices, payments, and
billing for organizations. Payment providers (Stripe, Square, etc.) can be
plugged in via the Strategy Pattern without modifying existing code.

Technical Rationale:
- FastAPI app factory with async lifespan for startup/shutdown
- Hydra configuration management
- HTTPS via self-signed certificates (platform standard)
- Global exception handler maps PaymentBaseException → HTTP responses
"""

import os
import sys
import logging
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

import hydra
import uvicorn
from omegaconf import DictConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from payment_service.exceptions import PaymentBaseException
from payment_service.infrastructure.container import (
    initialize_container,
    get_container,
    cleanup_container,
)
from middleware.error_handling import payment_exception_handler
from middleware.audit_logging import AuditLoggingMiddleware

from api.plan_endpoints import router as plan_router
from api.subscription_endpoints import router as subscription_router
from api.invoice_endpoints import router as invoice_router
from api.payment_endpoints import router as payment_router
from api.billing_endpoints import router as billing_router
from api.webhook_endpoints import router as webhook_router

container = None
current_config: Optional[DictConfig] = None


def setup_docker_logging(service_name: str, log_level: str = "INFO"):
    """Configure structured logging for Docker containers."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter(
        f"%(asctime)s [{service_name}] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan — initialize container on startup, cleanup on shutdown."""
    global container
    logging.info("Initializing Payment Service...")
    container = initialize_container(current_config)
    await container.initialize()
    logging.info("Payment Service container initialized")
    yield
    logging.info("Shutting down Payment Service...")
    if container:
        await cleanup_container()
        logging.info("Payment Service container cleaned up")


def create_app(config: DictConfig = None) -> FastAPI:
    """Application factory for the Payment Service."""
    global current_config
    current_config = config or {}

    app = FastAPI(
        title="Payment Service",
        description="Provider-agnostic payment processing for the Course Creator Platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "https://localhost:3000,https://localhost:3001"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_middleware(AuditLoggingMiddleware)

    app.add_exception_handler(PaymentBaseException, payment_exception_handler)

    app.include_router(plan_router)
    app.include_router(subscription_router)
    app.include_router(invoice_router)
    app.include_router(payment_router)
    app.include_router(billing_router)
    app.include_router(webhook_router)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "payment-service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }

    return app


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point using Hydra configuration."""
    global current_config
    current_config = cfg

    service_name = os.environ.get("SERVICE_NAME", "payment-service")
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    setup_docker_logging(service_name, log_level)

    port = cfg.get("server", {}).get("port", 8018)
    host = cfg.get("server", {}).get("host", "0.0.0.0")

    logging.info("Starting Payment Service on %s:%s", host, port)

    global app
    app = create_app(cfg)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
        ssl_keyfile="/app/ssl/nginx-selfsigned.key",
        ssl_certfile="/app/ssl/nginx-selfsigned.crt",
    )


app = create_app()

if __name__ == "__main__":
    main()
