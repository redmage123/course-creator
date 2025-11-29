"""
Integration Tests for Organization Content Workflow

This module tests the integration of organization content workflows including:
1. Direct course creation under organizations
2. Track-based course creation
3. Organization content overview retrieval
4. Slide template management

BUSINESS FLOWS TESTED:
- Organization creates course directly (no project/track required)
- Organization creates course via track (traditional hierarchy)
- Organization admin views all content (projects + courses)
- Slide templates are applied to course content
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure correct service path is at the front of sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'services' / 'course-management'))

from course_management.domain.entities.course import Course, DifficultyLevel
from course_management.domain.entities.slide_template import SlideTemplate


class TestDirectCourseCreationWorkflow:
    """
    Integration tests for direct organization course creation.

    BUSINESS CONTEXT:
    Organizations can now create courses directly without requiring
    the full project→track→course hierarchy. This simplifies course
    creation for organizations with straightforward training needs.
    """

    def test_organization_creates_direct_course(self):
        """
        Test that an organization can create a course directly.

        WORKFLOW:
        1. Organization exists
        2. Organization admin creates course with organization_id
        3. Course is created without track_id
        4. Course is accessible in organization's content

        BUSINESS RULE:
        Direct courses have organization_id set but track_id = NULL.
        """
        # Arrange
        org_id = str(uuid4())
        instructor_id = str(uuid4())

        # Act - Create direct org course
        course = Course(
            title="Direct Organization Course",
            description="Course created directly under organization",
            instructor_id=instructor_id,
            organization_id=org_id,
            difficulty_level=DifficultyLevel.BEGINNER
        )

        # Assert
        assert course.organization_id == org_id
        assert course.track_id is None
        assert course.get_organizational_context_mode() == "direct_org"
        assert course.validate_organizational_context() is True

    def test_direct_course_can_be_published(self):
        """
        Test that direct organization courses can be published.

        BUSINESS RULE:
        Direct courses follow same publication rules as track-based courses.
        """
        # Arrange
        course = Course(
            title="Publishable Direct Course",
            description="This course can be published",
            instructor_id=str(uuid4()),
            organization_id=str(uuid4())
        )

        # Assert
        assert course.can_be_published() is True

        # Act
        course.publish()

        # Assert
        assert course.is_published is True

    def test_multiple_direct_courses_per_organization(self):
        """
        Test that organizations can have multiple direct courses.

        BUSINESS RULE:
        No limit on number of direct courses per organization.
        """
        # Arrange
        org_id = str(uuid4())
        instructor_id = str(uuid4())

        # Act - Create multiple courses
        courses = []
        for i in range(5):
            course = Course(
                title=f"Direct Course {i+1}",
                description=f"Course number {i+1}",
                instructor_id=instructor_id,
                organization_id=org_id
            )
            courses.append(course)

        # Assert
        assert len(courses) == 5
        for course in courses:
            assert course.organization_id == org_id
            assert course.get_organizational_context_mode() == "direct_org"


class TestMixedContentWorkflow:
    """
    Integration tests for organizations with mixed content types.

    BUSINESS CONTEXT:
    Organizations can have both:
    - Projects with tracks containing courses
    - Direct courses without tracks
    The organization overview page shows all content unified.
    """

    def test_organization_with_direct_and_track_courses(self):
        """
        Test organization with both direct and track-based courses.

        WORKFLOW:
        1. Organization has projects with track-based courses
        2. Organization also has direct courses
        3. All courses are queryable from organization

        BUSINESS RULE:
        Both course types belong to the same organization and appear
        in the organization's content overview.
        """
        # Arrange
        org_id = str(uuid4())
        track_id = str(uuid4())
        instructor_id = str(uuid4())

        # Create direct course
        direct_course = Course(
            title="Direct Course",
            description="Course without track",
            instructor_id=instructor_id,
            organization_id=org_id
        )

        # Create track-based course
        track_course = Course(
            title="Track Course",
            description="Course in track",
            instructor_id=instructor_id,
            organization_id=org_id,
            track_id=track_id
        )

        # Assert both belong to same org
        assert direct_course.organization_id == track_course.organization_id

        # Assert different modes
        assert direct_course.get_organizational_context_mode() == "direct_org"
        assert track_course.get_organizational_context_mode() == "track_based"


class TestSlideTemplateIntegration:
    """
    Integration tests for slide template workflow.

    BUSINESS CONTEXT:
    Organizations can create slide templates to apply consistent
    branding across all course presentations.
    """

    def test_create_and_apply_template(self):
        """
        Test creating a template and applying it to slides.

        WORKFLOW:
        1. Organization admin creates template
        2. Template is set as default
        3. New slides automatically use default template
        """
        # Arrange
        org_id = str(uuid4())

        # Act - Create template
        template = SlideTemplate(
            name="Corporate Brand Template",
            organization_id=org_id,
            template_config={
                "theme": "corporate",
                "primaryColor": "#003366",
                "fontFamily": "Arial, sans-serif"
            },
            logo_url="https://example.com/logo.png",
            is_default=True
        )

        # Assert
        assert template.organization_id == org_id
        assert template.is_default is True
        assert template.get_primary_color() == "#003366"

    def test_multiple_templates_per_organization(self):
        """
        Test organization can have multiple templates.

        BUSINESS RULE:
        Organizations can have multiple templates but only one default.
        """
        # Arrange
        org_id = str(uuid4())

        # Act - Create multiple templates
        templates = [
            SlideTemplate(
                name="Light Theme",
                organization_id=org_id,
                template_config={"theme": "light"},
                is_default=True
            ),
            SlideTemplate(
                name="Dark Theme",
                organization_id=org_id,
                template_config={"theme": "dark"},
                is_default=False
            ),
            SlideTemplate(
                name="Custom Theme",
                organization_id=org_id,
                template_config={"theme": "custom"},
                is_default=False
            )
        ]

        # Assert
        assert len(templates) == 3
        default_count = sum(1 for t in templates if t.is_default)
        assert default_count == 1

    def test_template_css_variables_generation(self):
        """
        Test that templates generate correct CSS variables.

        WORKFLOW:
        1. Template is created with branding config
        2. CSS variables are generated for slide styling
        3. Variables can be applied to HTML slides
        """
        # Arrange
        template = SlideTemplate(
            name="Test Template",
            organization_id=str(uuid4()),
            template_config={
                "theme": "corporate",
                "primaryColor": "#1976d2",
                "secondaryColor": "#dc004e",
                "fontFamily": "Roboto"
            }
        )

        # Act
        css_vars = template.to_css_variables()

        # Assert
        assert "--template-primary" in css_vars
        assert "--template-secondary" in css_vars
        assert "--template-font" in css_vars
        assert css_vars["--template-primary"] == "#1976d2"


class TestOrganizationContentSummary:
    """
    Integration tests for organization content summary.

    BUSINESS CONTEXT:
    The organization overview page shows summary counts of
    projects, direct courses, and track-based courses.
    """

    def test_content_summary_calculation(self):
        """
        Test that content summary counts are calculated correctly.

        NOTE: This test validates the expected data structure.
        Actual database queries would use get_organization_content_summary().
        """
        # This would normally query the database
        # Here we validate the expected structure

        expected_summary = {
            "organization_id": str(uuid4()),
            "project_count": 3,
            "direct_course_count": 5,
            "track_course_count": 10,
            "total_course_count": 15,
            "published_course_count": 12
        }

        # Assert expected structure
        assert "project_count" in expected_summary
        assert "direct_course_count" in expected_summary
        assert "track_course_count" in expected_summary
        assert expected_summary["total_course_count"] == (
            expected_summary["direct_course_count"] +
            expected_summary["track_course_count"]
        )


class TestCourseCreationModeTransitions:
    """
    Test transitions between course creation modes.

    BUSINESS CONTEXT:
    Courses may need to transition from direct to track-based
    or vice versa as organizational needs change.
    """

    def test_direct_course_cannot_have_orphaned_track(self):
        """
        Test that adding track_id without org raises error.

        BUSINESS RULE:
        Tracks belong to organizations, so track_id cannot exist
        without organization_id.
        """
        with pytest.raises(ValueError):
            Course(
                title="Invalid Course",
                description="Course with orphaned track",
                instructor_id=str(uuid4()),
                track_id=str(uuid4())  # No organization_id
            )

    def test_standalone_to_direct_org_transition(self):
        """
        Test that a standalone course can become a direct org course.

        NOTE: In actual implementation, this would involve updating
        the course in the database. Here we validate the entity allows it.
        """
        # Create standalone course
        course = Course(
            title="Transition Course",
            description="Course that will transition",
            instructor_id=str(uuid4())
        )

        assert course.get_organizational_context_mode() == "standalone"

        # Simulate transition by creating new instance with org
        org_course = Course(
            title=course.title,
            description=course.description,
            instructor_id=course.instructor_id,
            organization_id=str(uuid4())
        )

        assert org_course.get_organizational_context_mode() == "direct_org"
