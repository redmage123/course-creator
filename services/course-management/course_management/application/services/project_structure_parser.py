"""
Project Structure Parser Service

This service provides functionality to parse project structures from various
text-based formats (JSON, YAML, plain text) for automated project creation.

BUSINESS CONTEXT:
Organization admins can upload files containing complete project structures
to quickly create projects with subprojects, tracks, courses, and instructor
assignments. This service extracts and normalizes project data from different
file formats into a consistent structure.

SUPPORTED FORMATS:
- JSON: Standard JSON format with nested objects
- YAML: Human-readable YAML format
- Plain Text: Indentation-based hierarchical format

FULL HIERARCHY SUPPORT:
- Projects: Top-level training programs
- Subprojects: Location-based instances (cohorts)
- Tracks: Learning paths within a project
- Courses: Individual courses (within tracks or directly under project)
- Instructors: Assigned instructors with roles

REQUIRED FIELDS:
- organization_id: Organization that owns this project
- project.name: Project display name
- project.slug: URL-friendly identifier
- project.description: Project description

OPTIONAL FIELDS:
- project.subprojects[]: Location instances
- project.tracks[]: Learning tracks with courses
- project.courses[]: Direct courses (no track required)
- project.instructors[]: Assigned instructors

USAGE EXAMPLE:
    parser = ProjectStructureParser()

    # Auto-detect format
    result = parser.parse(file_content)

    # Or specify format
    result = parser.parse(yaml_content, format_type="yaml")

    # Parse from file with filename hint
    result = parser.parse_file(file_bytes, "project.yaml")
"""
import json
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProjectStructureParseException(Exception):
    """
    Base exception for project structure parsing errors.

    All parser exceptions inherit from this class, allowing callers
    to catch all parsing errors with a single except clause.
    """
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidFormatException(ProjectStructureParseException):
    """
    Exception raised when file format is invalid or cannot be parsed.

    CAUSES:
    - Invalid JSON syntax
    - Invalid YAML syntax
    - Unrecognized file format
    - Malformed content structure
    """
    pass


class MissingRequiredFieldException(ProjectStructureParseException):
    """
    Exception raised when required fields are missing.

    REQUIRED FIELDS:
    - organization_id
    - project.name
    - project.slug
    - project.description
    - course.title (for each course)
    - instructor.email (for each instructor)
    """
    pass


class ProjectStructureParser:
    """
    Service for parsing project structures from JSON, YAML, and plain text.

    BUSINESS REQUIREMENTS:
    - Support multiple text formats (JSON, YAML, plain text)
    - Auto-detect format from content or filename
    - Parse full project hierarchy
    - Validate required fields
    - Normalize output structure
    - Provide descriptive error messages

    SUPPORTED HIERARCHY:
    organization_id
    project
      ├── name, slug, description
      ├── subprojects[] (location instances)
      │     └── name, location, start_date, end_date, max_students
      ├── tracks[] (learning paths)
      │     └── name, description, courses[]
      ├── courses[] (direct courses, no track)
      │     └── title, description, difficulty, duration_hours
      └── instructors[]
            └── email, name, role
    """

    # Required fields at each level
    REQUIRED_PROJECT_FIELDS = ['name', 'slug', 'description']
    REQUIRED_COURSE_FIELDS = ['title']
    REQUIRED_INSTRUCTOR_FIELDS = ['email']

    def detect_format(self, content: str) -> str:
        """
        Detect format from content structure.

        DETECTION LOGIC:
        1. If content starts with '{' or '[' -> JSON
        2. If content has 'key: value' pattern without JSON -> YAML
        3. Otherwise -> plain text

        Args:
            content: File content as string

        Returns:
            Format string: 'json', 'yaml', or 'text'
        """
        content = content.strip()

        # Check for JSON (starts with { or [)
        if content.startswith('{') or content.startswith('['):
            return "json"

        # Check for YAML (has key: value pattern at start of line)
        # YAML typically has unquoted keys followed by colon
        yaml_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*\S'
        if re.search(yaml_pattern, content, re.MULTILINE):
            # Additional check: not plain text with "Key: Value" format
            # YAML usually has nested structures with indentation
            if '\n  ' in content or content.count(':') > 2:
                return "yaml"

        return "text"

    def detect_format_from_filename(self, filename: str) -> str:
        """
        Detect format from filename extension.

        Args:
            filename: Original filename with extension

        Returns:
            Format string: 'json', 'yaml', or 'text'
        """
        ext = filename.lower().split('.')[-1]

        if ext == 'json':
            return "json"
        elif ext in ['yaml', 'yml']:
            return "yaml"
        elif ext == 'txt':
            return "text"
        else:
            return "text"  # Default to text

    def parse(self, content: str, format_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse project structure from content.

        BUSINESS LOGIC:
        - Auto-detect format if not specified
        - Route to appropriate parser method
        - Validate required fields
        - Normalize output structure

        Args:
            content: File content as string
            format_type: Optional format hint ('json', 'yaml', 'text')

        Returns:
            Normalized project structure dictionary

        Raises:
            InvalidFormatException: If content cannot be parsed
            MissingRequiredFieldException: If required fields are missing
        """
        if not content or not content.strip():
            raise InvalidFormatException("Empty content provided")

        # Auto-detect format if not specified
        if not format_type:
            format_type = self.detect_format(content)

        # Parse based on format
        if format_type == "json":
            data = self._parse_json(content)
        elif format_type == "yaml":
            data = self._parse_yaml(content)
        elif format_type == "text":
            data = self._parse_text(content)
        else:
            raise InvalidFormatException(f"Unsupported format: {format_type}")

        # Validate and normalize
        self._validate_structure(data)
        normalized = self._normalize_structure(data)

        logger.info(
            f"Parsed project structure: {normalized['project']['name']} with "
            f"{len(normalized['project']['tracks'])} tracks, "
            f"{len(normalized['project']['courses'])} direct courses, "
            f"{len(normalized['project']['subprojects'])} subprojects, "
            f"{len(normalized['project']['instructors'])} instructors"
        )

        return normalized

    def parse_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse project structure from file bytes.

        Args:
            file_content: File content as bytes
            filename: Original filename (used for format detection)

        Returns:
            Normalized project structure dictionary
        """
        # Decode bytes to string
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            content = file_content.decode('latin-1')

        # Use filename for format hint
        format_type = self.detect_format_from_filename(filename)

        return self.parse(content, format_type)

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON content into dictionary.

        Args:
            content: JSON string

        Returns:
            Parsed dictionary

        Raises:
            InvalidFormatException: If JSON is invalid
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise InvalidFormatException(
                f"Invalid JSON format: {str(e)}",
                details={"line": e.lineno, "column": e.colno}
            )

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML content into dictionary.

        Args:
            content: YAML string

        Returns:
            Parsed dictionary

        Raises:
            InvalidFormatException: If YAML is invalid
        """
        try:
            import yaml
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise InvalidFormatException(
                f"Invalid YAML format: {str(e)}",
                details={"error": str(e)}
            )
        except ImportError:
            raise InvalidFormatException(
                "YAML parsing requires PyYAML library. Install with: pip install pyyaml"
            )

    def _parse_text(self, content: str) -> Dict[str, Any]:
        """
        Parse plain text content into dictionary.

        TEXT FORMAT SPECIFICATION:
        - Key: Value pairs at root level
        - Indentation (2 spaces) indicates nesting
        - Lists start with '- ' prefix
        - Case-insensitive keys

        EXAMPLE:
        Organization: org-123
        Project: My Project
        Slug: my-project
        Description: Project description

        Tracks:
          - Name: Track 1
            Courses:
              - Title: Course 1
                Description: Course desc

        Args:
            content: Plain text content

        Returns:
            Parsed dictionary
        """
        result = {
            "organization_id": None,
            "project": {
                "name": None,
                "slug": None,
                "description": None,
                "tracks": [],
                "courses": [],
                "subprojects": [],
                "instructors": []
            }
        }

        lines = content.strip().split('\n')
        current_section = None
        current_list = None
        current_item = None
        current_sublist = None
        current_subitem = None

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            line_content = line.strip()

            # Root level (no indentation)
            if indent == 0:
                if ':' in line_content:
                    key, value = line_content.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key == 'organization':
                        result["organization_id"] = value
                    elif key == 'project':
                        result["project"]["name"] = value
                    elif key == 'slug':
                        result["project"]["slug"] = value
                    elif key == 'description':
                        result["project"]["description"] = value
                    elif key in ['tracks', 'courses', 'subprojects', 'instructors']:
                        current_section = key
                        current_list = result["project"][key]
                        current_item = None

            # List item level (2 spaces or starts with -)
            elif indent == 2 or (line_content.startswith('- ') and indent < 4):
                if line_content.startswith('- '):
                    line_content = line_content[2:].strip()

                if ':' in line_content and current_section:
                    key, value = line_content.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Start new list item
                    if key in ['name', 'title', 'email']:
                        current_item = {}
                        current_list.append(current_item)
                        current_sublist = None

                    if current_item is not None:
                        # Map keys to expected names (normalize spaces to underscores)
                        normalized_key = key.replace(' ', '_')
                        key_map = {
                            'name': 'name',
                            'title': 'title',
                            'email': 'email',
                            'description': 'description',
                            'location': 'location',
                            'start': 'start_date',
                            'start_date': 'start_date',
                            'end': 'end_date',
                            'end_date': 'end_date',
                            'max_students': 'max_students',
                            'difficulty': 'difficulty',
                            'duration': 'duration_hours',
                            'duration_hours': 'duration_hours',
                            'role': 'role'
                        }

                        mapped_key = key_map.get(normalized_key, normalized_key)

                        # Convert numeric values
                        if mapped_key in ['max_students', 'duration_hours']:
                            try:
                                value = int(value)
                            except ValueError:
                                pass

                        current_item[mapped_key] = value

                        # Check if this starts a sublist
                        if key == 'courses':
                            current_item['courses'] = []
                            current_sublist = current_item['courses']

            # Continuation of list item OR sublist level (4+ spaces)
            elif indent >= 4 and current_item:
                if line_content.startswith('- '):
                    line_content = line_content[2:].strip()

                if ':' in line_content:
                    key, value = line_content.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # If no sublist active, this is continuation of current item
                    if current_sublist is None:
                        # Map keys and add to current item
                        normalized_key = key.replace(' ', '_')
                        key_map = {
                            'name': 'name',
                            'title': 'title',
                            'email': 'email',
                            'description': 'description',
                            'location': 'location',
                            'start': 'start_date',
                            'start_date': 'start_date',
                            'end': 'end_date',
                            'end_date': 'end_date',
                            'max_students': 'max_students',
                            'difficulty': 'difficulty',
                            'duration': 'duration_hours',
                            'duration_hours': 'duration_hours',
                            'role': 'role'
                        }
                        mapped_key = key_map.get(normalized_key, normalized_key)

                        # Convert numeric values
                        if mapped_key in ['max_students', 'duration_hours']:
                            try:
                                value = int(value)
                            except ValueError:
                                pass

                        current_item[mapped_key] = value

                        # Check if this starts a sublist
                        if key == 'courses':
                            current_item['courses'] = []
                            current_sublist = current_item['courses']
                        continue

                    # Start new sublist item
                    if key in ['title', 'name'] and current_sublist is not None:
                        current_subitem = {}
                        current_sublist.append(current_subitem)

                    if current_subitem is not None:
                        key_map = {
                            'title': 'title',
                            'description': 'description',
                            'difficulty': 'difficulty',
                            'duration': 'duration_hours',
                            'duration_hours': 'duration_hours'
                        }
                        mapped_key = key_map.get(key, key)

                        if mapped_key == 'duration_hours':
                            try:
                                value = int(value)
                            except ValueError:
                                pass

                        current_subitem[mapped_key] = value

        return result

    def _validate_structure(self, data: Dict[str, Any]) -> None:
        """
        Validate required fields are present.

        Args:
            data: Parsed data dictionary

        Raises:
            MissingRequiredFieldException: If required fields are missing
        """
        # Check organization_id
        if not data.get('organization_id'):
            raise MissingRequiredFieldException(
                "Missing required field: organization_id",
                details={"field": "organization_id"}
            )

        # Check project exists
        project = data.get('project', {})
        if not project:
            raise MissingRequiredFieldException(
                "Missing required field: project",
                details={"field": "project"}
            )

        # Check required project fields
        for field in self.REQUIRED_PROJECT_FIELDS:
            if not project.get(field):
                raise MissingRequiredFieldException(
                    f"Missing required project field: {field}",
                    details={"field": f"project.{field}"}
                )

        # Validate courses have titles
        for i, course in enumerate(project.get('courses', [])):
            if not course.get('title'):
                raise MissingRequiredFieldException(
                    f"Missing required field: title for course at index {i}",
                    details={"field": f"project.courses[{i}].title"}
                )

        # Validate track courses have titles
        for t_idx, track in enumerate(project.get('tracks', [])):
            for c_idx, course in enumerate(track.get('courses', [])):
                if not course.get('title'):
                    raise MissingRequiredFieldException(
                        f"Missing required field: title for course in track '{track.get('name', t_idx)}'",
                        details={"field": f"project.tracks[{t_idx}].courses[{c_idx}].title"}
                    )

        # Validate instructors have emails
        for i, instructor in enumerate(project.get('instructors', [])):
            if not instructor.get('email'):
                raise MissingRequiredFieldException(
                    f"Missing required field: email for instructor at index {i}",
                    details={"field": f"project.instructors[{i}].email"}
                )

    def _normalize_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parsed data into consistent output structure.

        Ensures all optional fields exist as empty lists if not provided.

        Args:
            data: Validated data dictionary

        Returns:
            Normalized dictionary with consistent structure
        """
        project = data.get('project', {})

        # Ensure all list fields exist
        normalized_project = {
            'name': project.get('name'),
            'slug': project.get('slug'),
            'description': project.get('description'),
            'tracks': project.get('tracks', []),
            'courses': project.get('courses', []),
            'subprojects': project.get('subprojects', []),
            'instructors': project.get('instructors', [])
        }

        # Normalize tracks - ensure courses list exists
        for track in normalized_project['tracks']:
            if 'courses' not in track:
                track['courses'] = []

        # Add default description to courses if missing
        for course in normalized_project['courses']:
            if 'description' not in course:
                course['description'] = ''

        for track in normalized_project['tracks']:
            for course in track.get('courses', []):
                if 'description' not in course:
                    course['description'] = ''

        return {
            'organization_id': data.get('organization_id'),
            'project': normalized_project
        }

    @staticmethod
    def generate_template(format_type: str = "yaml") -> str:
        """
        Generate a template file for project structure import.

        Args:
            format_type: Output format ('json', 'yaml', 'text')

        Returns:
            Template content as string
        """
        if format_type == "json":
            return '''{
  "organization_id": "YOUR_ORGANIZATION_ID",
  "project": {
    "name": "Project Name",
    "slug": "project-slug",
    "description": "Project description",

    "subprojects": [
      {
        "name": "Q1 2024 Cohort",
        "location": "Main Campus",
        "start_date": "2024-01-15",
        "end_date": "2024-03-31",
        "max_students": 25
      }
    ],

    "tracks": [
      {
        "name": "Track Name",
        "description": "Track description",
        "courses": [
          {
            "title": "Course Title",
            "description": "Course description",
            "difficulty": "beginner",
            "duration_hours": 40
          }
        ]
      }
    ],

    "courses": [
      {
        "title": "Direct Course (no track)",
        "description": "Course description"
      }
    ],

    "instructors": [
      {
        "email": "instructor@example.com",
        "name": "Instructor Name",
        "role": "lead"
      }
    ]
  }
}'''

        elif format_type == "yaml":
            return '''# Project Structure Import Template
# Organization ID is required - get from organization settings

organization_id: YOUR_ORGANIZATION_ID

project:
  name: Project Name
  slug: project-slug
  description: Project description

  # Subprojects are location-based instances (optional)
  subprojects:
    - name: Q1 2024 Cohort
      location: Main Campus
      start_date: 2024-01-15
      end_date: 2024-03-31
      max_students: 25

  # Tracks contain courses (optional)
  tracks:
    - name: Track Name
      description: Track description
      courses:
        - title: Course Title
          description: Course description
          difficulty: beginner  # beginner, intermediate, advanced
          duration_hours: 40

  # Direct courses without tracks (optional)
  courses:
    - title: Direct Course
      description: Course not in a track

  # Instructor assignments (optional)
  instructors:
    - email: instructor@example.com
      name: Instructor Name
      role: lead  # lead, assistant, etc.
'''

        else:  # text format
            return '''# Project Structure Import Template
# Lines starting with # are comments

Organization: YOUR_ORGANIZATION_ID
Project: Project Name
Slug: project-slug
Description: Project description

Subprojects:
  - Name: Q1 2024 Cohort
    Location: Main Campus
    Start: 2024-01-15
    End: 2024-03-31
    Max Students: 25

Tracks:
  - Name: Track Name
    Description: Track description
    Courses:
      - Title: Course Title
        Description: Course description
        Difficulty: beginner
        Duration: 40

Courses:
  - Title: Direct Course
    Description: Course not in a track

Instructors:
  - Email: instructor@example.com
    Name: Instructor Name
    Role: lead
'''
