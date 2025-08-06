"""
Test utilities for course creator platform tests
Provides common utilities for integration and e2e tests
"""

import requests
import time
from typing import Optional, Dict, Any


def wait_for_service(url: str, timeout: int = 30, interval: int = 1) -> bool:
    """Wait for a service to become available"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(interval)
    
    return False


def create_test_session(session_type: str = "instructor") -> Optional[Dict[str, Any]]:
    """Create a test session for integration testing"""
    try:
        # This would create a test session in the actual system
        # For now, return a mock session
        return {
            "session_id": "test-session",
            "user_type": session_type,
            "created": True
        }
    except Exception:
        return None


def cleanup_test_data(session_id: str) -> bool:
    """Clean up test data after testing"""
    try:
        # This would clean up test data in the actual system
        return True
    except Exception:
        return False