"""
Unit Tests for File Import Domain Entities

BUSINESS CONTEXT:
These tests verify the domain entities used for importing roster files
(instructors, students) in the AI-powered project builder feature.

WHY THESE TESTS EXIST:
1. Validate roster entry validation rules
2. Ensure proper file upload tracking
3. Verify column mapping functionality
4. Test validation result aggregation
5. Verify exception handling and error messages

WHAT IS TESTED:
- InstructorRosterEntry: Parsed instructor row validation
- StudentRosterEntry: Parsed student row validation
- ColumnAlias: Column name matching
- ColumnMapping: Field to column mappings
- FileUpload: Upload metadata tracking
- ParsedRoster: Parsed data aggregation
- ValidationIssue: Individual validation issues
- RosterValidationResult: Complete validation results
- ImportProgress: Import progress tracking
- Custom exceptions: All file import exceptions

HOW TO RUN:
    pytest tests/unit/course_management/test_file_import_entities.py -v

TDD: Tests written BEFORE implementation verification.

@module test_file_import_entities
@author Course Creator Platform
@version 1.0.0
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'services' / 'course-management'))

from course_management.domain.entities.file_import import (
    # File upload entities
    FileUpload,
    ColumnMapping,
    ColumnAlias,
    ParsedRoster,
    # Roster entry entities
    InstructorRosterEntry,
    StudentRosterEntry,
    # Validation entities
    ValidationIssue,
    RosterValidationResult,
    ImportProgress,
    # Column alias configurations
    INSTRUCTOR_COLUMN_ALIASES,
    STUDENT_COLUMN_ALIASES,
    # Enumerations
    FileFormat,
    RosterType,
    FileUploadStatus,
    ValidationSeverity,
    # Exceptions
    FileImportException,
    UnsupportedFileFormatException,
    MissingRequiredColumnException,
    InvalidDataException,
    EmptyFileException,
    DuplicateEntryException
)


# =============================================================================
# COLUMN ALIAS TESTS
# =============================================================================

class TestColumnAlias:
    """
    Test suite for ColumnAlias value object.

    WHY: Column aliases enable flexible column name matching in roster files.
    Users have different naming conventions that must be handled.
    """

    def test_create_column_alias(self):
        """
        Test creating a column alias.

        WHY: Basic happy path for alias creation.
        """
        alias = ColumnAlias(
            target_field="email",
            aliases=["email", "e-mail", "email_address"],
            required=True
        )

        assert alias.target_field == "email"
        assert len(alias.aliases) == 3
        assert alias.required is True

    def test_column_alias_matches_exact(self):
        """
        Test exact match on column name.

        WHY: Exact matches should work.
        """
        alias = ColumnAlias(
            target_field="email",
            aliases=["email", "e-mail"]
        )

        assert alias.matches("email") is True
        assert alias.matches("e-mail") is True

    def test_column_alias_matches_case_insensitive(self):
        """
        Test case-insensitive matching.

        WHY: Column headers may have different casing.
        """
        alias = ColumnAlias(
            target_field="email",
            aliases=["email", "Email_Address"]
        )

        assert alias.matches("EMAIL") is True
        assert alias.matches("email") is True
        assert alias.matches("email_address") is True

    def test_column_alias_matches_with_whitespace(self):
        """
        Test matching with leading/trailing whitespace.

        WHY: CSV files often have whitespace around headers.
        """
        alias = ColumnAlias(
            target_field="email",
            aliases=["email"]
        )

        assert alias.matches("  email  ") is True
        assert alias.matches("email ") is True

    def test_column_alias_no_match(self):
        """
        Test non-matching column name.

        WHY: Non-matching columns should return False.
        """
        alias = ColumnAlias(
            target_field="email",
            aliases=["email", "e-mail"]
        )

        assert alias.matches("phone") is False
        assert alias.matches("mail") is False


class TestColumnMapping:
    """
    Test suite for ColumnMapping value object.

    WHY: ColumnMapping tracks which source columns map to which target fields.
    """

    def test_create_column_mapping(self):
        """
        Test creating a column mapping.

        WHY: Basic creation test.
        """
        mapping = ColumnMapping(
            field_to_source={
                "name": "Full Name",
                "email": "Email Address"
            },
            unmapped_columns=["Notes"],
            confidence=0.95
        )

        assert mapping.get_source_column("name") == "Full Name"
        assert mapping.get_source_column("email") == "Email Address"
        assert len(mapping.unmapped_columns) == 1

    def test_column_mapping_has_field(self):
        """
        Test checking if field is mapped.

        WHY: Useful for conditional processing.
        """
        mapping = ColumnMapping(
            field_to_source={"name": "Name", "email": "Email"}
        )

        assert mapping.has_field("name") is True
        assert mapping.has_field("email") is True
        assert mapping.has_field("phone") is False

    def test_column_mapping_to_dict(self):
        """
        Test serialization.

        WHY: Mappings need to be stored/transferred.
        """
        mapping = ColumnMapping(
            field_to_source={"name": "Name"},
            confidence=0.9
        )

        result = mapping.to_dict()

        assert result["field_to_source"]["name"] == "Name"
        assert result["confidence"] == 0.9


# =============================================================================
# INSTRUCTOR ROSTER ENTRY TESTS
# =============================================================================

class TestInstructorRosterEntry:
    """
    Test suite for InstructorRosterEntry domain entity.

    WHY: InstructorRosterEntry represents a parsed row from an instructor
    roster file. Validation ensures data quality before import.
    """

    def test_create_valid_instructor_entry(self):
        """
        Test creating a valid instructor entry.

        WHY: Basic happy path for instructor row.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="john@example.com",
            source_row=2
        )

        assert entry.name == "John Doe"
        assert entry.email == "john@example.com"
        assert entry.source_row == 2

    def test_instructor_entry_with_all_fields(self):
        """
        Test instructor entry with all optional fields.

        WHY: Roster files may include additional data.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="john@example.com",
            source_row=2,
            tracks=["Backend", "DevOps"],
            role="lead_instructor",
            available_days=["Monday", "Wednesday"],
            start_date="2024-01-15",
            end_date="2024-06-30",
            phone="+1-555-1234",
            department="Engineering",
            notes="Part-time availability"
        )

        assert len(entry.tracks) == 2
        assert entry.role == "lead_instructor"
        assert entry.start_date == "2024-01-15"

    def test_instructor_entry_validation_valid(self):
        """
        Test validation passes for valid entry.

        WHY: Valid data should pass validation.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="john@example.com",
            source_row=2
        )

        result = entry.validate()

        assert result is True
        assert entry.is_valid is True
        assert len(entry.validation_errors) == 0

    def test_instructor_entry_validation_missing_name(self):
        """
        Test validation fails for missing name.

        WHY: Name is required.
        """
        entry = InstructorRosterEntry(
            name="",
            email="john@example.com",
            source_row=2
        )

        result = entry.validate()

        assert result is False
        assert entry.is_valid is False
        assert "name" in entry.validation_errors[0].lower()

    def test_instructor_entry_validation_missing_email(self):
        """
        Test validation fails for missing email.

        WHY: Email is required.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="",
            source_row=2
        )

        result = entry.validate()

        assert result is False
        assert "email" in entry.validation_errors[0].lower()

    def test_instructor_entry_validation_invalid_email(self):
        """
        Test validation fails for invalid email format.

        WHY: Email must be valid format.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="invalid-email",
            source_row=2
        )

        result = entry.validate()

        assert result is False
        assert "email" in entry.validation_errors[0].lower()

    def test_instructor_entry_validation_invalid_role(self):
        """
        Test validation fails for invalid role.

        WHY: Role must be valid enum value.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="john@example.com",
            role="professor",  # Invalid
            source_row=2
        )

        result = entry.validate()

        assert result is False
        assert "role" in entry.validation_errors[0].lower()

    def test_instructor_entry_to_dict(self):
        """
        Test serialization to dictionary.

        WHY: Entries need to be serialized for storage/transfer.
        """
        entry = InstructorRosterEntry(
            name="John Doe",
            email="john@example.com",
            tracks=["Backend"],
            source_row=2
        )
        entry.validate()

        result = entry.to_dict()

        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["tracks"] == ["Backend"]
        assert result["is_valid"] is True


# =============================================================================
# STUDENT ROSTER ENTRY TESTS
# =============================================================================

class TestStudentRosterEntry:
    """
    Test suite for StudentRosterEntry domain entity.

    WHY: StudentRosterEntry represents a parsed row from a student
    roster file. Validation ensures data quality before import.
    """

    def test_create_valid_student_entry(self):
        """
        Test creating a valid student entry.

        WHY: Basic happy path for student row.
        """
        entry = StudentRosterEntry(
            name="Jane Smith",
            email="jane@example.com",
            track="Backend Development",
            source_row=2
        )

        assert entry.name == "Jane Smith"
        assert entry.email == "jane@example.com"
        assert entry.track == "Backend Development"

    def test_student_entry_with_all_fields(self):
        """
        Test student entry with all optional fields.

        WHY: Roster files may include additional data.
        """
        entry = StudentRosterEntry(
            name="Jane Smith",
            email="jane@example.com",
            track="Backend Development",
            source_row=2,
            location="New York",
            instructor="john@example.com",
            group="Study Group A",
            employee_id="EMP123",
            department="Engineering",
            manager_email="manager@example.com",
            notes="Needs accommodations"
        )

        assert entry.location == "New York"
        assert entry.instructor == "john@example.com"
        assert entry.employee_id == "EMP123"

    def test_student_entry_validation_valid(self):
        """
        Test validation passes for valid entry.

        WHY: Valid data should pass validation.
        """
        entry = StudentRosterEntry(
            name="Jane Smith",
            email="jane@example.com",
            track="Backend",
            source_row=2
        )

        result = entry.validate()

        assert result is True
        assert entry.is_valid is True

    def test_student_entry_validation_missing_track(self):
        """
        Test validation fails for missing track.

        WHY: Track is required for students.
        """
        entry = StudentRosterEntry(
            name="Jane Smith",
            email="jane@example.com",
            track="",
            source_row=2
        )

        result = entry.validate()

        assert result is False
        assert "track" in entry.validation_errors[0].lower()

    def test_student_entry_validation_invalid_manager_email(self):
        """
        Test validation fails for invalid manager email.

        WHY: If provided, manager email must be valid.
        """
        entry = StudentRosterEntry(
            name="Jane Smith",
            email="jane@example.com",
            track="Backend",
            manager_email="invalid",
            source_row=2
        )

        result = entry.validate()

        assert result is False
        assert "manager" in entry.validation_errors[0].lower()


# =============================================================================
# FILE UPLOAD TESTS
# =============================================================================

class TestFileUpload:
    """
    Test suite for FileUpload domain entity.

    WHY: FileUpload tracks file metadata and processing status.
    """

    def test_create_file_upload(self):
        """
        Test creating a file upload record.

        WHY: Basic happy path for file upload tracking.
        """
        upload = FileUpload(
            original_filename="instructors.csv",
            file_size_bytes=1024,
            file_format=FileFormat.CSV,
            roster_type=RosterType.INSTRUCTOR
        )

        assert upload.original_filename == "instructors.csv"
        assert upload.file_format == FileFormat.CSV
        assert upload.status == FileUploadStatus.PENDING

    def test_file_upload_status_transitions(self):
        """
        Test file upload status updates.

        WHY: Status tracks processing progress.
        """
        upload = FileUpload(
            original_filename="students.xlsx",
            file_format=FileFormat.EXCEL_XLSX
        )

        assert upload.status == FileUploadStatus.PENDING

        upload.status = FileUploadStatus.PARSING
        assert upload.status == FileUploadStatus.PARSING

        upload.status = FileUploadStatus.PARSED
        upload.parsed_at = datetime.now()
        assert upload.parsed_at is not None

    def test_file_upload_to_dict(self):
        """
        Test serialization to dictionary.

        WHY: Uploads need to be serialized for API responses.
        """
        upload = FileUpload(
            original_filename="instructors.csv",
            file_format=FileFormat.CSV,
            roster_type=RosterType.INSTRUCTOR,
            total_rows=10,
            valid_rows=8,
            error_rows=2
        )

        result = upload.to_dict()

        assert result["original_filename"] == "instructors.csv"
        assert result["file_format"] == "csv"
        assert result["roster_type"] == "instructor"
        assert result["total_rows"] == 10


# =============================================================================
# PARSED ROSTER TESTS
# =============================================================================

class TestParsedRoster:
    """
    Test suite for ParsedRoster domain entity.

    WHY: ParsedRoster aggregates all parsed entries and statistics.
    """

    def test_create_instructor_parsed_roster(self):
        """
        Test creating parsed roster for instructors.

        WHY: Basic happy path for instructor roster.
        """
        roster = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            instructor_entries=[
                InstructorRosterEntry(name="John", email="john@example.com", source_row=2),
                InstructorRosterEntry(name="Jane", email="jane@example.com", source_row=3)
            ],
            source_headers=["Name", "Email"],
            total_rows=2,
            valid_rows=2
        )

        assert roster.roster_type == RosterType.INSTRUCTOR
        assert len(roster.instructor_entries) == 2
        assert roster.total_rows == 2

    def test_create_student_parsed_roster(self):
        """
        Test creating parsed roster for students.

        WHY: Basic happy path for student roster.
        """
        roster = ParsedRoster(
            roster_type=RosterType.STUDENT,
            student_entries=[
                StudentRosterEntry(name="Alice", email="alice@example.com", track="Backend", source_row=2),
                StudentRosterEntry(name="Bob", email="bob@example.com", track="Frontend", source_row=3)
            ],
            source_headers=["Name", "Email", "Track"],
            total_rows=2,
            valid_rows=2
        )

        assert roster.roster_type == RosterType.STUDENT
        assert len(roster.student_entries) == 2

    def test_parsed_roster_get_entries(self):
        """
        Test getting entries based on roster type.

        WHY: Helper method simplifies access.
        """
        roster = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            instructor_entries=[
                InstructorRosterEntry(name="John", email="john@example.com", source_row=2)
            ]
        )

        entries = roster.get_entries()

        assert len(entries) == 1
        assert entries[0].name == "John"

    def test_parsed_roster_get_valid_entries(self):
        """
        Test filtering valid entries.

        WHY: Only valid entries should be imported.
        """
        entry1 = InstructorRosterEntry(name="John", email="john@example.com", source_row=2)
        entry1.validate()

        entry2 = InstructorRosterEntry(name="", email="invalid", source_row=3)
        entry2.validate()

        roster = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            instructor_entries=[entry1, entry2],
            valid_rows=1,
            error_rows=1
        )

        valid = roster.get_valid_entries()
        invalid = roster.get_invalid_entries()

        assert len(valid) == 1
        assert len(invalid) == 1

    def test_parsed_roster_get_unique_tracks(self):
        """
        Test getting unique track names.

        WHY: Track names are used for cross-reference validation.
        """
        roster = ParsedRoster(
            roster_type=RosterType.STUDENT,
            student_entries=[
                StudentRosterEntry(name="Alice", email="a@example.com", track="Backend", source_row=2),
                StudentRosterEntry(name="Bob", email="b@example.com", track="Frontend", source_row=3),
                StudentRosterEntry(name="Carol", email="c@example.com", track="Backend", source_row=4)
            ]
        )

        tracks = roster.get_unique_tracks()

        assert len(tracks) == 2
        assert "Backend" in tracks
        assert "Frontend" in tracks

    def test_parsed_roster_has_errors(self):
        """
        Test error detection.

        WHY: Determines if roster can be imported.
        """
        roster_ok = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            error_rows=0
        )
        assert roster_ok.has_errors() is False

        roster_errors = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            error_rows=3
        )
        assert roster_errors.has_errors() is True

        roster_duplicates = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            error_rows=0,
            duplicate_emails={"john@example.com": [2, 5]}
        )
        assert roster_duplicates.has_errors() is True


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================

class TestValidationIssue:
    """
    Test suite for ValidationIssue value object.

    WHY: ValidationIssue provides detailed info about validation problems.
    """

    def test_create_validation_issue(self):
        """
        Test creating a validation issue.

        WHY: Basic happy path.
        """
        issue = ValidationIssue(
            row=5,
            column="email",
            severity=ValidationSeverity.ERROR,
            code="INVALID_EMAIL",
            message="Email format is invalid",
            value="not-an-email",
            suggestion="Use format: name@domain.com"
        )

        assert issue.row == 5
        assert issue.column == "email"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.code == "INVALID_EMAIL"

    def test_validation_issue_to_dict(self):
        """
        Test serialization.

        WHY: Issues need to be serialized for API responses.
        """
        issue = ValidationIssue(
            row=5,
            column="email",
            severity=ValidationSeverity.WARNING,
            code="DUPLICATE",
            message="Duplicate email"
        )

        result = issue.to_dict()

        assert result["row"] == 5
        assert result["severity"] == "warning"


class TestRosterValidationResult:
    """
    Test suite for RosterValidationResult domain entity.

    WHY: RosterValidationResult aggregates all validation findings.
    """

    def test_create_validation_result(self):
        """
        Test creating a validation result.

        WHY: Basic happy path.
        """
        result = RosterValidationResult(
            roster_type=RosterType.INSTRUCTOR,
            is_valid=True
        )

        assert result.is_valid is True
        assert result.error_count == 0

    def test_validation_result_add_error(self):
        """
        Test adding error issue.

        WHY: Errors should invalidate the roster.
        """
        result = RosterValidationResult(
            roster_type=RosterType.INSTRUCTOR,
            is_valid=True
        )

        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="MISSING_NAME",
            message="Name is required"
        ))

        assert result.is_valid is False
        assert result.error_count == 1

    def test_validation_result_add_warning(self):
        """
        Test adding warning issue.

        WHY: Warnings don't invalidate the roster.
        """
        result = RosterValidationResult(
            roster_type=RosterType.INSTRUCTOR,
            is_valid=True
        )

        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="MISSING_PHONE",
            message="Phone number is missing"
        ))

        assert result.is_valid is True  # Still valid
        assert result.warning_count == 1

    def test_validation_result_get_errors(self):
        """
        Test filtering errors.

        WHY: Users need to see only errors sometimes.
        """
        result = RosterValidationResult(roster_type=RosterType.INSTRUCTOR)

        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="E1",
            message="Error 1"
        ))
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="W1",
            message="Warning 1"
        ))
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="E2",
            message="Error 2"
        ))

        errors = result.get_errors()
        warnings = result.get_warnings()

        assert len(errors) == 2
        assert len(warnings) == 1


# =============================================================================
# IMPORT PROGRESS TESTS
# =============================================================================

class TestImportProgress:
    """
    Test suite for ImportProgress value object.

    WHY: ImportProgress enables progress tracking for large imports.
    """

    def test_create_import_progress(self):
        """
        Test creating import progress tracker.

        WHY: Basic happy path.
        """
        progress = ImportProgress(
            total_files=2,
            total_rows=100
        )

        assert progress.status == "pending"
        assert progress.total_files == 2
        assert progress.total_rows == 100

    def test_import_progress_overall(self):
        """
        Test calculating overall progress.

        WHY: Progress bar display needs percentage.
        """
        progress = ImportProgress(
            total_rows=100,
            processed_rows=25
        )

        assert progress.get_overall_progress() == 25.0

    def test_import_progress_to_dict(self):
        """
        Test serialization.

        WHY: Progress needs to be polled via API.
        """
        progress = ImportProgress(
            status="in_progress",
            current_step="Importing instructors",
            total_rows=100,
            processed_rows=50,
            success_rows=48,
            error_rows=2
        )

        result = progress.to_dict()

        assert result["status"] == "in_progress"
        assert result["overall_progress"] == 50.0
        assert result["success_rows"] == 48


# =============================================================================
# COLUMN ALIAS CONFIGURATION TESTS
# =============================================================================

class TestColumnAliasConfigurations:
    """
    Test suite for predefined column alias configurations.

    WHY: Verify alias configurations match expected column names.
    """

    def test_instructor_name_aliases(self):
        """
        Test instructor name column aliases.

        WHY: Common variations should be recognized.
        """
        name_alias = next(
            (a for a in INSTRUCTOR_COLUMN_ALIASES if a.target_field == "name"),
            None
        )

        assert name_alias is not None
        assert name_alias.required is True
        assert name_alias.matches("name")
        assert name_alias.matches("instructor_name")
        assert name_alias.matches("Full Name")

    def test_instructor_email_aliases(self):
        """
        Test instructor email column aliases.

        WHY: Common variations should be recognized.
        """
        email_alias = next(
            (a for a in INSTRUCTOR_COLUMN_ALIASES if a.target_field == "email"),
            None
        )

        assert email_alias is not None
        assert email_alias.required is True
        assert email_alias.matches("email")
        assert email_alias.matches("e-mail")
        assert email_alias.matches("email_address")

    def test_student_track_aliases(self):
        """
        Test student track column aliases.

        WHY: Common variations should be recognized.
        """
        track_alias = next(
            (a for a in STUDENT_COLUMN_ALIASES if a.target_field == "track"),
            None
        )

        assert track_alias is not None
        assert track_alias.required is True
        assert track_alias.matches("track")
        assert track_alias.matches("program")
        assert track_alias.matches("learning_path")


# =============================================================================
# EXCEPTION TESTS
# =============================================================================

class TestFileImportExceptions:
    """
    Test suite for custom file import exceptions.

    WHY: Exceptions must provide detailed error information.
    """

    def test_file_import_exception(self):
        """
        Test base FileImportException.

        WHY: Base exception establishes pattern.
        """
        exc = FileImportException(
            message="Import failed",
            code="IMPORT_ERROR",
            row=5,
            column="email"
        )

        assert exc.message == "Import failed"
        assert exc.row == 5
        assert exc.column == "email"

        result = exc.to_dict()
        assert result["row"] == 5
        assert result["column"] == "email"

    def test_unsupported_file_format_exception(self):
        """
        Test UnsupportedFileFormatException.

        WHY: Provides supported formats in error.
        """
        exc = UnsupportedFileFormatException(
            filename="data.pdf",
            detected_format="pdf"
        )

        assert exc.filename == "data.pdf"
        assert exc.detected_format == "pdf"
        assert "supported" in exc.message.lower()
        assert exc.context["supported_formats"] == ["csv", "xlsx", "xls", "json"]

    def test_missing_required_column_exception(self):
        """
        Test MissingRequiredColumnException.

        WHY: Shows available columns for debugging.
        """
        exc = MissingRequiredColumnException(
            column_name="email",
            available_columns=["Name", "Phone", "Department"]
        )

        assert exc.column_name == "email"
        assert "email" in exc.message
        assert len(exc.available_columns) == 3

    def test_invalid_data_exception(self):
        """
        Test InvalidDataException.

        WHY: Shows exact location and value of error.
        """
        exc = InvalidDataException(
            message="Invalid email format",
            row=5,
            column="email",
            value="not-an-email",
            expected="name@domain.com"
        )

        assert exc.row == 5
        assert exc.column == "email"
        assert exc.value == "not-an-email"
        assert exc.expected == "name@domain.com"

    def test_empty_file_exception(self):
        """
        Test EmptyFileException.

        WHY: Indicates file has no data.
        """
        exc = EmptyFileException(filename="empty.csv")

        assert exc.filename == "empty.csv"
        assert "empty" in exc.message.lower()

    def test_duplicate_entry_exception(self):
        """
        Test DuplicateEntryException.

        WHY: Shows which rows have duplicates.
        """
        exc = DuplicateEntryException(
            field="email",
            value="john@example.com",
            rows=[2, 5, 8]
        )

        assert exc.field == "email"
        assert exc.value == "john@example.com"
        assert exc.rows == [2, 5, 8]


# =============================================================================
# ENUMERATION TESTS
# =============================================================================

class TestFileImportEnumerations:
    """
    Test suite for file import enumerations.

    WHY: Enums must have expected values.
    """

    def test_file_format_values(self):
        """
        Test FileFormat enum values.

        WHY: Parser uses these values.
        """
        assert FileFormat.CSV.value == "csv"
        assert FileFormat.EXCEL_XLSX.value == "xlsx"
        assert FileFormat.EXCEL_XLS.value == "xls"
        assert FileFormat.JSON.value == "json"

    def test_roster_type_values(self):
        """
        Test RosterType enum values.

        WHY: Determines validation rules.
        """
        assert RosterType.INSTRUCTOR.value == "instructor"
        assert RosterType.STUDENT.value == "student"

    def test_file_upload_status_values(self):
        """
        Test FileUploadStatus enum values.

        WHY: Tracks processing progress.
        """
        assert FileUploadStatus.PENDING.value == "pending"
        assert FileUploadStatus.PARSING.value == "parsing"
        assert FileUploadStatus.COMPLETED.value == "completed"
        assert FileUploadStatus.ERROR.value == "error"

    def test_validation_severity_values(self):
        """
        Test ValidationSeverity enum values.

        WHY: Determines if roster can be imported.
        """
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.INFO.value == "info"
