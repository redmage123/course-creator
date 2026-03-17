## Advanced Assessment DAO Migration Guide

**Version:** 1.0
**Effective Date:** TBD (Post-Refactoring)
**Deprecation Period:** 2 releases (approximately 6 months)
**Removal Target:** v4.0.0 (Q2 2026)

---

## Overview

The `AdvancedAssessmentDAO` god class (2,842 lines) has been split into 4 specialized DAOs to improve maintainability, testability, and adherence to SOLID principles.

**Old Architecture (Deprecated):**
```
AdvancedAssessmentDAO (2,842 lines)
├── All rubric operations
├── All assessment operations
├── All submission operations
├── All peer review operations
├── All competency operations
└── All analytics operations
```

**New Architecture:**
```
RubricDAO (~490 lines)
├── Rubric CRUD
├── Criteria and performance levels
└── Rubric evaluations

AssessmentDAO (~985 lines)
├── Assessment CRUD
├── Project milestones
└── Assessment analytics

SubmissionDAO (~620 lines)
├── Submission CRUD
├── Portfolio artifacts
└── Submission queries (grading queue, best/latest)

PeerReviewDAO (~320 lines)
├── Peer review assignments
└── Peer review submissions

AdvancedAssessmentDAO (Deprecated, ~335 lines remaining)
└── Competency operations (will be extracted to CompetencyDAO in future)
```

---

## Migration Checklist

### For Service Developers

- [ ] Update service imports to use new DAOs
- [ ] Inject specialized DAOs via container
- [ ] Update service methods to call correct DAO
- [ ] Remove dependency on `AdvancedAssessmentDAO` (except competencies)
- [ ] Run unit tests to verify behavior unchanged
- [ ] Update service layer tests to mock new DAOs

### For API Developers

- [ ] Update endpoint dependencies to inject new DAOs
- [ ] Verify API contract unchanged (backward compatibility)
- [ ] Update API tests to use new DAOs
- [ ] Check OpenAPI/Swagger documentation accuracy

### For Test Developers

- [ ] Update test fixtures to use new DAOs
- [ ] Migrate mocks from old DAO to new DAOs
- [ ] Verify integration tests still pass
- [ ] Add tests for new DAO-specific functionality

---

## Code Migration Examples

### Example 1: Rubric Operations

#### Before (Deprecated):
```python
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO

class AdvancedAssessmentService:
    def __init__(self, dao: AdvancedAssessmentDAO):
        self.dao = dao

    async def create_rubric(self, rubric: AssessmentRubric) -> AssessmentRubric:
        """Create a new assessment rubric."""
        return await self.dao.create_rubric(rubric)

    async def evaluate_submission(
        self,
        evaluation: RubricEvaluation
    ) -> RubricEvaluation:
        """Evaluate submission using rubric."""
        return await self.dao.create_evaluation(evaluation)
```

#### After (Recommended):
```python
from content_management.data_access.rubric_dao import RubricDAO

class AdvancedAssessmentService:
    def __init__(
        self,
        rubric_dao: RubricDAO,
        # Other specialized DAOs as needed
    ):
        self.rubric_dao = rubric_dao

    async def create_rubric(self, rubric: AssessmentRubric) -> AssessmentRubric:
        """Create a new assessment rubric."""
        return await self.rubric_dao.create_rubric(rubric)

    async def evaluate_submission(
        self,
        evaluation: RubricEvaluation
    ) -> RubricEvaluation:
        """Evaluate submission using rubric."""
        return await self.rubric_dao.create_evaluation(evaluation)
```

**Key Changes:**
- Import `RubricDAO` instead of `AdvancedAssessmentDAO`
- Inject `RubricDAO` via constructor
- Call rubric-specific methods on `rubric_dao` instance

---

### Example 2: Assessment Operations

#### Before (Deprecated):
```python
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO

class AssessmentManagementService:
    def __init__(self, dao: AdvancedAssessmentDAO):
        self.dao = dao

    async def create_project_assessment(
        self,
        assessment: AdvancedAssessment,
        milestones: List[ProjectMilestone]
    ) -> AdvancedAssessment:
        """Create project assessment with milestones."""
        # Single DAO handles both assessment and milestones
        created_assessment = await self.dao.create_assessment(assessment)

        for milestone in milestones:
            await self.dao.create_milestone(milestone)

        return created_assessment

    async def get_assessment_analytics(
        self,
        assessment_id: UUID
    ) -> AssessmentAnalytics:
        """Get analytics for assessment."""
        return await self.dao.get_analytics_by_assessment(assessment_id)
```

#### After (Recommended):
```python
from content_management.data_access.assessment_dao import AssessmentDAO

class AssessmentManagementService:
    def __init__(self, assessment_dao: AssessmentDAO):
        self.assessment_dao = assessment_dao

    async def create_project_assessment(
        self,
        assessment: AdvancedAssessment,
        milestones: List[ProjectMilestone]
    ) -> AdvancedAssessment:
        """Create project assessment with milestones."""
        # AssessmentDAO handles both assessment and milestones
        created_assessment = await self.assessment_dao.create_assessment(assessment)

        for milestone in milestones:
            await self.assessment_dao.create_milestone(milestone)

        return created_assessment

    async def get_assessment_analytics(
        self,
        assessment_id: UUID
    ) -> AssessmentAnalytics:
        """Get analytics for assessment."""
        return await self.assessment_dao.get_analytics_by_assessment(assessment_id)
```

**Key Changes:**
- Import `AssessmentDAO` instead of `AdvancedAssessmentDAO`
- `AssessmentDAO` handles assessments, milestones, and analytics together
- No change to method signatures or behavior (backward compatible)

---

### Example 3: Submission Operations

#### Before (Deprecated):
```python
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO

class SubmissionService:
    def __init__(self, dao: AdvancedAssessmentDAO):
        self.dao = dao

    async def submit_with_artifacts(
        self,
        submission: AssessmentSubmission,
        artifacts: List[PortfolioArtifact]
    ) -> AssessmentSubmission:
        """Submit assessment with portfolio artifacts."""
        created_submission = await self.dao.create_submission(submission)

        for artifact in artifacts:
            await self.dao.create_artifact(artifact)

        return await self.dao.get_submission_by_id(created_submission.id)

    async def get_submissions_to_grade(
        self,
        course_id: UUID,
        instructor_id: UUID
    ) -> List[AssessmentSubmission]:
        """Get submissions awaiting grading."""
        return await self.dao.get_submissions_to_grade(
            course_id,
            instructor_id
        )
```

#### After (Recommended):
```python
from content_management.data_access.submission_dao import SubmissionDAO

class SubmissionService:
    def __init__(self, submission_dao: SubmissionDAO):
        self.submission_dao = submission_dao

    async def submit_with_artifacts(
        self,
        submission: AssessmentSubmission,
        artifacts: List[PortfolioArtifact]
    ) -> AssessmentSubmission:
        """Submit assessment with portfolio artifacts."""
        created_submission = await self.submission_dao.create_submission(submission)

        for artifact in artifacts:
            await self.submission_dao.create_artifact(artifact)

        return await self.submission_dao.get_submission_by_id(created_submission.id)

    async def get_submissions_to_grade(
        self,
        course_id: UUID,
        instructor_id: UUID
    ) -> List[AssessmentSubmission]:
        """Get submissions awaiting grading."""
        return await self.submission_dao.get_submissions_to_grade(
            course_id,
            instructor_id
        )
```

**Key Changes:**
- Import `SubmissionDAO` instead of `AdvancedAssessmentDAO`
- `SubmissionDAO` handles submissions and artifacts together
- Grading queue queries moved to `SubmissionDAO`

---

### Example 4: Peer Review Operations

#### Before (Deprecated):
```python
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO

class PeerReviewService:
    def __init__(self, dao: AdvancedAssessmentDAO):
        self.dao = dao

    async def assign_peer_reviews(
        self,
        assignments: List[PeerReviewAssignment]
    ) -> List[PeerReviewAssignment]:
        """Assign submissions for peer review."""
        created = []
        for assignment in assignments:
            created.append(
                await self.dao.create_peer_review_assignment(assignment)
            )
        return created

    async def submit_peer_review(
        self,
        review: PeerReview
    ) -> PeerReview:
        """Submit peer review for assigned submission."""
        return await self.dao.create_peer_review(review)
```

#### After (Recommended):
```python
from content_management.data_access.peer_review_dao import PeerReviewDAO

class PeerReviewService:
    def __init__(self, peer_review_dao: PeerReviewDAO):
        self.peer_review_dao = peer_review_dao

    async def assign_peer_reviews(
        self,
        assignments: List[PeerReviewAssignment]
    ) -> List[PeerReviewAssignment]:
        """Assign submissions for peer review."""
        created = []
        for assignment in assignments:
            created.append(
                await self.peer_review_dao.create_peer_review_assignment(assignment)
            )
        return created

    async def submit_peer_review(
        self,
        review: PeerReview
    ) -> PeerReview:
        """Submit peer review for assigned submission."""
        return await self.peer_review_dao.create_peer_review(review)
```

**Key Changes:**
- Import `PeerReviewDAO` instead of `AdvancedAssessmentDAO`
- Specialized DAO for peer review workflows

---

### Example 5: Complex Service Using Multiple DAOs

#### Before (Deprecated):
```python
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO

class CompleteAssessmentWorkflowService:
    """
    Orchestrates complete assessment workflow:
    1. Create assessment with rubric
    2. Students submit with artifacts
    3. Instructor evaluates using rubric
    4. Track analytics
    """

    def __init__(self, dao: AdvancedAssessmentDAO):
        self.dao = dao

    async def create_assessment_workflow(
        self,
        assessment: AdvancedAssessment,
        rubric: AssessmentRubric
    ) -> Dict[str, Any]:
        """Create assessment with associated rubric."""
        created_rubric = await self.dao.create_rubric(rubric)

        assessment.rubric_id = created_rubric.id
        created_assessment = await self.dao.create_assessment(assessment)

        return {
            "assessment": created_assessment,
            "rubric": created_rubric
        }

    async def grade_submission(
        self,
        submission_id: UUID,
        evaluation: RubricEvaluation
    ) -> Dict[str, Any]:
        """Grade submission and update analytics."""
        # Create evaluation
        created_evaluation = await self.dao.create_evaluation(evaluation)

        # Get submission for score update
        submission = await self.dao.get_submission_by_id(submission_id)
        submission.score = evaluation.total_score
        submission.status = SubmissionStatus.GRADED
        updated_submission = await self.dao.update_submission(submission)

        # Update analytics
        analytics = await self.dao.get_analytics_by_assessment(
            submission.assessment_id
        )
        # ... analytics update logic ...

        return {
            "evaluation": created_evaluation,
            "submission": updated_submission,
            "analytics": analytics
        }
```

#### After (Recommended):
```python
from content_management.data_access.rubric_dao import RubricDAO
from content_management.data_access.assessment_dao import AssessmentDAO
from content_management.data_access.submission_dao import SubmissionDAO

class CompleteAssessmentWorkflowService:
    """
    Orchestrates complete assessment workflow:
    1. Create assessment with rubric
    2. Students submit with artifacts
    3. Instructor evaluates using rubric
    4. Track analytics

    NOTE: This service now uses multiple specialized DAOs for better
    separation of concerns and testability.
    """

    def __init__(
        self,
        rubric_dao: RubricDAO,
        assessment_dao: AssessmentDAO,
        submission_dao: SubmissionDAO
    ):
        self.rubric_dao = rubric_dao
        self.assessment_dao = assessment_dao
        self.submission_dao = submission_dao

    async def create_assessment_workflow(
        self,
        assessment: AdvancedAssessment,
        rubric: AssessmentRubric
    ) -> Dict[str, Any]:
        """Create assessment with associated rubric."""
        # Use RubricDAO for rubric creation
        created_rubric = await self.rubric_dao.create_rubric(rubric)

        # Use AssessmentDAO for assessment creation
        assessment.rubric_id = created_rubric.id
        created_assessment = await self.assessment_dao.create_assessment(assessment)

        return {
            "assessment": created_assessment,
            "rubric": created_rubric
        }

    async def grade_submission(
        self,
        submission_id: UUID,
        evaluation: RubricEvaluation
    ) -> Dict[str, Any]:
        """Grade submission and update analytics."""
        # Use RubricDAO for evaluation
        created_evaluation = await self.rubric_dao.create_evaluation(evaluation)

        # Use SubmissionDAO for submission update
        submission = await self.submission_dao.get_submission_by_id(submission_id)
        submission.score = evaluation.total_score
        submission.status = SubmissionStatus.GRADED
        updated_submission = await self.submission_dao.update_submission(submission)

        # Use AssessmentDAO for analytics
        analytics = await self.assessment_dao.get_analytics_by_assessment(
            submission.assessment_id
        )
        # ... analytics update logic ...

        return {
            "evaluation": created_evaluation,
            "submission": updated_submission,
            "analytics": analytics
        }
```

**Key Changes:**
- Inject **3 specialized DAOs** instead of 1 monolithic DAO
- Each DAO handles its domain responsibility
- Service layer orchestrates across DAOs
- Better testability (can mock each DAO independently)
- Clearer dependencies (explicit about what data service needs)

---

## Container (Dependency Injection) Updates

### Before (Deprecated):
```python
# services/content-management/infrastructure/container.py

class Container:
    def __init__(self, config: DictConfig):
        self._db_pool = None
        self._advanced_assessment_dao = None

    def get_advanced_assessment_dao(self) -> AdvancedAssessmentDAO:
        """Get singleton instance of AdvancedAssessmentDAO."""
        if not self._advanced_assessment_dao:
            self._advanced_assessment_dao = AdvancedAssessmentDAO(self._db_pool)
        return self._advanced_assessment_dao

    def get_assessment_service(self) -> AdvancedAssessmentService:
        """Get assessment service with DAO injected."""
        return AdvancedAssessmentService(
            dao=self.get_advanced_assessment_dao()
        )
```

### After (Recommended):
```python
# services/content-management/infrastructure/container.py

from content_management.data_access.rubric_dao import RubricDAO
from content_management.data_access.assessment_dao import AssessmentDAO
from content_management.data_access.submission_dao import SubmissionDAO
from content_management.data_access.peer_review_dao import PeerReviewDAO

class Container:
    def __init__(self, config: DictConfig):
        self._db_pool = None
        self._rubric_dao = None
        self._assessment_dao = None
        self._submission_dao = None
        self._peer_review_dao = None

    # Specialized DAO factory methods
    def get_rubric_dao(self) -> RubricDAO:
        """Get singleton instance of RubricDAO."""
        if not self._rubric_dao:
            self._rubric_dao = RubricDAO(self._db_pool)
        return self._rubric_dao

    def get_assessment_dao(self) -> AssessmentDAO:
        """Get singleton instance of AssessmentDAO."""
        if not self._assessment_dao:
            self._assessment_dao = AssessmentDAO(self._db_pool)
        return self._assessment_dao

    def get_submission_dao(self) -> SubmissionDAO:
        """Get singleton instance of SubmissionDAO."""
        if not self._submission_dao:
            self._submission_dao = SubmissionDAO(self._db_pool)
        return self._submission_dao

    def get_peer_review_dao(self) -> PeerReviewDAO:
        """Get singleton instance of PeerReviewDAO."""
        if not self._peer_review_dao:
            self._peer_review_dao = PeerReviewDAO(self._db_pool)
        return self._peer_review_dao

    # Service factory methods (inject specialized DAOs)
    def get_assessment_service(self) -> AdvancedAssessmentService:
        """Get assessment service with specialized DAOs injected."""
        return AdvancedAssessmentService(
            rubric_dao=self.get_rubric_dao(),
            assessment_dao=self.get_assessment_dao(),
            submission_dao=self.get_submission_dao(),
            peer_review_dao=self.get_peer_review_dao()
        )
```

**Key Changes:**
- Add factory methods for each specialized DAO
- Services receive specific DAOs they need (not monolithic DAO)
- Singleton pattern maintained per DAO

---

## Test Migration Examples

### Before (Deprecated):
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_advanced_assessment_dao():
    """Mock the monolithic AdvancedAssessmentDAO."""
    dao = MagicMock(spec=AdvancedAssessmentDAO)

    # Mock ALL methods (tedious for 50+ methods)
    dao.create_rubric = AsyncMock(return_value=sample_rubric)
    dao.create_assessment = AsyncMock(return_value=sample_assessment)
    dao.create_submission = AsyncMock(return_value=sample_submission)
    dao.create_peer_review_assignment = AsyncMock(return_value=sample_assignment)
    # ... 46 more method mocks ...

    return dao

async def test_assessment_service_create_rubric(mock_advanced_assessment_dao):
    """Test rubric creation via service."""
    service = AdvancedAssessmentService(dao=mock_advanced_assessment_dao)

    result = await service.create_rubric(sample_rubric)

    mock_advanced_assessment_dao.create_rubric.assert_called_once_with(sample_rubric)
    assert result == sample_rubric
```

### After (Recommended):
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_rubric_dao():
    """Mock the specialized RubricDAO."""
    dao = MagicMock(spec=RubricDAO)

    # Mock only rubric-related methods (focused, ~12 methods)
    dao.create_rubric = AsyncMock(return_value=sample_rubric)
    dao.get_rubric_by_id = AsyncMock(return_value=sample_rubric)
    dao.create_evaluation = AsyncMock(return_value=sample_evaluation)
    # ... ~9 more rubric method mocks ...

    return dao

@pytest.fixture
def mock_assessment_dao():
    """Mock the specialized AssessmentDAO."""
    dao = MagicMock(spec=AssessmentDAO)

    # Mock only assessment-related methods (~15 methods)
    dao.create_assessment = AsyncMock(return_value=sample_assessment)
    dao.get_assessment_by_id = AsyncMock(return_value=sample_assessment)
    # ... ~13 more assessment method mocks ...

    return dao

async def test_assessment_service_create_rubric(mock_rubric_dao):
    """Test rubric creation via service."""
    # Only need RubricDAO mock for this test
    service = AdvancedAssessmentService(
        rubric_dao=mock_rubric_dao,
        assessment_dao=None,  # Not needed for this test
        submission_dao=None,
        peer_review_dao=None
    )

    result = await service.create_rubric(sample_rubric)

    mock_rubric_dao.create_rubric.assert_called_once_with(sample_rubric)
    assert result == sample_rubric
```

**Benefits:**
- **Focused mocks:** Only mock methods you need for specific test
- **Faster test setup:** Don't mock 50 methods when you need 3
- **Clearer test intent:** Obvious which DAO operations are being tested
- **Better isolation:** Test rubric logic without mocking submission logic

---

## API Endpoint Migration

### Before (Deprecated):
```python
# services/content-management/api/assessment_endpoints.py

from fastapi import APIRouter, Depends
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO

router = APIRouter()

async def get_dao() -> AdvancedAssessmentDAO:
    """Dependency injection for DAO."""
    container = get_container()
    return container.get_advanced_assessment_dao()

@router.post("/rubrics")
async def create_rubric(
    rubric: AssessmentRubricCreate,
    dao: AdvancedAssessmentDAO = Depends(get_dao)
):
    """Create a new assessment rubric."""
    created = await dao.create_rubric(rubric.to_entity())
    return AssessmentRubricResponse.from_entity(created)

@router.post("/assessments")
async def create_assessment(
    assessment: AdvancedAssessmentCreate,
    dao: AdvancedAssessmentDAO = Depends(get_dao)
):
    """Create a new assessment."""
    created = await dao.create_assessment(assessment.to_entity())
    return AdvancedAssessmentResponse.from_entity(created)
```

### After (Recommended):
```python
# services/content-management/api/assessment_endpoints.py

from fastapi import APIRouter, Depends
from content_management.data_access.rubric_dao import RubricDAO
from content_management.data_access.assessment_dao import AssessmentDAO

router = APIRouter()

async def get_rubric_dao() -> RubricDAO:
    """Dependency injection for RubricDAO."""
    container = get_container()
    return container.get_rubric_dao()

async def get_assessment_dao() -> AssessmentDAO:
    """Dependency injection for AssessmentDAO."""
    container = get_container()
    return container.get_assessment_dao()

@router.post("/rubrics")
async def create_rubric(
    rubric: AssessmentRubricCreate,
    rubric_dao: RubricDAO = Depends(get_rubric_dao)
):
    """Create a new assessment rubric."""
    created = await rubric_dao.create_rubric(rubric.to_entity())
    return AssessmentRubricResponse.from_entity(created)

@router.post("/assessments")
async def create_assessment(
    assessment: AdvancedAssessmentCreate,
    assessment_dao: AssessmentDAO = Depends(get_assessment_dao)
):
    """Create a new assessment."""
    created = await assessment_dao.create_assessment(assessment.to_entity())
    return AdvancedAssessmentResponse.from_entity(created)
```

**Key Changes:**
- Separate dependency injection functions per DAO
- Endpoints depend on specific DAOs they need
- Clear dependency declarations (explicit > implicit)

---

## Common Pitfalls and Solutions

### Pitfall 1: Importing Wrong DAO

**Problem:**
```python
# Still importing deprecated DAO
from content_management.data_access.advanced_assessment_dao import AdvancedAssessmentDAO
```

**Solution:**
```python
# Import specialized DAOs
from content_management.data_access.rubric_dao import RubricDAO
from content_management.data_access.assessment_dao import AssessmentDAO
from content_management.data_access.submission_dao import SubmissionDAO
from content_management.data_access.peer_review_dao import PeerReviewDAO
```

**Detection:** Use linter/IDE warnings for deprecated imports

---

### Pitfall 2: Creating DAO Directly Instead of Via Container

**Problem:**
```python
# Manual instantiation bypasses singleton pattern
rubric_dao = RubricDAO(db_pool)
```

**Solution:**
```python
# Use container for dependency injection
container = get_container()
rubric_dao = container.get_rubric_dao()
```

**Why:** Container ensures singleton pattern, connection pooling, and consistent configuration

---

### Pitfall 3: Mixing Old and New DAOs

**Problem:**
```python
# Inconsistent mixing of old and new
def __init__(
    self,
    old_dao: AdvancedAssessmentDAO,  # Deprecated
    rubric_dao: RubricDAO  # New
):
    self.old_dao = old_dao
    self.rubric_dao = rubric_dao
```

**Solution:**
```python
# Use only new DAOs
def __init__(
    self,
    rubric_dao: RubricDAO,
    assessment_dao: AssessmentDAO,
    submission_dao: SubmissionDAO
):
    self.rubric_dao = rubric_dao
    self.assessment_dao = assessment_dao
    self.submission_dao = submission_dao
```

**Why:** Complete migration prevents confusion and enables eventual removal of old DAO

---

### Pitfall 4: Not Updating Tests After Migration

**Problem:**
```python
# Test still uses old DAO mock
@pytest.fixture
def mock_dao():
    return MagicMock(spec=AdvancedAssessmentDAO)
```

**Solution:**
```python
# Update to specialized DAO mocks
@pytest.fixture
def mock_rubric_dao():
    return MagicMock(spec=RubricDAO)

@pytest.fixture
def mock_assessment_dao():
    return MagicMock(spec=AssessmentDAO)
```

**Detection:** Tests fail with attribute errors for methods not on old DAO

---

## Backward Compatibility Notes

### During Deprecation Period (2 releases)

1. **Old DAO Still Available:**
   - `AdvancedAssessmentDAO` remains in codebase (deprecated)
   - Marked with deprecation warnings
   - Documentation clearly states "use new DAOs instead"

2. **Gradual Migration Supported:**
   - Can mix old and new DAOs temporarily (not recommended)
   - Old DAO delegates to new DAOs internally
   - No breaking API changes

3. **Competency Operations:**
   - Remain in `AdvancedAssessmentDAO` (not yet refactored)
   - Will be extracted to `CompetencyDAO` in future release
   - For now, still use `AdvancedAssessmentDAO` for competencies

### Post-Removal (v4.0.0+)

1. **Breaking Changes:**
   - `AdvancedAssessmentDAO` class removed entirely
   - Imports will fail if not migrated
   - Tests using old DAO will fail

2. **Migration Required:**
   - All services must use specialized DAOs
   - All tests must mock specialized DAOs
   - All API endpoints must inject specialized DAOs

---

## Rollback Plan

If critical bugs discovered post-migration:

### Option 1: Quick Rollback (Deprecation Period Only)

1. Revert service layer to use `AdvancedAssessmentDAO`
2. Revert container to inject old DAO
3. Keep new DAOs in codebase (no-op)
4. File bugs for discovered issues
5. Re-attempt migration after fixes

### Option 2: Hotfix New DAOs

1. Identify bug in specific specialized DAO
2. Apply hotfix to that DAO only
3. Run targeted tests for that DAO
4. Deploy hotfix without full rollback
5. Update migration guide with learnings

### Option 3: Feature Flag Toggle

1. Add feature flag: `USE_SPECIALIZED_ASSESSMENT_DAOS`
2. Service layer checks flag at runtime
3. If false, use old `AdvancedAssessmentDAO`
4. If true, use new specialized DAOs
5. Gradual rollout with monitoring

---

## Support and Questions

### During Migration

- **Documentation:** This guide + [Refactoring Plan](/docs/ADVANCED_ASSESSMENT_DAO_REFACTORING_PLAN.md)
- **Code Examples:** See examples above
- **Test Examples:** `/tests/unit/content_management/test_rubric_dao.py`
- **Questions:** Contact backend team lead or file GitHub issue

### Post-Migration Support

- **Bugs:** File GitHub issues with label `assessment-dao-refactoring`
- **Questions:** Team Slack channel #backend-architecture
- **Code Reviews:** Tag @backend-team-lead for DAO-related PRs

---

## Timeline

| Milestone | Date | Status |
|-----------|------|--------|
| Refactoring Complete | TBD | Pending |
| Deprecation Notice Added | TBD | Pending |
| Migration Guide Published | TBD | In Progress |
| First Deprecation Release (v3.8.0) | TBD | Planned |
| Second Deprecation Release (v3.9.0) | TBD | Planned |
| Old DAO Removal (v4.0.0) | Q2 2026 | Planned |

---

## Change Summary Table

| Operation | Old Import | New Import | Notes |
|-----------|-----------|------------|-------|
| Rubric CRUD | `AdvancedAssessmentDAO` | `RubricDAO` | Includes evaluations |
| Assessment CRUD | `AdvancedAssessmentDAO` | `AssessmentDAO` | Includes milestones, analytics |
| Submission CRUD | `AdvancedAssessmentDAO` | `SubmissionDAO` | Includes artifacts |
| Peer Review | `AdvancedAssessmentDAO` | `PeerReviewDAO` | Assignments + reviews |
| Competencies | `AdvancedAssessmentDAO` | `AdvancedAssessmentDAO` | **NOT MIGRATED YET** |

---

**Document Version:** 1.0
**Last Updated:** 2026-02-05
**Maintainer:** Backend Architecture Team
**Status:** Draft (Pre-Implementation)
