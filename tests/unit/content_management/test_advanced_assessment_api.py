#!/usr/bin/env python3

"""
Advanced Assessment API Endpoint Tests

WHAT: Unit tests for advanced assessment REST API endpoints
WHERE: Tests endpoints in api/advanced_assessment_endpoints.py
WHY: Ensures API contracts, validation, and error handling work correctly

Author: Course Creator Platform
Version: 1.0.0
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
import pytest

# Add service path to allow imports
import os
service_path = os.path.join(
    os.path.dirname(__file__),
    '../../../services/content-management'
)
sys.path.insert(0, os.path.abspath(service_path))

# Mock all data_access modules before any imports
mock_dao_module = MagicMock()
sys.modules['data_access'] = mock_dao_module
sys.modules['data_access.advanced_assessment_dao'] = MagicMock()
sys.modules['data_access.interactive_content_dao'] = MagicMock()
sys.modules['data_access.content_version_dao'] = MagicMock()
sys.modules['data_access.content_dao'] = MagicMock()
sys.modules['data_access.syllabus_dao'] = MagicMock()
sys.modules['main'] = MagicMock()

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Import just the advanced_assessment_endpoints module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "advanced_assessment_endpoints",
    os.path.join(service_path, "api/advanced_assessment_endpoints.py")
)
api_module = importlib.util.module_from_spec(spec)
sys.modules['advanced_assessment_endpoints'] = api_module
spec.loader.exec_module(api_module)
router = api_module.router


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_service():
    """Creates mock assessment service"""
    service = AsyncMock()
    return service


@pytest.fixture
def app(mock_service):
    """Creates test FastAPI app with mocked dependencies"""
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[api_module.get_assessment_service] = lambda: mock_service
    yield test_app
    test_app.dependency_overrides.clear()


@pytest.fixture
def sample_assessment():
    """Sample assessment for testing"""
    return MagicMock(
        id=uuid4(),
        course_id=uuid4(),
        title="Test Assessment",
        description="Test description",
        instructions="Complete all questions",
        assessment_type=MagicMock(value="rubric"),
        status=MagicMock(value="draft"),
        max_score=Decimal("100"),
        passing_score=Decimal("70"),
        weight=Decimal("1.0"),
        max_attempts=3,
        time_limit_minutes=60,
        due_date=datetime.utcnow() + timedelta(days=7),
        available_from=datetime.utcnow(),
        available_until=datetime.utcnow() + timedelta(days=14),
        late_submission_allowed=True,
        late_penalty_percentage=Decimal("10"),
        peer_review_enabled=False,
        peer_review_type=None,
        peer_review_count=0,
        created_at=datetime.utcnow(),
        updated_at=None,
        published_at=None
    )


@pytest.fixture
def sample_submission():
    """Sample submission for testing"""
    return MagicMock(
        id=uuid4(),
        assessment_id=uuid4(),
        student_id=uuid4(),
        status=MagicMock(value="submitted"),
        attempt_number=1,
        content={"answers": ["a", "b", "c"]},
        reflections="My thoughts",
        started_at=datetime.utcnow(),
        submitted_at=datetime.utcnow(),
        is_late=False,
        final_score=Decimal("85"),
        passed=True,
        instructor_feedback="Good work",
        graded_at=datetime.utcnow()
    )


# ============================================================================
# Assessment Endpoint Tests
# ============================================================================


class TestAssessmentEndpoints:
    """Tests for assessment CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_create_assessment_success(self, app, mock_service, sample_assessment):
        """Tests successful assessment creation"""
        mock_service.create_assessment.return_value = sample_assessment

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/assessments",
                json={
                    "course_id": str(uuid4()),
                    "title": "Test Assessment",
                    "description": "Test description",
                    "assessment_type": "rubric",
                    "max_score": "100",
                    "passing_score": "70"
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Assessment"

    @pytest.mark.asyncio
    async def test_create_assessment_validation_error(self, app, mock_service):
        """Tests validation error on invalid data"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/assessments",
                json={
                    "course_id": str(uuid4()),
                    "title": "AB"  # Too short
                }
            )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_assessment_success(self, app, mock_service, sample_assessment):
        """Tests successful assessment retrieval"""
        mock_service.get_assessment.return_value = sample_assessment

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(f"/api/v1/assessments/{sample_assessment.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Assessment"

    @pytest.mark.asyncio
    async def test_get_assessment_not_found(self, app, mock_service):
        """Tests 404 when assessment not found"""
        mock_service.get_assessment.return_value = None

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(f"/api/v1/assessments/{uuid4()}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_assessment_success(self, app, mock_service, sample_assessment):
        """Tests successful assessment update"""
        sample_assessment.title = "Updated Title"
        sample_assessment.updated_at = datetime.utcnow()
        mock_service.update_assessment.return_value = sample_assessment

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.put(
                f"/api/v1/assessments/{sample_assessment.id}",
                json={"title": "Updated Title"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_publish_assessment_success(self, app, mock_service, sample_assessment):
        """Tests publishing an assessment"""
        sample_assessment.status = MagicMock(value="published")
        sample_assessment.published_at = datetime.utcnow()
        mock_service.publish_assessment.return_value = sample_assessment

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(f"/api/v1/assessments/{sample_assessment.id}/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"


# ============================================================================
# Rubric Endpoint Tests
# ============================================================================


class TestRubricEndpoints:
    """Tests for rubric management endpoints"""

    @pytest.mark.asyncio
    async def test_create_rubric_success(self, app, mock_service):
        """Tests successful rubric creation"""
        rubric_id = uuid4()
        assessment_id = uuid4()
        # Note: 'name' is a special MagicMock param, must set as attribute after
        rubric = MagicMock()
        rubric.id = rubric_id
        rubric.assessment_id = assessment_id
        rubric.name = "Test Rubric"
        rubric.rubric_type = "analytic"
        rubric.criteria = [MagicMock()]
        rubric.created_at = datetime.utcnow()
        # Explicitly set as AsyncMock with return value
        mock_service.create_rubric = AsyncMock(return_value=rubric)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/rubrics",
                json={
                    "assessment_id": str(uuid4()),
                    "name": "Test Rubric",
                    "rubric_type": "analytic",
                    "criteria": [
                        {
                            "name": "Clarity",
                            "max_points": 25,
                            "performance_levels": []
                        }
                    ]
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Rubric"


# ============================================================================
# Submission Endpoint Tests
# ============================================================================


class TestSubmissionEndpoints:
    """Tests for submission workflow endpoints"""

    @pytest.mark.asyncio
    async def test_start_submission_success(self, app, mock_service, sample_submission):
        """Tests starting a new submission"""
        mock_service.start_submission.return_value = sample_submission

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/submissions",
                json={
                    "assessment_id": str(uuid4()),
                    "student_id": str(uuid4())
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_submit_assessment_success(self, app, mock_service, sample_submission):
        """Tests submitting assessment for grading"""
        mock_service.submit_assessment.return_value = sample_submission

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(f"/api/v1/submissions/{sample_submission.id}/submit")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"


# ============================================================================
# Grading Endpoint Tests
# ============================================================================


class TestGradingEndpoints:
    """Tests for grading operations"""

    @pytest.mark.asyncio
    async def test_grade_submission_success(self, app, mock_service, sample_submission):
        """Tests grading a submission"""
        sample_submission.status = MagicMock(value="graded")
        mock_service.grade_submission.return_value = (sample_submission, [])

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                f"/api/v1/submissions/{sample_submission.id}/grade",
                json={
                    "grader_id": str(uuid4()),
                    "total_score": "85",
                    "feedback": "Good work!"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "graded"


# ============================================================================
# Peer Review Endpoint Tests
# ============================================================================


class TestPeerReviewEndpoints:
    """Tests for peer review functionality"""

    @pytest.mark.asyncio
    async def test_assign_peer_reviewers_success(self, app, mock_service):
        """Tests assigning peer reviewers"""
        reviewer_ids = [uuid4(), uuid4(), uuid4()]
        assignments = [MagicMock(id=uuid4(), reviewer_id=rid) for rid in reviewer_ids]
        mock_service.assign_peer_reviewers.return_value = assignments

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/peer-reviews/assign",
                json={
                    "assessment_id": str(uuid4()),
                    "submission_id": str(uuid4()),
                    "reviewer_ids": [str(rid) for rid in reviewer_ids]
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["assignments_created"] == 3


# ============================================================================
# Competency Endpoint Tests
# ============================================================================


class TestCompetencyEndpoints:
    """Tests for competency tracking"""

    @pytest.mark.asyncio
    async def test_create_competency_success(self, app, mock_service):
        """Tests creating a competency"""
        competency = MagicMock(
            id=uuid4(),
            code="PROG-001",
            name="Python Programming",
            required_proficiency=MagicMock(value="proficient"),
            created_at=datetime.utcnow()
        )
        mock_service.create_competency.return_value = competency

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/competencies",
                json={
                    "name": "Python Programming",
                    "code": "PROG-001",
                    "description": "Basic Python skills",
                    "organization_id": str(uuid4())
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "PROG-001"


# ============================================================================
# Portfolio Endpoint Tests
# ============================================================================


class TestPortfolioEndpoints:
    """Tests for portfolio management"""

    @pytest.mark.asyncio
    async def test_add_portfolio_artifact_success(self, app, mock_service):
        """Tests adding portfolio artifact"""
        artifact = MagicMock(
            id=uuid4(),
            title="Project Demo",
            artifact_type="video",
            created_at=datetime.utcnow()
        )
        mock_service.add_portfolio_artifact.return_value = artifact

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/portfolios/artifacts",
                json={
                    "submission_id": str(uuid4()),
                    "student_id": str(uuid4()),
                    "title": "Project Demo",
                    "description": "Demo video",
                    "artifact_type": "video",
                    "content_url": "https://example.com/video.mp4"
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Project Demo"


# ============================================================================
# Milestone Endpoint Tests
# ============================================================================


class TestMilestoneEndpoints:
    """Tests for project milestone management"""

    @pytest.mark.asyncio
    async def test_add_milestone_success(self, app, mock_service):
        """Tests adding project milestone"""
        milestone_id = uuid4()
        assessment_id = uuid4()
        # Note: 'name' is a special MagicMock param, must set as attribute after
        milestone = MagicMock()
        milestone.id = milestone_id
        milestone.assessment_id = assessment_id
        milestone.name = "Requirements"
        milestone.sort_order = 1
        milestone.due_date = datetime.utcnow() + timedelta(days=7)
        milestone.created_at = datetime.utcnow()
        # Explicitly set as AsyncMock with return value
        mock_service.add_milestone = AsyncMock(return_value=milestone)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/projects/milestones",
                json={
                    "assessment_id": str(uuid4()),
                    "name": "Requirements",
                    "description": "Requirements gathering",
                    "max_points": 25,
                    "sort_order": 1
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Requirements"


# ============================================================================
# Analytics Endpoint Tests
# ============================================================================


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints"""

    @pytest.mark.asyncio
    async def test_get_assessment_analytics_success(self, app, mock_service):
        """Tests getting assessment analytics"""
        analytics = MagicMock(
            assessment_id=uuid4(),
            submissions_count=50,
            completed_count=45,
            in_progress_count=5,
            pass_count=40,
            fail_count=5,
            average_score=Decimal("82.5"),
            median_score=Decimal("85"),
            highest_score=Decimal("100"),
            lowest_score=Decimal("45"),
            pass_rate=Decimal("88.9"),
            calculated_at=datetime.utcnow()
        )
        mock_service.get_assessment_analytics.return_value = analytics

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(f"/api/v1/analytics/assessments/{uuid4()}")

        assert response.status_code == 200
        data = response.json()
        assert data["submissions_count"] == 50

    @pytest.mark.asyncio
    async def test_get_assessment_analytics_no_data(self, app, mock_service):
        """Tests analytics when no submissions exist"""
        mock_service.get_assessment_analytics.return_value = None

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(f"/api/v1/analytics/assessments/{uuid4()}")

        assert response.status_code == 200
        data = response.json()
        assert data["submissions_count"] == 0


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, app, mock_service):
        """Tests invalid UUID handling"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get("/api/v1/assessments/not-a-valid-uuid")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_service_error_returns_500(self, app, mock_service):
        """Tests internal error handling"""
        mock_service.create_assessment.side_effect = Exception("Database error")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/assessments",
                json={
                    "course_id": str(uuid4()),
                    "title": "Test Assessment"
                }
            )

        assert response.status_code == 500
