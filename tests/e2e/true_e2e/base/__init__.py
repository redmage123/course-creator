"""
Base classes for True E2E Testing

Provides:
- TrueE2EBaseTest: Base test class with anti-pattern detection
- ReactWaitHelpers: Utilities for waiting on React Query state
"""

from tests.e2e.true_e2e.base.true_e2e_base import TrueE2EBaseTest
from tests.e2e.true_e2e.base.react_waits import ReactWaitHelpers

__all__ = ['TrueE2EBaseTest', 'ReactWaitHelpers']
