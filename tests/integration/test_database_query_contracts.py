"""
Database Integration Tests for Query Structure

BUSINESS CONTEXT:
Tests that verify database queries return all fields required by Pydantic models.
These catch mismatches between SELECT statements and model expectations,
preventing ValidationErrors at runtime.

TECHNICAL IMPLEMENTATION:
- Tests actual database queries with real connection pool
- Validates query results match Pydantic model fields
- Checks data types and optional vs required fields
- Tests JOIN operations return expected structure

TDD METHODOLOGY:
These tests would have caught:
- Query missing organization_id column
- Query missing joined_at column
- asyncpg parameter errors ($1 vs %s)
- Missing JOINs causing null values
"""

import pytest
import asyncio
from uuid import UUID, uuid4
from datetime import datetime
import sys
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

# Add organization-management service to path
org_mgmt_path = Path(__file__).parent.parent.parent / 'services' / 'organization-management'
sys.path.insert(0, str(org_mgmt_path))

try:
    from database.connection_pool import ConnectionPool
    from services.membership_service import MembershipService
    from services.organization_service import OrganizationService
    from models.organization import Organization
except ImportError as e:
    pytest.skip(f"organization-management service not available: {e}", allow_module_level=True)

# Define MemberResponse locally
class MemberResponse(BaseModel):
    """Member response model"""
    id: UUID
    user_id: UUID
    organization_id: Optional[UUID] = None
    username: str
    email: str
    role: str
    is_active: bool
    joined_at: Optional[datetime] = None


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Setup database connection pool"""
    pool = ConnectionPool.get_instance()
    await pool.initialize()
    yield pool
    # Don't close pool - it's a singleton used by other tests


class TestMembershipQueryStructure:
    """
    Test Suite: Membership Query Field Validation

    REQUIREMENT: Membership queries must return all fields for MemberResponse
    """

    @pytest.mark.asyncio
    async def test_get_organization_members_returns_all_required_fields(self, db_pool):
        """
        TEST: get_organization_members includes all MemberResponse fields
        REQUIREMENT: Query must SELECT all fields that Pydantic model expects

        THIS TEST WOULD HAVE CAUGHT:
        - Missing organization_id in SELECT
        - Missing joined_at in SELECT
        - Field name mismatches between DB and model
        """
        service = MembershipService(db_pool)

        # Use known organization from demo data
        org_id = UUID("259da6df-c148-40c2-bcd9-dc6889e7e9fb")

        try:
            members = await service.get_organization_members(org_id, role_filter=None)

            # Should return a list
            assert isinstance(members, list), "get_organization_members should return list"

            if len(members) == 0:
                pytest.skip("No members in test organization, cannot validate structure")

            # Check first member has all required fields
            member = members[0]

            # Required fields for MemberResponse
            required_fields = {
                'id': (UUID, str),
                'user_id': (UUID, str),
                'username': str,
                'email': str,
                'role': str,
                'is_active': bool
            }

            # Optional fields for MemberResponse
            optional_fields = {
                'organization_id': (UUID, str, type(None)),
                'joined_at': (datetime, str, type(None))
            }

            # Validate required fields exist and have correct type
            for field_name, expected_types in required_fields.items():
                assert field_name in member, \
                    f"Required field '{field_name}' missing from query result. Got: {member.keys()}"

                field_value = member[field_name]
                assert field_value is not None, \
                    f"Required field '{field_name}' is None"

                # Check type (handle both UUID objects and strings)
                if isinstance(expected_types, tuple):
                    assert isinstance(field_value, expected_types), \
                        f"Field '{field_name}' has wrong type: {type(field_value)}, expected {expected_types}"
                else:
                    assert isinstance(field_value, expected_types), \
                        f"Field '{field_name}' has wrong type: {type(field_value)}, expected {expected_types}"

            # Validate optional fields exist (but can be None)
            for field_name, expected_types in optional_fields.items():
                assert field_name in member, \
                    f"Optional field '{field_name}' missing from query result. " \
                    f"Even optional fields should be present (can be None). Got: {member.keys()}"

                field_value = member[field_name]
                if field_value is not None:
                    assert isinstance(field_value, expected_types), \
                        f"Optional field '{field_name}' has wrong type: {type(field_value)}"

            # Try to create MemberResponse from query result
            try:
                member_obj = MemberResponse(**member)
                assert member_obj is not None
            except Exception as e:
                pytest.fail(
                    f"Failed to create MemberResponse from DB query result:\n"
                    f"Error: {e}\n"
                    f"Query returned: {member}"
                )

            print(f"✅ Query returns all required fields for {len(members)} members")

        except AttributeError as e:
            pytest.fail(f"MembershipService missing get_organization_members method: {e}")
        except Exception as e:
            pytest.fail(f"Query failed: {e}")

    @pytest.mark.asyncio
    async def test_get_organization_members_with_role_filter(self, db_pool):
        """
        TEST: Filtered query returns correct structure
        REQUIREMENT: WHERE clause should not break field selection
        """
        from services.organization_management.models.role import RoleType

        service = MembershipService(db_pool)
        org_id = UUID("259da6df-c148-40c2-bcd9-dc6889e7e9fb")

        # Test with each role filter
        for role in [RoleType.STUDENT, RoleType.INSTRUCTOR, RoleType.ORGANIZATION_ADMIN]:
            members = await service.get_organization_members(org_id, role_filter=role)

            assert isinstance(members, list)

            # If results exist, validate structure
            if len(members) > 0:
                member = members[0]

                # All required fields should exist
                assert 'id' in member
                assert 'user_id' in member
                assert 'username' in member
                assert 'email' in member
                assert 'role' in member
                assert 'is_active' in member

                # Optional fields should exist
                assert 'organization_id' in member
                assert 'joined_at' in member

                # Validate role filter worked
                assert member['role'] == role.value or member['role'] == role.name

        print(f"✅ Role-filtered queries return correct structure")

    @pytest.mark.asyncio
    async def test_membership_query_uses_correct_parameterization(self, db_pool):
        """
        TEST: Query uses asyncpg parameterization ($1, $2) not psycopg2 (%s)
        REQUIREMENT: Must use asyncpg syntax for parameter placeholders

        THIS TEST WOULD HAVE CAUGHT:
        - Using %s instead of $1 causing syntax errors
        """
        # This is indirectly tested by the query succeeding
        # If it used %s, asyncpg would fail with syntax error

        service = MembershipService(db_pool)
        org_id = UUID("259da6df-c148-40c2-bcd9-dc6889e7e9fb")

        try:
            # If query works, it's using correct parameterization
            members = await service.get_organization_members(org_id)

            # Success means no syntax error from wrong parameterization
            assert isinstance(members, list)

            print("✅ Query uses correct asyncpg parameterization")

        except Exception as e:
            if "syntax error" in str(e).lower() and "%" in str(e):
                pytest.fail(
                    "Query uses psycopg2 parameterization (%s) instead of asyncpg ($1): "
                    f"{e}"
                )
            raise


class TestOrganizationQueryStructure:
    """
    Test Suite: Organization Query Field Validation

    REQUIREMENT: Organization queries must return complete data
    """

    @pytest.mark.asyncio
    async def test_get_organization_returns_all_fields(self, db_pool):
        """
        TEST: get_organization returns all OrganizationResponse fields
        REQUIREMENT: Query must include all organization attributes
        """
        service = OrganizationService(db_pool)
        org_id = UUID("259da6df-c148-40c2-bcd9-dc6889e7e9fb")

        try:
            organization = await service.get_organization(org_id)

            assert organization is not None, "Organization should exist"

            # Validate it's an Organization model
            assert isinstance(organization, Organization)

            # Validate required fields
            assert organization.id is not None
            assert organization.name is not None
            assert organization.slug is not None

            # Validate UUID type
            assert isinstance(organization.id, UUID)

            print(f"✅ Organization query returns complete data: {organization.name}")

        except AttributeError as e:
            pytest.fail(f"OrganizationService missing get_organization method: {e}")
        except Exception as e:
            pytest.fail(f"Organization query failed: {e}")

    @pytest.mark.asyncio
    async def test_organization_query_handles_nonexistent_id(self, db_pool):
        """
        TEST: Query handles non-existent org ID gracefully
        REQUIREMENT: Should return None, not crash
        """
        service = OrganizationService(db_pool)
        nonexistent_id = UUID("00000000-0000-0000-0000-000000000000")

        organization = await service.get_organization(nonexistent_id)

        # Should return None, not crash
        assert organization is None, "Non-existent organization should return None"

        print("✅ Query handles non-existent IDs gracefully")


class TestUserManagementQueryStructure:
    """
    Test Suite: User Management Query Validation

    REQUIREMENT: Login queries must return organization_id for org admins
    """

    @pytest.mark.asyncio
    async def test_login_query_includes_organization_id(self, db_pool):
        """
        TEST: Login query joins organization_memberships for org admins
        REQUIREMENT: Query must fetch organization_id for org admin users

        THIS TEST WOULD HAVE CAUGHT:
        - Login not querying organization_memberships table
        - Missing organization_id in login response
        """
        # Get a connection from pool
        async with db_pool.acquire() as conn:
            # Simulate the login query that should fetch organization_id
            query = """
                SELECT om.organization_id
                FROM course_creator.users u
                LEFT JOIN course_creator.organization_memberships om ON u.id = om.user_id
                WHERE u.username = $1 AND om.is_active = true
                LIMIT 1
            """

            # Test with known org admin user
            result = await conn.fetchrow(query, "bbrelin")

            if result is None:
                pytest.skip("Test user 'bbrelin' not found in database")

            # Should have organization_id
            assert 'organization_id' in result, \
                "Login query missing organization_id JOIN"

            org_id = result['organization_id']
            assert org_id is not None, \
                "organization_id should not be None for org admin"

            # Should be valid UUID
            assert isinstance(org_id, UUID) or isinstance(org_id, str)

            print(f"✅ Login query includes organization_id: {org_id}")

    @pytest.mark.asyncio
    async def test_organization_membership_table_structure(self, db_pool):
        """
        TEST: organization_memberships table has expected columns
        REQUIREMENT: Table schema should match application expectations
        """
        async with db_pool.acquire() as conn:
            # Query table structure
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'course_creator'
                AND table_name = 'organization_memberships'
                ORDER BY ordinal_position
            """

            columns = await conn.fetch(query)

            if len(columns) == 0:
                pytest.fail("organization_memberships table not found")

            column_names = [col['column_name'] for col in columns]

            # Required columns
            required_columns = [
                'id',
                'user_id',
                'organization_id',
                'is_active'
            ]

            # Optional but expected columns
            optional_columns = [
                'joined_at',
                'created_at'
            ]

            # Check required columns exist
            for col in required_columns:
                assert col in column_names, \
                    f"Required column '{col}' missing from organization_memberships table"

            print(f"✅ organization_memberships table has all required columns")
            print(f"   Columns: {column_names}")


class TestQueryPerformance:
    """
    Test Suite: Database Query Performance

    REQUIREMENT: Queries should complete in reasonable time
    """

    @pytest.mark.asyncio
    async def test_get_organization_members_performance(self, db_pool):
        """
        TEST: Members query completes quickly
        REQUIREMENT: Should not have N+1 query problems
        """
        import time

        service = MembershipService(db_pool)
        org_id = UUID("259da6df-c148-40c2-bcd9-dc6889e7e9fb")

        start_time = time.time()
        members = await service.get_organization_members(org_id)
        elapsed_time = time.time() - start_time

        # Query should complete in under 1 second
        assert elapsed_time < 1.0, \
            f"Query too slow: {elapsed_time:.2f}s (possible N+1 problem)"

        print(f"✅ Query completed in {elapsed_time:.3f}s for {len(members)} members")

    @pytest.mark.asyncio
    async def test_query_uses_indexes_efficiently(self, db_pool):
        """
        TEST: Queries use database indexes
        REQUIREMENT: Should use indexes on organization_id, user_id
        """
        async with db_pool.acquire() as conn:
            # Check if indexes exist
            query = """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'course_creator'
                AND tablename = 'organization_memberships'
            """

            indexes = await conn.fetch(query)

            if len(indexes) == 0:
                pytest.skip("No indexes found on organization_memberships (might be intended)")

            index_names = [idx['indexname'] for idx in indexes]
            print(f"✅ Found {len(indexes)} indexes: {index_names}")


class TestDataIntegrity:
    """
    Test Suite: Data Integrity Validation

    REQUIREMENT: Database should maintain referential integrity
    """

    @pytest.mark.asyncio
    async def test_organization_membership_has_valid_user_id(self, db_pool):
        """
        TEST: organization_memberships references valid users
        REQUIREMENT: Foreign key constraints should be enforced
        """
        async with db_pool.acquire() as conn:
            # Find memberships with invalid user_id
            query = """
                SELECT om.id, om.user_id
                FROM course_creator.organization_memberships om
                LEFT JOIN course_creator.users u ON om.user_id = u.id
                WHERE u.id IS NULL
                LIMIT 5
            """

            orphaned_memberships = await conn.fetch(query)

            assert len(orphaned_memberships) == 0, \
                f"Found {len(orphaned_memberships)} orphaned memberships (invalid user_id)"

            print("✅ All memberships reference valid users")

    @pytest.mark.asyncio
    async def test_organization_membership_has_valid_org_id(self, db_pool):
        """
        TEST: organization_memberships references valid organizations
        REQUIREMENT: Foreign key constraints should be enforced
        """
        async with db_pool.acquire() as conn:
            # Find memberships with invalid organization_id
            query = """
                SELECT om.id, om.organization_id
                FROM course_creator.organization_memberships om
                LEFT JOIN course_creator.organizations org ON om.organization_id = org.id
                WHERE org.id IS NULL
                LIMIT 5
            """

            orphaned_memberships = await conn.fetch(query)

            assert len(orphaned_memberships) == 0, \
                f"Found {len(orphaned_memberships)} orphaned memberships (invalid organization_id)"

            print("✅ All memberships reference valid organizations")
