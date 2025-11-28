"""
Enrollment Management API Endpoints

BUSINESS CONTEXT:
This module contains all student enrollment REST API endpoints following the Single
Responsibility Principle. It handles individual enrollments, bulk course enrollments,
and bulk track enrollments with comprehensive spreadsheet parsing and validation.

SOLID PRINCIPLES APPLIED:
- Single Responsibility: Only enrollment management endpoints
- Open/Closed: Extensible through dependency injection
- Liskov Substitution: Uses interface abstractions
- Interface Segregation: Depends only on IEnrollmentService
- Dependency Inversion: Depends on abstractions

ENROLLMENT WORKFLOWS:
1. Individual Enrollment: Single student enrollment in a course
2. Bulk Course Enrollment: Upload spreadsheet to enroll multiple students in one course
3. Bulk Track Enrollment: Upload spreadsheet to enroll multiple students in all track courses

SUPPORTED FORMATS (Bulk Enrollment):
- CSV (Comma-Separated Values)
- XLSX (Microsoft Excel 2007+)
- XLS (Microsoft Excel Legacy)
- ODS (LibreOffice Calc)

@module api/enrollment_endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import List
import logging
import sys
import os

# JWT Authentication - Import from auth module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from auth import get_current_user_id as get_authenticated_user_id

# Domain entities and services
from course_management.domain.entities.enrollment import EnrollmentRequest, BulkEnrollmentRequest
from course_management.domain.interfaces.enrollment_service import IEnrollmentService

# Bulk enrollment services
from course_management.application.services.spreadsheet_parser import SpreadsheetParser
from course_management.application.services.student_validator import StudentDataValidator
from course_management.application.services.bulk_enrollment_service import BulkEnrollmentService

# Pydantic models for API (Data Transfer Objects)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# API Models (DTOs - following Single Responsibility)
class EnrollmentRequestDTO(BaseModel):
    """
    Data Transfer Object for individual student enrollment requests.

    BUSINESS CONTEXT:
    Represents a request to enroll a single student in a course.
    Used for manual enrollments by instructors or self-enrollment by students.

    VALIDATION:
    - Email must be valid format
    - Course ID must be provided
    """
    student_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    course_id: str

class BulkEnrollmentRequestDTO(BaseModel):
    """
    Data Transfer Object for bulk enrollment requests.

    BUSINESS CONTEXT:
    Represents a request to enroll multiple students in a course at once.
    Used for batch operations when instructors have a list of student emails.

    VALIDATION:
    - Course ID must be provided
    - At least one student email must be provided
    """
    course_id: str
    student_emails: List[str] = Field(..., min_items=1)

# Constants for bulk enrollment
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.ods'}
SUPPORTED_MIME_TYPES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.oasis.opendocument.spreadsheet'
}

# Create router with enrollment prefix and tag
router = APIRouter(tags=["enrollments"])

# Dependency injection helpers
def get_enrollment_service() -> IEnrollmentService:
    """Dependency injection for enrollment service"""
    from main import container
    if not container:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return container.get_enrollment_service()

# JWT-authenticated user ID extraction (replaced deprecated mock)
get_current_user_id = get_authenticated_user_id

# ============================================================================
# ENROLLMENT ENDPOINTS
# ============================================================================

@router.post("/enrollments")
async def enroll_student(
    request: EnrollmentRequestDTO,
    enrollment_service: IEnrollmentService = Depends(get_enrollment_service)
):
    """
    Enroll a single student in a course.

    BUSINESS CONTEXT:
    Allows instructors to manually enroll a student in their course by providing
    the student's email address. The system creates the student account if it
    doesn't exist and establishes the enrollment relationship.

    WORKFLOW:
    1. Validate student email format
    2. Validate course exists
    3. Check if student account exists (create if needed)
    4. Create enrollment record
    5. Send enrollment confirmation email (if configured)
    6. Return enrollment confirmation

    REQUEST BODY:
    - student_email: Valid email address of student to enroll
    - course_id: ID of course to enroll student in

    RESPONSE:
    - message: Success confirmation message
    - enrollment_id: Unique identifier for the enrollment record

    ERROR HANDLING:
    - 400: Invalid email format or course not found
    - 422: Enrollment already exists or business rule violation
    - 500: Database or internal server error

    EXAMPLE USAGE:
        curl -X POST "https://localhost:8001/enrollments" \\
             -H "Authorization: Bearer $TOKEN" \\
             -H "Content-Type: application/json" \\
             -d '{"student_email": "student@example.com", "course_id": "course-123"}'
    """
    try:
        enrollment_request = EnrollmentRequest(
            student_email=request.student_email,
            course_id=request.course_id
        )

        enrollment = await enrollment_service.enroll_student(enrollment_request)
        return {"message": "Student enrolled successfully", "enrollment_id": enrollment.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error enrolling student: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/courses/{course_id}/bulk-enroll")
async def bulk_enroll_in_course(
    course_id: str,
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Bulk enroll students in a course via spreadsheet upload.

    BUSINESS CONTEXT (v3.3.1):
    Instructors can upload spreadsheets containing student information to
    quickly enroll multiple students in a course. The system automatically
    creates student accounts and enrollments.

    WORKFLOW:
    1. Upload spreadsheet (CSV, XLSX, or ODS)
    2. Parse student data from spreadsheet
    3. Validate all student records
    4. Create accounts for new students
    5. Enroll all students in course
    6. Return detailed enrollment report

    SUPPORTED FORMATS:
    - CSV (Comma-Separated Values)
    - XLSX (Microsoft Excel)
    - ODS (LibreOffice Calc)

    REQUIRED COLUMNS:
    - email: Student email address
    - last_name: Student last name
    - first_name: Student first name (optional)
    - role: User role (optional, defaults to 'student')

    REQUEST:
    - course_id: Course ID to enroll students in
    - file: Spreadsheet file (multipart/form-data)

    RESPONSE:
    - total_students: Total number of students in spreadsheet
    - successful_enrollments: Number of successful enrollments
    - failed_enrollments: Number of failed enrollments
    - created_accounts: List of newly created student accounts
    - skipped_accounts: List of existing accounts that were skipped
    - errors: List of errors for failed operations
    - processing_time_ms: Time taken to process enrollment

    EXAMPLE USAGE:
        curl -X POST "https://localhost:8001/courses/course-123/bulk-enroll" \\
             -H "Authorization: Bearer $TOKEN" \\
             -F "file=@students.csv"
    """
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Validate file type
        file_extension = '.' + file.filename.lower().split('.')[-1]
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Parse spreadsheet
        logger.info(f"Parsing spreadsheet: {file.filename} ({len(file_content)} bytes)")
        parser = SpreadsheetParser()
        students_data = parser.parse_file(file_content, file.filename)
        logger.info(f"Parsed {len(students_data)} students from spreadsheet")

        # Validate data
        validator = StudentDataValidator()
        validation_results = validator.validate_batch(students_data)

        # Get validation summary
        validation_summary = validator.get_validation_summary(validation_results)
        logger.info(
            f"Validation complete: {validation_summary['valid_count']} valid, "
            f"{validation_summary['invalid_count']} invalid"
        )

        # Filter valid students
        valid_students = [
            student for student, result in zip(students_data, validation_results)
            if result.is_valid
        ]

        # Enroll students
        enrollment_service = BulkEnrollmentService()
        result = await enrollment_service.enroll_in_course(valid_students, course_id)

        # Add validation summary to response
        result.metadata['validation_summary'] = validation_summary
        result.metadata['filename'] = file.filename

        logger.info(
            f"Bulk enrollment complete for course {course_id}: "
            f"{result.successful_enrollments} successful, {result.failed_enrollments} failed"
        )

        return {
            "success": True,
            "message": f"Processed {result.total_students} students",
            "total_students": result.total_students,
            "successful_enrollments": result.successful_enrollments,
            "failed_enrollments": result.failed_enrollments,
            "created_accounts": result.created_accounts,
            "skipped_accounts": result.skipped_accounts,
            "errors": result.errors,
            "metadata": result.metadata,
            "processing_time_ms": result.processing_time_ms
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during bulk enrollment: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error during bulk enrollment: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during bulk enrollment: {str(e)}"
        ) from e


@router.post("/tracks/{track_id}/bulk-enroll")
async def bulk_enroll_in_track(
    track_id: str,
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Bulk enroll students in all courses within a track via spreadsheet upload.

    BUSINESS CONTEXT (v3.3.1):
    Organization admins can upload spreadsheets to enroll multiple students
    in all courses within a track. This is useful for structured learning
    paths and corporate training programs.

    WORKFLOW:
    1. Upload spreadsheet (CSV, XLSX, or ODS)
    2. Parse student data from spreadsheet
    3. Validate all student records
    4. Get all courses in the track
    5. Create accounts for new students
    6. Enroll all students in ALL track courses
    7. Return detailed enrollment report

    REQUEST:
    - track_id: Track ID to enroll students in
    - file: Spreadsheet file (multipart/form-data)

    RESPONSE:
    Same format as course bulk enrollment, with additional metadata:
    - track_id: ID of the track
    - track_courses_count: Number of courses in track

    EXAMPLE USAGE:
        curl -X POST "https://localhost:8001/tracks/track-123/bulk-enroll" \\
             -H "Authorization: Bearer $TOKEN" \\
             -F "file=@students.csv"
    """
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Validate file type
        file_extension = '.' + file.filename.lower().split('.')[-1]
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Parse spreadsheet
        logger.info(f"Parsing spreadsheet: {file.filename} ({len(file_content)} bytes)")
        parser = SpreadsheetParser()
        students_data = parser.parse_file(file_content, file.filename)
        logger.info(f"Parsed {len(students_data)} students from spreadsheet")

        # Validate data
        validator = StudentDataValidator()
        validation_results = validator.validate_batch(students_data)
        validation_summary = validator.get_validation_summary(validation_results)

        # Filter valid students
        valid_students = [
            student for student, result in zip(students_data, validation_results)
            if result.is_valid
        ]

        # Enroll students in track
        enrollment_service = BulkEnrollmentService()
        result = await enrollment_service.enroll_in_track(valid_students, track_id)

        # Add validation summary to response
        result.metadata['validation_summary'] = validation_summary
        result.metadata['filename'] = file.filename

        logger.info(
            f"Bulk track enrollment complete for track {track_id}: "
            f"{result.successful_enrollments} successful, {result.failed_enrollments} failed"
        )

        return {
            "success": True,
            "message": f"Processed {result.total_students} students for track enrollment",
            "total_students": result.total_students,
            "successful_enrollments": result.successful_enrollments,
            "failed_enrollments": result.failed_enrollments,
            "created_accounts": result.created_accounts,
            "skipped_accounts": result.skipped_accounts,
            "errors": result.errors,
            "metadata": result.metadata,
            "processing_time_ms": result.processing_time_ms
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during track bulk enrollment: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error during track bulk enrollment: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during bulk enrollment: {str(e)}"
        ) from e
