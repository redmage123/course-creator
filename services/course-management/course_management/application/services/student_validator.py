"""
Student Data Validator Service

This service validates student data extracted from spreadsheets before
bulk enrollment operations. It ensures data integrity and provides
detailed error reporting for invalid entries.

BUSINESS CONTEXT:
Before creating student accounts and enrollments, we must validate that
all student data meets platform requirements. This prevents data integrity
issues and provides instructors with clear feedback on data problems.

VALIDATION RULES:
- Email: Must be valid RFC 5322 format
- First Name: Optional but if provided, must be 1-100 characters
- Last Name: Optional but if provided, must be 1-100 characters
- Role: Must be 'student' (default) or other valid role

AI ASSISTANT INTEGRATION:
Future enhancement: Use AI assistant to detect and correct common data
entry errors (e.g., swapped first/last names, typos in email domains).

USAGE EXAMPLE:
    validator = StudentDataValidator()
    result = validator.validate(student_data)
    if result.is_valid:
        # Proceed with enrollment
    else:
        # Report errors to instructor
"""
import re
from typing import Dict, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Validation result for a single student record.

    BUSINESS CONTEXT:
    Provides detailed feedback on validation status and any errors found.
    Enables instructors to quickly identify and fix data problems.

    Attributes:
        is_valid: True if all validations passed
        errors: Dictionary mapping field names to error messages
        warnings: Dictionary mapping field names to warning messages
        student_data: Original student data that was validated
    """
    is_valid: bool
    errors: Dict[str, str] = field(default_factory=dict)
    warnings: Dict[str, str] = field(default_factory=dict)
    student_data: Dict = field(default_factory=dict)


class StudentDataValidator:
    """
    Service for validating student data from spreadsheets.

    BUSINESS REQUIREMENTS:
    - Validate required fields are present
    - Validate email format (RFC 5322)
    - Validate field lengths and formats
    - Provide detailed error messages
    - Support batch validation
    """

    # Email validation regex (simplified RFC 5322)
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Field constraints
    MAX_NAME_LENGTH = 100
    MIN_NAME_LENGTH = 1

    def validate(self, student_data: Dict) -> ValidationResult:
        """
        Validate a single student record.

        BUSINESS LOGIC:
        - Check required fields are present
        - Validate email format
        - Validate field lengths
        - Return detailed validation result

        Args:
            student_data: Dictionary containing student information

        Returns:
            ValidationResult with validation status and any errors

        Example:
            result = validator.validate({
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'role': 'student'
            })
        """
        errors = {}
        warnings = {}

        # Validate required fields
        if 'email' not in student_data or not student_data['email']:
            errors['email'] = 'Email is required'
        elif not self._validate_email_format(student_data['email']):
            errors['email'] = f"Invalid email format: {student_data['email']}"

        # Validate optional fields if present
        if 'first_name' in student_data and student_data['first_name']:
            if not self._validate_name_length(student_data['first_name']):
                errors['first_name'] = f"First name must be between {self.MIN_NAME_LENGTH} and {self.MAX_NAME_LENGTH} characters"

        if 'last_name' in student_data and student_data['last_name']:
            if not self._validate_name_length(student_data['last_name']):
                errors['last_name'] = f"Last name must be between {self.MIN_NAME_LENGTH} and {self.MAX_NAME_LENGTH} characters"
        elif 'last_name' not in student_data or not student_data['last_name']:
            errors['last_name'] = 'Last name is required'

        # Validate role
        if 'role' in student_data:
            if student_data['role'] not in ['student', 'instructor', 'admin']:
                warnings['role'] = f"Unusual role: {student_data['role']}. Defaulting to 'student'"
                student_data['role'] = 'student'

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            student_data=student_data
        )

    def validate_batch(self, students_data: List[Dict]) -> List[ValidationResult]:
        """
        Validate multiple student records in batch.

        BUSINESS LOGIC:
        - Validate each student record independently
        - Return list of validation results
        - Log summary statistics

        Args:
            students_data: List of dictionaries containing student information

        Returns:
            List of ValidationResult objects, one for each student

        Example:
            results = validator.validate_batch([
                {'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'},
                {'first_name': 'Jane', 'last_name': 'Smith', 'email': 'invalid-email'}
            ])
        """
        results = []

        for i, student_data in enumerate(students_data):
            try:
                result = self.validate(student_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating student at index {i}: {e}")
                results.append(ValidationResult(
                    is_valid=False,
                    errors={'general': f"Validation error: {str(e)}"},
                    student_data=student_data
                ))

        # Log summary
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count
        logger.info(f"Batch validation complete: {valid_count} valid, {invalid_count} invalid")

        return results

    def _validate_email_format(self, email: str) -> bool:
        """
        Validate email address format.

        BUSINESS LOGIC:
        - Use regex to validate email format
        - Follow RFC 5322 simplified rules
        - Reject obviously invalid formats

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False

        return bool(self.EMAIL_REGEX.match(email.strip()))

    def _validate_name_length(self, name: str) -> bool:
        """
        Validate name field length.

        BUSINESS LOGIC:
        - Ensure name is between min and max length
        - Reject empty strings or whitespace-only names

        Args:
            name: Name string to validate

        Returns:
            True if name length is valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False

        name = name.strip()
        return self.MIN_NAME_LENGTH <= len(name) <= self.MAX_NAME_LENGTH

    def get_validation_summary(self, results: List[ValidationResult]) -> Dict:
        """
        Generate summary statistics for batch validation results.

        BUSINESS LOGIC:
        - Count total, valid, and invalid records
        - Collect common error types
        - Provide actionable insights

        Args:
            results: List of ValidationResult objects

        Returns:
            Dictionary with summary statistics

        Example:
            summary = validator.get_validation_summary(results)
            print(f"Valid: {summary['valid_count']}, Invalid: {summary['invalid_count']}")
        """
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count

        # Collect error types
        error_types = {}
        for result in results:
            if not result.is_valid:
                for field, error in result.errors.items():
                    error_types[field] = error_types.get(field, 0) + 1

        return {
            'total_records': len(results),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'validation_rate': (valid_count / len(results) * 100) if results else 0,
            'common_errors': error_types
        }
