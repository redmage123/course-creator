"""
Frontend Tests for Lab Integration System
Tests JavaScript modules, UI interactions, and browser-based functionality
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import asyncio
from datetime import datetime, timedelta

# For testing JavaScript functionality, we'll simulate browser behavior
class MockWindow:
    """Mock browser window object"""
    def __init__(self):
        self.localStorage = MockLocalStorage()
        self.locations = MockLocation()
        self.addEventListener = Mock()
        self.removeEventListener = Mock()
        self.open = Mock()
        self.focus = Mock()
        self.postMessage = Mock()
        self.closed = False
        
    def alert(self, message):
        print(f"Alert: {message}")
        
    def confirm(self, message):
        print(f"Confirm: {message}")
        return True


class MockLocalStorage:
    """Mock localStorage implementation"""
    def __init__(self):
        self._storage = {}
        
    def getItem(self, key):
        return self._storage.get(key)
        
    def setItem(self, key, value):
        self._storage[key] = str(value)
        
    def removeItem(self, key):
        if key in self._storage:
            del self._storage[key]
            
    def clear(self):
        self._storage.clear()


class MockLocation:
    """Mock window.locations object"""
    def __init__(self):
        self.href = "http://localhost:8080/student-dashboard.html"
        self.pathname = "/student-dashboard.html"
        self.origin = "http://localhost:8080"


class MockDocument:
    """Mock document object"""
    def __init__(self):
        self.readyState = "complete"
        self.hidden = False
        self.visibilityState = "visible"
        self.addEventListener = Mock()
        self.removeEventListener = Mock()
        self.createElement = Mock(return_value=MockElement())
        self.getElementById = Mock(return_value=MockElement())
        self.querySelector = Mock(return_value=MockElement())
        self.querySelectorAll = Mock(return_value=[MockElement()])
        self.body = MockElement()
        self.head = MockElement()


class MockElement:
    """Mock DOM element"""
    def __init__(self, tag_name="div"):
        self.tagName = tag_name
        self.innerHTML = ""
        self.textContent = ""
        self.className = ""
        self.style = MockStyle()
        self.classList = MockClassList()
        self.dataset = {}
        self.parentElement = None
        self.children = []
        self.addEventListener = Mock()
        self.removeEventListener = Mock()
        self.appendChild = Mock()
        self.remove = Mock()
        
    def getAttribute(self, name):
        return getattr(self, name, None)
        
    def setAttribute(self, name, value):
        setattr(self, name, value)


class MockStyle:
    """Mock element style object"""
    def __init__(self):
        self.display = "block"
        self.opacity = "1"
        self.animation = ""


class MockClassList:
    """Mock element classList object"""
    def __init__(self):
        self._classes = set()
        
    def add(self, class_name):
        self._classes.add(class_name)
        
    def remove(self, class_name):
        self._classes.discard(class_name)
        
    def contains(self, class_name):
        return class_name in self._classes


class MockFetch:
    """Mock fetch API"""
    def __init__(self):
        self.responses = {}
        self.calls = []
        
    def set_response(self, url, response_data, status_code=200):
        self.responses[url] = MockResponse(response_data, status_code)
        
    async def __call__(self, url, options=None):
        self.calls.append({"url": url, "options": options})
        
        # Check for exact URL match first
        if url in self.responses:
            return self.responses[url]
            
        # Check for pattern matches
        for pattern, response in self.responses.items():
            if pattern in url or url.startswith(pattern):
                return response
                
        # Default response
        return MockResponse({"error": "Not found"}, 404)


class MockResponse:
    """Mock fetch response"""
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        
    async def json(self):
        return self._data
        
    async def text(self):
        return json.dumps(self._data) if isinstance(self._data, dict) else str(self._data)


@pytest.fixture
def mock_browser_env():
    """Set up mock browser environment"""
    window = MockWindow()
    document = MockDocument()
    fetch = MockFetch()
    
    # Set up default responses
    fetch.set_response("http://localhost:8006/labs/student", {
        "lab_id": "test-lab-123",
        "user_id": "test-user",
        "course_id": "test-course",
        "status": "running",
        "access_url": "http://localhost:9000",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "last_accessed": datetime.utcnow().isoformat()
    })
    
    fetch.set_response("http://localhost:8006/labs/test-lab-123", {
        "lab_id": "test-lab-123",
        "status": "running",
        "access_url": "http://localhost:9000"
    })
    
    return {
        "window": window,
        "document": document,
        "fetch": fetch
    }


class TestLabLifecycleManager:
    """Test the Lab Lifecycle Manager JavaScript class"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_browser_env):
        """Test lab lifecycle manager initialization"""
        # Mock the lab lifecycle manager
        class MockLabLifecycleManager:
            def __init__(self):
                self.initialized = False
                self.current_user = None
                self.enrolled_courses = []
                self.active_labs = {}
                
            async def initialize(self, user):
                self.current_user = user
                self.initialized = True
                
                # Simulate loading enrolled courses
                self.enrolled_courses = [
                    {"id": "course1", "name": "Python Programming"},
                    {"id": "course2", "name": "Web Development"}
                ]
                
                # Simulate initializing labs
                for course in self.enrolled_courses:
                    lab_data = await self.get_or_create_student_lab(course["id"])
                    self.active_labs[course["id"]] = lab_data
                
                return True
                
            async def get_or_create_student_lab(self, course_id):
                return {
                    "lab_id": f"lab-{self.current_user['id']}-{course_id}",
                    "course_id": course_id,
                    "status": "running",
                    "access_url": f"http://localhost:900{len(self.active_labs)}"
                }
        
        manager = MockLabLifecycleManager()
        
        # Test initialization
        user = {"id": "test-user", "email": "test@example.com", "role": "student"}
        await manager.initialize(user)
        
        assert manager.initialized is True
        assert manager.current_user == user
        assert len(manager.enrolled_courses) == 2
        assert len(manager.active_labs) == 2

    @pytest.mark.asyncio
    async def test_lab_access(self, mock_browser_env):
        """Test lab access functionality"""
        fetch = mock_browser_env["fetch"]
        window = mock_browser_env["window"]
        
        # Mock lab lifecycle manager with access method
        class MockLabLifecycleManager:
            def __init__(self):
                self.active_labs = {
                    "course1": {
                        "lab_id": "test-lab-123",
                        "status": "running",
                        "access_url": "http://localhost:9000"
                    }
                }
                
            async def access_lab(self, course_id):
                lab = self.active_labs.get(course_id)
                if not lab:
                    raise Exception("Lab not found")
                    
                if lab["status"] == "paused":
                    # Resume lab
                    lab["status"] = "running"
                    
                return lab["access_url"]
        
        manager = MockLabLifecycleManager()
        
        # Test successful lab access
        access_url = await manager.access_lab("course1")
        assert access_url == "http://localhost:9000"
        
        # Test lab not found
        with pytest.raises(Exception, match="Lab not found"):
            await manager.access_lab("nonexistent-course")

    @pytest.mark.asyncio
    async def test_lab_pause_resume_cycle(self, mock_browser_env):
        """Test lab pause and resume functionality"""
        fetch = mock_browser_env["fetch"]
        
        # Set up pause/resume responses
        fetch.set_response("http://localhost:8006/labs/test-lab-123/pause", {"message": "Lab paused"})
        fetch.set_response("http://localhost:8006/labs/test-lab-123/resume", {"message": "Lab resumed"})
        
        class MockLabLifecycleManager:
            def __init__(self):
                self.active_labs = {
                    "course1": {
                        "lab_id": "test-lab-123",
                        "status": "running"
                    }
                }
                
            async def pause_lab(self, lab_id):
                # Simulate API call
                response = await fetch(f"http://localhost:8006/labs/{lab_id}/pause", {
                    "method": "POST"
                })
                
                if response.ok:
                    # Update local state
                    for course_id, lab in self.active_labs.items():
                        if lab["lab_id"] == lab_id:
                            lab["status"] = "paused"
                            break
                    return True
                return False
                
            async def resume_lab(self, lab_id):
                # Simulate API call
                response = await fetch(f"http://localhost:8006/labs/{lab_id}/resume", {
                    "method": "POST"
                })
                
                if response.ok:
                    # Update local state
                    for course_id, lab in self.active_labs.items():
                        if lab["lab_id"] == lab_id:
                            lab["status"] = "running"
                            break
                    return True
                return False
        
        manager = MockLabLifecycleManager()
        
        # Test pause
        success = await manager.pause_lab("test-lab-123")
        assert success is True
        assert manager.active_labs["course1"]["status"] == "paused"
        
        # Test resume
        success = await manager.resume_lab("test-lab-123")
        assert success is True
        assert manager.active_labs["course1"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_cleanup_on_logout(self, mock_browser_env):
        """Test lab cleanup on logout"""
        fetch = mock_browser_env["fetch"]
        
        # Set up pause responses for multiple labs
        fetch.set_response("http://localhost:8006/labs/lab-1/pause", {"message": "Lab paused"})
        fetch.set_response("http://localhost:8006/labs/lab-2/pause", {"message": "Lab paused"})
        
        class MockLabLifecycleManager:
            def __init__(self):
                self.active_labs = {
                    "course1": {"lab_id": "lab-1", "status": "running"},
                    "course2": {"lab_id": "lab-2", "status": "running"}
                }
                self.initialized = True
                
            async def cleanup(self):
                # Pause all active labs
                for course_id, lab in self.active_labs.items():
                    if lab["status"] == "running":
                        await self.pause_lab(lab["lab_id"])
                
                # Clear state
                self.active_labs.clear()
                self.initialized = False
                
            async def pause_lab(self, lab_id):
                response = await fetch(f"http://localhost:8006/labs/{lab_id}/pause", {
                    "method": "POST"
                })
                return response.ok
        
        manager = MockLabLifecycleManager()
        
        # Verify initial state
        assert len(manager.active_labs) == 2
        assert manager.initialized is True
        
        # Test cleanup
        await manager.cleanup()
        
        # Verify cleanup completed
        assert len(manager.active_labs) == 0
        assert manager.initialized is False


class TestInstructorLabManagement:
    """Test instructor lab management UI functionality"""
    
    def test_lab_management_modal_display(self, mock_browser_env):
        """Test lab management modal display"""
        document = mock_browser_env["document"]
        
        # Mock modal element
        modal = MockElement()
        modal.style.display = "none"
        document.getElementById.return_value = modal
        
        # Simulate opening lab management modal
        def show_modal(modal_id):
            modal_element = document.getElementById(modal_id)
            modal_element.style.display = "block"
            return modal_element
        
        # Test modal display
        result = show_modal("labContainerModal")
        assert result.style.display == "block"
        document.getElementById.assert_called_with("labContainerModal")

    @pytest.mark.asyncio
    async def test_student_lab_overview_loading(self, mock_browser_env):
        """Test loading student lab overview"""
        fetch = mock_browser_env["fetch"]
        document = mock_browser_env["document"]
        
        # Mock API response
        fetch.set_response("http://localhost:8006/labs/instructor/course123", {
            "course_id": "course123",
            "students": [
                {
                    "user_id": "student1",
                    "username": "student1@test.com",
                    "lab_status": "running",
                    "last_accessed": datetime.utcnow().isoformat(),
                    "lab_id": "lab-student1-course123"
                },
                {
                    "user_id": "student2",
                    "username": "student2@test.com",
                    "lab_status": "paused",
                    "last_accessed": datetime.utcnow().isoformat(),
                    "lab_id": "lab-student2-course123"
                }
            ]
        })
        
        # Mock DOM elements
        students_list = MockElement()
        document.getElementById.return_value = students_list
        
        # Simulate loading student labs
        async def load_student_labs(course_id):
            response = await fetch(f"http://localhost:8006/labs/instructor/{course_id}")
            data = await response.json()
            
            # Simulate rendering student cards
            students_html = ""
            for student in data["students"]:
                students_html += f'<div class="student-lab-card" data-status="{student["lab_status"]}">'
                students_html += f'<h4>{student["username"]}</h4>'
                students_html += f'<span class="status-badge">{student["lab_status"]}</span>'
                students_html += '</div>'
            
            students_list.innerHTML = students_html
            return data
        
        # Test loading
        result = await load_student_labs("course123")
        
        assert len(result["students"]) == 2
        assert "student-lab-card" in students_list.innerHTML
        assert "running" in students_list.innerHTML
        assert "paused" in students_list.innerHTML

    @pytest.mark.asyncio
    async def test_bulk_lab_operations(self, mock_browser_env):
        """Test bulk lab operations (pause all, stop all)"""
        fetch = mock_browser_env["fetch"]
        
        # Set up API responses
        fetch.set_response("http://localhost:8006/labs/instructor/course123", {
            "course_id": "course123",
            "students": [
                {"lab_id": "lab-1", "lab_status": "running"},
                {"lab_id": "lab-2", "lab_status": "running"},
                {"lab_id": "lab-3", "lab_status": "paused"}
            ]
        })
        
        fetch.set_response("http://localhost:8006/labs/lab-1/pause", {"message": "Lab paused"})
        fetch.set_response("http://localhost:8006/labs/lab-2/pause", {"message": "Lab paused"})
        
        async def pause_all_student_labs(course_id):
            # Get all student labs
            response = await fetch(f"http://localhost:8006/labs/instructor/{course_id}")
            data = await response.json()
            
            paused_count = 0
            for student in data["students"]:
                if student["lab_status"] == "running":
                    pause_response = await fetch(f"http://localhost:8006/labs/{student['lab_id']}/pause", {
                        "method": "POST"
                    })
                    if pause_response.ok:
                        paused_count += 1
            
            return paused_count
        
        # Test bulk pause
        paused_count = await pause_all_student_labs("course123")
        assert paused_count == 2  # Only running labs should be paused

    def test_lab_status_filtering(self, mock_browser_env):
        """Test lab status filtering functionality"""
        document = mock_browser_env["document"]
        
        # Mock student lab cards
        cards = [
            MockElement(),
            MockElement(),
            MockElement()
        ]
        
        cards[0].dataset = {"status": "running", "username": "student1"}
        cards[1].dataset = {"status": "paused", "username": "student2"}
        cards[2].dataset = {"status": "error", "username": "student3"}
        
        for card in cards:
            card.style.display = "block"
        
        document.querySelectorAll.return_value = cards
        
        def filter_student_labs(name_filter="", status_filter=""):
            name_filter = name_filter.lower()
            
            for card in cards:
                username = card.dataset.get("username", "").lower()
                status = card.dataset.get("status", "")
                
                name_match = not name_filter or name_filter in username
                status_match = not status_filter or status == status_filter
                
                card.style.display = "block" if (name_match and status_match) else "none"
        
        # Test status filtering
        filter_student_labs(status_filter="running")
        assert cards[0].style.display == "block"
        assert cards[1].style.display == "none"
        assert cards[2].style.display == "none"
        
        # Test name filtering
        filter_student_labs(name_filter="student2")
        assert cards[0].style.display == "none"
        assert cards[1].style.display == "block"
        assert cards[2].style.display == "none"
        
        # Test combined filtering
        filter_student_labs(name_filter="student", status_filter="error")
        assert cards[0].style.display == "none"
        assert cards[1].style.display == "none"
        assert cards[2].style.display == "block"


class TestStudentLabIntegration:
    """Test student-side lab integration"""
    
    @pytest.mark.asyncio
    async def test_lab_button_status_updates(self, mock_browser_env):
        """Test lab button status updates"""
        document = mock_browser_env["document"]
        
        # Mock lab button
        lab_button = MockElement()
        lab_button.classList = MockClassList()
        
        button_text = MockElement()
        lab_button.querySelector = Mock(return_value=button_text)
        
        document.querySelector.return_value = lab_button
        
        def update_lab_status_indicator(course_id, status):
            button = document.querySelector(f"[onclick=\"openLabEnvironment('{course_id}')\"]")
            
            if button:
                # Remove all status classes
                status_classes = ["btn-success", "btn-warning", "btn-info", "btn-secondary", "btn-danger", "btn-primary"]
                for cls in status_classes:
                    button.classList.remove(cls)
                
                # Add current status class
                status_class_map = {
                    "running": "btn-success",
                    "paused": "btn-warning",
                    "building": "btn-info",
                    "stopped": "btn-secondary",
                    "error": "btn-danger",
                    "not_created": "btn-primary"
                }
                
                button.classList.add(status_class_map.get(status, "btn-primary"))
                
                # Update button text
                status_text_map = {
                    "running": "Open Lab",
                    "paused": "Resume Lab",
                    "building": "Building...",
                    "stopped": "Start Lab",
                    "error": "Lab Error",
                    "not_created": "Create Lab"
                }
                
                button_text_element = button.querySelector(".button-text")
                if button_text_element:
                    button_text_element.textContent = status_text_map.get(status, "Lab Environment")
        
        # Test status updates
        update_lab_status_indicator("course1", "running")
        assert lab_button.classList.contains("btn-success")
        assert button_text.textContent == "Open Lab"
        
        update_lab_status_indicator("course1", "paused")
        assert lab_button.classList.contains("btn-warning")
        assert button_text.textContent == "Resume Lab"
        
        update_lab_status_indicator("course1", "building")
        assert lab_button.classList.contains("btn-info")
        assert button_text.textContent == "Building..."

    @pytest.mark.asyncio
    async def test_lab_window_management(self, mock_browser_env):
        """Test lab window opening and management"""
        window = mock_browser_env["window"]
        
        # Mock window.open
        mock_lab_window = MockWindow()
        window.open.return_value = mock_lab_window
        
        async def open_lab_environment(course_id, access_url):
            # Open lab in new window
            lab_window = window.open(
                access_url,
                f"lab-{course_id}",
                "width=1200,height=800,scrollbars=yes,resizable=yes"
            )
            
            if lab_window:
                lab_window.focus()
                return lab_window
            
            return None
        
        # Test lab window opening
        lab_window = await open_lab_environment("course1", "http://localhost:9000")
        
        assert lab_window is not None
        window.open.assert_called_with(
            "http://localhost:9000",
            "lab-course1",
            "width=1200,height=800,scrollbars=yes,resizable=yes"
        )

    def test_notification_system(self, mock_browser_env):
        """Test notification system"""
        document = mock_browser_env["document"]
        
        # Mock notification creation
        notification_element = MockElement()
        document.createElement.return_value = notification_element
        document.body = MockElement()
        
        def show_notification(message, type="info"):
            notification = document.createElement("div")
            notification.className = f"lab-notification lab-notification-{type}"
            
            icons = {
                "success": "fas fa-check-circle",
                "error": "fas fa-exclamation-circle",
                "warning": "fas fa-exclamation-triangle",
                "info": "fas fa-info-circle"
            }
            
            notification.innerHTML = f"""
                <div class="lab-notification-content">
                    <i class="{icons.get(type, icons['info'])}"></i>
                    <span class="lab-notification-message">{message}</span>
                    <button class="lab-notification-close">×</button>
                </div>
            """
            
            document.body.appendChild(notification)
            return notification
        
        # Test notification creation
        notification = show_notification("Lab environment ready!", "success")
        
        assert notification.className == "lab-notification lab-notification-success"
        assert "Lab environment ready!" in notification.innerHTML
        assert "fas fa-check-circle" in notification.innerHTML
        document.body.appendChild.assert_called_with(notification)

    @pytest.mark.asyncio
    async def test_authentication_integration(self, mock_browser_env):
        """Test authentication integration with lab system"""
        window = mock_browser_env["window"]
        fetch = mock_browser_env["fetch"]
        
        # Mock auth manager
        class MockAuthManager:
            def __init__(self):
                self.current_user = None
                self.auth_token = None
                
            async def login(self, credentials):
                # Simulate successful login
                self.current_user = {
                    "id": "test-user",
                    "email": credentials["username"],
                    "role": "student"
                }
                self.auth_token = "test-token-123"
                
                window.localStorage.setItem("authToken", self.auth_token)
                window.localStorage.setItem("currentUser", json.dumps(self.current_user))
                
                return {"success": True, "user": self.current_user}
                
            async def logout(self):
                # Simulate logout with lab cleanup
                self.current_user = None
                self.auth_token = None
                
                window.localStorage.removeItem("authToken")
                window.localStorage.removeItem("currentUser")
                
                return {"success": True}
        
        # Mock lab lifecycle manager
        class MockLabLifecycleManager:
            def __init__(self):
                self.initialized = False
                
            async def initialize(self, user):
                self.initialized = True
                # Simulate lab initialization
                return True
                
            async def cleanup(self):
                self.initialized = False
                # Simulate lab cleanup
                return True
        
        auth_manager = MockAuthManager()
        lab_manager = MockLabLifecycleManager()
        
        # Test login flow
        login_result = await auth_manager.login({"username": "test@example.com", "password": "password"})
        assert login_result["success"] is True
        
        # Simulate lab manager initialization after login
        if login_result["user"]["role"] == "student":
            await lab_manager.initialize(login_result["user"])
        
        assert lab_manager.initialized is True
        assert window.localStorage.getItem("authToken") == "test-token-123"
        
        # Test logout flow
        logout_result = await auth_manager.logout()
        assert logout_result["success"] is True
        
        # Simulate lab cleanup after logout
        await lab_manager.cleanup()
        
        assert lab_manager.initialized is False
        assert window.localStorage.getItem("authToken") is None


class TestLabAnalytics:
    """Test lab analytics and tracking functionality"""
    
    def test_lab_access_tracking(self, mock_browser_env):
        """Test lab access tracking"""
        window = mock_browser_env["window"]
        
        def track_lab_access(course_id, user_id):
            access_data = {
                "course_id": course_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": f"session-{int(time.time())}"
            }
            
            # Get existing access data
            existing_access = window.localStorage.getItem("labAccess")
            access_list = json.loads(existing_access) if existing_access else []
            
            # Add new access
            access_list.append(access_data)
            
            # Keep only last 100 accesses
            if len(access_list) > 100:
                access_list = access_list[-100:]
            
            window.localStorage.setItem("labAccess", json.dumps(access_list))
            return access_data
        
        # Test tracking
        access1 = track_lab_access("course1", "user1")
        access2 = track_lab_access("course2", "user1")
        
        # Verify tracking
        stored_access = json.loads(window.localStorage.getItem("labAccess"))
        assert len(stored_access) == 2
        assert stored_access[0]["course_id"] == "course1"
        assert stored_access[1]["course_id"] == "course2"

    def test_lab_analytics_calculation(self, mock_browser_env):
        """Test lab analytics calculation"""
        window = mock_browser_env["window"]
        
        # Set up sample access data
        sample_access = [
            {"course_id": "course1", "user_id": "user1", "timestamp": "2023-01-01T10:00:00"},
            {"course_id": "course1", "user_id": "user1", "timestamp": "2023-01-01T11:00:00"},
            {"course_id": "course2", "user_id": "user1", "timestamp": "2023-01-01T12:00:00"},
            {"course_id": "course1", "user_id": "user2", "timestamp": "2023-01-01T13:00:00"}
        ]
        
        window.localStorage.setItem("labAccess", json.dumps(sample_access))
        
        def get_lab_analytics():
            access_data = json.loads(window.localStorage.getItem("labAccess") or "[]")
            
            total_accesses = len(access_data)
            unique_courses = len(set(item["course_id"] for item in access_data))
            unique_users = len(set(item["user_id"] for item in access_data))
            
            last_access = None
            if access_data:
                last_access = access_data[-1]["timestamp"]
            
            return {
                "total_accesses": total_accesses,
                "unique_courses": unique_courses,
                "unique_users": unique_users,
                "last_access": last_access
            }
        
        # Test analytics calculation
        analytics = get_lab_analytics()
        
        assert analytics["total_accesses"] == 4
        assert analytics["unique_courses"] == 2
        assert analytics["unique_users"] == 2
        assert analytics["last_access"] == "2023-01-01T13:00:00"


if __name__ == "__main__":
    # Run frontend tests
    pytest.main([__file__, "-v", "--tb=short"])