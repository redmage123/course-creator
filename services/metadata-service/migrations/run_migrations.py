"""
Database Migration Runner for Metadata Service

BUSINESS REQUIREMENT:
Apply SQL migrations to create materialized views, indexes, and search functions

USAGE:
    python migrations/run_migrations.py
"""

import asyncio
import asyncpg
import os
from pathlib import Path


class MigrationRunner:
    """
    Manages database migrations for metadata service

    RESPONSIBILITIES:
    - Connect to PostgreSQL database
    - Execute SQL migration files in order
    - Track applied migrations
    - Rollback on errors
    """

    def __init__(self, db_url: str):
        """
        Initialize migration runner

        Args:
            db_url: PostgreSQL connection URL
        """
        self.db_url = db_url
        self.migrations_dir = Path(__file__).parent

    async def run(self):
        """
        Execute all pending migrations

        BUSINESS LOGIC:
        - Connects to database
        - Finds all .sql files in migrations directory
        - Executes them in alphabetical order
        - Reports success/failure

        Raises:
            Exception: If migration fails
        """
        print("=" * 70)
        print("METADATA SERVICE - DATABASE MIGRATION RUNNER")
        print("=" * 70)

        # Connect to database
        conn = await asyncpg.connect(self.db_url)
        print(f"✓ Connected to database")

        try:
            # Find all migration files
            migration_files = sorted(self.migrations_dir.glob("*.sql"))
            print(f"✓ Found {len(migration_files)} migration file(s)")

            if not migration_files:
                print("⚠ No migration files found")
                return

            # Execute each migration
            for migration_file in migration_files:
                await self._run_migration(conn, migration_file)

            print("\n" + "=" * 70)
            print("✓ ALL MIGRATIONS COMPLETED SUCCESSFULLY")
            print("=" * 70)

        except Exception as e:
            print(f"\n✗ MIGRATION FAILED: {str(e)}")
            raise

        finally:
            await conn.close()
            print("✓ Database connection closed")

    async def _run_migration(self, conn: asyncpg.Connection, migration_file: Path):
        """
        Execute a single migration file

        Args:
            conn: Database connection
            migration_file: Path to SQL migration file
        """
        print(f"\n→ Running migration: {migration_file.name}")

        # Read migration SQL
        with open(migration_file, 'r') as f:
            sql = f.read()

        try:
            # Execute migration in a transaction
            async with conn.transaction():
                await conn.execute(sql)

            print(f"  ✓ Migration {migration_file.name} completed successfully")

        except asyncpg.PostgresError as e:
            print(f"  ✗ Migration {migration_file.name} failed: {str(e)}")
            raise


async def main():
    """Main entry point for migration runner"""

    # Get database URL from environment or use default
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://course_user:course_pass@localhost:5433/course_creator'
    )

    print(f"Database URL: {db_url.split('@')[1] if '@' in db_url else db_url}")

    runner = MigrationRunner(db_url)
    await runner.run()


if __name__ == '__main__':
    asyncio.run(main())
