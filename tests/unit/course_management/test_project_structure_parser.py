"""
Unit Tests for Project Structure Parser

Tests parsing of project structures from plain text, JSON, and YAML formats.
Supports full organizational hierarchy:
- Projects
- Subprojects (locations)
- Tracks
- Courses
- Instructors

TDD: Tests written BEFORE implementation.
"""
import pytest
from uuid import uuid4

# Ensure correct service path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.application.services.project_structure_parser import (
    ProjectStructureParser,
    ProjectStructureParseException,
    InvalidFormatException,
    MissingRequiredFieldException
)


class TestFormatDetection:
    """Test automatic format detection from content and filename."""

    def test_detect_json_from_content(self):
        """JSON content should be detected by opening brace."""
        parser = ProjectStructureParser()
        content = '{"project": "Test"}'
        assert parser.detect_format(content) == "json"

    def test_detect_yaml_from_content(self):
        """YAML content should be detected by key: value pattern."""
        parser = ProjectStructureParser()
        content = "project:\n  name: Test Project"
        assert parser.detect_format(content) == "yaml"

    def test_detect_text_from_content(self):
        """Plain text content - explicitly use text format for ambiguous cases."""
        parser = ProjectStructureParser()
        # Note: Plain text with "Key: Value" format is ambiguous with YAML
        # For auto-detection, YAML wins. Use filename hint for .txt files.
        content = "Organization: org-123\nProject: Test"
        # This will detect as YAML due to key: value pattern
        # That's expected - use filename hint for .txt files
        assert parser.detect_format(content) in ["yaml", "text"]

    def test_detect_format_from_filename_json(self):
        """Filename with .json extension."""
        parser = ProjectStructureParser()
        assert parser.detect_format_from_filename("project.json") == "json"

    def test_detect_format_from_filename_yaml(self):
        """Filename with .yaml or .yml extension."""
        parser = ProjectStructureParser()
        assert parser.detect_format_from_filename("project.yaml") == "yaml"
        assert parser.detect_format_from_filename("project.yml") == "yaml"

    def test_detect_format_from_filename_text(self):
        """Filename with .txt extension."""
        parser = ProjectStructureParser()
        assert parser.detect_format_from_filename("project.txt") == "text"


class TestJSONParsing:
    """Test parsing project structure from JSON format."""

    def test_parse_minimal_json(self):
        """Parse JSON with only required fields."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Python Training",
                "slug": "python-training",
                "description": "Learn Python programming"
            }
        }'''

        result = parser.parse(json_content, format_type="json")

        assert result["organization_id"] == "org-123"
        assert result["project"]["name"] == "Python Training"
        assert result["project"]["slug"] == "python-training"

    def test_parse_json_with_tracks(self):
        """Parse JSON with tracks containing courses."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Python Training",
                "slug": "python-training",
                "description": "Learn Python",
                "tracks": [
                    {
                        "name": "Fundamentals",
                        "courses": [
                            {"title": "Python Basics", "description": "Intro to Python"},
                            {"title": "Data Types", "description": "Learn data types"}
                        ]
                    }
                ]
            }
        }'''

        result = parser.parse(json_content, format_type="json")

        assert len(result["project"]["tracks"]) == 1
        assert result["project"]["tracks"][0]["name"] == "Fundamentals"
        assert len(result["project"]["tracks"][0]["courses"]) == 2

    def test_parse_json_with_subprojects(self):
        """Parse JSON with subprojects (locations)."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Global Training",
                "slug": "global-training",
                "description": "Multi-location training",
                "subprojects": [
                    {
                        "name": "New York",
                        "location": "NYC Office",
                        "start_date": "2024-01-15",
                        "end_date": "2024-06-30",
                        "max_students": 25
                    },
                    {
                        "name": "London",
                        "location": "UK Office",
                        "start_date": "2024-02-01"
                    }
                ]
            }
        }'''

        result = parser.parse(json_content, format_type="json")

        assert len(result["project"]["subprojects"]) == 2
        assert result["project"]["subprojects"][0]["name"] == "New York"
        assert result["project"]["subprojects"][0]["max_students"] == 25

    def test_parse_json_with_instructors(self):
        """Parse JSON with instructor assignments."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Python Training",
                "slug": "python-training",
                "description": "Learn Python",
                "instructors": [
                    {"email": "john@example.com", "name": "John Doe", "role": "lead"},
                    {"email": "jane@example.com", "name": "Jane Smith"}
                ]
            }
        }'''

        result = parser.parse(json_content, format_type="json")

        assert len(result["project"]["instructors"]) == 2
        assert result["project"]["instructors"][0]["email"] == "john@example.com"
        assert result["project"]["instructors"][0]["role"] == "lead"

    def test_parse_json_with_direct_courses(self):
        """Parse JSON with direct courses (no track required)."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Quick Start",
                "slug": "quick-start",
                "description": "Quick training",
                "courses": [
                    {"title": "Intro Course", "description": "Quick intro"}
                ]
            }
        }'''

        result = parser.parse(json_content, format_type="json")

        assert len(result["project"]["courses"]) == 1
        assert result["project"]["courses"][0]["title"] == "Intro Course"

    def test_parse_json_missing_organization_raises_error(self):
        """Missing organization_id should raise error."""
        parser = ProjectStructureParser()
        json_content = '''{
            "project": {
                "name": "Test",
                "slug": "test",
                "description": "Test"
            }
        }'''

        with pytest.raises(MissingRequiredFieldException) as exc_info:
            parser.parse(json_content, format_type="json")

        assert "organization_id" in str(exc_info.value)

    def test_parse_invalid_json_raises_error(self):
        """Invalid JSON syntax should raise error."""
        parser = ProjectStructureParser()
        json_content = '{"project": invalid}'

        with pytest.raises(InvalidFormatException):
            parser.parse(json_content, format_type="json")


class TestYAMLParsing:
    """Test parsing project structure from YAML format."""

    def test_parse_minimal_yaml(self):
        """Parse YAML with only required fields."""
        parser = ProjectStructureParser()
        yaml_content = """
organization_id: org-123
project:
  name: Python Training
  slug: python-training
  description: Learn Python programming
"""

        result = parser.parse(yaml_content, format_type="yaml")

        assert result["organization_id"] == "org-123"
        assert result["project"]["name"] == "Python Training"

    def test_parse_yaml_with_full_hierarchy(self):
        """Parse YAML with complete project hierarchy."""
        parser = ProjectStructureParser()
        yaml_content = """
organization_id: org-123
project:
  name: Full Stack Development
  slug: full-stack-dev
  description: Complete web development training

  subprojects:
    - name: Q1 2024 Cohort
      location: Main Campus
      start_date: 2024-01-15
      end_date: 2024-03-31
      max_students: 30

    - name: Q2 2024 Cohort
      location: Online
      start_date: 2024-04-01

  tracks:
    - name: Backend Development
      description: Server-side programming
      courses:
        - title: Python Fundamentals
          description: Core Python concepts
          difficulty: beginner
          duration_hours: 40

        - title: Django Framework
          description: Web framework
          difficulty: intermediate

    - name: Frontend Development
      courses:
        - title: HTML & CSS
          description: Web basics
        - title: JavaScript
          description: Browser scripting

  instructors:
    - email: lead@example.com
      name: Lead Instructor
      role: lead
    - email: assistant@example.com
      name: Assistant
"""

        result = parser.parse(yaml_content, format_type="yaml")

        assert result["project"]["name"] == "Full Stack Development"
        assert len(result["project"]["subprojects"]) == 2
        assert len(result["project"]["tracks"]) == 2
        assert len(result["project"]["tracks"][0]["courses"]) == 2
        assert result["project"]["tracks"][0]["courses"][0]["difficulty"] == "beginner"
        assert len(result["project"]["instructors"]) == 2

    def test_parse_invalid_yaml_raises_error(self):
        """Invalid YAML syntax should raise error."""
        parser = ProjectStructureParser()
        yaml_content = """
organization_id: org-123
project:
  name: Test
  invalid yaml here:
    - broken
  : missing key
"""

        with pytest.raises(InvalidFormatException):
            parser.parse(yaml_content, format_type="yaml")


class TestPlainTextParsing:
    """Test parsing project structure from plain text format."""

    def test_parse_minimal_text(self):
        """Parse plain text with minimal structure."""
        parser = ProjectStructureParser()
        text_content = """
Organization: org-123
Project: Python Training
Slug: python-training
Description: Learn Python programming
"""

        result = parser.parse(text_content, format_type="text")

        assert result["organization_id"] == "org-123"
        assert result["project"]["name"] == "Python Training"
        assert result["project"]["slug"] == "python-training"

    def test_parse_text_with_indented_hierarchy(self):
        """Parse plain text with indentation-based hierarchy."""
        parser = ProjectStructureParser()
        text_content = """
Organization: org-123
Project: Web Development Training
Slug: web-dev
Description: Full stack web development

Subprojects:
  - Name: Spring 2024
    Location: Main Campus
    Start: 2024-01-15
    End: 2024-05-30
    Max Students: 25

Tracks:
  - Name: Backend
    Description: Server-side development
    Courses:
      - Title: Python Basics
        Description: Introduction to Python
        Difficulty: beginner
      - Title: APIs with Flask
        Description: Building REST APIs

  - Name: Frontend
    Courses:
      - Title: HTML/CSS
        Description: Web fundamentals
      - Title: React
        Description: Modern frontend

Instructors:
  - Email: john@example.com
    Name: John Doe
    Role: lead
  - Email: jane@example.com
    Name: Jane Smith
"""

        result = parser.parse(text_content, format_type="text")

        assert result["project"]["name"] == "Web Development Training"
        assert len(result["project"]["subprojects"]) == 1
        assert result["project"]["subprojects"][0]["max_students"] == 25
        assert len(result["project"]["tracks"]) == 2
        assert len(result["project"]["tracks"][0]["courses"]) == 2
        assert len(result["project"]["instructors"]) == 2

    def test_parse_text_case_insensitive_keys(self):
        """Keys should be case-insensitive."""
        parser = ProjectStructureParser()
        text_content = """
ORGANIZATION: org-123
PROJECT: Test Project
SLUG: test
DESCRIPTION: Test description
"""

        result = parser.parse(text_content, format_type="text")

        assert result["organization_id"] == "org-123"
        assert result["project"]["name"] == "Test Project"


class TestFullStructureValidation:
    """Test validation of complete project structures."""

    def test_validate_required_project_fields(self):
        """Project must have name, slug, description."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Test"
            }
        }'''

        with pytest.raises(MissingRequiredFieldException) as exc_info:
            parser.parse(json_content, format_type="json")

        assert "slug" in str(exc_info.value) or "description" in str(exc_info.value)

    def test_validate_course_has_title(self):
        """Courses must have a title."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Test",
                "slug": "test",
                "description": "Test",
                "courses": [
                    {"description": "Missing title"}
                ]
            }
        }'''

        with pytest.raises(MissingRequiredFieldException) as exc_info:
            parser.parse(json_content, format_type="json")

        assert "title" in str(exc_info.value)

    def test_validate_instructor_has_email(self):
        """Instructors must have an email."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Test",
                "slug": "test",
                "description": "Test",
                "instructors": [
                    {"name": "Missing Email"}
                ]
            }
        }'''

        with pytest.raises(MissingRequiredFieldException) as exc_info:
            parser.parse(json_content, format_type="json")

        assert "email" in str(exc_info.value)


class TestAutoDetectAndParse:
    """Test automatic format detection and parsing."""

    def test_parse_auto_detects_json(self):
        """Auto-detect and parse JSON content."""
        parser = ProjectStructureParser()
        content = '{"organization_id": "org-123", "project": {"name": "Test", "slug": "test", "description": "Test"}}'

        result = parser.parse(content)  # No format specified

        assert result["project"]["name"] == "Test"

    def test_parse_auto_detects_yaml(self):
        """Auto-detect and parse YAML content."""
        parser = ProjectStructureParser()
        content = """
organization_id: org-123
project:
  name: Test
  slug: test
  description: Test
"""

        result = parser.parse(content)  # No format specified

        assert result["project"]["name"] == "Test"

    def test_parse_file_with_filename_hint(self):
        """Use filename extension as format hint."""
        parser = ProjectStructureParser()
        content = '{"organization_id": "org-123", "project": {"name": "Test", "slug": "test", "description": "Test"}}'

        result = parser.parse_file(content.encode(), "project.json")

        assert result["project"]["name"] == "Test"


class TestOutputNormalization:
    """Test that output is normalized regardless of input format."""

    def test_output_structure_from_json(self):
        """JSON output has consistent structure."""
        parser = ProjectStructureParser()
        json_content = '''{
            "organization_id": "org-123",
            "project": {
                "name": "Test",
                "slug": "test",
                "description": "Test"
            }
        }'''

        result = parser.parse(json_content, format_type="json")

        # Verify normalized structure
        assert "organization_id" in result
        assert "project" in result
        assert "tracks" in result["project"]  # Empty list by default
        assert "courses" in result["project"]  # Empty list by default
        assert "subprojects" in result["project"]  # Empty list by default
        assert "instructors" in result["project"]  # Empty list by default

    def test_output_structure_from_yaml(self):
        """YAML output has same structure as JSON."""
        parser = ProjectStructureParser()
        yaml_content = """
organization_id: org-123
project:
  name: Test
  slug: test
  description: Test
"""

        result = parser.parse(yaml_content, format_type="yaml")

        # Same normalized structure
        assert "organization_id" in result
        assert "project" in result
        assert "tracks" in result["project"]
        assert "courses" in result["project"]
        assert "subprojects" in result["project"]
        assert "instructors" in result["project"]
