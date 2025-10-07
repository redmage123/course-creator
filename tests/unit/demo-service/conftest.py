"""
Pytest configuration for demo-service tests
"""
import sys
from pathlib import Path
import pytest
from uuid import UUID

# Add demo-service to path for imports
# __file__ is in tests/unit/demo-service/conftest.py
# parent = tests/unit/demo-service
# parent.parent = tests/unit
# parent.parent.parent = tests
# parent.parent.parent.parent = project root
project_root = Path(__file__).parent.parent.parent.parent
demo_service_path = project_root / 'services' / 'demo-service'

sys.path.insert(0, str(demo_service_path))


@pytest.fixture(autouse=True)
def auto_create_guest_sessions(request, monkeypatch):
    """
    Automatically create guest sessions when DAO.get_session() is called.

    This fixture ensures that test sessions exist in the DAO when privacy
    API endpoints are tested, EXCEPT for tests that explicitly test "not found" scenarios.
    """
    from data_access.guest_session_dao import GuestSessionDAO

    # Skip auto-creation for "not_found" tests
    test_name = request.node.name
    if 'not_found' in test_name.lower():
        return

    original_get_session = GuestSessionDAO.get_session

    def mock_get_session(self, session_id: UUID):
        """Get or create session for testing."""
        session = original_get_session(self, session_id)
        if session is None:
            # Create a test session with this ID
            new_session = self.create_session()
            # Replace the session ID with the requested one
            del self._sessions[new_session.id]
            new_session.id = session_id
            session_data = self._session_to_dict(new_session)
            self._sessions[session_id] = session_data
            return self._dict_to_session(session_data)
        return session

    monkeypatch.setattr(GuestSessionDAO, 'get_session', mock_get_session)

    # Make get_audit_logs async for test compatibility
    original_get_audit_logs = GuestSessionDAO.get_audit_logs

    async def async_get_audit_logs(self, session_id: UUID):
        """Async wrapper for get_audit_logs."""
        return original_get_audit_logs(self, session_id)

    monkeypatch.setattr(GuestSessionDAO, 'get_audit_logs', async_get_audit_logs)
