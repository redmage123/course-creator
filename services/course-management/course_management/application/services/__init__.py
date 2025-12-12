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
    'AdaptiveLearningServiceException',
    'RosterFileParser',
    'ScheduleGenerator',
    'BulkProjectCreator',
    'BulkProjectCreatorException',
    'ProjectBuilderOrchestrator',
    'ProjectBuilderSession',
    'ProjectBuilderState',
    'OrchestratorResponse',
    'OrchestratorException'
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
    elif name == 'RosterFileParser':
        from course_management.application.services.roster_file_parser import RosterFileParser
        return RosterFileParser
    elif name == 'ScheduleGenerator':
        from course_management.application.services.schedule_generator import ScheduleGenerator
        return ScheduleGenerator
    elif name == 'BulkProjectCreator':
        from course_management.application.services.bulk_project_creator import BulkProjectCreator
        return BulkProjectCreator
    elif name == 'BulkProjectCreatorException':
        from course_management.application.services.bulk_project_creator import BulkProjectCreatorException
        return BulkProjectCreatorException
    elif name == 'ProjectBuilderOrchestrator':
        from course_management.application.services.project_builder_orchestrator import ProjectBuilderOrchestrator
        return ProjectBuilderOrchestrator
    elif name == 'ProjectBuilderSession':
        from course_management.application.services.project_builder_orchestrator import ProjectBuilderSession
        return ProjectBuilderSession
    elif name == 'ProjectBuilderState':
        from course_management.application.services.project_builder_orchestrator import ProjectBuilderState
        return ProjectBuilderState
    elif name == 'OrchestratorResponse':
        from course_management.application.services.project_builder_orchestrator import OrchestratorResponse
        return OrchestratorResponse
    elif name == 'OrchestratorException':
        from course_management.application.services.project_builder_orchestrator import OrchestratorException
        return OrchestratorException
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")