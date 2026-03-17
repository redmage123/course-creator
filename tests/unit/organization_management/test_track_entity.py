"""
Unit Tests for Track Domain Entity

BUSINESS REQUIREMENT:
Validates track entity business logic for learning path management including
sequential and milestone-based tracks, enrollment controls, and progression tracking.

TECHNICAL IMPLEMENTATION:
Tests domain entity validation, status transitions, business rules, and
learning path organization within the organization management system.
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'organization-management'))

from organization_management.domain.entities.track import Track, TrackStatus, TrackType


class TestTrackEntity:
    """Test Track domain entity business logic"""
    
    def test_track_creation_with_defaults(self):
        """Test track creation with minimal required fields"""
        project_id = uuid4()
        track = Track(
            project_id=project_id,
            name="App Developer Track",
            slug="app-dev-track"
        )
        
        assert track.project_id == project_id
        assert track.name == "App Developer Track"
        assert track.slug == "app-dev-track"
        assert track.id is not None
        assert isinstance(track.id, UUID)
        assert track.track_type == TrackType.SEQUENTIAL
        assert track.status == TrackStatus.DRAFT
        assert track.target_audience == []
        assert track.prerequisites == []
        assert track.learning_objectives == []
        assert track.skills_taught == []
        assert track.difficulty_level == "beginner"
        assert track.sequence_order == 0
        assert track.auto_enroll_enabled is True
        assert track.settings == {}
        assert track.created_at is not None
        assert track.updated_at is not None
    
    def test_track_creation_with_full_data(self):
        """Test track creation with all fields"""
        project_id = uuid4()
        created_by = uuid4()
        target_audience = ["Application Developer", "Full-Stack Developer"]
        prerequisites = ["Basic Programming", "Git Knowledge"]
        learning_objectives = ["Learn React", "Master Node.js"]
        skills_taught = ["React", "Node.js", "Docker"]
        settings = {"notifications": True, "difficulty_adjustment": "adaptive"}
        
        track = Track(
            project_id=project_id,
            name="Advanced App Developer Track",
            slug="advanced-app-dev",
            description="Advanced full-stack development training",
            track_type=TrackType.MILESTONE_BASED,
            target_audience=target_audience,
            prerequisites=prerequisites,
            duration_weeks=16,
            max_enrolled=50,
            learning_objectives=learning_objectives,
            skills_taught=skills_taught,
            difficulty_level="advanced",
            sequence_order=2,
            auto_enroll_enabled=False,
            status=TrackStatus.ACTIVE,
            settings=settings,
            created_by=created_by
        )
        
        assert track.project_id == project_id
        assert track.name == "Advanced App Developer Track"
        assert track.slug == "advanced-app-dev"
        assert track.description == "Advanced full-stack development training"
        assert track.track_type == TrackType.MILESTONE_BASED
        assert track.target_audience == target_audience
        assert track.prerequisites == prerequisites
        assert track.duration_weeks == 16
        assert track.max_enrolled == 50
        assert track.learning_objectives == learning_objectives
        assert track.skills_taught == skills_taught
        assert track.difficulty_level == "advanced"
        assert track.sequence_order == 2
        assert track.auto_enroll_enabled is False
        assert track.status == TrackStatus.ACTIVE
        assert track.settings == settings
        assert track.created_by == created_by
    
    def test_track_update_info(self):
        """Test track information update"""
        track = Track(
            project_id=uuid4(),
            name="Original Track",
            slug="original-track"
        )
        original_updated_at = track.updated_at
        
        # Wait a moment to ensure updated_at changes
        import time
        time.sleep(0.01)
        
        new_objectives = ["New Objective 1", "New Objective 2"]
        new_skills = ["Python", "Django"]
        track.update_info(
            name="Updated Track",
            description="Updated description",
            duration_weeks=12,
            learning_objectives=new_objectives,
            skills_taught=new_skills,
            difficulty_level="intermediate"
        )
        
        assert track.name == "Updated Track"
        assert track.description == "Updated description"
        assert track.duration_weeks == 12
        assert track.learning_objectives == new_objectives
        assert track.skills_taught == new_skills
        assert track.difficulty_level == "intermediate"
        assert track.updated_at > original_updated_at
    
    def test_track_activation(self):
        """Test track activation business logic"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track"
        )
        
        assert track.status == TrackStatus.DRAFT
        assert track.can_activate() is True  # Valid track can be activated
        
        track.activate()
        
        assert track.status == TrackStatus.ACTIVE
        assert track.is_active() is True
        assert track.can_enroll_students() is True
    
    def test_track_completion(self):
        """Test track completion logic"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track",
            status=TrackStatus.ACTIVE
        )
        
        track.complete()
        
        assert track.status == TrackStatus.COMPLETED
        assert track.is_active() is False
        assert track.can_enroll_students() is False
    
    def test_track_archival(self):
        """Test track archival"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track",
            status=TrackStatus.ACTIVE
        )
        
        track.archive()
        
        assert track.status == TrackStatus.ARCHIVED
        assert track.is_active() is False
        assert track.can_enroll_students() is False
    
    def test_track_slug_validation(self):
        """Test slug format validation"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="valid-slug-123"
        )
        
        assert track.validate_slug() is True
        
        # Test invalid slugs
        track.slug = "Invalid Slug"  # Spaces not allowed
        assert track.validate_slug() is False
        
        track.slug = "invalid_slug"  # Underscores not allowed
        assert track.validate_slug() is False
        
        track.slug = "Invalid-Slug"  # Capital letters not allowed
        assert track.validate_slug() is False
    
    def test_track_duration_validation(self):
        """Test duration constraints validation"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track"
        )
        
        # Valid durations
        track.duration_weeks = 1
        assert track.validate_duration() is True
        
        track.duration_weeks = 26
        assert track.validate_duration() is True
        
        track.duration_weeks = 52
        assert track.validate_duration() is True
        
        # Invalid durations
        track.duration_weeks = 0
        assert track.validate_duration() is False
        
        track.duration_weeks = 53
        assert track.validate_duration() is False
        
        track.duration_weeks = None
        assert track.validate_duration() is True  # None is valid (no duration specified)
    
    def test_track_enrollment_limit_validation(self):
        """Test max enrollment validation"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track"
        )
        
        # Valid enrollment limits
        track.max_enrolled = 1
        assert track.validate_enrollment_limit() is True
        
        track.max_enrolled = 100
        assert track.validate_enrollment_limit() is True
        
        track.max_enrolled = None
        assert track.validate_enrollment_limit() is True  # None is valid (no limit)
        
        # Invalid enrollment limits
        track.max_enrolled = 0
        assert track.validate_enrollment_limit() is False
        
        track.max_enrolled = -1
        assert track.validate_enrollment_limit() is False
    
    def test_track_difficulty_validation(self):
        """Test difficulty level validation"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track"
        )
        
        # Valid difficulty levels
        track.difficulty_level = "beginner"
        assert track.validate_difficulty_level() is True
        
        track.difficulty_level = "intermediate"
        assert track.validate_difficulty_level() is True
        
        track.difficulty_level = "advanced"
        assert track.validate_difficulty_level() is True
        
        # Invalid difficulty level
        track.difficulty_level = "expert"
        assert track.validate_difficulty_level() is False
    
    def test_track_validation_complete(self):
        """Test complete track validation"""
        # Valid track
        track = Track(
            project_id=uuid4(),
            name="Valid Track",
            slug="valid-track",
            duration_weeks=12,
            max_enrolled=50,
            difficulty_level="intermediate"
        )
        
        assert track.is_valid() is True
        
        # Invalid track - empty name
        track.name = ""
        assert track.is_valid() is False
        
        track.name = "Valid Track"  # Fix name
        
        # Invalid track - empty slug
        track.slug = ""
        assert track.is_valid() is False
        
        track.slug = "valid-track"  # Fix slug
        
        # Invalid track - bad slug format
        track.slug = "Invalid Slug"
        assert track.is_valid() is False
    
    def test_track_can_activate_logic(self):
        """Test track activation eligibility"""
        # Valid draft track can be activated
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track"
        )
        
        assert track.can_activate() is True
        
        # Active track cannot be activated again
        track.status = TrackStatus.ACTIVE
        assert track.can_activate() is False
        
        # Invalid track cannot be activated
        track.status = TrackStatus.DRAFT
        track.name = ""  # Make invalid
        assert track.can_activate() is False
    
    def test_track_enrollment_eligibility(self):
        """Test student enrollment eligibility"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track",
            status=TrackStatus.ACTIVE,
            auto_enroll_enabled=True
        )
        
        assert track.can_enroll_students() is True
        
        # Inactive track cannot enroll students
        track.status = TrackStatus.DRAFT
        assert track.can_enroll_students() is False
        
        track.status = TrackStatus.ACTIVE
        
        # Track with auto-enrollment disabled cannot auto-enroll
        track.auto_enroll_enabled = False
        assert track.can_enroll_students() is False
    
    def test_track_display_methods(self):
        """Test display formatting methods"""
        track = Track(
            project_id=uuid4(),
            name="Test Track",
            slug="test-track",
            target_audience=["Developer", "Analyst"],
            skills_taught=["Python", "SQL", "Docker"],
            duration_weeks=12,
            difficulty_level="intermediate"
        )
        
        # Test target audience display
        assert track.get_target_audience_display() == "Developer, Analyst"
        
        track.target_audience = []
        assert track.get_target_audience_display() == "General"
        
        # Test skills display
        track.skills_taught = ["Python", "SQL", "Docker"]
        assert track.get_skills_display() == "Python, SQL, Docker"
        
        track.skills_taught = []
        assert track.get_skills_display() == "Various Skills"
        
        # Test completion time estimation
        track.duration_weeks = 1
        track.difficulty_level = "beginner"
        completion_time = track.estimate_completion_time()
        assert "week" in completion_time  # Should mention weeks
        
        track.duration_weeks = 8
        track.difficulty_level = "advanced"
        completion_time = track.estimate_completion_time()
        assert "month" in completion_time or "week" in completion_time
        
        track.duration_weeks = None
        assert track.estimate_completion_time() == "Variable"


if __name__ == "__main__":
    pytest.main([__file__])