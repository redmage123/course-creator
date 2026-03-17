"""
Course Validator Plugin

BUSINESS CONTEXT:
Validates course content before saving to ensure quality standards.
Prevents low-quality or incomplete courses from being published.

FEATURES:
- Validates course titles and descriptions
- Ensures learning objectives are present
- Validates quiz question limits
- Provides detailed validation error messages

USAGE:
This plugin is activated automatically when loaded.
It hooks into 'before-course-save' and validates content.

@module course-validator
"""

from typing import Any, Dict, List, Optional

# Plugin API imports (provided by platform)
# These will be available when the plugin system is integrated


class ValidationError(Exception):
    """Raised when course validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class CourseValidator:
    """
    Validates course content against quality standards.

    BUSINESS VALUE:
    - Ensures consistent content quality
    - Prevents incomplete courses from being published
    - Provides actionable feedback to instructors
    """

    def __init__(self, settings: Dict[str, Any]):
        """
        Initialize validator with settings.

        Args:
            settings: Plugin settings from config
        """
        self.min_title_length = settings.get('min_course_title_length', 5)
        self.min_description_length = settings.get('min_description_length', 50)
        self.require_objectives = settings.get('require_learning_objectives', True)
        self.max_quiz_questions = settings.get('max_quiz_questions', 50)

    def validate_course(self, course: Dict[str, Any]) -> List[str]:
        """
        Validate a course against quality standards.

        Args:
            course: Course data dict

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate title
        title = course.get('title', '') or course.get('name', '')
        if len(title) < self.min_title_length:
            errors.append(
                f"Course title must be at least {self.min_title_length} characters"
            )

        # Validate description
        description = course.get('description', '')
        if len(description) < self.min_description_length:
            errors.append(
                f"Course description must be at least {self.min_description_length} characters"
            )

        # Validate learning objectives
        if self.require_objectives:
            objectives = course.get('learning_objectives', [])
            if not objectives or len(objectives) == 0:
                errors.append("Course must have at least one learning objective")

        return errors

    def validate_quiz(self, quiz: Dict[str, Any]) -> List[str]:
        """
        Validate a quiz against quality standards.

        Args:
            quiz: Quiz data dict

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate question count
        questions = quiz.get('questions', [])
        if len(questions) > self.max_quiz_questions:
            errors.append(
                f"Quiz cannot have more than {self.max_quiz_questions} questions"
            )

        # Validate each question has at least 2 options
        for i, question in enumerate(questions):
            options = question.get('options', [])
            if len(options) < 2:
                errors.append(f"Question {i + 1} must have at least 2 answer options")

            # Validate correct answer exists
            correct = question.get('correct_answer')
            if correct is None:
                errors.append(f"Question {i + 1} must have a correct answer specified")

        return errors


# Global validator instance (initialized on activation)
_validator: Optional[CourseValidator] = None


def activate(api: Any) -> None:
    """
    Called when plugin is loaded and activated.

    Sets up hooks and event subscriptions.

    Args:
        api: PlatformAPI instance
    """
    global _validator

    api.log.info("Course Validator plugin activating...")

    # Load settings
    settings = api.config.get_all()
    _validator = CourseValidator(settings)

    # Register hooks
    @api.hooks['before-course-save'].add
    def validate_before_save(course: Dict[str, Any]) -> Dict[str, Any]:
        """Validate course before saving."""
        errors = _validator.validate_course(course)
        if errors:
            api.log.warning(f"Course validation failed: {errors}")
            raise ValidationError(errors)
        api.log.info(f"Course '{course.get('title', 'Unknown')}' passed validation")
        return course

    @api.hooks['before-quiz-save'].add
    def validate_quiz_before_save(quiz: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quiz before saving."""
        errors = _validator.validate_quiz(quiz)
        if errors:
            api.log.warning(f"Quiz validation failed: {errors}")
            raise ValidationError(errors)
        api.log.info(f"Quiz '{quiz.get('title', 'Unknown')}' passed validation")
        return quiz

    # Subscribe to events
    @api.events.subscribe('course.created')
    def on_course_created(event):
        """Log when courses are created."""
        api.log.info(f"New course created: {event.data.get('name', 'Unknown')}")

    api.log.info("Course Validator plugin activated successfully")


def deactivate(api: Any) -> None:
    """
    Called when plugin is being unloaded.

    Cleans up resources and removes hooks.

    Args:
        api: PlatformAPI instance
    """
    global _validator

    api.log.info("Course Validator plugin deactivating...")
    _validator = None
    api.log.info("Course Validator plugin deactivated")


def get_validator() -> Optional[CourseValidator]:
    """Get the current validator instance."""
    return _validator
