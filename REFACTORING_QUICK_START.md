# Namespace Refactoring Quick Start

## TL;DR

```bash
# Step 1: Preview what will happen
python3 refactor_namespaces.py --dry-run

# Step 2: Test on one service
python3 refactor_namespaces.py --service analytics

# Step 3: Verify it works
docker-compose restart analytics
curl http://localhost:8002/health

# Step 4: Refactor everything
python3 refactor_namespaces.py
```

## What This Does

Transforms this:
```python
from domain.entities.user import User
from application.services.auth import AuthService
from infrastructure.container import Container
```

Into this:
```python
from user_management.domain.entities.user import User
from user_management.application.services.auth import AuthService
from user_management.infrastructure.container import Container
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `--dry-run` | Preview changes without executing |
| `--service NAME` | Refactor only one service |
| `--verbose` | Show detailed progress |
| `--validate` | Check syntax only, no changes |

## Expected Results

```
Services processed: 13
  ✓ Successful: 13
  ✗ Failed: 0

Total changes:
  • Directories moved: 26
  • Imports updated: 208
```

**Services Affected:**
- analytics (18 imports)
- content-management (35 imports)
- course-generator (25 imports)
- course-management (22 imports)
- knowledge-graph-service (20 imports)
- metadata-service (6 imports)
- nlp-preprocessing (19 imports)
- organization-management (43 imports)
- user-management (20 imports)
- content-storage (0 imports - no change)
- demo-service (0 imports - no change)
- lab-manager (0 imports - no change)
- rag-service (0 imports - no change)

## Safety Features

- **Automatic backups** → `.backups/namespace_refactoring/`
- **Dry-run mode** → See changes before applying
- **Syntax validation** → Ensures Python code remains valid
- **Service isolation** → Test one service at a time
- **Rollback support** → Easy to restore from backups

## If Something Goes Wrong

```bash
# Restore from backup
BACKUP_DIR=".backups/namespace_refactoring"
SERVICE="analytics"
TIMESTAMP=$(ls -t $BACKUP_DIR | grep $SERVICE | head -1)
rm -rf services/$SERVICE
cp -r $BACKUP_DIR/${TIMESTAMP} services/$SERVICE
docker-compose restart $SERVICE
```

## Post-Refactoring Checklist

- [ ] Services start: `docker-compose ps`
- [ ] Health checks pass: `curl http://localhost:8000/health` (etc.)
- [ ] Tests pass: `pytest`
- [ ] No import errors in logs: `docker-compose logs | grep -i "import"`

## Documentation

Full guide: [NAMESPACE_REFACTORING_GUIDE.md](./NAMESPACE_REFACTORING_GUIDE.md)
