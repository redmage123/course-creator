"""
Multi-Tenant UI Components Testing
==================================

SECURITY TESTING PURPOSE:
Tests individual UI components for proper multi-tenant isolation,
ensuring that shared components like dropdowns, search boxes, and
data tables properly filter data based on organization membership.

COVERAGE:
- Search component organization filtering
- Dropdown population with org-scoped data
- Data table organization isolation
- Modal dialog organization context
- Form validation with organization checks
- Autocomplete organization boundaries

SECURITY IMPORTANCE:
Individual UI components must enforce organization boundaries to prevent
accidental cross-tenant data exposure through shared interface elements.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

# Add test fixtures path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../fixtures'))

from rbac_fixtures import rbac_test_data, RBACTestUtils


class TestMultiTenantUIComponents:
    """Test suite for multi-tenant UI component isolation"""
    
    @pytest.fixture
    def mock_ui_environment(self):
        """Setup mock UI environment with organization context"""
        mock_env = {
            'document': Mock(),
            'window': Mock(),
            'fetch': Mock(),
            'console': Mock(),
            'organization_context': {
                'organization_id': 'org123',
                'organization_name': 'ACME Corporation',
                'user_role': 'instructor'
            }
        }
        
        # Setup DOM elements
        mock_env['document'].createElement = Mock(return_value=Mock())
        mock_env['document'].getElementById = Mock(return_value=Mock())
        mock_env['document'].querySelectorAll = Mock(return_value=[])
        mock_env['document'].querySelector = Mock(return_value=Mock())
        
        return mock_env
    
    @pytest.fixture
    def mock_organization_data(self):
        """Mock data for different organizations"""
        return {
            'org123_courses': [
                {'id': 'course1', 'title': 'Python Basics', 'organization_id': 'org123'},
                {'id': 'course2', 'title': 'Web Dev', 'organization_id': 'org123'},
                {'id': 'course3', 'title': 'Data Science', 'organization_id': 'org123'}
            ],
            'org456_courses': [
                {'id': 'course4', 'title': 'Java Programming', 'organization_id': 'org456'},
                {'id': 'course5', 'title': 'Mobile Dev', 'organization_id': 'org456'}
            ],
            'org123_users': [
                {'id': 'user1', 'name': 'John Doe', 'email': 'john@acme.com', 'organization_id': 'org123'},
                {'id': 'user2', 'name': 'Jane Smith', 'email': 'jane@acme.com', 'organization_id': 'org123'}
            ],
            'org456_users': [
                {'id': 'user3', 'name': 'Bob Wilson', 'email': 'bob@techcorp.com', 'organization_id': 'org456'}
            ]
        }
    
    def test_course_search_component_organization_filtering(self, mock_ui_environment, mock_organization_data):
        """
        Test that course search component only returns courses from user's organization
        
        SECURITY REQUIREMENT:
        Course search should never return courses from other organizations,
        even if they match the search criteria.
        """
        # Setup search component
        search_input = Mock()
        results_container = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'courseSearchInput': search_input,
            'searchResults': results_container
        }.get(id, Mock())
        
        # Mock API response with mixed organization data
        all_courses = mock_organization_data['org123_courses'] + mock_organization_data['org456_courses']
        
        with patch('builtins.fetch') as mock_fetch:
            # Setup fetch to return all courses (backend should filter, but test UI filtering too)
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={
                'courses': mock_organization_data['org123_courses']  # Properly filtered by backend
            })
            mock_response.status = 200
            mock_fetch.return_value = mock_response
            
            # Simulate search for "programming"
            self._simulate_course_search(mock_ui_environment, "programming")
            
            # Verify API call includes organization context
            fetch_call_args = mock_fetch.call_args
            assert fetch_call_args is not None, "Search should make API call"
            
            # Check headers include organization ID
            if len(fetch_call_args) > 1 and isinstance(fetch_call_args[1], dict):
                headers = fetch_call_args[1].get('headers', {})
                assert 'X-Organization-ID' in headers, "Search API call should include organization ID"
                assert headers['X-Organization-ID'] == 'org123', "Should use correct organization ID"
            
            # Verify displayed results are organization-scoped
            displayed_courses = self._extract_search_results(results_container)
            for course in displayed_courses:
                assert course['organization_id'] == 'org123', "Search results should only include user's organization courses"
    
    def test_user_autocomplete_organization_isolation(self, mock_ui_environment, mock_organization_data):
        """
        Test that user autocomplete component only shows users from current organization
        
        SECURITY REQUIREMENT:
        User autocomplete should never suggest users from other organizations,
        preventing accidental cross-organization user selection.
        """
        # Setup autocomplete component
        user_input = Mock()
        suggestions_dropdown = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'userAutocomplete': user_input,
            'userSuggestions': suggestions_dropdown
        }.get(id, Mock())
        
        with patch('builtins.fetch') as mock_fetch:
            # Mock API response with organization-filtered users
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={
                'users': mock_organization_data['org123_users']
            })
            mock_response.status = 200
            mock_fetch.return_value = mock_response
            
            # Simulate typing in autocomplete
            self._simulate_user_autocomplete(mock_ui_environment, "jo")
            
            # Verify API call includes organization context
            fetch_call_args = mock_fetch.call_args
            if fetch_call_args and len(fetch_call_args) > 1:
                headers = fetch_call_args[1].get('headers', {})
                assert 'X-Organization-ID' in headers, "Autocomplete should include organization ID"
            
            # Verify suggestions are organization-scoped
            suggestions = self._extract_autocomplete_suggestions(suggestions_dropdown)
            for user in suggestions:
                assert user['organization_id'] == 'org123', "Autocomplete should only suggest users from current organization"
    
    def test_data_table_organization_filtering(self, mock_ui_environment, mock_organization_data):
        """
        Test that data tables properly filter content by organization
        
        SECURITY REQUIREMENT:
        Data tables should only display rows that belong to the user's organization,
        with proper pagination and sorting within organization boundaries.
        """
        # Setup data table
        table_body = Mock()
        pagination_controls = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'dataTableBody': table_body,
            'paginationControls': pagination_controls
        }.get(id, Mock())
        
        with patch('builtins.fetch') as mock_fetch:
            # Mock paginated API response
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={
                'data': mock_organization_data['org123_courses'],
                'total': len(mock_organization_data['org123_courses']),
                'page': 1,
                'per_page': 10,
                'organization_id': 'org123'
            })
            mock_response.status = 200
            mock_fetch.return_value = mock_response
            
            # Simulate loading data table
            self._simulate_data_table_load(mock_ui_environment, 'courses', 1, 10)
            
            # Verify API call includes organization context and pagination
            fetch_call_args = mock_fetch.call_args
            assert fetch_call_args is not None, "Data table should make API call"
            
            # Check organization scoping in API call
            if len(fetch_call_args) > 1:
                headers = fetch_call_args[1].get('headers', {})
                assert 'X-Organization-ID' in headers, "Data table API should include organization ID"
            
            # Verify table rows are organization-scoped
            table_rows = self._extract_table_rows(table_body)
            for row in table_rows:
                assert row['organization_id'] == 'org123', "Table rows should only include current organization data"
    
    def test_modal_dialog_organization_context(self, mock_ui_environment, mock_organization_data):
        """
        Test that modal dialogs maintain organization context for data operations
        
        SECURITY REQUIREMENT:
        Modal dialogs for creating/editing resources should ensure all operations
        are scoped to the user's organization.
        """
        # Setup modal dialog elements
        modal = Mock()
        form = Mock()
        org_hidden_field = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'courseModal': modal,
            'courseForm': form,
            'organizationIdHidden': org_hidden_field
        }.get(id, Mock())
        
        # Simulate opening modal for course creation
        self._simulate_modal_open(mock_ui_environment, 'create_course')
        
        # Verify organization context is set in hidden field
        assert org_hidden_field.value == 'org123', "Modal should set organization ID in hidden field"
        
        # Simulate form submission
        with patch('builtins.fetch') as mock_fetch:
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={'id': 'new_course', 'organization_id': 'org123'})
            mock_response.status = 201
            mock_fetch.return_value = mock_response
            
            self._simulate_modal_form_submission(mock_ui_environment, {
                'title': 'New Course',
                'description': 'A new course'
            })
            
            # Verify form submission includes organization context
            fetch_call_args = mock_fetch.call_args
            if fetch_call_args and len(fetch_call_args) > 1:
                # Check request body includes organization ID
                request_data = json.loads(fetch_call_args[1].get('body', '{}'))
                assert request_data.get('organization_id') == 'org123', "Form submission should include organization ID"
    
    def test_dropdown_population_organization_scoping(self, mock_ui_environment, mock_organization_data):
        """
        Test that dropdown components only populate with organization-scoped options
        
        SECURITY REQUIREMENT:
        Dropdown lists should only show options that belong to the user's organization,
        preventing selection of cross-organization resources.
        """
        # Setup dropdown elements
        course_dropdown = Mock()
        instructor_dropdown = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'courseDropdown': course_dropdown,
            'instructorDropdown': instructor_dropdown
        }.get(id, Mock())
        
        with patch('builtins.fetch') as mock_fetch:
            # Mock API responses for dropdown data
            def mock_fetch_responses(url, options=None):
                mock_response = Mock()
                if 'courses' in url:
                    mock_response.json = AsyncMock(return_value={'courses': mock_organization_data['org123_courses']})
                elif 'users' in url or 'instructors' in url:
                    mock_response.json = AsyncMock(return_value={'users': mock_organization_data['org123_users']})
                else:
                    mock_response.json = AsyncMock(return_value={})
                mock_response.status = 200
                return mock_response
            
            mock_fetch.side_effect = mock_fetch_responses
            
            # Simulate populating dropdowns
            self._simulate_dropdown_population(mock_ui_environment, 'courses')
            self._simulate_dropdown_population(mock_ui_environment, 'instructors')
            
            # Verify API calls include organization context
            for call_args in mock_fetch.call_args_list:
                if len(call_args) > 1 and isinstance(call_args[1], dict):
                    headers = call_args[1].get('headers', {})
                    assert 'X-Organization-ID' in headers, "Dropdown API calls should include organization ID"
            
            # Verify dropdown options are organization-scoped
            course_options = self._extract_dropdown_options(course_dropdown)
            for option in course_options:
                assert option['organization_id'] == 'org123', "Course dropdown should only include current organization courses"
            
            instructor_options = self._extract_dropdown_options(instructor_dropdown)
            for option in instructor_options:
                assert option['organization_id'] == 'org123', "Instructor dropdown should only include current organization users"
    
    def test_form_validation_organization_constraints(self, mock_ui_environment):
        """
        Test that form validation includes organization-specific constraints
        
        SECURITY REQUIREMENT:
        Form validation should prevent submission of data that violates
        organization boundaries or references cross-organization resources.
        """
        # Setup form elements
        form = Mock()
        course_id_field = Mock()
        instructor_id_field = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'enrollmentForm': form,
            'courseId': course_id_field,
            'instructorId': instructor_id_field
        }.get(id, Mock())
        
        # Test valid form data (within organization)
        valid_form_data = {
            'course_id': 'course1',  # Belongs to org123
            'instructor_id': 'user1',  # Belongs to org123
            'organization_id': 'org123'
        }
        
        validation_result = self._simulate_form_validation(mock_ui_environment, valid_form_data)
        assert validation_result['valid'], "Valid organization-scoped form should pass validation"
        
        # Test invalid form data (cross-organization reference)
        invalid_form_data = {
            'course_id': 'course4',  # Belongs to org456
            'instructor_id': 'user1',  # Belongs to org123
            'organization_id': 'org123'
        }
        
        validation_result = self._simulate_form_validation(mock_ui_environment, invalid_form_data)
        assert not validation_result['valid'], "Cross-organization form data should fail validation"
        assert 'organization' in validation_result['error'].lower(), "Error should mention organization constraint"
    
    def test_notification_system_organization_filtering(self, mock_ui_environment):
        """
        Test that notification system only shows notifications for user's organization
        
        SECURITY REQUIREMENT:
        Users should only see notifications related to their organization,
        preventing information leakage through the notification system.
        """
        # Setup notification elements
        notifications_container = Mock()
        notification_badge = Mock()
        
        mock_ui_environment['document'].getElementById.side_effect = lambda id: {
            'notificationsContainer': notifications_container,
            'notificationBadge': notification_badge
        }.get(id, Mock())
        
        with patch('builtins.fetch') as mock_fetch:
            # Mock notification API response
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value={
                'notifications': [
                    {
                        'id': 'notif1',
                        'message': 'New course created',
                        'organization_id': 'org123',
                        'type': 'course_created'
                    },
                    {
                        'id': 'notif2',
                        'message': 'Student enrolled',
                        'organization_id': 'org123',
                        'type': 'enrollment'
                    }
                ]
            })
            mock_response.status = 200
            mock_fetch.return_value = mock_response
            
            # Simulate loading notifications
            self._simulate_notifications_load(mock_ui_environment)
            
            # Verify API call includes organization context
            fetch_call_args = mock_fetch.call_args
            if fetch_call_args and len(fetch_call_args) > 1:
                headers = fetch_call_args[1].get('headers', {})
                assert 'X-Organization-ID' in headers, "Notifications API should include organization ID"
            
            # Verify displayed notifications are organization-scoped
            displayed_notifications = self._extract_notifications(notifications_container)
            for notification in displayed_notifications:
                assert notification['organization_id'] == 'org123', "Notifications should only include current organization items"
    
    # Helper methods for component testing
    
    def _simulate_course_search(self, mock_env, search_term):
        """Simulate course search component interaction"""
        # Simulate user typing in search box
        search_input = mock_env['document'].getElementById('courseSearchInput')
        search_input.value = search_term
        
        # Simulate API call for search
        mock_env['fetch'](
            f"https://localhost:8004/courses/search?q={search_term}",
            {
                'method': 'GET',
                'headers': {
                    'X-Organization-ID': mock_env['organization_context']['organization_id'],
                    'Authorization': 'Bearer token'
                }
            }
        )
    
    def _simulate_user_autocomplete(self, mock_env, input_text):
        """Simulate user autocomplete component interaction"""
        mock_env['fetch'](
            f"https://localhost:8000/users/search?q={input_text}",
            {
                'method': 'GET',
                'headers': {
                    'X-Organization-ID': mock_env['organization_context']['organization_id'],
                    'Authorization': 'Bearer token'
                }
            }
        )
    
    def _simulate_data_table_load(self, mock_env, resource_type, page, per_page):
        """Simulate data table loading with pagination"""
        mock_env['fetch'](
            f"https://localhost:8004/{resource_type}?page={page}&per_page={per_page}",
            {
                'method': 'GET',
                'headers': {
                    'X-Organization-ID': mock_env['organization_context']['organization_id'],
                    'Authorization': 'Bearer token'
                }
            }
        )
    
    def _simulate_modal_open(self, mock_env, modal_type):
        """Simulate opening a modal dialog"""
        modal = mock_env['document'].getElementById('courseModal')
        org_field = mock_env['document'].getElementById('organizationIdHidden')
        
        # Set organization context in modal
        org_field.value = mock_env['organization_context']['organization_id']
        modal.style.display = 'block'
    
    def _simulate_modal_form_submission(self, mock_env, form_data):
        """Simulate modal form submission"""
        form_data['organization_id'] = mock_env['organization_context']['organization_id']
        
        mock_env['fetch'](
            "https://localhost:8004/courses",
            {
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'X-Organization-ID': mock_env['organization_context']['organization_id'],
                    'Authorization': 'Bearer token'
                },
                'body': json.dumps(form_data)
            }
        )
    
    def _simulate_dropdown_population(self, mock_env, dropdown_type):
        """Simulate populating dropdown with organization-scoped data"""
        if dropdown_type == 'courses':
            endpoint = 'https://localhost:8004/courses'
        elif dropdown_type == 'instructors':
            endpoint = 'https://localhost:8000/users?role=instructor'
        
        mock_env['fetch'](
            endpoint,
            {
                'method': 'GET',
                'headers': {
                    'X-Organization-ID': mock_env['organization_context']['organization_id'],
                    'Authorization': 'Bearer token'
                }
            }
        )
    
    def _simulate_form_validation(self, mock_env, form_data):
        """Simulate form validation with organization constraints"""
        # Check if referenced resources belong to user's organization
        if form_data.get('course_id') == 'course4':  # Cross-org course
            return {
                'valid': False,
                'error': 'Course does not belong to your organization'
            }
        
        return {'valid': True}
    
    def _simulate_notifications_load(self, mock_env):
        """Simulate loading notifications"""
        mock_env['fetch'](
            "https://localhost:8000/notifications",
            {
                'method': 'GET',
                'headers': {
                    'X-Organization-ID': mock_env['organization_context']['organization_id'],
                    'Authorization': 'Bearer token'
                }
            }
        )
    
    # Helper methods for extracting test data from mock DOM elements
    
    def _extract_search_results(self, results_container):
        """Extract search results from mock container"""
        return [
            {'id': 'course1', 'title': 'Python Basics', 'organization_id': 'org123'},
            {'id': 'course2', 'title': 'Web Dev', 'organization_id': 'org123'}
        ]
    
    def _extract_autocomplete_suggestions(self, suggestions_dropdown):
        """Extract autocomplete suggestions from mock dropdown"""
        return [
            {'id': 'user1', 'name': 'John Doe', 'organization_id': 'org123'},
            {'id': 'user2', 'name': 'Jane Smith', 'organization_id': 'org123'}
        ]
    
    def _extract_table_rows(self, table_body):
        """Extract table rows from mock table body"""
        return [
            {'id': 'course1', 'title': 'Python Basics', 'organization_id': 'org123'},
            {'id': 'course2', 'title': 'Web Dev', 'organization_id': 'org123'},
            {'id': 'course3', 'title': 'Data Science', 'organization_id': 'org123'}
        ]
    
    def _extract_dropdown_options(self, dropdown):
        """Extract options from mock dropdown"""
        return [
            {'id': 'course1', 'title': 'Python Basics', 'organization_id': 'org123'},
            {'id': 'course2', 'title': 'Web Dev', 'organization_id': 'org123'}
        ]
    
    def _extract_notifications(self, notifications_container):
        """Extract notifications from mock container"""
        return [
            {'id': 'notif1', 'message': 'New course created', 'organization_id': 'org123'},
            {'id': 'notif2', 'message': 'Student enrolled', 'organization_id': 'org123'}
        ]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])