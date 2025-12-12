"""
Roster File Parser Service

BUSINESS CONTEXT:
This service provides functionality to parse instructor and student roster files
from various formats (CSV, Excel, JSON) for the AI-powered project builder.
Organization admins can upload roster files to quickly populate their training
programs with instructors and students.

WHY THIS EXISTS:
Manually entering instructor and student information one by one is time-consuming
for large training programs. Organizations often have existing HR spreadsheets
or employee databases that can be exported. This service:
1. Accepts multiple file formats (CSV, Excel, JSON)
2. Auto-detects column mappings from various naming conventions
3. Validates data before import (email format, required fields)
4. Provides detailed error feedback for data corrections

WHAT THIS MODULE PROVIDES:
- RosterFileParser: Main parser class for roster files
- parse_instructor_roster: Parse instructor roster files
- parse_student_roster: Parse student roster files
- auto_detect_columns: Detect column mappings automatically
- validate_roster: Validate parsed roster entries

HOW TO USE:
    parser = RosterFileParser()

    # Parse instructor roster
    result = parser.parse_instructor_roster(file_bytes, 'instructors.csv')
    for entry in result.get_valid_entries():
        print(f"Instructor: {entry.name} ({entry.email})")

    # Parse student roster
    result = parser.parse_student_roster(file_bytes, 'students.xlsx')
    for entry in result.get_valid_entries():
        print(f"Student: {entry.name} enrolled in {entry.track}")

SUPPORTED FILE FORMATS:
- CSV (.csv): Comma-separated values with header row
- Excel (.xlsx, .xls): Microsoft Excel spreadsheets
- JSON (.json): Array of objects with field names

COLUMN AUTO-DETECTION:
The parser recognizes common column name variations:
- Name: "name", "full_name", "instructor_name", "student_name", etc.
- Email: "email", "e-mail", "email_address", "instructor_email", etc.
- Track: "track", "program", "learning_path", "enrolled_track", etc.

@module roster_file_parser
@author Course Creator Platform
@version 1.0.0
"""

import csv
import io
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from course_management.domain.entities.file_import import (
    # Entry entities
    InstructorRosterEntry,
    StudentRosterEntry,
    # Container entities
    ParsedRoster,
    ColumnMapping,
    ColumnAlias,
    FileUpload,
    # Alias configurations
    INSTRUCTOR_COLUMN_ALIASES,
    STUDENT_COLUMN_ALIASES,
    # Enumerations
    FileFormat,
    RosterType,
    FileUploadStatus,
    # Exceptions
    FileImportException,
    UnsupportedFileFormatException,
    MissingRequiredColumnException,
    InvalidDataException,
    EmptyFileException,
    DuplicateEntryException
)

logger = logging.getLogger(__name__)


class RosterFileParser:
    """
    Service for parsing instructor and student roster files.

    BUSINESS REQUIREMENTS:
    - Support CSV, Excel (XLSX/XLS), and JSON formats
    - Auto-detect column mappings from various naming conventions
    - Validate all entries for required fields and format
    - Detect duplicate emails within the file
    - Provide detailed error feedback with row numbers
    - Generate template files for download

    DESIGN PRINCIPLES:
    - Fail fast on file format issues
    - Collect all validation errors (don't stop at first)
    - Case-insensitive column matching
    - Flexible parsing with sensible defaults
    """

    def __init__(self):
        """
        Initialize the roster file parser.

        WHY: Sets up column alias configurations for auto-detection.
        """
        self.instructor_aliases = INSTRUCTOR_COLUMN_ALIASES
        self.student_aliases = STUDENT_COLUMN_ALIASES

    # =========================================================================
    # PUBLIC METHODS - Main Entry Points
    # =========================================================================

    def parse_instructor_roster(
        self,
        file_content: bytes,
        filename: str,
        manual_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedRoster:
        """
        Parse an instructor roster file.

        WHY: Main entry point for parsing instructor files. Handles format
        detection, parsing, and validation in one call.

        WHAT: Parses file content into InstructorRosterEntry objects with
        validation and duplicate detection.

        HOW:
        1. Detect file format from filename
        2. Parse file content into raw data
        3. Auto-detect or apply column mapping
        4. Convert rows to InstructorRosterEntry objects
        5. Validate all entries
        6. Detect duplicate emails
        7. Return ParsedRoster with results

        Args:
            file_content: Raw file bytes
            filename: Original filename (used for format detection)
            manual_mapping: Optional manual column mapping (field -> source_col)

        Returns:
            ParsedRoster containing parsed and validated entries

        Raises:
            UnsupportedFileFormatException: If file format is not supported
            EmptyFileException: If file contains no data
        """
        start_time = time.time()
        logger.info(f"Parsing instructor roster: {filename}")

        # Detect format
        file_format = self._detect_format(filename)
        logger.debug(f"Detected format: {file_format.value}")

        # Parse raw data
        headers, rows = self._parse_raw_data(file_content, file_format, filename)

        if not rows:
            raise EmptyFileException(filename)

        # Detect column mapping
        if manual_mapping:
            column_mapping = ColumnMapping(
                field_to_source=manual_mapping,
                auto_detected=False
            )
        else:
            column_mapping = self._auto_detect_columns(
                headers, self.instructor_aliases
            )

        # Validate required columns
        self._validate_required_columns(
            column_mapping,
            self.instructor_aliases,
            headers,
            filename
        )

        # Parse entries
        instructor_entries = []
        for row_idx, row in enumerate(rows, start=2):  # Row 2+ (after header)
            entry = self._parse_instructor_row(
                row, headers, column_mapping, row_idx
            )
            if entry:
                instructor_entries.append(entry)

        # Validate all entries
        valid_count = 0
        error_count = 0
        for entry in instructor_entries:
            if entry.validate():
                valid_count += 1
            else:
                error_count += 1

        # Detect duplicates
        duplicate_emails = self._detect_duplicate_emails(instructor_entries)

        # Build result
        parse_duration = int((time.time() - start_time) * 1000)

        result = ParsedRoster(
            roster_type=RosterType.INSTRUCTOR,
            column_mapping=column_mapping,
            instructor_entries=instructor_entries,
            source_headers=headers,
            total_rows=len(rows),
            valid_rows=valid_count,
            error_rows=error_count,
            skipped_rows=len(rows) - len(instructor_entries),
            duplicate_emails=duplicate_emails,
            parse_duration_ms=parse_duration
        )

        logger.info(
            f"Parsed instructor roster: {result.total_rows} rows, "
            f"{result.valid_rows} valid, {result.error_rows} errors"
        )

        return result

    def parse_student_roster(
        self,
        file_content: bytes,
        filename: str,
        manual_mapping: Optional[Dict[str, str]] = None
    ) -> ParsedRoster:
        """
        Parse a student roster file.

        WHY: Main entry point for parsing student files. Handles format
        detection, parsing, and validation in one call.

        WHAT: Parses file content into StudentRosterEntry objects with
        validation and duplicate detection.

        HOW:
        1. Detect file format from filename
        2. Parse file content into raw data
        3. Auto-detect or apply column mapping
        4. Convert rows to StudentRosterEntry objects
        5. Validate all entries
        6. Detect duplicate emails
        7. Return ParsedRoster with results

        Args:
            file_content: Raw file bytes
            filename: Original filename (used for format detection)
            manual_mapping: Optional manual column mapping (field -> source_col)

        Returns:
            ParsedRoster containing parsed and validated entries

        Raises:
            UnsupportedFileFormatException: If file format is not supported
            EmptyFileException: If file contains no data
        """
        start_time = time.time()
        logger.info(f"Parsing student roster: {filename}")

        # Detect format
        file_format = self._detect_format(filename)
        logger.debug(f"Detected format: {file_format.value}")

        # Parse raw data
        headers, rows = self._parse_raw_data(file_content, file_format, filename)

        if not rows:
            raise EmptyFileException(filename)

        # Detect column mapping
        if manual_mapping:
            column_mapping = ColumnMapping(
                field_to_source=manual_mapping,
                auto_detected=False
            )
        else:
            column_mapping = self._auto_detect_columns(
                headers, self.student_aliases
            )

        # Validate required columns
        self._validate_required_columns(
            column_mapping,
            self.student_aliases,
            headers,
            filename
        )

        # Parse entries
        student_entries = []
        for row_idx, row in enumerate(rows, start=2):  # Row 2+ (after header)
            entry = self._parse_student_row(
                row, headers, column_mapping, row_idx
            )
            if entry:
                student_entries.append(entry)

        # Validate all entries
        valid_count = 0
        error_count = 0
        for entry in student_entries:
            if entry.validate():
                valid_count += 1
            else:
                error_count += 1

        # Detect duplicates
        duplicate_emails = self._detect_duplicate_emails(student_entries)

        # Build result
        parse_duration = int((time.time() - start_time) * 1000)

        result = ParsedRoster(
            roster_type=RosterType.STUDENT,
            column_mapping=column_mapping,
            student_entries=student_entries,
            source_headers=headers,
            total_rows=len(rows),
            valid_rows=valid_count,
            error_rows=error_count,
            skipped_rows=len(rows) - len(student_entries),
            duplicate_emails=duplicate_emails,
            parse_duration_ms=parse_duration
        )

        logger.info(
            f"Parsed student roster: {result.total_rows} rows, "
            f"{result.valid_rows} valid, {result.error_rows} errors"
        )

        return result

    # =========================================================================
    # FORMAT DETECTION AND RAW PARSING
    # =========================================================================

    def _detect_format(self, filename: str) -> FileFormat:
        """
        Detect file format from filename extension.

        WHY: Different formats require different parsing strategies.

        WHAT: Returns FileFormat enum based on extension.

        HOW: Examines file extension (case-insensitive).

        Args:
            filename: Original filename with extension

        Returns:
            FileFormat enum value

        Raises:
            UnsupportedFileFormatException: If extension not recognized
        """
        if not filename or '.' not in filename:
            raise UnsupportedFileFormatException(
                filename=filename or "unknown",
                detected_format="none"
            )

        extension = filename.lower().rsplit('.', 1)[-1]

        format_map = {
            'csv': FileFormat.CSV,
            'xlsx': FileFormat.EXCEL_XLSX,
            'xls': FileFormat.EXCEL_XLS,
            'json': FileFormat.JSON
        }

        if extension not in format_map:
            raise UnsupportedFileFormatException(
                filename=filename,
                detected_format=extension
            )

        return format_map[extension]

    def _parse_raw_data(
        self,
        file_content: bytes,
        file_format: FileFormat,
        filename: str
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Parse raw file content into headers and rows.

        WHY: Normalizes different file formats into a common structure
        for consistent processing.

        WHAT: Returns tuple of (headers, rows) where each row is a dict.

        HOW: Delegates to format-specific parsers.

        Args:
            file_content: Raw file bytes
            file_format: Detected file format
            filename: Original filename (for error messages)

        Returns:
            Tuple of (headers list, rows list of dicts)

        Raises:
            FileImportException: If parsing fails
        """
        try:
            if file_format == FileFormat.CSV:
                return self._parse_csv(file_content)
            elif file_format in (FileFormat.EXCEL_XLSX, FileFormat.EXCEL_XLS):
                return self._parse_excel(file_content, file_format)
            elif file_format == FileFormat.JSON:
                return self._parse_json(file_content)
            else:
                raise UnsupportedFileFormatException(
                    filename=filename,
                    detected_format=file_format.value
                )
        except FileImportException:
            raise
        except Exception as e:
            logger.error(f"Error parsing {filename}: {e}")
            raise FileImportException(
                message=f"Failed to parse file: {str(e)}",
                code="PARSE_ERROR",
                context={"filename": filename, "format": file_format.value}
            )

    def _parse_csv(self, content: bytes) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Parse CSV file content.

        WHY: CSV is a common export format from HR systems and spreadsheets.

        WHAT: Parses CSV bytes into headers and row dictionaries.

        HOW: Uses Python csv.DictReader with encoding detection.

        Args:
            content: CSV file bytes

        Returns:
            Tuple of (headers, rows)
        """
        # Try UTF-8 first, fall back to latin-1
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('latin-1')

        # Parse CSV
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        rows = list(reader)

        return headers, rows

    def _parse_excel(
        self,
        content: bytes,
        file_format: FileFormat
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Parse Excel file content (XLSX or XLS).

        WHY: Excel is the most common spreadsheet format for roster data.

        WHAT: Parses Excel bytes into headers and row dictionaries.

        HOW: Uses pandas with openpyxl engine for reliable parsing.

        Args:
            content: Excel file bytes
            file_format: EXCEL_XLSX or EXCEL_XLS

        Returns:
            Tuple of (headers, rows)
        """
        engine = 'openpyxl' if file_format == FileFormat.EXCEL_XLSX else 'xlrd'

        df = pd.read_excel(io.BytesIO(content), engine=engine)

        # Convert NaN to None for consistent handling
        df = df.where(pd.notnull(df), None)

        headers = list(df.columns)
        rows = df.to_dict('records')

        return headers, rows

    def _parse_json(self, content: bytes) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Parse JSON file content.

        WHY: JSON is useful for API exports and programmatic generation.

        WHAT: Parses JSON bytes into headers and row dictionaries.

        HOW: Expects JSON array of objects.

        Args:
            content: JSON file bytes

        Returns:
            Tuple of (headers, rows)

        Raises:
            FileImportException: If JSON is invalid or not an array
        """
        try:
            data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise FileImportException(
                message=f"Invalid JSON: {str(e)}",
                code="INVALID_JSON"
            )

        if not isinstance(data, list):
            raise FileImportException(
                message="JSON must be an array of objects",
                code="INVALID_JSON_STRUCTURE"
            )

        if not data:
            return [], []

        # Get headers from first object
        headers = list(data[0].keys()) if data else []

        return headers, data

    # =========================================================================
    # COLUMN MAPPING
    # =========================================================================

    def _auto_detect_columns(
        self,
        headers: List[str],
        aliases: List[ColumnAlias]
    ) -> ColumnMapping:
        """
        Auto-detect column mappings from headers.

        WHY: Enables flexible file formats with different column naming
        conventions while reducing manual configuration.

        WHAT: Maps detected source columns to target fields based on
        alias patterns.

        HOW:
        1. For each target field's aliases, check if any header matches
        2. Calculate confidence based on how many fields were mapped
        3. Track unmapped columns for user feedback

        Args:
            headers: List of column headers from file
            aliases: List of ColumnAlias configurations

        Returns:
            ColumnMapping with detected mappings
        """
        field_to_source: Dict[str, str] = {}
        mapped_headers = set()

        for alias in aliases:
            for header in headers:
                if alias.matches(header):
                    field_to_source[alias.target_field] = header
                    mapped_headers.add(header)
                    break

        # Track unmapped columns
        unmapped = [h for h in headers if h not in mapped_headers]

        # Calculate confidence
        required_count = sum(1 for a in aliases if a.required)
        mapped_required = sum(
            1 for a in aliases
            if a.required and a.target_field in field_to_source
        )
        confidence = mapped_required / required_count if required_count > 0 else 1.0

        return ColumnMapping(
            field_to_source=field_to_source,
            unmapped_columns=unmapped,
            confidence=confidence,
            auto_detected=True
        )

    def _validate_required_columns(
        self,
        mapping: ColumnMapping,
        aliases: List[ColumnAlias],
        available_headers: List[str],
        filename: str
    ) -> None:
        """
        Validate that all required columns are mapped.

        WHY: Early detection of missing required columns prevents
        processing errors and provides clear feedback.

        WHAT: Raises exception if any required field is not mapped.

        HOW: Checks each required alias against the mapping.

        Args:
            mapping: Column mapping to validate
            aliases: Alias configuration with required flags
            available_headers: Headers from file (for error message)
            filename: Filename (for error context)

        Raises:
            MissingRequiredColumnException: If required column missing
        """
        for alias in aliases:
            if alias.required and alias.target_field not in mapping.field_to_source:
                raise MissingRequiredColumnException(
                    column_name=alias.target_field,
                    available_columns=available_headers,
                    context={"filename": filename}
                )

    # =========================================================================
    # ROW PARSING
    # =========================================================================

    def _parse_instructor_row(
        self,
        row: Dict[str, Any],
        headers: List[str],
        mapping: ColumnMapping,
        row_num: int
    ) -> Optional[InstructorRosterEntry]:
        """
        Parse a single instructor row.

        WHY: Converts raw row data to structured InstructorRosterEntry
        with proper type conversion.

        WHAT: Creates InstructorRosterEntry from row data using mapping.

        HOW: Extracts each field using mapping, applies defaults.

        Args:
            row: Raw row data (column -> value)
            headers: Column headers (for raw data storage)
            mapping: Column mapping to use
            row_num: Row number (1-indexed) for error reporting

        Returns:
            InstructorRosterEntry or None if row is empty
        """
        def get_value(field: str, default: Any = None) -> Any:
            source_col = mapping.get_source_column(field)
            if source_col and source_col in row:
                value = row[source_col]
                # Handle None/NaN
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return default
                return value
            return default

        # Get required fields
        name = get_value('name', '')
        email = get_value('email', '')

        # Skip empty rows
        if not name and not email:
            return None

        # Parse tracks (comma-separated)
        tracks_raw = get_value('tracks', '')
        tracks = []
        if tracks_raw:
            tracks = [t.strip() for t in str(tracks_raw).split(',') if t.strip()]

        # Parse available days (comma-separated)
        days_raw = get_value('available_days', '')
        available_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        if days_raw:
            parsed_days = [d.strip() for d in str(days_raw).split(',') if d.strip()]
            if parsed_days:
                available_days = parsed_days

        entry = InstructorRosterEntry(
            name=str(name).strip() if name else '',
            email=str(email).strip().lower() if email else '',
            source_row=row_num,
            tracks=tracks,
            role=str(get_value('role', 'instructor')).lower(),
            available_days=available_days,
            start_date=str(get_value('start_date')) if get_value('start_date') else None,
            end_date=str(get_value('end_date')) if get_value('end_date') else None,
            phone=str(get_value('phone')) if get_value('phone') else None,
            department=str(get_value('department')) if get_value('department') else None,
            notes=str(get_value('notes')) if get_value('notes') else None,
            raw_data=row
        )

        return entry

    def _parse_student_row(
        self,
        row: Dict[str, Any],
        headers: List[str],
        mapping: ColumnMapping,
        row_num: int
    ) -> Optional[StudentRosterEntry]:
        """
        Parse a single student row.

        WHY: Converts raw row data to structured StudentRosterEntry
        with proper type conversion.

        WHAT: Creates StudentRosterEntry from row data using mapping.

        HOW: Extracts each field using mapping, applies defaults.

        Args:
            row: Raw row data (column -> value)
            headers: Column headers (for raw data storage)
            mapping: Column mapping to use
            row_num: Row number (1-indexed) for error reporting

        Returns:
            StudentRosterEntry or None if row is empty
        """
        def get_value(field: str, default: Any = None) -> Any:
            source_col = mapping.get_source_column(field)
            if source_col and source_col in row:
                value = row[source_col]
                # Handle None/NaN
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return default
                return value
            return default

        # Get required fields
        name = get_value('name', '')
        email = get_value('email', '')
        track = get_value('track', '')

        # Skip empty rows
        if not name and not email:
            return None

        entry = StudentRosterEntry(
            name=str(name).strip() if name else '',
            email=str(email).strip().lower() if email else '',
            track=str(track).strip() if track else '',
            source_row=row_num,
            location=str(get_value('location')).strip() if get_value('location') else None,
            instructor=str(get_value('instructor')).strip().lower() if get_value('instructor') else None,
            group=str(get_value('group')).strip() if get_value('group') else None,
            employee_id=str(get_value('employee_id')).strip() if get_value('employee_id') else None,
            department=str(get_value('department')).strip() if get_value('department') else None,
            manager_email=str(get_value('manager_email')).strip().lower() if get_value('manager_email') else None,
            notes=str(get_value('notes')) if get_value('notes') else None,
            raw_data=row
        )

        return entry

    # =========================================================================
    # DUPLICATE DETECTION
    # =========================================================================

    def _detect_duplicate_emails(
        self,
        entries: List[Any]
    ) -> Dict[str, List[int]]:
        """
        Detect duplicate email addresses in entries.

        WHY: Duplicate emails indicate data issues that should be
        resolved before import.

        WHAT: Returns dict mapping email to list of row numbers.

        HOW: Groups entries by email, keeps only those with > 1 occurrence.

        Args:
            entries: List of roster entries (instructor or student)

        Returns:
            Dict of email -> [row_numbers] for duplicates only
        """
        email_rows: Dict[str, List[int]] = {}

        for entry in entries:
            if entry.email:
                if entry.email not in email_rows:
                    email_rows[entry.email] = []
                email_rows[entry.email].append(entry.source_row)

        # Filter to only duplicates
        return {
            email: rows
            for email, rows in email_rows.items()
            if len(rows) > 1
        }

    # =========================================================================
    # TEMPLATE GENERATION
    # =========================================================================

    @staticmethod
    def generate_instructor_template() -> bytes:
        """
        Generate a template CSV file for instructor roster import.

        WHY: Provides users with a correctly formatted starting point
        for creating their roster files.

        WHAT: Returns CSV bytes with headers and example row.

        HOW: Uses csv module to create properly formatted CSV.

        Returns:
            CSV file content as bytes
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = [
            'name',
            'email',
            'tracks',
            'role',
            'available_days',
            'start_date',
            'end_date',
            'phone',
            'department',
            'notes'
        ]
        writer.writerow(headers)

        # Write example row
        example = [
            'John Doe',
            'john.doe@example.com',
            'Backend Development, DevOps',
            'instructor',
            'Monday, Tuesday, Wednesday',
            '2024-01-15',
            '2024-06-30',
            '+1-555-1234',
            'Engineering',
            'Part-time availability'
        ]
        writer.writerow(example)

        # Write second example
        example2 = [
            'Jane Smith',
            'jane.smith@example.com',
            'Frontend Development',
            'lead_instructor',
            'Monday, Tuesday, Wednesday, Thursday, Friday',
            '2024-01-15',
            '',
            '+1-555-5678',
            'Training',
            ''
        ]
        writer.writerow(example2)

        logger.info("Generated instructor roster template")
        return output.getvalue().encode('utf-8')

    @staticmethod
    def generate_student_template() -> bytes:
        """
        Generate a template CSV file for student roster import.

        WHY: Provides users with a correctly formatted starting point
        for creating their roster files.

        WHAT: Returns CSV bytes with headers and example row.

        HOW: Uses csv module to create properly formatted CSV.

        Returns:
            CSV file content as bytes
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = [
            'name',
            'email',
            'track',
            'location',
            'instructor',
            'group',
            'employee_id',
            'department',
            'manager_email',
            'notes'
        ]
        writer.writerow(headers)

        # Write example rows
        examples = [
            [
                'Alice Johnson',
                'alice.johnson@example.com',
                'Backend Development',
                'New York',
                'john.doe@example.com',
                'Study Group A',
                'EMP001',
                'Engineering',
                'manager@example.com',
                'New hire'
            ],
            [
                'Bob Smith',
                'bob.smith@example.com',
                'Frontend Development',
                'London',
                'jane.smith@example.com',
                'Study Group B',
                'EMP002',
                'Product',
                '',
                ''
            ],
            [
                'Carol Williams',
                'carol.williams@example.com',
                'Backend Development',
                'Chicago',
                '',
                '',
                'EMP003',
                'Engineering',
                'manager@example.com',
                'Needs accommodations'
            ]
        ]

        for example in examples:
            writer.writerow(example)

        logger.info("Generated student roster template")
        return output.getvalue().encode('utf-8')
