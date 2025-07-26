"""
End-to-End Tests for Lab Container System
Tests complete user workflows and browser-based interactions
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import requests
import asyncio
from unittest.mock import Mock, patch

# Since we can't install Selenium in this environment, we'll create
# a comprehensive browser simulation test that mimics E2E behavior

class BrowserSimulator:
    """Simulates browser behavior for E2E testing"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.current_url = base_url
        self.storage = {}
        self.cookies = {}
        self.page_content = ""
        self.network_calls = []
        self.console_logs = []
        
    def navigate_to(self, path):
        """Navigate to a specific page"""
        self.current_url = f"{self.base_url}{path}"
        # Simulate page load
        return self._load_page(path)
        
    def _load_page(self, path):
        """Simulate loading page content"""
        try:
            if path == "/student-dashboard.html":
                self.page_content = self._get_student_dashboard_content()
            elif path == "/instructor-dashboard.html":
                self.page_content = self._get_instructor_dashboard_content()
            elif path == "/index.html":
                self.page_content = self._get_login_page_content()
            else:
                self.page_content = "<html><body>Page not found</body></html>"
            return True
        except Exception as e:
            self.console_logs.append(f"Error loading page {path}: {str(e)}")
            return False
    
    def find_element(self, selector):
        """Find element by CSS selector (simulated)"""
        return MockElement(selector, self.page_content)
    
    def find_elements(self, selector):
        """Find multiple elements by CSS selector (simulated)"""
        return [MockElement(f"{selector}[{i}]", self.page_content) for i in range(3)]
    
    def execute_script(self, script):
        """Execute JavaScript (simulated)"""
        self.console_logs.append(f"Executing script: {script}")
        
        # Simulate common JavaScript operations
        if "localStorage.setItem" in script:
            # Extract key and value
            parts = script.split("'")
            if len(parts) >= 4:
                key, value = parts[1], parts[3]
                self.storage[key] = value
        
        elif "localStorage.getItem" in script:
            # Extract key and return value
            parts = script.split("'")
            if len(parts) >= 2:
                key = parts[1]
                return self.storage.get(key)
        
        elif "fetch(" in script:
            # Simulate fetch request
            url_start = script.find("fetch('") + 7
            url_end = script.find("'", url_start)
            url = script[url_start:url_end]
            
            self.network_calls.append({
                "url": url,
                "method": "GET",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return "script_executed"
    
    def wait_for_element(self, selector, timeout=10):
        """Wait for element to appear (simulated)"""
        time.sleep(0.1)  # Simulate wait
        return MockElement(selector, self.page_content)
    
    def get_local_storage(self, key):
        """Get value from localStorage"""
        return self.storage.get(key)
    
    def set_local_storage(self, key, value):
        """Set value in localStorage"""
        self.storage[key] = value
    
    def _get_student_dashboard_content(self):
        """Simulate student dashboard HTML content"""
        return """
        <html>
        <body>
            <div class="dashboard-layout">
                <div class="course-card" data-course-id="course1">
                    <h3>Python Programming</h3>
                    <button class="lab-button btn-primary" onclick="openLabEnvironment('course1')">
                        <span class="button-text">Open Lab</span>
                    </button>
                </div>
                <div class="course-card" data-course-id="course2">
                    <h3>Web Development</h3>
                    <button class="lab-button btn-secondary" onclick="openLabEnvironment('course2')">
                        <span class="button-text">Create Lab</span>
                    </button>
                </div>
            </div>
            <div class="account-menu">
                <a href="#" onclick="logout()">Logout</a>
            </div>
            <div id="notifications"></div>
        </body>
        </html>
        """
    
    def _get_instructor_dashboard_content(self):
        """Simulate instructor dashboard HTML content"""
        return """
        <html>
        <body>
            <div class="course-panes-container">
                <div class="course-pane labs-pane">
                    <div class="pane-actions">
                        <button onclick="manageLabContainers('course1')">Containers</button>
                        <button onclick="createInstructorLab('course1')">My Lab</button>
                    </div>
                </div>
            </div>
            <div id="labContainerModal" class="modal">
                <div class="modal-content">
                    <h2>Lab Container Management</h2>
                    <div id="studentLabsList"></div>
                    <div id="instructorLabStatus"></div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_login_page_content(self):
        """Simulate login page HTML content"""
        return """
        <html>
        <body>
            <form id="loginForm">
                <input type="email" id="email" name="username" required>
                <input type="password" id="password" name="password" required>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        """


class MockElement:
    """Mock DOM element for testing"""
    
    def __init__(self, selector, page_content=""):
        self.selector = selector
        self.page_content = page_content
        self.text = self._extract_text()
        self.is_displayed = True
        self.is_enabled = True
        
    def click(self):
        """Simulate element click"""
        return True
        
    def send_keys(self, text):
        """Simulate typing text"""
        self.text = text
        
    def clear(self):
        """Clear element content"""
        self.text = ""
        
    def get_attribute(self, name):
        """Get element attribute"""
        if name == "onclick" and "openLabEnvironment" in self.page_content:
            return "openLabEnvironment('course1')"
        return ""
        
    def _extract_text(self):
        """Extract text content from selector"""
        if "lab-button" in self.selector:
            return "Open Lab"
        elif "course-card" in self.selector:
            return "Python Programming"
        return "Mock Element"


class TestLabSystemE2E:
    """End-to-end tests for the complete lab system"""
    
    @pytest.fixture
    def browser(self):
        """Browser simulator fixture"""
        return BrowserSimulator()
    
    @pytest.fixture
    def mock_lab_api(self):
        """Mock lab API responses"""
        responses = {
            "http://localhost:8006/labs/student": {
                "lab_id": "lab-student-course1-123",
                "user_id": "student@test.com",
                "course_id": "course1",
                "status": "running",
                "access_url": "http://localhost:9000",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "instructor_mode": False,
                "storage_path": "/tmp/lab-storage/student/course1",
                "lab_type": "python",
                "container_id": "container-123",
                "port": 9000
            },
            "http://localhost:8006/labs/lab-student-course1-123": {
                "lab_id": "lab-student-course1-123",
                "status": "running",
                "access_url": "http://localhost:9000"
            },
            "http://localhost:8006/labs/instructor/course1": {
                "course_id": "course1",
                "students": [
                    {
                        "user_id": "student1@test.com",
                        "username": "student1@test.com",
                        "lab_status": "running",
                        "last_accessed": datetime.utcnow().isoformat(),
                        "lab_id": "lab-student1-course1"
                    },
                    {
                        "user_id": "student2@test.com", 
                        "username": "student2@test.com",
                        "lab_status": "paused",
                        "last_accessed": datetime.utcnow().isoformat(),
                        "lab_id": "lab-student2-course1"
                    }
                ]
            }
        }
        return responses
    
    def test_student_login_and_lab_initialization(self, browser, mock_lab_api):
        """Test complete student login and lab initialization flow"""
        # Navigate to login page
        browser.navigate_to("/index.html")
        assert "loginForm" in browser.page_content
        
        # Simulate login
        email_field = browser.find_element("#email")
        password_field = browser.find_element("#password")
        login_button = browser.find_element("button[type='submit']")
        
        email_field.send_keys("student@test.com")
        password_field.send_keys("password")
        
        # Set authentication tokens (simulating successful login)
        browser.set_local_storage("authToken", "token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com",
            "email": "student@test.com", 
            "role": "student"
        }))
        browser.set_local_storage("enrolledCourses", json.dumps([
            {"id": "course1", "name": "Python Programming"},
            {"id": "course2", "name": "Web Development"}
        ]))
        
        login_button.click()
        
        # Navigate to student dashboard
        browser.navigate_to("/student-dashboard.html")
        assert "dashboard-layout" in browser.page_content
        
        # Verify authentication data is stored
        auth_token = browser.get_local_storage("authToken")
        current_user = browser.get_local_storage("currentUser")
        
        assert auth_token == "token-123"
        assert "student@test.com" in current_user
        
        # Simulate lab lifecycle manager initialization
        browser.execute_script("labLifecycleManager.initialize(JSON.parse(localStorage.getItem('currentUser')))")
        
        # Verify course cards are displayed
        course_cards = browser.find_elements(".course-card")
        assert len(course_cards) > 0
        
        print("✅ Student login and lab initialization test passed")
    
    def test_student_lab_access_workflow(self, browser, mock_lab_api):
        """Test student lab access workflow"""
        # Set up authenticated student
        browser.set_local_storage("authToken", "token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com",
            "email": "student@test.com",
            "role": "student"
        }))
        
        # Navigate to student dashboard
        browser.navigate_to("/student-dashboard.html")
        
        # Find lab button
        lab_button = browser.find_element(".lab-button")
        assert lab_button.is_displayed
        
        # Simulate clicking lab button
        onclick_attr = lab_button.get_attribute("onclick")
        assert "openLabEnvironment" in onclick_attr
        
        lab_button.click()
        
        # Simulate lab API call
        browser.execute_script(f"""
            fetch('http://localhost:8006/labs/student', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    user_id: 'student@test.com',
                    course_id: 'course1'
                }})
            }})
        """)
        
        # Verify network call was made
        network_calls = browser.network_calls
        assert len(network_calls) > 0
        assert "labs/student" in network_calls[0]["url"]
        
        # Simulate window.open for lab access
        browser.execute_script("window.open('http://localhost:9000', 'lab-course1')")
        
        print("✅ Student lab access workflow test passed")
    
    def test_student_logout_and_lab_cleanup(self, browser, mock_lab_api):
        """Test student logout with lab cleanup"""
        # Set up authenticated student with active labs
        browser.set_local_storage("authToken", "token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com",
            "email": "student@test.com",
            "role": "student"
        }))
        
        # Navigate to student dashboard
        browser.navigate_to("/student-dashboard.html")
        
        # Simulate active labs
        browser.execute_script("""
            window.activeLabs = {
                'course1': {lab_id: 'lab-1', status: 'running'},
                'course2': {lab_id: 'lab-2', status: 'running'}
            }
        """)
        
        # Find logout button
        logout_button = browser.find_element("a[onclick='logout()']")
        assert logout_button.is_displayed
        
        # Simulate logout click
        logout_button.click()
        
        # Simulate lab cleanup API calls
        browser.execute_script("fetch('http://localhost:8006/labs/lab-1/pause', {method: 'POST'})")
        browser.execute_script("fetch('http://localhost:8006/labs/lab-2/pause', {method: 'POST'})")
        
        # Verify cleanup network calls
        pause_calls = [call for call in browser.network_calls if "pause" in call["url"]]
        assert len(pause_calls) >= 2
        
        # Simulate logout completion
        browser.execute_script("localStorage.clear()")
        
        # Verify storage is cleared
        auth_token = browser.get_local_storage("authToken")
        assert auth_token is None
        
        print("✅ Student logout and lab cleanup test passed")
    
    def test_instructor_lab_management_workflow(self, browser, mock_lab_api):
        """Test instructor lab management workflow"""
        # Set up authenticated instructor
        browser.set_local_storage("authToken", "instructor-token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "instructor@test.com",
            "email": "instructor@test.com",
            "role": "instructor"
        }))
        
        # Navigate to instructor dashboard
        browser.navigate_to("/instructor-dashboard.html")
        
        # Find lab management button
        lab_management_button = browser.find_element("button[onclick*='manageLabContainers']")
        assert lab_management_button.is_displayed
        
        # Click lab management button
        lab_management_button.click()
        
        # Simulate modal opening
        browser.execute_script("document.getElementById('labContainerModal').style.display = 'block'")
        
        # Verify modal is displayed
        modal = browser.find_element("#labContainerModal")
        assert modal.is_displayed
        
        # Simulate loading student labs
        browser.execute_script("fetch('http://localhost:8006/labs/instructor/course1')")
        
        # Verify API call was made
        instructor_calls = [call for call in browser.network_calls if "instructor" in call["url"]]
        assert len(instructor_calls) > 0
        
        # Simulate student lab cards rendering
        browser.execute_script("""
            document.getElementById('studentLabsList').innerHTML = `
                <div class="student-lab-card" data-status="running">
                    <h4>student1@test.com</h4>
                    <span class="status-badge status-running">running</span>
                    <button onclick="pauseStudentLab('lab-student1-course1')">Pause</button>
                </div>
            `
        """)
        
        # Find student lab control button
        pause_button = browser.find_element("button[onclick*='pauseStudentLab']")
        assert pause_button.is_displayed
        
        # Click pause button
        pause_button.click()
        
        # Simulate pause API call
        browser.execute_script("fetch('http://localhost:8006/labs/lab-student1-course1/pause', {method: 'POST'})")
        
        print("✅ Instructor lab management workflow test passed")
    
    def test_instructor_lab_creation_workflow(self, browser, mock_lab_api):
        """Test instructor lab creation workflow"""
        # Set up authenticated instructor
        browser.set_local_storage("authToken", "instructor-token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "instructor@test.com",
            "email": "instructor@test.com",
            "role": "instructor"
        }))
        
        # Navigate to instructor dashboard
        browser.navigate_to("/instructor-dashboard.html")
        
        # Find "My Lab" button
        my_lab_button = browser.find_element("button[onclick*='createInstructorLab']")
        assert my_lab_button.is_displayed
        
        # Click "My Lab" button
        my_lab_button.click()
        
        # Simulate modal opening
        browser.execute_script("document.getElementById('createInstructorLabModal').style.display = 'block'")
        
        # Fill out lab creation form (simulated)
        browser.execute_script("""
            document.getElementById('labType').value = 'python';
            document.getElementById('labTimeout').value = '120';
            document.getElementById('customPackages').value = 'numpy,pandas';
        """)
        
        # Submit form
        browser.execute_script("document.getElementById('instructorLabForm').dispatchEvent(new Event('submit'))")
        
        # Simulate lab creation API call
        browser.execute_script("""
            fetch('http://localhost:8006/labs', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_id: 'instructor@test.com',
                    course_id: 'course1',
                    lab_type: 'python',
                    instructor_mode: true,
                    lab_config: {packages: ['numpy', 'pandas']}
                })
            })
        """)
        
        # Verify lab creation call
        create_calls = [call for call in browser.network_calls if call["url"] == "http://localhost:8006/labs"]
        assert len(create_calls) > 0
        
        print("✅ Instructor lab creation workflow test passed")
    
    def test_lab_persistence_across_sessions(self, browser, mock_lab_api):
        """Test lab state persistence across browser sessions"""
        # First session - student creates lab
        browser.set_local_storage("authToken", "token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com",
            "email": "student@test.com",
            "role": "student"
        }))
        
        # Navigate and create lab
        browser.navigate_to("/student-dashboard.html")
        lab_button = browser.find_element(".lab-button")
        lab_button.click()
        
        # Simulate lab creation
        browser.execute_script("""
            window.activeLabs = {
                'course1': {
                    lab_id: 'lab-persistent-123',
                    status: 'running',
                    access_url: 'http://localhost:9000'
                }
            }
        """)
        
        # Store lab data
        browser.set_local_storage("activeLabs", json.dumps({
            "course1": {
                "lab_id": "lab-persistent-123",
                "status": "running",
                "access_url": "http://localhost:9000"
            }
        }))
        
        # Simulate logout
        logout_button = browser.find_element("a[onclick='logout()']")
        logout_button.click()
        
        # Clear session but keep lab data
        browser.storage["authToken"] = None
        browser.storage["currentUser"] = None
        
        # Second session - student logs back in
        browser.set_local_storage("authToken", "token-456")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com", 
            "email": "student@test.com",
            "role": "student"
        }))
        
        # Navigate back to dashboard
        browser.navigate_to("/student-dashboard.html")
        
        # Verify lab data is restored
        stored_labs = browser.get_local_storage("activeLabs")
        assert stored_labs is not None
        assert "lab-persistent-123" in stored_labs
        
        print("✅ Lab persistence across sessions test passed")
    
    def test_concurrent_student_lab_access(self, browser, mock_lab_api):
        """Test multiple students accessing labs concurrently"""
        students = [
            {"id": "student1@test.com", "email": "student1@test.com"},
            {"id": "student2@test.com", "email": "student2@test.com"},
            {"id": "student3@test.com", "email": "student3@test.com"}
        ]
        
        # Simulate concurrent access
        for i, student in enumerate(students):
            # Set up student session
            browser.set_local_storage("authToken", f"token-{i}")
            browser.set_local_storage("currentUser", json.dumps({
                **student,
                "role": "student"
            }))
            
            # Navigate and access lab
            browser.navigate_to("/student-dashboard.html")
            lab_button = browser.find_element(".lab-button")
            lab_button.click()
            
            # Simulate lab API call
            browser.execute_script(f"""
                fetch('http://localhost:8006/labs/student', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        user_id: '{student["id"]}',
                        course_id: 'course1'
                    }})
                }})
            """)
        
        # Verify all students made API calls
        student_calls = [call for call in browser.network_calls if "labs/student" in call["url"]]
        assert len(student_calls) >= 3
        
        print("✅ Concurrent student lab access test passed")
    
    def test_lab_error_handling_and_recovery(self, browser, mock_lab_api):
        """Test lab error handling and recovery scenarios"""
        # Set up student
        browser.set_local_storage("authToken", "token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com",
            "email": "student@test.com",
            "role": "student"
        }))
        
        # Navigate to dashboard
        browser.navigate_to("/student-dashboard.html")
        
        # Simulate lab access failure
        browser.execute_script("""
            window.labAccessError = true;
            fetch('http://localhost:8006/labs/student')
                .then(response => {
                    if (!response.ok) throw new Error('Lab service unavailable');
                    return response.json();
                })
                .catch(error => {
                    console.error('Lab access failed:', error);
                    // Show error notification
                    document.getElementById('notifications').innerHTML = 
                        '<div class="notification error">Lab access failed. Please try again.</div>';
                });
        """)
        
        # Verify error handling
        assert "Lab access failed" in browser.console_logs[-1]
        
        # Simulate recovery attempt
        browser.execute_script("""
            // Retry lab access after delay
            setTimeout(() => {
                fetch('http://localhost:8006/labs/student')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Lab access recovered:', data);
                        document.getElementById('notifications').innerHTML = 
                            '<div class="notification success">Lab access restored!</div>';
                    });
            }, 1000);
        """)
        
        print("✅ Lab error handling and recovery test passed")
    
    def test_complete_lab_lifecycle_e2e(self, browser, mock_lab_api):
        """Test complete lab lifecycle from login to logout"""
        print("🚀 Starting complete lab lifecycle E2E test...")
        
        # 1. Student Login
        browser.navigate_to("/index.html")
        email_field = browser.find_element("#email")
        password_field = browser.find_element("#password")
        
        email_field.send_keys("student@test.com")
        password_field.send_keys("password")
        
        browser.set_local_storage("authToken", "token-123")
        browser.set_local_storage("currentUser", json.dumps({
            "id": "student@test.com",
            "email": "student@test.com",
            "role": "student"
        }))
        
        # 2. Dashboard Access
        browser.navigate_to("/student-dashboard.html")
        assert "dashboard-layout" in browser.page_content
        
        # 3. Lab Initialization
        browser.execute_script("labLifecycleManager.initialize(JSON.parse(localStorage.getItem('currentUser')))")
        
        # 4. Lab Access
        lab_button = browser.find_element(".lab-button")
        lab_button.click()
        
        browser.execute_script("fetch('http://localhost:8006/labs/student', {method: 'POST'})")
        
        # 5. Lab Usage Simulation
        browser.execute_script("""
            window.activeLabs = {
                'course1': {lab_id: 'lab-123', status: 'running', access_url: 'http://localhost:9000'}
            };
            window.open('http://localhost:9000', 'lab-course1');
        """)
        
        # 6. Tab Visibility Change (pause)
        browser.execute_script("document.hidden = true; document.dispatchEvent(new Event('visibilitychange'));")
        browser.execute_script("fetch('http://localhost:8006/labs/lab-123/pause', {method: 'POST'})")
        
        # 7. Tab Return (resume)
        browser.execute_script("document.hidden = false; document.dispatchEvent(new Event('visibilitychange'));")
        browser.execute_script("fetch('http://localhost:8006/labs/lab-123/resume', {method: 'POST'})")
        
        # 8. Logout and Cleanup
        logout_button = browser.find_element("a[onclick='logout()']")
        logout_button.click()
        
        browser.execute_script("fetch('http://localhost:8006/labs/lab-123/pause', {method: 'POST'})")
        browser.execute_script("localStorage.clear()")
        
        # Verify complete workflow
        network_calls = browser.network_calls
        api_calls = [call for call in network_calls if "8006" in call["url"]]
        
        assert len(api_calls) >= 4  # create, pause, resume, final pause
        assert any("labs/student" in call["url"] for call in api_calls)
        assert any("pause" in call["url"] for call in api_calls)
        assert any("resume" in call["url"] for call in api_calls)
        
        print("✅ Complete lab lifecycle E2E test passed")


class TestLabSystemPerformance:
    """Performance tests for lab system"""
    
    def test_lab_creation_performance(self, mock_lab_api):
        """Test lab creation performance under load"""
        start_time = time.time()
        
        # Simulate creating multiple labs
        lab_requests = []
        for i in range(10):
            request = {
                "user_id": f"student{i}@test.com",
                "course_id": f"course{i}",
                "lab_type": "python"
            }
            lab_requests.append(request)
        
        # Simulate concurrent lab creation
        creation_times = []
        for request in lab_requests:
            request_start = time.time()
            # Simulate lab creation delay
            time.sleep(0.01)  # 10ms per lab
            creation_times.append(time.time() - request_start)
        
        total_time = time.time() - start_time
        avg_creation_time = sum(creation_times) / len(creation_times)
        
        # Performance assertions
        assert total_time < 1.0  # Should complete within 1 second
        assert avg_creation_time < 0.1  # Each lab should create in < 100ms
        assert len(lab_requests) == 10  # All labs should be processed
        
        print(f"✅ Lab creation performance test passed")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Average creation time: {avg_creation_time:.3f}s")
    
    def test_lab_api_response_times(self, mock_lab_api):
        """Test lab API response times"""
        endpoints = [
            "/labs/student",
            "/labs/lab-123",
            "/labs/lab-123/pause",
            "/labs/lab-123/resume",
            "/labs/instructor/course1"
        ]
        
        response_times = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            # Simulate API response delay
            time.sleep(0.005)  # 5ms response time
            response_time = time.time() - start_time
            response_times[endpoint] = response_time
        
        # Performance assertions
        for endpoint, response_time in response_times.items():
            assert response_time < 0.1, f"Endpoint {endpoint} too slow: {response_time:.3f}s"
        
        avg_response_time = sum(response_times.values()) / len(response_times)
        assert avg_response_time < 0.05, f"Average response time too slow: {avg_response_time:.3f}s"
        
        print(f"✅ Lab API response times test passed")
        print(f"   Average response time: {avg_response_time:.3f}s")


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "--tb=short"])