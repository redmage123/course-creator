# Lab Environment E2E Test Suite

Comprehensive end-to-end testing for lab environment resource management and container lifecycle.

## Overview

This test suite validates Docker container resource limits, enforcement mechanisms, and instructor analytics for student lab environments. Tests use real Docker API inspection and resource-intensive workloads to verify proper resource management.

## Test Files

### test_lab_resource_management.py (16 tests, 1,360 lines) ✅ COMPLETE

Comprehensive resource management testing covering:

**CPU Management (4 tests)**:
- CPU limit enforcement (1.0 core)
- 80% usage warning
- CPU throttling verification
- Instructor CPU analytics

**Memory Management (4 tests)**:
- Memory limit enforcement (2GB)
- 80% usage warning
- OOM killer testing
- Instructor memory analytics

**Storage Management (3 tests)**:
- Storage quota enforcement (500MB)
- 90% usage warning
- Write blocking when quota exceeded

**Network Management (2 tests)**:
- Bandwidth limit enforcement (10 Mbps)
- Unauthorized host blocking

**Resource Analytics (2 tests)**:
- Unified resource dashboard
- CSV export functionality

**Status**: Implementation complete, TDD RED phase (all tests expected to fail until features implemented)

---

### Other Test Files (Templates/In Progress)

- `test_lab_lifecycle_complete.py` (1,482 lines) - Lab lifecycle management
- `test_lab_storage_persistence.py` (934 lines) - Storage persistence testing
- `test_lab_timeout_cleanup.py` (1,056 lines) - Timeout and cleanup testing
- `test_multi_ide_support.py` (736 lines) - Multi-IDE support testing

**Note**: These files appear to be templates or in-progress implementations.

---

## Running Tests

### Run All Resource Management Tests

```bash
pytest tests/e2e/lab_environment/test_lab_resource_management.py -v
```

### Run Specific Categories

```bash
# CPU tests only
pytest tests/e2e/lab_environment/test_lab_resource_management.py -k "cpu" -v

# Memory tests only
pytest tests/e2e/lab_environment/test_lab_resource_management.py -k "memory" -v

# Critical priority tests
pytest tests/e2e/lab_environment/test_lab_resource_management.py -m "priority_critical" -v

# Analytics tests
pytest tests/e2e/lab_environment/test_lab_resource_management.py -k "analytics" -v
```

### Run with Test Markers

```bash
# Resource management tests only
pytest -m "resource_management" -v

# Lab environment tests only
pytest -m "lab_environment" -v

# Critical priority across all tests
pytest -m "priority_critical" -v
```

---

## Prerequisites

### Required Dependencies

```bash
pip install pytest pytest-asyncio docker selenium webdriver-manager asyncpg numpy
```

### Docker Access

Tests require Docker daemon access:

```bash
# Ensure Docker socket is accessible
ls -la /var/run/docker.sock

# Add test user to docker group if needed
sudo usermod -aG docker $USER
```

### Environment Variables

```bash
export TEST_BASE_URL="https://localhost:3000"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_USER="course_creator"
export DB_PASSWORD="secure_password"
export DB_NAME="course_creator"
export HEADLESS="true"
```

### Database Schema

Tests require the following table:

```sql
CREATE TABLE lab_resource_usage (
    id SERIAL PRIMARY KEY,
    student_id UUID NOT NULL,
    lab_id UUID NOT NULL,
    resource_type VARCHAR(20) NOT NULL,
    usage_value DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(10) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (lab_id) REFERENCES lab_environments(id)
);

CREATE INDEX idx_student_resource ON lab_resource_usage(student_id, resource_type, recorded_at);
CREATE INDEX idx_lab_resource ON lab_resource_usage(lab_id, recorded_at);
```

---

## Test Execution Time

Estimated execution times (headless mode):

- **CPU tests**: 30-60 seconds each (4 tests = 2-4 minutes)
- **Memory tests**: 20-40 seconds each (4 tests = 1.5-3 minutes)
- **Storage tests**: 30-90 seconds each (3 tests = 1.5-4.5 minutes)
- **Network tests**: 30-60 seconds each (2 tests = 1-2 minutes)
- **Analytics tests**: 10-20 seconds each (2 tests = 20-40 seconds)

**Total**: ~10-15 minutes for complete suite

---

## Resource Limits Tested

### Current Configuration

| Resource | Limit | Warning Threshold | Test Coverage |
|----------|-------|-------------------|---------------|
| CPU | 1.0 core | 80% (0.8 cores) | ✅ Verified via Docker API |
| Memory | 2GB | 80% (1.6GB) | ✅ Verified via Docker API + OOM testing |
| Storage | 500MB | 90% (450MB) | ✅ Verified via file I/O operations |
| Network | 10 Mbps | N/A | ✅ Verified via download speed measurement |

### Docker Configuration Verified

```python
# CPU Limit
container.attrs['HostConfig']['CpuQuota'] = 100000
container.attrs['HostConfig']['CpuPeriod'] = 100000
# Effective: 100000 / 100000 = 1.0 core

# Memory Limit
container.attrs['HostConfig']['Memory'] = 2147483648  # 2GB in bytes

# OOM Killer
container.attrs['State']['OOMKilled'] = True  # When memory exceeded
```

---

## Test Markers

Tests use pytest markers for categorization:

```python
@pytest.mark.e2e                    # End-to-end test
@pytest.mark.lab_environment        # Lab environment category
@pytest.mark.resource_management    # Resource management category
@pytest.mark.priority_critical      # Critical priority
@pytest.mark.priority_high          # High priority
@pytest.mark.priority_medium        # Medium priority
@pytest.mark.asyncio                # Async test (requires pytest-asyncio)
```

---

## Known Issues and Limitations

### Docker Daemon Access

Tests may fail in CI/CD environments without Docker access. Requires:
- Docker socket mounted (`/var/run/docker.sock`)
- Test runner has Docker group permissions
- Docker daemon is running

### OOM Killer Timing

OOM killer may take 5-10 seconds to terminate containers. Tests use generous timeouts.

### CPU Measurement Variance

CPU percentage measurements vary based on system load. Tests allow 10% variance (110% max).

### Network Test Reliability

Network bandwidth tests depend on external servers. May fail in:
- Air-gapped environments
- Networks with strict firewall rules
- Regions with poor connectivity to test servers

### Storage Quota Implementation

Docker lacks native per-container storage quotas. Tests assume:
- Volume driver with quota support (e.g., `local` with `size` option)
- OR filesystem-level quotas (e.g., XFS project quotas)
- OR application-level enforcement

### Headless Mode Limitations

CSV export download cannot be verified in headless mode. Test only verifies:
- Export button is clickable
- No errors thrown on click
- Actual file download not validated

---

## Troubleshooting

### "Cannot connect to Docker daemon"

```bash
# Check Docker daemon status
sudo systemctl status docker

# Check socket permissions
ls -la /var/run/docker.sock

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### "Container not found"

```bash
# Check lab containers exist
docker ps -a | grep lab_

# Verify test student account exists
psql -U course_creator -d course_creator -c "SELECT * FROM users WHERE email='student.test@example.com';"
```

### "TimeoutException" on UI elements

```bash
# Verify platform is running
curl -k https://localhost:3000

# Check all services healthy
docker ps | grep -E 'course-creator|lab-manager'

# Increase wait timeouts in code if system is slow
```

### "Connection refused" to database

```bash
# Check PostgreSQL running
docker ps | grep postgres

# Verify credentials
psql -h localhost -p 5432 -U course_creator -d course_creator

# Check environment variables
env | grep DB_
```

---

## TDD Development Workflow

### Phase 1: RED (Current Status)

All tests expected to FAIL as features not yet implemented:

```bash
pytest tests/e2e/lab_environment/test_lab_resource_management.py -v
# Expected: 16 failed, 0 passed
```

### Phase 2: GREEN

Implement features to pass tests one category at a time:

1. **Docker Resource Limits** (4 tests)
   - Configure CpuQuota, CpuPeriod, Memory in container creation
   - Expected: 4 passed after implementation

2. **Resource Warnings** (3 tests)
   - Implement monitoring service
   - Add UI warning components
   - Expected: 7 passed total

3. **Storage Quotas** (2 tests)
   - Configure volume quotas or filesystem limits
   - Expected: 9 passed total

4. **Network Limits** (2 tests)
   - Implement traffic control (tc)
   - Configure network policy whitelist
   - Expected: 11 passed total

5. **Analytics Dashboard** (5 tests)
   - Build instructor resource dashboard
   - Implement CSV export
   - Expected: 16 passed total (100%)

### Phase 3: REFACTOR

Optimize implementations while maintaining passing tests.

---

## Future Enhancements

### Planned Features

- [ ] **Dynamic resource allocation** based on course requirements
- [ ] **Resource prediction** using ML to forecast needs
- [ ] **Auto-scaling** for premium students
- [ ] **Resource pooling** for small labs
- [ ] **Real-time alerts** for instructors via WebSocket
- [ ] **Historical trends** with time-series analysis
- [ ] **Cost optimization** recommendations
- [ ] **Anomaly detection** for unusual patterns

### Additional Test Coverage

- [ ] GPU resource limits (for ML courses)
- [ ] Disk I/O throttling (iops limits)
- [ ] Container burst capabilities
- [ ] Resource reservation (minimum guarantees)
- [ ] Multi-container labs (microservices)
- [ ] Resource sharing between containers
- [ ] Dynamic limit adjustments
- [ ] Resource usage predictions

---

## Documentation

- **Test Report**: `TEST_REPORT_LAB_RESOURCE_MANAGEMENT.md` (19KB, comprehensive analysis)
- **This README**: Overview and usage guide
- **Test File**: `test_lab_resource_management.py` (46KB, 1,360 lines, 16 tests)

---

## Contact

For questions or issues with lab environment testing:

- **Platform Team**: Course Creator Platform Team
- **Test Suite Maintainer**: See git blame for latest contributors
- **Documentation**: This README and test report

---

**Last Updated**: 2025-11-05  
**Version**: 1.0.0  
**Status**: TDD RED Phase Complete
