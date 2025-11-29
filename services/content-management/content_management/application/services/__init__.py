# Content Management Application Services
"""
Application Services Package

WHAT: Application layer services for content management operations
WHERE: Used by API endpoints to orchestrate business logic
WHY: Provides clean separation between presentation and domain layers

Available Services:
- SyllabusService: Syllabus creation and management
- ContentSearchService: Content search and discovery
- ContentValidationService: Content quality validation
- InteractiveContentService: Interactive content types
- ContentVersionService: Content versioning and branching
- AdvancedAssessmentService: Advanced assessment types

Note: Import services directly from their modules to avoid circular imports
"""