"""
Course Management Application Services

This package contains business logic services for course management operations.
All services coordinate with DAOs and enforce business rules.
"""

# Lazy imports to avoid circular dependency issues
# Import services directly from their modules when needed:
# from course_management.application.services.sub_project_service import SubProjectService
# from course_management.application.services.adaptive_learning_service import AdaptiveLearningService

__all__ = [
    'SubProjectService',
    'AdaptiveLearningService',
    'AdaptiveLearningServiceException'
]


def __getattr__(name):
    """
    WHAT: Lazy import mechanism for service classes
    WHERE: Called when attributes are accessed
    WHY: Prevents circular import issues during module loading
    """
    if name == 'SubProjectService':
        from course_management.application.services.sub_project_service import SubProjectService
        return SubProjectService
    elif name == 'AdaptiveLearningService':
        from course_management.application.services.adaptive_learning_service import AdaptiveLearningService
        return AdaptiveLearningService
    elif name == 'AdaptiveLearningServiceException':
        from course_management.application.services.adaptive_learning_service import AdaptiveLearningServiceException
        return AdaptiveLearningServiceException
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")