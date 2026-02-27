"""
Provider Registry — maps provider names to implementation classes.

Business Context:
Acts as the single source of truth for which payment providers are available
on the platform. When an organization's subscription specifies a provider
(e.g., 'stripe'), the orchestrator uses this registry to instantiate the
correct implementation at runtime.

Technical Rationale:
Centralizing provider registration here means adding a new payment gateway
requires exactly two steps:
1. Create a new module implementing the PaymentProvider ABC.
2. Add a single entry to PROVIDER_REGISTRY in this file.

No other code in the system needs to change — the orchestrator, webhook
router, and domain services all work through the abstract interface.
"""

from typing import Dict, Type, Any
import logging

from payment_service.infrastructure.providers.base import PaymentProvider
from payment_service.infrastructure.providers.null_provider import NullProvider
from payment_service.exceptions import PaymentProviderNotFoundError, PaymentProviderConfigError

logger = logging.getLogger(__name__)

PROVIDER_REGISTRY: Dict[str, Type[PaymentProvider]] = {
    "null": NullProvider,
    # "stripe": StripeProvider,   # Add when implementing Stripe
    # "square": SquareProvider,   # Add when implementing Square
}


def get_provider(name: str, config: Dict[str, Any] = None) -> PaymentProvider:
    """
    Factory function to instantiate a payment provider by name.

    Looks up the provider class in PROVIDER_REGISTRY and instantiates it
    with the supplied configuration. Raises domain-specific exceptions if
    the provider is not registered or if instantiation fails.

    To add a new provider:
    1. Create provider_name_provider.py implementing PaymentProvider ABC
    2. Add entry to PROVIDER_REGISTRY above
    3. Pass provider-specific config (API keys, webhook secrets, etc.)

    Args:
        name: Registered provider name (e.g., 'null', 'stripe', 'square').
        config: Provider-specific configuration dictionary. For example,
                Stripe would expect {'api_key': '...', 'webhook_secret': '...'}.

    Returns:
        An instantiated PaymentProvider ready for use.

    Raises:
        PaymentProviderNotFoundError: If the provider name is not in the registry.
        PaymentProviderConfigError: If the provider fails to initialize with the
                                    given configuration.
    """
    cls = PROVIDER_REGISTRY.get(name)
    if cls is None:
        logger.error("Payment provider not found in registry: '%s'. Available: %s", name, list(PROVIDER_REGISTRY.keys()))
        raise PaymentProviderNotFoundError(name)

    config = config or {}
    try:
        provider = cls(config)
        logger.info("Instantiated payment provider: '%s' (%s)", name, cls.__name__)
        return provider
    except PaymentProviderConfigError:
        raise
    except Exception as e:
        logger.error("Failed to instantiate payment provider '%s': %s", name, str(e))
        raise PaymentProviderConfigError(name, str(e), original_exception=e)
