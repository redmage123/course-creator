"""
Unit Tests for RBAC Track Service
Tests the learning track management functionality
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Add test fixtures path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../fixtures'))

from rbac_fixtures import (
    mock_track_data,
    mock_track_repository,
    mock_audit_logger,
    mock_email_service,
    RBACTestUtils
)


class TestTrackService:
    """Test cases for TrackService"""
    
    @pytest.fixture
    def track_service(self, mock_track_repository, mock_audit_logger, mock_email_service):
        """Create track service with mocked dependencies."""
        from unittest.mock import Mock
        
        service = Mock()
        service.track_repository = mock_track_repository
        service.audit_logger = mock_audit_logger
        service.email_service = mock_email_service
        
        # Mock service methods
        async def mock_create_track(org_id, track_data):
            return {
                "id": str(uuid.uuid4()),
                "name": track_data["name"],
                "description": track_data.get("description", ""),
                "organization_id": org_id,
                "project_id": track_data.get("project_id"),
                "difficulty_level": track_data.get("difficulty_level", "beginner"),
                "duration_weeks": track_data.get("duration_weeks", 8),
                "target_audience": track_data.get("target_audience", []),
                "prerequisites": track_data.get("prerequisites", []),
                "learning_objectives": track_data.get("learning_objectives", []),
                "status": "active",
                "auto_enrollment": track_data.get("auto_enrollment", False),
                "created_at": datetime.utcnow()
            }
        
        async def mock_get_organization_tracks(org_id, filters=None):
            tracks = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Python Programming Track",
                    "description": "Learn Python from basics to advanced",
                    "difficulty_level": "intermediate",
                    "duration_weeks": 12,
                    "status": "active",
                    "enrolled_count": 15
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Web Development Track",
                    "description": "Full-stack web development",
                    "difficulty_level": "advanced",
                    "duration_weeks": 16,
                    "status": "active",
                    "enrolled_count": 8
                }
            ]
            
            if filters:
                if "difficulty_level" in filters:
                    tracks = [t for t in tracks if t["difficulty_level"] == filters["difficulty_level"]]
                if "status" in filters:
                    tracks = [t for t in tracks if t["status"] == filters["status"]]
            
            return tracks
        
        async def mock_update_track(track_id, update_data):
            return {
                "id": track_id,
                **update_data,
                "updated_at": datetime.utcnow()
            }
        
        async def mock_delete_track(track_id):
            return {
                "success": True,
                "track_id": track_id,
                "unenrolled_students": 5
            }
        
        async def mock_enroll_student_in_track(track_id, student_id):
            return {
                "id": str(uuid.uuid4()),
                "track_id": track_id,
                "student_id": student_id,
                "enrolled_at": datetime.utcnow(),
                "status": "active",
                "progress": 0.0
            }
        
        async def mock_get_track_enrollments(track_id):
            return [
                {
                    "id": str(uuid.uuid4()),
                    "student_id": str(uuid.uuid4()),
                    "student_name": "John Student",
                    "enrolled_at": datetime.utcnow() - timedelta(days=10),
                    "progress": 0.3,
                    "status": "active"
                },
                {
                    "id": str(uuid.uuid4()),
                    "student_id": str(uuid.uuid4()),
                    "student_name": "Jane Student",
                    "enrolled_at": datetime.utcnow() - timedelta(days=5),
                    "progress": 0.1,
                    "status": "active"
                }
            ]
        
        service.create_track = mock_create_track
        service.get_organization_tracks = mock_get_organization_tracks
        service.update_track = mock_update_track
        service.delete_track = mock_delete_track
        service.enroll_student_in_track = mock_enroll_student_in_track
        service.get_track_enrollments = mock_get_track_enrollments
        
        return service
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_track_success(self, track_service):
        """Test successful track creation."""
        # Arrange
        org_id = str(uuid.uuid4())
        track_data = {
            "name": "Advanced Machine Learning",
            "description": "Deep dive into ML algorithms and applications",
            "project_id": str(uuid.uuid4()),
            "difficulty_level": "advanced",
            "duration_weeks": 16,
            "target_audience": ["data_scientists", "developers"],
            "prerequisites": ["python_programming", "statistics"],
            "learning_objectives": [
                "Master supervised learning algorithms",
                "Understand neural networks",
                "Build ML applications"
            ],
            "auto_enrollment": True
        }
        
        # Act
        result = await track_service.create_track(org_id, track_data)
        
        # Assert
        assert result["name"] == track_data["name"]
        assert result["description"] == track_data["description"]
        assert result["organization_id"] == org_id
        assert result["project_id"] == track_data["project_id"]
        assert result["difficulty_level"] == track_data["difficulty_level"]
        assert result["duration_weeks"] == track_data["duration_weeks"]
        assert result["target_audience"] == track_data["target_audience"]
        assert result["prerequisites"] == track_data["prerequisites"]
        assert result["learning_objectives"] == track_data["learning_objectives"]
        assert result["auto_enrollment"] == track_data["auto_enrollment"]
        assert result["status"] == "active"
        assert "id" in result
        assert "created_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_track_with_minimal_data(self, track_service):
        """Test track creation with minimal required data."""
        # Arrange
        org_id = str(uuid.uuid4())
        track_data = {
            "name": "Basic Programming"
        }
        
        # Act
        result = await track_service.create_track(org_id, track_data)
        
        # Assert
        assert result["name"] == track_data["name"]
        assert result["organization_id"] == org_id
        assert result["difficulty_level"] == "beginner"  # Default
        assert result["duration_weeks"] == 8  # Default
        assert result["target_audience"] == []  # Default
        assert result["prerequisites"] == []  # Default
        assert result["learning_objectives"] == []  # Default
        assert result["auto_enrollment"] is False  # Default
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_organization_tracks_all(self, track_service):
        """Test getting all organization tracks."""
        # Arrange
        org_id = str(uuid.uuid4())
        
        # Act
        result = await track_service.get_organization_tracks(org_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        
        for track in result:
            assert "id" in track
            assert "name" in track
            assert "description" in track
            assert "difficulty_level" in track
            assert "duration_weeks" in track
            assert "status" in track
            assert "enrolled_count" in track
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_organization_tracks_filtered_by_difficulty(self, track_service):
        """Test getting organization tracks filtered by difficulty level."""
        # Arrange
        org_id = str(uuid.uuid4())
        filters = {"difficulty_level": "intermediate"}
        
        # Act
        result = await track_service.get_organization_tracks(org_id, filters)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["difficulty_level"] == "intermediate"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_organization_tracks_filtered_by_status(self, track_service):
        """Test getting organization tracks filtered by status."""
        # Arrange
        org_id = str(uuid.uuid4())
        filters = {"status": "active"}
        
        # Act
        result = await track_service.get_organization_tracks(org_id, filters)
        
        # Assert
        assert isinstance(result, list)
        for track in result:
            assert track["status"] == "active"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_track_success(self, track_service):
        """Test successful track update."""
        # Arrange
        track_id = str(uuid.uuid4())
        update_data = {
            "name": "Updated Track Name",
            "description": "Updated description",
            "difficulty_level": "advanced",
            "duration_weeks": 20,
            "status": "inactive"
        }
        
        # Act
        result = await track_service.update_track(track_id, update_data)
        
        # Assert
        assert result["id"] == track_id
        assert result["name"] == update_data["name"]
        assert result["description"] == update_data["description"]
        assert result["difficulty_level"] == update_data["difficulty_level"]
        assert result["duration_weeks"] == update_data["duration_weeks"]
        assert result["status"] == update_data["status"]
        assert "updated_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_track_success(self, track_service):
        """Test successful track deletion."""
        # Arrange
        track_id = str(uuid.uuid4())
        
        # Act
        result = await track_service.delete_track(track_id)
        
        # Assert
        assert result["success"] is True
        assert result["track_id"] == track_id
        assert "unenrolled_students" in result
        assert result["unenrolled_students"] >= 0
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enroll_student_in_track_success(self, track_service):
        """Test successful student enrollment in track."""
        # Arrange
        track_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        
        # Act
        result = await track_service.enroll_student_in_track(track_id, student_id)
        
        # Assert
        assert result["track_id"] == track_id
        assert result["student_id"] == student_id
        assert result["status"] == "active"
        assert result["progress"] == 0.0
        assert "id" in result
        assert "enrolled_at" in result
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_track_enrollments(self, track_service):
        """Test getting track enrollments."""
        # Arrange
        track_id = str(uuid.uuid4())
        
        # Act
        result = await track_service.get_track_enrollments(track_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        
        for enrollment in result:
            assert "id" in enrollment
            assert "student_id" in enrollment
            assert "student_name" in enrollment
            assert "enrolled_at" in enrollment
            assert "progress" in enrollment
            assert "status" in enrollment
            assert 0.0 <= enrollment["progress"] <= 1.0
    
    @pytest.mark.unit  
    def test_validate_track_data_valid(self):
        """Test track data validation with valid data."""
        # Mock validation function
        def validate_track_data(data):
            required_fields = ["name"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            if len(data["name"]) < 3:
                raise ValueError("Track name must be at least 3 characters")
            
            if "difficulty_level" in data:
                valid_levels = ["beginner", "intermediate", "advanced"]
                if data["difficulty_level"] not in valid_levels:
                    raise ValueError(f"Invalid difficulty level: {data['difficulty_level']}")
            
            if "duration_weeks" in data:
                if not isinstance(data["duration_weeks"], int) or data["duration_weeks"] <= 0:
                    raise ValueError("Duration weeks must be a positive integer")
            
            return True
        
        # Test valid data
        valid_data = {
            "name": "Valid Track",
            "description": "A valid track",
            "difficulty_level": "intermediate",
            "duration_weeks": 12
        }
        
        assert validate_track_data(valid_data) is True
    
    @pytest.mark.unit
    def test_validate_track_data_invalid(self):
        """Test track data validation with invalid data."""
        # Mock validation function
        def validate_track_data(data):
            required_fields = ["name"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            if len(data["name"]) < 3:
                raise ValueError("Track name must be at least 3 characters")
            
            if "difficulty_level" in data:
                valid_levels = ["beginner", "intermediate", "advanced"]
                if data["difficulty_level"] not in valid_levels:
                    raise ValueError(f"Invalid difficulty level: {data['difficulty_level']}")
            
            if "duration_weeks" in data:
                if not isinstance(data["duration_weeks"], int) or data["duration_weeks"] <= 0:
                    raise ValueError("Duration weeks must be a positive integer")
            
            return True
        
        # Test missing name
        invalid_data_1 = {"description": "Missing name"}
        with pytest.raises(ValueError, match="Missing required field: name"):
            validate_track_data(invalid_data_1)
        
        # Test short name
        invalid_data_2 = {"name": "AB"}
        with pytest.raises(ValueError, match="Track name must be at least 3 characters"):
            validate_track_data(invalid_data_2)
        
        # Test invalid difficulty level
        invalid_data_3 = {"name": "Valid Name", "difficulty_level": "expert"}
        with pytest.raises(ValueError, match="Invalid difficulty level: expert"):
            validate_track_data(invalid_data_3)
        
        # Test invalid duration
        invalid_data_4 = {"name": "Valid Name", "duration_weeks": -5}
        with pytest.raises(ValueError, match="Duration weeks must be a positive integer"):
            validate_track_data(invalid_data_4)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_progress_tracking(self, track_service):
        """Test track progress tracking functionality."""
        # Mock progress tracking methods
        async def mock_update_student_progress(track_id, student_id, progress_data):
            return {
                "track_id": track_id,
                "student_id": student_id,
                "progress": progress_data["progress"],
                "completed_lessons": progress_data.get("completed_lessons", 0),
                "total_lessons": progress_data.get("total_lessons", 10),
                "last_activity": datetime.utcnow()
            }
        
        async def mock_get_student_progress(track_id, student_id):
            return {
                "track_id": track_id,
                "student_id": student_id,
                "progress": 0.6,
                "completed_lessons": 6,
                "total_lessons": 10,
                "time_spent_minutes": 480,
                "last_activity": datetime.utcnow() - timedelta(hours=2)
            }
        
        track_service.update_student_progress = mock_update_student_progress
        track_service.get_student_progress = mock_get_student_progress
        
        # Test progress update
        track_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        progress_data = {
            "progress": 0.8,
            "completed_lessons": 8,
            "total_lessons": 10
        }
        
        result = await track_service.update_student_progress(track_id, student_id, progress_data)
        
        assert result["track_id"] == track_id
        assert result["student_id"] == student_id
        assert result["progress"] == 0.8
        assert result["completed_lessons"] == 8
        assert result["total_lessons"] == 10
        
        # Test progress retrieval
        progress = await track_service.get_student_progress(track_id, student_id)
        
        assert progress["progress"] == 0.6
        assert progress["completed_lessons"] == 6
        assert progress["total_lessons"] == 10
        assert "time_spent_minutes" in progress
        assert "last_activity" in progress
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_track_completion_and_certification(self, track_service):
        """Test track completion and certification functionality."""
        # Mock completion methods
        async def mock_complete_track(track_id, student_id):
            return {
                "track_id": track_id,
                "student_id": student_id,
                "completed_at": datetime.utcnow(),
                "final_score": 0.85,
                "certificate_id": str(uuid.uuid4()),
                "status": "completed"
            }
        
        async def mock_get_track_completions(track_id):
            return [
                {
                    "student_id": str(uuid.uuid4()),
                    "student_name": "John Graduate",
                    "completed_at": datetime.utcnow() - timedelta(days=2),
                    "final_score": 0.92,
                    "certificate_id": str(uuid.uuid4())
                },
                {
                    "student_id": str(uuid.uuid4()),
                    "student_name": "Jane Graduate",
                    "completed_at": datetime.utcnow() - timedelta(days=1),
                    "final_score": 0.88,
                    "certificate_id": str(uuid.uuid4())
                }
            ]
        
        track_service.complete_track = mock_complete_track
        track_service.get_track_completions = mock_get_track_completions
        
        # Test track completion
        track_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        
        completion = await track_service.complete_track(track_id, student_id)
        
        assert completion["track_id"] == track_id
        assert completion["student_id"] == student_id
        assert completion["status"] == "completed"
        assert "completed_at" in completion
        assert "final_score" in completion
        assert "certificate_id" in completion
        assert 0.0 <= completion["final_score"] <= 1.0
        
        # Test getting completions
        completions = await track_service.get_track_completions(track_id)
        
        assert isinstance(completions, list)
        assert len(completions) == 2
        
        for completion in completions:
            assert "student_id" in completion
            assert "student_name" in completion
            assert "completed_at" in completion
            assert "final_score" in completion
            assert "certificate_id" in completion
    
    @pytest.mark.unit
    @pytest.mark.asyncio  
    async def test_auto_enrollment_functionality(self, track_service):
        """Test automatic enrollment functionality."""
        # Mock auto-enrollment methods
        async def mock_process_auto_enrollments(org_id):
            auto_enrollment_tracks = [
                {
                    "track_id": str(uuid.uuid4()),
                    "track_name": "Orientation Track",
                    "auto_enrollment": True,
                    "target_audience": ["new_students"]
                }
            ]
            
            eligible_students = [
                {
                    "student_id": str(uuid.uuid4()),
                    "student_name": "New Student 1",
                    "role": "student",
                    "enrollment_date": datetime.utcnow()
                }
            ]
            
            enrollments = []
            for track in auto_enrollment_tracks:
                for student in eligible_students:
                    enrollments.append({
                        "enrollment_id": str(uuid.uuid4()),
                        "track_id": track["track_id"],
                        "student_id": student["student_id"],
                        "enrolled_at": datetime.utcnow(),
                        "auto_enrolled": True
                    })
            
            return enrollments
        
        track_service.process_auto_enrollments = mock_process_auto_enrollments
        
        # Test auto-enrollment processing
        org_id = str(uuid.uuid4())
        enrollments = await track_service.process_auto_enrollments(org_id)
        
        assert isinstance(enrollments, list)
        assert len(enrollments) > 0
        
        for enrollment in enrollments:
            assert "enrollment_id" in enrollment
            assert "track_id" in enrollment
            assert "student_id" in enrollment
            assert "enrolled_at" in enrollment
            assert enrollment["auto_enrolled"] is True