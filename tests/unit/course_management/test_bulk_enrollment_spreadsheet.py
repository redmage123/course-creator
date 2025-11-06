"""
Test Suite for Bulk Student Enrollment via Spreadsheet Upload

This test suite follows Test-Driven Development (TDD) principles to ensure
comprehensive coverage of the bulk enrollment feature.

FEATURE REQUIREMENTS:
1. Support multiple spreadsheet formats: CSV, XLSX (MS Office), ODS (LibreOffice)
2. Parse student data from spreadsheet (name, email, etc.)
3. Validate student data using AI assistant
4. Bulk create student accounts
5. Bulk enroll students in courses or tracks
6. Support enrollment at both course-level and track-level
7. Provide detailed error reporting for invalid data

TDD APPROACH:
- RED: Write failing tests that specify expected behavior
- GREEN: Implement minimal code to make tests pass
- REFACTOR: Improve code quality and design

TEST ORGANIZATION:
- Unit tests for spreadsheet parsing logic
- Unit tests for data validation
- Integration tests for bulk enrollment workflow
- E2E tests for complete user journey
"""
import pytest
import pandas as pd
import io
from typing import List, Dict
from datetime import datetime


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_csv_content() -> str:
    """Sample CSV content with valid student data."""
    return """first_name,last_name,email,role
John,Doe,john.doe@example.com,student
Jane,Smith,jane.smith@example.com,student
Bob,Johnson,bob.johnson@example.com,student"""


@pytest.fixture
def sample_csv_with_invalid_data() -> str:
    """Sample CSV with invalid email addresses."""
    return """first_name,last_name,email,role
John,Doe,invalid-email,student
Jane,Smith,jane.smith@example.com,student
Bob,Johnson,bob@,student"""


@pytest.fixture
def sample_xlsx_bytes() -> bytes:
    """Sample XLSX file as bytes."""
    df = pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'email': ['john.doe@example.com', 'jane.smith@example.com', 'bob.johnson@example.com'],
        'role': ['student', 'student', 'student']
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    return buffer.getvalue()


@pytest.fixture
def sample_ods_bytes() -> bytes:
    """Sample ODS file as bytes."""
    df = pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'email': ['john.doe@example.com', 'jane.smith@example.com', 'bob.johnson@example.com'],
        'role': ['student', 'student', 'student']
    })
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='odf')
    return buffer.getvalue()


# ============================================================================
# TEST CASES: SPREADSHEET PARSING
# ============================================================================

class TestSpreadsheetParser:
    """
    Test suite for spreadsheet parsing functionality.

    BUSINESS REQUIREMENTS:
    - Support CSV, XLSX, and ODS formats
    - Extract student data with proper column mapping
    - Handle missing columns gracefully
    - Report parsing errors clearly
    """

    def test_parse_csv_file_returns_student_list(self, sample_csv_content):
        """
        TDD RED: Test CSV parsing returns list of student dictionaries.

        EXPECTED BEHAVIOR:
        - Parse CSV content successfully
        - Return list of dictionaries with student data
        - Map columns: first_name, last_name, email, role
        """
        from course_management.application.services.spreadsheet_parser import SpreadsheetParser

        parser = SpreadsheetParser()
        students = parser.parse_csv(sample_csv_content)

        assert len(students) == 3
        assert students[0]['first_name'] == 'John'
        assert students[0]['last_name'] == 'Doe'
        assert students[0]['email'] == 'john.doe@example.com'
        assert students[0]['role'] == 'student'

    def test_parse_xlsx_file_returns_student_list(self, sample_xlsx_bytes):
        """
        TDD RED: Test XLSX parsing returns list of student dictionaries.

        EXPECTED BEHAVIOR:
        - Parse XLSX binary content successfully
        - Return list of dictionaries with student data
        - Support Microsoft Office Excel format
        """
        from course_management.application.services.spreadsheet_parser import SpreadsheetParser

        parser = SpreadsheetParser()
        students = parser.parse_xlsx(sample_xlsx_bytes)

        assert len(students) == 3
        assert students[1]['first_name'] == 'Jane'
        assert students[1]['email'] == 'jane.smith@example.com'

    def test_parse_ods_file_returns_student_list(self, sample_ods_bytes):
        """
        TDD RED: Test ODS parsing returns list of student dictionaries.

        EXPECTED BEHAVIOR:
        - Parse ODS binary content successfully
        - Return list of dictionaries with student data
        - Support LibreOffice Calc format
        """
        from course_management.application.services.spreadsheet_parser import SpreadsheetParser

        parser = SpreadsheetParser()
        students = parser.parse_ods(sample_ods_bytes)

        assert len(students) == 3
        assert students[2]['first_name'] == 'Bob'
        assert students[2]['email'] == 'bob.johnson@example.com'

    def test_parse_csv_with_missing_columns_raises_error(self):
        """
        TDD RED: Test CSV parsing raises error for missing required columns.

        EXPECTED BEHAVIOR:
        - Detect missing required columns (email)
        - Raise ValueError with descriptive error message
        """
        from course_management.application.services.spreadsheet_parser import SpreadsheetParser

        csv_content = "first_name,last_name\nJohn,Doe"
        parser = SpreadsheetParser()

        with pytest.raises(ValueError, match="Missing required column: email"):
            parser.parse_csv(csv_content)

    def test_parse_empty_csv_raises_error(self):
        """
        TDD RED: Test parsing empty CSV raises error.

        EXPECTED BEHAVIOR:
        - Detect empty file
        - Raise ValueError with descriptive error message
        """
        from course_management.application.services.spreadsheet_parser import SpreadsheetParser

        csv_content = ""
        parser = SpreadsheetParser()

        with pytest.raises(ValueError, match="Empty spreadsheet"):
            parser.parse_csv(csv_content)


# ============================================================================
# TEST CASES: DATA VALIDATION
# ============================================================================

class TestStudentDataValidator:
    """
    Test suite for student data validation.

    BUSINESS REQUIREMENTS:
    - Validate email addresses (RFC 5322 format)
    - Validate required fields (first_name, last_name, email)
    - Use AI assistant for intelligent validation
    - Provide detailed validation errors
    """

    def test_validate_student_data_with_valid_data(self):
        """
        TDD RED: Test validation passes for valid student data.

        EXPECTED BEHAVIOR:
        - Validate all fields successfully
        - Return validation result with no errors
        """
        from course_management.application.services.student_validator import StudentDataValidator

        validator = StudentDataValidator()
        student_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'role': 'student'
        }

        result = validator.validate(student_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_student_data_with_invalid_email(self):
        """
        TDD RED: Test validation fails for invalid email.

        EXPECTED BEHAVIOR:
        - Detect invalid email format
        - Return validation error with field name and message
        """
        from course_management.application.services.student_validator import StudentDataValidator

        validator = StudentDataValidator()
        student_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'role': 'student'
        }

        result = validator.validate(student_data)

        assert result.is_valid is False
        assert 'email' in result.errors
        assert 'invalid' in result.errors['email'].lower() and 'format' in result.errors['email'].lower()

    def test_validate_student_data_with_missing_required_field(self):
        """
        TDD RED: Test validation fails for missing required fields.

        EXPECTED BEHAVIOR:
        - Detect missing required fields
        - Return validation error for each missing field
        """
        from course_management.application.services.student_validator import StudentDataValidator

        validator = StudentDataValidator()
        student_data = {
            'first_name': 'John',
            'role': 'student'
            # Missing last_name and email
        }

        result = validator.validate(student_data)

        assert result.is_valid is False
        assert 'last_name' in result.errors
        assert 'email' in result.errors

    def test_validate_batch_returns_validation_results_for_all_students(self):
        """
        TDD RED: Test batch validation returns results for all students.

        EXPECTED BEHAVIOR:
        - Validate all students in batch
        - Return list of validation results
        - Include both valid and invalid students
        """
        from course_management.application.services.student_validator import StudentDataValidator

        validator = StudentDataValidator()
        students_data = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com', 'role': 'student'},
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'invalid-email', 'role': 'student'},
            {'first_name': 'Bob', 'email': 'bob@example.com', 'role': 'student'}  # Missing last_name
        ]

        results = validator.validate_batch(students_data)

        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[2].is_valid is False


# ============================================================================
# TEST CASES: BULK ENROLLMENT SERVICE
# ============================================================================

class TestBulkEnrollmentService:
    """
    Test suite for bulk enrollment service.

    BUSINESS REQUIREMENTS:
    - Create student accounts from validated data
    - Enroll students in courses or tracks
    - Support both course-level and track-level enrollment
    - Provide transaction rollback on errors
    - Return detailed enrollment report
    """

    @pytest.mark.asyncio
    async def test_enroll_students_in_course_creates_accounts_and_enrollments(self, mock_user_service_account_not_found):
        """
        TDD RED: Test bulk enrollment in course creates accounts and enrollments.

        EXPECTED BEHAVIOR:
        - Create student accounts for new users
        - Enroll all students in specified course
        - Return enrollment report with success/failure details
        """
        from course_management.application.services.bulk_enrollment_service import BulkEnrollmentService

        service = BulkEnrollmentService()
        students_data = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com', 'role': 'student'},
            {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'jane.smith@example.com', 'role': 'student'}
        ]
        course_id = 'course-123'

        result = await service.enroll_in_course(students_data, course_id)

        assert result.total_students == 2
        assert result.successful_enrollments == 2
        assert result.failed_enrollments == 0
        assert len(result.created_accounts) == 2

    @pytest.mark.asyncio
    async def test_enroll_students_in_track_enrolls_in_all_track_courses(self, mock_user_service_account_not_found):
        """
        TDD RED: Test bulk enrollment in track enrolls students in all track courses.

        EXPECTED BEHAVIOR:
        - Create student accounts for new users
        - Enroll students in ALL courses within the track
        - Return enrollment report with per-course details
        """
        from course_management.application.services.bulk_enrollment_service import BulkEnrollmentService

        service = BulkEnrollmentService()
        students_data = [
            {'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@example.com', 'role': 'student'}
        ]
        track_id = 'track-456'

        result = await service.enroll_in_track(students_data, track_id)

        assert result.total_students == 1
        assert result.successful_enrollments > 0  # Enrolled in multiple courses
        assert 'track_id' in result.metadata
        assert result.metadata['track_id'] == track_id

    @pytest.mark.asyncio
    async def test_enroll_existing_students_skips_account_creation(self, mock_user_service_account_exists):
        """
        TDD RED: Test enrollment of existing students skips account creation.

        EXPECTED BEHAVIOR:
        - Detect existing student accounts by email
        - Skip account creation for existing users
        - Enroll existing students in course
        """
        from course_management.application.services.bulk_enrollment_service import BulkEnrollmentService

        service = BulkEnrollmentService()
        students_data = [
            {'first_name': 'Existing', 'last_name': 'Student', 'email': 'existing@example.com', 'role': 'student'}
        ]
        course_id = 'course-123'

        result = await service.enroll_in_course(students_data, course_id)

        assert result.total_students == 1
        assert result.successful_enrollments == 1
        assert len(result.created_accounts) == 0  # No new accounts
        assert len(result.skipped_accounts) == 1

    @pytest.mark.asyncio
    async def test_enroll_with_validation_errors_reports_failures(self, mock_user_service_account_not_found):
        """
        TDD RED: Test enrollment with invalid data reports failures.

        EXPECTED BEHAVIOR:
        - Validate data before processing
        - Report validation failures with details
        - Process valid students successfully
        """
        from course_management.application.services.bulk_enrollment_service import BulkEnrollmentService

        service = BulkEnrollmentService()
        students_data = [
            {'first_name': 'Valid', 'last_name': 'Student', 'email': 'valid@example.com', 'role': 'student'},
            {'first_name': 'Invalid', 'last_name': 'Student', 'email': 'invalid-email', 'role': 'student'}
        ]
        course_id = 'course-123'

        result = await service.enroll_in_course(students_data, course_id)

        assert result.total_students == 2
        assert result.successful_enrollments == 1
        assert result.failed_enrollments == 1
        assert len(result.errors) == 1


# ============================================================================
# TEST CASES: API ENDPOINT
# ============================================================================

class TestBulkEnrollmentAPIEndpoint:
    """
    Test suite for bulk enrollment API endpoint.

    BUSINESS REQUIREMENTS:
    - Accept multipart/form-data with file upload
    - Support CSV, XLSX, and ODS file types
    - Validate file size and format
    - Return enrollment report as JSON
    """

    @pytest.mark.asyncio
    async def test_upload_csv_file_returns_enrollment_report(self, sample_csv_content):
        """
        TDD RED: Test CSV upload endpoint returns enrollment report.

        EXPECTED BEHAVIOR:
        - Accept CSV file upload
        - Process file and enroll students
        - Return JSON response with enrollment details
        """
        from fastapi.testclient import TestClient
        from course_management.main import app

        client = TestClient(app)

        files = {'file': ('students.csv', sample_csv_content, 'text/csv')}
        response = client.post(
            '/courses/course-123/bulk-enroll',
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert 'total_students' in data
        assert 'successful_enrollments' in data
        assert data['successful_enrollments'] > 0

    @pytest.mark.asyncio
    async def test_upload_xlsx_file_returns_enrollment_report(self, sample_xlsx_bytes):
        """
        TDD RED: Test XLSX upload endpoint returns enrollment report.

        EXPECTED BEHAVIOR:
        - Accept XLSX file upload
        - Process file and enroll students
        - Return JSON response with enrollment details
        """
        from fastapi.testclient import TestClient
        from course_management.main import app

        client = TestClient(app)

        files = {'file': ('students.xlsx', sample_xlsx_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = client.post(
            '/courses/course-123/bulk-enroll',
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert 'total_students' in data
        assert data['successful_enrollments'] > 0

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type_returns_error(self):
        """
        TDD RED: Test invalid file type returns 400 error.

        EXPECTED BEHAVIOR:
        - Reject unsupported file types
        - Return 400 Bad Request with error message
        """
        from fastapi.testclient import TestClient
        from course_management.main import app

        client = TestClient(app)

        files = {'file': ('students.txt', 'invalid content', 'text/plain')}
        response = client.post(
            '/courses/course-123/bulk-enroll',
            files=files
        )

        assert response.status_code == 400
        assert 'unsupported file type' in response.json()['detail'].lower()

    @pytest.mark.asyncio
    async def test_upload_oversized_file_returns_error(self):
        """
        TDD RED: Test oversized file returns 413 error.

        EXPECTED BEHAVIOR:
        - Enforce file size limit (e.g., 10MB)
        - Return 413 Payload Too Large error
        """
        from fastapi.testclient import TestClient
        from course_management.main import app

        client = TestClient(app)

        # Create oversized file content (11MB)
        large_content = 'a' * (11 * 1024 * 1024)
        files = {'file': ('students.csv', large_content, 'text/csv')}

        response = client.post(
            '/courses/course-123/bulk-enroll',
            files=files
        )

        assert response.status_code == 413
        assert 'file too large' in response.json()['detail'].lower()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestBulkEnrollmentIntegration:
    """
    Integration tests for complete bulk enrollment workflow.

    BUSINESS REQUIREMENTS:
    - End-to-end workflow from file upload to enrollment
    - Database transaction integrity
    - AI assistant integration for validation
    """

    @pytest.mark.asyncio
    async def test_complete_bulk_enrollment_workflow(self, sample_csv_content, mock_user_service_account_not_found):
        """
        TDD RED: Test complete workflow from CSV upload to enrollment.

        EXPECTED BEHAVIOR:
        - Upload CSV file
        - Parse and validate student data
        - Create student accounts
        - Enroll students in course
        - Return comprehensive enrollment report
        """
        from course_management.application.services.bulk_enrollment_service import BulkEnrollmentService
        from course_management.application.services.spreadsheet_parser import SpreadsheetParser
        from course_management.application.services.student_validator import StudentDataValidator

        # Parse spreadsheet
        parser = SpreadsheetParser()
        students_data = parser.parse_csv(sample_csv_content)

        # Validate data
        validator = StudentDataValidator()
        validation_results = validator.validate_batch(students_data)
        valid_students = [
            student for student, result in zip(students_data, validation_results)
            if result.is_valid
        ]

        # Enroll students
        service = BulkEnrollmentService()
        result = await service.enroll_in_course(valid_students, 'course-123')

        assert result.total_students == 3
        assert result.successful_enrollments == 3
        assert result.failed_enrollments == 0
