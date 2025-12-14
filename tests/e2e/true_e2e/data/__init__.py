"""
Test Data Management for True E2E Testing

Provides:
- DataSeeder: Seeds test data directly into the database
- DatabaseVerifier: Verifies database state matches UI expectations

DESIGN PRINCIPLE:
Database manipulation is only allowed for test SETUP and VERIFICATION,
never during the actual test workflow. The test workflow must use
the real UI to create/modify data.
"""

from tests.e2e.true_e2e.data.data_seeder import DataSeeder
from tests.e2e.true_e2e.data.database_verifier import DatabaseVerifier

__all__ = ['DataSeeder', 'DatabaseVerifier']
