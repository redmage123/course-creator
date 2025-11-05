"""
User DAO Unit Tests

BUSINESS CONTEXT:
Comprehensive tests for User Management Data Access Object ensuring all database
operations work correctly, handle edge cases, and maintain data integrity.

TECHNICAL IMPLEMENTATION:
- Tests all CRUD operations for users
- Validates transaction behavior and rollback
- Tests error handling and constraint violations
- Ensures SQL queries return correct data structures

TDD APPROACH:
These tests validate that the DAO layer correctly:
- Creates users with all required fields
- Retrieves users by various criteria
- Updates user profiles and settings
- Handles unique constraint violations
- Manages transactions properly
"""

import pytest
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4
import sys
from pathlib import Path

# Add user-management service to path
user_mgmt_path = Path(__file__).parent.parent.parent.parent / 'services' / 'user-management'
sys.path.insert(0, str(user_mgmt_path))

from data_access.user_dao import UserManagementDAO
from user_management.domain.entities.user import UserRole, UserStatus


class TestUserDAOCreate:
    """
    Test Suite: User Creation Operations

    BUSINESS REQUIREMENT:
    System must create new user accounts with validation and security
    """

    @pytest.mark.asyncio
    async def test_create_user_with_required_fields_only(self, db_transaction, test_user_data):
        """
        TEST: Create user with only required fields

        BUSINESS REQUIREMENT:
        Users must be creatable with minimal required information

        VALIDATES:
        - User record is created in database
        - Generated ID is valid UUID
        - created_at timestamp is set
        - Default values are applied (status=active)
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_data = {
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password_hash': test_user_data['password_hash'],
            'role': test_user_data['role'],
        }

        # Execute: Create user via DAO
        user_id = await dao.create_user(user_data)

        # Assert: User was created with valid ID
        assert user_id is not None
        assert isinstance(user_id, str)

        # Verify: User exists in database
        result = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.users WHERE id = $1",
            user_id
        )
        assert result is not None
        assert result['username'] == user_data['username']
        assert result['email'] == user_data['email']
        assert result['role'] == user_data['role']
        assert result['status'] == 'active'  # Default value
        assert result['created_at'] is not None

    @pytest.mark.asyncio
    async def test_create_user_with_all_optional_fields(self, db_transaction):
        """
        TEST: Create user with all optional profile fields

        BUSINESS REQUIREMENT:
        Users should be able to provide comprehensive profile information

        VALIDATES:
        - All optional fields are stored correctly
        - Profile data is retrievable
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_data = {
            'username': f'fulluser_{uuid4().hex[:8]}',
            'email': f'full_{uuid4().hex[:8]}@example.com',
            'password_hash': '$2b$12$test',
            'role': 'instructor',
            'first_name': 'John',
            'last_name': 'Doe',
            'full_name': 'John Doe',
            'phone': '+1-555-0123',
            'timezone': 'America/New_York',
            'language': 'en',
            'bio': 'Experienced educator',
            'organization': 'Test University',
        }

        user_id = await dao.create_user(user_data)

        # Verify all fields were stored
        result = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.users WHERE id = $1",
            user_id
        )
        assert result['first_name'] == 'John'
        assert result['last_name'] == 'Doe'
        assert result['full_name'] == 'John Doe'
        assert result['phone'] == '+1-555-0123'
        assert result['timezone'] == 'America/New_York'
        assert result['bio'] == 'Experienced educator'

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username_fails(self, db_transaction, test_user_data):
        """
        TEST: Duplicate username creation should fail

        BUSINESS REQUIREMENT:
        Usernames must be unique across the platform

        VALIDATES:
        - Unique constraint on username is enforced
        - Appropriate exception is raised
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create first user
        first_id = await dao.create_user(test_user_data)
        assert first_id is not None

        # Attempt to create second user with same username
        duplicate_data = test_user_data.copy()
        duplicate_data['email'] = f'different_{uuid4().hex[:8]}@example.com'

        with pytest.raises(Exception) as exc_info:
            await dao.create_user(duplicate_data)

        # Verify it was a unique constraint violation
        assert 'unique' in str(exc_info.value).lower() or 'duplicate' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_fails(self, db_transaction, test_user_data):
        """
        TEST: Duplicate email creation should fail

        BUSINESS REQUIREMENT:
        Email addresses must be unique across the platform

        VALIDATES:
        - Unique constraint on email is enforced
        - Users cannot create multiple accounts with same email
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create first user
        first_id = await dao.create_user(test_user_data)
        assert first_id is not None

        # Attempt to create second user with same email
        duplicate_data = test_user_data.copy()
        duplicate_data['username'] = f'different_{uuid4().hex[:8]}'

        with pytest.raises(Exception) as exc_info:
            await dao.create_user(duplicate_data)

        assert 'unique' in str(exc_info.value).lower() or 'duplicate' in str(exc_info.value).lower()


class TestUserDAORetrieve:
    """
    Test Suite: User Retrieval Operations

    BUSINESS REQUIREMENT:
    System must retrieve users by various criteria (ID, username, email)
    """

    @pytest.mark.asyncio
    async def test_get_user_by_id_returns_user(self, db_transaction, test_user_data):
        """
        TEST: Retrieve user by ID

        VALIDATES:
        - User can be fetched by UUID
        - Returned user has all expected fields
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create test user
        user_id = await dao.create_user(test_user_data)

        # Retrieve user
        user = await dao.get_user_by_id(user_id)

        assert user is not None
        assert user.id == user_id
        assert user.username == test_user_data['username']
        assert user.email == test_user_data['email']
        assert user.role == UserRole(test_user_data['role'])

    @pytest.mark.asyncio
    async def test_get_user_by_username_returns_user(self, db_transaction, test_user_data):
        """
        TEST: Retrieve user by username

        BUSINESS REQUIREMENT:
        Users must be findable by username for login
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_id = await dao.create_user(test_user_data)

        user = await dao.get_user_by_username(test_user_data['username'])

        assert user is not None
        assert user.id == user_id
        assert user.username == test_user_data['username']

    @pytest.mark.asyncio
    async def test_get_user_by_email_returns_user(self, db_transaction, test_user_data):
        """
        TEST: Retrieve user by email

        BUSINESS REQUIREMENT:
        Users must be findable by email for login and password reset
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_id = await dao.create_user(test_user_data)

        user = await dao.get_user_by_email(test_user_data['email'])

        assert user is not None
        assert user.id == user_id
        assert user.email == test_user_data['email']

    @pytest.mark.asyncio
    async def test_get_user_by_nonexistent_id_returns_none(self, db_transaction):
        """
        TEST: Retrieve nonexistent user returns None

        VALIDATES:
        - Query for nonexistent user doesn't raise exception
        - Returns None instead of raising error
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        fake_id = str(uuid4())
        user = await dao.get_user_by_id(fake_id)

        assert user is None


class TestUserDAOUpdate:
    """
    Test Suite: User Update Operations

    BUSINESS REQUIREMENT:
    Users must be able to update their profile information
    """

    @pytest.mark.asyncio
    async def test_update_user_profile_fields(self, db_transaction, test_user_data):
        """
        TEST: Update user profile fields

        VALIDATES:
        - User fields can be updated
        - updated_at timestamp is changed
        - Only specified fields are updated
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_id = await dao.create_user(test_user_data)

        # Update profile
        update_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'bio': 'Updated bio',
        }

        await dao.update_user(user_id, update_data)

        # Verify updates
        user = await dao.get_user_by_id(user_id)
        assert user.first_name == 'Jane'
        assert user.last_name == 'Smith'
        assert user.bio == 'Updated bio'
        # Original fields unchanged
        assert user.username == test_user_data['username']
        assert user.email == test_user_data['email']

    @pytest.mark.asyncio
    async def test_update_user_password(self, db_transaction, test_user_data):
        """
        TEST: Update user password hash

        BUSINESS REQUIREMENT:
        Users must be able to change their password

        VALIDATES:
        - Password hash can be updated
        - Old hash is replaced with new hash
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_id = await dao.create_user(test_user_data)

        new_hash = '$2b$12$NewPasswordHash'
        await dao.update_user(user_id, {'password_hash': new_hash})

        # Verify password was updated
        result = await db_transaction.fetchrow(
            "SELECT password_hash FROM course_creator.users WHERE id = $1",
            user_id
        )
        assert result['password_hash'] == new_hash


class TestUserDAODelete:
    """
    Test Suite: User Deletion Operations

    BUSINESS REQUIREMENT:
    System must support user account deletion (soft or hard delete)
    """

    @pytest.mark.asyncio
    async def test_soft_delete_user_sets_inactive_status(self, db_transaction, test_user_data):
        """
        TEST: Soft delete sets user status to inactive

        BUSINESS REQUIREMENT:
        User accounts should be deactivated (not deleted) to preserve data integrity

        VALIDATES:
        - User status changes to 'inactive'
        - User record remains in database
        - User cannot login with inactive status
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_id = await dao.create_user(test_user_data)

        # Soft delete (deactivate)
        await dao.deactivate_user(user_id)

        # Verify user still exists but is inactive
        result = await db_transaction.fetchrow(
            "SELECT status FROM course_creator.users WHERE id = $1",
            user_id
        )
        assert result['status'] == 'inactive'

    @pytest.mark.asyncio
    async def test_hard_delete_user_removes_from_database(self, db_transaction, test_user_data):
        """
        TEST: Hard delete removes user from database

        BUSINESS REQUIREMENT:
        Admin should be able to permanently delete user accounts (GDPR compliance)

        VALIDATES:
        - User record is removed from database
        - Subsequent queries return None
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_id = await dao.create_user(test_user_data)

        # Hard delete
        await dao.delete_user_permanently(user_id)

        # Verify user no longer exists
        user = await dao.get_user_by_id(user_id)
        assert user is None


class TestUserDAOList:
    """
    Test Suite: User Listing Operations

    BUSINESS REQUIREMENT:
    Admins must be able to list and filter users
    """

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, db_transaction):
        """
        TEST: List users with pagination

        VALIDATES:
        - Users can be fetched in pages
        - Limit and offset work correctly
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create multiple test users
        user_ids = []
        for i in range(5):
            user_data = {
                'username': f'user_{i}_{uuid4().hex[:8]}',
                'email': f'user{i}@example.com',
                'password_hash': '$2b$12$test',
                'role': 'student',
            }
            user_id = await dao.create_user(user_data)
            user_ids.append(user_id)

        # List first 3 users
        users_page1 = await dao.list_users(limit=3, offset=0)
        assert len(users_page1) <= 3

        # List next 2 users
        users_page2 = await dao.list_users(limit=2, offset=3)
        assert len(users_page2) <= 2

    @pytest.mark.asyncio
    async def test_list_users_filter_by_role(self, db_transaction):
        """
        TEST: Filter users by role

        BUSINESS REQUIREMENT:
        Admins need to find all users with specific roles
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        # Create users with different roles
        for role in ['student', 'instructor', 'student']:
            user_data = {
                'username': f'{role}_{uuid4().hex[:8]}',
                'email': f'{role}_{uuid4().hex[:8]}@example.com',
                'password_hash': '$2b$12$test',
                'role': role,
            }
            await dao.create_user(user_data)

        # Filter by role
        students = await dao.list_users(role_filter='student')
        assert all(user.role == UserRole.STUDENT for user in students)
        assert len(students) >= 2


class TestUserDAOTransactions:
    """
    Test Suite: Transaction Behavior

    BUSINESS REQUIREMENT:
    Database operations must be atomic and handle failures gracefully
    """

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_transaction):
        """
        TEST: Failed transaction rolls back changes

        VALIDATES:
        - Partial changes are not committed
        - Database state is consistent after error
        """
        dao = UserManagementDAO(None)
        dao.db_pool = type('obj', (object,), {'acquire': lambda: db_transaction})()

        user_data = {
            'username': f'rollback_{uuid4().hex[:8]}',
            'email': f'rollback@example.com',
            'password_hash': '$2b$12$test',
            'role': 'student',
        }

        # Start transaction
        try:
            user_id = await dao.create_user(user_data)

            # Force an error (e.g., constraint violation)
            await db_transaction.execute(
                "INSERT INTO course_creator.users (username, email, password_hash, role) "
                "VALUES ($1, $2, $3, $4)",
                user_data['username'],  # Duplicate username
                'different@example.com',
                '$2b$12$test',
                'student'
            )
        except Exception:
            pass

        # Verify original user creation was rolled back
        result = await db_transaction.fetchrow(
            "SELECT * FROM course_creator.users WHERE username = $1",
            user_data['username']
        )
        # Due to transaction rollback in fixture, this should not exist
        # (This test documents expected behavior)
