"""
Payment Service Dependency Injection Container

Business Context:
Manages lifecycle and wiring of all payment service dependencies. Uses lazy
initialization so resources (DB pool, providers, services) are only created
when first accessed. This follows the organization-management container pattern.

Technical Rationale:
- Singleton container initialized during FastAPI lifespan startup
- asyncpg pool with search_path set to course_creator,public
- Provider instances cached per-name to avoid re-creation
- Cleanup method ensures graceful shutdown of all connections
"""

import logging
from typing import Optional, Dict, Any

import asyncpg
from omegaconf import DictConfig

from payment_service.data_access.payment_dao import PaymentDAO
from payment_service.infrastructure.providers.base import PaymentProvider
from payment_service.infrastructure.providers.registry import get_provider
from payment_service.application.services.payment_orchestrator import PaymentOrchestrator
from payment_service.application.services.subscription_service import SubscriptionService
from payment_service.application.services.invoice_service import InvoiceService
from payment_service.application.services.billing_service import BillingService


class Container:
    """
    Dependency injection container for the payment service.

    All dependencies are lazily initialized: created on first access and
    cached for the lifetime of the container.
    """

    def __init__(self, config: DictConfig):
        self._config = config
        self._logger = logging.getLogger(__name__)

        self._connection_pool: Optional[asyncpg.Pool] = None
        self._dao: Optional[PaymentDAO] = None
        self._providers: Dict[str, PaymentProvider] = {}

        self._payment_orchestrator: Optional[PaymentOrchestrator] = None
        self._subscription_service: Optional[SubscriptionService] = None
        self._invoice_service: Optional[InvoiceService] = None
        self._billing_service: Optional[BillingService] = None

    async def initialize(self) -> None:
        """Initialize core resources (DB pool)."""
        await self.get_connection_pool()
        self._logger.info("Payment service container initialized")

    async def get_connection_pool(self) -> asyncpg.Pool:
        """Get or create the asyncpg connection pool."""
        if self._connection_pool is None:
            database_config = self._config.database
            self._connection_pool = await asyncpg.create_pool(
                host=database_config.host,
                port=database_config.port,
                user=database_config.user,
                password=database_config.password,
                database=database_config.name,
                min_size=database_config.get('min_connections', 5),
                max_size=database_config.get('max_connections', 20),
                command_timeout=database_config.get('command_timeout', 60),
                server_settings={'search_path': 'course_creator,public'}
            )
            self._logger.info("Database connection pool created")
        return self._connection_pool

    async def get_dao(self) -> PaymentDAO:
        """Get the payment DAO instance."""
        if self._dao is None:
            pool = await self.get_connection_pool()
            self._dao = PaymentDAO(pool)
        return self._dao

    def get_provider(self, name: str) -> PaymentProvider:
        """
        Get a cached provider instance by name.

        Provider-specific config is read from config.yaml under
        payment.providers.<name>.
        """
        if name not in self._providers:
            provider_configs = self._config.get('payment', {}).get('providers', {})
            provider_config = provider_configs.get(name, {})
            self._providers[name] = get_provider(name, dict(provider_config) if provider_config else {})
            self._logger.info(f"Initialized payment provider: {name}")
        return self._providers[name]

    async def get_payment_orchestrator(self) -> PaymentOrchestrator:
        """Get the payment orchestrator service."""
        if self._payment_orchestrator is None:
            dao = await self.get_dao()
            self._payment_orchestrator = PaymentOrchestrator(dao, self)
        return self._payment_orchestrator

    async def get_subscription_service(self) -> SubscriptionService:
        """Get the subscription service."""
        if self._subscription_service is None:
            dao = await self.get_dao()
            self._subscription_service = SubscriptionService(dao, self)
        return self._subscription_service

    async def get_invoice_service(self) -> InvoiceService:
        """Get the invoice service."""
        if self._invoice_service is None:
            dao = await self.get_dao()
            self._invoice_service = InvoiceService(dao)
        return self._invoice_service

    async def get_billing_service(self) -> BillingService:
        """Get the billing service."""
        if self._billing_service is None:
            dao = await self.get_dao()
            self._billing_service = BillingService(dao)
        return self._billing_service

    async def cleanup(self) -> None:
        """Release all resources on shutdown."""
        if self._connection_pool:
            await self._connection_pool.close()
            self._logger.info("Database connection pool closed")
        self._providers.clear()


_container: Optional[Container] = None


def initialize_container(config: DictConfig) -> Container:
    """Create and store the global container singleton."""
    global _container
    _container = Container(config)
    return _container


def get_container() -> Container:
    """Retrieve the global container (must be initialized first)."""
    if _container is None:
        raise RuntimeError("Container not initialized. Call initialize_container first.")
    return _container


async def cleanup_container():
    """Cleanup the global container."""
    global _container
    if _container:
        await _container.cleanup()
        _container = None
