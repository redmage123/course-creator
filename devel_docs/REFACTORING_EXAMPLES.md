# Namespace Refactoring Examples

This document shows concrete before/after examples of the namespace refactoring.

## Overview

The refactoring addresses namespace collision by moving from:
- **Generic namespaces**: `domain`, `application`, `infrastructure`
- **Service-specific namespaces**: `analytics.domain`, `analytics.application`, etc.

## Directory Structure Changes

### Before Refactoring

```
services/
├── analytics/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   └── student_analytics.py
│   │   └── interfaces/
│   │       └── analytics_service.py
│   ├── application/
│   │   └── services/
│   │       ├── learning_analytics_service.py
│   │       └── student_activity_service.py
│   ├── infrastructure/
│   │   ├── container.py
│   │   └── metadata_client.py
│   ├── main.py
│   └── requirements.txt
│
└── user-management/
    ├── domain/          ← COLLISION! Same name as analytics/domain/
    │   └── entities/
    │       └── user.py
    ├── application/     ← COLLISION! Same name as analytics/application/
    │   └── services/
    └── infrastructure/  ← COLLISION! Same name as analytics/infrastructure/
```

### After Refactoring

```
services/
├── analytics/
│   ├── analytics/           ← NEW: Service-specific namespace
│   │   ├── __init__.py      ← NEW: Package marker
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   └── student_analytics.py
│   │   │   └── interfaces/
│   │   │       └── analytics_service.py
│   │   ├── application/
│   │   │   └── services/
│   │   │       ├── learning_analytics_service.py
│   │   │       └── student_activity_service.py
│   │   └── infrastructure/
│   │       ├── container.py
│   │       └── metadata_client.py
│   ├── main.py              ← Import statements updated
│   └── requirements.txt
│
└── user-management/
    └── user_management/     ← NEW: Service-specific namespace
        ├── __init__.py
        ├── domain/          ← NO MORE COLLISION!
        ├── application/     ← NO MORE COLLISION!
        └── infrastructure/  ← NO MORE COLLISION!
```

## Import Statement Changes

### Example 1: Simple From-Import

**File**: `services/analytics/main.py`

**Before:**
```python
from infrastructure.container import AnalyticsContainer
```

**After:**
```python
from analytics.infrastructure.container import AnalyticsContainer
```

---

### Example 2: Multiple Entity Imports

**File**: `services/analytics/application/services/learning_analytics_service.py`

**Before:**
```python
from domain.entities.student_analytics import LearningAnalytics, RiskLevel
from domain.interfaces.analytics_service import (
    ILearningAnalyticsService,
    IStudentActivityService
)
```

**After:**
```python
from analytics.domain.entities.student_analytics import LearningAnalytics, RiskLevel
from analytics.domain.interfaces.analytics_service import (
    ILearningAnalyticsService,
    IStudentActivityService
)
```

---

### Example 3: Infrastructure Imports

**File**: `services/analytics/metadata_analytics_endpoints.py`

**Before:**
```python
from infrastructure.metadata_client import get_metadata_client, MetadataServiceClient
```

**After:**
```python
from analytics.infrastructure.metadata_client import get_metadata_client, MetadataServiceClient
```

---

### Example 4: Cross-Layer Domain Import

**File**: `services/analytics/domain/interfaces/analytics_service.py`

**Before:**
```python
from domain.entities.student_analytics import (
    StudentActivity,
    LearningAnalytics,
    ActivityType,
    RiskLevel
)
```

**After:**
```python
from analytics.domain.entities.student_analytics import (
    StudentActivity,
    LearningAnalytics,
    ActivityType,
    RiskLevel
)
```

---

### Example 5: Application Service Imports

**File**: `services/analytics/infrastructure/container.py`

**Before:**
```python
from domain.interfaces.analytics_service import (
    IStudentActivityService,
    ILearningAnalyticsService,
    ICourseProgressService
)
from application.services.student_activity_service import StudentActivityService
from application.services.learning_analytics_service import LearningAnalyticsService
```

**After:**
```python
from analytics.domain.interfaces.analytics_service import (
    IStudentActivityService,
    ILearningAnalyticsService,
    ICourseProgressService
)
from analytics.application.services.student_activity_service import StudentActivityService
from analytics.application.services.learning_analytics_service import LearningAnalyticsService
```

---

## Real Import Statistics

Based on dry-run analysis:

### Analytics Service (18 imports changed)
- **Files affected**: 9 Python files
- **Domain imports**: 8
- **Application imports**: 4
- **Infrastructure imports**: 6

### User Management Service (20 imports changed)
- **Files affected**: Multiple files
- **Domain imports**: Most common
- **Application imports**: Service layer
- **Infrastructure imports**: Container, repositories

### Organization Management Service (43 imports changed)
- **Files affected**: Most complex service
- **Highest number of cross-layer dependencies**

## Import Patterns Handled

The script handles these patterns:

### Pattern 1: Direct From-Import
```python
# Before
from domain.entities import User

# After
from user_management.domain.entities import User
```

### Pattern 2: Specific Item Import
```python
# Before
from domain.entities.user import User, UserRole

# After
from user_management.domain.entities.user import User, UserRole
```

### Pattern 3: Multi-line Imports
```python
# Before
from domain.interfaces.analytics_service import (
    IAnalyticsService,
    IReportingService
)

# After
from analytics.domain.interfaces.analytics_service import (
    IAnalyticsService,
    IReportingService
)
```

### Pattern 4: Direct Import (less common)
```python
# Before
import domain.entities

# After
import analytics.domain.entities
```

## Services Without Changes

Some services don't use the layered architecture and require no changes:
- **content-storage**: Uses flat structure
- **demo-service**: Simple service without layers
- **lab-manager**: Different organization pattern
- **rag-service**: Minimal structure

## Benefits of Refactoring

### 1. No More Namespace Collisions
```python
# Before: Which service's User?
from domain.entities.user import User  # Ambiguous!

# After: Crystal clear
from user_management.domain.entities.user import User
from analytics.domain.entities.analytics_user import AnalyticsUser
```

### 2. Better IDE Support
- Auto-complete knows which service you're importing from
- Jump-to-definition works reliably
- Refactoring tools can track dependencies

### 3. Explicit Dependencies
```python
# It's now obvious which service depends on what
from analytics.domain.entities import AnalyticsUser
from user_management.application.services import AuthService
```

### 4. Improved Testability
```python
# Mock imports are clearer
@patch('analytics.infrastructure.container.AnalyticsContainer')
def test_analytics_endpoint(mock_container):
    # Test code
```

## Common Questions

### Q: What about relative imports?
**A**: The script focuses on absolute imports (`from domain.X`). Relative imports (`from ..domain`) are less common and should be reviewed manually.

### Q: Will this break existing code?
**A**: Only if external code imports from these services. Internal imports are all updated by the script.

### Q: How long does refactoring take?
**A**: ~5-10 seconds per service, ~2-3 minutes total for all 13 services.

### Q: Can I refactor services incrementally?
**A**: Yes! Use `--service <name>` to refactor one service at a time.

## Validation

After refactoring, the script validates:
1. **Python syntax**: All `.py` files parse correctly
2. **Import resolution**: No undefined references
3. **Package structure**: `__init__.py` files present

## Rollback

Backups are automatically created before refactoring:
```bash
.backups/namespace_refactoring/
├── analytics_20251006_221558/
├── user-management_20251006_221600/
└── ...
```

To rollback:
```bash
rm -rf services/analytics
cp -r .backups/namespace_refactoring/analytics_TIMESTAMP services/analytics
```

## Next Steps

After running the refactoring:
1. Restart services: `docker-compose restart`
2. Run tests: `pytest`
3. Check logs for import errors
4. Update any external code that imports from these services
5. Commit changes: `git add . && git commit -m "refactor: namespace isolation"`
