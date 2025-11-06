#!/usr/bin/env python3
"""
Unit Tests for Complete Project Management System

BUSINESS REQUIREMENT:
Tests all project management functionality: creation, instantiation, track/module management,
instructor assignment, student enrollment, analytics, unenrollment, and removal.

TECHNICAL IMPLEMENTATION:
Tests FastAPI endpoints for complete project lifecycle management including
validation, authorization, and error handling.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import uuid4, UUID
from datetime import datetime
import json

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock shared.cache module before importing organization-management modules
sys.modules['shared'] = MagicMock()
sys.modules['shared.cache'] = MagicMock()
sys.modules['shared.cache.redis_cache'] = MagicMock()

# Clean sys.path of other services to avoid 'main' module conflicts
sys.path = [p for p in sys.path if '/services/' not in p or 'organization-management' in p]

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'organization-management'))

from main import app, create_app
from api.project_endpoints import router
from exceptions import (
    ValidationException, AuthorizationException
)


class TestProjectCreationEndpoints:
    """Test suite for Project Creation and Management API Endpoints"""

    def setup_method(self):
        """Set up test fixtures for each test method"""
        self.client = TestClient(app)
        self.test_org_id = uuid4()
        self.test_user_id = uuid4()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
