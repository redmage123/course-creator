# Troubleshooting

## Common Issues and Problem-Solving Methodology

### Service Startup Issues (Resolved v2.1)
Recent fixes have resolved common startup problems:

#### Pydantic Version Compatibility
- **Issue**: Services failing with `'regex' is removed. use 'pattern' instead` error
- **Resolution**: Updated all Pydantic Field definitions from `regex=` to `pattern=` across all services
- **Affected Services**: Course Management, User Management, Content Storage
- **Status**: ✅ Resolved

#### Docker Health Check Failures
- **Issue**: Frontend service showing as unhealthy despite working correctly
- **Root Cause**: Health check using `localhost` resolving to IPv6 `[::1]` while nginx listening on IPv4
- **Resolution**: Updated health check in docker-compose.yml to use `127.0.0.1:3000/health`
- **Status**: ✅ Resolved

#### Container Rebuild Issues
- **Issue**: Code changes not reflected in running containers
- **Resolution**: Use `docker build --no-cache` and ensure proper container recreation
- **Best Practice**: Always stop and remove containers before recreating with new images

## Docker Service Startup Troubleshooting Guide

**CRITICAL**: Follow Chain of Thoughts methodology for service startup issues. Do not apply incremental fixes.

### 1. Python Import Resolution Issues

**Root Cause**: Relative imports fail in Docker containers due to module path resolution.

**Symptoms**:
- `ImportError: attempted relative import beyond top-level package`
- Services continuously restarting with import errors

**Systematic Solution**:
```bash
# 1. Identify all relative imports
grep -r "from \.\.\." services/[service-name]/

# 2. Convert ALL relative imports to absolute imports
# FROM: from ...domain.interfaces.user_repository import IUserRepository
# TO:   from domain.interfaces.user_repository import IUserRepository

# 3. Affected files typically include:
# - application/services/*.py
# - infrastructure/repositories/*.py
# - Any file using ../../.. import patterns
```

**Files Requiring Import Fixes**:
- `services/user-management/application/services/user_service.py`
- `services/user-management/application/services/authentication_service.py`
- `services/user-management/application/services/session_service.py`
- `services/user-management/infrastructure/repositories/postgresql_user_repository.py`
- `services/user-management/infrastructure/repositories/postgresql_session_repository.py`

### 2. FastAPI Dependency Injection Issues

**Root Cause**: Missing dependency injection functions for FastAPI endpoints.

**Symptoms**:
- `NameError: name 'get_syllabus_service' is not defined`
- Import errors on service startup

**Systematic Solution**:
```python
# Add missing dependency functions to app/dependencies.py:
def get_syllabus_service() -> SyllabusService:
    """Get syllabus service for FastAPI dependency injection."""
    return get_container().get_syllabus_service()

def get_exercise_service() -> ExerciseGenerationService:
    """Get exercise service for FastAPI dependency injection."""
    return get_container().get_exercise_service()
```

**Required Imports in API Files**:
```python
from app.dependencies import get_container, get_syllabus_service
```

### 3. Hydra Configuration Structure Issues

**Root Cause**: Configuration access patterns don't match actual Hydra config structure.

**Symptoms**:
- `ConfigAttributeError: Key 'app' is not in struct`
- `Missing key service`

**Systematic Solution**:
```python
# Use defensive configuration access:
docs_url="/docs" if getattr(config, 'service', {}).get('debug', False) else None

# Instead of direct access:
docs_url="/docs" if config.app.debug else None  # WRONG
```

### 4. Docker Container Code Caching

**Root Cause**: Docker containers use cached code that doesn't reflect file system changes due to aggressive build caching.

**Why Docker Caching Fails**:
- Build context caching uses file checksums but sometimes misses changes
- Image removal doesn't always clear associated build cache layers  
- Docker Compose may reference old cached layers even after image removal
- Container recreation vs rebuild - restart uses existing images

**Systematic Solution** (in order of increasing thoroughness):

```bash
# Level 1: Standard rebuild (often insufficient)
docker compose stop [service-name]
docker image rm -f course-creator-[service-name]:latest
docker compose up -d [service-name]

# Level 2: Force complete cache clearing (recommended)
docker compose stop [service-name]
docker image rm -f course-creator-[service-name]:latest
docker builder prune -f
docker compose build --no-cache [service-name]
docker compose up -d [service-name]

# Level 3: Nuclear option (for persistent cache issues)
docker compose down [service-name]
docker image rm -f course-creator-[service-name]:latest
docker builder prune -af
docker system prune -f
docker compose build --no-cache [service-name]
docker compose up -d [service-name]

# Verification Steps:
docker logs course-creator-[service-name]-1 --tail 10
docker inspect course-creator-[service-name]:latest | grep Created
```

**Prevention Best Practices**:
- Always use `--no-cache` flag when debugging code changes
- Use `docker builder prune -f` between rebuilds
- Verify image creation timestamp matches your rebuild time
- Check container logs immediately after rebuild to confirm changes took effect

### 5. Database Connection Issues

**Root Cause**: Database configuration mismatches or connectivity problems.

**Symptoms**:
- `psycopg2.OperationalError: could not connect to server`
- `FATAL: database "course_creator" does not exist`
- Services unable to start due to database errors

**Systematic Solution**:
```bash
# 1. Check database container status
docker compose ps postgres

# 2. Verify database logs
docker compose logs postgres

# 3. Test database connectivity
docker exec -it course-creator-postgres-1 psql -U course_creator -d course_creator -c "SELECT 1;"

# 4. Reset database if needed
docker compose down
docker volume rm course-creator_postgres_data
python deploy/setup-database.py

# 5. Verify environment variables
grep -r "DATABASE_URL\|DB_HOST\|DB_PORT" .env docker-compose.yml
```

### 6. Port Conflicts

**Root Cause**: Service ports already in use by other processes.

**Symptoms**:
- `bind: address already in use`
- Services failing to start with port binding errors

**Systematic Solution**:
```bash
# 1. Identify process using the port
lsof -i :8000  # Replace with specific port
netstat -tulpn | grep :8000

# 2. Stop conflicting processes
sudo kill -9 [PID]

# 3. Verify ports are available
for port in 8000 8001 8003 8004 8005 8006 8007 8008; do
    lsof -i :$port && echo "Port $port is in use" || echo "Port $port is available"
done

# 4. Use alternative ports if needed (modify docker-compose.yml)
```

## Lab Container Issues

### Container Creation Failures

**Root Cause**: Docker daemon access or resource constraints.

**Symptoms**:
- Lab containers fail to start
- Permission denied errors when creating containers
- Resource allocation failures

**Systematic Solution**:
```bash
# 1. Verify Docker daemon access
docker ps
ls -la /var/run/docker.sock

# 2. Check resource availability
docker system df
docker stats

# 3. Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# 4. Cleanup unused resources
docker system prune -f
docker container prune -f
docker image prune -f
```

### IDE Service Failures

**Root Cause**: IDE services within lab containers not starting properly.

**Symptoms**:
- IDE interfaces not loading
- Connection timeouts to IDE ports
- IDE services showing as unhealthy

**Systematic Solution**:
```bash
# 1. Check IDE service logs within container
docker exec [lab-container] ps aux | grep -E "code-server|jupyter|intellij"

# 2. Verify port mappings
docker port [lab-container]

# 3. Test IDE service health
curl http://localhost:[ide-port]/health

# 4. Restart IDE services within container
docker exec [lab-container] supervisorctl restart all
```

## Frontend Issues

### JavaScript Module Loading Errors

**Root Cause**: ES6 module import/export issues or missing dependencies.

**Symptoms**:
- `SyntaxError: Cannot use import statement outside a module`
- `ReferenceError: [function] is not defined`
- Frontend functionality not working

**Systematic Solution**:
```bash
# 1. Verify module type in HTML
grep 'type="module"' frontend/html/*.html

# 2. Check import/export syntax
grep -r "import\|export" frontend/js/

# 3. Validate JavaScript syntax
node -c frontend/js/[file].js

# 4. Check browser console for errors
# Open browser DevTools and check Console tab
```

### CSS Styling Issues

**Root Cause**: CSS conflicts, missing stylesheets, or specificity problems.

**Symptoms**:
- Layout broken or inconsistent
- Styles not applying as expected
- Missing visual elements

**Systematic Solution**:
```bash
# 1. Validate CSS syntax
stylelint frontend/css/*.css

# 2. Check for missing CSS files
grep -r "\.css" frontend/html/ | xargs -I {} test -f {}

# 3. Verify CSS loading in browser
# Check Network tab in DevTools for 404 errors

# 4. Inspect element styles in browser
# Use DevTools Elements tab to debug specificity issues
```

## Authentication and Authorization Issues

### JWT Token Problems

**Root Cause**: Token expiration, invalid signatures, or malformed tokens.

**Symptoms**:
- `401 Unauthorized` errors
- Users automatically logged out
- API requests failing with authentication errors

**Systematic Solution**:
```bash
# 1. Check JWT secret consistency
grep JWT_SECRET .env docker-compose.yml

# 2. Verify token expiration settings
grep -r "expires\|expiry" services/user-management/

# 3. Test token validation
curl -H "Authorization: Bearer [token]" http://localhost:8000/auth/profile

# 4. Check user session in Redis
docker exec -it course-creator-redis-1 redis-cli
> KEYS session:*
> GET session:[session-id]
```

### RBAC Permission Errors

**Root Cause**: Incorrect role assignments or permission configurations.

**Symptoms**:
- Users unable to access features they should have access to
- `403 Forbidden` errors for authorized actions
- Role-based UI not displaying correctly

**Systematic Solution**:
```bash
# 1. Check user roles in database
docker exec -it course-creator-postgres-1 psql -U course_creator -d course_creator
# SELECT * FROM organization_memberships WHERE user_id = '[user-id]';

# 2. Verify permission definitions
grep -r "permissions" services/organization-management/

# 3. Test API endpoints with proper roles
curl -H "Authorization: Bearer [token]" http://localhost:8008/api/v1/rbac/permissions/[user-id]

# 4. Check RBAC cache
docker exec -it course-creator-redis-1 redis-cli
> KEYS rbac:*
```

### Login Redirect Issues (Fixed v3.3.1)

**Root Cause**: Missing localStorage data or URL parameters required by role-specific dashboards.

**Symptoms**:
- User redirects to dashboard but bounces back to homepage after 10-12 seconds
- Org-admin login appears to work but redirects back to homepage
- Dashboard loads briefly then redirects away

**Common Issues**:

#### Issue 1: Missing currentUser Object in localStorage
- **Symptom**: Dashboard validateSession() fails immediately
- **Cause**: Login only stored authToken/userRole, not full user object
- **Solution**: Login must store complete user object:
```javascript
// In frontend/html/index.html handleAccountLogin function
localStorage.setItem('currentUser', JSON.stringify(data.user));
localStorage.setItem('authToken', data.access_token);
localStorage.setItem('userRole', data.user.role);
localStorage.setItem('userName', data.user.username);
localStorage.setItem('isGuest', 'false');
```

#### Issue 2: Missing Session Timestamps
- **Symptom**: Dashboard validateSession() fails on timestamp check
- **Cause**: Login didn't create sessionStart/lastActivity timestamps
- **Solution**: Add session timestamps during login:
```javascript
const now = Date.now();
localStorage.setItem('sessionStart', now.toString());
localStorage.setItem('lastActivity', now.toString());
```

#### Issue 3: Org-Admin Missing org_id Parameter (CRITICAL)
- **Symptom**: Org-admin redirects to dashboard, then back to home after timeout
- **Cause**: org-admin-dashboard.html REQUIRES `org_id` URL parameter
- **Location**: `frontend/js/modules/org-admin-core.js:87-91`
- **Solution**: Include org_id in redirect URL:
```javascript
// For org-admin login redirect
const orgId = data.user.organization_id;
window.location.href = orgId
    ? `/html/org-admin-dashboard.html?org_id=${orgId}`
    : '/html/org-admin-dashboard.html';
```

#### Issue 4: Missing is_site_admin Field
- **Symptom**: Site admin dashboard rejects user with role check failure
- **Cause**: UserResponse missing calculated is_site_admin boolean
- **Solution**: Backend must include is_site_admin in response:
```python
# In services/user-management/routes.py UserResponse model
class UserResponse(BaseModel):
    # ... other fields ...
    is_site_admin: bool = False

# In _user_to_response() helper
def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        # ... other fields ...
        is_site_admin=(user.role.value == "site_admin")
    )
```

**Verification Commands**:
```bash
# Test admin redirect
pytest tests/e2e/test_login_redirect_proof.py::TestLoginRedirectProof::test_admin_login_redirects_to_site_admin_dashboard -v

# Test org-admin redirect (includes org_id verification)
pytest tests/e2e/test_login_redirect_proof.py::TestLoginRedirectProof::test_org_admin_login_redirects_to_org_admin_dashboard -v

# Check localStorage after login (browser console)
console.log({
    authToken: localStorage.getItem('authToken'),
    userRole: localStorage.getItem('userRole'),
    currentUser: JSON.parse(localStorage.getItem('currentUser')),
    sessionStart: localStorage.getItem('sessionStart'),
    lastActivity: localStorage.getItem('lastActivity')
});
```

**Related Files**:
- Login handler: `frontend/html/index.html:513-620`
- Site admin validation: `frontend/js/site-admin-dashboard.js:245`
- Org admin validation: `frontend/js/modules/org-admin-core.js:44-126`
- User response model: `services/user-management/routes.py:25-45`
- E2E tests: `tests/e2e/test_login_redirect_proof.py`

## Password Management Issues (v3.0)

### Password Change Failures

**Root Cause**: Authentication issues, password validation failures, or service communication problems.

**Symptoms**:
- "Current password is incorrect" errors
- Password change form not submitting
- Authentication token errors
- Service communication failures between organization and user management services

**Systematic Solution**:
```bash
# 1. Verify user authentication
curl -X POST "http://localhost:8000/auth/password/change" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password": "current", "new_password": "newpassword123"}'

# 2. Check authentication token validity
# Look for JWT token in browser localStorage or sessionStorage
# Verify token hasn't expired

# 3. Test password validation
# Frontend validation: minimum 8 chars, complexity requirements
# Backend validation: old password verification

# 4. Check service logs
docker logs course-creator-user-management-1 | grep -i password
docker logs course-creator-organization-management-1 | grep -i admin
```

### Organization Registration with Password Issues

**Root Cause**: Service communication failures, password validation errors, or form submission issues.

**Symptoms**:
- Organization registration failing after password entry
- Admin user not being created
- ES6 export syntax errors in browser
- Form validation errors despite valid input

**Systematic Solution**:
```bash
# 1. Test organization registration endpoint
curl -X POST "http://localhost:8008/api/v1/organizations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Org",
    "slug": "test-org", 
    "address": "123 Test St",
    "contact_phone": "+15551234567",
    "contact_email": "admin@testorg.com",
    "admin_full_name": "Test Admin",
    "admin_email": "admin@testorg.com", 
    "admin_password": "TestPassword123!"
  }'

# 2. Check service communication
# Organization service should call user management service
docker logs course-creator-organization-management-1 | grep "Creating organization administrator"
docker logs course-creator-user-management-1 | grep "register"

# 3. Verify frontend configuration
# Check that config-global.js is loaded instead of config.js
curl -s "https://localhost:3000/js/config-global.js" | head -10

# 4. Test password strength validation
# Open browser console on registration page
# Type in password field and verify strength indicator appears
```

### Password Strength Validation Issues

**Root Cause**: JavaScript errors, missing password strength calculation, or UI display problems.

**Symptoms**:
- Password strength indicator not appearing
- Strength calculation showing incorrect results  
- Visual feedback not updating in real-time
- Password confirmation not validating properly

**Systematic Solution**:
```bash
# 1. Check JavaScript console for errors
# Open browser dev tools → Console tab
# Look for errors related to password strength calculation

# 2. Verify password strength algorithm
# Test in browser console:
# calculatePasswordStrength("weak")      # Should return score <= 2
# calculatePasswordStrength("Str0ng!")   # Should return score >= 4

# 3. Test password matching validation
# Verify confirm password field shows error when passwords don't match
# Should clear error when passwords match

# 4. Check CSS styling
# Ensure .password-strength classes are defined
# Verify .password-strength-bar and .password-strength-fill elements appear
```

### Country Dropdown Keyboard Navigation Issues

**Root Cause**: JavaScript initialization failures, event handler problems, or search functionality errors.

**Symptoms**:
- Type-to-search not working in country dropdowns
- Search feedback not appearing
- Keyboard navigation not responding
- Country selection not working properly

**Systematic Solution**:
```bash
# 1. Check JavaScript console
# Look for errors in organization-registration.js
# Verify initializeCountryDropdowns() is called

# 2. Test search functionality
# Click on country dropdown
# Type country name (e.g., "united")
# Should filter and show "United States"
# Should show search feedback popup

# 3. Verify event handlers
# Check that keydown events are attached to select elements
# Verify search timeout is working (1 second delay)

# 4. Test keyboard controls
# Arrow keys should navigate options
# Enter should select current option
# Escape should clear search and close dropdown
```

## Performance Issues

### Slow Response Times

**Root Cause**: Database query performance, resource constraints, or inefficient code.

**Symptoms**:
- API endpoints responding slowly
- Frontend loading delays
- Timeouts on operations

**Systematic Solution**:
```bash
# 1. Monitor resource usage
docker stats

# 2. Check database performance
docker exec -it course-creator-postgres-1 psql -U course_creator -d course_creator
# SELECT * FROM pg_stat_activity;

# 3. Review service logs for slow operations
docker compose logs | grep -E "slow|timeout|performance"

# 4. Profile specific endpoints
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Memory and CPU Issues

**Root Cause**: Resource leaks, inefficient algorithms, or insufficient resource allocation.

**Symptoms**:
- Containers being killed by Docker
- Out of memory errors
- High CPU usage

**Systematic Solution**:
```bash
# 1. Monitor container resources
docker stats --no-stream

# 2. Check Docker resource limits
docker inspect [container] | grep -A 10 "Resources"

# 3. Increase resource limits if needed (docker-compose.yml)
# deploy:
#   resources:
#     limits:
#       memory: 2G
#       cpus: '1.5'

# 4. Profile memory usage
docker exec [container] ps aux --sort=-%mem | head -10
```

## Debugging Methodology

### Chain of Thoughts Approach

1. **Identify Symptoms** - What exactly is failing?
2. **Gather Information** - Logs, error messages, system state
3. **Hypothesize Root Cause** - What could cause these symptoms?
4. **Test Hypothesis** - Verify if the hypothesis explains all symptoms
5. **Apply Systematic Fix** - Fix the root cause, not just symptoms
6. **Verify Resolution** - Confirm the issue is completely resolved
7. **Document Solution** - Update troubleshooting guides

### Essential Debugging Commands

```bash
# Service health and status
./app-control.sh status
docker compose ps
docker compose logs [service]

# Network connectivity
curl http://localhost:[port]/health
netstat -tulpn | grep [port]

# Resource monitoring
docker stats
df -h
free -h

# Database connectivity
docker exec -it course-creator-postgres-1 psql -U course_creator -d course_creator -c "SELECT 1;"

# Cache inspection
docker exec -it course-creator-redis-1 redis-cli ping

# Container inspection
docker logs [container] --tail 50
docker exec -it [container] /bin/bash
```

### Log Analysis

```bash
# Find errors across all services
docker compose logs | grep -i error

# Monitor logs in real-time
docker compose logs -f

# Service-specific error patterns
docker compose logs [service] | grep -E "error|exception|failed"

# Performance analysis
docker compose logs | grep -E "slow|timeout|performance"
```

## Emergency Recovery Procedures

### Complete System Reset

```bash
# Stop all services
docker compose down

# Remove all containers and images
docker system prune -af

# Remove volumes (WARNING: destroys all data)
docker volume prune -f

# Rebuild and restart
docker compose build --no-cache
docker compose up -d

# Restore database
python deploy/setup-database.py
```

### Service-Specific Recovery

```bash
# Restart single service
docker compose restart [service]

# Rebuild single service
docker compose stop [service]
docker compose build --no-cache [service]
docker compose up -d [service]

# Check service health
curl http://localhost:[port]/health
```

### Data Recovery

```bash
# Backup before recovery
docker exec course-creator-postgres-1 pg_dump -U course_creator course_creator > backup.sql

# Restore from backup
docker exec -i course-creator-postgres-1 psql -U course_creator course_creator < backup.sql

# Reset specific tables if needed
python deploy/setup-database.py --reset-table [table_name]
```

## Prevention Best Practices

1. **Regular Health Checks** - Monitor service health endpoints
2. **Log Monitoring** - Set up alerts for error patterns
3. **Resource Monitoring** - Track CPU, memory, and disk usage
4. **Backup Strategy** - Regular database and configuration backups
5. **Testing** - Comprehensive testing before deployment
6. **Documentation** - Keep troubleshooting guides updated
7. **Monitoring** - Implement comprehensive monitoring and alerting