"""
Unit Tests for Audit Log API Endpoints

BUSINESS CONTEXT:
Audit logs are critical for compliance, security monitoring, and accountability.
These tests ensure that audit log retrieval and export functionality works correctly
and enforces proper access control.

TECHNICAL IMPLEMENTATION:
- Tests for GET /api/v1/rbac/audit-log endpoint
- Tests for GET /api/v1/rbac/audit-log/export endpoint
- Tests for filtering, pagination, and access control
- Tests for CSV export functionality

TEST COVERAGE:
- Successful audit log retrieval
- Filtering by action and date
- Pagination functionality
- Access control (site_admin only)
- CSV export with proper formatting
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import io


@pytest.fixture
def mock_site_admin_user():
    """Mock site admin user for authentication"""
    return {
        'id': 'site-admin-123',
        'email': 'admin@platform.com',
        'username': 'site_admin',
        'role': 'site_admin',
        'role_type': 'site_admin'
    }


@pytest.fixture
def mock_regular_user():
    """Mock regular user (non-admin) for testing access control"""
    return {
        'id': 'user-456',
        'email': 'user@example.com',
        'username': 'regular_user',
        'role': 'instructor',
        'role_type': 'instructor'
    }


@pytest.fixture
def sample_audit_entries():
    """Sample audit log entries for testing"""
    return [
        {
            "event_id": "audit-001",
            "action": "organization_created",
            "timestamp": "2025-01-15T10:30:00Z",
            "user_id": "user-123",
            "user_name": "John Admin",
            "user_email": "john@example.com",
            "organization_id": "org-456",
            "target_resource_type": "organization",
            "target_resource": "Acme Corp",
            "description": "Created new organization Acme Corp",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0",
            "severity": "medium"
        },
        {
            "event_id": "audit-002",
            "action": "user_created",
            "timestamp": "2025-01-15T11:00:00Z",
            "user_id": "user-123",
            "user_name": "John Admin",
            "user_email": "john@example.com",
            "organization_id": "org-456",
            "target_resource_type": "user",
            "target_resource": "jane@example.com",
            "description": "Created new user account for jane@example.com",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0",
            "severity": "medium"
        },
        {
            "event_id": "audit-003",
            "action": "organization_deleted",
            "timestamp": "2025-01-14T15:45:00Z",
            "user_id": "user-789",
            "user_name": "Admin User",
            "user_email": "admin@platform.com",
            "organization_id": "org-old",
            "target_resource_type": "organization",
            "target_resource": "Old Organization",
            "description": "Deleted organization 'Old Organization'",
            "ip_address": "192.168.1.50",
            "user_agent": "Mozilla/5.0",
            "severity": "high"
        }
    ]


class TestAuditLogEndpoint:
    """
    Tests for GET /api/v1/rbac/audit-log endpoint

    BUSINESS REQUIREMENT:
    Site admins must be able to retrieve audit logs with filtering
    and pagination capabilities.
    """

    def test_get_audit_log_success(self, client, mock_site_admin_user):
        """
        Test successful retrieval of audit log entries

        VALIDATION:
        - Returns 200 status code
        - Returns audit entries array
        - Includes pagination metadata
        - Returns proper structure
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log')

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert 'entries' in data
            assert 'total' in data
            assert 'limit' in data
            assert 'offset' in data
            assert 'has_more' in data

            # Verify entries are present
            assert isinstance(data['entries'], list)
            assert len(data['entries']) > 0

            # Verify entry structure
            first_entry = data['entries'][0]
            assert 'event_id' in first_entry
            assert 'action' in first_entry
            assert 'timestamp' in first_entry
            assert 'user_id' in first_entry
            assert 'description' in first_entry
            assert 'severity' in first_entry

    def test_get_audit_log_filter_by_action(self, client, mock_site_admin_user):
        """
        Test filtering audit log by action type

        VALIDATION:
        - Returns only entries matching the action filter
        - Maintains proper response structure
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log?action=organization_created')

            assert response.status_code == 200
            data = response.json()

            # Verify filtering worked
            for entry in data['entries']:
                assert entry['action'] == 'organization_created'

    def test_get_audit_log_filter_by_date(self, client, mock_site_admin_user):
        """
        Test filtering audit log by date

        VALIDATION:
        - Returns only entries from the specified date
        - Date format is handled correctly
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log?date=2025-01-15')

            assert response.status_code == 200
            data = response.json()

            # Verify date filtering worked
            for entry in data['entries']:
                assert entry['timestamp'].startswith('2025-01-15')

    def test_get_audit_log_pagination(self, client, mock_site_admin_user):
        """
        Test pagination functionality

        VALIDATION:
        - Respects limit parameter
        - Respects offset parameter
        - Returns correct has_more flag
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            # Get first page
            response = client.get('/api/v1/rbac/audit-log?limit=1&offset=0')

            assert response.status_code == 200
            data = response.json()

            assert data['limit'] == 1
            assert data['offset'] == 0
            assert len(data['entries']) <= 1

    def test_get_audit_log_access_denied_non_admin(self, client, mock_regular_user):
        """
        Test that non-admin users cannot access audit logs

        SECURITY REQUIREMENT:
        Only site administrators should be able to view audit logs

        VALIDATION:
        - Returns 403 Forbidden for non-admin users
        - Returns appropriate error message
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_regular_user):
            response = client.get('/api/v1/rbac/audit-log')

            assert response.status_code == 403
            assert 'site administrator' in response.json()['detail'].lower()

    def test_get_audit_log_combined_filters(self, client, mock_site_admin_user):
        """
        Test combining multiple filters (action + date)

        VALIDATION:
        - Both filters are applied
        - Results match both criteria
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log?action=user_created&date=2025-01-15')

            assert response.status_code == 200
            data = response.json()

            # Verify both filters applied
            for entry in data['entries']:
                assert entry['action'] == 'user_created'
                assert entry['timestamp'].startswith('2025-01-15')

    def test_get_audit_log_empty_result(self, client, mock_site_admin_user):
        """
        Test audit log with no matching entries

        VALIDATION:
        - Returns 200 with empty entries array
        - Pagination metadata is correct
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log?action=nonexistent_action')

            assert response.status_code == 200
            data = response.json()

            assert data['entries'] == []
            assert data['total'] == 0

    def test_get_audit_log_default_pagination(self, client, mock_site_admin_user):
        """
        Test default pagination values

        VALIDATION:
        - Default limit is 100
        - Default offset is 0
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log')

            assert response.status_code == 200
            data = response.json()

            assert data['limit'] == 100
            assert data['offset'] == 0


class TestAuditLogExportEndpoint:
    """
    Tests for GET /api/v1/rbac/audit-log/export endpoint

    BUSINESS REQUIREMENT:
    Site admins must be able to export audit logs for compliance
    and archival purposes.
    """

    def test_export_audit_log_success(self, client, mock_site_admin_user):
        """
        Test successful CSV export of audit log

        VALIDATION:
        - Returns 200 status code
        - Returns CSV content type
        - Contains CSV headers
        - Contains audit data
        - Has proper Content-Disposition header
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log/export')

            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/csv; charset=utf-8'
            assert 'Content-Disposition' in response.headers
            assert 'attachment' in response.headers['Content-Disposition']
            assert 'audit-log-' in response.headers['Content-Disposition']

            # Verify CSV content
            csv_content = response.text
            assert 'event_id' in csv_content
            assert 'action' in csv_content
            assert 'timestamp' in csv_content
            assert 'user_id' in csv_content

    def test_export_audit_log_with_filters(self, client, mock_site_admin_user):
        """
        Test CSV export with filters applied

        VALIDATION:
        - Filters are respected in export
        - Only matching entries are exported
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log/export?action=organization_created')

            assert response.status_code == 200
            csv_content = response.text

            # Verify filtering in CSV
            lines = csv_content.strip().split('\n')
            assert len(lines) >= 1  # At least header

            # Check that data lines contain the filter action
            if len(lines) > 1:
                assert 'organization_created' in csv_content

    def test_export_audit_log_filename_format(self, client, mock_site_admin_user):
        """
        Test that exported filename includes current date

        VALIDATION:
        - Filename follows format: audit-log-YYYY-MM-DD.csv
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log/export')

            assert response.status_code == 200

            content_disposition = response.headers['Content-Disposition']
            assert 'audit-log-' in content_disposition
            assert '.csv' in content_disposition

            # Verify date format (YYYY-MM-DD)
            import re
            date_pattern = r'audit-log-\d{4}-\d{2}-\d{2}\.csv'
            assert re.search(date_pattern, content_disposition)

    def test_export_audit_log_access_denied_non_admin(self, client, mock_regular_user):
        """
        Test that non-admin users cannot export audit logs

        SECURITY REQUIREMENT:
        Only site administrators should be able to export audit logs

        VALIDATION:
        - Returns 403 Forbidden for non-admin users
        - Returns appropriate error message
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_regular_user):
            response = client.get('/api/v1/rbac/audit-log/export')

            assert response.status_code == 403
            assert 'site administrator' in response.json()['detail'].lower()

    def test_export_audit_log_csv_structure(self, client, mock_site_admin_user):
        """
        Test that CSV has proper structure

        VALIDATION:
        - Header row contains all expected fields
        - Data rows are properly formatted
        - No malformed CSV
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log/export')

            assert response.status_code == 200

            import csv
            csv_content = response.text
            csv_reader = csv.DictReader(io.StringIO(csv_content))

            # Verify headers
            headers = csv_reader.fieldnames
            expected_headers = [
                'event_id', 'action', 'timestamp', 'user_id', 'user_name',
                'user_email', 'organization_id', 'target_resource_type',
                'target_resource', 'description', 'ip_address', 'user_agent', 'severity'
            ]

            for header in expected_headers:
                assert header in headers

    def test_export_audit_log_empty_result(self, client, mock_site_admin_user):
        """
        Test export with no matching entries

        VALIDATION:
        - Returns valid CSV with headers only
        - No data rows
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            response = client.get('/api/v1/rbac/audit-log/export?action=nonexistent_action')

            assert response.status_code == 200

            csv_content = response.text
            lines = csv_content.strip().split('\n')

            # Should have at least header row
            assert len(lines) >= 1


class TestAuditLogAccessControl:
    """
    Tests for audit log access control and security

    SECURITY REQUIREMENT:
    Audit logs contain sensitive information and must be
    properly protected with role-based access control.
    """

    def test_audit_log_requires_authentication(self, client):
        """
        Test that audit log endpoint requires authentication

        VALIDATION:
        - Returns 401/403 when no authentication provided
        """
        # This test depends on how authentication is set up
        # Adjust based on actual auth implementation
        pass  # Placeholder - implement based on auth setup

    def test_audit_log_export_requires_authentication(self, client):
        """
        Test that export endpoint requires authentication

        VALIDATION:
        - Returns 401/403 when no authentication provided
        """
        # This test depends on how authentication is set up
        # Adjust based on actual auth implementation
        pass  # Placeholder - implement based on auth setup

    @pytest.mark.parametrize('role', ['instructor', 'student', 'organization_admin'])
    def test_audit_log_denied_for_non_site_admin_roles(self, client, role):
        """
        Test that all non-site_admin roles are denied access

        VALIDATION:
        - Instructors cannot access audit logs
        - Students cannot access audit logs
        - Organization admins cannot access audit logs
        """
        mock_user = {
            'id': 'user-123',
            'email': 'user@example.com',
            'role': role,
            'role_type': role
        }

        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_user):
            response = client.get('/api/v1/rbac/audit-log')
            assert response.status_code == 403

            response = client.get('/api/v1/rbac/audit-log/export')
            assert response.status_code == 403


class TestAuditLogErrorHandling:
    """
    Tests for error handling in audit log endpoints

    BUSINESS REQUIREMENT:
    Audit log functionality must handle errors gracefully
    and provide meaningful error messages.
    """

    def test_audit_log_handles_server_error(self, client, mock_site_admin_user):
        """
        Test that server errors are handled properly

        VALIDATION:
        - Returns 500 status code
        - Returns error message
        """
        with patch('services.organization_management.api.rbac_endpoints.get_current_user', return_value=mock_site_admin_user):
            # Mock an internal error
            with patch('services.organization_management.api.rbac_endpoints.get_audit_log', side_effect=Exception('Database error')):
                # This test structure depends on how the endpoint is implemented
                # Adjust based on actual implementation
                pass  # Placeholder

    def test_export_handles_csv_generation_error(self, client, mock_site_admin_user):
        """
        Test that CSV generation errors are handled

        VALIDATION:
        - Returns appropriate error status
        - Returns error message
        """
        # Placeholder - implement based on actual error handling
        pass


@pytest.fixture
def client():
    """
    Create FastAPI test client

    TECHNICAL IMPLEMENTATION:
    This fixture provides a test client for making HTTP requests
    to the API endpoints without running a real server.
    """
    from fastapi.testclient import TestClient
    from services.organization_management.main import app

    return TestClient(app)
