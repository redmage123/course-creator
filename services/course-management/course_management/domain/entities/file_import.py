"""
File Import Domain Entities

BUSINESS CONTEXT:
This module defines domain entities for importing roster files (instructors,
students) and other structured data files into the project builder system.

WHY THIS EXISTS:
Organization administrators often have existing spreadsheets with instructor
and student information. Rather than manually entering each person, they can
upload these files and have the system parse them automatically. This module
provides the domain entities for:
1. Representing parsed roster data
2. Tracking file upload sessions
3. Handling column mapping for flexible file formats
4. Validating parsed data before import

WHAT THIS MODULE PROVIDES:
- FileUpload: Metadata for an uploaded file
- ColumnMapping: Maps source columns to target fields
- ParsedRoster: Container for parsed roster data
- InstructorRosterEntry: Parsed instructor from roster file
- StudentRosterEntry: Parsed student from roster file
- RosterValidationResult: Results of validating parsed roster
- ImportProgress: Tracks multi-file import progress

HOW TO USE:
1. Create FileUpload when user uploads a file
2. Use RosterFileParser to create ParsedRoster
3. Validate with RosterValidationResult
4. Convert to InstructorSpec/StudentSpec for ProjectBuilderSpec

SUPPORTED FILE FORMATS:
- CSV (.csv) - Comma-separated values
- Excel (.xlsx, .xls) - Microsoft Excel spreadsheets
- JSON (.json) - JSON array of objects

COLUMN AUTO-DETECTION:
The system supports flexible column naming. For example, instructor email
can be in columns named: "email", "instructor_email", "email_address", "e-mail"

@module file_import
@author Course Creator Platform
@version 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from uuid import UUID, uuid4
from enum import Enum


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class FileImportException(Exception):
    """
    Base exception for all file import domain errors.

    WHY: Provides a common base class for catching all file import
    related errors while maintaining specific error types for different
    failure scenarios (format errors, validation errors, etc.).

    WHAT: Base exception that all file import exceptions inherit from.
    Includes error code, row number (if applicable), and context.

    HOW: Catch FileImportException to handle any import error,
    or catch specific subclasses for targeted error handling.
    """

    def __init__(
        self,
        message: str,
        code: str = "FILE_IMPORT_ERROR",
        row: Optional[int] = None,
        column: Optional[str] = None,
        context: Dict[str, Any] = None
    ):
        """
        Initialize file import exception.

        Args:
            message: Human-readable error description
            code: Machine-readable error code for programmatic handling
            row: Row number where error occurred (1-indexed, or None)
            column: Column name where error occurred (or None)
            context: Additional context data for debugging
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.row = row
        self.column = column
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "error": self.code,
            "message": self.message,
            "context": self.context
        }
        if self.row is not None:
            result["row"] = self.row
        if self.column is not None:
            result["column"] = self.column
        return result


class UnsupportedFileFormatException(FileImportException):
    """
    Raised when file format is not supported.

    WHY: Users may upload files in formats we don't support.
    This exception provides clear feedback about supported formats.

    WHAT: Indicates the uploaded file type is not in the supported list.

    HOW: Raised early in parsing when file type is determined.
    """

    def __init__(self, filename: str, detected_format: str = None, context: Dict[str, Any] = None):
        ctx = context or {}
        ctx["filename"] = filename
        ctx["detected_format"] = detected_format
        ctx["supported_formats"] = ["csv", "xlsx", "xls", "json"]
        message = f"Unsupported file format: {detected_format or 'unknown'}. Supported formats: CSV, Excel (.xlsx, .xls), JSON"
        super().__init__(message, "UNSUPPORTED_FILE_FORMAT", context=ctx)
        self.filename = filename
        self.detected_format = detected_format


class MissingRequiredColumnException(FileImportException):
    """
    Raised when required column is not found in file.

    WHY: Roster files must have certain columns (name, email).
    This exception identifies which required column is missing.

    WHAT: Indicates a required column could not be found or mapped.

    HOW: Raised during column mapping when required field has no source.
    """

    def __init__(self, column_name: str, available_columns: List[str] = None, context: Dict[str, Any] = None):
        ctx = context or {}
        ctx["missing_column"] = column_name
        if available_columns:
            ctx["available_columns"] = available_columns
        message = f"Required column '{column_name}' not found in file"
        if available_columns:
            message += f". Available columns: {', '.join(available_columns)}"
        super().__init__(message, "MISSING_REQUIRED_COLUMN", column=column_name, context=ctx)
        self.column_name = column_name
        self.available_columns = available_columns or []


class InvalidDataException(FileImportException):
    """
    Raised when data in a cell is invalid.

    WHY: Data validation catches issues like invalid email formats,
    missing values in required fields, or invalid enum values.

    WHAT: Indicates specific data in a specific cell is invalid.

    HOW: Raised during row parsing when cell data fails validation.
    """

    def __init__(
        self,
        message: str,
        row: int,
        column: str,
        value: Any = None,
        expected: str = None,
        context: Dict[str, Any] = None
    ):
        ctx = context or {}
        if value is not None:
            ctx["value"] = str(value)
        if expected:
            ctx["expected"] = expected
        super().__init__(message, "INVALID_DATA", row=row, column=column, context=ctx)
        self.value = value
        self.expected = expected


class EmptyFileException(FileImportException):
    """
    Raised when uploaded file is empty.

    WHY: Empty files indicate user error (wrong file, truncated upload).
    Clear feedback helps users identify the issue quickly.

    WHAT: Indicates the file contains no data rows.

    HOW: Raised after parsing when no data rows are found.
    """

    def __init__(self, filename: str, context: Dict[str, Any] = None):
        ctx = context or {}
        ctx["filename"] = filename
        message = f"File '{filename}' is empty or contains only headers"
        super().__init__(message, "EMPTY_FILE", context=ctx)
        self.filename = filename


class DuplicateEntryException(FileImportException):
    """
    Raised when duplicate entries are found (e.g., same email twice).

    WHY: Duplicate entries can cause issues during import. Users need
    to know which entries are duplicated so they can fix their files.

    WHAT: Indicates duplicate entries based on unique field (email).

    HOW: Raised during validation when duplicates are detected.
    """

    def __init__(
        self,
        field: str,
        value: str,
        rows: List[int],
        context: Dict[str, Any] = None
    ):
        ctx = context or {}
        ctx["duplicate_field"] = field
        ctx["duplicate_value"] = value
        ctx["duplicate_rows"] = rows
        message = f"Duplicate {field} '{value}' found in rows {rows}"
        super().__init__(message, "DUPLICATE_ENTRY", context=ctx)
        self.field = field
        self.value = value
        self.rows = rows


# =============================================================================
# ENUMERATIONS
# =============================================================================

class FileFormat(str, Enum):
    """
    Supported file formats for roster import.

    WHY: Different file formats require different parsing logic.
    This enum enables format-specific handling.

    WHAT: Enumerates all supported file formats.

    HOW: Detected from file extension or content, used to select parser.
    """
    CSV = "csv"
    EXCEL_XLSX = "xlsx"
    EXCEL_XLS = "xls"
    JSON = "json"


class RosterType(str, Enum):
    """
    Types of roster files.

    WHY: Instructor and student rosters have different required
    fields and validation rules.

    WHAT: Distinguishes between roster types for appropriate validation.

    HOW: Set during upload, determines column mapping and validation.
    """
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class FileUploadStatus(str, Enum):
    """
    Status of a file upload.

    WHY: File uploads go through multiple stages (upload → parse → validate → import).
    Status tracking enables progress display and error recovery.

    WHAT: Tracks current state of file processing.

    HOW: Updated as file progresses through processing pipeline.
    """
    PENDING = "pending"        # File received, not yet parsed
    PARSING = "parsing"        # Currently parsing file
    PARSED = "parsed"          # Parsing complete, awaiting validation
    VALIDATING = "validating"  # Currently validating data
    VALIDATED = "validated"    # Validation complete, ready for import
    IMPORTING = "importing"    # Currently importing data
    COMPLETED = "completed"    # Import complete
    ERROR = "error"            # Error occurred


class ValidationSeverity(str, Enum):
    """
    Severity levels for validation issues.

    WHY: Some issues are errors (must fix), others are warnings
    (can proceed but may have issues).

    WHAT: Categorizes validation issues by severity.

    HOW: Used in validation results to help users prioritize fixes.
    """
    ERROR = "error"      # Must be fixed before import
    WARNING = "warning"  # Can proceed, but may cause issues
    INFO = "info"        # Informational (e.g., "5 rows parsed")


# =============================================================================
# COLUMN MAPPING VALUE OBJECTS
# =============================================================================

@dataclass
class ColumnAlias:
    """
    Alias configuration for a column.

    WHY: Users have different naming conventions for columns.
    "Email", "email", "E-Mail", "email_address" all mean the same thing.

    WHAT: Maps multiple possible source names to a target field.

    HOW: Used by column auto-detection to find matching columns.
    """

    # Target field name (our internal name)
    target_field: str

    # Possible source column names (case-insensitive)
    aliases: List[str] = field(default_factory=list)

    # Is this field required?
    required: bool = False

    # Default value if not found and not required
    default_value: Any = None

    def matches(self, column_name: str) -> bool:
        """
        Check if a column name matches this alias.

        WHY: Enables flexible column matching with different naming conventions.

        WHAT: Returns True if column_name matches any alias.

        HOW: Case-insensitive comparison, strips whitespace.
        """
        normalized = column_name.lower().strip()
        return any(alias.lower().strip() == normalized for alias in self.aliases)


@dataclass
class ColumnMapping:
    """
    Mapping from source columns to target fields.

    WHY: After auto-detection or manual configuration, we need a
    concrete mapping to use during parsing.

    WHAT: Maps each source column index/name to target field name.

    HOW: Created by auto-detection or manual configuration,
    used by parser to extract field values.
    """

    # Maps target field name to source column name
    field_to_source: Dict[str, str] = field(default_factory=dict)

    # Source columns that were not mapped (for display to user)
    unmapped_columns: List[str] = field(default_factory=list)

    # Confidence score (0-1) for auto-detected mapping
    confidence: float = 1.0

    # Whether mapping was auto-detected or manual
    auto_detected: bool = True

    def get_source_column(self, field_name: str) -> Optional[str]:
        """Get source column name for a field."""
        return self.field_to_source.get(field_name)

    def has_field(self, field_name: str) -> bool:
        """Check if field is mapped."""
        return field_name in self.field_to_source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field_to_source": self.field_to_source,
            "unmapped_columns": self.unmapped_columns,
            "confidence": self.confidence,
            "auto_detected": self.auto_detected
        }


# =============================================================================
# INSTRUCTOR COLUMN ALIASES
# =============================================================================

INSTRUCTOR_COLUMN_ALIASES = [
    ColumnAlias(
        target_field="name",
        aliases=["name", "instructor_name", "full_name", "instructor", "full name", "instructor name"],
        required=True
    ),
    ColumnAlias(
        target_field="email",
        aliases=["email", "instructor_email", "email_address", "e-mail", "mail", "instructor email"],
        required=True
    ),
    ColumnAlias(
        target_field="tracks",
        aliases=["tracks", "track", "assigned_tracks", "teaching", "courses", "assigned tracks", "track assignment"],
        required=False,
        default_value=[]
    ),
    ColumnAlias(
        target_field="role",
        aliases=["role", "instructor_role", "position", "title", "instructor role"],
        required=False,
        default_value="instructor"
    ),
    ColumnAlias(
        target_field="available_days",
        aliases=["available_days", "days", "availability", "available days", "working days"],
        required=False,
        default_value=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    ),
    ColumnAlias(
        target_field="start_date",
        aliases=["start_date", "start", "from_date", "start date", "from date", "available from"],
        required=False
    ),
    ColumnAlias(
        target_field="end_date",
        aliases=["end_date", "end", "to_date", "end date", "to date", "available until"],
        required=False
    ),
    ColumnAlias(
        target_field="phone",
        aliases=["phone", "phone_number", "mobile", "telephone", "phone number", "contact"],
        required=False
    ),
    ColumnAlias(
        target_field="department",
        aliases=["department", "dept", "team", "group"],
        required=False
    ),
    ColumnAlias(
        target_field="notes",
        aliases=["notes", "comments", "remarks", "additional_info", "additional info"],
        required=False
    )
]


# =============================================================================
# STUDENT COLUMN ALIASES
# =============================================================================

STUDENT_COLUMN_ALIASES = [
    ColumnAlias(
        target_field="name",
        aliases=["name", "student_name", "full_name", "student", "full name", "student name", "learner"],
        required=True
    ),
    ColumnAlias(
        target_field="email",
        aliases=["email", "student_email", "email_address", "e-mail", "mail", "student email"],
        required=True
    ),
    ColumnAlias(
        target_field="track",
        aliases=["track", "program", "learning_path", "course", "track name", "learning path", "enrolled track"],
        required=True
    ),
    ColumnAlias(
        target_field="location",
        aliases=["location", "site", "office", "sub_project", "cohort", "location name", "training location"],
        required=False
    ),
    ColumnAlias(
        target_field="instructor",
        aliases=["instructor", "preferred_instructor", "assigned_instructor", "instructor email", "preferred instructor"],
        required=False
    ),
    ColumnAlias(
        target_field="group",
        aliases=["group", "study_group", "team", "cohort_group", "study group", "group name"],
        required=False
    ),
    ColumnAlias(
        target_field="employee_id",
        aliases=["employee_id", "id", "student_id", "emp_id", "employee id", "student id"],
        required=False
    ),
    ColumnAlias(
        target_field="department",
        aliases=["department", "dept", "team", "business_unit", "business unit"],
        required=False
    ),
    ColumnAlias(
        target_field="manager_email",
        aliases=["manager_email", "manager", "supervisor", "manager email", "reports_to", "reports to"],
        required=False
    ),
    ColumnAlias(
        target_field="notes",
        aliases=["notes", "comments", "remarks", "special_requirements", "special requirements"],
        required=False
    )
]


# =============================================================================
# PARSED ENTRY VALUE OBJECTS
# =============================================================================

@dataclass
class InstructorRosterEntry:
    """
    A parsed instructor entry from a roster file.

    WHY: Raw file data needs to be transformed into a structured
    format before conversion to InstructorSpec.

    WHAT: Contains all parsed fields for one instructor row.

    HOW: Created by RosterFileParser for each row in instructor roster.
    """

    # Required fields
    name: str
    email: str

    # Row number in source file (for error reporting)
    source_row: int = 0

    # Optional fields
    tracks: List[str] = field(default_factory=list)
    role: str = "instructor"
    available_days: List[str] = field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    start_date: Optional[str] = None  # String from file, converted later
    end_date: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None

    # Validation state
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    # Raw data (for debugging)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validate this entry.

        WHY: Each entry needs validation before import to catch issues
        like invalid email format or missing required fields.

        WHAT: Validates name, email, and optional field formats.

        HOW: Called after parsing, populates validation_errors list.

        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []

        if not self.name or not self.name.strip():
            self.validation_errors.append("Name is required")

        if not self.email or "@" not in self.email:
            self.validation_errors.append("Valid email is required")

        # Validate role
        valid_roles = ["instructor", "lead_instructor", "teaching_assistant"]
        if self.role and self.role not in valid_roles:
            self.validation_errors.append(f"Invalid role: {self.role}. Must be one of {valid_roles}")

        self.is_valid = len(self.validation_errors) == 0
        return self.is_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "email": self.email,
            "source_row": self.source_row,
            "tracks": self.tracks,
            "role": self.role,
            "available_days": self.available_days,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "phone": self.phone,
            "department": self.department,
            "notes": self.notes,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors
        }


@dataclass
class StudentRosterEntry:
    """
    A parsed student entry from a roster file.

    WHY: Raw file data needs to be transformed into a structured
    format before conversion to StudentSpec.

    WHAT: Contains all parsed fields for one student row.

    HOW: Created by RosterFileParser for each row in student roster.
    """

    # Required fields
    name: str
    email: str
    track: str

    # Row number in source file (for error reporting)
    source_row: int = 0

    # Optional fields
    location: Optional[str] = None
    instructor: Optional[str] = None  # Preferred instructor email
    group: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    manager_email: Optional[str] = None
    notes: Optional[str] = None

    # Validation state
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    # Raw data (for debugging)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validate this entry.

        WHY: Each entry needs validation before import to catch issues
        like invalid email format or missing required fields.

        WHAT: Validates name, email, track, and optional field formats.

        HOW: Called after parsing, populates validation_errors list.

        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []

        if not self.name or not self.name.strip():
            self.validation_errors.append("Name is required")

        if not self.email or "@" not in self.email:
            self.validation_errors.append("Valid email is required")

        if not self.track or not self.track.strip():
            self.validation_errors.append("Track assignment is required")

        # Validate manager email if provided
        if self.manager_email and "@" not in self.manager_email:
            self.validation_errors.append("Invalid manager email format")

        self.is_valid = len(self.validation_errors) == 0
        return self.is_valid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "email": self.email,
            "track": self.track,
            "source_row": self.source_row,
            "location": self.location,
            "instructor": self.instructor,
            "group": self.group,
            "employee_id": self.employee_id,
            "department": self.department,
            "manager_email": self.manager_email,
            "notes": self.notes,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors
        }


# =============================================================================
# FILE UPLOAD AND PARSING ENTITIES
# =============================================================================

@dataclass
class FileUpload:
    """
    Metadata for an uploaded file.

    WHY: Tracks file through processing pipeline, stores original
    file info and processing status.

    WHAT: Contains file metadata, processing status, and results.

    HOW: Created when file is uploaded, updated as processing progresses.
    """

    # Identification
    id: UUID = field(default_factory=uuid4)
    session_id: Optional[UUID] = None  # Project builder session

    # File metadata
    original_filename: str = ""
    file_size_bytes: int = 0
    file_format: Optional[FileFormat] = None
    roster_type: Optional[RosterType] = None

    # Processing status
    status: FileUploadStatus = FileUploadStatus.PENDING
    error_message: Optional[str] = None

    # Column mapping (after detection)
    column_mapping: Optional[ColumnMapping] = None

    # Parse results
    total_rows: int = 0
    valid_rows: int = 0
    error_rows: int = 0

    # Timestamps
    uploaded_at: datetime = field(default_factory=datetime.now)
    parsed_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # User who uploaded
    uploaded_by: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id) if self.session_id else None,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "file_format": self.file_format.value if self.file_format else None,
            "roster_type": self.roster_type.value if self.roster_type else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "column_mapping": self.column_mapping.to_dict() if self.column_mapping else None,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "error_rows": self.error_rows,
            "uploaded_at": self.uploaded_at.isoformat(),
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "uploaded_by": str(self.uploaded_by) if self.uploaded_by else None
        }


@dataclass
class ParsedRoster:
    """
    Container for parsed roster data.

    WHY: Aggregates all parsed entries with validation summary,
    enabling display of parse results to user for review.

    WHAT: Contains parsed entries, column mapping, and validation summary.

    HOW: Created by RosterFileParser after parsing file.
    """

    # File reference
    file_upload_id: UUID = field(default_factory=uuid4)
    roster_type: RosterType = RosterType.INSTRUCTOR

    # Column mapping used
    column_mapping: ColumnMapping = field(default_factory=ColumnMapping)

    # Parsed entries (one of these will be populated based on roster_type)
    instructor_entries: List[InstructorRosterEntry] = field(default_factory=list)
    student_entries: List[StudentRosterEntry] = field(default_factory=list)

    # Headers from file
    source_headers: List[str] = field(default_factory=list)

    # Summary statistics
    total_rows: int = 0
    valid_rows: int = 0
    error_rows: int = 0
    skipped_rows: int = 0  # Empty rows

    # Validation issues
    validation_issues: List[Dict[str, Any]] = field(default_factory=list)

    # Duplicate detection
    duplicate_emails: Dict[str, List[int]] = field(default_factory=dict)

    # Parsing metadata
    parsed_at: datetime = field(default_factory=datetime.now)
    parse_duration_ms: int = 0

    def get_entries(self) -> List[Any]:
        """Get entries based on roster type."""
        if self.roster_type == RosterType.INSTRUCTOR:
            return self.instructor_entries
        return self.student_entries

    def get_valid_entries(self) -> List[Any]:
        """Get only valid entries."""
        entries = self.get_entries()
        return [e for e in entries if e.is_valid]

    def get_invalid_entries(self) -> List[Any]:
        """Get only invalid entries."""
        entries = self.get_entries()
        return [e for e in entries if not e.is_valid]

    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        return self.error_rows > 0 or len(self.duplicate_emails) > 0

    def has_duplicates(self) -> bool:
        """
        Check if there are any duplicate emails in the roster.

        WHY: Quick check for data quality issues.
        WHAT: Returns True if duplicate_emails dict is non-empty.
        HOW: Checks length of duplicate_emails dictionary.

        Returns:
            True if duplicate emails exist, False otherwise.
        """
        return len(self.duplicate_emails) > 0

    def get_unique_tracks(self) -> Set[str]:
        """Get unique track names from entries."""
        if self.roster_type == RosterType.INSTRUCTOR:
            tracks = set()
            for entry in self.instructor_entries:
                tracks.update(entry.tracks)
            return tracks
        else:
            return {e.track for e in self.student_entries if e.track}

    def get_unique_locations(self) -> Set[str]:
        """Get unique location names from student entries."""
        if self.roster_type == RosterType.STUDENT:
            return {e.location for e in self.student_entries if e.location}
        return set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_upload_id": str(self.file_upload_id),
            "roster_type": self.roster_type.value,
            "column_mapping": self.column_mapping.to_dict(),
            "instructor_entries": [e.to_dict() for e in self.instructor_entries],
            "student_entries": [e.to_dict() for e in self.student_entries],
            "source_headers": self.source_headers,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "error_rows": self.error_rows,
            "skipped_rows": self.skipped_rows,
            "validation_issues": self.validation_issues,
            "duplicate_emails": self.duplicate_emails,
            "parsed_at": self.parsed_at.isoformat(),
            "parse_duration_ms": self.parse_duration_ms,
            "unique_tracks": list(self.get_unique_tracks()),
            "unique_locations": list(self.get_unique_locations())
        }


# =============================================================================
# VALIDATION RESULT VALUE OBJECTS
# =============================================================================

@dataclass
class ValidationIssue:
    """
    A single validation issue found in roster data.

    WHY: Detailed validation issues help users fix their files.
    Each issue has location, severity, and suggested fix.

    WHAT: Represents one validation problem with context.

    HOW: Created during validation, collected in RosterValidationResult.
    """

    # Issue identification
    id: UUID = field(default_factory=uuid4)

    # Location in file
    row: Optional[int] = None
    column: Optional[str] = None

    # Issue details
    severity: ValidationSeverity = ValidationSeverity.ERROR
    code: str = ""  # Machine-readable code
    message: str = ""  # Human-readable description
    value: Optional[str] = None  # The problematic value

    # Suggested fix
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "row": self.row,
            "column": self.column,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "value": self.value,
            "suggestion": self.suggestion
        }


@dataclass
class RosterValidationResult:
    """
    Complete validation results for a parsed roster.

    WHY: Users need comprehensive validation feedback before import,
    showing all issues, duplicates, and cross-reference problems.

    WHAT: Aggregates all validation issues with summary statistics.

    HOW: Created by validator service, presented to user for review.
    """

    # Roster reference
    roster_id: UUID = field(default_factory=uuid4)
    roster_type: RosterType = RosterType.INSTRUCTOR

    # Overall result
    is_valid: bool = True  # True if no errors (warnings OK)

    # Issue breakdown
    issues: List[ValidationIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    # Cross-reference validation (against existing spec)
    unknown_tracks: List[str] = field(default_factory=list)
    unknown_locations: List[str] = field(default_factory=list)

    # Duplicate detection
    duplicate_emails: List[Dict[str, Any]] = field(default_factory=list)

    # Validation metadata
    validated_at: datetime = field(default_factory=datetime.now)
    validation_duration_ms: int = 0

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue and update counts."""
        self.issues.append(issue)

        if issue.severity == ValidationSeverity.ERROR:
            self.error_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1

    def get_errors(self) -> List[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def get_warnings(self) -> List[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "roster_id": str(self.roster_id),
            "roster_type": self.roster_type.value,
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "unknown_tracks": self.unknown_tracks,
            "unknown_locations": self.unknown_locations,
            "duplicate_emails": self.duplicate_emails,
            "validated_at": self.validated_at.isoformat(),
            "validation_duration_ms": self.validation_duration_ms
        }


# =============================================================================
# IMPORT PROGRESS TRACKING
# =============================================================================

@dataclass
class ImportProgress:
    """
    Tracks progress of multi-file import operation.

    WHY: Large imports take time. Progress tracking enables progress
    bars and allows users to see what's happening.

    WHAT: Tracks overall and per-file progress with timing.

    HOW: Updated by import service, polled by frontend for display.
    """

    # Session reference
    session_id: UUID = field(default_factory=uuid4)

    # Overall status
    status: str = "pending"  # pending, in_progress, completed, error
    current_step: str = ""
    current_step_progress: float = 0.0  # 0-100

    # File processing
    total_files: int = 0
    processed_files: int = 0
    current_file: Optional[str] = None

    # Row processing
    total_rows: int = 0
    processed_rows: int = 0
    success_rows: int = 0
    error_rows: int = 0

    # Entity creation
    entities_created: Dict[str, int] = field(default_factory=lambda: {
        "instructors": 0,
        "students": 0,
        "enrollments": 0
    })

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_remaining_seconds: Optional[int] = None

    # Errors encountered
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def get_overall_progress(self) -> float:
        """Get overall progress as percentage (0-100)."""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": str(self.session_id),
            "status": self.status,
            "current_step": self.current_step,
            "current_step_progress": self.current_step_progress,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "current_file": self.current_file,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "success_rows": self.success_rows,
            "error_rows": self.error_rows,
            "entities_created": self.entities_created,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "overall_progress": self.get_overall_progress(),
            "errors": self.errors
        }
