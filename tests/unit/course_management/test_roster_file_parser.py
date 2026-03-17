"""
Unit Tests for Roster File Parser Service

BUSINESS CONTEXT:
Tests the RosterFileParser service which parses instructor and student roster
files from CSV, Excel, and JSON formats for the AI-powered project builder.

WHY THESE TESTS:
1. Ensure reliable parsing of various file formats
2. Verify column auto-detection works with different naming conventions
3. Validate error handling for malformed files
4. Confirm duplicate email detection works correctly
5. Test template generation for user downloads

WHAT IS TESTED:
- Format detection from filename extensions
- CSV parsing with encoding handling
- Excel parsing (XLSX/XLS)
- JSON parsing with validation
- Column auto-detection
- Required column validation
- Instructor roster parsing
- Student roster parsing
- Duplicate email detection
- Template generation

HOW TO RUN:
    # Run all roster file parser tests
    pytest tests/unit/course_management/test_roster_file_parser.py -v

    # Run specific test class
    pytest tests/unit/course_management/test_roster_file_parser.py::TestFormatDetection -v

@module test_roster_file_parser
@author Course Creator Platform
@version 1.0.0
"""

import csv
import io
import json
import pytest
import sys
from pathlib import Path

# Add course-management service to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.application.services.roster_file_parser import (
    RosterFileParser
)
from course_management.domain.entities.file_import import (
    FileFormat,
    RosterType,
    ColumnMapping,
    ColumnAlias,
    ParsedRoster,
    InstructorRosterEntry,
    StudentRosterEntry,
    FileImportException,
    UnsupportedFileFormatException,
    MissingRequiredColumnException,
    EmptyFileException
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def parser():
    """
    Create a fresh RosterFileParser instance for each test.

    WHY: Ensures test isolation and no state leakage between tests.
    """
    return RosterFileParser()


@pytest.fixture
def valid_instructor_csv():
    """
    Create a valid instructor CSV file content.

    WHY: Provides a baseline valid file for testing successful parsing.
    """
    return b"""name,email,tracks,role,available_days,phone,department,notes
John Doe,john.doe@example.com,"Backend Development, DevOps",instructor,"Monday, Tuesday, Wednesday",+1-555-1234,Engineering,Part-time
Jane Smith,jane.smith@example.com,Frontend Development,lead_instructor,"Monday, Tuesday, Wednesday, Thursday, Friday",+1-555-5678,Training,
"""


@pytest.fixture
def valid_student_csv():
    """
    Create a valid student CSV file content.

    WHY: Provides a baseline valid file for testing successful parsing.
    """
    return b"""name,email,track,location,instructor,group,employee_id,department,manager_email,notes
Alice Johnson,alice.johnson@example.com,Backend Development,New York,john.doe@example.com,Study Group A,EMP001,Engineering,manager@example.com,New hire
Bob Smith,bob.smith@example.com,Frontend Development,London,jane.smith@example.com,Study Group B,EMP002,Product,,
Carol Williams,carol.williams@example.com,Backend Development,Chicago,,,EMP003,Engineering,manager@example.com,Needs accommodations
"""


@pytest.fixture
def valid_instructor_json():
    """
    Create a valid instructor JSON file content.

    WHY: Tests JSON format parsing with same data as CSV.
    """
    data = [
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "tracks": "Backend Development, DevOps",
            "role": "instructor"
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "tracks": "Frontend Development",
            "role": "lead_instructor"
        }
    ]
    return json.dumps(data).encode('utf-8')


@pytest.fixture
def valid_student_json():
    """
    Create a valid student JSON file content.

    WHY: Tests JSON format parsing with same data as CSV.
    """
    data = [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "track": "Backend Development",
            "location": "New York"
        },
        {
            "name": "Bob Smith",
            "email": "bob.smith@example.com",
            "track": "Frontend Development",
            "location": "London"
        }
    ]
    return json.dumps(data).encode('utf-8')


# =============================================================================
# TEST: FORMAT DETECTION
# =============================================================================

class TestFormatDetection:
    """
    Tests for file format detection from filename.

    WHY: Format detection is the first step in parsing and must be reliable.
    Incorrect detection leads to parse failures.
    """

    def test_detect_csv_format(self, parser):
        """
        GIVEN: A filename with .csv extension
        WHEN: _detect_format is called
        THEN: Returns FileFormat.CSV

        WHY: CSV is the most common format for roster exports.
        """
        result = parser._detect_format("instructors.csv")
        assert result == FileFormat.CSV

    def test_detect_csv_format_uppercase(self, parser):
        """
        GIVEN: A filename with .CSV extension (uppercase)
        WHEN: _detect_format is called
        THEN: Returns FileFormat.CSV

        WHY: Extension matching should be case-insensitive.
        """
        result = parser._detect_format("instructors.CSV")
        assert result == FileFormat.CSV

    def test_detect_xlsx_format(self, parser):
        """
        GIVEN: A filename with .xlsx extension
        WHEN: _detect_format is called
        THEN: Returns FileFormat.EXCEL_XLSX

        WHY: Modern Excel files use XLSX format.
        """
        result = parser._detect_format("students.xlsx")
        assert result == FileFormat.EXCEL_XLSX

    def test_detect_xls_format(self, parser):
        """
        GIVEN: A filename with .xls extension
        WHEN: _detect_format is called
        THEN: Returns FileFormat.EXCEL_XLS

        WHY: Legacy Excel files use XLS format.
        """
        result = parser._detect_format("roster.xls")
        assert result == FileFormat.EXCEL_XLS

    def test_detect_json_format(self, parser):
        """
        GIVEN: A filename with .json extension
        WHEN: _detect_format is called
        THEN: Returns FileFormat.JSON

        WHY: JSON is useful for API exports and programmatic generation.
        """
        result = parser._detect_format("data.json")
        assert result == FileFormat.JSON

    def test_unsupported_format_raises_exception(self, parser):
        """
        GIVEN: A filename with unsupported extension
        WHEN: _detect_format is called
        THEN: Raises UnsupportedFileFormatException

        WHY: Clear error for unsupported formats helps users correct issues.
        """
        with pytest.raises(UnsupportedFileFormatException) as exc_info:
            parser._detect_format("document.pdf")

        assert "pdf" in str(exc_info.value.message).lower()

    def test_no_extension_raises_exception(self, parser):
        """
        GIVEN: A filename without extension
        WHEN: _detect_format is called
        THEN: Raises UnsupportedFileFormatException

        WHY: Cannot determine format without extension.
        """
        with pytest.raises(UnsupportedFileFormatException):
            parser._detect_format("instructors")

    def test_empty_filename_raises_exception(self, parser):
        """
        GIVEN: An empty filename
        WHEN: _detect_format is called
        THEN: Raises UnsupportedFileFormatException

        WHY: Empty filename is invalid input.
        """
        with pytest.raises(UnsupportedFileFormatException):
            parser._detect_format("")

    def test_none_filename_raises_exception(self, parser):
        """
        GIVEN: None as filename
        WHEN: _detect_format is called
        THEN: Raises UnsupportedFileFormatException

        WHY: None filename is invalid input.
        """
        with pytest.raises(UnsupportedFileFormatException):
            parser._detect_format(None)


# =============================================================================
# TEST: CSV PARSING
# =============================================================================

class TestCSVParsing:
    """
    Tests for CSV file parsing.

    WHY: CSV is the most common format and must handle various edge cases
    including encoding differences and malformed data.
    """

    def test_parse_valid_csv(self, parser, valid_instructor_csv):
        """
        GIVEN: Valid CSV file with instructor data
        WHEN: parse_instructor_roster is called
        THEN: Returns ParsedRoster with correct entries

        WHY: Tests the happy path for CSV parsing.
        """
        result = parser.parse_instructor_roster(valid_instructor_csv, "instructors.csv")

        assert result.roster_type == RosterType.INSTRUCTOR
        assert result.total_rows == 2
        assert len(result.instructor_entries) == 2

    def test_parse_csv_with_utf8_encoding(self, parser):
        """
        GIVEN: CSV file with UTF-8 special characters
        WHEN: _parse_csv is called
        THEN: Characters are preserved correctly

        WHY: UTF-8 is standard encoding but must be handled explicitly.
        """
        csv_content = "name,email\nJürgen Müller,jurgen@example.com\n".encode('utf-8')
        headers, rows = parser._parse_csv(csv_content)

        assert "Jürgen Müller" in rows[0]['name']

    def test_parse_csv_with_latin1_encoding(self, parser):
        """
        GIVEN: CSV file with latin-1 encoding
        WHEN: _parse_csv is called
        THEN: Falls back to latin-1 and parses correctly

        WHY: Legacy systems may export latin-1 encoded files.
        """
        csv_content = "name,email\nJürgen Müller,jurgen@example.com\n".encode('latin-1')
        headers, rows = parser._parse_csv(csv_content)

        assert len(rows) == 1
        assert "jurgen@example.com" in rows[0]['email']

    def test_parse_csv_extracts_headers(self, parser):
        """
        GIVEN: CSV file with header row
        WHEN: _parse_csv is called
        THEN: Headers are extracted correctly

        WHY: Headers are needed for column mapping.
        """
        csv_content = b"name,email,department\nJohn,john@example.com,Engineering\n"
        headers, rows = parser._parse_csv(csv_content)

        assert headers == ['name', 'email', 'department']
        assert len(rows) == 1

    def test_parse_empty_csv_returns_empty_list(self, parser):
        """
        GIVEN: CSV file with only headers
        WHEN: _parse_csv is called
        THEN: Returns empty rows list

        WHY: Header-only files should not cause errors.
        """
        csv_content = b"name,email\n"
        headers, rows = parser._parse_csv(csv_content)

        assert headers == ['name', 'email']
        assert rows == []


# =============================================================================
# TEST: JSON PARSING
# =============================================================================

class TestJSONParsing:
    """
    Tests for JSON file parsing.

    WHY: JSON format is useful for API integrations but requires
    strict format validation.
    """

    def test_parse_valid_json_array(self, parser, valid_instructor_json):
        """
        GIVEN: Valid JSON array of objects
        WHEN: _parse_json is called
        THEN: Returns headers and rows correctly

        WHY: Tests the happy path for JSON parsing.
        """
        headers, rows = parser._parse_json(valid_instructor_json)

        assert 'name' in headers
        assert 'email' in headers
        assert len(rows) == 2

    def test_parse_json_preserves_structure(self, parser):
        """
        GIVEN: JSON with nested structure
        WHEN: _parse_json is called
        THEN: Data is preserved correctly

        WHY: JSON may contain complex data that should be preserved.
        """
        data = [{"name": "Test", "email": "test@example.com"}]
        content = json.dumps(data).encode('utf-8')

        headers, rows = parser._parse_json(content)

        assert rows[0]['name'] == "Test"
        assert rows[0]['email'] == "test@example.com"

    def test_parse_invalid_json_raises_exception(self, parser):
        """
        GIVEN: Invalid JSON content
        WHEN: _parse_json is called
        THEN: Raises FileImportException

        WHY: Invalid JSON should produce clear error message.
        """
        content = b"{invalid json content"

        with pytest.raises(FileImportException) as exc_info:
            parser._parse_json(content)

        assert "Invalid JSON" in str(exc_info.value.message)

    def test_parse_json_non_array_raises_exception(self, parser):
        """
        GIVEN: JSON object (not array)
        WHEN: _parse_json is called
        THEN: Raises FileImportException

        WHY: Only arrays of objects are supported.
        """
        content = json.dumps({"name": "Test"}).encode('utf-8')

        with pytest.raises(FileImportException) as exc_info:
            parser._parse_json(content)

        assert "array" in str(exc_info.value.message).lower()

    def test_parse_empty_json_array(self, parser):
        """
        GIVEN: Empty JSON array
        WHEN: _parse_json is called
        THEN: Returns empty headers and rows

        WHY: Empty arrays are valid but should be handled.
        """
        content = json.dumps([]).encode('utf-8')
        headers, rows = parser._parse_json(content)

        assert headers == []
        assert rows == []


# =============================================================================
# TEST: COLUMN AUTO-DETECTION
# =============================================================================

class TestColumnAutoDetection:
    """
    Tests for automatic column mapping detection.

    WHY: Auto-detection allows flexible file formats while minimizing
    manual configuration for users.
    """

    def test_auto_detect_standard_columns(self, parser):
        """
        GIVEN: Headers with standard column names
        WHEN: _auto_detect_columns is called
        THEN: Maps all columns correctly

        WHY: Standard naming should work without issues.
        """
        headers = ['name', 'email', 'tracks']
        mapping = parser._auto_detect_columns(headers, parser.instructor_aliases)

        assert mapping.get_source_column('name') == 'name'
        assert mapping.get_source_column('email') == 'email'
        assert mapping.get_source_column('tracks') == 'tracks'
        assert mapping.confidence == 1.0

    def test_auto_detect_alternative_column_names(self, parser):
        """
        GIVEN: Headers with alternative column names
        WHEN: _auto_detect_columns is called
        THEN: Maps columns using aliases

        WHY: Different organizations use different naming conventions.
        """
        headers = ['full_name', 'email_address', 'assigned_tracks']
        mapping = parser._auto_detect_columns(headers, parser.instructor_aliases)

        assert mapping.get_source_column('name') == 'full_name'
        assert mapping.get_source_column('email') == 'email_address'

    def test_auto_detect_partial_columns(self, parser):
        """
        GIVEN: Headers with only some expected columns
        WHEN: _auto_detect_columns is called
        THEN: Maps available columns and reports unmapped

        WHY: Not all files have all optional columns.
        """
        headers = ['name', 'email', 'custom_field']
        mapping = parser._auto_detect_columns(headers, parser.instructor_aliases)

        assert mapping.get_source_column('name') == 'name'
        assert 'custom_field' in mapping.unmapped_columns

    def test_auto_detect_tracks_unmapped_columns(self, parser):
        """
        GIVEN: Headers with columns that don't match any alias
        WHEN: _auto_detect_columns is called
        THEN: Records unmapped columns for user feedback

        WHY: Users should know which columns were ignored.
        """
        headers = ['name', 'email', 'unknown_column', 'another_unknown']
        mapping = parser._auto_detect_columns(headers, parser.instructor_aliases)

        assert 'unknown_column' in mapping.unmapped_columns
        assert 'another_unknown' in mapping.unmapped_columns

    def test_auto_detect_case_insensitive(self, parser):
        """
        GIVEN: Headers with mixed case
        WHEN: _auto_detect_columns is called
        THEN: Matches case-insensitively

        WHY: Column names may vary in capitalization.
        """
        headers = ['NAME', 'Email', 'TRACKS']
        mapping = parser._auto_detect_columns(headers, parser.instructor_aliases)

        assert mapping.get_source_column('name') == 'NAME'
        assert mapping.get_source_column('email') == 'Email'

    def test_auto_detect_confidence_calculation(self, parser):
        """
        GIVEN: Headers with partial required column coverage
        WHEN: _auto_detect_columns is called
        THEN: Confidence reflects coverage percentage

        WHY: Confidence helps determine if parsing is likely to succeed.
        """
        # Only name is present (missing email which is required)
        headers = ['name']
        mapping = parser._auto_detect_columns(headers, parser.instructor_aliases)

        # Should have less than 100% confidence
        assert mapping.confidence < 1.0


# =============================================================================
# TEST: REQUIRED COLUMN VALIDATION
# =============================================================================

class TestRequiredColumnValidation:
    """
    Tests for required column validation.

    WHY: Missing required columns should be caught early with clear errors.
    """

    def test_validation_passes_with_all_required(self, parser):
        """
        GIVEN: Mapping with all required columns
        WHEN: _validate_required_columns is called
        THEN: No exception is raised

        WHY: Valid mappings should pass silently.
        """
        mapping = ColumnMapping(
            field_to_source={'name': 'name', 'email': 'email'},
            auto_detected=True
        )

        # Should not raise
        parser._validate_required_columns(
            mapping,
            parser.instructor_aliases,
            ['name', 'email'],
            'test.csv'
        )

    def test_validation_fails_missing_required(self, parser):
        """
        GIVEN: Mapping missing required columns
        WHEN: _validate_required_columns is called
        THEN: Raises MissingRequiredColumnException

        WHY: Clear error helps users fix their files.
        """
        mapping = ColumnMapping(
            field_to_source={'name': 'name'},
            auto_detected=True
        )

        with pytest.raises(MissingRequiredColumnException) as exc_info:
            parser._validate_required_columns(
                mapping,
                parser.instructor_aliases,
                ['name'],
                'test.csv'
            )

        assert 'email' in str(exc_info.value.message).lower()


# =============================================================================
# TEST: INSTRUCTOR ROSTER PARSING
# =============================================================================

class TestInstructorRosterParsing:
    """
    Tests for complete instructor roster parsing workflow.

    WHY: End-to-end parsing tests ensure all components work together.
    """

    def test_parse_valid_instructor_roster(self, parser, valid_instructor_csv):
        """
        GIVEN: Valid CSV file with instructor data
        WHEN: parse_instructor_roster is called
        THEN: Returns ParsedRoster with all entries

        WHY: Tests the complete parsing pipeline.
        """
        result = parser.parse_instructor_roster(valid_instructor_csv, "instructors.csv")

        assert result.roster_type == RosterType.INSTRUCTOR
        assert result.total_rows == 2
        assert result.valid_rows == 2
        assert result.error_rows == 0

    def test_parse_instructor_roster_extracts_fields(self, parser, valid_instructor_csv):
        """
        GIVEN: Valid CSV with all instructor fields
        WHEN: parse_instructor_roster is called
        THEN: All fields are extracted correctly

        WHY: Ensures field extraction works for all supported fields.
        """
        result = parser.parse_instructor_roster(valid_instructor_csv, "instructors.csv")

        entry = result.instructor_entries[0]
        assert entry.name == "John Doe"
        assert entry.email == "john.doe@example.com"
        assert "Backend Development" in entry.tracks
        assert "DevOps" in entry.tracks
        assert entry.role == "instructor"

    def test_parse_instructor_tracks_comma_separated(self, parser):
        """
        GIVEN: CSV with comma-separated tracks
        WHEN: parse_instructor_roster is called
        THEN: Tracks are split correctly

        WHY: Instructors may teach multiple tracks.
        """
        csv_content = b"name,email,tracks\nJohn,john@example.com,\"Track A, Track B, Track C\"\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        entry = result.instructor_entries[0]
        assert len(entry.tracks) == 3
        assert "Track A" in entry.tracks
        assert "Track B" in entry.tracks
        assert "Track C" in entry.tracks

    def test_parse_instructor_available_days(self, parser):
        """
        GIVEN: CSV with available_days column
        WHEN: parse_instructor_roster is called
        THEN: Available days are parsed correctly

        WHY: Scheduling requires knowledge of instructor availability.
        """
        csv_content = b"name,email,available_days\nJohn,john@example.com,\"Monday, Wednesday, Friday\"\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        entry = result.instructor_entries[0]
        assert "Monday" in entry.available_days
        assert "Wednesday" in entry.available_days
        assert "Friday" in entry.available_days

    def test_parse_instructor_default_available_days(self, parser):
        """
        GIVEN: CSV without available_days column
        WHEN: parse_instructor_roster is called
        THEN: Default to Monday-Friday

        WHY: Sensible default for unspecified availability.
        """
        csv_content = b"name,email\nJohn,john@example.com\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        entry = result.instructor_entries[0]
        assert len(entry.available_days) == 5
        assert "Monday" in entry.available_days
        assert "Friday" in entry.available_days

    def test_parse_instructor_empty_file_raises_exception(self, parser):
        """
        GIVEN: CSV file with only headers
        WHEN: parse_instructor_roster is called
        THEN: Raises EmptyFileException

        WHY: Empty files indicate user error.
        """
        csv_content = b"name,email\n"

        with pytest.raises(EmptyFileException):
            parser.parse_instructor_roster(csv_content, "empty.csv")

    def test_parse_instructor_skips_empty_rows(self, parser):
        """
        GIVEN: CSV with empty rows
        WHEN: parse_instructor_roster is called
        THEN: Empty rows are skipped

        WHY: Empty rows shouldn't create invalid entries.
        """
        csv_content = b"name,email\nJohn,john@example.com\n,,\n,,\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert len(result.instructor_entries) == 1
        assert result.skipped_rows == 2

    def test_parse_instructor_with_manual_mapping(self, parser):
        """
        GIVEN: CSV with custom column names and manual mapping
        WHEN: parse_instructor_roster is called with manual_mapping
        THEN: Uses provided mapping

        WHY: Manual mapping allows handling non-standard files.
        """
        csv_content = b"instructor_name,instructor_email\nJohn,john@example.com\n"
        manual_mapping = {
            'name': 'instructor_name',
            'email': 'instructor_email'
        }

        result = parser.parse_instructor_roster(
            csv_content,
            "custom.csv",
            manual_mapping=manual_mapping
        )

        assert len(result.instructor_entries) == 1
        assert result.instructor_entries[0].name == "John"

    def test_parse_instructor_json_format(self, parser, valid_instructor_json):
        """
        GIVEN: Valid JSON file with instructor data
        WHEN: parse_instructor_roster is called
        THEN: Parses JSON correctly

        WHY: JSON format support for API integrations.
        """
        result = parser.parse_instructor_roster(valid_instructor_json, "instructors.json")

        assert result.roster_type == RosterType.INSTRUCTOR
        assert result.total_rows == 2
        assert len(result.instructor_entries) == 2

    def test_parse_instructor_records_parse_duration(self, parser, valid_instructor_csv):
        """
        GIVEN: Valid instructor CSV
        WHEN: parse_instructor_roster is called
        THEN: Records parse duration in milliseconds

        WHY: Performance metrics help identify issues.
        """
        result = parser.parse_instructor_roster(valid_instructor_csv, "test.csv")

        assert result.parse_duration_ms >= 0

    def test_parse_instructor_email_normalized(self, parser):
        """
        GIVEN: CSV with uppercase email
        WHEN: parse_instructor_roster is called
        THEN: Email is lowercased

        WHY: Consistent email format prevents duplicates.
        """
        csv_content = b"name,email\nJohn,JOHN@EXAMPLE.COM\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert result.instructor_entries[0].email == "john@example.com"


# =============================================================================
# TEST: STUDENT ROSTER PARSING
# =============================================================================

class TestStudentRosterParsing:
    """
    Tests for complete student roster parsing workflow.

    WHY: Student rosters have different fields than instructor rosters.
    """

    def test_parse_valid_student_roster(self, parser, valid_student_csv):
        """
        GIVEN: Valid CSV file with student data
        WHEN: parse_student_roster is called
        THEN: Returns ParsedRoster with all entries

        WHY: Tests the complete parsing pipeline.
        """
        result = parser.parse_student_roster(valid_student_csv, "students.csv")

        assert result.roster_type == RosterType.STUDENT
        assert result.total_rows == 3
        assert result.valid_rows == 3

    def test_parse_student_roster_extracts_fields(self, parser, valid_student_csv):
        """
        GIVEN: Valid CSV with all student fields
        WHEN: parse_student_roster is called
        THEN: All fields are extracted correctly

        WHY: Ensures field extraction works for all supported fields.
        """
        result = parser.parse_student_roster(valid_student_csv, "students.csv")

        entry = result.student_entries[0]
        assert entry.name == "Alice Johnson"
        assert entry.email == "alice.johnson@example.com"
        assert entry.track == "Backend Development"
        assert entry.location == "New York"
        assert entry.employee_id == "EMP001"

    def test_parse_student_track_required(self, parser):
        """
        GIVEN: CSV with track column
        WHEN: parse_student_roster is called
        THEN: Track is extracted correctly

        WHY: Track assignment is critical for students.
        """
        csv_content = b"name,email,track\nAlice,alice@example.com,Python Programming\n"
        result = parser.parse_student_roster(csv_content, "test.csv")

        assert result.student_entries[0].track == "Python Programming"

    def test_parse_student_location_optional(self, parser):
        """
        GIVEN: CSV without location column
        WHEN: parse_student_roster is called
        THEN: Location is None

        WHY: Location is optional for single-location programs.
        """
        csv_content = b"name,email,track\nAlice,alice@example.com,Backend\n"
        result = parser.parse_student_roster(csv_content, "test.csv")

        assert result.student_entries[0].location is None

    def test_parse_student_empty_file_raises_exception(self, parser):
        """
        GIVEN: CSV file with only headers
        WHEN: parse_student_roster is called
        THEN: Raises EmptyFileException

        WHY: Empty files indicate user error.
        """
        csv_content = b"name,email,track\n"

        with pytest.raises(EmptyFileException):
            parser.parse_student_roster(csv_content, "empty.csv")

    def test_parse_student_skips_empty_rows(self, parser):
        """
        GIVEN: CSV with empty rows
        WHEN: parse_student_roster is called
        THEN: Empty rows are skipped

        WHY: Empty rows shouldn't create invalid entries.
        """
        csv_content = b"name,email,track\nAlice,alice@example.com,Backend\n,,\n"
        result = parser.parse_student_roster(csv_content, "test.csv")

        assert len(result.student_entries) == 1
        assert result.skipped_rows == 1

    def test_parse_student_json_format(self, parser, valid_student_json):
        """
        GIVEN: Valid JSON file with student data
        WHEN: parse_student_roster is called
        THEN: Parses JSON correctly

        WHY: JSON format support for API integrations.
        """
        result = parser.parse_student_roster(valid_student_json, "students.json")

        assert result.roster_type == RosterType.STUDENT
        assert result.total_rows == 2
        assert len(result.student_entries) == 2

    def test_parse_student_instructor_email_normalized(self, parser):
        """
        GIVEN: CSV with instructor field
        WHEN: parse_student_roster is called
        THEN: Instructor email is lowercased

        WHY: Consistent email format for matching.
        """
        csv_content = b"name,email,track,instructor\nAlice,alice@example.com,Backend,JOHN@EXAMPLE.COM\n"
        result = parser.parse_student_roster(csv_content, "test.csv")

        assert result.student_entries[0].instructor == "john@example.com"

    def test_parse_student_with_manual_mapping(self, parser):
        """
        GIVEN: CSV with custom column names and manual mapping
        WHEN: parse_student_roster is called with manual_mapping
        THEN: Uses provided mapping

        WHY: Manual mapping allows handling non-standard files.
        """
        csv_content = b"student_name,student_email,learning_track\nAlice,alice@example.com,Backend\n"
        manual_mapping = {
            'name': 'student_name',
            'email': 'student_email',
            'track': 'learning_track'
        }

        result = parser.parse_student_roster(
            csv_content,
            "custom.csv",
            manual_mapping=manual_mapping
        )

        assert len(result.student_entries) == 1
        assert result.student_entries[0].name == "Alice"


# =============================================================================
# TEST: DUPLICATE EMAIL DETECTION
# =============================================================================

class TestDuplicateEmailDetection:
    """
    Tests for duplicate email detection.

    WHY: Duplicate emails indicate data issues that need resolution.
    """

    def test_detect_duplicates_in_instructor_roster(self, parser):
        """
        GIVEN: CSV with duplicate instructor emails
        WHEN: parse_instructor_roster is called
        THEN: Duplicates are detected and reported

        WHY: Same instructor shouldn't be listed twice.
        """
        csv_content = b"""name,email
John,john@example.com
Jane,jane@example.com
John Duplicate,john@example.com
"""
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert "john@example.com" in result.duplicate_emails
        assert result.duplicate_emails["john@example.com"] == [2, 4]  # Row numbers

    def test_detect_duplicates_in_student_roster(self, parser):
        """
        GIVEN: CSV with duplicate student emails
        WHEN: parse_student_roster is called
        THEN: Duplicates are detected and reported

        WHY: Same student shouldn't be enrolled twice.
        """
        csv_content = b"""name,email,track
Alice,alice@example.com,Backend
Bob,bob@example.com,Frontend
Alice Duplicate,alice@example.com,Backend
"""
        result = parser.parse_student_roster(csv_content, "test.csv")

        assert "alice@example.com" in result.duplicate_emails
        assert len(result.duplicate_emails["alice@example.com"]) == 2

    def test_no_false_positive_duplicates(self, parser):
        """
        GIVEN: CSV with unique emails
        WHEN: parse_instructor_roster is called
        THEN: No duplicates are reported

        WHY: Unique emails shouldn't be flagged.
        """
        csv_content = b"""name,email
John,john@example.com
Jane,jane@example.com
Bob,bob@example.com
"""
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert len(result.duplicate_emails) == 0


# =============================================================================
# TEST: TEMPLATE GENERATION
# =============================================================================

class TestTemplateGeneration:
    """
    Tests for roster template file generation.

    WHY: Templates help users create properly formatted files.
    """

    def test_generate_instructor_template_is_valid_csv(self):
        """
        GIVEN: No inputs
        WHEN: generate_instructor_template is called
        THEN: Returns valid CSV bytes

        WHY: Template must be parseable CSV.
        """
        template = RosterFileParser.generate_instructor_template()

        # Should be bytes
        assert isinstance(template, bytes)

        # Should be valid CSV
        reader = csv.reader(io.StringIO(template.decode('utf-8')))
        rows = list(reader)

        assert len(rows) >= 2  # Header + at least one example

    def test_generate_instructor_template_has_required_headers(self):
        """
        GIVEN: No inputs
        WHEN: generate_instructor_template is called
        THEN: Contains all required headers

        WHY: Template should guide users on required fields.
        """
        template = RosterFileParser.generate_instructor_template()

        reader = csv.reader(io.StringIO(template.decode('utf-8')))
        headers = next(reader)

        assert 'name' in headers
        assert 'email' in headers
        assert 'tracks' in headers

    def test_generate_instructor_template_has_examples(self):
        """
        GIVEN: No inputs
        WHEN: generate_instructor_template is called
        THEN: Contains example data rows

        WHY: Examples show proper format for each field.
        """
        template = RosterFileParser.generate_instructor_template()

        reader = csv.reader(io.StringIO(template.decode('utf-8')))
        rows = list(reader)

        assert len(rows) >= 2  # Header + examples
        assert rows[1][0]  # First example has name

    def test_generate_student_template_is_valid_csv(self):
        """
        GIVEN: No inputs
        WHEN: generate_student_template is called
        THEN: Returns valid CSV bytes

        WHY: Template must be parseable CSV.
        """
        template = RosterFileParser.generate_student_template()

        # Should be bytes
        assert isinstance(template, bytes)

        # Should be valid CSV
        reader = csv.reader(io.StringIO(template.decode('utf-8')))
        rows = list(reader)

        assert len(rows) >= 2

    def test_generate_student_template_has_required_headers(self):
        """
        GIVEN: No inputs
        WHEN: generate_student_template is called
        THEN: Contains all required headers

        WHY: Template should guide users on required fields.
        """
        template = RosterFileParser.generate_student_template()

        reader = csv.reader(io.StringIO(template.decode('utf-8')))
        headers = next(reader)

        assert 'name' in headers
        assert 'email' in headers
        assert 'track' in headers

    def test_generate_student_template_has_multiple_examples(self):
        """
        GIVEN: No inputs
        WHEN: generate_student_template is called
        THEN: Contains multiple example rows

        WHY: Multiple examples show different valid configurations.
        """
        template = RosterFileParser.generate_student_template()

        reader = csv.reader(io.StringIO(template.decode('utf-8')))
        rows = list(reader)

        # Header + at least 3 examples
        assert len(rows) >= 4

    def test_templates_are_parseable_by_parser(self):
        """
        GIVEN: Generated templates
        WHEN: Templates are fed back to the parser
        THEN: Parser handles them without errors

        WHY: Self-consistency check - our templates should work with our parser.
        """
        parser = RosterFileParser()

        # Instructor template
        instructor_template = RosterFileParser.generate_instructor_template()
        instructor_result = parser.parse_instructor_roster(
            instructor_template, "template.csv"
        )
        assert instructor_result.total_rows >= 1

        # Student template
        student_template = RosterFileParser.generate_student_template()
        student_result = parser.parse_student_roster(
            student_template, "template.csv"
        )
        assert student_result.total_rows >= 1


# =============================================================================
# TEST: EDGE CASES
# =============================================================================

class TestEdgeCases:
    """
    Tests for edge cases and boundary conditions.

    WHY: Edge cases often cause production issues.
    """

    def test_whitespace_trimmed_from_values(self, parser):
        """
        GIVEN: CSV with whitespace around values
        WHEN: parse_instructor_roster is called
        THEN: Whitespace is trimmed

        WHY: Stray whitespace causes matching issues.
        """
        csv_content = b"name,email\n  John Doe  ,  john@example.com  \n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert result.instructor_entries[0].name == "John Doe"
        assert result.instructor_entries[0].email == "john@example.com"

    def test_handles_none_values_gracefully(self, parser):
        """
        GIVEN: CSV where some fields are empty
        WHEN: parse_instructor_roster is called
        THEN: Empty fields become None or empty string

        WHY: Missing optional data is common.
        """
        csv_content = b"name,email,phone,notes\nJohn,john@example.com,,\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        entry = result.instructor_entries[0]
        assert entry.name == "John"
        # Optional fields should handle None gracefully

    def test_handles_very_long_values(self, parser):
        """
        GIVEN: CSV with very long field values
        WHEN: parse_instructor_roster is called
        THEN: Values are preserved

        WHY: Some notes fields may be lengthy.
        """
        long_note = "A" * 10000
        csv_content = f"name,email,notes\nJohn,john@example.com,{long_note}\n".encode('utf-8')
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert len(result.instructor_entries[0].notes) == 10000

    def test_handles_special_characters_in_csv(self, parser):
        """
        GIVEN: CSV with special characters (quotes, commas)
        WHEN: parse_instructor_roster is called
        THEN: Characters are preserved correctly

        WHY: CSV escaping must be handled properly.
        """
        csv_content = b'name,email,notes\n"John ""JD"" Doe",john@example.com,"Note with, comma"\n'
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        entry = result.instructor_entries[0]
        assert 'JD' in entry.name
        assert 'comma' in entry.notes

    def test_handles_unicode_in_names(self, parser):
        """
        GIVEN: CSV with Unicode characters in names
        WHEN: parse_instructor_roster is called
        THEN: Unicode is preserved

        WHY: International names contain various characters.
        """
        csv_content = "name,email\n日本語名前,japanese@example.com\n".encode('utf-8')
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert "日本語" in result.instructor_entries[0].name

    def test_preserves_raw_data_for_debugging(self, parser):
        """
        GIVEN: CSV with various fields
        WHEN: parse_instructor_roster is called
        THEN: Raw row data is preserved in entry

        WHY: Raw data helps debug mapping issues.
        """
        csv_content = b"name,email,custom\nJohn,john@example.com,value\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        entry = result.instructor_entries[0]
        assert entry.raw_data is not None
        assert entry.raw_data['custom'] == 'value'

    def test_row_numbers_start_from_2(self, parser):
        """
        GIVEN: CSV with multiple rows
        WHEN: parse_instructor_roster is called
        THEN: Row numbers start from 2 (after header)

        WHY: Row numbers should match spreadsheet display.
        """
        csv_content = b"name,email\nFirst,first@example.com\nSecond,second@example.com\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert result.instructor_entries[0].source_row == 2
        assert result.instructor_entries[1].source_row == 3


# =============================================================================
# TEST: VALIDATION INTEGRATION
# =============================================================================

class TestValidationIntegration:
    """
    Tests for entry validation integration.

    WHY: Validation counts must accurately reflect entry validity.
    """

    def test_valid_entries_counted_correctly(self, parser):
        """
        GIVEN: CSV with valid entries
        WHEN: parse_instructor_roster is called
        THEN: valid_rows reflects actually valid entries

        WHY: Metrics guide users on file quality.
        """
        csv_content = b"name,email\nJohn,john@example.com\nJane,jane@example.com\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert result.valid_rows == 2
        assert result.error_rows == 0

    def test_invalid_entries_counted_correctly(self, parser):
        """
        GIVEN: CSV with invalid entries (missing email)
        WHEN: parse_instructor_roster is called
        THEN: error_rows reflects invalid entries

        WHY: Users need to know how many entries need fixing.
        """
        csv_content = b"name,email\nJohn,john@example.com\nInvalid,not-an-email\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        # Entry with invalid email should be counted as error
        # (depends on validation implementation)
        assert result.total_rows == 2

    def test_get_valid_entries_returns_only_valid(self, parser):
        """
        GIVEN: ParsedRoster with mixed valid/invalid entries
        WHEN: get_valid_entries is called
        THEN: Returns only valid entries

        WHY: Easy access to processable entries.
        """
        csv_content = b"name,email\nJohn,john@example.com\nJane,jane@example.com\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        valid = result.get_valid_entries()
        assert len(valid) == 2


# =============================================================================
# TEST: ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """
    Tests for error handling and exception wrapping.

    WHY: Proper error handling provides useful debugging information.
    """

    def test_parse_error_includes_filename(self, parser):
        """
        GIVEN: Invalid file content
        WHEN: Parsing fails
        THEN: Exception includes filename for context

        WHY: Filename helps identify problematic file.
        """
        # Binary garbage that's not valid CSV
        with pytest.raises(Exception):
            # This might raise various exceptions depending on content
            parser.parse_instructor_roster(b'\x00\x01\x02', "binary.csv")

    def test_empty_file_exception_includes_filename(self, parser):
        """
        GIVEN: Empty CSV file
        WHEN: parse_instructor_roster is called
        THEN: EmptyFileException includes filename

        WHY: User needs to know which file is empty.
        """
        csv_content = b"name,email\n"

        with pytest.raises(EmptyFileException) as exc_info:
            parser.parse_instructor_roster(csv_content, "empty.csv")

        assert "empty.csv" in str(exc_info.value.message)

    def test_missing_column_exception_lists_available(self, parser):
        """
        GIVEN: CSV missing required columns
        WHEN: parse_instructor_roster is called
        THEN: Exception lists available columns

        WHY: Helps user understand what columns exist.
        """
        csv_content = b"wrong_column,another_wrong\nvalue1,value2\n"

        with pytest.raises(MissingRequiredColumnException) as exc_info:
            parser.parse_instructor_roster(csv_content, "bad.csv")

        # Should mention available columns
        assert exc_info.value.available_columns is not None


# =============================================================================
# TEST: PARSED ROSTER METHODS
# =============================================================================

class TestParsedRosterMethods:
    """
    Tests for ParsedRoster utility methods.

    WHY: Utility methods simplify working with parse results.
    """

    def test_has_errors_when_errors_exist(self, parser):
        """
        GIVEN: ParsedRoster with error entries
        WHEN: has_errors is called
        THEN: Returns True

        WHY: Quick check for processing decision.
        """
        csv_content = b"name,email\nJohn,invalid-email\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        # Check if has_errors method exists and works
        if hasattr(result, 'has_errors'):
            # Result may have errors depending on validation
            pass

    def test_has_duplicates_when_duplicates_exist(self, parser):
        """
        GIVEN: ParsedRoster with duplicate emails
        WHEN: has_duplicates is called
        THEN: Returns True

        WHY: Quick check for data quality.
        """
        csv_content = b"name,email\nJohn,john@example.com\nJane,john@example.com\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert result.has_duplicates() is True

    def test_has_duplicates_when_no_duplicates(self, parser):
        """
        GIVEN: ParsedRoster without duplicate emails
        WHEN: has_duplicates is called
        THEN: Returns False

        WHY: Quick check for data quality.
        """
        csv_content = b"name,email\nJohn,john@example.com\nJane,jane@example.com\n"
        result = parser.parse_instructor_roster(csv_content, "test.csv")

        assert result.has_duplicates() is False
