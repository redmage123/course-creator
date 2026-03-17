# Bug Tracking System Workflow

## Overview

The Course Creator Platform includes an automated bug tracking system that uses Claude AI to analyze bugs, generate fixes, and create Pull Requests. This document describes the complete workflow and requirements.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  Bug Tracking   │────▶│  Background     │
│   Bug Form      │     │  API Service    │     │  Job Processor  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                        │
                                │                        ▼
                                ▼                ┌─────────────────┐
                        ┌─────────────────┐     │  Claude API     │
                        │  PostgreSQL     │     │  Integration    │
                        │  (bug_reports)  │     └─────────────────┘
                        └─────────────────┘              │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Git/PR         │
                                                │  Operations     │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Email Service  │
                                                │  Notification   │
                                                └─────────────────┘
```

## Workflow Stages

### Stage 1: Bug Submission

1. User submits bug via web form at `/bugs/submit`
2. Required fields:
   - Title (10-255 characters)
   - Description (minimum 20 characters)
   - Submitter email
3. Optional fields:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Severity (low, medium, high, critical)
   - Affected component
   - Browser info

### Stage 2: Claude Analysis

1. Bug is queued for background processing
2. Claude API analyzes the bug report with codebase context
3. Analysis produces:
   - **Root Cause Analysis** - Why the bug is occurring
   - **Suggested Fix** - Recommended code changes
   - **Affected Files** - List of files to modify
   - **Complexity Estimate** - trivial, simple, moderate, complex, major
   - **Confidence Score** - 0-100% confidence in analysis

### Stage 3: Fix Generation

1. If confidence score >= 70% and complexity <= moderate:
   - Claude generates fix code
   - Creates git branch: `bugfix/auto-{bug_id}`
   - Applies changes to affected files

### Stage 4: Pre-PR Validation

Before creating a PR, the system runs validation:

1. **Python files**: `python3 -m py_compile` syntax check
2. **TypeScript/JavaScript files**: File readability verification
3. If validation fails, changes are reverted

### Stage 5: Pull Request Creation

1. Changes are committed with descriptive message
2. Branch is pushed to origin
3. PR is created via GitHub CLI (`gh pr create`)
4. PR includes:
   - Bug ID and title
   - Root cause analysis
   - Fix description
   - Files changed with line counts
   - Confidence score

### Stage 6: Email Notification

Submitter receives email containing:
- Bug status update
- Root cause analysis
- Suggested fix details
- PR link (if created)
- Confidence score

---

## CRITICAL WORKFLOW REQUIREMENT

### No Merge Until Tests Pass

**IMPORTANT: Bugfix branches must NOT be merged into master until ALL tests have been verified to pass.**

#### Merge Checklist

Before merging any `bugfix/auto-*` branch:

- [ ] CI/CD pipeline has completed
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Code review completed (if required)
- [ ] No merge conflicts

#### Recommended GitHub Branch Protection Rules

Configure the following branch protection rules for `master`:

```yaml
# Settings > Branches > Branch protection rules > master

Require a pull request before merging: Yes
  - Require approvals: 1 (optional for auto-fixes)

Require status checks to pass before merging: Yes
  - Require branches to be up to date: Yes
  - Status checks required:
    - docker-infrastructure-test
    - unit-tests
    - integration-tests
    - e2e-tests

Require conversation resolution before merging: Yes

Do not allow bypassing the above settings: Yes
```

#### Workflow Diagram

```
Bug Submitted
      │
      ▼
Claude Analyzes
      │
      ▼
Fix Generated
      │
      ▼
PR Created ◄──────────────────────────────┐
      │                                    │
      ▼                                    │
CI/CD Runs Tests                           │
      │                                    │
      ├─── Tests Fail ───► Fix Required ───┘
      │
      ▼
Tests Pass ✅
      │
      ▼
Manual Review (optional)
      │
      ▼
Merge Approved
      │
      ▼
Merge to Master
```

---

## API Endpoints

### Bug Submission
```
POST /bugs
Content-Type: application/json

{
  "title": "Login button not working on mobile",
  "description": "When clicking the login button on mobile devices...",
  "severity": "high",
  "affected_component": "frontend-react",
  "submitter_email": "user@example.com"
}
```

### Get Bug Status
```
GET /bugs/{bug_id}

Response:
{
  "id": "e17e15d3-...",
  "title": "Login button not working on mobile",
  "status": "pr_opened",
  "analysis": {
    "root_cause": "...",
    "confidence_score": 85,
    "pr_url": "https://github.com/owner/repo/pull/1"
  }
}
```

### List Bugs
```
GET /bugs?status=analyzing&limit=10
```

---

## Configuration

### Required Environment Variables

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# GitHub (for PR creation)
GITHUB_OWNER=your-username
GITHUB_REPO=your-repo
GITHUB_TOKEN=ghp_...

# Codebase path (inside container)
CODEBASE_PATH=/workspace

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=...
```

### Docker Configuration

The bug-tracking service requires:
- Volume mount for codebase: `.:/workspace:rw`
- Git configured with safe.directory
- GitHub CLI (`gh`) installed
- CA certificates for HTTPS

---

## Service Information

- **Port**: 8017
- **Health Check**: `https://localhost:8017/health`
- **Docker Image**: `course-creator-bug-tracking:latest`

## Related Files

- Service: `services/bug-tracking/`
- Migration: `migrations/20251212_bug_tracking_system.sql`
- Frontend: `frontend-react/src/features/bug-tracking/`
- Plan: `.claude/plans/compiled-waddling-sketch.md`

---

## Troubleshooting

### Common Issues

1. **Git "dubious ownership" error**
   - Ensure Dockerfile includes: `git config --global --add safe.directory /workspace`

2. **SSH host key verification failed**
   - Service uses HTTPS with token authentication, not SSH
   - Verify `GITHUB_TOKEN` is set correctly

3. **Claude API 401 error**
   - Check `ANTHROPIC_API_KEY` is valid and not expired

4. **Tests timing out**
   - Basic syntax checks are used instead of full test suite
   - Full tests run in CI/CD after PR creation

5. **PR creation fails**
   - Verify `GH_TOKEN` environment variable is set
   - Check GitHub token has `repo` scope permissions
