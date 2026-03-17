# Advanced Assessment DAO Refactoring Plan

**Version:** 1.0
**Date:** 2026-02-05
**Status:** Proposed
**Complexity:** HIGH (2,842 lines → 4 specialized DAOs)

## Executive Summary

The `AdvancedAssessmentDAO` (2,842 lines) is a god class violating the Single Responsibility Principle. This document outlines a refactoring strategy to split it into 4 specialized DAOs following Test-Driven Development (TDD) principles.

---

## Current State Analysis

### File Location
`/home/bbrelin/course-creator/services/content-management/data_access/advanced_assessment_dao.py`

### Responsibility Groups (9 identified)

| Section | Lines | Responsibilities | Methods |
|---------|-------|------------------|---------|
| **Assessment Rubric Operations** | 108-475 (368 lines) | Create/read/update/delete rubrics with criteria and performance levels | `create_rubric`, `get_rubric_by_id`, `get_rubrics_by_course`, `get_template_rubrics`, `update_rubric`, `delete_rubric`, `_create_criterion`, `_create_performance_level`, `_get_criteria_for_rubric` |
| **Advanced Assessment Operations** | 477-831 (355 lines) | CRUD for assessments (projects, portfolios, peer reviews) | `create_assessment`, `get_assessment_by_id`, `get_assessments_by_course`, `get_available_assessments`, `update_assessment`, `delete_assessment`, `_get_milestones_for_assessment` |
| **Project Milestone Operations** | 833-1013 (181 lines) | Manage project milestones for assessments | `_create_milestone`, `create_milestone`, `get_milestone_by_id`, `update_milestone`, `delete_milestone` |
| **Assessment Submission Operations** | 1015-1406 (392 lines) | Student submission CRUD, grading workflows | `create_submission`, `get_submission_by_id`, `get_submissions_by_assessment`, `get_student_submissions`, `get_latest_submission`, `get_best_submission`, `update_submission`, `get_submissions_to_grade`, `_get_artifacts_for_submission` |
| **Portfolio Artifact Operations** | 1408-1625 (218 lines) | Manage portfolio artifacts attached to submissions | `_create_artifact`, `create_artifact`, `get_artifact_by_id`, `update_artifact`, `delete_artifact` |
| **Rubric Evaluation Operations** | 1627-1745 (119 lines) | Apply rubrics to submissions for grading | `create_evaluation`, `get_evaluations_for_submission`, `update_evaluation` |
| **Peer Review Operations** | 1747-2064 (318 lines) | Peer review assignment and review workflows | `create_peer_review_assignment`, `get_peer_assignment_by_id`, `get_assignments_for_reviewer`, `get_assignments_for_submission`, `update_peer_assignment`, `create_peer_review`, `get_peer_review_by_id`, `get_reviews_for_submission`, `update_peer_review` |
| **Competency Operations** | 2066-2400 (335 lines) | Competency tracking and progress | `create_competency`, `get_competency_by_id`, `get_competency_by_code`, `get_competencies_by_organization`, `update_competency`, `create_competency_progress`, `get_student_competency_progress`, `get_student_competencies`, `update_competency_progress` |
| **Assessment Analytics Operations** | 2402-2842 (441 lines) | Assessment metrics and analytics | `create_or_update_analytics`, `get_analytics_by_assessment`, helper methods for analytics calculation |

### Problems with Current Design

1. **Violates Single Responsibility Principle (SRP)**
   - Single class handles 9 distinct responsibilities
   - Changes to rubrics affect same file as peer reviews
   - Difficult to reason about class boundaries

2. **High Coupling**
   - All assessment-related operations tightly coupled
   - Cannot test rubrics independently from submissions
   - Shared state and helper methods create hidden dependencies

3. **Maintainability Issues**
   - 2,842 lines in single file overwhelming for developers
   - Difficult to navigate and understand
   - Merge conflicts likely with multiple developers

4. **Testing Challenges**
   - Single test file would be massive (300+ tests)
   - Cannot run rubric tests independently from submission tests
   - Test setup/teardown complexity multiplies

5. **Deployment Risks**
   - Changes to one assessment type (e.g., rubrics) risk breaking another (e.g., peer reviews)
   - Difficult to isolate bugs
   - Large blast radius for any change

---

## Proposed Refactoring

### Target Architecture: 4 Specialized DAOs

#### 1. RubricDAO (~490 lines)
**Responsibilities:**
- Assessment rubric CRUD
- Rubric criteria and performance levels management
- Rubric evaluation operations
- Template rubric management

**Methods:**
```python
# Rubric Operations
async def create_rubric(rubric: AssessmentRubric, conn: Optional[Connection] = None) -> AssessmentRubric
async def get_rubric_by_id(rubric_id: UUID, conn: Optional[Connection] = None) -> Optional[AssessmentRubric]
async def get_rubrics_by_course(course_id: UUID, limit: int = 100, offset: int = 0, conn: Optional[Connection] = None) -> List[AssessmentRubric]
async def get_template_rubrics(organization_id: UUID, limit: int = 100, offset: int = 0, conn: Optional[Connection] = None) -> List[AssessmentRubric]
async def update_rubric(rubric: AssessmentRubric, conn: Optional[Connection] = None) -> AssessmentRubric
async def delete_rubric(rubric_id: UUID, conn: Optional[Connection] = None) -> bool

# Criterion Operations (private helpers)
async def _create_criterion(criterion: RubricCriterion, rubric_id: UUID, conn: Connection) -> None
async def _create_performance_level(level: RubricPerformanceLevel, criterion_id: UUID, conn: Connection) -> None
async def _get_criteria_for_rubric(rubric_id: UUID, conn: Connection) -> List[RubricCriterion]

# Evaluation Operations
async def create_evaluation(evaluation: RubricEvaluation, conn: Optional[Connection] = None) -> RubricEvaluation
async def get_evaluations_for_submission(submission_id: UUID, conn: Optional[Connection] = None) -> List[RubricEvaluation]
async def update_evaluation(evaluation: RubricEvaluation, conn: Optional[Connection] = None) -> RubricEvaluation

# Row conversion helpers
def _row_to_rubric(row: Record, criteria: List[RubricCriterion]) -> AssessmentRubric
def _row_to_criterion(row: Record, performance_levels: List[RubricPerformanceLevel]) -> RubricCriterion
def _row_to_performance_level(row: Record) -> RubricPerformanceLevel
def _row_to_evaluation(row: Record) -> RubricEvaluation
```

**Database Tables:**
- `assessment_rubrics`
- `rubric_criteria`
- `rubric_performance_levels`
- `rubric_evaluations`

**Test Coverage:** 40-50 tests
- Rubric creation with nested structures
- Template vs course rubrics
- Weighted criteria validation
- Evaluation score calculation
- Organization/course isolation

---

#### 2. AssessmentDAO (~985 lines)
**Responsibilities:**
- Advanced assessment CRUD (projects, portfolios, presentations)
- Project milestone management
- Assessment analytics

**Methods:**
```python
# Assessment Operations
async def create_assessment(assessment: AdvancedAssessment, conn: Optional[Connection] = None) -> AdvancedAssessment
async def get_assessment_by_id(assessment_id: UUID, conn: Optional[Connection] = None) -> Optional[AdvancedAssessment]
async def get_assessments_by_course(course_id: UUID, assessment_type: Optional[AssessmentType] = None, status: Optional[AssessmentStatus] = None, limit: int = 100, offset: int = 0, conn: Optional[Connection] = None) -> List[AdvancedAssessment]
async def get_available_assessments(course_id: UUID, student_id: UUID, conn: Optional[Connection] = None) -> List[AdvancedAssessment]
async def update_assessment(assessment: AdvancedAssessment, conn: Optional[Connection] = None) -> AdvancedAssessment
async def delete_assessment(assessment_id: UUID, conn: Optional[Connection] = None) -> bool

# Milestone Operations
async def create_milestone(milestone: ProjectMilestone, conn: Optional[Connection] = None) -> ProjectMilestone
async def get_milestone_by_id(milestone_id: UUID, conn: Optional[Connection] = None) -> Optional[ProjectMilestone]
async def update_milestone(milestone: ProjectMilestone, conn: Optional[Connection] = None) -> ProjectMilestone
async def delete_milestone(milestone_id: UUID, conn: Optional[Connection] = None) -> bool
async def _create_milestone(milestone: ProjectMilestone, assessment_id: UUID, conn: Connection) -> None
async def _get_milestones_for_assessment(assessment_id: UUID, conn: Connection) -> List[ProjectMilestone]

# Analytics Operations
async def create_or_update_analytics(analytics: AssessmentAnalytics, conn: Optional[Connection] = None) -> AssessmentAnalytics
async def get_analytics_by_assessment(assessment_id: UUID, conn: Optional[Connection] = None) -> Optional[AssessmentAnalytics]

# Row conversion helpers
def _row_to_assessment(row: Record, milestones: List[ProjectMilestone]) -> AdvancedAssessment
def _row_to_milestone(row: Record) -> ProjectMilestone
def _row_to_analytics(row: Record) -> AssessmentAnalytics
```

**Database Tables:**
- `advanced_assessments`
- `project_milestones`
- `assessment_analytics`

**Test Coverage:** 50-60 tests
- Assessment lifecycle (draft → published → completed → archived)
- Milestone dependencies and deadlines
- Assessment availability windows
- Analytics aggregation
- Assessment type variations (project, portfolio, presentation)

---

#### 3. SubmissionDAO (~620 lines)
**Responsibilities:**
- Assessment submission CRUD
- Portfolio artifact management
- Submission queries (by student, by assessment, grading queue)

**Methods:**
```python
# Submission Operations
async def create_submission(submission: AssessmentSubmission, conn: Optional[Connection] = None) -> AssessmentSubmission
async def get_submission_by_id(submission_id: UUID, conn: Optional[Connection] = None) -> Optional[AssessmentSubmission]
async def get_submissions_by_assessment(assessment_id: UUID, status: Optional[SubmissionStatus] = None, limit: int = 100, offset: int = 0, conn: Optional[Connection] = None) -> List[AssessmentSubmission]
async def get_student_submissions(student_id: UUID, assessment_id: UUID, conn: Optional[Connection] = None) -> List[AssessmentSubmission]
async def get_latest_submission(student_id: UUID, assessment_id: UUID, conn: Optional[Connection] = None) -> Optional[AssessmentSubmission]
async def get_best_submission(student_id: UUID, assessment_id: UUID, conn: Optional[Connection] = None) -> Optional[AssessmentSubmission]
async def update_submission(submission: AssessmentSubmission, conn: Optional[Connection] = None) -> AssessmentSubmission
async def get_submissions_to_grade(course_id: UUID, instructor_id: UUID, limit: int = 50, offset: int = 0, conn: Optional[Connection] = None) -> List[AssessmentSubmission]

# Artifact Operations
async def create_artifact(artifact: PortfolioArtifact, conn: Optional[Connection] = None) -> PortfolioArtifact
async def get_artifact_by_id(artifact_id: UUID, conn: Optional[Connection] = None) -> Optional[PortfolioArtifact]
async def update_artifact(artifact: PortfolioArtifact, conn: Optional[Connection] = None) -> PortfolioArtifact
async def delete_artifact(artifact_id: UUID, conn: Optional[Connection] = None) -> bool
async def _create_artifact(artifact: PortfolioArtifact, submission_id: UUID, conn: Connection) -> None
async def _get_artifacts_for_submission(submission_id: UUID, conn: Connection) -> List[PortfolioArtifact]

# Row conversion helpers
def _row_to_submission(row: Record, artifacts: List[PortfolioArtifact]) -> AssessmentSubmission
def _row_to_artifact(row: Record) -> PortfolioArtifact
```

**Database Tables:**
- `assessment_submissions`
- `portfolio_artifacts`

**Test Coverage:** 40-50 tests
- Submission attempts and attempts limit
- Late submission handling
- Artifact file management
- Best/latest submission logic
- Grading queue queries
- Submission status transitions

---

#### 4. PeerReviewDAO (~320 lines)
**Responsibilities:**
- Peer review assignment management
- Peer review submission and tracking
- Review assignment algorithms

**Methods:**
```python
# Peer Review Assignment Operations
async def create_peer_review_assignment(assignment: PeerReviewAssignment, conn: Optional[Connection] = None) -> PeerReviewAssignment
async def get_peer_assignment_by_id(assignment_id: UUID, conn: Optional[Connection] = None) -> Optional[PeerReviewAssignment]
async def get_assignments_for_reviewer(reviewer_id: UUID, assessment_id: UUID, conn: Optional[Connection] = None) -> List[PeerReviewAssignment]
async def get_assignments_for_submission(submission_id: UUID, conn: Optional[Connection] = None) -> List[PeerReviewAssignment]
async def update_peer_assignment(assignment: PeerReviewAssignment, conn: Optional[Connection] = None) -> PeerReviewAssignment

# Peer Review Operations
async def create_peer_review(review: PeerReview, conn: Optional[Connection] = None) -> PeerReview
async def get_peer_review_by_id(review_id: UUID, conn: Optional[Connection] = None) -> Optional[PeerReview]
async def get_reviews_for_submission(submission_id: UUID, conn: Optional[Connection] = None) -> List[PeerReview]
async def update_peer_review(review: PeerReview, conn: Optional[Connection] = None) -> PeerReview

# Row conversion helpers
def _row_to_peer_assignment(row: Record) -> PeerReviewAssignment
def _row_to_peer_review(row: Record) -> PeerReview
```

**Database Tables:**
- `peer_review_assignments`
- `peer_reviews`

**Test Coverage:** 30-40 tests
- Assignment creation and distribution
- Review submission and validation
- Reviewer anonymity
- Review rubric application
- Review deadlines

---

### DAO Relationships

```
┌──────────────────┐
│  RubricDAO       │────┐
│                  │    │
│ - Rubrics        │    │ (used by)
│ - Criteria       │    │
│ - Performance    │    │
│   Levels         │    │
│ - Evaluations    │    │
└──────────────────┘    │
                        │
┌──────────────────┐    │
│  AssessmentDAO   │◄───┘
│                  │
│ - Assessments    │────┐
│ - Milestones     │    │
│ - Analytics      │    │
└──────────────────┘    │
                        │ (generates)
┌──────────────────┐    │
│  SubmissionDAO   │◄───┘
│                  │
│ - Submissions    │────┐
│ - Artifacts      │    │
└──────────────────┘    │
                        │ (creates)
┌──────────────────┐    │
│  PeerReviewDAO   │◄───┘
│                  │
│ - Assignments    │
│ - Reviews        │
└──────────────────┘
```

**Note:** Competency Operations (~335 lines) will remain in AdvancedAssessmentDAO as it's a separate concern spanning multiple domains. Can be extracted to CompetencyDAO in future iteration if needed.

---

## Implementation Plan (TDD Approach)

### Phase 1: Test Creation (Red Phase) - Estimated 16 hours
**Goal:** Write comprehensive unit tests for all 4 DAOs (160-240 tests total)

1. **RubricDAO Tests** (4 hours) - 40-50 tests
   - Create `tests/unit/content_management/test_rubric_dao.py`
   - Test classes:
     - `TestRubricCreation` (8 tests)
     - `TestRubricRetrieval` (7 tests)
     - `TestRubricUpdate` (5 tests)
     - `TestRubricDeletion` (4 tests)
     - `TestRubricEvaluation` (8 tests)
     - `TestRubricBusinessRules` (8 tests)
     - `TestRubricPerformanceAndScalability` (3 tests)

2. **AssessmentDAO Tests** (5 hours) - 50-60 tests
   - Create `tests/unit/content_management/test_assessment_dao.py`
   - Test classes:
     - `TestAssessmentCreation` (10 tests)
     - `TestAssessmentRetrieval` (8 tests)
     - `TestAssessmentUpdate` (6 tests)
     - `TestAssessmentDeletion` (4 tests)
     - `TestMilestoneOperations` (8 tests)
     - `TestAssessmentAvailability` (7 tests)
     - `TestAssessmentAnalytics` (8 tests)
     - `TestAssessmentBusinessRules` (8 tests)

3. **SubmissionDAO Tests** (4 hours) - 40-50 tests
   - Create `tests/unit/content_management/test_submission_dao.py`
   - Test classes:
     - `TestSubmissionCreation` (8 tests)
     - `TestSubmissionRetrieval` (8 tests)
     - `TestSubmissionUpdate` (6 tests)
     - `TestArtifactOperations` (8 tests)
     - `TestSubmissionQueries` (8 tests)
     - `TestSubmissionBusinessRules` (8 tests)

4. **PeerReviewDAO Tests** (3 hours) - 30-40 tests
   - Create `tests/unit/content_management/test_peer_review_dao.py`
   - Test classes:
     - `TestPeerReviewAssignment` (8 tests)
     - `TestPeerReviewCreation` (7 tests)
     - `TestPeerReviewRetrieval` (6 tests)
     - `TestPeerReviewUpdate` (5 tests)
     - `TestPeerReviewBusinessRules` (7 tests)

**Deliverable:** All tests written and failing (Red phase complete)

---

### Phase 2: DAO Implementation (Green Phase) - Estimated 20 hours

1. **RubricDAO Implementation** (5 hours)
   - Create `services/content-management/data_access/rubric_dao.py`
   - Implement all methods with proper error handling
   - Comprehensive docstrings explaining business logic
   - Row conversion helpers

2. **AssessmentDAO Implementation** (6 hours)
   - Create `services/content-management/data_access/assessment_dao.py`
   - Implement assessments, milestones, and analytics operations
   - Complex query logic for availability windows

3. **SubmissionDAO Implementation** (5 hours)
   - Create `services/content-management/data_access/submission_dao.py`
   - Implement submissions and artifacts
   - Best/latest submission logic

4. **PeerReviewDAO Implementation** (4 hours)
   - Create `services/content-management/data_access/peer_review_dao.py`
   - Implement assignments and reviews
   - Review assignment distribution logic

**Deliverable:** All tests passing (Green phase complete)

---

### Phase 3: Integration (Refactor Phase) - Estimated 8 hours

1. **Update Container** (2 hours)
   - Modify `services/content-management/infrastructure/container.py`
   - Add factory methods for new DAOs
   ```python
   class Container:
       def __init__(self, config: DictConfig):
           self._rubric_dao: Optional[RubricDAO] = None
           self._assessment_dao: Optional[AssessmentDAO] = None
           self._submission_dao: Optional[SubmissionDAO] = None
           self._peer_review_dao: Optional[PeerReviewDAO] = None

       def get_rubric_dao(self) -> RubricDAO:
           if not self._rubric_dao:
               self._rubric_dao = RubricDAO(self._db_pool)
           return self._rubric_dao

       # Similar for other DAOs...
   ```

2. **Update Service Layer** (3 hours)
   - Modify `AdvancedAssessmentService` to use new DAOs
   - Update service methods to call specialized DAOs
   - Remove dependencies on old DAO

3. **Update API Endpoints** (2 hours)
   - Modify `services/content-management/api/assessment_endpoints.py`
   - Inject new DAOs via container
   - Verify API contract unchanged

4. **Deprecate Old DAO** (1 hour)
   - Add deprecation notice to `AdvancedAssessmentDAO`
   ```python
   """
   ⚠️ DEPRECATED: This god class has been split into specialized DAOs.

   Use the following instead:
   - RubricDAO: Rubric creation, evaluation, and template management
   - AssessmentDAO: Assessment CRUD, milestones, and analytics
   - SubmissionDAO: Submission and artifact management
   - PeerReviewDAO: Peer review assignments and reviews

   This class will be removed in v4.0.0 (target: Q2 2026)

   Migration Guide: /docs/ADVANCED_ASSESSMENT_DAO_MIGRATION_GUIDE.md
   """
   ```

**Deliverable:** Integrated system with all tests passing

---

### Phase 4: Documentation and Testing - Estimated 4 hours

1. **Create Migration Guide** (2 hours)
   - Document for developers
   - Before/after code examples
   - Breaking changes (if any)
   - Rollback procedures

2. **Run Full Test Suite** (1 hour)
   - Unit tests (160-240 new tests)
   - Integration tests (existing tests should still pass)
   - E2E tests for assessment workflows

3. **Performance Validation** (1 hour)
   - Verify no performance regressions
   - Check query efficiency (N+1 problems)
   - Load testing for bulk operations

**Deliverable:** Complete documentation and passing tests

---

## Test Coverage Targets

| DAO | Test Classes | Test Methods | Lines of Code | Coverage Target |
|-----|--------------|--------------|---------------|-----------------|
| RubricDAO | 7 | 40-50 | ~490 | 95% |
| AssessmentDAO | 8 | 50-60 | ~985 | 95% |
| SubmissionDAO | 6 | 40-50 | ~620 | 95% |
| PeerReviewDAO | 5 | 30-40 | ~320 | 95% |
| **Total** | **26** | **160-240** | **~2,415** | **95%** |

---

## Benefits of Refactoring

### 1. SOLID Compliance
- **Single Responsibility Principle**: Each DAO handles one domain concept
- **Open/Closed Principle**: Extend DAOs without modifying existing code
- **Liskov Substitution**: Each DAO can be mocked/stubbed independently
- **Interface Segregation**: Services depend only on DAOs they need
- **Dependency Inversion**: Services depend on DAO abstractions, not implementations

### 2. Improved Maintainability
- Smaller, focused classes easier to understand
- Changes to rubrics don't risk breaking submissions
- Easier to onboard new developers (learn one DAO at a time)
- Reduced cognitive load (400-600 lines vs 2,842 lines)

### 3. Better Testability
- Test DAOs independently
- Run rubric tests without loading submission tests
- Faster test execution (parallel test runs)
- Easier to identify failing test location

### 4. Enhanced Code Reusability
- RubricDAO can be reused for different assessment types
- SubmissionDAO works for quizzes, assignments, and advanced assessments
- PeerReviewDAO portable to other contexts

### 5. Reduced Deployment Risk
- Smaller blast radius for changes
- Easier to isolate bugs
- Can deploy DAO changes independently (with caution)
- Lower risk of merge conflicts

### 6. Performance Optimization Opportunities
- Optimize RubricDAO for rubric-heavy operations
- Cache assessment availability queries in AssessmentDAO
- Implement specialized indexes per DAO
- Easier to identify slow queries

---

## Risks and Mitigation

### Risk 1: Breaking Existing Code
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Comprehensive test coverage before refactoring
- Keep old DAO available during transition period
- Gradual migration (deprecation notice for 2 releases)
- Thorough integration testing

### Risk 2: Performance Regressions
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Benchmark current performance before refactoring
- Performance tests for each DAO
- Query analysis to avoid N+1 problems
- Load testing before production deployment

### Risk 3: Incomplete Migration
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Complete inventory of all DAO usages
- Grep codebase for `AdvancedAssessmentDAO` references
- Update all service layers simultaneously
- Integration tests to verify full migration

### Risk 4: Increased Complexity
**Likelihood:** Low
**Impact:** Low
**Mitigation:**
- Clear documentation of DAO relationships
- Dependency injection via container pattern
- Service layer orchestrates DAOs (not DAOs calling each other)

### Risk 5: Test Maintenance Burden
**Likelihood:** Medium
**Impact:** Low
**Mitigation:**
- Shared test fixtures across DAO tests
- Test helpers for common patterns
- Faker library for test data generation
- Automated test generation tools

---

## Success Criteria

### Quantitative Metrics
1. **Code Organization**
   - ✅ 4 specialized DAOs created (~2,415 lines total)
   - ✅ Average DAO size: 600 lines (vs 2,842 lines original)
   - ✅ 0 god classes (classes > 1,000 lines)

2. **Test Coverage**
   - ✅ 160-240 new unit tests created
   - ✅ 95%+ code coverage on all new DAOs
   - ✅ 0 test failures in existing test suite
   - ✅ 100% backward compatibility maintained

3. **Performance**
   - ✅ 0% performance degradation (baseline maintained)
   - ✅ Query count unchanged or reduced
   - ✅ Response times within 5% of baseline

4. **Documentation**
   - ✅ Migration guide created
   - ✅ All DAOs have comprehensive docstrings
   - ✅ API documentation updated
   - ✅ Architecture diagrams updated

### Qualitative Metrics
1. **Developer Experience**
   - Easier to find relevant code (focused DAOs)
   - Faster to understand specific domain logic
   - Reduced time to implement new features
   - Lower bug introduction rate

2. **Code Quality**
   - SOLID principles compliance
   - Reduced cyclomatic complexity
   - Improved code readability
   - Better separation of concerns

3. **Maintainability**
   - Easier to isolate and fix bugs
   - Reduced merge conflict frequency
   - Simpler code review process
   - Lower risk deployments

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Tests** | 16 hours | 160-240 unit tests (Red phase) |
| **Phase 2: Implementation** | 20 hours | 4 specialized DAOs (Green phase) |
| **Phase 3: Integration** | 8 hours | Updated container, services, APIs |
| **Phase 4: Documentation** | 4 hours | Migration guide, test validation |
| **Total** | **48 hours** | **Complete refactoring** |

**Estimated Calendar Time:** 6 working days (8 hours/day) for single developer

---

## Next Steps

1. **Approval Required:**
   - Review refactoring plan with team
   - Confirm test coverage targets acceptable
   - Agree on timeline and resources

2. **Pre-Refactoring:**
   - Create feature branch: `refactor/advanced-assessment-dao-split`
   - Set up test infrastructure (FakeAsyncPGPool, fixtures)
   - Establish performance baseline

3. **Execution:**
   - Begin Phase 1 (TDD Red Phase)
   - Daily progress updates
   - Code reviews after each phase

4. **Post-Refactoring:**
   - Monitor production metrics
   - Gather developer feedback
   - Schedule old DAO removal (v4.0.0)

---

## References

- **Original DAO:** `/services/content-management/data_access/advanced_assessment_dao.py`
- **Domain Entities:** `/services/content-management/content_management/domain/entities/advanced_assessment.py`
- **Service Layer:** `/services/content-management/content_management/application/services/advanced_assessment_service.py`
- **API Endpoints:** `/services/content-management/api/assessment_endpoints.py`
- **Test Examples:** `/tests/unit/content_management/test_rubric_dao.py` (created)

---

## Appendix A: Sample Test Structure

See `/home/bbrelin/course-creator/tests/unit/content_management/test_rubric_dao.py` for complete example of test organization and coverage.

Key patterns:
- **Arrange-Act-Assert (AAA)** pattern
- **WHAT-WHERE-WHY docstrings** explaining business context
- **Domain-driven test names** (not implementation-focused)
- **Comprehensive edge case coverage**
- **Business rule validation tests**
- **Performance and scalability tests**

---

## Appendix B: Container Pattern Example

```python
# Before (monolithic)
class Container:
    def get_advanced_assessment_dao(self) -> AdvancedAssessmentDAO:
        if not self._advanced_assessment_dao:
            self._advanced_assessment_dao = AdvancedAssessmentDAO(self._db_pool)
        return self._advanced_assessment_dao

# After (specialized)
class Container:
    def get_rubric_dao(self) -> RubricDAO:
        if not self._rubric_dao:
            self._rubric_dao = RubricDAO(self._db_pool)
        return self._rubric_dao

    def get_assessment_dao(self) -> AssessmentDAO:
        if not self._assessment_dao:
            self._assessment_dao = AssessmentDAO(self._db_pool)
        return self._assessment_dao

    def get_submission_dao(self) -> SubmissionDAO:
        if not self._submission_dao:
            self._submission_dao = SubmissionDAO(self._db_pool)
        return self._submission_dao

    def get_peer_review_dao(self) -> PeerReviewDAO:
        if not self._peer_review_dao:
            self._peer_review_dao = PeerReviewDAO(self._db_pool)
        return self._peer_review_dao
```

---

**Document Status:** Ready for Review
**Author:** Claude Code (Advanced Assessment DAO Refactoring Agent)
**Last Updated:** 2026-02-05
