# Microservices Test Refactoring - Master Plan

## Overview

Comprehensive refactoring of all microservice test suites to ensure consistent quality, coverage, and maintainability across the entire Course Creator Platform.

## Microservices Analysis

### Services to Refactor
1. ✅ **analytics** (port 8001) - Learning analytics and metrics
2. ✅ **content-management** (port 8002) - Course content CRUD
3. ✅ **content-storage** (port 8003) - File storage and retrieval
4. ✅ **course-generator** (port 8000) - AI course generation with RAG
5. ✅ **course-management** (port 8004) - Course lifecycle + videos
6. ✅ **demo-service** (port 8010) - Demo data generation
7. ✅ **lab-manager** (port 8005) - Docker lab containers
8. ✅ **organization-management** (port 8006) - Multi-tenant RBAC
9. ✅ **user-management** (port 8007) - Authentication and users
10. ✅ **rag-service** (port 8009) - RAG for progressive learning

## Current Test Coverage Status

### Existing Tests
```
tests/unit/
├── analytics/           - 2 files (test_analytics_service.py, test_domain_entities.py)
├── backend/            - 4 files (content generation, session, endpoints)
├── content_management/ - 1 file (test_domain_entities.py)
├── course_generator/   - 1 file (test_domain_entities.py)
├── course_videos/      - 4 files (COMPLETE - newly created)
├── demo_service/       - 1 file (test_demo_api_endpoints.py)
├── lab_container/      - 1 file (test_lab_manager_service.py)
├── organization_management/ - 5 files (endpoints, service, tracks)
├── rbac/               - Comprehensive (RBAC system)
├── user_management/    - 2 files (domain entities, student login)
└── services/           - 5 files (service integration tests)
```

### Test Types Needed Per Service
1. **Unit Tests** - Models, services, utilities
2. **API Tests** - Endpoint validation, auth, errors
3. **DAO Tests** - Database operations
4. **Integration Tests** - Service interactions
5. **E2E Tests** - Complete user workflows

## Refactoring Strategy

### Phase 1: Fix Import Paths (CRITICAL)
All new tests need proper Python path configuration to import from services.

**Solution**: Create `tests/conftest.py`:
```python
import sys
from pathlib import Path

# Add all service directories to Python path
project_root = Path(__file__).parent.parent
services_dir = project_root / 'services'

# Add each service to path
for service_dir in services_dir.iterdir():
    if service_dir.is_dir() and not service_dir.name.startswith('.'):
        sys.path.insert(0, str(service_dir))
```

### Phase 2: Service-by-Service Refactoring

#### 1. Analytics Service (Port 8001)
**Existing**: 2 test files
**Add**:
- `test_analytics_dao.py` - Database operations for metrics
- `test_analytics_endpoints.py` - API endpoint testing
- `test_metrics_calculation.py` - Metric computation logic
- `test_analytics_aggregation.py` - Data aggregation

**Coverage Target**: 85%

#### 2. Content-Management Service (Port 8002)
**Existing**: 1 test file
**Add**:
- `test_content_dao.py` - Content CRUD operations
- `test_content_endpoints.py` - API testing
- `test_content_validation.py` - Content validation
- `test_content_versioning.py` - Version control

**Coverage Target**: 85%

#### 3. Content-Storage Service (Port 8003)
**Existing**: None
**Create**:
- `test_storage_dao.py` - File storage operations
- `test_storage_endpoints.py` - Upload/download APIs
- `test_file_validation.py` - File type/size validation
- `test_storage_cleanup.py` - Cleanup operations

**Coverage Target**: 80%

#### 4. Course-Generator Service (Port 8000)
**Existing**: 1 test file
**Add**:
- `test_course_generator_service.py` - AI generation logic
- `test_rag_integration.py` - RAG service integration
- `test_template_engine.py` - Course templates
- `test_generator_endpoints.py` - API testing

**Coverage Target**: 85%

#### 5. Course-Management Service (Port 8004)
**Existing**: Video tests (complete)
**Add**:
- `test_course_dao.py` - Course CRUD
- `test_course_endpoints.py` - Course APIs
- `test_course_lifecycle.py` - Lifecycle management
- `test_enrollment.py` - Enrollment logic

**Coverage Target**: 90% (critical service)

#### 6. Demo-Service (Port 8010)
**Existing**: 1 test file
**Add**:
- `test_demo_data_generator.py` - Data generation
- `test_demo_scenarios.py` - Demo scenarios
- `test_demo_cleanup.py` - Cleanup logic

**Coverage Target**: 75%

#### 7. Lab-Manager Service (Port 8005)
**Existing**: 1 test file
**Add**:
- `test_docker_operations.py` - Docker container ops
- `test_lab_lifecycle.py` - Lab creation/destruction
- `test_ide_provisioning.py` - IDE setup
- `test_resource_limits.py` - Resource management

**Coverage Target**: 85%

#### 8. Organization-Management Service (Port 8006)
**Existing**: 5 test files
**Add**:
- `test_multi_tenant_isolation.py` - Tenant isolation
- `test_organization_rbac.py` - RBAC integration
- `test_project_management.py` - Project lifecycle
- `test_hierarchy.py` - Org hierarchy

**Coverage Target**: 90% (critical service)

#### 9. User-Management Service (Port 8007)
**Existing**: 2 test files
**Add**:
- `test_user_dao.py` - User CRUD
- `test_authentication.py` - Auth flows
- `test_password_management.py` - Password operations
- `test_user_endpoints.py` - User APIs
- `test_role_assignment.py` - Role management

**Coverage Target**: 90% (critical service)

#### 10. RAG-Service (Port 8009)
**Existing**: None
**Create**:
- `test_rag_retrieval.py` - Document retrieval
- `test_embedding_generation.py` - Embeddings
- `test_rag_endpoints.py` - API testing
- `test_progressive_learning.py` - Learning adaptation

**Coverage Target**: 80%

### Phase 3: Integration Tests

Create comprehensive integration tests in `tests/integration/`:

1. **Service Communication**
   - `test_course_generator_to_rag.py`
   - `test_course_to_content_management.py`
   - `test_user_to_organization.py`
   - `test_analytics_integration.py`

2. **End-to-End Workflows**
   - `test_course_creation_workflow.py`
   - `test_student_enrollment_workflow.py`
   - `test_lab_provisioning_workflow.py`
   - `test_organization_setup_workflow.py`

### Phase 4: E2E Selenium Tests

Expand `tests/e2e/` with comprehensive workflows:

1. **Student Workflows**
   - `test_student_dashboard_selenium.py`
   - `test_student_course_access_selenium.py`
   - `test_student_lab_selenium.py`

2. **Instructor Workflows**
   - `test_instructor_course_creation_selenium.py`
   - `test_instructor_analytics_selenium.py`
   - `test_instructor_grading_selenium.py`

3. **Org Admin Workflows**
   - `test_org_admin_projects_selenium.py`
   - `test_org_admin_users_selenium.py`
   - `test_org_admin_analytics_selenium.py`

### Phase 5: Frontend Tests

Expand `tests/frontend/unit/`:

1. **Component Tests**
   - `auth.test.js`
   - `dashboard.test.js`
   - `course-list.test.js`
   - `notifications.test.js`
   - `org-admin-dashboard.test.js`

2. **Utility Tests**
   - `api-client.test.js`
   - `validators.test.js`
   - `formatters.test.js`

## Test Standards

### All Tests Must Include

1. **Comprehensive Documentation**
   ```python
   """
   Unit Tests for [Component]

   BUSINESS REQUIREMENT:
   [Why this component exists]

   TECHNICAL IMPLEMENTATION:
   [How it's tested]
   """
   ```

2. **Proper Imports**
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'services' / 'service-name'))
   ```

3. **Fixtures and Mocks**
   - Real database connections for integration tests
   - Mocked external dependencies for unit tests
   - Shared fixtures in `tests/fixtures/`

4. **Coverage Annotations**
   ```python
   @pytest.mark.unit
   @pytest.mark.coverage
   ```

5. **Assertions**
   - Clear, descriptive assertion messages
   - Multiple assertions per test when appropriate
   - Edge case coverage

## Success Metrics

### Code Coverage Targets
- Critical services (auth, RBAC, org): **90%+**
- Core services (courses, content, analytics): **85%+**
- Supporting services (demo, storage): **75%+**
- Overall platform coverage: **85%+**

### Test Quality Metrics
- All tests must pass
- No test warnings (except deprecation)
- Execution time < 5 minutes for unit tests
- Execution time < 15 minutes for integration tests
- E2E tests complete in < 30 minutes

### Documentation
- Every test file has comprehensive docstring
- Complex test logic is commented
- Test README updated with new tests

## Execution Plan

### Week 1: Foundation
- ✅ Day 1: Create conftest.py, fix import paths
- ✅ Day 2-3: Refactor analytics + content-management
- ✅ Day 4-5: Refactor content-storage + course-generator

### Week 2: Core Services
- ✅ Day 1-2: Refactor course-management (beyond videos)
- ✅ Day 3: Refactor demo-service
- ✅ Day 4-5: Refactor lab-manager

### Week 3: Critical Services
- ✅ Day 1-2: Refactor organization-management
- ✅ Day 3-4: Refactor user-management
- ✅ Day 5: Refactor rag-service

### Week 4: Integration & E2E
- ✅ Day 1-2: Create integration tests
- ✅ Day 3-4: Create E2E Selenium tests
- ✅ Day 5: Frontend tests + final validation

## Deliverables

1. **~100 new test files** across all services
2. **5,000+ lines of test code**
3. **500+ test cases**
4. **85%+ overall coverage**
5. **Updated documentation**
6. **CI/CD integration ready**

---

**Status**: Planning Complete - Ready for Execution
**Next Step**: Create conftest.py and begin analytics service refactoring
