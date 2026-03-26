# Namespace Refactoring Guide

## Overview

This guide documents the automated namespace refactoring process for the Course Creator microservices platform. The refactoring script (`refactor_namespaces.py`) transforms 13 microservices from using colliding top-level namespaces to service-specific namespaces.

## Problem Statement

**Current State:**
```
services/
├── analytics/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── user-management/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
└── ...
```

All services use the same top-level package names (`domain`, `application`, `infrastructure`), causing:
- Namespace collisions when services interact
- Ambiguity in import statements
- Difficulties in shared Python environments
- Import resolution issues

**Target State:**
```
services/
├── analytics/
│   └── analytics/
│       ├── domain/
│       ├── application/
│       └── infrastructure/
├── user-management/
│   └── user_management/
│       ├── domain/
│       ├── application/
│       └── infrastructure/
└── ...
```

Each service has its own namespace, eliminating collisions.

## Script Features

### 1. Directory Restructuring
- Creates service-specific top-level package
- Moves `domain/`, `application/`, `infrastructure/` under service namespace
- Preserves all `__init__.py` files
- Creates new `__init__.py` for namespace package

### 2. Import Rewriting
- Scans all `.py` files in each service
- Detects patterns:
  - `from domain.` → `from SERVICE_NAME.domain.`
  - `from application.` → `from SERVICE_NAME.application.`
  - `from infrastructure.` → `from SERVICE_NAME.infrastructure.`
  - `import domain` → `import SERVICE_NAME.domain`
- Handles both `from X import Y` and `import X` styles

### 3. Safety Features
- **Dry-run mode**: Preview changes without execution
- **Automatic backups**: Creates timestamped backups before changes
- **Syntax validation**: Verifies Python syntax after refactoring
- **Detailed reporting**: Shows all changes made per service
- **Error handling**: Graceful failure with detailed error messages

### 4. Validation
- Pre-flight syntax validation
- Post-refactoring syntax verification
- Import statement correctness checking

## Usage

### Prerequisites
```bash
cd /home/bbrelin/course-creator
python3 --version  # Requires Python 3.7+
```

### Command-Line Options

```bash
# Show help
python3 refactor_namespaces.py --help

# Preview all changes (DRY RUN)
python3 refactor_namespaces.py --dry-run

# Preview changes for single service
python3 refactor_namespaces.py --dry-run --service analytics

# Preview with detailed output
python3 refactor_namespaces.py --dry-run --verbose

# Validate current Python syntax (no refactoring)
python3 refactor_namespaces.py --validate

# Execute refactoring for single service
python3 refactor_namespaces.py --service analytics

# Execute refactoring for ALL services (requires confirmation)
python3 refactor_namespaces.py

# Execute with detailed progress
python3 refactor_namespaces.py --verbose
```

### Recommended Workflow

#### Step 1: Pre-flight Validation
```bash
# Validate all services have valid Python syntax
python3 refactor_namespaces.py --validate
```

Expected output:
```
🔍 Validating Python imports for 13 services...

✓ analytics
✓ content-management
✓ content-storage
...
```

#### Step 2: Preview Changes (Dry Run)
```bash
# Preview changes for all services
python3 refactor_namespaces.py --dry-run --verbose
```

Review the output carefully:
- Number of imports to be changed
- Directories to be moved
- Expected final structure

#### Step 3: Test on Single Service
```bash
# Refactor one service as a test
python3 refactor_namespaces.py --service analytics

# Verify the service still works
docker-compose restart analytics
docker-compose logs analytics

# Test the service endpoints
curl http://localhost:8002/health
```

#### Step 4: Refactor All Services
```bash
# Execute full refactoring
python3 refactor_namespaces.py --verbose
```

When prompted, type `yes` to confirm.

#### Step 5: Post-Refactoring Testing
```bash
# Restart all services
docker-compose down
docker-compose up -d

# Check service health
docker-compose ps

# Run test suite
pytest

# Manual smoke tests
curl http://localhost:8000/health  # user-management
curl http://localhost:8002/health  # analytics
# ... test other services
```

## Script Output

### Summary Report
```
REFACTORING SUMMARY
================================================================================

Services processed: 13
  ✓ Successful: 13
  ✗ Failed: 0

Total changes:
  • Directories moved: 39
  • Imports updated: 247

DETAILED RESULTS
────────────────────────────────────────────────────────────────────────────────

✓ SUCCESS - analytics
  Directories moved: 3
  Imports updated: 18

✓ SUCCESS - user-management
  Directories moved: 3
  Imports updated: 25
...
```

### Backup Location
```
Backups saved to: /home/bbrelin/course-creator/.backups/namespace_refactoring/

analytics_20251006_221558/
user-management_20251006_221600/
...
```

## Services Affected

The script will refactor these 13 services:
1. `analytics`
2. `content-management`
3. `content-storage`
4. `course-generator`
5. `course-management`
6. `demo-service`
7. `knowledge-graph-service`
8. `lab-manager`
9. `metadata-service`
10. `nlp-preprocessing`
11. `organization-management`
12. `rag-service`
13. `user-management`

## Example Transformations

### Before Refactoring

**File**: `services/analytics/main.py`
```python
from domain.entities.student_analytics import LearningAnalytics
from domain.interfaces.analytics_service import IAnalyticsService
from infrastructure.container import AnalyticsContainer
```

**Structure**:
```
services/analytics/
├── domain/
│   ├── entities/
│   └── interfaces/
├── application/
│   └── services/
└── infrastructure/
    └── container.py
```

### After Refactoring

**File**: `services/analytics/main.py`
```python
from analytics.domain.entities.student_analytics import LearningAnalytics
from analytics.domain.interfaces.analytics_service import IAnalyticsService
from analytics.infrastructure.container import AnalyticsContainer
```

**Structure**:
```
services/analytics/
└── analytics/
    ├── __init__.py
    ├── domain/
    │   ├── entities/
    │   └── interfaces/
    ├── application/
    │   └── services/
    └── infrastructure/
        └── container.py
```

## Rollback Procedure

If you need to rollback after refactoring:

### Option 1: Restore from Backup (Recommended)
```bash
# Find your backup timestamp
ls -la /home/bbrelin/course-creator/.backups/namespace_refactoring/

# Restore a specific service
SERVICE_NAME="analytics"
TIMESTAMP="20251006_221558"
rm -rf services/${SERVICE_NAME}
cp -r .backups/namespace_refactoring/${SERVICE_NAME}_${TIMESTAMP} services/${SERVICE_NAME}

# Restart the service
docker-compose restart ${SERVICE_NAME}
```

### Option 2: Git Reset (if committed)
```bash
# If changes were committed to git
git log --oneline  # Find the commit hash before refactoring
git reset --hard <commit-hash>
docker-compose restart
```

### Option 3: Manual Reversal
```bash
# For each service, move directories back
cd services/analytics
mv analytics/domain ./
mv analytics/application ./
mv analytics/infrastructure ./
rmdir analytics

# Manually revert import statements (use git diff for reference)
```

## Troubleshooting

### Issue: Import Errors After Refactoring
**Symptoms**: `ModuleNotFoundError: No module named 'analytics.domain'`

**Solution**:
1. Check that `__init__.py` exists in the new namespace directory
2. Verify PYTHONPATH includes the service directory
3. Restart the service container

### Issue: Syntax Errors in Refactored Files
**Symptoms**: Script reports validation errors

**Solution**:
1. Review the specific file mentioned in error
2. Check for edge cases in import statements
3. Restore from backup and manually fix the problematic file
4. Re-run script on remaining services

### Issue: Service Won't Start After Refactoring
**Symptoms**: Docker container exits immediately

**Solution**:
1. Check container logs: `docker-compose logs <service>`
2. Look for import-related errors
3. Verify all import statements were updated
4. Check for circular import issues
5. Restore from backup if needed

## Post-Refactoring Checklist

- [ ] All services start successfully in Docker
- [ ] Health endpoints respond correctly
- [ ] API endpoints function as expected
- [ ] Test suite passes (pytest)
- [ ] No import errors in logs
- [ ] Database migrations still work
- [ ] Inter-service communication works
- [ ] CI/CD pipeline passes
- [ ] Update deployment scripts if needed
- [ ] Update documentation referencing old paths

## Additional Considerations

### PYTHONPATH Configuration
After refactoring, ensure your PYTHONPATH is configured correctly:

```bash
# In docker-compose.yml or service run scripts
PYTHONPATH=/app:/app/services/<service-name>
```

### Import Style Consistency
The script handles both import styles:
```python
# Both are updated correctly
from domain.entities import User
import domain.entities as entities
```

### Relative Imports
The script focuses on absolute imports. If your code uses relative imports (e.g., `from ..domain import X`), those will need manual review.

### Service-to-Service Imports
If services import from each other (rare in microservices), you'll need to update those manually:
```python
# Before
from domain.entities import User  # ambiguous

# After
from analytics.domain.entities import AnalyticsUser
from user_management.domain.entities import User  # explicit
```

## Performance Notes

- **Typical runtime**: 5-10 seconds per service
- **Backup size**: ~5-10 MB per service
- **Total refactoring time**: ~2-3 minutes for all 13 services

## Version Information

- **Script version**: 1.0.0
- **Python requirement**: 3.7+
- **Platform**: Course Creator v3.1.0+

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review script output for specific error messages
3. Examine backup files for comparison
4. Check git history for reference

## License

This script is part of the Course Creator platform codebase.
