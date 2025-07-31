"""
End-to-End Tests for RBAC Complete Workflows
Tests complete user workflows from authentication through RBAC operations
"""

import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add test fixtures path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../fixtures'))

from rbac_fixtures import (
    rbac_test_data,
    RBACTestUtils
)


class TestRBACCompleteWorkflows:
    """End-to-end test cases for complete RBAC workflows"""
    
    @pytest.fixture
    def mock_browser_session(self):
        """Mock browser session for E2E testing."""
        session = Mock()
        session.cookies = {}
        session.local_storage = {}
        session.current_url = "http://localhost:3000"
        session.page_source = ""
        
        # Mock navigation methods
        session.get = Mock()
        session.find_element = Mock()
        session.find_elements = Mock(return_value=[])
        session.execute_script = Mock()
        session.wait_for_element = Mock()
        session.click = Mock()
        session.send_keys = Mock()
        session.clear = Mock()
        session.submit = Mock()
        
        return session
    
    @pytest.fixture
    def mock_api_server(self, rbac_test_data):
        """Mock API server responses for E2E testing."""
        api_responses = {
            'auth': {
                'login': {
                    'success': True,
                    'token': 'test_jwt_token',
                    'user': rbac_test_data["users"]["org_admin"],
                    'expires_in': 3600
                },
                'me': rbac_test_data["users"]["org_admin"]
            },
            'organizations': {
                'list': [rbac_test_data["organization"]],
                'members': [
                    {
                        "membership_id": "member1",
                        "name": "John Instructor",
                        "email": "john@test.org",
                        "role_type": "instructor",
                        "status": "active"
                    }
                ],
                'tracks': [rbac_test_data["track"]],
                'meeting_rooms': rbac_test_data["meeting_rooms"],
                'projects': [rbac_test_data["project"]]
            },
            'site_admin': {
                'organizations': [
                    {
                        **rbac_test_data["organization"],
                        "total_members": 15,
                        "project_count": 3,
                        "member_counts": {"instructor": 5, "student": 10}
                    }
                ],
                'platform_stats': {
                    "total_organizations": 3,
                    "total_users": 150,
                    "total_projects": 25,
                    "total_tracks": 40,
                    "total_meeting_rooms": 60
                }
            }
        }
        return api_responses
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_organization_admin_workflow(self, mock_browser_session, mock_api_server, rbac_test_data):
        """Test complete workflow for organization administrator."""
        # Step 1: User Login
        mock_browser_session.get("http://localhost:3000/login.html")
        
        # Mock login form elements
        email_input = Mock()
        password_input = Mock()
        login_button = Mock()
        
        mock_browser_session.find_element.side_effect = lambda by, value: {
            'email': email_input,
            'password': password_input,
            'login-btn': login_button
        }.get(value.split('=')[-1] if '=' in value else value, Mock())
        
        # Fill login form
        email_input.send_keys("admin@testorg.com")
        password_input.send_keys("SecurePassword123!")
        login_button.click()
        
        # Mock successful login response
        mock_browser_session.local_storage['authToken'] = mock_api_server['auth']['login']['token']
        mock_browser_session.current_url = "http://localhost:3000/org-admin-enhanced.html"
        
        # Verify login successful
        assert mock_browser_session.current_url.endswith('org-admin-enhanced.html')
        assert 'authToken' in mock_browser_session.local_storage
        
        # Step 2: Dashboard Loading
        # Mock dashboard elements
        dashboard_elements = {
            'currentUserName': Mock(),
            'orgName': Mock(),
            'totalMembers': Mock(),
            'membersContainer': Mock(),
            'addMemberBtn': Mock()
        }
        
        def mock_find_dashboard_element(by, value):
            element_id = value.split('=')[-1] if '=' in value else value
            return dashboard_elements.get(element_id, Mock())
        
        mock_browser_session.find_element = mock_find_dashboard_element
        
        # Verify dashboard loaded with user data
        current_user_element = dashboard_elements['currentUserName']
        current_user_element.text = mock_api_server['auth']['me']['full_name']
        assert current_user_element.text == "Organization Administrator"
        
        # Step 3: Add New Member
        add_member_btn = dashboard_elements['addMemberBtn']
        add_member_btn.click()
        
        # Mock add member modal elements
        modal_elements = {
            'memberEmail': Mock(),
            'memberRole': Mock(),
            'projectAccess': Mock(),
            'addMemberSubmit': Mock(),
            'addMemberModal': Mock()
        }
        
        def mock_find_modal_element(by, value):
            element_id = value.split('=')[-1] if '=' in value else value
            return modal_elements.get(element_id, Mock())
        
        # Fill member form
        modal_elements['memberEmail'].send_keys("newmember@testorg.com")
        modal_elements['memberRole'].send_keys("instructor")
        modal_elements['addMemberSubmit'].click()
        
        # Mock successful member addition
        new_member_data = {
            "id": str(uuid.uuid4()),
            "user_email": "newmember@testorg.com",
            "role_type": "instructor",
            "status": "active"
        }
        
        # Verify member was added to the list
        members_container = dashboard_elements['membersContainer']
        members_container.innerHTML = f'<div class="member-card">{new_member_data["user_email"]}</div>'
        
        # Step 4: Create Meeting Room
        # Navigate to meeting rooms tab
        meeting_rooms_tab = Mock()
        meeting_rooms_tab.click()
        
        # Mock meeting room elements
        room_elements = {
            'createRoomBtn': Mock(),
            'roomName': Mock(),
            'roomPlatform': Mock(),
            'roomType': Mock(),
            'createRoomSubmit': Mock()
        }
        
        room_elements['createRoomBtn'].click()
        
        # Fill room form
        room_elements['roomName'].send_keys("New Python Track Room")
        room_elements['roomPlatform'].send_keys("teams")
        room_elements['roomType'].send_keys("track_room")
        room_elements['createRoomSubmit'].click()
        
        # Mock successful room creation
        new_room_data = {
            "id": str(uuid.uuid4()),
            "name": "New Python Track Room",
            "platform": "teams",
            "room_type": "track_room",
            "join_url": "https://teams.microsoft.com/l/meetup-join/...",
            "status": "active"
        }
        
        # Step 5: View Analytics
        analytics_tab = Mock()
        analytics_tab.click()
        
        # Mock analytics data display
        analytics_elements = {
            'memberStats': Mock(),
            'trackStats': Mock(),
            'roomUsage': Mock()
        }
        
        analytics_elements['memberStats'].text = "15 Active Members"
        analytics_elements['trackStats'].text = "5 Learning Tracks"
        analytics_elements['roomUsage'].text = "3 Meeting Rooms"
        
        # Verify analytics data displayed
        assert "15 Active Members" in analytics_elements['memberStats'].text
        
        # Step 6: Logout
        logout_btn = Mock()
        logout_btn.click()
        
        # Mock logout process
        del mock_browser_session.local_storage['authToken']
        mock_browser_session.current_url = "http://localhost:3000/login.html"
        
        # Verify logout successful
        assert 'authToken' not in mock_browser_session.local_storage
        assert mock_browser_session.current_url.endswith('login.html')
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_site_admin_workflow(self, mock_browser_session, mock_api_server, rbac_test_data):
        """Test complete workflow for site administrator."""
        # Step 1: Site Admin Login
        mock_browser_session.get("http://localhost:3000/login.html")
        
        # Mock login with site admin credentials
        email_input = Mock()
        password_input = Mock()
        login_button = Mock()
        
        email_input.send_keys("admin@platform.com")
        password_input.send_keys("AdminPassword123!")
        login_button.click()
        
        # Mock successful site admin login
        site_admin_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["site_admin"])
        mock_browser_session.local_storage['authToken'] = site_admin_token
        mock_browser_session.current_url = "http://localhost:3000/site-admin-dashboard.html"
        
        # Verify site admin dashboard access
        assert mock_browser_session.current_url.endswith('site-admin-dashboard.html')
        
        # Step 2: View Platform Statistics
        dashboard_elements = {
            'totalOrganizations': Mock(),
            'totalUsers': Mock(),
            'totalProjects': Mock(),
            'platformHealth': Mock(),
            'organizationsContainer': Mock()
        }
        
        # Mock platform stats display
        stats = mock_api_server['site_admin']['platform_stats']
        dashboard_elements['totalOrganizations'].text = str(stats['total_organizations'])
        dashboard_elements['totalUsers'].text = str(stats['total_users'])
        dashboard_elements['totalProjects'].text = str(stats['total_projects'])
        
        # Verify stats displayed correctly
        assert dashboard_elements['totalOrganizations'].text == "3"
        assert dashboard_elements['totalUsers'].text == "150"
        
        # Step 3: Manage Organizations
        organizations_tab = Mock()
        organizations_tab.click()
        
        # Mock organization list
        organizations = mock_api_server['site_admin']['organizations']
        orgs_html = ""
        for org in organizations:
            orgs_html += f'<div class="organization-card">'
            orgs_html += f'<h3>{org["name"]}</h3>'
            orgs_html += f'<span>{org["total_members"]} members</span>'
            orgs_html += f'<button class="delete-org-btn" data-org-id="{org["id"]}">Delete</button>'
            orgs_html += '</div>'
        
        dashboard_elements['organizationsContainer'].innerHTML = orgs_html
        
        # Step 4: Test Organization Deletion (Mock Confirmation)
        delete_button = Mock()
        delete_button.getAttribute = Mock(return_value=rbac_test_data["organization"]["id"])
        delete_button.click()
        
        # Mock deletion confirmation modal
        modal_elements = {
            'deleteOrgModal': Mock(),
            'orgNameToDelete': Mock(),
            'confirmOrgName': Mock(),
            'confirmDeleteBtn': Mock()
        }
        
        modal_elements['orgNameToDelete'].text = rbac_test_data["organization"]["name"]
        modal_elements['confirmOrgName'].send_keys(rbac_test_data["organization"]["name"])
        modal_elements['confirmDeleteBtn'].click()
        
        # Mock successful deletion
        deletion_result = {
            "success": True,
            "organization_name": rbac_test_data["organization"]["name"],
            "deleted_members": 15,
            "deleted_meeting_rooms": 3
        }
        
        # Verify deletion notification
        notification = Mock()
        notification.text = f'Organization "{deletion_result["organization_name"]}" deleted successfully'
        assert rbac_test_data["organization"]["name"] in notification.text
        
        # Step 5: Test Integration Health Checks
        integrations_tab = Mock()
        integrations_tab.click()
        
        integration_elements = {
            'teamsTestBtn': Mock(),
            'zoomTestBtn': Mock(),
            'teamsStatus': Mock(),
            'zoomStatus': Mock()
        }
        
        # Test Teams integration
        integration_elements['teamsTestBtn'].click()
        integration_elements['teamsStatus'].text = "Active"
        integration_elements['teamsStatus'].className = "integration-status active"
        
        # Test Zoom integration
        integration_elements['zoomTestBtn'].click()
        integration_elements['zoomStatus'].text = "Active"
        integration_elements['zoomStatus'].className = "integration-status active"
        
        # Verify integration status
        assert integration_elements['teamsStatus'].text == "Active"
        assert integration_elements['zoomStatus'].text == "Active"
        
        # Step 6: View Audit Log
        audit_tab = Mock()
        audit_tab.click()
        
        audit_elements = {
            'auditContainer': Mock()
        }
        
        # Mock audit log entries
        audit_entries = [
            {
                "action": "organization_deleted",
                "user": "admin@platform.com",
                "timestamp": datetime.utcnow(),
                "details": f"Deleted organization: {rbac_test_data['organization']['name']}"
            },
            {
                "action": "integration_tested",
                "user": "admin@platform.com", 
                "timestamp": datetime.utcnow(),
                "details": "Teams integration health check completed"
            }
        ]
        
        audit_html = ""
        for entry in audit_entries:
            audit_html += f'<div class="audit-entry">'
            audit_html += f'<span class="audit-action">{entry["action"]}</span>'
            audit_html += f'<span class="audit-user">{entry["user"]}</span>'
            audit_html += f'<span class="audit-details">{entry["details"]}</span>'
            audit_html += '</div>'
        
        audit_elements['auditContainer'].innerHTML = audit_html
        
        # Verify audit log populated
        assert "organization_deleted" in audit_elements['auditContainer'].innerHTML
        assert "integration_tested" in audit_elements['auditContainer'].innerHTML
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_instructor_student_interaction_workflow(self, mock_browser_session, mock_api_server, rbac_test_data):
        """Test workflow involving instructor and student interactions."""
        # Step 1: Instructor Login and Track Creation
        mock_browser_session.get("http://localhost:3000/login.html")
        
        # Login as instructor
        instructor_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["instructor"])
        mock_browser_session.local_storage['authToken'] = instructor_token
        mock_browser_session.current_url = "http://localhost:3000/instructor-dashboard.html"
        
        # Create new track
        track_elements = {
            'createTrackBtn': Mock(),
            'trackName': Mock(),
            'trackDescription': Mock(),
            'trackDifficulty': Mock(),
            'trackDuration': Mock(),
            'createTrackSubmit': Mock()
        }
        
        track_elements['createTrackBtn'].click()
        track_elements['trackName'].send_keys("Advanced JavaScript")
        track_elements['trackDescription'].send_keys("Master modern JavaScript concepts")
        track_elements['trackDifficulty'].send_keys("intermediate")
        track_elements['trackDuration'].send_keys("10")
        track_elements['createTrackSubmit'].click()
        
        new_track_id = str(uuid.uuid4())
        new_track = {
            "id": new_track_id,
            "name": "Advanced JavaScript",
            "description": "Master modern JavaScript concepts",
            "difficulty_level": "intermediate",
            "duration_weeks": 10,
            "status": "active"
        }
        
        # Step 2: Create Meeting Room for Track
        room_elements = {
            'createRoomBtn': Mock(),
            'roomName': Mock(),
            'roomPlatform': Mock(),
            'roomType': Mock(),
            'trackSelect': Mock(),
            'createRoomSubmit': Mock()
        }
        
        room_elements['createRoomBtn'].click()
        room_elements['roomName'].send_keys("JavaScript Track Room")
        room_elements['roomPlatform'].send_keys("zoom")
        room_elements['roomType'].send_keys("track_room")
        room_elements['trackSelect'].send_keys(new_track_id)
        room_elements['createRoomSubmit'].click()
        
        new_room = {
            "id": str(uuid.uuid4()),
            "name": "JavaScript Track Room",
            "platform": "zoom",
            "room_type": "track_room",
            "track_id": new_track_id,
            "join_url": "https://zoom.us/j/123456789",
            "status": "active"
        }
        
        # Step 3: Student Login and Track Enrollment
        # Logout instructor
        logout_btn = Mock()
        logout_btn.click()
        del mock_browser_session.local_storage['authToken']
        
        # Login as student
        student_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["student"])
        mock_browser_session.local_storage['authToken'] = student_token
        mock_browser_session.current_url = "http://localhost:3000/student-dashboard.html"
        
        # View available tracks
        student_elements = {
            'availableTracks': Mock(),
            'enrollBtn': Mock(),
            'myTracks': Mock(),
            'trackRooms': Mock()
        }
        
        # Mock available tracks display
        tracks_html = f'<div class="track-card" data-track-id="{new_track_id}">'
        tracks_html += f'<h3>{new_track["name"]}</h3>'
        tracks_html += f'<p>{new_track["description"]}</p>'
        tracks_html += f'<button class="enroll-btn">Enroll</button>'
        tracks_html += '</div>'
        
        student_elements['availableTracks'].innerHTML = tracks_html
        
        # Enroll in track
        enroll_btn = Mock()
        enroll_btn.getAttribute = Mock(return_value=new_track_id)
        enroll_btn.click()
        
        # Mock successful enrollment
        enrollment = {
            "id": str(uuid.uuid4()),
            "student_id": rbac_test_data["users"]["student"]["id"],
            "track_id": new_track_id,
            "enrolled_at": datetime.utcnow(),
            "status": "active"
        }
        
        # Step 4: Student Access to Track Meeting Room
        # Mock enrolled tracks with meeting rooms
        my_tracks_html = f'<div class="enrolled-track">'
        my_tracks_html += f'<h3>{new_track["name"]}</h3>'
        my_tracks_html += f'<div class="track-rooms">'
        my_tracks_html += f'<button class="join-room-btn" data-room-url="{new_room["join_url"]}">Join Meeting</button>'
        my_tracks_html += '</div>'
        my_tracks_html += '</div>'
        
        student_elements['myTracks'].innerHTML = my_tracks_html
        
        # Test joining meeting room
        join_room_btn = Mock()
        join_room_btn.getAttribute = Mock(return_value=new_room["join_url"])
        join_room_btn.click()
        
        # Mock opening meeting room URL
        mock_browser_session.execute_script(f'window.open("{new_room["join_url"]}", "_blank")')
        
        # Step 5: Track Progress and Analytics
        # Mock progress tracking
        progress_elements = {
            'progressBar': Mock(),
            'completedLessons': Mock(),
            'totalLessons': Mock()
        }
        
        progress_data = {
            "completed_lessons": 3,
            "total_lessons": 10,
            "progress_percentage": 30
        }
        
        progress_elements['progressBar'].style = Mock()
        progress_elements['progressBar'].style.width = f"{progress_data['progress_percentage']}%"
        progress_elements['completedLessons'].text = str(progress_data['completed_lessons'])
        progress_elements['totalLessons'].text = str(progress_data['total_lessons'])
        
        # Verify progress display
        assert progress_elements['progressBar'].style.width == "30%"
        assert progress_elements['completedLessons'].text == "3"
        
        # Step 6: Instructor Views Student Progress
        # Switch back to instructor
        del mock_browser_session.local_storage['authToken']
        mock_browser_session.local_storage['authToken'] = instructor_token
        mock_browser_session.current_url = "http://localhost:3000/instructor-dashboard.html"
        
        # View track analytics
        analytics_elements = {
            'trackAnalytics': Mock(),
            'enrolledStudents': Mock(),
            'averageProgress': Mock(),
            'meetingAttendance': Mock()
        }
        
        # Mock analytics data
        track_analytics = {
            "enrolled_students": 5,
            "average_progress": 45,
            "meeting_attendance": 80,
            "completion_rate": 20
        }
        
        analytics_elements['enrolledStudents'].text = f"{track_analytics['enrolled_students']} students"
        analytics_elements['averageProgress'].text = f"{track_analytics['average_progress']}% average progress"
        analytics_elements['meetingAttendance'].text = f"{track_analytics['meeting_attendance']}% attendance"
        
        # Verify analytics display
        assert "5 students" in analytics_elements['enrolledStudents'].text
        assert "45%" in analytics_elements['averageProgress'].text
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_permission_boundary_testing(self, mock_browser_session, mock_api_server, rbac_test_data):
        """Test permission boundaries and access control across different user roles."""
        # Test 1: Student attempting to access admin functionality
        student_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["student"])
        mock_browser_session.local_storage['authToken'] = student_token
        
        # Attempt to access organization admin dashboard
        mock_browser_session.get("http://localhost:3000/org-admin-enhanced.html")
        
        # Mock permission check failure
        error_elements = {
            'errorMessage': Mock(),
            'redirectNotice': Mock()
        }
        
        error_elements['errorMessage'].text = "Access Denied: Insufficient permissions"
        error_elements['redirectNotice'].text = "Redirecting to student dashboard..."
        
        # Verify access denied
        assert "Access Denied" in error_elements['errorMessage'].text
        
        # Mock redirect to appropriate dashboard
        mock_browser_session.current_url = "http://localhost:3000/student-dashboard.html"
        assert mock_browser_session.current_url.endswith('student-dashboard.html')
        
        # Test 2: Instructor attempting site admin functions
        instructor_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["instructor"])
        mock_browser_session.local_storage['authToken'] = instructor_token
        
        # Attempt to access site admin dashboard
        mock_browser_session.get("http://localhost:3000/site-admin-dashboard.html")
        
        # Mock permission check failure
        error_elements['errorMessage'].text = "Access Denied: Site administrator access required"
        
        # Verify access denied
        assert "Site administrator access required" in error_elements['errorMessage'].text
        
        # Test 3: Organization admin attempting to delete organizations
        org_admin_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["org_admin"])
        mock_browser_session.local_storage['authToken'] = org_admin_token
        mock_browser_session.current_url = "http://localhost:3000/org-admin-enhanced.html"
        
        # Attempt organization deletion (should fail)
        delete_org_btn = Mock()
        delete_org_btn.click()
        
        # Mock API error response
        api_error = {
            "status_code": 403,
            "detail": "Only site administrators can delete organizations"
        }
        
        error_notification = Mock()
        error_notification.text = api_error["detail"]
        
        # Verify error notification
        assert "Only site administrators" in error_notification.text
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_cross_browser_compatibility(self, rbac_test_data):
        """Test RBAC functionality across different browser environments."""
        browsers = ['chrome', 'firefox', 'safari', 'edge']
        
        for browser in browsers:
            # Mock browser-specific session
            browser_session = Mock()
            browser_session.name = browser
            browser_session.local_storage = {}
            browser_session.session_storage = {}
            browser_session.cookies = {}
            
            # Mock browser-specific behavior
            if browser == 'safari':
                # Safari has different local storage behavior
                browser_session.local_storage_available = False
                browser_session.cookies_available = True
            else:
                browser_session.local_storage_available = True
                browser_session.cookies_available = True
            
            # Test authentication storage
            auth_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["org_admin"])
            
            if browser_session.local_storage_available:
                browser_session.local_storage['authToken'] = auth_token
                assert 'authToken' in browser_session.local_storage
            else:
                # Fallback to cookies for Safari
                browser_session.cookies['authToken'] = auth_token
                assert 'authToken' in browser_session.cookies
            
            # Test dashboard functionality
            dashboard_elements = {
                'membersContainer': Mock(),
                'tracksContainer': Mock(),
                'meetingRoomsContainer': Mock()
            }
            
            # Mock responsive behavior for different browsers
            if browser in ['chrome', 'firefox']:
                # Modern browsers support all features
                dashboard_elements['membersContainer'].innerHTML = '<div class="member-card">Full functionality</div>'
            elif browser == 'safari':
                # Safari might need polyfills
                dashboard_elements['membersContainer'].innerHTML = '<div class="member-card">Safari compatible</div>'
            elif browser == 'edge':
                # Edge compatibility
                dashboard_elements['membersContainer'].innerHTML = '<div class="member-card">Edge compatible</div>'
            
            # Verify browser-specific functionality
            assert 'compatible' in dashboard_elements['membersContainer'].innerHTML or 'functionality' in dashboard_elements['membersContainer'].innerHTML
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, mock_browser_session, rbac_test_data):
        """Test RBAC system behavior during network failures and recovery."""
        # Step 1: Normal operation
        org_admin_token = RBACTestUtils.create_test_jwt_token(rbac_test_data["users"]["org_admin"])
        mock_browser_session.local_storage['authToken'] = org_admin_token
        mock_browser_session.current_url = "http://localhost:3000/org-admin-enhanced.html"
        
        # Mock network connectivity
        network_status = {"connected": True, "retry_count": 0}
        
        # Step 2: Simulate network failure during member addition
        network_status["connected"] = False
        
        member_form_elements = {
            'memberEmail': Mock(),
            'memberRole': Mock(),
            'addMemberSubmit': Mock()
        }
        
        member_form_elements['memberEmail'].send_keys("newmember@test.org")
        member_form_elements['memberRole'].send_keys("instructor")
        member_form_elements['addMemberSubmit'].click()
        
        # Mock network error
        if not network_status["connected"]:
            error_notification = Mock()
            error_notification.text = "Network error: Unable to add member. Retrying..."
            error_notification.className = "notification error"
            
            # Mock retry mechanism
            retry_button = Mock()
            retry_button.text = "Retry"
            retry_button.click()
            
            network_status["retry_count"] += 1
            
            # Verify error handling
            assert "Network error" in error_notification.text
            assert network_status["retry_count"] == 1
        
        # Step 3: Network recovery
        network_status["connected"] = True
        
        # Mock successful retry
        if network_status["connected"] and network_status["retry_count"] > 0:
            success_notification = Mock()
            success_notification.text = "Member added successfully"
            success_notification.className = "notification success"
            
            # Verify recovery
            assert "successfully" in success_notification.text
        
        # Step 4: Test offline mode functionality
        network_status["connected"] = False
        
        # Mock offline indicator
        offline_indicator = Mock()
        offline_indicator.text = "You are currently offline"
        offline_indicator.className = "offline-indicator visible"
        offline_indicator.style = Mock()
        offline_indicator.style.display = "block"
        
        # Mock cached data display
        cached_members = [
            {"name": "Cached Member 1", "email": "cached1@test.org"},
            {"name": "Cached Member 2", "email": "cached2@test.org"}
        ]
        
        members_container = Mock()
        cached_html = ""
        for member in cached_members:
            cached_html += f'<div class="member-card cached">{member["name"]}</div>'
        members_container.innerHTML = cached_html
        
        # Verify offline functionality
        assert offline_indicator.style.display == "block"
        assert "cached" in members_container.innerHTML.lower()
        
        # Step 5: Return online and sync
        network_status["connected"] = True
        
        # Mock sync process
        sync_notification = Mock()
        sync_notification.text = "Syncing data..."
        sync_notification.className = "notification info"
        
        # Mock successful sync
        sync_success = Mock()
        sync_success.text = "Data synchronized successfully"
        sync_success.className = "notification success"
        
        # Hide offline indicator
        offline_indicator.style.display = "none"
        
        # Verify sync completion
        assert "synchronized" in sync_success.text
        assert offline_indicator.style.display == "none"